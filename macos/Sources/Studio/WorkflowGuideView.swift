import SwiftUI
import StudioCore

struct ProjectOverviewView:View {
    @EnvironmentObject var w:Workspace
    var guide:WorkflowGuideSnapshot? {try? WorkflowGuideSnapshot.parse(w.workflow)}
    var body:some View {
        ScrollView {VStack(alignment:.leading,spacing:20) {
            if w.project.isEmpty {StudioEmptyState(symbol:"folder.badge.plus",title:"Create your first production",detail:"Choose New to make a project, or Open to continue an existing production.")}
            Text("Project overview").font(.title2.bold())
            Text("See what is in the project and the next evidence-based workflow step. Completion is shown only when the saved workflow says it is complete.").foregroundStyle(.secondary)
            if let workflow=guide?.activeWorkflow {
                GroupBox("Active workflow") {VStack(alignment:.leading,spacing:10) {
                    HStack {Text(workflow.name).font(.headline);Spacer();if let next=guide?.nextStep {StudioStatus(status:next.status.label)}}
                    if let next=guide?.nextStep {Text("Next: \(next.label)").font(.title3.weight(.semibold));Text(next.detail).foregroundStyle(.secondary)}
                    else {Text("No next step is reported. Review the saved workflow state before treating the project as complete.").foregroundStyle(.secondary)}
                    Button("Open Workflow Guide") {w.select(.workflowGuide)}
                }.padding(12)}
            } else {
                StudioEmptyState(symbol:"point.topleft.down.to.point.bottomright.curvepath",title:"No active workflow",detail:"Open Workflow Guide and add a workflow for this project.")
                Button("Open Workflow Guide") {w.select(.workflowGuide)}
            }
            HStack(spacing:14) {
                ProjectCountCard(title:"Sources",value:w.assets.count,symbol:"tray.and.arrow.down",action:{w.select(.sources)})
                ProjectCountCard(title:"Revisions",value:w.revisions.count,symbol:"film.stack",action:{w.select(.revisions)})
                ProjectCountCard(title:"Unresolved feedback",value:w.unresolvedFeedbackCount,symbol:"text.bubble",action:{w.select(.feedback)})
            }
            GroupBox("Project context") {VStack(alignment:.leading,spacing:8) {
                OverviewRow(label:"Brief",value:(w.data["brief"] as? [String:Any])?.isEmpty == false ? "Started" : "Not started")
                OverviewRow(label:"Editing style",value:editingStyleName)
                if hasSoloPodcastWorkflow {OverviewRow(label:"Podcast",value:w.data["podcast"] is [String:Any] ? "Solo audio-first configured" : "Workflow added · sources not configured")}
            }.padding(12)}
        }.padding(24)}
    }
    var editingStyleName:String {
        guard let raw=w.data["editing_styles"] as? [String:Any],let parsed=try? EditingStyleConfiguration.parse(raw) else{return "Default guidance"}
        return parsed.selectedStyle?.name ?? "No selection"
    }
    var hasSoloPodcastWorkflow:Bool {guide?.workflows.contains(where:\.isSoloPodcast) == true || w.data["podcast"] is [String:Any]}
}

private struct ProjectCountCard:View {
    let title:String;let value:Int;let symbol:String;let action:()->Void
    var body:some View {Button(action:action) {VStack(alignment:.leading,spacing:9) {
        Label(title,systemImage:symbol).font(.headline);Text("\(value)").font(.system(size:28,weight:.semibold,design:.rounded));Text("Open \(title.lowercased())").font(.caption).foregroundStyle(.secondary)
    }.frame(maxWidth:.infinity,alignment:.leading).padding(16).background(StudioTheme.panel,in:RoundedRectangle(cornerRadius:12)).overlay(RoundedRectangle(cornerRadius:12).stroke(StudioTheme.border.opacity(0.6)))}.buttonStyle(.plain).accessibilityLabel("\(title), \(value). Open \(title.lowercased()).")}
}

private struct OverviewRow:View {
    let label:String;let value:String
    var body:some View {HStack {Text(label);Spacer();Text(value).foregroundStyle(.secondary)}.accessibilityElement(children:.combine)}
}

