import SwiftUI
import StudioCore

struct WorkflowGuideView:View {
    // Workspace merges the bridge's workflow_instances and template catalog with current stage evidence.
    @EnvironmentObject var w:Workspace
    @State private var showingAdd=false
    @State private var showingInputs=false
    var guide:WorkflowGuideSnapshot? {try? WorkflowGuideSnapshot.parse(w.workflow)}
    var workflow:WorkflowInstance? {guide?.activeWorkflow}
    var selectedStep:WorkflowStep? {
        guard let workflow else{return nil}
        return workflow.steps.first {$0.id == w.selectedWorkflowStageID} ?? guide?.nextStep ?? workflow.steps.first
    }

    var body:some View {
        Group {
            if w.project.isEmpty {
                StudioEmptyState(symbol:"folder.badge.plus",title:"Create your first production",detail:"Choose New to make a project, or Open to continue an existing production.")
            } else if let guide,let workflow {
                VStack(spacing:0) {
                    WorkflowWorkspaceHeader(workflow:workflow,template:guide.template(for:workflow),showInputs:{showingInputs=true})
                    Divider()
                    HSplitView {
                        WorkflowStageRail(workflow:workflow,selectedStageID:w.selectedWorkflowStageID) {w.selectWorkflowStage($0)}
                            .frame(minWidth:220,idealWidth:250,maxWidth:285)
                        if let selectedStep {
                            WorkflowStageContent(workflow:workflow,step:selectedStep).id(workflow.id+":"+selectedStep.id)
                        } else {
                            StudioEmptyState(symbol:"list.number",title:"No workflow steps",detail:"Refresh after restoring the project workflow configuration.")
                        }
                    }
                }
            } else {
                VStack(spacing:18) {
                    StudioEmptyState(symbol:"point.topleft.down.to.point.bottomright.curvepath",title:"No current work",detail:"Choose New Work to create a deliverable or run a supporting action.")
                    Button("New Work",systemImage:"plus") {showingAdd=true}.buttonStyle(.borderedProminent).disabled(w.busy)
                }
            }
        }
        .sheet(isPresented:$showingAdd) {
            AddWorkflowSheet(templates:guide?.templates ?? [],deliverables:guide?.deliverables ?? [],assets:w.assets,revisions:w.revisions) {template,name,inputs,parentID in
                create(template:template,name:name,inputs:inputs,parentWorkflowID:parentID)
            }
        }
        .sheet(isPresented:$showingInputs) {
            if let workflow,let template=guide?.template(for:workflow) {
                WorkflowInputsSheet(template:template,initial:workflow.inputs,followsAllProjectMedia:workflow.inputMode == .allProject,assets:w.assets,revisions:w.revisions) {inputs in updateInputs(workflowID:workflow.id,inputs:inputs)}
            } else {
                StudioEmptyState(symbol:"exclamationmark.triangle",title:"Inputs unavailable",detail:"This workflow does not expose editable inputs.").frame(minWidth:480,minHeight:260)
            }
        }
        .onAppear {chooseInitialStage();if w.requestAddWorkflow {w.requestAddWorkflow=false;showingAdd=true};if w.requestEditWorkflowInputs {w.requestEditWorkflowInputs=false;showingInputs=true}}
        .onChange(of:w.requestAddWorkflow) {_,requested in if requested {w.requestAddWorkflow=false;showingAdd=true}}
        .onChange(of:w.requestEditWorkflowInputs) {_,requested in if requested {w.requestEditWorkflowInputs=false;showingInputs=true}}
        .onChange(of:w.activeWorkflowID) {_,_ in chooseInitialStage()}
    }

