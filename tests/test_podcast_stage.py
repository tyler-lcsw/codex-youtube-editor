import json
import io
import math
from pathlib import Path
import subprocess
import wave

import pytest


def write_audio(path: Path, seconds: int = 4, rate: int = 8_000) -> Path:
    """Alternating one-second silence/tone fixture."""
    samples = []
    for index in range(seconds * rate):
        second = index // rate
        value = 0 if second % 2 == 0 else round(12_000 * math.sin(2 * math.pi * 440 * index / rate))
        samples.append(int(value).to_bytes(2, "little", signed=True))
    with wave.open(str(path), "wb") as stream:
        stream.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        stream.writeframes(b"".join(samples))
    return path


def valid_contract():
    return {
        "schema_version": 1,
        "primary_audio": {
            "asset_id": "audio-1",
            "sha256": "a" * 64,
            "duration_ms": 4_000,
        },
        "render": {"fps": 30, "width": 1920, "height": 1080},
        "identity": {
            "show_title": "The Example Show",
            "episode_title": "A Useful Episode",
            "speaker_name": "Example Speaker",
        },
        "waveform": {
            "sample_period_ms": 50,
            "normalization": "peak-rms-v1",
            "values": ([0, 0.5, 1, 0.5] * 20),
        },
        "chapters": [
            {"id": "opening", "title": "Opening", "start_ms": 0, "end_ms": 2_000},
            {"id": "close", "title": "Close", "start_ms": 2_000, "end_ms": 4_000},
        ],
        "motion": "standard",
    }


def test_contract_accepts_v1_and_rejects_invalid_values_and_chapter_order():
    from tools.podcast_stage import validate_contract

    assert validate_contract(valid_contract()) == valid_contract()
    for mutate in (
        lambda value: value["waveform"]["values"].append(1.01),
        lambda value: value["waveform"]["values"].append(float("nan")),
        lambda value: value.update(motion="busy"),
        lambda value: value["chapters"].append(
            {"id": "backwards", "title": "Backwards", "start_ms": 1_000, "end_ms": 1_500}
        ),
        lambda value: value["primary_audio"].update(duration_ms=0),
        lambda value: value["waveform"].update(values=[0, 1]),
        lambda value: value.update(chapters=[]),
        lambda value: value["identity"].update(show_title="   "),
        lambda value: value["identity"].update(artwork={"path": "../outside.png", "sha256": "b" * 64}),
    ):
        candidate = valid_contract()
        mutate(candidate)
        with pytest.raises(ValueError):
            validate_contract(candidate)


def test_streamed_waveform_is_bounded_deterministic_and_tracks_silence(tmp_path):
    from tools.podcast_stage import extract_waveform

    source = write_audio(tmp_path / "source.wav")
    first = extract_waveform(source, sample_period_ms=50)
    second = extract_waveform(source, sample_period_ms=50)
    assert first == second
    assert 75 <= len(first) <= 81
    assert all(math.isfinite(value) and 0 <= value <= 1 for value in first)
    # Ignore the resampler's bounded transition ringing at the tone boundary.
    assert max(first[:18]) < 0.02
    assert max(first[20:40]) > 0.8
    assert max(first[42:58]) < 0.02


def test_waveform_error_output_cannot_fill_a_pipe(tmp_path, monkeypatch):
    from tools import podcast_stage

    class FailedProcess:
        stdout = io.BytesIO(b"")

        def wait(self, timeout=None):
            assert timeout == 60
            return 1

        def poll(self):
            return 1

    def fake_popen(_command, *, stdout, stderr):
        assert stdout is subprocess.PIPE
        assert stderr is not subprocess.PIPE
        stderr.write(b"decode error\n" * 100_000)
        return FailedProcess()

    monkeypatch.setattr(podcast_stage.subprocess, "Popen", fake_popen)
    with pytest.raises(RuntimeError, match="decode error") as raised:
        podcast_stage.extract_waveform(tmp_path / "damaged.wav")
    assert len(str(raised.value)) <= 2100


def test_waveform_reader_failure_terminates_and_reaps_ffmpeg(tmp_path, monkeypatch):
    from tools import podcast_stage

    class BrokenStdout:
        def read(self, _size):
            raise OSError("read failed")

    class RunningProcess:
        stdout = BrokenStdout()
        terminated = False
        reaped = False

        def poll(self):
            return None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            assert self.terminated and timeout == 5
            self.reaped = True
            return 1

    process = RunningProcess()
    monkeypatch.setattr(podcast_stage.subprocess, "Popen", lambda *_args, **_kwargs: process)
    with pytest.raises(OSError, match="read failed"):
        podcast_stage.extract_waveform(tmp_path / "damaged.wav")
    assert process.reaped