struct RevisionsView:View {
    @EnvironmentObject var w:Workspace
    var body:some View {ScrollView {VStack(alignment:.leading,spacing:18) {
        Text("Revisions").font(.title2.bold())
        Text("Add successful renders as revisions, then open Feedback to compare and annotate them. A revision is not acceptance.").foregroundStyle(.secondary)
        Button("Add rendered revision",systemImage:"plus") {w.importFiles(revision:true,attachToActiveWorkflow:true)}.buttonStyle(.borderedProminent).tint(StudioTheme.button).disabled(w.project.isEmpty || w.busy || w.activeWorkflow == nil)
        if w.revisions.isEmpty {StudioEmptyState(symbol:"film.stack",title:"No revisions yet",detail:"Render through the approved workflow, then register the result here for review.")}
        ForEach(w.revisions.indices,id:\.self) {index in
            let revision=w.revisions[index]
            GroupBox {VStack(alignment:.leading,spacing:7) {
                Text(revision["label"] as? String ?? "Revision").font(.headline)
                Text(revision["path"] as? String ?? "").font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
                if let duration=revision["duration_ms"] as? Int {Text(String(format:"%.1f seconds",Double(duration)/1000)).font(.caption)}
                if let id=revision["id"] as? String,!workflowNames(for:id).isEmpty {Text("Workflows: \(workflowNames(for:id).joined(separator:", "))").font(.caption).foregroundStyle(.secondary)}
                Button("Review this revision") {if let id=revision["id"] as? String {w.openFeedback(reviewing:id)}}
            }.padding(10)}
        }
    }.padding(24)}}
    func workflowNames(for revisionID:String)->[String] {
        let guide=try? WorkflowGuideSnapshot.parse(w.workflow)
        return guide?.workflows.filter{$0.inputs.revisionIDs.contains(revisionID)}.map(\.name) ?? []
    }
}

struct FeedbackView:View {
    var body:some View {ReviewView()}
}

struct WorkflowContextBar:View {
    @EnvironmentObject var w:Workspace
    var guide:WorkflowGuideSnapshot? {try? WorkflowGuideSnapshot.parse(w.workflow)}
    var body:some View {
        if !w.project.isEmpty,let workflow=guide?.activeWorkflow {
            HStack(spacing:10) {
                Image(systemName:"point.topleft.down.to.point.bottomright.curvepath").accessibilityHidden(true)
                Text(workflow.name).font(.subheadline.weight(.semibold)).lineLimit(1)
                if let next=guide?.nextStep {Text("Next: \(next.label)").font(.caption).foregroundStyle(.secondary).lineLimit(1);StudioStatus(status:next.status.label)}
                else {Text("No next step reported").font(.caption).foregroundStyle(.secondary)}
                Spacer()
                Button("Guide") {w.select(.workflowGuide)}.controlSize(.small)
            }.padding(.horizontal,24).padding(.vertical,9).background(StudioTheme.panel.opacity(0.75)).accessibilityElement(children:.contain)
        }
    }
}

