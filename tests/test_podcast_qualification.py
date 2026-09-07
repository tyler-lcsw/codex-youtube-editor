"""Long-form podcast qualification is measured, atomic, and never creative approval."""
import json
import copy
from pathlib import Path
import subprocess
import sys

import pytest


def fake_binding(project: Path, contract: Path) -> dict:
    source = project / "source/audio.wav"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"source audio")
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text('{"reviewed":true}')
    return {
        "source": {"path": str(source), "sha256": __import__("hashlib").sha256(source.read_bytes()).hexdigest()},
        "contract": {"path": str(contract), "sha256": __import__("hashlib").sha256(contract.read_bytes()).hexdigest()},
        "visual_score_revision_id": "a" * 64,
        "reviewed_stage_current": True,
        "qualification_target": {
            "duration_ms": 1_500_000,
            "fps": 30,
            "width": 1920,
            "height": 1080,
            "expected_frame_count": 45_000,
            "duration_tolerance_ms": 40,
            "audio_duration_tolerance_ms": 100,
            "frame_count_tolerance": 1,
            "fps_tolerance": 0.001,
        },
    }


def fake_executor(command, timeout):
    assert command[command.index("--quality-action-id") + 1]
    output = Path(command[command.index("--output") + 1])
    result = Path(command[command.index("--result") + 1])
    output.write_bytes(b"qualified output")
    result.write_text(
        json.dumps(
            {
                "delivery": {
                    "format_name": "mov,mp4",
                    "duration_ms": 1_500_000,
                    "size_bytes": output.stat().st_size,
                    "streams": [
                        {"type": "video", "codec": "h264", "frame_count": 45_000, "width": 1920, "height": 1080, "avg_frame_rate": "30/1"},
                        {"type": "audio", "codec": "aac", "duration_ms": 1_500_000, "sample_rate": 48_000, "channels": 2},
                    ],
                },
                "decode": {"status": "passed", "exit_code": 0, "stderr_tail": ""},
            }
        )
    )
    return {
        "wall_time_seconds": 12.5,
        "peak_child_tree_rss_bytes": 123_456,
        "rss_sample_count": 9,
        "memory_pressure": {
            "before_free_percent": 71.0, "after_free_percent": 69.0, "minimum_free_percent": 66.0,
            "before_level": 1, "after_level": 1, "peak_level": 1,
        },
    }


def authorize_worker(monkeypatch, qualification, action_id="quality-action"):
    monkeypatch.setattr(
        qualification,
        "_require_running_quality_action",
        lambda _project, _command, expected_id=None: expected_id or action_id,
    )


def test_public_qualification_routes_render_through_production_quality(tmp_path, monkeypatch):
    from tools import podcast_qualification as qualification

    project = tmp_path / "project"
    project.mkdir()
    evidence = project / "work/qualification-plan.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("Approved technical qualification plan; creative reviews remain pending.")
    captured = {}

    def fake_run_action(project_arg, command, rules, reason, evidence_paths, **options):
        captured.update(
            project=Path(project_arg), command=command, rules=rules, reason=reason,
            evidence=evidence_paths, options=options,
        )
        return {"id": "quality-action", "status": "succeeded", "exit_code": 0}

    monkeypatch.setattr(qualification.production_quality, "run_action", fake_run_action)
    result = qualification.qualify(project, [evidence], timeout=321)
    assert result["action"]["id"] == "quality-action"
    assert captured["command"][:3] == [sys.executable, "-m", "tools.podcast_qualification"]
    assert "_worker" in captured["command"]
    assert set(captured["rules"]) >= {"R04", "R20", "R21", "R24", "R26", "R29"}
    assert captured["options"]["stage"] == "edit"
    assert captured["options"]["timeout"] > 321
    assert captured["evidence"] == [evidence]


