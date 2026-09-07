"""Contracts for semantic podcast maps, visual proposals, and owner review."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import wave

import pytest

from tools.studio import dispatch


def call(project, method, **params):
    return dispatch({"method": method, "project": str(project), "params": params})


def write_audio(path: Path, seconds: int = 4) -> Path:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(8_000)
        output.writeframes(b"\0\0" * 8_000 * seconds)
    return path


@pytest.fixture
def podcast_project(tmp_path):
    project = tmp_path / "project"
    call(project, "create", title="Visual score")
    source = write_audio(tmp_path / "episode.wav")
    asset = call(project, "import_media", path=str(source), role="source")["assets"][0]
    call(
        project,
        "set_podcast_settings",
        primary_audio_asset_id=asset["id"],
        visual_density="balanced",
    )
    transcript_path = project / "work/transcript/episode.json"
    transcript_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "words": [
                    {"word": "Opening", "start_ms": 0, "end_ms": 400},
                    {"word": "comparison", "start_ms": 2_000, "end_ms": 2_600},
                ],
            }
        )
    )
    transcript_sha = hashlib.sha256(transcript_path.read_bytes()).hexdigest()
    episode_map = {
        "schema_version": 1,
        "podcast_settings_revision": 1,
        "primary_audio": {
            "asset_id": asset["id"],
            "sha256": asset["sha256"],
            "duration_ms": asset["duration_ms"],
        },
        "transcript": {"path": "work/transcript/episode.json", "sha256": transcript_sha},
        "chapters": [
            {
                "id": "opening",
                "title": "Opening",
                "start_ms": 0,
                "end_ms": 2_000,
                "transcript_anchor": {"start_ms": 0, "end_ms": 400, "text": "Opening"},
                "moments": [
                    {
                        "id": "opening-claim",
                        "kind": "claim",
                        "summary": "Opening claim",
                        "transcript_anchor": {"start_ms": 0, "end_ms": 400, "text": "Opening"},
                    }
                ],
            },
            {
                "id": "comparison",
                "title": "Comparison",
                "start_ms": 2_000,
                "end_ms": 4_000,
                "transcript_anchor": {
                    "start_ms": 2_000,
                    "end_ms": 2_600,
                    "text": "comparison",
                },
                "moments": [],
            },
        ],
    }
    return project, asset, episode_map


def visual_events(transcript_sha):
    common = {
        "chapter_id": "opening",
        "transcript_anchor": {"start_ms": 100, "end_ms": 300, "text": "Opening"},
        "purpose": "Reinforce the spoken point without changing its meaning.",
        "provenance": [{"kind": "transcript", "label": "Timed transcript", "sha256": transcript_sha}],
        "camera_policy": "base_only",
    }
    return [
        common
        | {
            "id": "base-1",
            "type": "base",
            "start_ms": 0,
            "end_ms": 300,
            "treatment": {"kind": "base"},
        },
        common
        | {
            "id": "chapter-1",
            "type": "chapter_card",
            "start_ms": 300,
            "end_ms": 600,
            "treatment": {"kind": "chapter_card", "heading": "Opening"},
        },
        common
        | {
            "id": "quote-1",
            "type": "quote",
            "start_ms": 600,
            "end_ms": 900,
            "treatment": {"kind": "quote", "mode": "key_point", "text": "A key point"},
        },
        common
        | {
            "id": "list-1",
            "type": "progressive_list",
            "start_ms": 900,
            "end_ms": 1_200,
            "treatment": {"kind": "progressive_list", "heading": "Steps", "items": ["One", "Two"]},
        },
        common
        | {
            "id": "comparison-1",
            "type": "comparison",
            "start_ms": 1_200,
            "end_ms": 1_500,
            "treatment": {
                "kind": "comparison",
                "heading": "Options",
                "left": {"label": "Before", "items": ["Manual"]},
                "right": {"label": "After", "items": ["Guided"]},
            },
        },
        common
        | {
            "id": "image-1",
            "type": "image_source",
            "start_ms": 1_500,
            "end_ms": 1_800,
            "treatment": {"kind": "image_source", "heading": "Source", "caption": "Project source"},
        },
    ]


def score_for(asset, episode_map_sha, transcript_sha, events=None):
    return {
        "schema_version": 1,
        "podcast_settings_revision": 1,
        "primary_audio": {
            "asset_id": asset["id"],
            "sha256": asset["sha256"],
            "duration_ms": asset["duration_ms"],
        },
        "episode_map_sha256": episode_map_sha,
        "visual_density": "balanced",
        "camera_policy": {"configured_asset_id": None, "default": "base_only"},
        "visual_events": events if events is not None else visual_events(transcript_sha),
    }


def install_episode_map(project, episode_map):
    state = call(project, "set_episode_map", episode_map=episode_map)
    assert state["episode_map"] == episode_map
    return state["episode_map_sha256"]


def test_episode_map_binds_exact_solo_audio_transcript_and_duration(podcast_project):
    project, asset, episode_map = podcast_project
    episode_map_sha = install_episode_map(project, episode_map)
    stored = json.loads((project / "work/podcast/episode-map.json").read_text())
    assert stored == episode_map
    assert episode_map_sha == hashlib.sha256((project / "work/podcast/episode-map.json").read_bytes()).hexdigest()

    previous = (project / "work/podcast/episode-map.json").read_bytes()
    for mutate in (
        lambda value: value["primary_audio"].update(duration_ms=3_000),
        lambda value: value["transcript"].update(sha256="0" * 64),
        lambda value: value["chapters"][0]["transcript_anchor"].update(end_ms=2_100),
        lambda value: value.update(podcast_settings_revision=0),
    ):
        invalid = copy.deepcopy(episode_map)
        mutate(invalid)
        with pytest.raises(ValueError):
            call(project, "set_episode_map", episode_map=invalid)
        assert (project / "work/podcast/episode-map.json").read_bytes() == previous
    assert call(project, "open")["assets"][0]["sha256"] == asset["sha256"]


def test_visual_score_revisions_are_validated_content_addressed_and_immutable(podcast_project):
    project, asset, episode_map = podcast_project
    episode_map_sha = install_episode_map(project, episode_map)
    score = score_for(asset, episode_map_sha, episode_map["transcript"]["sha256"])

    first = call(project, "create_visual_score_revision", score=score)
    first_id = first["current_revision_id"]
    assert first["score"]["revision_id"] == first_id
    assert first_id == hashlib.sha256(
        json.dumps(score, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    revision_path = project / f"work/podcast/visual-score/revisions/{first_id}.json"
    immutable = revision_path.read_bytes()

    identical = call(project, "create_visual_score_revision", score=score)
    assert identical["current_revision_id"] == first_id
    assert revision_path.read_bytes() == immutable

    changed = copy.deepcopy(score)
    changed["visual_events"][1]["purpose"] = "Introduce the chapter clearly."
    second = call(project, "create_visual_score_revision", score=changed)
    assert second["current_revision_id"] != first_id
    assert revision_path.read_bytes() == immutable
    assert len(list((project / "work/podcast/visual-score/revisions").glob("*.json"))) == 2


def test_invalid_visual_score_is_atomic_and_must_match_density_camera_and_provenance(podcast_project):
    project, asset, episode_map = podcast_project
    episode_map_sha = install_episode_map(project, episode_map)
    score = score_for(asset, episode_map_sha, episode_map["transcript"]["sha256"])
    preview = project / "work/podcast/previews/opening.png"
    preview.parent.mkdir(parents=True)
    preview.write_bytes(b"representative preview")
    score["representative_previews"] = [
        {
            "chapter_id": "opening",
            "path": "work/podcast/previews/opening.png",
            "sha256": hashlib.sha256(preview.read_bytes()).hexdigest(),
        }
    ]
    first = call(project, "create_visual_score_revision", score=score)
    assert first["score"]["representative_previews"] == score["representative_previews"]
    pointer = project / "work/podcast/visual-score/current.json"
    previous_pointer = pointer.read_bytes()
    revisions_before = set((project / "work/podcast/visual-score/revisions").iterdir())

    for mutate in (
        lambda value: value.update(visual_density="illustrative"),
        lambda value: value["camera_policy"].update(default="camera_permitted"),
        lambda value: value["visual_events"][0].update(end_ms=4_001),
        lambda value: value["visual_events"][1].update(type="quote"),
        lambda value: value["visual_events"][-1].update(provenance=[{"kind": "none", "label": "No source"}]),
        lambda value: value.update(episode_map_sha256="f" * 64),
        lambda value: value["representative_previews"].append(copy.deepcopy(value["representative_previews"][0])),
        lambda value: value["representative_previews"][0].update(chapter_id="missing"),
        lambda value: value["representative_previews"][0].update(path="../outside.png"),
        lambda value: value["representative_previews"][0].update(path="work/podcast/previews/missing.png"),
        lambda value: value["representative_previews"][0].update(sha256="0" * 64),
    ):
        invalid = copy.deepcopy(score)
        mutate(invalid)
        with pytest.raises(ValueError):
            call(project, "create_visual_score_revision", score=invalid)
        assert pointer.read_bytes() == previous_pointer
        assert set((project / "work/podcast/visual-score/revisions").iterdir()) == revisions_before
    assert call(project, "podcast_visual_score")["current_revision_id"] == first["current_revision_id"]


def test_owner_decisions_are_append_only_exact_and_gate_stage_materialization(podcast_project, monkeypatch):
    project, asset, episode_map = podcast_project
    episode_map_sha = install_episode_map(project, episode_map)
    score = score_for(asset, episode_map_sha, episode_map["transcript"]["sha256"])
    state = call(project, "create_visual_score_revision", score=score)
    revision_id = state["current_revision_id"]

    stage_path = project / "work/podcast/stage.json"
    stage = {
        "schema_version": 1,
        "primary_audio": score["primary_audio"],
        "render": {"fps": 30, "width": 1920, "height": 1080},
        "identity": {"show_title": "Show", "episode_title": "Episode", "speaker_name": "Speaker"},
        "waveform": {"sample_period_ms": 1000, "normalization": "peak-rms-v1", "values": [0, 0, 0, 0]},
        "chapters": [{"id": "episode", "title": "Episode", "start_ms": 0, "end_ms": 4_000}],
        "motion": "standard",
    }
    stage_path.write_text(json.dumps(stage))
    original_stage = stage_path.read_bytes()
    original_media = Path(asset["path"]).read_bytes()

    for bad in (
        {"revision_id": "0" * 64, "event_id": "chapter-1", "action": "accept", "owner_action": True},
        {"revision_id": revision_id, "event_id": "missing", "action": "accept", "owner_action": True},
        {"revision_id": revision_id, "event_id": "chapter-1", "action": "accept", "owner_action": False},
        {"revision_id": revision_id, "event_id": "image-1", "action": "accept", "owner_action": True},
    ):
        with pytest.raises(ValueError):
            call(project, "append_visual_score_decision", note="Owner review", **bad)

    call(
        project,
        "append_visual_score_decision",
        revision_id=revision_id,
        event_id="chapter-1",
        action="accept",
        note="Use the chapter reset",
        owner_action=True,
    )
    first_log = json.loads((project / "work/podcast/visual-score/decisions.json").read_text())
    call(
        project,
        "append_visual_score_decision",
        revision_id=revision_id,
        event_id="quote-1",
        action="use_base",
        note="Keep this passage quiet",
        owner_action=True,
    )
    second_log = json.loads((project / "work/podcast/visual-score/decisions.json").read_text())
    assert second_log["decisions"][:1] == first_log["decisions"]
    assert len(second_log["decisions"]) == 2

    reviewed = call(project, "materialize_reviewed_podcast_stage")
    reviewed_path = Path(reviewed["path"])
    derived = json.loads(reviewed_path.read_text())
    from tools.podcast_stage import validate_contract

    assert validate_contract(derived) == derived
    assert [event["type"] for event in derived["visual_events"]] == ["chapter_card", "base"]
    assert derived["visual_events"][1]["id"] == "quote-1"
    assert derived["visual_score_revision_id"] == revision_id
    assert stage_path.read_bytes() == original_stage
    assert Path(asset["path"]).read_bytes() == original_media

    malformed = copy.deepcopy(derived)
    malformed["visual_events"][0]["purpose"] = "   "
    with pytest.raises(ValueError):
        validate_contract(malformed)

    unreviewed = copy.deepcopy(derived)
    unreviewed["visual_events"].append(score["visual_events"][3])
    assert validate_contract(unreviewed) == unreviewed
    reviewed_path.write_text(json.dumps(unreviewed))
    from tools import podcast_stage

    monkeypatch.setattr(
        podcast_stage,
        "run_renderer",
        lambda *_args, **_kwargs: pytest.fail("renderer must not start for an unreviewed event"),
    )
    with pytest.raises(ValueError, match="unaccepted"):
        podcast_stage.render(project, reviewed_path)


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[1] / "remotion/node_modules/@remotion/renderer").exists(),
    reason="Remotion dependencies are not installed in this checkout",
)
def test_reviewed_visual_score_renders_only_explicitly_accepted_event(podcast_project):
    project, asset, episode_map = podcast_project
    episode_map_sha = install_episode_map(project, episode_map)
    score = score_for(asset, episode_map_sha, episode_map["transcript"]["sha256"])
    state = call(project, "create_visual_score_revision", score=score)
    revision_id = state["current_revision_id"]
    call(
        project,
        "append_visual_score_decision",
        revision_id=revision_id,
        event_id="chapter-1",
        action="accept",
        note="Use the chapter reset in the proof render",
        owner_action=True,
    )

    from tools.podcast_stage import prepare, render

    prepare(
        project,
        asset["id"],
        {"show_title": "Show", "episode_title": "Episode", "speaker_name": "Speaker"},
        width=320,
        height=180,
        sample_period_ms=1_000,
        motion="reduced",
    )
    reviewed = call(project, "materialize_reviewed_podcast_stage")
    reviewed_contract = json.loads(Path(reviewed["path"]).read_text())
    assert [event["id"] for event in reviewed_contract["visual_events"]] == ["chapter-1"]

    output = render(project, Path(reviewed["path"]), project / "output/reviewed-proof.mp4")
    probe = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(output)],
            text=True,
        )
    )
    assert {stream["codec_type"] for stream in probe["streams"]} >= {"audio", "video"}
    assert abs(float(probe["format"]["duration"]) - 4) <= 1 / 30 + 0.04


def test_old_revision_decisions_never_accept_events_in_current_revision(podcast_project):
    project, asset, episode_map = podcast_project
    episode_map_sha = install_episode_map(project, episode_map)
    score = score_for(asset, episode_map_sha, episode_map["transcript"]["sha256"])
    first = call(project, "create_visual_score_revision", score=score)
    call(
        project,
        "append_visual_score_decision",
        revision_id=first["current_revision_id"],
        event_id="chapter-1",
        action="accept",
        note="Accepted first draft",
        owner_action=True,
    )

    changed = copy.deepcopy(score)
    changed["visual_events"][1]["purpose"] = "Revised purpose"
    second = call(project, "create_visual_score_revision", score=changed)
    assert second["event_decisions"]["chapter-1"]["status"] == "unreviewed"
    with pytest.raises(ValueError, match="current revision"):
        call(
            project,
            "append_visual_score_decision",
            revision_id=first["current_revision_id"],
            event_id="chapter-1",
            action="accept",
            note="Stale click",
            owner_action=True,
        )


def test_score_camera_policy_binds_optional_configured_video(podcast_project, tmp_path):
    project, asset, episode_map = podcast_project
    camera_path = tmp_path / "camera.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
            "color=black:s=32x32:r=10:d=4", "-an", str(camera_path),
        ],
        check=True,
    )
    camera = call(project, "import_media", path=str(camera_path), role="source")["assets"][1]
    configured = call(project, "set_podcast_settings", camera_asset_id=camera["id"])
    episode_map["podcast_settings_revision"] = configured["podcast_settings_revision"]
    episode_map_sha = install_episode_map(project, episode_map)
    score = score_for(asset, episode_map_sha, episode_map["transcript"]["sha256"])
    score["podcast_settings_revision"] = configured["podcast_settings_revision"]
    score["camera_policy"] = {"configured_asset_id": camera["id"], "default": "camera_permitted"}
    score["visual_events"][1]["camera_policy"] = "camera_permitted"
    state = call(project, "create_visual_score_revision", score=score)
    assert state["binding_current"] is True

    invalid = copy.deepcopy(score)
    invalid["camera_policy"]["configured_asset_id"] = "missing"
    with pytest.raises(ValueError, match="camera policy"):
        call(project, "create_visual_score_revision", score=invalid)


def test_visual_score_bridge_preserves_unknown_project_state(podcast_project):
    project, _asset, episode_map = podcast_project
    project_path = project / "work/studio/project.json"
    project_state = json.loads(project_path.read_text())
    project_state["future_extension"] = {"kept": True}
    project_path.write_text(json.dumps(project_state))
    install_episode_map(project, episode_map)
    assert call(project, "open")["future_extension"] == {"kept": True}
