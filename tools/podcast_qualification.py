"""Measure a reviewed long-form podcast render without claiming creative review.

The public ``qualify`` command always enters through the production-quality
coordinator. Its worker renders to scratch, fully probes and decodes that
candidate, then atomically publishes the output and canonical success report.
Failed and interrupted attempts retain their own reports while leaving the last
successful report and output unchanged.
"""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid

from jsonschema import Draft202012Validator

from .jobs import file_hash
from .run_state import atomic_json, file_lock
from .runtime.worker import terminate_group
from . import podcast_stage
from . import podcast_visual_score
from . import production_quality
from . import studio_project


ROOT = Path(__file__).resolve().parents[1]
REPORT_SCHEMA = ROOT / "schemas/podcast-qualification-report.schema.json"
REPORT_PATH = Path("work/podcast/qualification/report.json")
ATTEMPTS_PATH = Path("work/podcast/qualification/attempts")
DEFAULT_CONTRACT = Path("work/podcast/stage-reviewed.json")
DEFAULT_OUTPUT = Path("output/podcast-qualified.mp4")
QUALITY_RULES = ["R04", "R05", "R15", "R17", "R20", "R21", "R24", "R25", "R26", "R29"]
MIN_DURATION_MS = 25 * 60 * 1000
MAX_DURATION_MS = 45 * 60 * 1000
TARGET_FPS = 30
TARGET_WIDTH = 1920
TARGET_HEIGHT = 1080
DURATION_TOLERANCE_MS = 40
AUDIO_DURATION_TOLERANCE_MS = 100
FRAME_COUNT_TOLERANCE = 1
FPS_TOLERANCE = 0.001
MAX_QUALIFICATION_TIMEOUT_SECONDS = 86_400


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_report(value: dict) -> dict:
    if not isinstance(value, dict):
        raise ValueError("Podcast qualification report must be an object")
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("Podcast qualification report requires finite JSON values") from error
    schema = json.loads(REPORT_SCHEMA.read_text())
    error = next(iter(Draft202012Validator(schema).iter_errors(value)), None)
    if error:
        location = ".".join(map(str, error.absolute_path)) or "report"
        raise ValueError(f"Invalid podcast qualification report at {location}: {error.message}")
    if value["status"] == "succeeded":
        if (
            value["failure"] is not None
            or value["bindings"] is None
            or value["performance"] is None
            or value["delivery"] is None
            or value["decode"] is None
            or value["decode"].get("status") != "passed"
            or value["reviews"]["technical_validation"] != "passed"
            or value["bindings"]["reviewed_stage_current"] is not True
        ):
            raise ValueError("Successful qualification requires current technical evidence")
        kinds = {stream.get("type") for stream in value["delivery"].get("streams", [])}
        videos = [stream for stream in value["delivery"].get("streams", []) if stream.get("type") == "video"]
        if not {"audio", "video"} <= kinds or not videos or any(stream.get("frame_count", 0) <= 0 for stream in videos):
            raise ValueError("Successful qualification requires counted video frames and audio")
        target = value["bindings"]["qualification_target"]
        _validate_qualification_target(target)
        _validate_delivery_against_target(value["delivery"], target)
    elif value["failure"] is None or value["reviews"]["technical_validation"] != "failed":
        raise ValueError("Failed qualification attempts require a recorded technical failure")
    return value


def _validate_qualification_target(target: dict) -> dict:
    duration_ms = target.get("duration_ms")
    if not isinstance(duration_ms, int) or isinstance(duration_ms, bool) or not MIN_DURATION_MS <= duration_ms <= MAX_DURATION_MS:
        raise ValueError("Long-form qualification requires canonical audio between 25 and 45 minutes inclusive")
    if (target.get("width"), target.get("height")) != (TARGET_WIDTH, TARGET_HEIGHT):
        raise ValueError("Long-form qualification requires 1920x1080 rendering")
    if target.get("fps") != TARGET_FPS:
        raise ValueError("Long-form qualification requires 30 fps rendering")
    expected = math.ceil(duration_ms * TARGET_FPS / 1000)
    if target.get("expected_frame_count") != expected:
        raise ValueError("Long-form qualification frame target does not match canonical duration")
    expected_tolerances = {
        "duration_tolerance_ms": DURATION_TOLERANCE_MS,
        "audio_duration_tolerance_ms": AUDIO_DURATION_TOLERANCE_MS,
        "frame_count_tolerance": FRAME_COUNT_TOLERANCE,
        "fps_tolerance": FPS_TOLERANCE,
    }
    if any(target.get(key) != expected_value for key, expected_value in expected_tolerances.items()):
        raise ValueError("Long-form qualification tolerances do not match the versioned profile")
    return target