def test_worker_publishes_atomic_success_report_without_claiming_review(tmp_path, monkeypatch):
    from tools import podcast_qualification as qualification

    project = tmp_path / "project"
    contract = project / "work/podcast/stage-reviewed.json"
    output = project / "output/podcast-qualified.mp4"
    old_report = project / "work/podcast/qualification/report.json"
    output.parent.mkdir(parents=True)
    old_report.parent.mkdir(parents=True)
    output.write_bytes(b"old output")
    old_report.write_text('{"old":true}')
    monkeypatch.setattr(qualification, "_input_binding", lambda p, c: fake_binding(p, c))
    monkeypatch.setattr(qualification, "_run_measured", fake_executor)
    authorize_worker(monkeypatch, qualification, "action-1")

    report = qualification.run_worker(project, contract, output, timeout=60)
    assert output.read_bytes() == b"qualified output"
    assert json.loads(old_report.read_text()) == report
    assert report["schema_version"] == 1 and report["status"] == "succeeded"
    assert report["bindings"]["output"]["sha256"]
    assert report["bindings"]["visual_score_revision_id"] == "a" * 64
    assert report["bindings"]["qualification_timeout_seconds"] == 60
    assert report["performance"]["peak_child_tree_rss_bytes"] == 123_456
    assert report["bindings"]["qualification_target"] == {
        "duration_ms": 1_500_000,
        "fps": 30,
        "width": 1920,
        "height": 1080,
        "expected_frame_count": 45_000,
        "duration_tolerance_ms": 40,
        "audio_duration_tolerance_ms": 100,
        "frame_count_tolerance": 1,
        "fps_tolerance": 0.001,
    }
    assert report["delivery"]["streams"][0]["frame_count"] == 45_000
    assert report["decode"]["status"] == "passed"
    assert report["interruption"] == {"status": "not_interrupted", "recovery": "not_exercised"}
    assert report["reviews"] == {
        "technical_validation": "passed",
        "visual_inspection": "pending",
        "normal_speed_listening": "pending",
        "owner_acceptance": "pending",
        "creative_acceptance": False,
    }
    assert report["safety"] == {"network_invoked": False, "publication_invoked": False, "models_invoked": False}
    attempts = list((project / "work/podcast/qualification/attempts").glob("*.json"))
    assert len(attempts) == 1 and json.loads(attempts[0].read_text()) == report
    qualification.validate_report(report)


@pytest.mark.parametrize(
    "change",
    [
        lambda report: report["bindings"]["qualification_target"].update(duration_ms=4_000),
        lambda report: next(stream for stream in report["delivery"]["streams"] if stream["type"] == "video").update(width=1280),
        lambda report: next(stream for stream in report["delivery"]["streams"] if stream["type"] == "video").update(frame_count=44_990),
        lambda report: next(stream for stream in report["delivery"]["streams"] if stream["type"] == "video").update(avg_frame_rate="30000/1001"),
        lambda report: next(stream for stream in report["delivery"]["streams"] if stream["type"] == "audio").update(duration_ms=1_499_000),
        lambda report: next(stream for stream in report["delivery"]["streams"] if stream["type"] == "audio").update(duration_ms=1_501_000),
        lambda report: report["delivery"]["streams"].append(
            copy.deepcopy(next(stream for stream in report["delivery"]["streams"] if stream["type"] == "audio"))
        ),
    ],
)
def test_success_report_rejects_noncanonical_target_or_delivery(tmp_path, monkeypatch, change):
    from tools import podcast_qualification as qualification

    project = tmp_path / "project"
    contract = project / "work/podcast/stage-reviewed.json"
    output = project / "output/podcast-qualified.mp4"
    monkeypatch.setattr(qualification, "_input_binding", lambda p, c: fake_binding(p, c))
    monkeypatch.setattr(qualification, "_run_measured", fake_executor)
    authorize_worker(monkeypatch, qualification)
    report = qualification.run_worker(project, contract, output, timeout=60)
    changed = copy.deepcopy(report)
    change(changed)

    with pytest.raises(ValueError):
        qualification.validate_report(changed)


@pytest.mark.parametrize(
    "duration_ms,width,height,fps",
    [
        (1_499_999, 1920, 1080, 30),
        (2_700_001, 1920, 1080, 30),
        (1_500_000, 1280, 720, 30),
        (1_500_000, 1920, 1080, 24),
    ],
)
def test_qualification_target_rejects_contracts_outside_long_form_profile(duration_ms, width, height, fps):
    from tools import podcast_qualification as qualification

    contract = {
        "primary_audio": {"duration_ms": duration_ms},
        "render": {"width": width, "height": height, "fps": fps},
    }
    with pytest.raises(ValueError, match="25|45|1920x1080|30 fps"):
        qualification._qualification_target(contract)