def test_prepare_binds_exact_studio_asset_and_reuses_waveform_cache(tmp_path, monkeypatch):
    from tools.studio import dispatch
    from tools import podcast_stage

    project = tmp_path / "project"
    dispatch({"method": "create", "project": str(project), "params": {"title": "Podcast"}})
    source = write_audio(tmp_path / "source.wav")
    state = dispatch(
        {"method": "import_media", "project": str(project), "params": {"path": str(source), "role": "source"}}
    )
    asset = state["assets"][0]
    identity = {"show_title": "Show", "episode_title": "Episode", "speaker_name": "Speaker"}

    contract_path = podcast_stage.prepare(project, asset["id"], identity, sample_period_ms=50)
    contract = json.loads(contract_path.read_text())
    assert contract["primary_audio"] == {
        "asset_id": asset["id"],
        "sha256": asset["sha256"],
        "duration_ms": asset["duration_ms"],
    }
    assert contract["waveform"]["values"]

    monkeypatch.setattr(
        podcast_stage,
        "extract_waveform",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("cache was not reused")),
    )
    assert podcast_stage.prepare(project, asset["id"], identity, sample_period_ms=50) == contract_path

    media_root = tmp_path / "media"
    artwork = media_root / "projects/show/artwork.png"
    artwork.parent.mkdir(parents=True)
    artwork.write_bytes(b"artwork")
    monkeypatch.setattr(podcast_stage, "MEDIA_ROOT", media_root)
    with pytest.raises(ValueError, match="artwork changed"):
        podcast_stage.prepare(
            project,
            asset["id"],
            identity | {"artwork": {"path": "projects/show/artwork.png", "sha256": "b" * 64}},
            sample_period_ms=50,
        )

    Path(asset["path"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        podcast_stage.prepare(project, asset["id"], identity, sample_period_ms=50)


def test_prepare_defaults_to_configured_solo_podcast_audio(tmp_path):
    from tools.studio import dispatch
    from tools.podcast_stage import prepare

    project = tmp_path / "project"
    dispatch({"method": "create", "project": str(project), "params": {"title": "Podcast"}})
    source = write_audio(tmp_path / "source.wav")
    state = dispatch(
        {"method": "import_media", "project": str(project), "params": {"path": str(source), "role": "source"}}
    )
    asset = state["assets"][0]
    identity = {"show_title": "Show", "episode_title": "Episode", "speaker_name": "Speaker"}

    with pytest.raises(ValueError, match="Configure Solo podcast visuals"):
        prepare(project, None, identity)

    dispatch(
        {
            "method": "set_podcast_settings",
            "project": str(project),
            "params": {"primary_audio_asset_id": asset["id"]},
        }
    )
    contract = json.loads(prepare(project, None, identity).read_text())
    assert contract["primary_audio"]["asset_id"] == asset["id"]


def test_prepare_rejects_media_without_audio(tmp_path):
    from tools.studio import dispatch
    from tools.podcast_stage import prepare

    project = tmp_path / "project"
    dispatch({"method": "create", "project": str(project), "params": {"title": "Podcast"}})
    video = tmp_path / "video.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
            "color=black:s=32x32:r=10:d=1", "-an", str(video),
        ],
        check=True,
    )
    state = dispatch(
        {"method": "import_media", "project": str(project), "params": {"path": str(video), "role": "source"}}
    )
    identity = {"show_title": "Show", "episode_title": "Episode", "speaker_name": "Speaker"}
    with pytest.raises(ValueError, match="audio stream"):
        prepare(project, state["assets"][0]["id"], identity)


def test_render_failure_preserves_previous_output(tmp_path, monkeypatch):
    from tools import podcast_stage

    project = tmp_path / "project"
    (project / "work/podcast").mkdir(parents=True)
    (project / "output").mkdir()
    contract = valid_contract()
    contract_path = project / "work/podcast/stage.json"
    contract_path.write_text(json.dumps(contract))
    source = write_audio(project / "source.wav")
    output = project / "output/podcast-stage.mp4"
    output.write_bytes(b"previous success")

    monkeypatch.setattr(podcast_stage, "resolve_audio", lambda *_args: source)
    monkeypatch.setattr(
        podcast_stage,
        "run_renderer",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("render failed")),
    )
    with pytest.raises(RuntimeError, match="render failed"):
        podcast_stage.render(project, contract_path, output)
    assert output.read_bytes() == b"previous success"


@pytest.mark.skipif(
    not (Path(__file__).resolve().parents[1] / "remotion/node_modules/@remotion/renderer").exists(),
    reason="Remotion dependencies are not installed in this checkout",
)
def test_short_stage_render_has_audio_video_and_bounded_duration(tmp_path):
    from tools.studio import dispatch
    from tools.podcast_stage import prepare, render

    project = tmp_path / "project"
    dispatch({"method": "create", "project": str(project), "params": {"title": "Podcast"}})
    source = write_audio(tmp_path / "source.wav", seconds=3)
    state = dispatch(
        {"method": "import_media", "project": str(project), "params": {"path": str(source), "role": "source"}}
    )
    contract_path = prepare(
        project,
        state["assets"][0]["id"],
        {"show_title": "Show", "episode_title": "Episode", "speaker_name": "Speaker"},
        width=320,
        height=180,
    )
    output = render(project, contract_path)
    probe = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(output)],
            text=True,
        )
    )
    assert {stream["codec_type"] for stream in probe["streams"]} >= {"audio", "video"}
    assert abs(float(probe["format"]["duration"]) - 3) <= 1 / 30 + 0.04
    assert json.loads((project / "work/podcast/render.json").read_text())["output_sha256"]