struct WorkflowGuideView:View {
    // Workspace merges the bridge's workflow_instances and templates envelopes with the active stage response.
    @EnvironmentObject var w:Workspace
    @State private var showingAdd=false
    @State private var showingInputs=false
    var guide:WorkflowGuideSnapshot? {try? WorkflowGuideSnapshot.parse(w.workflow)}
    var body:some View {
      ScrollView {VStack(alignment:.leading,spacing:20) {
        HStack {VStack(alignment:.leading,spacing:5) {Text("Workflow Guide").font(.title2.bold());Text("Follow the project’s actual state. Studio never converts a render or button press into manual completion.").foregroundStyle(.secondary)};Spacer();Button("Add Workflow",systemImage:"plus") {showingAdd=true}.disabled(w.project.isEmpty || w.busy)}
        if let guide {
            if guide.workflows.count > 1 {
                Picker("Active workflow",selection:Binding(get:{guide.activeWorkflowID ?? guide.workflows.first?.id ?? ""},set:selectWorkflow)) {ForEach(guide.workflows) {Text($0.name).tag($0.id)}}.disabled(w.busy)
            }
            if let workflow=guide.activeWorkflow {
                HStack {Text(workflow.name).font(.title3.bold());if guide.isLegacyFallback {Text("Legacy workflow").font(.caption).foregroundStyle(.secondary)};Spacer();Button("Edit workflow inputs") {showingInputs=true}.disabled(w.busy)}
                if !workflow.staleReasons.isEmpty {GroupBox("Workflow inputs need attention") {VStack(alignment:.leading,spacing:5) {ForEach(workflow.staleReasons) {reason in Label(reason.detail,systemImage:"exclamationmark.triangle").foregroundStyle(StudioTheme.accent)}}.padding(10)}}
                ForEach(Array(workflow.steps.enumerated()),id:\.element.id) {index,step in WorkflowStepCard(number:index+1,step:step,primaryAction:{w.select(step.destination)},promptAction:{prefillCodex(for:step)})}
                WorkflowEvidenceRecorder(workflowID:workflow.id).id(workflow.id)
            } else {StudioEmptyState(symbol:"point.topleft.down.to.point.bottomright.curvepath",title:"No active workflow",detail:"Add a workflow to get contextual next steps for this project.")}
        } else {StudioEmptyState(symbol:"exclamationmark.triangle",title:"Workflow state could not be read",detail:"Refresh the project. Invalid state is never treated as progress.")}
      }.padding(24)}
    .sheet(isPresented:$showingAdd) {AddWorkflowSheet(templates:guide?.templates ?? [],assets:w.assets,revisions:w.revisions) {template,name,inputs in create(template:template,name:name,inputs:inputs)}}
    .sheet(isPresented:$showingInputs) {if let workflow=guide?.activeWorkflow,let template=guide?.templates.first(where:{$0.id == workflow.templateID}) {WorkflowInputsSheet(template:template,initial:workflow.inputs,assets:w.assets,revisions:w.revisions) {inputs in updateInputs(workflowID:workflow.id,inputs:inputs)}} else {StudioEmptyState(symbol:"exclamationmark.triangle",title:"Inputs unavailable",detail:"This legacy workflow does not expose editable inputs.").frame(minWidth:480,minHeight:260)}}
    .onAppear {if w.requestAddWorkflow {w.requestAddWorkflow=false;showingAdd=true}}
    .onChange(of:w.requestAddWorkflow) {_,requested in if requested {w.requestAddWorkflow=false;showingAdd=true}}
    }

    func selectWorkflow(_ id:String) {w.perform {try await w.request("select_workflow",["workflow_id":id]);w.notice="Active workflow changed."}}
    func create(template:WorkflowTemplate,name:String,inputs:WorkflowInputs) {guard !name.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else {w.error="Workflow name is required.";return};let payload=template.createPayload(name:name,assetIDs:inputs.assetIDs,revisionIDs:inputs.revisionIDs);showingAdd=false;w.perform {try await w.request("create_workflow",payload);w.notice="Workflow added."}}
    func updateInputs(workflowID:String,inputs:WorkflowInputs) {showingInputs=false;w.perform {try await w.request("update_workflow_inputs",WorkflowGuideSnapshot.inputPayload(workflowID:workflowID,inputs:inputs));w.notice="Workflow inputs updated; dependent steps reassessed."}}
    func prefillCodex(for step:WorkflowStep) {w.updateCodexPrompt(step.prompt ?? "Help me complete the \(step.label) step for the active workflow. Produce or update the required project-local evidence, and do not mark the step complete without current evidence.");w.select(.codex)}
}

private struct WorkflowStepCard:View {
    let number:Int;let step:WorkflowStep;let primaryAction:()->Void;let promptAction:()->Void
    var body:some View {GroupBox {HStack(alignment:.top,spacing:14) {
        Image(systemName:step.status.systemImage).font(.title2).foregroundStyle(step.status == .completed ? .green : StudioTheme.accent).accessibilityHidden(true)
        VStack(alignment:.leading,spacing:7) {HStack {Text("\(number). \(step.label)").font(.headline);StudioStatus(status:step.status.label)};if !step.detail.isEmpty {Text(step.detail).foregroundStyle(.secondary).fixedSize(horizontal:false,vertical:true)};if !step.staleReasons.isEmpty {VStack(alignment:.leading,spacing:4) {ForEach(step.staleReasons) {reason in Label(reason.detail,systemImage:"exclamationmark.triangle").font(.caption).foregroundStyle(StudioTheme.accent)}}};if step.status != .completed && step.status != .blocked {HStack {if step.destination != .workflowGuide {Button("Open \(step.destination.rawValue)",action:primaryAction)};if step.prompt != nil {Button("Prepare editable Codex prompt",action:promptAction)}}}}
        Spacer()
    }.padding(12)}.accessibilityElement(children:.contain).accessibilityLabel("Step \(number), \(step.label), \(step.status.label)")}
}