def test_child_tree_rss_sampling_is_bounded_to_once_per_second(monkeypatch):
    from tools import podcast_qualification as qualification

    clock = [0.0]
    rss_samples = []

    class Process:
        pid = 123

        def poll(self):
            return None if clock[0] < 3.1 else 0

        def wait(self):
            return 0

    monkeypatch.setattr(qualification.subprocess, "Popen", lambda *_args, **_kwargs: Process())
    monkeypatch.setattr(qualification.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(qualification.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    monkeypatch.setattr(qualification, "_child_tree_rss_bytes", lambda _pid: rss_samples.append(clock[0]) or 1024)
    monkeypatch.setattr(qualification, "_memory_pressure_percent", lambda: 50.0)
    monkeypatch.setattr(qualification, "_memory_pressure_level", lambda: 1)

    result = qualification._run_measured(["worker"], timeout=10)

    assert result["rss_sample_count"] == len(rss_samples)
    assert 3 <= len(rss_samples) <= 4
    assert all(later - earlier >= 1 for earlier, later in zip(rss_samples, rss_samples[1:]))


def test_measured_timeout_claims_child_termination_only_after_reap(monkeypatch):
    from tools import podcast_qualification as qualification

    clock = [0.0]

    class Process:
        pid = 123
        alive = True

        def poll(self):
            return None if self.alive else -15

    process = Process()
    monkeypatch.setattr(qualification.subprocess, "Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr(qualification.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(qualification.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    monkeypatch.setattr(qualification, "_child_tree_rss_bytes", lambda _pid: 1024)
    monkeypatch.setattr(qualification, "_memory_pressure_percent", lambda: None)
    monkeypatch.setattr(qualification, "_memory_pressure_level", lambda: None)
    monkeypatch.setattr(qualification, "terminate_group", lambda child: setattr(child, "alive", False))

    with pytest.raises(subprocess.TimeoutExpired) as caught:
        qualification._run_measured(["worker"], timeout=0.5)

    assert caught.value._podcast_qualification_recovery == "child_process_terminated"


@pytest.mark.parametrize(
    ("raised", "expected_status"),
    [(RuntimeError("decode failed"), "failed"), (KeyboardInterrupt(), "interrupted")],
)
def test_worker_failure_or_interruption_preserves_prior_report_and_output(
    tmp_path, monkeypatch, raised, expected_status
):
    from tools import podcast_qualification as qualification

    project = tmp_path / expected_status
    contract = project / "work/podcast/stage-reviewed.json"
    output = project / "output/podcast-qualified.mp4"
    report_path = project / "work/podcast/qualification/report.json"
    output.parent.mkdir(parents=True)
    report_path.parent.mkdir(parents=True)
    output.write_bytes(b"previous successful output")
    report_path.write_bytes(b'{"previous":"successful report"}')
    previous_output = output.read_bytes()
    previous_report = report_path.read_bytes()
    monkeypatch.setattr(qualification, "_input_binding", lambda p, c: fake_binding(p, c))

    def fail_after_staging(command, timeout):
        Path(command[command.index("--output") + 1]).write_bytes(b"partial replacement")
        raise raised

    monkeypatch.setattr(qualification, "_run_measured", fail_after_staging)
    authorize_worker(monkeypatch, qualification, "action-2")
    with pytest.raises(BaseException) as caught:
        qualification.run_worker(project, contract, output, timeout=60)
    assert isinstance(caught.value, type(raised))
    assert output.read_bytes() == previous_output
    assert report_path.read_bytes() == previous_report
    attempts = list((project / "work/podcast/qualification/attempts").glob("*.json"))
    assert len(attempts) == 1
    attempt = json.loads(attempts[0].read_text())
    assert attempt["status"] == expected_status
    assert attempt["preservation"] == {"prior_output_preserved": True, "prior_report_preserved": True}
    assert attempt["interruption"] == {
        "status": "interrupted" if expected_status == "interrupted" else "not_interrupted",
        "recovery": "not_needed",
    }
    qualification.validate_report(attempt)


@pytest.mark.parametrize("interrupt_at", ["prelaunch", "publication"])
def test_interrupt_without_a_live_child_reports_no_cleanup(tmp_path, monkeypatch, interrupt_at):
    from tools import podcast_qualification as qualification

    project = tmp_path / interrupt_at
    contract = project / "work/podcast/stage-reviewed.json"
    output = project / "output/podcast-qualified.mp4"
    authorize_worker(monkeypatch, qualification)
    if interrupt_at == "prelaunch":
        monkeypatch.setattr(qualification, "_input_binding", lambda *_args: (_ for _ in ()).throw(KeyboardInterrupt()))
    else:
        monkeypatch.setattr(qualification, "_input_binding", lambda p, c: fake_binding(p, c))
        monkeypatch.setattr(qualification, "_run_measured", fake_executor)
        monkeypatch.setattr(
            qualification,
            "_publish_success",
            lambda *_args: (_ for _ in ()).throw(KeyboardInterrupt()),
        )

    with pytest.raises(KeyboardInterrupt):
        qualification.run_worker(project, contract, output, timeout=60)

    attempt = json.loads(next((project / "work/podcast/qualification/attempts").glob("*.json")).read_text())
    assert attempt["interruption"] == {"status": "interrupted", "recovery": "not_needed"}


def test_worker_requires_a_running_quality_action(tmp_path, monkeypatch):
    from tools import podcast_qualification as qualification

    project = tmp_path / "project"
    contract = project / "work/podcast/stage-reviewed.json"
    output = project / "output/podcast-qualified.mp4"
    with pytest.raises(ValueError, match="production-quality"):
        qualification.run_worker(project, contract, output, timeout=1)


def test_worker_rejects_arbitrary_action_override_and_mismatched_exact_command(tmp_path):
    from tools import podcast_qualification as qualification

    project = tmp_path / "project"
    project.mkdir()
    contract = project / "work/podcast/stage-reviewed.json"
    output = project / "output/podcast-qualified.mp4"
    with pytest.raises(TypeError, match="quality_action_id"):
        qualification.run_worker(project, contract, output, timeout=1, quality_action_id="forged")

    state_path = project / "work/quality/state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(json.dumps({"actions": [{"id": "action", "status": "running", "command": ["other"]}]}))
    with pytest.raises(ValueError, match="exactly one"):
        qualification.run_worker(project, contract, output, timeout=1)


def test_execute_requires_exact_running_parent_quality_action(tmp_path, monkeypatch):
    from tools import podcast_qualification as qualification

    project = tmp_path / "project"
    project.mkdir()
    contract = project / "work/podcast/stage-reviewed.json"
    output = project / "output/podcast-qualified.mp4"
    result = project / "result.json"
    state_path = project / "work/quality/state.json"
    state_path.parent.mkdir(parents=True)
    expected = qualification._worker_command(project.resolve(), contract.resolve(), output.resolve(), 60)
    state_path.write_text(json.dumps({"actions": [{"id": "action", "status": "failed", "command": expected}]}))
    monkeypatch.setattr(qualification.podcast_stage, "render", lambda *_args, **_kwargs: pytest.fail("render started"))

    with pytest.raises(ValueError, match="exactly one"):
        qualification._execute(
            project, contract, project / "candidate.mp4", result,
            quality_action_id="action", worker_output=output, worker_timeout=60,
        )
    state_path.write_text(json.dumps({"actions": [{"id": "action", "status": "running", "command": expected}]}))
    with pytest.raises(ValueError, match="exactly one"):
        qualification._execute(
            project, contract, project / "candidate.mp4", result,
            quality_action_id="wrong-action", worker_output=output, worker_timeout=60,
        )

    cli = subprocess.run(
        [
            sys.executable, "-m", "tools.podcast_qualification", "_execute", str(project),
            "--contract", str(contract), "--output", str(project / "candidate.mp4"), "--result", str(result),
        ],
        capture_output=True,
        text=True,
    )
    assert cli.returncode == 2
    assert "--quality-action-id" in cli.stderr


def test_worker_revalidates_reviewed_binding_before_publication(tmp_path, monkeypatch):
    from tools import podcast_qualification as qualification

    project = tmp_path / "project"
    contract = project / "work/podcast/stage-reviewed.json"
    output = project / "output/podcast-qualified.mp4"
    report_path = project / "work/podcast/qualification/report.json"
    output.parent.mkdir(parents=True)
    report_path.parent.mkdir(parents=True)
    output.write_bytes(b"previous output")
    report_path.write_bytes(b'{"previous":true}')
    first = fake_binding(project, contract)
    calls = 0

    def changing_binding(_project, _contract):
        nonlocal calls
        calls += 1
        return first if calls == 1 else first | {"visual_score_revision_id": "b" * 64}

    monkeypatch.setattr(qualification, "_input_binding", changing_binding)
    monkeypatch.setattr(qualification, "_run_measured", fake_executor)
    authorize_worker(monkeypatch, qualification, "action-3")
    with pytest.raises(ValueError, match="changed during measurement"):
        qualification.run_worker(project, contract, output, timeout=60)
    assert output.read_bytes() == b"previous output"
    assert report_path.read_bytes() == b'{"previous":true}'


def test_real_delivery_probe_counts_frames_and_fully_decodes(tmp_path):
    from tools.podcast_qualification import inspect_delivery

    output = tmp_path / "fixture.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
            "color=black:s=32x32:r=10:d=1", "-f", "lavfi", "-i",
            "sine=frequency=440:sample_rate=48000:duration=1", "-c:v", "libx264",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(output),
        ],
        check=True,
    )
    delivery, decode = inspect_delivery(output)
    assert delivery["duration_ms"] == pytest.approx(1_000, abs=80)
    assert {stream["type"] for stream in delivery["streams"]} >= {"audio", "video"}
    video = next(stream for stream in delivery["streams"] if stream["type"] == "video")
    audio = next(stream for stream in delivery["streams"] if stream["type"] == "audio")
    assert video["codec"] == "h264" and video["frame_count"] == 10
    assert audio["duration_ms"] == pytest.approx(1_000, abs=80)
    assert decode["status"] == "passed" and decode["exit_code"] == 0


def test_audio_stream_duration_falls_back_to_duration_ticks():
    from tools import podcast_qualification as qualification

    assert qualification._stream_duration_ms({"duration_ts": "48000", "time_base": "1/48000"}) == 1_000
    with pytest.raises(ValueError, match="audio stream duration"):
        qualification._stream_duration_ms({"duration": "N/A"})


def test_delivery_probe_rejects_multiple_audio_streams_before_decode(tmp_path, monkeypatch):
    from tools import podcast_qualification as qualification

    info = {
        "format": {"duration": "1.0", "format_name": "mov"},
        "streams": [
            {"codec_type": "video", "codec_name": "h264", "nb_read_frames": "30", "width": 1920, "height": 1080, "avg_frame_rate": "30/1"},
            {"codec_type": "audio", "codec_name": "aac", "duration": "1.0", "sample_rate": "48000", "channels": 2},
            {"codec_type": "audio", "codec_name": "aac", "duration": "1.0", "sample_rate": "48000", "channels": 2},
        ],
    }
    monkeypatch.setattr(
        qualification.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, json.dumps(info), ""),
    )
    with pytest.raises(ValueError, match="exactly one audio"):
        qualification.inspect_delivery(tmp_path / "candidate.mp4")