def _qualification_target(contract: dict) -> dict:
    duration_ms = contract.get("primary_audio", {}).get("duration_ms")
    render = contract.get("render", {})
    target = {
        "duration_ms": duration_ms,
        "fps": render.get("fps"),
        "width": render.get("width"),
        "height": render.get("height"),
        "expected_frame_count": (
            math.ceil(duration_ms * TARGET_FPS / 1000)
            if isinstance(duration_ms, int) and not isinstance(duration_ms, bool)
            else None
        ),
        "duration_tolerance_ms": DURATION_TOLERANCE_MS,
        "audio_duration_tolerance_ms": AUDIO_DURATION_TOLERANCE_MS,
        "frame_count_tolerance": FRAME_COUNT_TOLERANCE,
        "fps_tolerance": FPS_TOLERANCE,
    }
    return _validate_qualification_target(target)


def _validate_delivery_against_target(delivery: dict, target: dict) -> None:
    if abs(delivery.get("duration_ms", -1) - target["duration_ms"]) > target["duration_tolerance_ms"]:
        raise ValueError("Qualified delivery duration does not match the long-form contract")
    videos = [stream for stream in delivery.get("streams", []) if stream.get("type") == "video"]
    audios = [stream for stream in delivery.get("streams", []) if stream.get("type") == "audio"]
    if len(videos) != 1:
        raise ValueError("Qualified delivery requires exactly one canonical video stream")
    if len(audios) != 1:
        raise ValueError("Qualified delivery requires exactly one canonical audio stream")
    video = videos[0]
    if (video.get("width"), video.get("height")) != (target["width"], target["height"]):
        raise ValueError("Qualified delivery dimensions do not match the long-form contract")
    if abs(video.get("frame_count", -1) - target["expected_frame_count"]) > target["frame_count_tolerance"]:
        raise ValueError("Qualified delivery frame count does not match the long-form contract")
    try:
        frame_rate = float(Fraction(video.get("avg_frame_rate", "")))
    except (TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError("Qualified delivery has an invalid average frame rate") from error
    if not math.isfinite(frame_rate) or abs(frame_rate - target["fps"]) > target["fps_tolerance"]:
        raise ValueError("Qualified delivery frame rate does not match the long-form contract")
    audio_duration = audios[0].get("duration_ms", -1)
    audio_tolerance = target["audio_duration_tolerance_ms"]
    video_duration = video["frame_count"] / frame_rate * 1000
    if (
        abs(audio_duration - target["duration_ms"]) > audio_tolerance
        or abs(audio_duration - delivery["duration_ms"]) > audio_tolerance
        or abs(audio_duration - video_duration) > audio_tolerance
    ):
        raise ValueError("Qualified delivery audio duration does not match the canonical target, video, and container")


def _platform() -> dict:
    return {"system": platform.system(), "release": platform.release(), "machine": platform.machine()}


def _file_state(path: Path) -> dict | None:
    return {"path": str(path), "sha256": file_hash(path)} if path.is_file() else None


def _cache_snapshot(project: Path) -> list[dict]:
    entries = []
    for path in sorted((project / "work/podcast").glob("waveform-*.json")):
        if path.is_file():
            entries.append(
                {"path": str(path.relative_to(project)), "sha256": file_hash(path), "size_bytes": path.stat().st_size}
            )
    return entries


def _cache_report(before: list[dict], after: list[dict]) -> dict:
    old = {item["path"]: item for item in before}
    new = {item["path"]: item for item in after}
    return {
        "scope": "project_waveform_json",
        "before": before,
        "after": after,
        "reused": sorted(path for path in old.keys() & new.keys() if old[path] == new[path]),
        "created": sorted(new.keys() - old.keys()),
        "changed": sorted(path for path in old.keys() & new.keys() if old[path] != new[path]),
    }


def _input_binding(project: Path, contract_path: Path) -> dict:
    expected = (project / DEFAULT_CONTRACT).resolve()
    if contract_path.resolve() != expected:
        raise ValueError("Long-form qualification requires the configured reviewed podcast stage")
    data = studio_project.read(project)
    contract = podcast_stage.validate_contract(json.loads(contract_path.read_text()))
    podcast_visual_score.validate_reviewed_stage(project, data, contract)
    qualification_target = _qualification_target(contract)
    source = podcast_stage.resolve_audio(project, contract)
    return {
        "source": {"path": str(source), "sha256": file_hash(source)},
        "contract": {"path": str(contract_path), "sha256": file_hash(contract_path)},
        "visual_score_revision_id": contract["visual_score_revision_id"],
        "reviewed_stage_current": True,
        "qualification_target": qualification_target,
    }


def _worker_command(project: Path, contract: Path, output: Path, timeout: float) -> list[str]:
    return [
        sys.executable,
        "-m",
        "tools.podcast_qualification",
        "_worker",
        str(Path(project).resolve()),
        "--contract",
        str(Path(contract).resolve()),
        "--output",
        str(Path(output).resolve()),
        "--timeout",
        f"{float(timeout):.17g}",
    ]


def _qualification_timeout_seconds(value: float) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
        or value > MAX_QUALIFICATION_TIMEOUT_SECONDS
    ):
        raise ValueError("Qualification timeout must be between 0 and 86400 seconds")
    return value


