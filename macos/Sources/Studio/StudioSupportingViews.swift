import SwiftUI
import AppKit
import StudioCore

struct WorkflowContextInspector:View {
    @EnvironmentObject var w:Workspace
    var workflow:WorkflowInstance? {w.activeWorkflow}
    var step:WorkflowStep? {workflow?.steps.first{$0.id == w.selectedWorkflowStageID}}
    var body:some View {ScrollView {VStack(alignment:.leading,spacing:16) {
        Text("Current context").font(.title3.bold())
        if let workflow {
            GroupBox("Work") {VStack(alignment:.leading,spacing:7) {Label(workflow.name,systemImage:StudioTheme.symbol(forTemplate:workflow.templateID)).font(.headline);if let step {Text(step.label).fontWeight(.semibold);StudioStatus(status:step.status.label);Text(step.detail).font(.caption).foregroundStyle(.secondary)};if !workflow.staleReasons.isEmpty {ForEach(workflow.staleReasons) {reason in Label(reason.detail,systemImage:"exclamationmark.triangle").font(.caption).foregroundStyle(StudioTheme.accent)}}}.padding(10)}
            GroupBox("Bound material") {VStack(alignment:.leading,spacing:7) {Text("\(workflow.inputs.assetIDs.count) source\(workflow.inputs.assetIDs.count == 1 ? "" : "s")");Text("\(workflow.inputs.revisionIDs.count) revision\(workflow.inputs.revisionIDs.count == 1 ? "" : "s")");Text("Changing bound material can make dependent evidence stale.").font(.caption).foregroundStyle(.secondary)}.padding(10)}
            Button("Edit workflow inputs") {w.navigation.select(.currentWork);w.requestEditWorkflowInputs=true}.disabled(w.busy)
        } else {StudioEmptyState(symbol:"sidebar.trailing",title:"No workflow selected",detail:"Open a project and choose work from the sidebar.")}
    }.padding(16)}}
}

struct QualityInspector:View {
    @EnvironmentObject var w:Workspace
    var body:some View {ScrollView {VStack(alignment:.leading,spacing:16) {
        Text("Production QA").font(.title3.bold())
        Text("Technical validation, visual inspection, listening, and owner acceptance remain separate. A successful render is never automatic approval.").foregroundStyle(.secondary)
        ForEach(["before","during","after"],id:\.self) {phase in
            let gate=(w.quality["gates"] as? [String:Any])?[phase] as? [String:Any] ?? [:]
            GroupBox {VStack(alignment:.leading,spacing:8) {HStack {Text(phase.capitalized).font(.headline);Spacer();StudioStatus(status:gate["passed"] as? Bool == true ? "passed" : "pending")};DisclosureGroup("Findings") {Text(prettyJSON(gate["failures"] ?? [])).font(.system(.caption,design:.monospaced)).textSelection(.enabled)}}.padding(8)}
        }
        Button("Open authoritative rules") {NSWorkspace.shared.open(URL(fileURLWithPath:w.engine+"/docs/production-rules.md"))}.accessibilityLabel("Open authoritative production rules")
    }.padding(16)}}
}
