import Foundation
import StudioCore

private let successfulQualificationJSON="""
{"schema_version":1,"attempt_id":"attempt-success","status":"succeeded","started_at":"2026-09-07T12:00:00Z","finished_at":"2026-09-07T12:31:00Z","quality_action_id":"quality-1","platform":{"system":"Darwin","release":"25.6.0","machine":"arm64"},
 "bindings":{"source":{"path":"media/episode.wav","sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},"contract":{"path":"work/podcast/stage-reviewed.json","sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},"output":{"path":"work/podcast/qualification/episode.mp4","sha256":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"},"visual_score_revision_id":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","reviewed_stage_current":true,"qualification_target":{"duration_ms":1800000,"fps":30,"width":1920,"height":1080,"expected_frame_count":54000,"duration_tolerance_ms":40,"audio_duration_tolerance_ms":100,"frame_count_tolerance":1,"fps_tolerance":0.001}},
 "cache":{"descriptor":"hit","waveform":"hit"},
 "performance":{"wall_time_seconds":1860.5,"peak_child_tree_rss_bytes":8589934592,"rss_sample_count":62,"memory_pressure":{"before_free_percent":71.0,"after_free_percent":69.0,"minimum_free_percent":66.0,"before_level":0,"after_level":1,"peak_level":1}},
 "delivery":{"format_name":"mov,mp4","duration_ms":1800000,"size_bytes":987654321,"streams":[{"type":"video","codec":"h264","frame_count":54000,"width":1920,"height":1080,"avg_frame_rate":"30/1"},{"type":"audio","codec":"aac","duration_ms":1800000,"sample_rate":48000,"channels":2}]},
 "decode":{"status":"passed","exit_code":0,"stderr_tail":""},
 "interruption":{"status":"not_interrupted","recovery":"not_needed"},
 "reviews":{"technical_validation":"passed","visual_inspection":"pending","normal_speed_listening":"pending","owner_acceptance":"pending","creative_acceptance":false},
 "safety":{"network_invoked":false,"publication_invoked":false,"models_invoked":false},"failure":null,"preservation":{"prior_output_preserved":true,"prior_report_preserved":true}}
"""

func testPodcastQualificationParsesTechnicalMetricsWithoutInventingCreativeCompletion() throws {
    let report=try PodcastQualificationAttempt.decode(Data(successfulQualificationJSON.utf8))
    XCTAssertEqual(report.status,.succeeded)
    XCTAssertEqual(report.performance.wallSeconds,1860.5)
    XCTAssertEqual(report.performance.peakRSSBytes,8589934592)
    XCTAssertEqual(report.performance.peakPressureLevel,1)
    XCTAssertEqual(report.delivery.width,1920)
    XCTAssertEqual(report.delivery.videoCodec,"h264")
    XCTAssertEqual(report.delivery.audioDurationSeconds,1800)
    XCTAssertEqual(report.bindings.target?.expectedFrameCount,54000)
    XCTAssertEqual(report.reviews.visualInspection,"pending")
    XCTAssertEqual(report.reviews.normalSpeedListening,"pending")
    XCTAssertEqual(report.reviews.ownerAcceptance,"pending")
    XCTAssertFalse(report.reviews.creativeAcceptance)
    XCTAssertFalse(report.isComplete)
    XCTAssertTrue(report.summary.contains("human review pending"))
    XCTAssertThrowsError(try PodcastQualificationAttempt.decode(Data(
        successfulQualificationJSON.replacingOccurrences(of:"\"creative_acceptance\":false",with:"\"creative_acceptance\":true").utf8
    )))
    XCTAssertThrowsError(try PodcastQualificationAttempt.decode(Data(
        successfulQualificationJSON.replacingOccurrences(of:"\"duration_ms\":1800000,\"size_bytes\"",with:"\"duration_ms\":1200000,\"size_bytes\"").utf8
    )))
    XCTAssertThrowsError(try PodcastQualificationAttempt.decode(Data(
        successfulQualificationJSON.replacingOccurrences(of:"\"width\":1920,\"height\":1080",with:"\"width\":1280,\"height\":720").utf8
    )))
    XCTAssertThrowsError(try PodcastQualificationAttempt.decode(Data(
        successfulQualificationJSON.replacingOccurrences(of:"\"visual_score_revision_id\":\"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd\"",with:"\"visual_score_revision_id\":\"unbound\"").utf8
    )))
    XCTAssertThrowsError(try PodcastQualificationAttempt.decode(Data(
        successfulQualificationJSON.replacingOccurrences(of:"\"codec\":\"aac\",\"duration_ms\":1800000",with:"\"codec\":\"aac\",\"duration_ms\":1801000").utf8
    )))
    let audiovisualDrift=successfulQualificationJSON
        .replacingOccurrences(of:"\"frame_count\":54000",with:"\"frame_count\":53999")
        .replacingOccurrences(of:"\"codec\":\"aac\",\"duration_ms\":1800000",with:"\"codec\":\"aac\",\"duration_ms\":1800100")
    XCTAssertThrowsError(try PodcastQualificationAttempt.decode(Data(audiovisualDrift.utf8)))
    XCTAssertThrowsError(try PodcastQualificationAttempt.decode(Data(
        successfulQualificationJSON.replacingOccurrences(of:"]},\n \"decode\"",with:",{\"type\":\"audio\",\"codec\":\"aac\",\"duration_ms\":1800000,\"sample_rate\":48000,\"channels\":2}]},\n \"decode\"").utf8
    )))
}

