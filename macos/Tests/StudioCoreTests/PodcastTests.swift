import Foundation
import StudioCore

func testPodcastConfigurationParsesMediaAndBuildsPatchPayload() throws {
    let records:[[String:Any]] = [
        ["id":"audio-1","label":"Episode master.wav","role":"source","stream_types":["audio"]],
        ["id":"camera-1","label":"Camera.mp4","role":"source","stream_types":["audio","video"]],
        ["id":"notes-1","label":"Notes","role":"document","stream_types":[]],
    ]
    let media = try PodcastMediaOption.options(from:records)
    XCTAssertEqual(media.count,2)
    XCTAssertTrue(media[0].canBePrimaryAudio)
    XCTAssertFalse(media[0].canBeCamera)
    XCTAssertTrue(media[1].canBePrimaryAudio)
    XCTAssertTrue(media[1].canBeCamera)

    let project:[String:Any] = ["podcast":[
        "schema_version":1,"kind":"solo_audio_first",
        "primary_audio_asset_id":"audio-1","camera_asset_id":"camera-1",
        "visual_density":"illustrative",
    ]]
    let saved = try XCTUnwrap(PodcastConfiguration.from(project:project))
    XCTAssertEqual(saved.primaryAudioAssetID,"audio-1")
    XCTAssertEqual(saved.cameraAssetID,"camera-1")
    XCTAssertEqual(saved.visualDensity,.illustrative)

    let payload = try PodcastConfiguration(
        primaryAudioAssetID:"audio-1", cameraAssetID:nil, visualDensity:.restrained
    ).patchPayload()
    XCTAssertEqual(payload["primary_audio_asset_id"] as? String,"audio-1")
    XCTAssertTrue(payload["camera_asset_id"] is NSNull)
    XCTAssertEqual(payload["visual_density"] as? String,"restrained")
}

func testPodcastConfigurationHandlesLegacyCapabilitiesAndRejectsMalformedState() throws {
    let legacy = try PodcastMediaOption.options(from:[
        ["id":"legacy-1","label":"Older import","role":"source"]
    ])
    XCTAssertEqual(legacy.count,1)
    XCTAssertTrue(legacy[0].needsCapabilityValidation)
    XCTAssertTrue(legacy[0].canBePrimaryAudio)
    XCTAssertTrue(legacy[0].canBeCamera)

    for podcast in [
        ["schema_version":2,"kind":"solo_audio_first","primary_audio_asset_id":"a","visual_density":"balanced"],
        ["schema_version":1,"kind":"group","primary_audio_asset_id":"a","visual_density":"balanced"],
        ["schema_version":1,"kind":"solo_audio_first","primary_audio_asset_id":"a","visual_density":"dense"],
    ] as [[String:Any]] {
        XCTAssertThrowsError(try PodcastConfiguration.from(project:["podcast":podcast]))
    }
    XCTAssertThrowsError(try PodcastMediaOption.options(from:[
        ["id":"bad","label":"Bad metadata","role":"source","stream_types":["subtitle"]]
    ]))
    XCTAssertThrowsError(try PodcastConfiguration(
        primaryAudioAssetID:" ",cameraAssetID:nil,visualDensity:.balanced
    ).patchPayload())
}

func testReviewMarkerDecisionSeparatesAudioTimeFromVideoCapture() {
    XCTAssertEqual(ReviewMarkerDecision.action(seconds:1.2346,hasVideo:false),.markTime(1235))
    XCTAssertEqual(ReviewMarkerDecision.action(seconds:1.2346,hasVideo:true),.captureFrame(1235))
    XCTAssertNil(ReviewMarkerDecision.action(seconds:.nan,hasVideo:false))
    XCTAssertNil(ReviewMarkerDecision.action(seconds:-0.001,hasVideo:true))
    XCTAssertNil(ReviewMarkerDecision.action(seconds:Double.greatestFiniteMagnitude,hasVideo:false))
}
