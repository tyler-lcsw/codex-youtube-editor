import SwiftUI
import StudioCore

struct EditingStylesView:View {
    @EnvironmentObject var w:Workspace
    @State private var configuration:EditingStyleConfiguration?
    @State private var draftName=""
    @State private var draftRules=[EditingStyleRule]()
    @State private var baselineRevision=0
    @State private var dirty=false
    @State private var localError:String?
    @State private var showingNewStyle=false
    @State private var newStyleName=""
    @State private var deleteCandidate:EditingStyleProfile?

    var savedRevision:Int? {
        guard let raw=w.data["editing_styles"] as? [String:Any] else{return nil}
        return raw["revision"] as? Int
    }
    var hasConflict:Bool {dirty && savedRevision != nil && savedRevision != baselineRevision}

    var body:some View {
        ScrollView {
            VStack(alignment:.leading,spacing:20) {
                if w.project.isEmpty {
                    StudioEmptyState(symbol:"checklist",title:"Open a production first",detail:"Editing styles are saved separately for each project.")
                } else if let configuration,let selected=configuration.selectedStyle {
                    Text("Choose how this project should be edited.").font(.title2.bold())
                    Text("Each style is a project-local copy of the master rule list. Unchecking a rule removes it from this style’s editorial guidance; the mandatory production-quality policy still applies.").foregroundStyle(.secondary).fixedSize(horizontal:false,vertical:true)
                    GroupBox("Project style") {
                        VStack(alignment:.leading,spacing:12) {
                            HStack {
                                Picker("Editing style",selection:Binding(get:{configuration.selectedStyleID},set:selectStyle)) {
                                    ForEach(configuration.styles) {style in Text(style.name).tag(style.id)}
                                }.disabled(w.busy || dirty)
                                Button("New from master") {newStyleName="";showingNewStyle=true}.disabled(w.busy || dirty)
                                Menu("Delete style") {
                                    ForEach(configuration.styles.filter {$0.id != configuration.selectedStyleID}) {style in
                                        Button(style.name,role:.destructive) {deleteCandidate=style}
                                    }
                                }.disabled(w.busy || dirty || configuration.styles.count < 2)
                            }
                            TextField("Style name",text:Binding(get:{draftName},set:{draftName=$0;markDirty()})).textFieldStyle(.roundedBorder).accessibilityLabel("Editing style name")
                            HStack {
                                Button("Save style",action:save).keyboardShortcut("s",modifiers:.command).disabled(w.busy || draftName.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty || !dirty || hasConflict)
                                if dirty {Button("Reload saved style",action:reloadFromDisk).disabled(w.busy)}
                                Spacer()
                                Text("\(draftRules.filter(\.enabled).count) of \(draftRules.count) rules enabled").font(.caption).foregroundStyle(.secondary)
                            }
                            if hasConflict {
                                Label("The saved style changed. Reload it before saving this draft.",systemImage:"exclamationmark.triangle").foregroundStyle(StudioTheme.accent)
                            } else if configuration.masterChanged {
                                Label("The master rule file has changed since one or more styles were created. Existing custom wording was preserved.",systemImage:"info.circle").foregroundStyle(.secondary)
                            }
                            Text(configuration.materialized ? "Saved in work/studio/editing-styles.json" : "This legacy default will be saved to work/studio/editing-styles.json after your first change.").font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
                        }.padding(12)
                    }
                    LazyVStack(alignment:.leading,spacing:12) {
                        ForEach(draftRules.indices,id:\.self) {index in
                            EditingRuleRow(rule:Binding(get:{draftRules[index]},set:{draftRules[index]=$0;markDirty()}))
                        }
                    }
                    Text("The master production rules remain the QA authority. Style changes invalidate dependent editorial reviews so they can be reassessed.").font(.callout).foregroundStyle(.secondary)
                    Text("Selected: \(selected.name)").font(.caption).foregroundStyle(.secondary).accessibilityHidden(true)
                } else if let localError {
                    StudioEmptyState(symbol:"exclamationmark.triangle",title:"Editing styles could not be loaded",detail:localError)
                    Button("Retry") {reloadFromDisk()}.disabled(w.busy)
                } else {
                    ProgressView("Loading editing styles")
                }
            }.padding(24)
        }
        .onAppear(perform:load)
        .onChange(of:w.project) {_,_ in load()}
        .onChange(of:w.dataRevision) {_,_ in if !dirty {load()} else if hasConflict {localError=nil}}
        .alert("New editing style",isPresented:$showingNewStyle) {
            TextField("Style name",text:$newStyleName).accessibilityLabel("New editing style name")
            Button("Cancel",role:.cancel) {}
            Button("Create") {createStyle()}.disabled(newStyleName.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty)
        } message: {Text("The new style starts with every current master rule enabled.")}
        .confirmationDialog("Delete \(deleteCandidate?.name ?? "style")?",isPresented:Binding(get:{deleteCandidate != nil},set:{if !$0 {deleteCandidate=nil}}),titleVisibility:.visible) {
            Button("Delete style",role:.destructive) {deleteStyle()}
            Button("Cancel",role:.cancel) {deleteCandidate=nil}
        } message: {Text("This removes the unselected style from this project. The selected style is unchanged.")}
    }

