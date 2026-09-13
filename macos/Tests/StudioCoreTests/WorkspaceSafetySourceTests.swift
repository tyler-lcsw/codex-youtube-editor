import Foundation

private func studioSource(_ name:String) throws -> String {
    let testFile=URL(fileURLWithPath:#filePath)
    let macos=testFile.deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    return try String(contentsOf:macos.appendingPathComponent("Sources/Studio/\(name)"),encoding:.utf8)
}

func testWorkflowEvidenceDraftIsBoundToWorkflowIdentity() throws {
    let guide=try studioSource("WorkflowGuideView.swift")
    let evidence=try studioSource("UnderstandingView.swift")
    XCTAssertTrue(guide.contains("WorkflowEvidenceRecorder(workflowID:workflow.id,selectedStageID:step.id)"))
    XCTAssertTrue(evidence.contains(".onChange(of:workflowID)"))
    XCTAssertTrue(evidence.contains("resetDraft()"))
}

func testReviewAndResourceDraftsResetWhenProjectChanges() throws {
    let review=try studioSource("ReviewView.swift")
    let intake=try studioSource("IntakeView.swift")
    XCTAssertTrue(review.contains("func resetReviewDraft()"))
    XCTAssertTrue(review.contains("onChange(of:w.project){_,_ in resetReviewDraft()"))
    XCTAssertTrue(intake.contains("func resetResourceDraft()"))
    XCTAssertTrue(intake.contains("onChange(of:w.project){_,_ in resetResourceDraft()"))
    XCTAssertTrue(review.contains("Import a source in the Prepare step"))
    XCTAssertFalse(review.contains("Import a source in Brief & sources"))
}

func testCodexSendRequiresCurrentProjectAndWorkflowProvenance() throws {
    let workspace=try studioSource("Workspace.swift")
    let codex=try studioSource("CodexView.swift")
    XCTAssertTrue(workspace.contains("var codexPromptIsCurrent:Bool"))
    XCTAssertTrue(codex.contains("!w.codexPromptIsCurrent"))
    XCTAssertTrue(codex.contains("guard w.codexPromptIsCurrent"))
}

func testProjectOpenOnlyClearsDraftsAfterSelectionSucceeds() throws {
    let workspace=try studioSource("Workspace.swift")
    let newProject=try XCTUnwrap(workspace.range(of:"func newProject()"))
    let openProject=try XCTUnwrap(workspace.range(of:"func openProject()"))
    let importFiles=try XCTUnwrap(workspace.range(of:"func importFiles"))
    let newBody=String(workspace[newProject.lowerBound..<openProject.lowerBound])
    let openBody=String(workspace[openProject.lowerBound..<importFiles.lowerBound])
    for body in [newBody,openBody] {
        let selection=try XCTUnwrap(body.range(of:"try await self.selection.open"))
        let clear=try XCTUnwrap(body.range(of:"self.clearProjectDrafts()"))
        XCTAssertTrue(selection.lowerBound < clear.lowerBound)
    }
}

func testRevisionImportRequiresActiveWorkflowOwnership() throws {
    let workspace=try studioSource("Workspace.swift")
    let review=try studioSource("ReviewView.swift")
    let guide=try studioSource("WorkflowGuideView.swift")
    XCTAssertTrue(workspace.contains("guard !revision || !attachToActiveWorkflow || workflowAtImport != nil"))
    XCTAssertTrue(review.contains("w.activeWorkflow == nil"))
    XCTAssertTrue(guide.contains("w.activeWorkflow == nil"))
}

func testAddWorkflowRequestOnlyArmsAfterSuccessfulNavigation() throws {
    let workspace=try studioSource("Workspace.swift")
    let app=try studioSource("StudioApp.swift")
    XCTAssertTrue(workspace.contains("func showAddWorkflow()"))
    XCTAssertTrue(workspace.contains("guard navigation.destination == .currentWork else{return}"))
    XCTAssertTrue(app.contains("w.showAddWorkflow()"))
}

func testWorkflowWorkspaceEmbedsStagesAndKeepsCodexManual() throws {
    let guide=try studioSource("WorkflowGuideView.swift")
    XCTAssertFalse(guide.contains("w.select(step.destination)"))
    XCTAssertTrue(guide.contains("case \"intake\":BriefView()"))
    XCTAssertTrue(guide.contains("case \"source_understanding\":WorkflowUnderstandingStage"))
    XCTAssertTrue(guide.contains("Work on this step with Codex"))
    XCTAssertTrue(guide.contains("Prepares an editable prompt in the Codex inspector. It does not send the prompt."))
}
