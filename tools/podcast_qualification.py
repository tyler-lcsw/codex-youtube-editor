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
FRAME_COUNT_TOLERANCE = 1
FPS_TOLERANCE = 0.001


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
        "frame_count_tolerance": FRAME_COUNT_TOLERANCE,
        "fps_tolerance": FPS_TOLERANCE,
    }
    return _validate_qualification_target(target)


def _validate_delivery_against_target(delivery: dict, target: dict) -> None:
    if abs(delivery.get("duration_ms", -1) - target["duration_ms"]) > target["duration_tolerance_ms"]:
        raise ValueError("Qualified delivery duration does not match the long-form contract")
    videos = [stream for stream in delivery.get("streams", []) if stream.get("type") == "video"]
    if len(videos) != 1:
        raise ValueError("Qualified delivery requires exactly one canonical video stream")
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


def _running_quality_action_id(project: Path) -> str | None:
    running = []
    for action in production_quality.state(project).get("actions", []):
        command = action.get("command", [])
        if (
            action.get("status") == "running"
            and isinstance(command, list)
            and "tools.podcast_qualification" in command
            and "_worker" in command
        ):
            running.append(action.get("id"))
    return running[0] if len(running) == 1 and isinstance(running[0], str) else None


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
                    terminate_group(process)
                    raise subprocess.TimeoutExpired(command, timeout)
                time.sleep(0.25)
            code = process.wait()
        except BaseException:
            if process.poll() is None:
                terminate_group(process)
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
    streams = []
    for stream in info.get("streams", []):
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
            streams.append(
                {
                    "type": "audio",
                    "codec": stream.get("codec_name") or "unknown",
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


def _execute(project: Path, contract: Path, output: Path, result_path: Path) -> None:
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
    quality_action_id: str | None = None,
) -> dict:
    project = Path(project).expanduser().resolve()
    contract = Path(contract).expanduser().resolve()
    output = Path(output).expanduser().resolve()
    action_id = quality_action_id or _running_quality_action_id(project)
    if not action_id:
        raise ValueError("Podcast qualification must run inside a production-quality action")
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
        bindings = _input_binding(project, contract)
        output.parent.mkdir(parents=True, exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix=".podcast-qualification-", dir=output.parent))
        staged = scratch / "candidate.mp4"
        result_path = scratch / "technical-result.json"
        command = [
            sys.executable, "-m", "tools.podcast_qualification", "_execute", str(project),
            "--contract", str(contract), "--output", str(staged), "--result", str(result_path),
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
            current = _input_binding(project, contract)
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
                "recovery": "child_process_terminated" if interrupted or timeout_failure else "not_needed",
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
    contract = project / DEFAULT_CONTRACT
    output = project / DEFAULT_OUTPUT
    command = [
        sys.executable, "-m", "tools.podcast_qualification", "_worker", str(project),
        "--contract", str(contract), "--output", str(output), "--timeout", str(timeout),
    ]
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
    args = parser.parse_args()
    if args.command == "qualify":
        result = qualify(args.project, args.evidence, timeout=args.timeout)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result["action"].get("status") != "succeeded":
            raise SystemExit(1)
    elif args.command == "_execute":
        _execute(args.project, args.contract, args.output, args.result)
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
