import SwiftUI
import StudioCore

struct ProjectHomeView:View {
    @EnvironmentObject var w:Workspace
    var guide:WorkflowGuideSnapshot? {try? WorkflowGuideSnapshot.parse(w.workflow)}
    var body:some View {
        ScrollView {VStack(alignment:.leading,spacing:22) {
            if w.project.isEmpty {
                StudioEmptyState(symbol:"folder.badge.plus",title:"Create your first production",detail:"Choose New to make a project, or Open to continue an existing production.")
            } else {
                Text("Project Home").font(.title2.bold())
                Text("Continue a deliverable or supporting action without navigating through separate feature pages.").foregroundStyle(.secondary)
                if let guide,let active=guide.activeWorkflow {
                    GroupBox("Continue") {VStack(alignment:.leading,spacing:10) {
                        HStack {Label(active.name,systemImage:StudioTheme.symbol(forTemplate:active.templateID)).font(.headline);Spacer();if let next=guide.nextStep {StudioStatus(status:next.status.label)}}
                        if let next=guide.nextStep {Text(next.label).font(.title3.weight(.semibold));Text(next.detail).foregroundStyle(.secondary);Button("Continue \(next.label)") {w.openWorkflow(active.id,stageID:next.id)}.buttonStyle(.borderedProminent).tint(StudioTheme.button)}
                        else {Text("No next step is reported. Review the saved workflow state before treating this work as complete.").foregroundStyle(.secondary);Button("Open work") {w.openWorkflow(active.id)}}
                    }.padding(12)}
                    workflowGroup("Deliverables",workflows:guide.deliverables,guide:guide)
                    if !guide.supportingActions.isEmpty {workflowGroup("Supporting actions",workflows:guide.supportingActions,guide:guide)}
                } else {
                    StudioEmptyState(symbol:"point.topleft.down.to.point.bottomright.curvepath",title:"No current work",detail:"Choose New Work to create a deliverable or run a supporting action.")
                    Button("New Work",systemImage:"plus") {w.showAddWorkflow()}.buttonStyle(.borderedProminent)
                }
                GroupBox("Shared project context") {VStack(alignment:.leading,spacing:9) {
                    contextRow("Sources",value:"\(w.assets.count)")
                    contextRow("Editing style",value:editingStyleName)
                    contextRow("Unresolved feedback",value:"\(w.unresolvedFeedbackCount)")
                    Button("Open Project Settings") {w.select(.projectSettings)}
                }.padding(12)}
            }
        }.padding(24)}
    }

    @ViewBuilder func workflowGroup(_ title:String,workflows:[WorkflowInstance],guide:WorkflowGuideSnapshot)->some View {
        if !workflows.isEmpty {
            VStack(alignment:.leading,spacing:10) {
                Text(title).font(.headline)
                LazyVGrid(columns:[GridItem(.adaptive(minimum:260),spacing:12)],spacing:12) {
                    ForEach(workflows) {workflow in WorkflowHomeCard(workflow:workflow,template:guide.template(for:workflow),parent:workflow.parentWorkflowID.flatMap{id in guide.workflows.first{$0.id == id}?.name}) {w.openWorkflow(workflow.id)}}
                }
            }
        }
    }
    @ViewBuilder func contextRow(_ label:String,value:String)->some View {HStack {Text(label);Spacer();Text(value).foregroundStyle(.secondary)}.accessibilityElement(children:.combine)}
    var editingStyleName:String {guard let raw=w.data["editing_styles"] as? [String:Any],let parsed=try? EditingStyleConfiguration.parse(raw) else{return "Default guidance"};return parsed.selectedStyle?.name ?? "No selection"}
}

private struct WorkflowHomeCard:View {
    let workflow:WorkflowInstance
    let template:WorkflowTemplate?
    let parent:String?
    let action:()->Void
    var nextStep:WorkflowStep? {workflow.steps.first{[.needsAttention,.current,.ready].contains($0.status)} ?? workflow.steps.first{$0.status != .completed}}
    var body:some View {
        Button(action:action) {VStack(alignment:.leading,spacing:8) {
            HStack {Label(workflow.name,systemImage:StudioTheme.symbol(forTemplate:workflow.templateID)).font(.headline);Spacer();if let nextStep {Image(systemName:nextStep.status.systemImage).accessibilityHidden(true)}}
            Text(template?.name ?? workflow.templateID.replacingOccurrences(of:"_",with:" ").capitalized).font(.caption).foregroundStyle(.secondary)
            if let parent {Text("For \(parent)").font(.caption).foregroundStyle(.secondary)}
            Text(nextStep.map{"Next: \($0.label)"} ?? "No next step reported").lineLimit(2)
        }.frame(maxWidth:.infinity,minHeight:105,alignment:.topLeading).padding(14).background(StudioTheme.panel,in:RoundedRectangle(cornerRadius:12)).overlay(RoundedRectangle(cornerRadius:12).stroke(StudioTheme.border.opacity(0.6)))}.buttonStyle(.plain)
            .accessibilityLabel("\(workflow.name)\(parent.map{", supporting action under \($0)"} ?? ""), \(nextStep.map{$0.status.label+", next step "+$0.label} ?? "no next step reported")")
    }
}
