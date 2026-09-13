import SwiftUI
import AppKit
import StudioCore

@main struct StudioApp: App {
    @StateObject private var workspace=Workspace()
    init() {
        Diagnostics.shared?.captureRuntimeErrors()
        if Diagnostics.shared == nil {NSLog("Codex Media Studio could not open its diagnostics folder.")}
        NSSetUncaughtExceptionHandler {exception in
            Diagnostics.shared?.record("uncaught_exception",detail:exception.name.rawValue)
        }
        Diagnostics.shared?.importCrashReports(from:FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/DiagnosticReports"))
    }
    var body: some Scene {
        WindowGroup("Codex Media Studio") {
            StudioWindow().environmentObject(workspace).frame(minWidth:1100,minHeight:740)
                .task {NSApp.setActivationPolicy(.regular);NSApp.activate(ignoringOtherApps:true)
                    for window in NSApp.windows where window.title == "Codex Media Studio" {
                        Diagnostics.shared?.record("window_focus_before",detail:"key=\(window.isKeyWindow) canKey=\(window.canBecomeKey) visible=\(window.isVisible)")
                        window.makeKeyAndOrderFront(nil)
                        Diagnostics.shared?.record("window_focus_after",detail:"key=\(window.isKeyWindow)")
                    }
                    if !workspace.project.isEmpty {workspace.perform {try await workspace.refresh()}}
                    if ProcessInfo.processInfo.arguments.contains("--smoke-review") {
                        try? await Task.sleep(for:.seconds(1));workspace.selectedWorkflowStageID="final_review";workspace.select(.currentWork)
                        try? await Task.sleep(for:.seconds(4));Diagnostics.shared?.record("review_smoke_passed");try? FileHandle.standardOutput.write(contentsOf:Data("REVIEW_SMOKE_OK\n".utf8));NSApp.terminate(nil)
                    }
                }
        }.defaultSize(width:1360,height:880)
        .commands {CommandGroup(after:.help) {Button("Codex Media Studio Help") {workspace.select(.help)}.accessibilityLabel("Codex Media Studio Help");Button("Open Diagnostic Logs") {if let folder=Diagnostics.shared?.directory {NSWorkspace.shared.open(folder)}}.accessibilityLabel("Open Diagnostic Logs")}}
    }
}
struct StudioWindow:View {
    @EnvironmentObject var w:Workspace
    @State private var helpSection: String?
    @State private var showingHelp = false
    var guide:WorkflowGuideSnapshot? {try? WorkflowGuideSnapshot.parse(w.workflow)}
    var permanentItems:[StudioNavigationItem] {StudioNavigationContract.sections.flatMap(\.items)}
    var body:some View {
        NavigationSplitView {
            VStack(alignment:.leading,spacing:14) {
                HStack(spacing:10) {
                    if let url=Bundle.main.url(forResource:"StudioMark",withExtension:"png"),let mark=NSImage(contentsOf:url) {
                        Image(nsImage:mark).resizable().frame(width:42,height:42).accessibilityHidden(true)
                    }
                    Text("Codex Media Studio").font(.headline).lineLimit(2)
                }
                Text(w.title).font(.title2.bold())
                Text(w.project.isEmpty ? "Start a production or open one you already have." : "Continue the work, one clear step at a time.").foregroundStyle(.secondary).fixedSize(horizontal:false,vertical:true)
                List {
                    Section("Project") {
                        if let home=permanentItems.first(where:{$0.destination == .projectHome}) {StudioSidebarRow(item:home,selected:w.navigation.destination == .projectHome) {w.select(.projectHome)}}
                    }
                    Section("Current Work") {
                        if let guide,!guide.workflows.isEmpty {
                            if !guide.deliverables.isEmpty {Text("Deliverables").font(.caption.weight(.semibold)).foregroundStyle(.secondary).accessibilityAddTraits(.isHeader)}
                            ForEach(guide.deliverables) {workflow in
                                WorkflowSidebarRow(workflow:workflow,selected:w.navigation.destination == .currentWork && guide.activeWorkflowID == workflow.id) {w.openWorkflow(workflow.id)}
                                ForEach(guide.supportingActions(parentedTo:workflow.id)) {action in
                                    WorkflowSidebarRow(workflow:action,selected:w.navigation.destination == .currentWork && guide.activeWorkflowID == action.id,isChild:true,parentName:workflow.name) {w.openWorkflow(action.id)}
                                }
                            }
                            if !guide.standaloneActions.isEmpty {Text("Standalone actions").font(.caption.weight(.semibold)).foregroundStyle(.secondary).accessibilityAddTraits(.isHeader)}
                            ForEach(guide.standaloneActions) {workflow in
                                WorkflowSidebarRow(workflow:workflow,selected:w.navigation.destination == .currentWork && guide.activeWorkflowID == workflow.id) {w.openWorkflow(workflow.id)}
                            }
                        } else {
                            Text(w.project.isEmpty ? "Open a project to see its work." : "No work is available yet.").font(.caption).foregroundStyle(.secondary)
                        }
                        Button("New Work",systemImage:"plus") {w.showAddWorkflow()}.disabled(w.project.isEmpty || w.busy)
                    }
                    Section("Settings") {
                        ForEach(permanentItems.filter{$0.destination == .projectSettings}) {item in
                            StudioSidebarRow(item:item,selected:w.navigation.destination == item.destination) {w.select(item.destination)}
                        }
                    }
                    Section("Help") {
                        ForEach(permanentItems.filter{$0.destination == .help}) {item in
                            StudioSidebarRow(item:item,selected:w.navigation.destination == item.destination) {w.select(item.destination)}
                        }
                    }
                }.listStyle(.sidebar).scrollContentBackground(.hidden)
                HStack {Button("New",action:w.newProject).accessibilityLabel("New");Button("Open",action:w.openProject).accessibilityLabel("Open")}
                Text("Development edition · M4\n\(StudioBuildIdentity.current.visibleLabel)").font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
            }.padding(18).background(StudioTheme.panel).navigationSplitViewColumnWidth(260)
        } detail: {
            VStack(spacing:0) {
                HStack {
                    VStack(alignment:.leading) {Text(detailTitle).font(.title.bold());Text(w.project.isEmpty ? "Create a production to begin" : w.project).font(.caption).foregroundStyle(.secondary).lineLimit(1)}
                    Spacer()
                    Button("Help for this step",systemImage:"questionmark.circle") {helpSection=StudioTheme.helpSection(for:w.navigation,stageID:w.selectedWorkflowStageID);showingHelp=true}.accessibilityLabel("Help for this step")
                    if w.busy {ProgressView().controlSize(.small)}
                    Button(w.inspectorPresented ? "Hide Inspector" : "Show Inspector",systemImage:"sidebar.trailing") {w.inspectorPresented.toggle()}.accessibilityLabel(w.inspectorPresented ? "Hide context and Codex inspector" : "Show context and Codex inspector")
                    Button("Refresh",systemImage:"arrow.clockwise") {w.perform {try await w.refresh()}}.accessibilityLabel("Refresh").disabled(w.project.isEmpty || w.busy)
                    Button("Export handoff",systemImage:"square.and.arrow.up") {w.perform {_ = try await w.handoff()}}.accessibilityLabel("Export handoff").disabled(w.project.isEmpty || w.busy)
                }.padding(24)
                Divider()
                Group {
                    switch w.navigation.destination {
                    case .help:HelpView(engine:w.engine)
                    case .projectHome:ProjectHomeView()
                    case .currentWork:WorkflowGuideView()
                    case .projectSettings:ProjectSettingsView()
                    }
                }.frame(maxWidth:.infinity,maxHeight:.infinity)
                if !w.notice.isEmpty {Text(w.notice).font(.caption).foregroundStyle(.secondary).padding(8)}
            }.background(StudioTheme.canvas)
        }.tint(StudioTheme.accent).foregroundStyle(StudioTheme.text).groupBoxStyle(StudioPanelStyle())
        .inspector(isPresented:$w.inspectorPresented) {
            StudioInspectorView().inspectorColumnWidth(min:320,ideal:380,max:460)
        }
        .sheet(isPresented:$showingHelp) {
            VStack(spacing:0) {
                HStack {Text("Help · \(helpSection ?? w.section)").font(.title2.bold());Spacer();Button("Done") {showingHelp=false}.accessibilityLabel("Done").keyboardShortcut(.cancelAction)}.padding(24)
                Divider()
                HelpView(engine:w.engine,initialSection:helpSection ?? w.section)
            }.frame(minWidth:900,minHeight:620).background(StudioTheme.canvas)
                .foregroundStyle(StudioTheme.text).tint(StudioTheme.accent).groupBoxStyle(StudioPanelStyle())
        }
        .onReceive(NotificationCenter.default.publisher(for:NSApplication.willTerminateNotification)) {_ in Diagnostics.shared?.record("session_ended")}
        .alert("Action needs attention",isPresented:Binding(get:{w.error != nil},set:{if !$0 {w.error=nil}})) {Button("OK"){w.error=nil}.accessibilityLabel("OK")} message:{Text(w.error ?? "")}
    }
    var detailTitle:String {
        if w.navigation.destination == .currentWork {return w.activeWorkflow?.name ?? "Current Work"}
        return w.section
    }
}
private struct StudioSidebarRow:View {
    let item:StudioNavigationItem
    let selected:Bool
    let action:()->Void
    var body:some View {Button(action:action) {Label(item.title,systemImage:item.systemImage).frame(maxWidth:.infinity,alignment:.leading).padding(.vertical,6).contentShape(Rectangle())}.buttonStyle(.plain).listRowBackground(selected ? StudioTheme.accent.opacity(0.14) : Color.clear).accessibilityAddTraits(selected ? .isSelected : [])}
}

private struct WorkflowSidebarRow:View {
    let workflow:WorkflowInstance
    let selected:Bool
    var isChild=false
    var parentName:String?
    let action:()->Void
    var nextStep:WorkflowStep? {workflow.steps.first{[.needsAttention,.current,.ready].contains($0.status)} ?? workflow.steps.first{$0.status != .completed}}
    var body:some View {
        Button(action:action) {
            HStack(alignment:.top,spacing:8) {
                Image(systemName:StudioTheme.symbol(forTemplate:workflow.templateID)).frame(width:18).accessibilityHidden(true)
                VStack(alignment:.leading,spacing:2) {
                    Text(workflow.name).lineLimit(1)
                    Text(nextStep.map{"Next: \($0.label)"} ?? "No next step reported").font(.caption).foregroundStyle(.secondary).lineLimit(1)
                }
                Spacer(minLength:4)
                if let nextStep {Image(systemName:nextStep.status.systemImage).foregroundStyle(nextStep.status == .completed ? StudioTheme.success : StudioTheme.accent).accessibilityHidden(true)}
            }.frame(maxWidth:.infinity,alignment:.leading).padding(.vertical,5).padding(.leading,isChild ? 18 : 0).contentShape(Rectangle())
        }.buttonStyle(.plain).listRowBackground(selected ? StudioTheme.accent.opacity(0.14) : Color.clear)
            .accessibilityLabel("\(workflow.name)\(parentName.map{", supporting action under \($0)"} ?? ""), \(nextStep.map{$0.status.label+", next step "+$0.label} ?? "no next step reported")")
            .accessibilityAddTraits(selected ? .isSelected : [])
    }
}

struct ProjectSettingsView:View {
    @EnvironmentObject var w:Workspace
    var body:some View {
        VStack(spacing:0) {
            Picker("Project setting",selection:Binding(get:{w.projectSettingsSection},set:selectSection)) {ForEach(StudioProjectSettingsSection.allCases,id:\.self) {Text($0.rawValue).tag($0)}}.pickerStyle(.segmented).frame(maxWidth:420).padding(16)
            Divider()
            switch w.projectSettingsSection {case .editing:EditingStylesView();case .resources:ResourcesView();case .application:ApplicationSettingsView()}
        }
    }
    func selectSection(_ next:StudioProjectSettingsSection) {
        guard StudioProjectSettingsSection.permitsTransition(hasUnsavedStyleDraft:w.hasUnsavedStyleDraft,to:next) else {w.error="Save or reload the editing style before opening another Project Settings section.";return}
        w.projectSettingsSection=next
    }
}

private struct ApplicationSettingsView:View {
    @EnvironmentObject var w:Workspace
    var body:some View {
        ScrollView {VStack(alignment:.leading,spacing:20) {
            Text("Application paths").font(.title2.bold())
            Text("These paths connect the installed app to its local engine and ChatGPT subscription client. They are application settings, not editing decisions for the current workflow.").foregroundStyle(.secondary)
            GroupBox("Local tools") {VStack(alignment:.leading,spacing:12) {
                TextField("Engine repository",text:$w.engine).accessibilityLabel("Engine repository").textFieldStyle(.roundedBorder)
                TextField("Python executable",text:$w.python).accessibilityLabel("Python executable").textFieldStyle(.roundedBorder)
                TextField("Codex executable",text:$w.codexBinary).accessibilityLabel("Codex executable").textFieldStyle(.roundedBorder)
                HStack {Button("Save application paths") {w.persist()}.accessibilityLabel("Save application paths");Spacer()}
                Text("Studio uses ChatGPT subscription authentication only. Saving a path does not enable an API-key fallback or authorize hosted generation.").font(.caption).foregroundStyle(.secondary)
            }.padding(12)}
        }.padding(24)}.disabled(w.busy || w.codex.running)
    }
}

struct StudioInspectorView:View {
    @EnvironmentObject var w:Workspace
    var body:some View {
        VStack(spacing:0) {
            Picker("Inspector",selection:$w.inspectorSection) {ForEach(StudioInspectorSection.allCases,id:\.self) {Text($0.rawValue).tag($0)}}.pickerStyle(.segmented).padding(12)
            Divider()
            switch w.inspectorSection {
            case .context:WorkflowContextInspector()
            case .codex:CodexView(client:w.codex)
            case .quality:QualityInspector()
            }
        }.background(StudioTheme.panel)
    }
}