func testPodcastQualificationSurfacesFailureAndInterruptionRecovery() throws {
    let interrupted=try PodcastQualificationAttempt.decode(Data("""
    {"schema_version":1,"attempt_id":"attempt-interrupted","status":"interrupted","started_at":"2026-09-07T12:00:00Z","finished_at":"2026-09-07T12:10:00Z","quality_action_id":"quality-2","platform":{"system":"Darwin","release":"25.6.0","machine":"arm64"},
     "bindings":null,"cache":{},"performance":null,"delivery":null,"decode":null,
     "interruption":{"status":"interrupted","recovery":"child_process_terminated"},
     "reviews":{"technical_validation":"failed","visual_inspection":"pending","normal_speed_listening":"pending","owner_acceptance":"pending","creative_acceptance":false},
     "safety":{"network_invoked":false,"publication_invoked":false,"models_invoked":false},
     "failure":{"type":"KeyboardInterrupt","message":"Operator interrupted the qualification run."},"preservation":{"prior_output_preserved":true,"prior_report_preserved":true}}
    """.utf8))
    XCTAssertEqual(interrupted.status,.interrupted)
    XCTAssertEqual(interrupted.failure?.type,"KeyboardInterrupt")
    XCTAssertEqual(interrupted.interruption.recoveryStatus,"child_process_terminated")
    XCTAssertTrue(interrupted.interruption.recoveryLabel.contains("terminated and reaped"))
    XCTAssertFalse(interrupted.isComplete)
    XCTAssertTrue(interrupted.summary.contains("interrupted"))
}

func testPodcastQualificationRecoveryLabelsDoNotInventTermination() {
    XCTAssertFalse(PodcastQualificationInterruption(status:"interrupted",recoveryStatus:"not_needed").recoveryLabel.contains("terminated"))
    XCTAssertTrue(PodcastQualificationInterruption(status:"interrupted",recoveryStatus:"not_needed").recoveryLabel.contains("No live child"))
    XCTAssertTrue(PodcastQualificationInterruption(status:"interrupted",recoveryStatus:"child_process_termination_failed").recoveryLabel.contains("could not be verified"))
}

