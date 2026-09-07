import Foundation
import StudioCore

func testPodcastVisualScoreParsesChaptersEventsPreviewsAndDecisions() throws {
    let episodeMap = try PodcastEpisodeMap.decode(Data("""
    {"schema_version":1,"duration_ms":60000,"chapters":[
      {"id":"opening","title":"Opening","start_ms":0,"end_ms":30000},
      {"id":"close","title":"Close","start_ms":30000,"end_ms":60000}
    ]}
    """.utf8))
    XCTAssertEqual(episodeMap.durationMS,60000)
    XCTAssertEqual(episodeMap.chapters.map(\.id),["opening","close"])

    let score = try PodcastVisualScore.decode(Data("""
    {"schema_version":1,"revision_id":"score-rev-1","episode_map_sha256":"map-hash","visual_density":"balanced",
     "visual_events":[
       {"id":"event-1","type":"chapter_card","chapter_id":"opening","start_ms":0,"end_ms":2500,
        "transcript_anchor":{"start_word_id":"w1","end_word_id":"w4"},"purpose":"Orient the listener","treatment":{"title":"Opening"},
        "provenance":{"kind":"episode_map"},"camera_policy":"base_only","preview_path":"/tmp/opening.png"},
       {"id":"event-2","type":"future_card","chapter_id":"close","start_ms":40000,"end_ms":42000,
        "transcript_anchor":{},"purpose":"Future proposal","treatment":{},"provenance":{},"camera_policy":"none","extra_future_field":true}
     ],"representative_previews":[{"chapter_id":"close","path":"/tmp/close.png"}]}
    """.utf8))
    XCTAssertEqual(score.revisionID,"score-rev-1")
    XCTAssertEqual(score.events.count,2)
    XCTAssertEqual(score.events[0].typeLabel,"Chapter card")
    XCTAssertEqual(score.events[0].previewPath,"/tmp/opening.png")
    XCTAssertFalse(score.events[1].isSupported)
    XCTAssertEqual(score.previews.first?.path,"/tmp/close.png")

    let decisions = try PodcastVisualScoreDecisionLog.decode(Data("""
    {"schema_version":1,"decisions":[
      {"id":"decision-1","revision_id":"score-rev-1","event_id":"event-1","action":"accept","note":"Use this","decided_at":"2026-09-07T12:00:00Z","owner_action":true}
    ]}
    """.utf8))
    XCTAssertEqual(decisions.decisions.first?.action,.accept)
    XCTAssertEqual(decisions.latest(for:"event-1",revisionID:"score-rev-1")?.note,"Use this")
}

func testPodcastVisualScoreRejectsInvalidVersionsRangesAndNonOwnerDecisions() {
    XCTAssertThrowsError(try PodcastEpisodeMap.decode(Data("""
    {"schema_version":2,"duration_ms":1000,"chapters":[]}
    """.utf8)))
    XCTAssertThrowsError(try PodcastVisualScore.decode(Data("""
    {"schema_version":1,"revision_id":"rev","visual_density":"balanced","visual_events":[
      {"id":"event","type":"base","chapter_id":"chapter","start_ms":1000,"end_ms":1000,"purpose":"Keep stage","treatment":{},"provenance":{},"camera_policy":"none"}
    ]}
    """.utf8)))
    XCTAssertThrowsError(try PodcastVisualScoreDecisionLog.decode(Data("""
    {"schema_version":1,"decisions":[
      {"id":"decision","revision_id":"rev","event_id":"event","action":"accept","decided_at":"now","owner_action":false}
    ]}
    """.utf8)))
}

func testPodcastVisualScoreDecisionPayloadIsRevisionBoundAndExplicit() throws {
    let revision=String(repeating:"a",count:64)
    let payload = try PodcastVisualScoreDecisionPayload.build(
        revisionID:revision,eventID:"event-1",action:.useBase,note:"Prefer the continuous stage"
    )
    XCTAssertEqual(payload["revision_id"] as? String,revision)
    XCTAssertEqual(payload["event_id"] as? String,"event-1")
    XCTAssertEqual(payload["action"] as? String,"use_base")
    XCTAssertEqual(payload["note"] as? String,"Prefer the continuous stage")
    XCTAssertEqual(payload["owner_action"] as? Bool,true)
    XCTAssertThrowsError(try PodcastVisualScoreDecisionPayload.build(
        revisionID:"",eventID:"event-1",action:.accept,note:""
    ))
    XCTAssertThrowsError(try PodcastVisualScoreDecisionPayload.build(
        revisionID:"../../outside",eventID:"event-1",action:.accept,note:""
    ))
    XCTAssertTrue(PodcastVisualScoreBinding.isCurrent(
        ["current_revision_id":revision,"binding_current":true],revisionID:revision
    ))
    XCTAssertFalse(PodcastVisualScoreBinding.isCurrent(
        ["current_revision_id":String(repeating:"b",count:64),"binding_current":true],revisionID:revision
    ))
    XCTAssertFalse(PodcastVisualScoreBinding.isCurrent(
        ["current_revision_id":revision,"binding_current":false],revisionID:revision
    ))
}

func testPodcastVisualScoreArtifactsLoadCurrentRevisionAndTolerateMissingReview() throws {
    let root=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer {try? FileManager.default.removeItem(at:root)}
    let result=try PodcastVisualScoreArtifacts.load(projectPath:root.path)
    switch result {
    case .unavailable(let message):XCTAssertTrue(message.contains("episode map"))
    case .loaded:preconditionFailure("Expected missing artifacts")
    }

    let podcast=root.appendingPathComponent("work/podcast")
    let revisions=podcast.appendingPathComponent("visual-score/revisions")
    let revision=String(repeating:"a",count:64)
    try FileManager.default.createDirectory(at:revisions,withIntermediateDirectories:true)
    try Data("""
    {"schema_version":1,"primary_audio":{"duration_ms":4000},"chapters":[
      {"id":"chapter","title":"Chapter","start_ms":0,"end_ms":4000}
    ]}
    """.utf8).write(to:podcast.appendingPathComponent("episode-map.json"))
    try Data("{\"schema_version\":1,\"revision_id\":\"\(revision)\"}".utf8)
        .write(to:podcast.appendingPathComponent("visual-score/current.json"))
    try Data("""
    {"schema_version":1,"revision_id":"\(revision)","visual_density":"balanced","visual_events":[]}
    """.utf8).write(to:revisions.appendingPathComponent("\(revision).json"))

    let loaded=try PodcastVisualScoreArtifacts.load(projectPath:root.path)
    switch loaded {
    case .unavailable:preconditionFailure("Expected current score")
    case .loaded(let artifacts):
        XCTAssertEqual(artifacts.score.revisionID,revision)
        XCTAssertTrue(artifacts.decisions.decisions.isEmpty)
        XCTAssertEqual(artifacts.episodeMap.durationMS,4000)
    }
}
