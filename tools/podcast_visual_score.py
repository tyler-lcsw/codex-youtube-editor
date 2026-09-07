"""Validate and persist semantic podcast maps and owner-reviewed visual scores.

This module only writes JSON planning/review artifacts. It never edits source
media, invokes a renderer, or replaces the canonical podcast stage descriptor.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import uuid

from jsonschema import Draft202012Validator

from .jobs import file_hash
from .run_state import atomic_json
from . import studio_project
from .podcast_stage import MEDIA_ROOT, validate_contract as validate_stage_contract


ROOT = Path(__file__).resolve().parents[1]
EPISODE_MAP_SCHEMA = ROOT / "schemas/podcast-episode-map.schema.json"
VISUAL_SCORE_SCHEMA = ROOT / "schemas/podcast-visual-score.schema.json"
EPISODE_MAP_PATH = Path("work/podcast/episode-map.json")
SCORE_ROOT = Path("work/podcast/visual-score")
DECISIONS_PATH = SCORE_ROOT / "decisions.json"
CURRENT_PATH = SCORE_ROOT / "current.json"
REVIEWED_STAGE_PATH = Path("work/podcast/stage-reviewed.json")
DECISION_ACTIONS = {"accept", "reject", "request_changes", "use_base"}


def _json_hash(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _validate_schema(value: dict, path: Path, label: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{label} requires finite JSON values") from error
    schema = json.loads(path.read_text())
    error = next(iter(Draft202012Validator(schema).iter_errors(value)), None)
    if error:
        location = ".".join(map(str, error.absolute_path)) or "contract"
        raise ValueError(f"Invalid {label} at {location}: {error.message}")


def _require_text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")
    return value


def _audio_binding(data: dict) -> tuple[dict, dict]:
    podcast = data.get("podcast")
    if not isinstance(podcast, dict) or podcast.get("schema_version") != 1 or podcast.get("kind") != "solo_audio_first":
        raise ValueError("Configure Solo podcast visuals before creating semantic artifacts")
    asset = studio_project.source_asset_by_id(data, podcast.get("primary_audio_asset_id"))
    if "audio" not in asset["stream_types"] or not isinstance(asset.get("duration_ms"), int) or asset["duration_ms"] <= 0:
        raise ValueError("Configured primary podcast source must contain bounded audio")
    binding = {"asset_id": asset["id"], "sha256": asset["sha256"], "duration_ms": asset["duration_ms"]}
    return podcast, binding


def _validate_anchor(anchor: dict, start_ms: int, end_ms: int, label: str) -> None:
    _require_text(anchor["text"], f"{label} text")
    if anchor["end_ms"] <= anchor["start_ms"]:
        raise ValueError(f"{label} must have positive duration")
    if anchor["start_ms"] < start_ms or anchor["end_ms"] > end_ms:
        raise ValueError(f"{label} must remain inside its chapter")


def validate_episode_map(project: Path, data: dict, value: dict) -> dict:
    """Validate an episode map against current Studio source and transcript bytes."""
    _validate_schema(value, EPISODE_MAP_SCHEMA, "podcast episode map")
    _podcast, audio = _audio_binding(data)
    if value["podcast_settings_revision"] != data.get("podcast_settings_revision"):
        raise ValueError("Episode map does not match current podcast settings revision")
    if value["primary_audio"] != audio:
        raise ValueError("Episode map does not match configured primary audio")

    relative = Path(value["transcript"]["path"])
    transcript = (project / relative).resolve()
    if not transcript.is_relative_to(project.resolve()) or not transcript.is_file():
        raise ValueError("Episode map transcript must be a project-local file")
    if file_hash(transcript) != value["transcript"]["sha256"]:
        raise ValueError("Episode map transcript changed after analysis")

    duration = audio["duration_ms"]
    previous_end = 0
    chapter_ids: set[str] = set()
    moment_ids: set[str] = set()
    for chapter in value["chapters"]:
        _require_text(chapter["id"], "Chapter ID")
        _require_text(chapter["title"], "Chapter title")
        if chapter["id"] in chapter_ids:
            raise ValueError("Episode map chapter IDs must be unique")
        chapter_ids.add(chapter["id"])
        if chapter["start_ms"] < previous_end or chapter["end_ms"] <= chapter["start_ms"]:
            raise ValueError("Episode map chapters must be ordered and non-overlapping")
        if chapter["end_ms"] > duration:
            raise ValueError("Episode map chapter exceeds primary audio duration")
        _validate_anchor(
            chapter["transcript_anchor"], chapter["start_ms"], chapter["end_ms"], "Chapter transcript anchor"
        )
        for moment in chapter["moments"]:
            _require_text(moment["id"], "Semantic moment ID")
            _require_text(moment["summary"], "Semantic moment summary")
            if moment["id"] in moment_ids:
                raise ValueError("Episode map semantic moment IDs must be unique")
            moment_ids.add(moment["id"])
            _validate_anchor(
                moment["transcript_anchor"], chapter["start_ms"], chapter["end_ms"], "Moment transcript anchor"
            )
        previous_end = chapter["end_ms"]
    return value


def _episode_map(project: Path, data: dict, *, require_current: bool = True) -> tuple[dict, str]:
    path = project / EPISODE_MAP_PATH
    if not path.is_file():
        raise ValueError("Create an episode map before creating a visual score")
    value = json.loads(path.read_text())
    if require_current:
        validate_episode_map(project, data, value)
    return value, file_hash(path)


def set_episode_map(project: Path, data: dict, value: dict) -> dict:
    validate_episode_map(project, data, value)
    # Surface corrupt related review state before publishing a valid new map.
    # That keeps a failed bridge request free of partial planning changes.
    visual_score_state(project, data)
    atomic_json(project / EPISODE_MAP_PATH, value)
    return visual_score_state(project, data)


def _validate_provenance(project: Path, data: dict, episode_map: dict, event: dict) -> None:
    for source in event["provenance"]:
        _require_text(source["label"], "Visual provenance label")
        kind = source["kind"]
        if kind == "transcript":
            if source.get("sha256") != episode_map["transcript"]["sha256"]:
                raise ValueError("Transcript provenance must bind the current episode-map transcript")
        elif kind == "project_asset":
            asset_id = source.get("asset_id")
            asset = studio_project.asset_by_id(data, asset_id)
            if source.get("sha256") != asset["sha256"]:
                raise ValueError("Project-asset provenance must bind exact imported bytes")
        elif kind == "project_resource":
            url = source.get("resource_url")
            if not any(item.get("url") == url for item in data.get("resources", [])):
                raise ValueError("Project-resource provenance must reference a saved resource URL")
        elif kind == "local_generation":
            if not source.get("sha256"):
                raise ValueError("Local-generation provenance requires an output hash")
        elif kind == "none" and event["type"] != "base":
            raise ValueError("Custom visual events require source provenance")
    if event["type"] != "base" and all(item["kind"] == "none" for item in event["provenance"]):
        raise ValueError("Custom visual events require source provenance")

    asset = event["treatment"].get("asset")
    if asset is not None:
        source = (MEDIA_ROOT / asset["path"]).resolve()
        if not source.is_relative_to(MEDIA_ROOT.resolve()) or not source.is_file():
            raise ValueError("Visual score image asset must be a file in the Remotion media root")
        if file_hash(source) != asset["sha256"]:
            raise ValueError("Visual score image asset changed after selection")


def validate_visual_score(project: Path, data: dict, value: dict) -> dict:
    """Validate a complete immutable score revision against current project state."""
    _validate_schema(value, VISUAL_SCORE_SCHEMA, "podcast visual score")
    podcast, audio = _audio_binding(data)
    if value["podcast_settings_revision"] != data.get("podcast_settings_revision"):
        raise ValueError("Visual score does not match current podcast settings revision")
    if value["primary_audio"] != audio:
        raise ValueError("Visual score does not match configured primary audio")
    episode_map, episode_map_sha = _episode_map(project, data)
    if value["episode_map_sha256"] != episode_map_sha:
        raise ValueError("Visual score does not match the current episode map")
    if value["visual_density"] != podcast.get("visual_density", "balanced"):
        raise ValueError("Visual score density does not match the configured preference")

    configured_camera = podcast.get("camera_asset_id")
    camera = value["camera_policy"]
    if camera["configured_asset_id"] != configured_camera:
        raise ValueError("Visual score camera policy does not match configured podcast camera")
    if configured_camera is not None:
        camera_asset = studio_project.source_asset_by_id(data, configured_camera)
        if "video" not in camera_asset["stream_types"]:
            raise ValueError("Configured podcast camera must contain video")
    elif camera["default"] != "base_only":
        raise ValueError("Camera cannot be permitted when no podcast camera is configured")

    duration = audio["duration_ms"]
    chapters = {chapter["id"]: chapter for chapter in episode_map["chapters"]}
    event_ids: set[str] = set()
    for event in value["visual_events"]:
        _require_text(event["id"], "Visual event ID")
        _require_text(event["purpose"], "Visual event purpose")
        if event["id"] in event_ids:
            raise ValueError("Visual event IDs must be unique")
        event_ids.add(event["id"])
        if event["end_ms"] <= event["start_ms"] or event["end_ms"] > duration:
            raise ValueError("Visual event timing must remain inside primary audio")
        chapter = chapters.get(event["chapter_id"])
        if chapter is None or event["start_ms"] < chapter["start_ms"] or event["end_ms"] > chapter["end_ms"]:
            raise ValueError("Visual event timing must remain inside its episode-map chapter")
        _validate_anchor(
            event["transcript_anchor"], chapter["start_ms"], chapter["end_ms"], "Visual event transcript anchor"
        )
        if event["treatment"]["kind"] != event["type"]:
            raise ValueError("Visual event type must match its treatment")
        if event["type"] == "base" and event["camera_policy"] != "base_only":
            raise ValueError("An unchanged base-stage event cannot permit camera")
        if configured_camera is None and event["camera_policy"] != "base_only":
            raise ValueError("Visual event cannot permit an unavailable camera")
        _validate_provenance(project, data, episode_map, event)
    preview_chapters: set[str] = set()
    for preview in value.get("representative_previews", []):
        chapter_id = _require_text(preview["chapter_id"], "Representative preview chapter ID")
        if chapter_id not in chapters:
            raise ValueError("Representative preview must reference an existing episode-map chapter")
        if chapter_id in preview_chapters:
            raise ValueError("Representative previews must identify unique chapters")
        preview_chapters.add(chapter_id)
        relative = Path(preview["path"])
        source = (project / relative).resolve()
        if not source.is_relative_to(project.resolve()) or not source.is_file():
            raise ValueError("Representative preview must be a project-local file")
        if file_hash(source) != preview["sha256"]:
            raise ValueError("Representative preview changed after selection")
    return value


def _revision_path(project: Path, revision_id: str) -> Path:
    return project / SCORE_ROOT / "revisions" / f"{revision_id}.json"


def create_visual_score_revision(project: Path, data: dict, score: dict) -> dict:
    if not isinstance(score, dict) or "revision_id" in score:
        raise ValueError("New visual-score content must omit revision_id")
    revision_id = _json_hash(score)
    revision = deepcopy(score)
    revision["revision_id"] = revision_id
    validate_visual_score(project, data, revision)
    _load_current_score(project)
    _read_decisions(project)
    path = _revision_path(project, revision_id)
    if path.exists():
        existing = json.loads(path.read_text())
        if existing != revision:
            raise ValueError("Existing visual-score revision does not match its content hash")
    else:
        atomic_json(path, revision)
    atomic_json(project / CURRENT_PATH, {"schema_version": 1, "revision_id": revision_id})
    return visual_score_state(project, data)


def _load_current_score(project: Path) -> tuple[str, dict] | tuple[None, None]:
    pointer_path = project / CURRENT_PATH
    if not pointer_path.is_file():
        return None, None
    pointer = json.loads(pointer_path.read_text())
    if set(pointer) != {"schema_version", "revision_id"} or pointer.get("schema_version") != 1:
        raise ValueError("Unsupported current visual-score pointer")
    revision_id = pointer.get("revision_id")
    if not isinstance(revision_id, str) or re.fullmatch(r"[0-9a-f]{64}", revision_id) is None:
        raise ValueError("Invalid current visual-score revision")
    path = _revision_path(project, revision_id)
    if not path.is_file():
        raise ValueError("Current visual-score revision is missing")
    revision = json.loads(path.read_text())
    body = {key: value for key, value in revision.items() if key != "revision_id"}
    if revision.get("revision_id") != revision_id or _json_hash(body) != revision_id:
        raise ValueError("Visual-score revision content changed after creation")
    return revision_id, revision


def _read_decisions(project: Path) -> dict:
    path = project / DECISIONS_PATH
    if not path.is_file():
        return {"schema_version": 1, "decisions": []}
    value = json.loads(path.read_text())
    if not isinstance(value, dict) or set(value) != {"schema_version", "decisions"}:
        raise ValueError("Invalid visual-score decision log")
    if value["schema_version"] != 1 or not isinstance(value["decisions"], list):
        raise ValueError("Unsupported visual-score decision log")
    for item in value["decisions"]:
        if (
            not isinstance(item, dict)
            or set(item) != {"id", "revision_id", "event_id", "action", "note", "decided_at", "owner_action"}
            or item.get("action") not in DECISION_ACTIONS
            or item.get("owner_action") is not True
        ):
            raise ValueError("Invalid visual-score owner decision")
        for key in ("id", "revision_id", "event_id", "note", "decided_at"):
            _require_text(item.get(key), f"Decision {key}")
    return value


def _latest_decisions(score: dict, decisions: list[dict]) -> dict[str, dict]:
    latest = {}
    for decision in decisions:
        if decision["revision_id"] == score["revision_id"]:
            latest[decision["event_id"]] = decision
    return latest


def _reviewed_events(score: dict, decisions: list[dict]) -> list[dict]:
    latest = _latest_decisions(score, decisions)
    accepted = []
    for event in score["visual_events"]:
        decision = latest.get(event["id"])
        if decision is None or decision["action"] not in {"accept", "use_base"}:
            continue
        materialized = deepcopy(event)
        if decision["action"] == "use_base":
            materialized["type"] = "base"
            materialized["treatment"] = {"kind": "base"}
            materialized["camera_policy"] = "base_only"
        accepted.append(materialized)
    return accepted


def visual_score_state(project: Path, data: dict) -> dict:
    episode_map = None
    episode_map_sha = None
    episode_path = project / EPISODE_MAP_PATH
    if episode_path.is_file():
        episode_map = json.loads(episode_path.read_text())
        episode_map_sha = file_hash(episode_path)
    revision_id, score = _load_current_score(project)
    decision_log = _read_decisions(project)
    current_decisions = [] if score is None else [
        item for item in decision_log["decisions"] if item["revision_id"] == revision_id
    ]
    event_decisions = {}
    binding_current = False
    if score is not None:
        try:
            validate_visual_score(project, data, score)
            binding_current = True
        except ValueError:
            binding_current = False
        latest = _latest_decisions(score, current_decisions)
        statuses = {
            "accept": "accepted",
            "reject": "rejected",
            "request_changes": "changes_requested",
            "use_base": "base",
        }
        for event in score["visual_events"]:
            decision = latest.get(event["id"])
            event_decisions[event["id"]] = {
                "status": statuses[decision["action"]] if decision else "unreviewed",
                "decision": decision,
            }
    return {
        "episode_map": episode_map,
        "episode_map_sha256": episode_map_sha,
        "current_revision_id": revision_id,
        "score": score,
        "binding_current": binding_current,
        "decisions": current_decisions,
        "event_decisions": event_decisions,
    }


def append_owner_decision(project: Path, data: dict, params: dict) -> dict:
    revision_id, score = _load_current_score(project)
    if score is None or params.get("revision_id") != revision_id:
        raise ValueError("Owner decisions must target the exact current revision")
    validate_visual_score(project, data, score)
    event_id = params.get("event_id")
    if not any(event["id"] == event_id for event in score["visual_events"]):
        raise ValueError("Owner decision must target an event in the current revision")
    if params.get("owner_action") is not True:
        raise ValueError("Visual-score decisions require an explicit owner action")
    action = params.get("action")
    if action not in DECISION_ACTIONS:
        raise ValueError("Unsupported visual-score owner decision")
    event = next(event for event in score["visual_events"] if event["id"] == event_id)
    if action == "accept" and event["type"] == "image_source" and event["treatment"].get("asset") is None:
        raise ValueError("An image/source card requires a hash-bound asset before owner acceptance")
    note = _require_text(params.get("note"), "Owner decision note").strip()
    log = _read_decisions(project)
    log["decisions"].append(
        {
            "id": uuid.uuid4().hex,
            "revision_id": revision_id,
            "event_id": event_id,
            "action": action,
            "note": note,
            "decided_at": studio_project.now(),
            "owner_action": True,
        }
    )
    atomic_json(project / DECISIONS_PATH, log)
    return visual_score_state(project, data)


def materialize_reviewed_stage(project: Path, data: dict) -> dict:
    """Write an accepted-only derived stage descriptor without rendering media."""
    revision_id, score = _load_current_score(project)
    if score is None:
        raise ValueError("No current visual-score revision")
    validate_visual_score(project, data, score)
    stage_path = project / "work/podcast/stage.json"
    stage = validate_stage_contract(json.loads(stage_path.read_text()))
    if stage["primary_audio"] != score["primary_audio"]:
        raise ValueError("Podcast stage and visual score bind different primary audio")
    decisions = _read_decisions(project)["decisions"]
    accepted = _reviewed_events(score, decisions)
    derived = deepcopy(stage)
    derived["visual_score_revision_id"] = revision_id
    derived["visual_events"] = accepted
    target = project / REVIEWED_STAGE_PATH
    atomic_json(target, derived)
    return {"path": str(target), "visual_score_revision_id": revision_id, "visual_event_count": len(accepted)}


def validate_reviewed_stage(project: Path, data: dict, contract: dict) -> dict:
    """Prove every derived event is the latest explicit current-revision choice."""
    revision_id, score = _load_current_score(project)
    if score is None or contract.get("visual_score_revision_id") != revision_id:
        raise ValueError("Reviewed podcast stage does not bind the exact current visual-score revision")
    validate_visual_score(project, data, score)
    if contract.get("primary_audio") != score["primary_audio"]:
        raise ValueError("Reviewed podcast stage and visual score bind different primary audio")
    expected = _reviewed_events(score, _read_decisions(project)["decisions"])
    if contract.get("visual_events") != expected:
        raise ValueError("Reviewed podcast stage contains unaccepted or changed visual events")
    return contract