func testPodcastQualificationLoaderTreatsMissingReportHonestlyAndKeepsAttempts() throws {
    let root=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer {try? FileManager.default.removeItem(at:root)}
    let attempts=root.appendingPathComponent("work/podcast/qualification/attempts")
    try FileManager.default.createDirectory(at:attempts,withIntermediateDirectories:true)
    let interrupted=successfulQualificationJSON
        .replacingOccurrences(of:"attempt-success",with:"attempt-old")
        .replacingOccurrences(of:"\"status\":\"succeeded\"",with:"\"status\":\"failed\"")
        .replacingOccurrences(of:"\"technical_validation\":\"passed\"",with:"\"technical_validation\":\"failed\"")
        .replacingOccurrences(of:"\"failure\":null",with:"\"failure\":{\"type\":\"RuntimeError\",\"message\":\"Decode failed\"}")
    try Data(interrupted.utf8).write(to:attempts.appendingPathComponent("attempt-old.json"))
    let snapshot=try PodcastQualificationSnapshot.load(projectPath:root.path)
    XCTAssertNil(snapshot.report)
    XCTAssertEqual(snapshot.attempts.count,1)
    XCTAssertEqual(snapshot.attempts[0].status,.failed)
    XCTAssertEqual(snapshot.availability,"No successful long-form qualification report is available.")

    let reportURL=root.appendingPathComponent("work/podcast/qualification/report.json")
    try Data(successfulQualificationJSON.utf8).write(to:reportURL)
    let withReport=try PodcastQualificationSnapshot.load(projectPath:root.path)
    XCTAssertEqual(withReport.report?.attemptID,"attempt-success")
    XCTAssertFalse(withReport.report?.isComplete ?? true)
}

func testPodcastQualificationStatusParsesRevisionBoundCurrentAndStaleResponses() throws {
    let current=try PodcastQualificationLiveStatus.decode([
        "schema_version":1,"current":true,"reasons":[String](),"report_attempt_id":"attempt-success",
        "report_visual_score_revision_id":String(repeating:"d",count:64),
    ])
    XCTAssertTrue(current.current)
    XCTAssertEqual(current.reportAttemptID,"attempt-success")
    XCTAssertEqual(current.reportVisualScoreRevisionID,String(repeating:"d",count:64))
    XCTAssertEqual(current.reasons,[])

    let stale=try PodcastQualificationLiveStatus.decode([
        "schema_version":1,"current":false,"reasons":["source_changed","output_missing"],
        "report_attempt_id":"attempt-success","report_visual_score_revision_id":String(repeating:"d",count:64),
    ])
    XCTAssertFalse(stale.current)
    XCTAssertEqual(stale.reasons,["source_changed","output_missing"])
    XCTAssertThrowsError(try PodcastQualificationLiveStatus.decode([
        "schema_version":1,"current":true,"reasons":["source_changed"],"report_attempt_id":"attempt-success",
        "report_visual_score_revision_id":String(repeating:"d",count:64),
    ]))
}

func testPodcastQualificationPresentationNeverPromotesSavedEvidenceWithoutLiveCurrentStatus() throws {
    let report=try PodcastQualificationAttempt.decode(Data(successfulQualificationJSON.utf8))
    let pending=PodcastQualificationPresentation(report:report,live:nil,verificationError:nil)
    XCTAssertFalse(pending.isCurrent)
    XCTAssertTrue(pending.headline.contains("Saved at-run evidence"))

    let stale=PodcastQualificationPresentation(report:report,live:try PodcastQualificationLiveStatus.decode([
        "schema_version":1,"current":false,"reasons":["contract_changed"],"report_attempt_id":"attempt-success",
        "report_visual_score_revision_id":String(repeating:"d",count:64),
    ]),verificationError:nil)
    XCTAssertFalse(stale.isCurrent)
    XCTAssertTrue(stale.detail.contains("Reviewed-stage contract changed"))

    let current=PodcastQualificationPresentation(report:report,live:try PodcastQualificationLiveStatus.decode([
        "schema_version":1,"current":true,"reasons":[String](),"report_attempt_id":"attempt-success",
        "report_visual_score_revision_id":String(repeating:"d",count:64),
    ]),verificationError:nil)
    XCTAssertTrue(current.isCurrent)
    XCTAssertTrue(current.headline.contains("Current technical long-form qualification"))
}