def test_podcast_stage_can_skip_ordinary_render_receipt_for_qualification(tmp_path, monkeypatch):
    from tools import podcast_stage

    project = tmp_path / "project"
    (project / "work/podcast").mkdir(parents=True)
    (project / "output").mkdir()
    prior = project / "work/podcast/render.json"
    prior.write_text('{"prior":true}')
    contract = {
        "schema_version": 1,
        "primary_audio": {"asset_id": "audio", "sha256": "a" * 64, "duration_ms": 1_000},
        "render": {"fps": 10, "width": 32, "height": 32},
        "identity": {"show_title": "Show", "episode_title": "Episode", "speaker_name": "Speaker"},
        "waveform": {"sample_period_ms": 1000, "normalization": "peak-rms-v1", "values": [0]},
        "chapters": [{"id": "episode", "title": "Episode", "start_ms": 0, "end_ms": 1_000}],
        "motion": "standard",
    }
    contract_path = project / "work/podcast/stage.json"
    contract_path.write_text(json.dumps(contract))
    source = project / "source.wav"
    source.write_bytes(b"source")
    monkeypatch.setattr(podcast_stage, "resolve_audio", lambda *_args: source)

    def fake_renderer(_contract, picture):
        picture.write_bytes(b"picture")

    def fake_run(command, **_kwargs):
        Path(command[-1]).write_bytes(b"staged")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(podcast_stage, "run_renderer", fake_renderer)
    monkeypatch.setattr(podcast_stage.subprocess, "run", fake_run)
    monkeypatch.setattr(
        podcast_stage,
        "_verify_delivery",
        lambda *_args: {"duration_ms": 1_000, "streams": ["audio", "video"]},
    )
    podcast_stage.render(project, contract_path, record_receipt=False)
    assert prior.read_text() == '{"prior":true}'


def test_remotion_stage_snapshot_lives_inside_python_owned_output_tree():
    script = (Path(__file__).parents[1] / "remotion/scripts/render-podcast-stage.mjs").read_text()
    assert "mkdtempSync(path.join(path.dirname(output), '.podcast-stage-media-'))" in script
    assert "os.tmpdir()" not in script