    func chooseInitialStage() {
        guard let workflow else{return}
        if !workflow.steps.contains(where:{$0.id == w.selectedWorkflowStageID}) {w.selectedWorkflowStageID=w.preferredStageID()}
    }
    func create(template:WorkflowTemplate,name:String,inputs:WorkflowInputs,parentWorkflowID:String?) {
        guard !name.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else {w.error="Work name is required.";return}
        let payload=template.createPayload(name:name,assetIDs:inputs.assetIDs,revisionIDs:inputs.revisionIDs,parentWorkflowID:parentWorkflowID)
        showingAdd=false
        w.perform {try await w.request("create_workflow",payload);w.navigation.select(.currentWork);w.selectedWorkflowStageID=w.preferredStageID();w.notice="New work added. Start with the current step; completion still requires current evidence."}
    }
    func updateInputs(workflowID:String,inputs:WorkflowInputs) {
        guard !w.busy else {return}
        showingInputs=false
        w.perform {try await w.request("update_workflow_inputs",WorkflowGuideSnapshot.inputPayload(workflowID:workflowID,inputs:inputs));w.notice="Workflow inputs updated; dependent steps reassessed."}
    }
}

private struct WorkflowWorkspaceHeader:View {
    @EnvironmentObject var w:Workspace
    let workflow:WorkflowInstance
    let template:WorkflowTemplate?
    let showInputs:()->Void
    var body:some View {
        HStack(alignment:.firstTextBaseline,spacing:12) {
            VStack(alignment:.leading,spacing:5) {
                HStack(spacing:8) {Label(workflow.name,systemImage:StudioTheme.symbol(forTemplate:workflow.templateID)).font(.title2.bold());StudioStatus(status:workflow.staleReasons.isEmpty ? "current" : "stale")}
                Text(template?.summary ?? "Follow the project’s evidence-backed steps.").foregroundStyle(.secondary).fixedSize(horizontal:false,vertical:true)
            }
            Spacer()
            Button("Edit inputs",systemImage:"slider.horizontal.3",action:showInputs).accessibilityLabel("Edit inputs for \(workflow.name)").disabled(w.busy)
        }.padding(20)
    }
}

private struct WorkflowStageRail:View {
    let workflow:WorkflowInstance
    let selectedStageID:String
    let select:(String)->Void
    var body:some View {
        ScrollView {VStack(alignment:.leading,spacing:8) {
            Text("Steps").font(.headline).padding(.horizontal,14).padding(.top,16)
            ForEach(Array(workflow.steps.enumerated()),id:\.element.id) {index,step in
                Button {select(step.id)} label: {
                    HStack(alignment:.top,spacing:10) {
                        ZStack {Circle().fill(step.id == selectedStageID ? StudioTheme.accent : StudioTheme.border.opacity(0.45)).frame(width:28,height:28);Text("\(index+1)").font(.caption.bold()).foregroundStyle(step.id == selectedStageID ? Color.white : StudioTheme.text)}.accessibilityHidden(true)
                        VStack(alignment:.leading,spacing:3) {Text(step.label).font(.subheadline.weight(.semibold)).multilineTextAlignment(.leading);Label(step.status.label,systemImage:step.status.systemImage).font(.caption).foregroundStyle(.secondary)}
                        Spacer(minLength:0)
                    }.frame(maxWidth:.infinity,alignment:.leading).padding(10).contentShape(Rectangle())
                }.buttonStyle(.plain).background(step.id == selectedStageID ? StudioTheme.accent.opacity(0.11) : Color.clear,in:RoundedRectangle(cornerRadius:10))
                    .accessibilityLabel("Step \(index+1) of \(workflow.steps.count), \(step.label), \(step.status.label)")
                    .accessibilityAddTraits(step.id == selectedStageID ? .isSelected : [])
            }
        }.padding(.horizontal,8).padding(.bottom,16)}.background(StudioTheme.panel.opacity(0.55))
    }
}

private struct WorkflowStageContent:View {
    let workflow:WorkflowInstance
    let step:WorkflowStep
    var body:some View {
        VStack(spacing:0) {
            WorkflowStageIntro(workflow:workflow,step:step)
            Divider()
            switch step.id {
            case "intake":BriefView()
            case "source_understanding":WorkflowUnderstandingStage(workflow:workflow,step:step)
            case "editorial_strategy":WorkflowPlanStage(workflow:workflow,step:step)
            case "edit":RevisionsView()
            case "final_review":ReviewView()
            default:WorkflowEvidenceStage(workflow:workflow,step:step)
            }
        }.frame(maxWidth:.infinity,maxHeight:.infinity)
    }
}

