import SwiftUI
import AppKit
import StudioCore

@main struct StudioApp: App {
    @StateObject private var workspace=Workspace()
    init() {
        Diagnostics.shared?.captureRuntimeErrors()
        if Diagnostics.shared == nil {NSLog("Codex Studio could not open its diagnostics folder.")}
        NSSetUncaughtExceptionHandler {exception in
            Diagnostics.shared?.record("uncaught_exception",detail:exception.name.rawValue)
        }
        Diagnostics.shared?.importCrashReports(from:FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/DiagnosticReports"))
    }
    var body: some Scene {
        WindowGroup("Codex Studio") {
            StudioWindow().environmentObject(workspace).frame(minWidth:1100,minHeight:740)
                .task {NSApp.setActivationPolicy(.regular);NSApp.activate(ignoringOtherApps:true)
                    for window in NSApp.windows where window.title == "Codex Studio" {
                        Diagnostics.shared?.record("window_focus_before",detail:"key=\(window.isKeyWindow) canKey=\(window.canBecomeKey) visible=\(window.isVisible)")
                        window.makeKeyAndOrderFront(nil)
                        Diagnostics.shared?.record("window_focus_after",detail:"key=\(window.isKeyWindow)")
                    }
                    if !workspace.project.isEmpty {workspace.perform {try await workspace.refresh()}}
                    if ProcessInfo.processInfo.arguments.contains("--smoke-review") {
                        try? await Task.sleep(for:.seconds(1));workspace.section="Review"
                        try? await Task.sleep(for:.seconds(4));Diagnostics.shared?.record("review_smoke_passed");try? FileHandle.standardOutput.write(contentsOf:Data("REVIEW_SMOKE_OK\n".utf8));NSApp.terminate(nil)
                    }
                }
        }.defaultSize(width:1360,height:880)
        .commands {CommandGroup(after:.help) {Button("Open Diagnostic Logs") {if let folder=Diagnostics.shared?.directory {NSWorkspace.shared.open(folder)}}.accessibilityLabel("Open Diagnostic Logs")}}
    }
}
struct StudioWindow:View {
    @EnvironmentObject var w:Workspace
    let sections=["Brief & sources","Understanding","Review","Resources","Codex & QA"]
    var body:some View {
        NavigationSplitView {
            VStack(alignment:.leading,spacing:20) {
                HStack(spacing:10) {
                    if let url=Bundle.main.url(forResource:"StudioMark",withExtension:"png"),let mark=NSImage(contentsOf:url) {
                        Image(nsImage:mark).resizable().frame(width:42,height:42).accessibilityHidden(true)
                    }
                    Text("CODEX STUDIO").font(.headline).tracking(1)
                }
                Text(w.title).font(.title2.bold())
                Text("A clear path from footage to finished story.").foregroundStyle(.secondary)
                List(sections,id:\.self,selection:$w.section) {name in Label(name,systemImage:StudioTheme.symbol(for:name)).padding(.vertical,7).tag(name)}.listStyle(.sidebar).scrollContentBackground(.hidden)
                HStack {Button("New",action:w.newProject).accessibilityLabel("New");Button("Open",action:w.openProject).accessibilityLabel("Open")}
                Text("Development edition · M4").font(.caption).foregroundStyle(.secondary)
            }.padding(18).background(StudioTheme.panel).navigationSplitViewColumnWidth(260)
        } detail: {
            VStack(spacing:0) {
                HStack {
                    VStack(alignment:.leading) {Text(w.section).font(.title.bold());Text(w.project.isEmpty ? "Create a production to begin" : w.project).font(.caption).foregroundStyle(.secondary).lineLimit(1)}
                    Spacer()
                    if w.busy {ProgressView().controlSize(.small)}
                    Button("Refresh",systemImage:"arrow.clockwise") {w.perform {try await w.refresh()}}.accessibilityLabel("Refresh").disabled(w.project.isEmpty || w.busy)
                    Button("Export handoff",systemImage:"square.and.arrow.up") {w.perform {_ = try await w.handoff()}}.accessibilityLabel("Export handoff").disabled(w.project.isEmpty || w.busy)
                }.padding(24)
                Divider()
                Group {
                    switch w.section {
                    case "Understanding":UnderstandingView()
                    case "Review":ReviewView()
                    case "Resources":ResourcesView()
                    case "Codex & QA":CodexView(client:w.codex)
                    default:IntakeView()
                    }
                }.frame(maxWidth:.infinity,maxHeight:.infinity)
                if !w.notice.isEmpty {Text(w.notice).font(.caption).foregroundStyle(.secondary).padding(8)}
            }.background(StudioTheme.canvas)
        }.tint(StudioTheme.accent).foregroundStyle(StudioTheme.text).groupBoxStyle(StudioPanelStyle())
        .onReceive(NotificationCenter.default.publisher(for:NSApplication.willTerminateNotification)) {_ in Diagnostics.shared?.record("session_ended")}
        .alert("Action needs attention",isPresented:Binding(get:{w.error != nil},set:{if !$0 {w.error=nil}})) {Button("OK"){w.error=nil}.accessibilityLabel("OK")} message:{Text(w.error ?? "")}
    }
}