private struct AddWorkflowSheet:View {
    @Environment(\.dismiss) var dismiss
    let templates:[WorkflowTemplate];let assets:[[String:Any]];let revisions:[[String:Any]];let onCreate:(WorkflowTemplate,String,WorkflowInputs)->Void
    @State private var selectedID="";@State private var name="";@State private var selectedAsset="";@State private var selectedRevision=""
    var selected:WorkflowTemplate? {templates.first {$0.id == selectedID} ?? templates.first}
    var body:some View {VStack(alignment:.leading,spacing:16) {HStack {Text("Add Workflow").font(.title2.bold());Spacer();Button("Cancel") {dismiss()}.keyboardShortcut(.cancelAction)};if templates.isEmpty {StudioEmptyState(symbol:"exclamationmark.triangle",title:"No workflow templates available",detail:"Refresh after restoring the workflow template catalog.")} else {Picker("Template",selection:Binding(get:{selected?.id ?? ""},set:{selectedID=$0;selectedAsset="";selectedRevision=""})) {ForEach(templates) {Text($0.name).tag($0.id)}};if let selected {Text(selected.summary).foregroundStyle(.secondary);TextField("Workflow name",text:$name).textFieldStyle(.roundedBorder);OptionalMediaPickers(assets:assets,revisions:revisions,selectedAsset:$selectedAsset,selectedRevision:$selectedRevision);HStack {Spacer();Button("Add Workflow") {onCreate(selected,name,WorkflowInputs(assetIDs:selectedAsset.isEmpty ? [] : [selectedAsset],revisionIDs:selectedRevision.isEmpty ? [] : [selectedRevision]))}.buttonStyle(.borderedProminent).disabled(name.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty)}}}}.padding(24).frame(minWidth:620,minHeight:420).onAppear {selectedID=templates.first?.id ?? ""}}
}

private struct WorkflowInputsSheet:View {
    @Environment(\.dismiss) var dismiss
    let template:WorkflowTemplate;let initial:WorkflowInputs;let assets:[[String:Any]];let revisions:[[String:Any]];let onSave:(WorkflowInputs)->Void
    @State private var assetIDs=Set<String>();@State private var revisionIDs=Set<String>()
    var body:some View {VStack(alignment:.leading,spacing:16) {HStack {Text("Workflow inputs").font(.title2.bold());Spacer();Button("Cancel") {dismiss()}.keyboardShortcut(.cancelAction)};Text(template.name).font(.headline);Text("Choose the project material this workflow owns. Feedback remains bound automatically unless the backend exposes a narrower annotation selection.").foregroundStyle(.secondary);MediaChecklist(title:"Sources",items:assets,selection:$assetIDs);MediaChecklist(title:"Output revisions",items:revisions,selection:$revisionIDs);Spacer();HStack {Spacer();Button("Save inputs") {onSave(WorkflowInputs(assetIDs:Array(assetIDs).sorted(),revisionIDs:Array(revisionIDs).sorted(),annotationIDs:initial.annotationIDs))}.buttonStyle(.borderedProminent)}}.padding(24).frame(minWidth:620,minHeight:520).onAppear {assetIDs=Set(initial.assetIDs);revisionIDs=Set(initial.revisionIDs)}}
}

private struct OptionalMediaPickers:View {
    let assets:[[String:Any]];let revisions:[[String:Any]];@Binding var selectedAsset:String;@Binding var selectedRevision:String
    var body:some View {GroupBox("Optional workflow inputs") {VStack(alignment:.leading,spacing:10) {
        Picker("Source",selection:$selectedAsset) {Text("Choose later").tag("");ForEach(assets.indices,id:\.self) {index in Text(assets[index]["label"] as? String ?? "Source").tag(assets[index]["id"] as? String ?? "")}}
        Picker("Output revision",selection:$selectedRevision) {Text("Choose later").tag("");ForEach(revisions.indices,id:\.self) {index in Text(revisions[index]["label"] as? String ?? "Revision").tag(revisions[index]["id"] as? String ?? "")}}
    }.padding(10)}}
}

private struct MediaChecklist:View {
    let title:String;let items:[[String:Any]];@Binding var selection:Set<String>
    var body:some View {GroupBox(title) {VStack(alignment:.leading,spacing:8) {if items.isEmpty {Text("None available").foregroundStyle(.secondary)};ForEach(items.indices,id:\.self) {index in let item=items[index],id=item["id"] as? String ?? "";Toggle(item["label"] as? String ?? "Item",isOn:Binding(get:{selection.contains(id)},set:{if $0 {selection.insert(id)} else {selection.remove(id)}})).disabled(id.isEmpty)}}.padding(10)}}
}