    func load() {
        guard !w.project.isEmpty,let raw=w.data["editing_styles"] as? [String:Any] else {configuration=nil;draftRules=[];draftName="";dirty=false;w.hasUnsavedStyleDraft=false;return}
        do {
            let parsed=try EditingStyleConfiguration.parse(raw)
            guard let selected=parsed.selectedStyle else {throw StudioError("Selected editing style is missing")}
            configuration=parsed;draftName=selected.name;draftRules=selected.rules;baselineRevision=parsed.revision;dirty=false;w.hasUnsavedStyleDraft=false;localError=nil
        } catch {configuration=nil;w.hasUnsavedStyleDraft=false;localError=error.localizedDescription}
    }

    func selectStyle(_ styleID:String) {
        guard let configuration,styleID != configuration.selectedStyleID else{return}
        w.perform {try await w.request("select_editing_style",["style_id":styleID,"expected_revision":configuration.revision,"expected_sha256":configuration.sha256]);load();w.notice="Editing style selected; dependent reviews reassessed."}
    }

    func createStyle() {
        guard let configuration else{return}
        let name=newStyleName
        w.perform {try await w.request("create_editing_style",["name":name,"expected_revision":configuration.revision,"expected_sha256":configuration.sha256]);load();w.notice="Editing style created from the current master rules."}
    }

    func save() {
        guard let configuration,var style=configuration.selectedStyle else{return}
        style.name=draftName;style.rules=draftRules
        var payload=style.savePayload(expectedRevision:baselineRevision);payload["expected_sha256"]=configuration.sha256
        w.perform {try await w.request("update_editing_style",payload);load();w.notice="Editing style saved; dependent reviews reassessed."}
    }

    func markDirty() {dirty=true;w.hasUnsavedStyleDraft=true}

    func reloadFromDisk() {
        w.perform {try await w.refresh();load();w.notice="Editing style reloaded from disk."}
    }

    func deleteStyle() {
        guard let configuration,let candidate=deleteCandidate else{return}
        deleteCandidate=nil
        w.perform {try await w.request("delete_editing_style",["style_id":candidate.id,"expected_revision":configuration.revision,"expected_sha256":configuration.sha256]);load();w.notice="Editing style deleted."}
    }
}

private struct EditingRuleRow:View {
    @Binding var rule:EditingStyleRule
    var body:some View {
        GroupBox(rule.id) {
            VStack(alignment:.leading,spacing:8) {
                HStack(alignment:.top) {
                    Toggle("Enable rule",isOn:$rule.enabled).labelsHidden().accessibilityLabel("\(rule.id) enabled")
                    Text(rule.id).font(.headline.monospaced()).frame(width:48,alignment:.leading)
                    TextEditor(text:$rule.text).font(.body).frame(minHeight:72,maxHeight:150).accessibilityLabel("\(rule.id) editing rule text")
                        .overlay(RoundedRectangle(cornerRadius:6).stroke(StudioTheme.border.opacity(0.7)))
                }
                Text(rule.enabled ? "Enabled in this style" : "Not used by this style").font(.caption).foregroundStyle(.secondary)
            }.padding(10)
        }.accessibilityElement(children:.contain).accessibilityLabel("Editing rule \(rule.id)")
    }
}