private struct WorkflowStageIntro:View {
    @EnvironmentObject var w:Workspace
    let workflow:WorkflowInstance
    let step:WorkflowStep
    var body:some View {
        VStack(alignment:.leading,spacing:10) {
            HStack(alignment:.firstTextBaseline) {Text(step.label).font(.title2.bold());StudioStatus(status:step.status.label);Spacer()}
            Text(step.detail).foregroundStyle(.secondary).fixedSize(horizontal:false,vertical:true)
            if !step.staleReasons.isEmpty {VStack(alignment:.leading,spacing:4) {ForEach(step.staleReasons) {reason in Label(reason.detail,systemImage:"exclamationmark.triangle").font(.caption).foregroundStyle(StudioTheme.accent)}}}
            if let prompt=step.prompt,step.status != .completed,step.status != .blocked {
                Button("Work on this step with Codex",systemImage:"sparkles") {prefillCodex(prompt)}.buttonStyle(.borderedProminent).tint(StudioTheme.button).accessibilityHint("Prepares an editable prompt in the Codex inspector. It does not send the prompt.")
            }
        }.padding(20).accessibilityElement(children:.contain)
    }
    func prefillCodex(_ prompt:String) {w.showCodex(prompt)}
}

private struct WorkflowUnderstandingStage:View {
    let workflow:WorkflowInstance
    let step:WorkflowStep
    @State private var showingEvidence=false
    var body:some View {
        VStack(spacing:0) {
            HStack {
                VStack(alignment:.leading,spacing:3) {
                    Text("Prepare and understand the source").font(.headline)
                    Text("Import material here, then use Edit inputs above to bind the exact sources this work owns.").font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
                Button("Record understanding evidence",systemImage:"checkmark.seal") {showingEvidence=true}
            }.padding(.horizontal,20).padding(.vertical,12)
            Divider()
            SourcesView()
        }.sheet(isPresented:$showingEvidence) {
            ScrollView {WorkflowEvidenceRecorder(workflowID:workflow.id,selectedStageID:step.id).padding(24)}.frame(minWidth:620,minHeight:460)
        }
    }
}

private struct WorkflowPlanStage:View {
    @EnvironmentObject var w:Workspace
    let workflow:WorkflowInstance
    let step:WorkflowStep
    var body:some View {ScrollView {VStack(alignment:.leading,spacing:18) {
        GroupBox("Editing approach") {VStack(alignment:.leading,spacing:9) {HStack {Text("Project editing style");Spacer();Text(editingStyleName).foregroundStyle(.secondary)};Text("The selected style and enabled rules guide this plan. Mandatory production rules and explicit review remain authoritative.").font(.caption).foregroundStyle(.secondary);Button("Review Project Settings") {w.select(.projectSettings)}}.padding(10)}
        GroupBox("Plan this work") {VStack(alignment:.leading,spacing:8) {Text(step.detail);Text("Use the Codex action above to prepare a plan request, then review the actual plan before recording evidence.").font(.caption).foregroundStyle(.secondary)}.padding(10)}
        WorkflowEvidenceRecorder(workflowID:workflow.id,selectedStageID:step.id)
    }.padding(20)}}
    var editingStyleName:String {guard let raw=w.data["editing_styles"] as? [String:Any],let parsed=try? EditingStyleConfiguration.parse(raw) else{return "Default guidance"};return parsed.selectedStyle?.name ?? "No selection"}
}

private struct WorkflowEvidenceStage:View {
    let workflow:WorkflowInstance
    let step:WorkflowStep
    var body:some View {ScrollView {VStack(alignment:.leading,spacing:18) {WorkflowEvidenceRecorder(workflowID:workflow.id,selectedStageID:step.id)}.padding(20)}}
}

struct RevisionsView:View {
    @EnvironmentObject var w:Workspace
    var ownedRevisions:[[String:Any]] {guard let workflow=w.activeWorkflow else{return []};let ids=Set(workflow.inputs.revisionIDs);return w.revisions.filter{ids.contains($0["id"] as? String ?? "")}}
    var body:some View {ScrollView {VStack(alignment:.leading,spacing:18) {
        Text("Revisions for this work").font(.title2.bold())
        Text("Add successful renders to the current workflow, then review the exact revision. A render is not acceptance.").foregroundStyle(.secondary)
        Button("Add rendered revision",systemImage:"plus") {w.importFiles(revision:true,attachToActiveWorkflow:true)}.buttonStyle(.borderedProminent).tint(StudioTheme.button).disabled(w.project.isEmpty || w.busy || w.activeWorkflow == nil)
        if ownedRevisions.isEmpty {StudioEmptyState(symbol:"film.stack",title:"No revisions for this work",detail:"Render through the reviewed plan, then register the result here.")}
        ForEach(ownedRevisions.indices,id:\.self) {index in let revision=ownedRevisions[index];GroupBox {VStack(alignment:.leading,spacing:7) {Text(revision["label"] as? String ?? "Revision").font(.headline);Text(revision["path"] as? String ?? "").font(.caption).foregroundStyle(.secondary).textSelection(.enabled);if let duration=revision["duration_ms"] as? Int {Text(String(format:"%.1f seconds",Double(duration)/1000)).font(.caption)};if let id=revision["id"] as? String {Text("Workflows: \(workflowNames(for:id).joined(separator:", "))").font(.caption).foregroundStyle(.secondary)};Button("Review this revision") {if let id=revision["id"] as? String {w.openFeedback(reviewing:id)}}}.padding(10)}}
    }.padding(24)}}
    func workflowNames(for revisionID:String)->[String] {let guide=try? WorkflowGuideSnapshot.parse(w.workflow);return guide?.workflows.filter{$0.inputs.revisionIDs.contains(revisionID)}.map(\.name) ?? []}
}

struct FeedbackView:View {var body:some View {ReviewView()}}

private struct AddWorkflowSheet:View {
    @Environment(\.dismiss) var dismiss
    let templates:[WorkflowTemplate]
    let deliverables:[WorkflowInstance]
    let assets:[[String:Any]]
    let revisions:[[String:Any]]
    let onCreate:(WorkflowTemplate,String,WorkflowInputs,String?)->Void
    @State private var kind=WorkflowTemplateKind.deliverable
    @State private var selectedID=""
    @State private var name=""
    @State private var selectedAsset=""
    @State private var selectedRevision=""
    @State private var parentWorkflowID=""
    var available:[WorkflowTemplate] {templates.filter{$0.kind == kind}}
    var selected:WorkflowTemplate? {available.first {$0.id == selectedID} ?? available.first}
    var body:some View {VStack(alignment:.leading,spacing:16) {
        HStack {Text("New Work").font(.title2.bold());Spacer();Button("Cancel") {dismiss()}.keyboardShortcut(.cancelAction)}
        Text("Create a finished deliverable, or run a supporting action on its own or for an existing deliverable.").foregroundStyle(.secondary)
        Picker("Work type",selection:$kind) {Text("Deliverable").tag(WorkflowTemplateKind.deliverable);Text("Supporting action").tag(WorkflowTemplateKind.supportingAction)}.pickerStyle(.segmented)
        if available.isEmpty {StudioEmptyState(symbol:"exclamationmark.triangle",title:"No matching templates",detail:"Refresh after restoring the workflow template catalog.")} else if let selected {
            Picker("Template",selection:Binding(get:{selected.id},set:{selectedID=$0;selectedAsset="";selectedRevision=""})) {ForEach(available) {Text($0.name).tag($0.id)}}
            Text(selected.summary).foregroundStyle(.secondary)
            TextField("Name this work",text:$name).textFieldStyle(.roundedBorder).accessibilityLabel("Work name")
            if kind == .supportingAction {Picker("Related deliverable",selection:$parentWorkflowID) {Text("Standalone action").tag("");ForEach(deliverables) {workflow in Text(workflow.name).tag(workflow.id)}};Text("Organization only: the action appears beneath its deliverable but does not inherit inputs, evidence, or approval.").font(.caption).foregroundStyle(.secondary)}
            OptionalMediaPickers(assets:assets,revisions:revisions,selectedAsset:$selectedAsset,selectedRevision:$selectedRevision)
            HStack {Spacer();Button("Create Work") {onCreate(selected,name,WorkflowInputs(assetIDs:selectedAsset.isEmpty ? [] : [selectedAsset],revisionIDs:selectedRevision.isEmpty ? [] : [selectedRevision]),kind == .supportingAction && !parentWorkflowID.isEmpty ? parentWorkflowID : nil)}.buttonStyle(.borderedProminent).disabled(name.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty)}
        }
    }.padding(24).frame(minWidth:650,minHeight:500).onAppear {selectedID=available.first?.id ?? ""}.onChange(of:kind) {_,_ in selectedID=available.first?.id ?? "";parentWorkflowID="";selectedAsset="";selectedRevision=""}}
}

private struct WorkflowInputsSheet:View {
    @Environment(\.dismiss) var dismiss
    @EnvironmentObject var w:Workspace
    let template:WorkflowTemplate
    let initial:WorkflowInputs
    let followsAllProjectMedia:Bool
    let assets:[[String:Any]]
    let revisions:[[String:Any]]
    let onSave:(WorkflowInputs)->Void
    @State private var assetIDs=Set<String>()
    @State private var revisionIDs=Set<String>()
    var current:WorkflowInputs {WorkflowInputs(assetIDs:Array(assetIDs).sorted(),revisionIDs:Array(revisionIDs).sorted(),annotationIDs:initial.annotationIDs)}
    var changed:Bool {assetIDs != Set(initial.assetIDs) || revisionIDs != Set(initial.revisionIDs)}
    var body:some View {VStack(alignment:.leading,spacing:16) {HStack {Text("Workflow inputs").font(.title2.bold());Spacer();Button("Cancel") {dismiss()}.keyboardShortcut(.cancelAction)};Text(template.name).font(.headline);Text("Choose the project material this work owns. Feedback remains version-bound and completion remains evidence-based.").foregroundStyle(.secondary);if followsAllProjectMedia {Label("This migrated work currently follows every project source and revision. Saving a changed selection makes that list fixed, so future imports will not be included automatically.",systemImage:"info.circle").font(.callout).foregroundStyle(.secondary)};MediaChecklist(title:"Sources",items:assets,selection:$assetIDs);MediaChecklist(title:"Output revisions",items:revisions,selection:$revisionIDs);Spacer();HStack {Spacer();Button(followsAllProjectMedia ? "Save as fixed inputs" : "Save inputs") {onSave(current)}.buttonStyle(.borderedProminent).disabled(w.busy || !changed)}}.padding(24).frame(minWidth:620,minHeight:520).onAppear {assetIDs=Set(initial.assetIDs);revisionIDs=Set(initial.revisionIDs)}}
}

private struct OptionalMediaPickers:View {
    let assets:[[String:Any]]
    let revisions:[[String:Any]]
    @Binding var selectedAsset:String
    @Binding var selectedRevision:String
    var body:some View {GroupBox("Optional inputs") {VStack(alignment:.leading,spacing:10) {Picker("Source",selection:$selectedAsset) {Text("Choose later").tag("");ForEach(assets.indices,id:\.self) {index in Text(assets[index]["label"] as? String ?? "Source").tag(assets[index]["id"] as? String ?? "")}};Picker("Output revision",selection:$selectedRevision) {Text("Choose later").tag("");ForEach(revisions.indices,id:\.self) {index in Text(revisions[index]["label"] as? String ?? "Revision").tag(revisions[index]["id"] as? String ?? "")}}}.padding(10)}}
}

private struct MediaChecklist:View {
    let title:String
    let items:[[String:Any]]
    @Binding var selection:Set<String>
    var body:some View {GroupBox(title) {VStack(alignment:.leading,spacing:8) {if items.isEmpty {Text("None available").foregroundStyle(.secondary)};ForEach(items.indices,id:\.self) {index in let item=items[index],id=item["id"] as? String ?? "";Toggle(item["label"] as? String ?? "Item",isOn:Binding(get:{selection.contains(id)},set:{if $0 {selection.insert(id)} else {selection.remove(id)}})).disabled(id.isEmpty)}}.padding(10)}}
}
