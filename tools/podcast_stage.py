"""Prepare and render the deterministic audio-first podcast visual stage.

The versioned JSON contract contains no filesystem path for the primary audio.
It binds an imported Studio asset by id, hash and measured duration. Rendering
resolves and revalidates that immutable asset, renders picture only in Remotion,
then muxes the selected source audio into an atomic output.
"""
from array import array
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from jsonschema import Draft202012Validator

from .jobs import file_hash
from .run_state import atomic_json, file_lock
from . import studio_project


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/podcast-stage.schema.json"
MEDIA_ROOT = ROOT / "media"
EXTRACTOR_VERSION = "streamed-rms-v1"
NORMALIZATION = "peak-rms-v1"


def _json_hash(value: dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate_contract(value: dict) -> dict:
    """Validate schema and timing relationships; return the original mapping."""
    if not isinstance(value, dict):
        raise ValueError("Podcast stage contract must be an object")
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("Podcast stage contract requires finite JSON values") from error
    schema = json.loads(SCHEMA.read_text())
    error = next(iter(Draft202012Validator(schema).iter_errors(value)), None)
    if error:
        location = ".".join(map(str, error.absolute_path)) or "contract"
        raise ValueError(f"Invalid podcast stage at {location}: {error.message}")

    width, height = value["render"]["width"], value["render"]["height"]
    if width % 2 or height % 2:
        raise ValueError("Podcast stage render dimensions must be even")
    duration = value["primary_audio"]["duration_ms"]
    expected_samples = math.ceil(duration / value["waveform"]["sample_period_ms"])
    if abs(len(value["waveform"]["values"]) - expected_samples) > 1:
        raise ValueError("Podcast waveform sample count does not cover primary audio duration")
    if any(not field.strip() for field in (
        value["identity"]["show_title"],
        value["identity"]["episode_title"],
        value["identity"]["speaker_name"],
    )):
        raise ValueError("Podcast identity fields cannot be whitespace only")
    previous_end = 0
    chapter_ids = set()
    for index, chapter in enumerate(value["chapters"]):
        if chapter["id"] in chapter_ids:
            raise ValueError("Podcast chapter IDs must be unique")
        chapter_ids.add(chapter["id"])
        if chapter["start_ms"] < previous_end or chapter["end_ms"] <= chapter["start_ms"]:
            raise ValueError("Podcast chapters must be ordered and non-overlapping")
        if chapter["end_ms"] > duration:
            raise ValueError("Podcast chapter exceeds primary audio duration")
        previous_end = chapter["end_ms"]
    visual_ids = set()
    for event in value.get("visual_events", []):
        anchor = event["transcript_anchor"]
        if (
            not event["id"].strip()
            or not event["chapter_id"].strip()
            or not event["purpose"].strip()
            or not anchor["text"].strip()
        ):
            raise ValueError("Podcast visual event context cannot be whitespace only")
        if event["id"] in visual_ids:
            raise ValueError("Podcast visual event IDs must be unique")
        visual_ids.add(event["id"])
        if event["end_ms"] <= event["start_ms"] or event["end_ms"] > duration:
            raise ValueError("Podcast visual event timing exceeds primary audio")
        if anchor["end_ms"] <= anchor["start_ms"] or anchor["end_ms"] > duration:
            raise ValueError("Podcast visual event transcript anchor exceeds primary audio")
        if event["type"] != event["treatment"]["kind"]:
            raise ValueError("Podcast visual event type must match its treatment")
        if event["type"] == "base" and event["camera_policy"] != "base_only":
            raise ValueError("An unchanged base-stage event cannot permit camera")
        if any(not source["label"].strip() for source in event["provenance"]):
            raise ValueError("Podcast visual provenance labels cannot be whitespace only")
        asset = event["treatment"].get("asset")
        if asset is not None:
            source = (MEDIA_ROOT / asset["path"]).resolve()
            if not source.is_relative_to(MEDIA_ROOT.resolve()) or not source.is_file():
                raise ValueError("Podcast visual asset must be a file in the Remotion media root")
            if file_hash(source) != asset["sha256"]:
                raise ValueError("Podcast visual asset changed after selection")
    return value


def _audio_probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode:
        raise ValueError("Primary media could not be inspected by ffprobe")
    try:
        info = json.loads(result.stdout)
        duration = float(info.get("format", {}).get("duration"))
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValueError("Primary media has no finite duration") from error
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Primary media has no finite duration")
    audio = [stream for stream in info.get("streams", []) if stream.get("codec_type") == "audio"]
    if not audio:
        raise ValueError("Primary media must contain an audio stream")
    return {"duration_ms": round(duration * 1000), "audio_streams": len(audio)}


def extract_waveform(path: Path, sample_period_ms: int = 50) -> list[float]:
    """Stream mono f32 PCM and retain only one RMS value per time bin."""
    if type(sample_period_ms) is not int or not 10 <= sample_period_ms <= 1000:
        raise ValueError("Waveform sample period must be an integer from 10 to 1000 ms")
    sample_rate = 1000
    samples_per_bin = sample_period_ms
    with tempfile.TemporaryFile() as error_file:
        process = subprocess.Popen(
            [
                "ffmpeg", "-nostdin", "-v", "error", "-i", str(path), "-map", "0:a:0",
                "-ac", "1", "-ar", str(sample_rate), "-f", "f32le", "pipe:1",
            ],
            stdout=subprocess.PIPE,
            stderr=error_file,
        )
        assert process.stdout is not None
        pending = b""
        square_sum = 0.0
        count = 0
        rms_values: list[float] = []
        try:
            while True:
                chunk = process.stdout.read(64 * 1024)
                if not chunk:
                    break
                payload = pending + chunk
                complete = len(payload) - len(payload) % 4
                pending = payload[complete:]
                values = array("f")
                values.frombytes(payload[:complete])
                if os.sys.byteorder != "little":
                    values.byteswap()
                for sample in values:
                    square_sum += float(sample) * float(sample)
                    count += 1
                    if count == samples_per_bin:
                        rms_values.append(math.sqrt(square_sum / count))
                        square_sum = 0.0
                        count = 0
            if count:
                rms_values.append(math.sqrt(square_sum / count))
            code = process.wait(timeout=60)
        except BaseException:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            raise
        error_file.seek(0, os.SEEK_END)
        error_file.seek(max(0, error_file.tell() - 2000))
        stderr = error_file.read().decode("utf-8", errors="replace")
    if code:
        raise RuntimeError("FFmpeg waveform extraction failed: " + stderr)
    if not rms_values:
        raise ValueError("Primary audio produced no waveform samples")
    peak = max(rms_values)
    if not math.isfinite(peak):
        raise ValueError("Primary audio produced a nonfinite waveform")
    if peak <= 1e-12:
        return [0.0 for _ in rms_values]
    return [round(min(1.0, max(0.0, value / peak)), 6) for value in rms_values]


def _cache_path(project: Path, audio_sha256: str, sample_period_ms: int) -> Path:
    key = _json_hash(
        {"extractor": EXTRACTOR_VERSION, "audio_sha256": audio_sha256, "sample_period_ms": sample_period_ms}
    )
    return project / "work/podcast" / f"waveform-{key}.json"


def _validate_artwork(identity: dict) -> None:
    artwork = identity.get("artwork")
    if artwork is None:
        return
    source = (MEDIA_ROOT / artwork["path"]).resolve()
    if not source.is_relative_to(MEDIA_ROOT.resolve()) or not source.is_file():
        raise ValueError("Podcast artwork must be a file in the Remotion media root")
    if file_hash(source) != artwork["sha256"]:
        raise ValueError("Podcast artwork changed after selection")


def prepare(
    project: Path,
    asset_id: str | None,
    identity: dict,
    *,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
    sample_period_ms: int = 50,
    chapters: list[dict] | None = None,
    motion: str = "standard",
) -> Path:
    """Create a validated contract bound to the exact imported Studio asset."""
    project = Path(project).expanduser().resolve()
    data = studio_project.read(project)
    if asset_id is None:
        podcast = data.get("podcast")
        if not isinstance(podcast, dict) or podcast.get("kind") != "solo_audio_first":
            raise ValueError("Configure Solo podcast visuals or provide --asset-id")
        asset_id = podcast.get("primary_audio_asset_id")
    asset = studio_project.source_asset_by_id(data, asset_id)
    source = Path(asset["path"])
    probe = _audio_probe(source)
    if abs(probe["duration_ms"] - asset["duration_ms"]) > 40:
        raise ValueError("Primary audio duration changed after import")

    _validate_artwork(identity)
    cache_path = _cache_path(project, asset["sha256"], sample_period_ms)
    waveform = None
    if cache_path.is_file():
        cached = json.loads(cache_path.read_text())
        if (
            cached.get("extractor") == EXTRACTOR_VERSION
            and cached.get("audio_sha256") == asset["sha256"]
            and cached.get("sample_period_ms") == sample_period_ms
            and isinstance(cached.get("values"), list)
        ):
            waveform = cached["values"]
    if waveform is None:
        waveform = extract_waveform(source, sample_period_ms)
        atomic_json(
            cache_path,
            {
                "extractor": EXTRACTOR_VERSION,
                "audio_sha256": asset["sha256"],
                "sample_period_ms": sample_period_ms,
                "values": waveform,
            },
        )

    duration = asset["duration_ms"]
    contract = {
        "schema_version": 1,
        "primary_audio": {
            "asset_id": asset["id"],
            "sha256": asset["sha256"],
            "duration_ms": duration,
        },
        "render": {"fps": fps, "width": width, "height": height},
        "identity": identity,
        "waveform": {
            "sample_period_ms": sample_period_ms,
            "normalization": NORMALIZATION,
            "values": waveform,
        },
        "chapters": chapters if chapters is not None else [
            {"id": "episode", "title": identity["episode_title"], "start_ms": 0, "end_ms": duration}
        ],
        "motion": motion,
    }
    validate_contract(contract)
    target = project / "work/podcast/stage.json"
    atomic_json(target, contract)
    return target


def resolve_audio(project: Path, contract: dict) -> Path:
    data = studio_project.read(project)
    expected = contract["primary_audio"]
    asset = studio_project.asset_by_id(data, expected["asset_id"])
    # Studio calls this field `id`; keep the external stage contract explicit.
    actual = {"asset_id": asset["id"], "sha256": asset["sha256"], "duration_ms": asset["duration_ms"]}
    if actual != expected:
        raise ValueError("Primary audio identity changed after stage preparation")
    source = Path(asset["path"])
    probe = _audio_probe(source)
    if abs(probe["duration_ms"] - expected["duration_ms"]) > 40:
        raise ValueError("Primary audio duration changed after stage preparation")
    return source


def run_renderer(contract_path: Path, output: Path) -> None:
    command = [
        "node",
        str(ROOT / "remotion/scripts/render-podcast-stage.mjs"),
        str(contract_path),
        str(output),
    ]
    result = subprocess.run(command, cwd=ROOT / "remotion", capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Podcast stage picture render failed: " + (result.stdout + result.stderr)[-4000:])


def _verify_delivery(path: Path, duration_ms: int, fps: int) -> dict:
    info = json.loads(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
            text=True,
        )
    )
    kinds = {stream.get("codec_type") for stream in info.get("streams", [])}
    if not {"audio", "video"} <= kinds:
        raise ValueError("Podcast stage output requires audio and video streams")
    duration = float(info.get("format", {}).get("duration", 0))
    tolerance = max(0.04, 1 / fps)
    if not math.isfinite(duration) or abs(duration - duration_ms / 1000) > tolerance:
        raise ValueError("Podcast stage output duration does not match primary audio")
    return {"duration_ms": round(duration * 1000), "streams": sorted(kinds)}


def render(
    project: Path,
    contract_path: Path | None = None,
    output: Path | None = None,
    *,
    record_receipt: bool = True,
) -> Path:
    """Render picture, mux canonical audio, verify, then atomically publish."""
    project = Path(project).expanduser().resolve()
    contract_path = Path(contract_path or project / "work/podcast/stage.json").resolve()
    contract = validate_contract(json.loads(contract_path.read_text()))
    validate_reviewed_stage = None
    if "visual_score_revision_id" in contract:
        # Lazy import avoids a module cycle: score tooling reuses this validator.
        from .podcast_visual_score import validate_reviewed_stage as reviewed_stage_validator

        validate_reviewed_stage = reviewed_stage_validator
        validate_reviewed_stage(project, studio_project.read(project), contract)
    _validate_artwork(contract["identity"])
    output = Path(output or project / "output/podcast-stage.mp4").resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    source = resolve_audio(project, contract)

    with file_lock(project / "work/podcast/.render.lock"):
        scratch = Path(tempfile.mkdtemp(prefix=".podcast-stage-", dir=output.parent))
        try:
            picture = scratch / "picture.mp4"
            staged = scratch / "completed.mp4"
            contract_snapshot = scratch / "contract.json"
            atomic_json(contract_snapshot, contract)
            run_renderer(contract_snapshot, picture)
            duration_s = contract["primary_audio"]["duration_ms"] / 1000
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-nostdin", "-v", "error", "-i", str(picture), "-i", str(source),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-af", "aresample=48000",
                    "-c:a", "aac", "-b:a", "192k", "-t", f"{duration_s:.6f}", "-movflags", "+faststart", str(staged),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode:
                raise RuntimeError("Podcast stage audio mux failed: " + result.stderr[-4000:])
            # Revalidate source identity after all reads, before replacing a prior success.
            resolve_audio(project, contract)
            if validate_contract(json.loads(contract_path.read_text())) != contract:
                raise ValueError("Podcast stage contract changed during render")
            _validate_artwork(contract["identity"])
            # Owner decisions use the Studio state lock. Hold it from the last
            # reviewed-binding check through verification, publication and its
            # receipt so no decision can race the publication boundary.
            with file_lock(project / "work/studio/.lock"):
                if validate_reviewed_stage is not None:
                    validate_reviewed_stage(project, studio_project.read(project), contract)
                verification = _verify_delivery(
                    staged, contract["primary_audio"]["duration_ms"], contract["render"]["fps"]
                )
                os.replace(staged, output)
                if record_receipt:
                    atomic_json(
                        project / "work/podcast/render.json",
                        {
                            "schema_version": 1,
                            "contract_sha256": file_hash(contract_path),
                            "audio_sha256": contract["primary_audio"]["sha256"],
                            "output": str(output),
                            "output_sha256": file_hash(output),
                            "verification": verification,
                        },
                    )
            return output
        finally:
            shutil.rmtree(scratch, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("project", type=Path)
    prepare_parser.add_argument(
        "--asset-id",
        help="Imported audio asset ID; defaults to the saved Solo podcast visuals selection",
    )
    prepare_parser.add_argument("--show-title", required=True)
    prepare_parser.add_argument("--episode-title", required=True)
    prepare_parser.add_argument("--speaker-name", required=True)
    prepare_parser.add_argument("--fps", type=int, default=30)
    prepare_parser.add_argument("--width", type=int, default=1920)
    prepare_parser.add_argument("--height", type=int, default=1080)
    prepare_parser.add_argument("--sample-period-ms", type=int, default=50)
    prepare_parser.add_argument("--motion", choices=("standard", "reduced"), default="standard")
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("project", type=Path)
    render_parser.add_argument("--contract", type=Path)
    render_parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        identity = {
            "show_title": args.show_title,
            "episode_title": args.episode_title,
            "speaker_name": args.speaker_name,
        }
        print(
            prepare(
                args.project,
                args.asset_id,
                identity,
                fps=args.fps,
                width=args.width,
                height=args.height,
                sample_period_ms=args.sample_period_ms,
                motion=args.motion,
            )
        )
    else:
        print(render(args.project, args.contract, args.output))


if __name__ == "__main__":
    main()