def _require_running_quality_action(
    project: Path,
    expected_command: list[str],
    *,
    expected_id: str | None = None,
) -> str:
    matches = [
        action
        for action in production_quality.state(project).get("actions", [])
        if action.get("status") == "running"
        and action.get("command") == expected_command
        and (expected_id is None or action.get("id") == expected_id)
    ]
    if len(matches) != 1 or not isinstance(matches[0].get("id"), str):
        raise ValueError("Podcast qualification requires exactly one matching running production-quality action")
    return matches[0]["id"]


def _memory_pressure_percent() -> float | None:
    if sys.platform != "darwin" or shutil.which("memory_pressure") is None:
        return None
    try:
        result = subprocess.run(["memory_pressure", "-Q"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    match = re.search(r"System-wide memory free percentage:\s*([0-9.]+)%", result.stdout + result.stderr)
    return float(match.group(1)) if result.returncode == 0 and match else None


def _memory_pressure_level() -> int | None:
    if sys.platform != "darwin":
        return None
    try:
        result = subprocess.run(
            ["sysctl", "-n", "kern.memorystatus_vm_pressure_level"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        return int(result.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def _child_tree_rss_bytes(root_pid: int) -> int | None:
    if sys.platform != "darwin":
        return None
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid=,ppid=,rss="], capture_output=True, text=True, timeout=5, check=True
        )
        rows = [tuple(map(int, line.split())) for line in result.stdout.splitlines() if len(line.split()) == 3]
    except (OSError, ValueError, subprocess.SubprocessError):
        return None
    children: dict[int, list[int]] = {}
    rss = {}
    for pid, parent, rss_kib in rows:
        children.setdefault(parent, []).append(pid)
        rss[pid] = rss_kib * 1024
    pending = [root_pid]
    descendants = set()
    while pending:
        pid = pending.pop()
        if pid in descendants:
            continue
        descendants.add(pid)
        pending.extend(children.get(pid, []))
    return sum(rss.get(pid, 0) for pid in descendants)


def _run_measured(command: list[str], timeout: float) -> dict:
    started = time.monotonic()
    before_pressure = _memory_pressure_percent()
    before_level = _memory_pressure_level()
    pressure_samples = [before_pressure] if before_pressure is not None else []
    level_samples = [before_level] if before_level is not None else []
    peak_rss = None
    rss_samples = 0
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        next_rss = started
        next_pressure = started
        try:
            while process.poll() is None:
                current = time.monotonic()
                if current >= next_rss:
                    sample = _child_tree_rss_bytes(process.pid)
                    if sample is not None:
                        peak_rss = sample if peak_rss is None else max(peak_rss, sample)
                        rss_samples += 1
                    next_rss = current + 1
                if current >= next_pressure:
                    pressure = _memory_pressure_percent()
                    if pressure is not None:
                        pressure_samples.append(pressure)
                    level = _memory_pressure_level()
                    if level is not None:
                        level_samples.append(level)
                    next_pressure = current + 2
                if current - started > timeout:
                    raise subprocess.TimeoutExpired(command, timeout)
                time.sleep(0.25)
            code = process.wait()
        except BaseException as error:
            recovery = "not_needed"
            if process.poll() is None:
                try:
                    terminate_group(process)
                    recovery = "child_process_terminated" if process.poll() is not None else "child_process_termination_failed"
                except BaseException:
                    recovery = "child_process_termination_failed"
            try:
                error._podcast_qualification_recovery = recovery
            except (AttributeError, TypeError):
                pass
            raise
        if code:
            log.seek(0, os.SEEK_END)
            log.seek(max(0, log.tell() - 4000))
            tail = log.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Podcast qualification child failed ({code}): {tail}")
    after_pressure = _memory_pressure_percent()
    after_level = _memory_pressure_level()
    if after_pressure is not None:
        pressure_samples.append(after_pressure)
    if after_level is not None:
        level_samples.append(after_level)
    return {
        "wall_time_seconds": round(time.monotonic() - started, 3),
        "peak_child_tree_rss_bytes": peak_rss,
        "rss_sample_count": rss_samples,
        "memory_pressure": {
            "before_free_percent": before_pressure,
            "after_free_percent": after_pressure,
            "minimum_free_percent": min(pressure_samples) if pressure_samples else None,
            "before_level": before_level,
            "after_level": after_level,
            "peak_level": max(level_samples) if level_samples else None,
        },
    }


def inspect_delivery(path: Path) -> tuple[dict, dict]:
    """Count frames with ffprobe and fully decode audio and video to null."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode:
        raise RuntimeError("ffprobe failed: " + result.stderr[-2000:])
    info = json.loads(result.stdout)
    raw_streams = info.get("streams", [])
    if sum(stream.get("codec_type") == "video" for stream in raw_streams) != 1:
        raise ValueError("Qualified delivery requires exactly one video stream")
    if sum(stream.get("codec_type") == "audio" for stream in raw_streams) != 1:
        raise ValueError("Qualified delivery requires exactly one audio stream")
    streams = []
    for stream in raw_streams:
        kind = stream.get("codec_type")
        if kind == "video":
            raw_count = stream.get("nb_read_frames", stream.get("nb_frames"))
            try:
                frame_count = int(raw_count)
            except (TypeError, ValueError) as error:
                raise ValueError("ffprobe did not return a counted video frame total") from error
            streams.append(
                {
                    "type": "video",
                    "codec": stream.get("codec_name") or "unknown",
                    "frame_count": frame_count,
                    "width": int(stream.get("width", 0)),
                    "height": int(stream.get("height", 0)),
                    "avg_frame_rate": stream.get("avg_frame_rate") or "0/0",
                }
            )
        elif kind == "audio":
            duration_ms = _stream_duration_ms(stream)
            streams.append(
                {
                    "type": "audio",
                    "codec": stream.get("codec_name") or "unknown",
                    "duration_ms": duration_ms,
                    "sample_rate": int(stream.get("sample_rate", 0)),
                    "channels": int(stream.get("channels", 0)),
                }
            )
    kinds = {stream["type"] for stream in streams}
    if not {"audio", "video"} <= kinds:
        raise ValueError("Qualified delivery requires audio and video streams")
    try:
        duration_ms = round(float(info["format"]["duration"]) * 1000)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Qualified delivery has no finite duration") from error
    if duration_ms <= 0:
        raise ValueError("Qualified delivery has no finite duration")

    with tempfile.TemporaryFile() as errors:
        decode_result = subprocess.run(
            [
                "ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
                "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "-",
            ],
            stdout=subprocess.DEVNULL,
            stderr=errors,
        )
        errors.seek(0, os.SEEK_END)
        errors.seek(max(0, errors.tell() - 4000))
        tail = errors.read().decode("utf-8", errors="replace")
    decode = {"status": "passed" if decode_result.returncode == 0 else "failed", "exit_code": decode_result.returncode, "stderr_tail": tail}
    if decode_result.returncode:
        raise RuntimeError("Full delivery decode failed: " + tail)
    delivery = {
        "format_name": info.get("format", {}).get("format_name") or "unknown",
        "duration_ms": duration_ms,
        "size_bytes": path.stat().st_size,
        "streams": streams,
    }
    return delivery, decode


def _stream_duration_ms(stream: dict) -> int:
    raw_duration = stream.get("duration")
    try:
        seconds = float(raw_duration)
    except (TypeError, ValueError):
        seconds = math.nan
    if not math.isfinite(seconds) or seconds <= 0:
        try:
            seconds = float(Fraction(str(stream["duration_ts"])) * Fraction(stream["time_base"]))
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
            raise ValueError("ffprobe did not return a bounded audio stream duration") from error
    duration_ms = round(seconds * 1000)
    if not math.isfinite(seconds) or duration_ms <= 0:
        raise ValueError("ffprobe did not return a bounded audio stream duration")
    return duration_ms


def _execute(
    project: Path,
    contract: Path,
    output: Path,
    result_path: Path,
    *,
    quality_action_id: str,
    worker_output: Path,
    worker_timeout: float,
) -> None:
    expected_command = _worker_command(project, contract, worker_output, worker_timeout)
    _require_running_quality_action(project, expected_command, expected_id=quality_action_id)
    target = _qualification_target(podcast_stage.validate_contract(json.loads(contract.read_text())))
    podcast_stage.render(project, contract, output, record_receipt=False)
    delivery, decode = inspect_delivery(output)
    _validate_delivery_against_target(delivery, target)
    atomic_json(result_path, {"delivery": delivery, "decode": decode})


def _reviews(passed: bool) -> dict:
    return {
        "technical_validation": "passed" if passed else "failed",
        "visual_inspection": "pending",
        "normal_speed_listening": "pending",
        "owner_acceptance": "pending",
        "creative_acceptance": False,
    }


def _safety() -> dict:
    return {"network_invoked": False, "publication_invoked": False, "models_invoked": False}


def _same_file(path: Path, prior: dict | None) -> bool:
    return _file_state(path) == prior


def _publish_success(output: Path, staged: Path, report_path: Path, report: dict, scratch: Path) -> None:
    backup = scratch / "prior-output"
    had_output = output.is_file()
    if had_output:
        try:
            os.link(output, backup)
        except OSError:
            shutil.copyfile(output, backup)
    os.replace(staged, output)
    try:
        atomic_json(report_path, report)
    except BaseException:
        if had_output:
            os.replace(backup, output)
        else:
            output.unlink(missing_ok=True)
        raise
    try:
        backup.unlink(missing_ok=True)
    except OSError:
        pass


def run_worker(
    project: Path,
    contract: Path,
    output: Path,
    *,
    timeout: float,
) -> dict:
    project = Path(project).expanduser().resolve()
    contract = Path(contract).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    timeout = _qualification_timeout_seconds(timeout)
    expected_action_command = _worker_command(project, contract, output, timeout)
    action_id = _require_running_quality_action(project, expected_action_command)
    if not contract.is_relative_to(project):
        raise ValueError("Podcast qualification contract must remain inside the project")
    if not output.is_relative_to((project / "output").resolve()):
        raise ValueError("Podcast qualification output must remain in the project output folder")

    attempt_id = uuid.uuid4().hex
    started_at = now()
    report_path = project / REPORT_PATH
    attempt_path = project / ATTEMPTS_PATH / f"{attempt_id}.json"
    prior_output = _file_state(output)
    prior_report = _file_state(report_path)
    before_cache = _cache_snapshot(project)
    bindings = None
    performance = None
    scratch = None
    try:
        bindings = {
            **_input_binding(project, contract),
            "qualification_timeout_seconds": timeout,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix=".podcast-qualification-", dir=output.parent))
        staged = scratch / "candidate.mp4"
        result_path = scratch / "technical-result.json"
        command = [
            sys.executable, "-m", "tools.podcast_qualification", "_execute", str(project),
            "--contract", str(contract), "--output", str(staged), "--result", str(result_path),
            "--quality-action-id", action_id, "--worker-output", str(output), "--worker-timeout", f"{float(timeout):.17g}",
        ]
        performance = _run_measured(command, timeout)
        result = json.loads(result_path.read_text())
        if result.get("decode", {}).get("status") != "passed":
            raise ValueError("Qualification candidate did not pass full decode")
        _validate_delivery_against_target(result.get("delivery", {}), bindings["qualification_target"])
        after_cache = _cache_snapshot(project)
        output_binding = {"path": str(output), "sha256": file_hash(staged)}
        success_bindings = {**bindings, "output": output_binding}
        report = {
            "schema_version": 1,
            "attempt_id": attempt_id,
            "status": "succeeded",
            "started_at": started_at,
            "finished_at": now(),
            "quality_action_id": action_id,
            "platform": _platform(),
            "bindings": success_bindings,
            "cache": _cache_report(before_cache, after_cache),
            "performance": performance,
            "delivery": result["delivery"],
            "decode": result["decode"],
            "interruption": {"status": "not_interrupted", "recovery": "not_exercised"},
            "reviews": _reviews(True),
            "safety": _safety(),
            "failure": None,
            "preservation": {"prior_output_preserved": True, "prior_report_preserved": True},
        }
        validate_report(report)
        # Match the renderer's decision-race boundary: no Studio owner action
        # can land between final reviewed-binding validation and publication.
        with file_lock(project / "work/studio/.lock"):
            current = {
                **_input_binding(project, contract),
                "qualification_timeout_seconds": timeout,
            }
            if current != bindings:
                raise ValueError("Podcast qualification inputs changed during measurement")
            _publish_success(output, staged, report_path, report, scratch)
        # Attempt history is supplementary; a disk error here cannot invalidate
        # the already atomically published output/report pair.
        try:
            atomic_json(attempt_path, report)
        except OSError:
            pass
        return report
    except BaseException as error:
        interrupted = isinstance(error, KeyboardInterrupt)
        timeout_failure = isinstance(error, subprocess.TimeoutExpired)
        status = "interrupted" if interrupted else "failed"
        after_cache = _cache_snapshot(project)
        failure_bindings = None if bindings is None else {
            **bindings,
            "output": {"path": str(output), "sha256": None},
        }
        attempt = {
            "schema_version": 1,
            "attempt_id": attempt_id,
            "status": status,
            "started_at": started_at,
            "finished_at": now(),
            "quality_action_id": action_id,
            "platform": _platform(),
            "bindings": failure_bindings,
            "cache": _cache_report(before_cache, after_cache),
            "performance": performance,
            "delivery": None,
            "decode": None,
            "interruption": {
                "status": "interrupted" if interrupted else "timeout" if timeout_failure else "not_interrupted",
                "recovery": (
                    getattr(error, "_podcast_qualification_recovery", "not_needed")
                    if interrupted or timeout_failure
                    else "not_needed"
                ),
            },
            "reviews": _reviews(False),
            "safety": _safety(),
            "failure": {"type": type(error).__name__, "message": str(error)[-2000:]},
            "preservation": {
                "prior_output_preserved": _same_file(output, prior_output),
                "prior_report_preserved": _same_file(report_path, prior_report),
            },
        }
        validate_report(attempt)
        atomic_json(attempt_path, attempt)
        raise
    finally:
        if scratch is not None:
            shutil.rmtree(scratch, ignore_errors=True)


def qualify(project: Path, evidence: list[Path], *, timeout: float = 14_400) -> dict:
    project = Path(project).expanduser().resolve()
    timeout = _qualification_timeout_seconds(timeout)
    contract = project / DEFAULT_CONTRACT
    output = project / DEFAULT_OUTPUT
    command = _worker_command(project, contract, output, timeout)
    action = production_quality.run_action(
        project,
        command,
        QUALITY_RULES,
        "Render and technically qualify the current owner-reviewed long-form podcast stage",
        [Path(path) for path in evidence],
        timeout=timeout + 120,
        stage="edit",
    )
    report_path = project / REPORT_PATH
    report = json.loads(report_path.read_text()) if action.get("status") == "succeeded" and report_path.is_file() else None
    return {"action": action, "report": report}


def qualification_status(project: Path, _data: dict) -> dict:
    """Return currentness of canonical qualification evidence without changing state."""
    project = Path(project).expanduser().resolve()
    report_path = project / REPORT_PATH
    result = {
        "schema_version": 1,
        "current": False,
        "reasons": [],
        "report_attempt_id": None,
        "report_visual_score_revision_id": None,
    }
    if not report_path.is_file():
        result["reasons"] = ["report_missing"]
        return result
    try:
        report = json.loads(report_path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        result["reasons"] = ["report_invalid"]
        return result
    if isinstance(report, dict):
        attempt_id = report.get("attempt_id")
        if isinstance(attempt_id, str):
            result["report_attempt_id"] = attempt_id
        bindings = report.get("bindings")
        if isinstance(bindings, dict) and isinstance(bindings.get("visual_score_revision_id"), str):
            result["report_visual_score_revision_id"] = bindings["visual_score_revision_id"]
    try:
        validate_report(report)
    except (TypeError, ValueError):
        result["reasons"] = ["report_invalid"]
        return result
    if report["status"] != "succeeded":
        result["reasons"] = ["report_not_succeeded"]
        return result

    reasons = []
    reported = report["bindings"]
    expected_action_command = _worker_command(
        project,
        project / DEFAULT_CONTRACT,
        project / DEFAULT_OUTPUT,
        reported["qualification_timeout_seconds"],
    )
    try:
        action_history = production_quality.state(project).get("actions", [])
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        action_history = []
    referenced_actions = [action for action in action_history if action.get("id") == report["quality_action_id"]]
    if (
        len(referenced_actions) != 1
        or referenced_actions[0].get("status") != "succeeded"
        or referenced_actions[0].get("exit_code") != 0
        or referenced_actions[0].get("command") != expected_action_command
    ):
        reasons.append("quality_action_invalid")
    try:
        current = _input_binding(project, (project / DEFAULT_CONTRACT).resolve())
    except (OSError, ValueError):
        current = None
        reasons.append("reviewed_stage_stale")
    if current is not None:
        if current["source"] != reported["source"]:
            reasons.append("source_changed")
        if current["contract"] != reported["contract"]:
            reasons.append("contract_changed")
        if current["visual_score_revision_id"] != reported["visual_score_revision_id"]:
            reasons.append("visual_score_changed")
        if current["qualification_target"] != reported["qualification_target"]:
            reasons.append("qualification_target_changed")

    expected_output = (project / DEFAULT_OUTPUT).resolve()
    reported_output = reported["output"]
    if not expected_output.is_file():
        reasons.append("output_missing")
    elif reported_output["path"] != str(expected_output) or reported_output["sha256"] != file_hash(expected_output):
        reasons.append("output_changed")
    result["reasons"] = list(dict.fromkeys(reasons))[:10]
    result["current"] = not result["reasons"]
    return result


def _install_interrupt_handler():
    previous = signal.getsignal(signal.SIGTERM)

    def interrupted(_signum, _frame):
        raise KeyboardInterrupt()

    signal.signal(signal.SIGTERM, interrupted)
    return previous


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    public = subparsers.add_parser("qualify")
    public.add_argument("project", type=Path)
    public.add_argument("--evidence", type=Path, nargs="+", required=True)
    public.add_argument("--timeout", type=float, default=14_400)
    worker = subparsers.add_parser("_worker", help=argparse.SUPPRESS)
    worker.add_argument("project", type=Path)
    worker.add_argument("--contract", type=Path, required=True)
    worker.add_argument("--output", type=Path, required=True)
    worker.add_argument("--timeout", type=float, required=True)
    execute = subparsers.add_parser("_execute", help=argparse.SUPPRESS)
    execute.add_argument("project", type=Path)
    execute.add_argument("--contract", type=Path, required=True)
    execute.add_argument("--output", type=Path, required=True)
    execute.add_argument("--result", type=Path, required=True)
    execute.add_argument("--quality-action-id", required=True)
    execute.add_argument("--worker-output", type=Path, required=True)
    execute.add_argument("--worker-timeout", type=float, required=True)
    args = parser.parse_args()
    if args.command == "qualify":
        result = qualify(args.project, args.evidence, timeout=args.timeout)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["action"].get("status") != "succeeded":
            raise SystemExit(1)
    elif args.command == "_execute":
        _execute(
            args.project,
            args.contract,
            args.output,
            args.result,
            quality_action_id=args.quality_action_id,
            worker_output=args.worker_output,
            worker_timeout=args.worker_timeout,
        )
    else:
        previous = _install_interrupt_handler()
        try:
            report = run_worker(args.project, args.contract, args.output, timeout=args.timeout)
            print(json.dumps(report, indent=2, ensure_ascii=False))
        except KeyboardInterrupt:
            raise SystemExit(130)
        finally:
            signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    main()
