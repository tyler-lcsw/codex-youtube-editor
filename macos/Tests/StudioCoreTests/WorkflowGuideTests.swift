import Foundation
import StudioCore

func testGroupedStudioNavigationReplacesPermanentPodcastAndUnderstandingTabs() {
    XCTAssertEqual(StudioNavigationContract.sections.map(\.title),["Project","Work","Project Setup","System"])
    XCTAssertEqual(StudioNavigationContract.sections.flatMap(\.items).map(\.destination),[
        .overview,.brief,.sources,.revisions,.feedback,.workflowGuide,.editingStyles,.resources,.codex,.help
    ])
    XCTAssertFalse(StudioDestination.allCases.map(\.rawValue).contains("Podcast"))
    XCTAssertFalse(StudioDestination.allCases.map(\.rawValue).contains("Understanding"))
    var state=StudioNavigationState()
    XCTAssertTrue(state.open(deepLink:"podcast/setup"));XCTAssertEqual(state.destination,.sources)
    XCTAssertTrue(state.open(deepLink:"review/podcast"));XCTAssertEqual(state.destination,.feedback);XCTAssertEqual(state.reviewArea,.podcast)
    XCTAssertTrue(state.open(deepLink:"workflow/source_understanding"));XCTAssertEqual(state.destination,.workflowGuide)
}

func testWorkflowGuideParsesExplicitContextWithoutInventingProgress() throws {
    let raw:[String:Any]=[
        "templates":[[
            "id":"solo_podcast","name":"Solo podcast","description":"Audio-first episode",
            "inputs":[["id":"primary_audio_asset_id","label":"Primary audio","required":true]]
        ]],
        "workflow_instances":[[
            "id":"workflow-1","template_id":"solo_podcast","name":"Episode workflow",
            "inputs":["asset_ids":["audio-1"],"revision_ids":[],"annotation_ids":NSNull()],
            "stale_reasons":[["code":"input_binding_changed","message":"A bound source changed."]],
            "steps":[
                ["id":"sources","label":"Choose sources","status":"completed","destination":"Sources"],
                ["id":"plan","label":"Plan visuals","status":"ready","destination":"Codex & QA","prompt":"Draft an evidence-bound visual plan."],
                ["id":"render","label":"Render","status":"blocked","destination":"Revisions"]
            ]
        ]],
        "active_workflow_id":"workflow-1"
    ]
    let guide=try WorkflowGuideSnapshot.parse(raw)
    XCTAssertEqual(guide.activeWorkflow?.name,"Episode workflow")
    XCTAssertEqual(guide.nextStep?.id,"plan")
    XCTAssertEqual(guide.nextStep?.status,.ready)
    XCTAssertEqual(guide.nextStep?.prompt,"Draft an evidence-bound visual plan.")
    XCTAssertTrue(guide.isActiveSoloPodcast)
    XCTAssertEqual(guide.activeWorkflow?.staleReasons,[WorkflowStaleReason(code:"input_binding_changed",detail:"A bound source changed.")])
    XCTAssertNil(guide.percentComplete)
}

func testWorkflowGuidePrefersTemplateDetailMapsPendingToReadyAndExplainsStaleState() throws {
    let raw:[String:Any]=["stages":[
        ["id":"intake","label":"Define production","status":"pending","instructions":"Generic instructions","detail":"Template-specific detail","destination":"Brief"],
        ["id":"source_understanding","label":"Understand source","status":"stale","detail":"Inspect the selected source","destination":"Sources","stale_reasons":[["code":"inputs_changed","detail":"Bound source files changed."]]]
    ]]
    let guide=try WorkflowGuideSnapshot.parse(raw)
    let steps=try XCTUnwrap(guide.activeWorkflow?.steps)
    XCTAssertEqual(steps[0].status,.ready)
    XCTAssertEqual(steps[0].detail,"Template-specific detail")
    XCTAssertEqual(steps[1].staleReasons,[WorkflowStaleReason(code:"inputs_changed",detail:"Bound source files changed.")])
}

func testWorkflowGuideBuildsHonestLegacyFallbackFromCurrentStageStates() throws {
    let raw:[String:Any]=["stages":[
        ["id":"intake","label":"Intake","status":"complete","instructions":"Confirm the brief."],
        ["id":"source_understanding","label":"Source understanding","status":"stale","instructions":"Review changed source evidence."],
        ["id":"edit","label":"Edit","status":"blocked","instructions":"Wait for prerequisites."]
    ]]
    let guide=try WorkflowGuideSnapshot.parse(raw)
    XCTAssertTrue(guide.isLegacyFallback)
    XCTAssertEqual(guide.activeWorkflow?.steps.map(\.status),[.completed,.needsAttention,.blocked])
    XCTAssertEqual(guide.nextStep?.id,"source_understanding")
    XCTAssertEqual(guide.nextStep?.destination,.workflowGuide)
}

func testWorkflowCreateAndInputPayloadsAreExplicit() throws {
    let template=WorkflowTemplate(id:"solo",name:"Solo podcast",summary:"Audio-first",inputs:[])
    let create=template.createPayload(name:"Episode",assetIDs:["audio-1"],revisionIDs:["revision-1"])
    XCTAssertEqual(create["template_id"] as? String,"solo")
    XCTAssertEqual(((create["inputs"] as? [String:Any])?["asset_ids"] as? [String]),["audio-1"])
    let payload=WorkflowGuideSnapshot.inputPayload(workflowID:"workflow-1",inputs:WorkflowInputs(assetIDs:["audio-1"],revisionIDs:[]))
    XCTAssertEqual(payload["workflow_id"] as? String,"workflow-1")
    XCTAssertEqual(((payload["inputs"] as? [String:Any])?["asset_ids"] as? [String]),["audio-1"])
}


func testCodexDraftIsBoundToProjectAndWorkflow() {
    let draft=CodexDraft(text:"Plan this edit",projectID:"/projects/one",workflowID:"workflow-a")
    XCTAssertTrue(draft.isValid(projectID:"/projects/one",workflowID:"workflow-a"))
    XCTAssertFalse(draft.isValid(projectID:"/projects/two",workflowID:"workflow-a"))
    XCTAssertFalse(draft.isValid(projectID:"/projects/one",workflowID:"workflow-b"))
    XCTAssertFalse(draft.isValid(projectID:"/projects/one",workflowID:nil))
}

func testRevisionAttachmentPreservesExistingWorkflowInputs() {
    let initial=WorkflowInputs(assetIDs:["source-a"],revisionIDs:["revision-a"],annotationIDs:["note-a"])
    let updated=initial.addingRevisionIDs(["revision-b","revision-a"])
    XCTAssertEqual(updated.assetIDs,["source-a"])
    XCTAssertEqual(updated.revisionIDs,["revision-a","revision-b"])
    XCTAssertEqual(updated.annotationIDs,["note-a"])
}

func testFeedbackSummaryCountsOnlyUnresolvedAnnotations() {
    let annotations:[[String:Any]]=[
        ["id":"a","status":"open"],
        ["id":"b","status":"addressed"],
        ["id":"c","status":"ready_for_review"],
        ["id":"d","status":"accepted"]
    ]
    XCTAssertEqual(FeedbackSummary.unresolvedCount(annotations),3)
}
