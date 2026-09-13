import Foundation
import StudioCore

func testWorkflowFirstNavigationRemovesCapabilityPagesAsPeers() {
    let titles=StudioNavigationContract.sections.flatMap(\.items).map(\.title)
    XCTAssertEqual(titles,["Project Home","Project Settings","Help"])
    for obsoletePeer in ["Brief","Sources","Revisions","Feedback","Workflow Guide","Editing Styles","Resources","Codex & QA"] {
        XCTAssertFalse(titles.contains(obsoletePeer))
    }
}

func testProjectSettingsSectionTransitionPreservesUnsavedStyleDrafts() {
    XCTAssertTrue(StudioProjectSettingsSection.permitsTransition(hasUnsavedStyleDraft:false,to:.resources))
    XCTAssertTrue(StudioProjectSettingsSection.permitsTransition(hasUnsavedStyleDraft:true,to:.editing))
    XCTAssertFalse(StudioProjectSettingsSection.permitsTransition(hasUnsavedStyleDraft:true,to:.resources))
    XCTAssertFalse(StudioProjectSettingsSection.permitsTransition(hasUnsavedStyleDraft:true,to:.application))
}

func testLegacyNavigationStillLandsInTheConsolidatedShell() {
    let legacyTitles:[String:String]=[
        "Overview":"Project Home",
        "Brief":"Current Work",
        "Sources":"Current Work",
        "Revisions":"Current Work",
        "Feedback":"Current Work",
        "Workflow Guide":"Current Work",
        "Editing Styles":"Project Settings",
        "Resources":"Project Settings",
        "Codex & QA":"Current Work",
        "How to Use":"Help",
    ]
    for (legacy,current) in legacyTitles {
        XCTAssertEqual(StudioDestination(title:legacy).rawValue,current)
    }

    var state=StudioNavigationState()
    for deepLink in ["podcast/setup","review/podcast","workflow/source_understanding"] {
        XCTAssertTrue(state.open(deepLink:deepLink))
        XCTAssertEqual(state.destination.rawValue,"Current Work")
        XCTAssertEqual(state.route.deepLink,deepLink)
    }
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
    XCTAssertEqual(guide.nextStep?.destination.rawValue,"Current Work")
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

func testWorkflowKindsAndParentGroupingRemainExplicit() throws {
    let raw:[String:Any]=[
        "templates":[
            ["id":"long_form_youtube","name":"Long-form YouTube","description":"Main delivery","kind":"deliverable"],
            ["id":"clean_audio","name":"Clean audio","description":"Supporting pass","kind":"supporting_action"],
        ],
        "workflow_instances":[
            ["id":"main","template_id":"long_form_youtube","name":"Main video","kind":"deliverable","inputs":["asset_ids":[],"revision_ids":[],"annotation_ids":NSNull()],"steps":[]],
            ["id":"clean","template_id":"clean_audio","name":"Clean narration","kind":"supporting_action","parent_workflow_id":"main","inputs":["asset_ids":[],"revision_ids":[],"annotation_ids":NSNull()],"steps":[]],
        ],
        "active_workflow_id":"main",
    ]
    let guide=try WorkflowGuideSnapshot.parse(raw)
    XCTAssertEqual(guide.deliverables.map(\.id),["main"])
    XCTAssertEqual(guide.supportingActions.map(\.id),["clean"])
    XCTAssertEqual(guide.supportingActions(parentedTo:"main").map(\.id),["clean"])
    XCTAssertTrue(guide.standaloneActions.isEmpty)
    XCTAssertEqual(guide.template(for:try XCTUnwrap(guide.activeWorkflow))?.kind,.deliverable)
    let unlink=WorkflowGuideSnapshot.parentPayload(workflowID:"clean",parentWorkflowID:nil)
    XCTAssertTrue(unlink["parent_workflow_id"] is NSNull)
}

func testWorkflowGuideUsesEffectiveInputsForAllProjectPresentation() throws {
    let raw:[String:Any]=[
        "templates":[["id":"long_form_youtube","label":"Long-form YouTube","summary":"Edit a video","inputs":[]]],
        "active_workflow_id":"main",
        "workflow_instances":[[
            "id":"main","template_id":"long_form_youtube","name":"Main production","input_mode":"all_project",
            "inputs":["asset_ids":[],"revision_ids":[],"annotation_ids":NSNull()],
            "effective_inputs":["asset_ids":["source-a"],"revision_ids":["revision-a"],"annotation_ids":["note-a"]],
            "steps":[],"stale_reasons":[],
        ]],
    ]
    let workflow=try XCTUnwrap(WorkflowGuideSnapshot.parse(raw).activeWorkflow)
    XCTAssertEqual(workflow.inputs.assetIDs,["source-a"])
    XCTAssertEqual(workflow.inputs.revisionIDs,["revision-a"])
    XCTAssertEqual(workflow.inputs.annotationIDs,["note-a"])
    XCTAssertEqual(workflow.inputMode,.allProject)
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
