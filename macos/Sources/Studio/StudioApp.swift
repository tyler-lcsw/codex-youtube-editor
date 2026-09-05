import SwiftUI
import AppKit
import StudioCore

@main struct StudioApp: App {
    @StateObject private var workspace=Workspace()
    var body: some Scene {
        WindowGroup("Codex Studio") {
            StudioWindow().environmentObject(workspace).frame(minWidth:1100,minHeight:740)
                .task {NSApp.setActivationPolicy(.regular);NSApp.activate(ignoringOtherApps:true)
                    if !workspace.project.isEmpty {workspace.perform {try await workspace.refresh()}}
                }
        }.defaultSize(width:1360,height:880)
    }
}
struct StudioWindow:View {
    @EnvironmentObject var w:Workspace
    let sections=["Brief & sources","Understanding","Review","Resources","Codex & QA"]
    var body:some View {
        NavigationSplitView {
            VStack(alignment:.leading,spacing:20) {
                Label("CODEX STUDIO",systemImage:"film.stack").font(.headline).foregroundStyle(.mint)
                Text(w.title).font(.title2.bold())
                Text("A clear path from footage to finished story.").foregroundStyle(.secondary)
                List(sections,id:\.self,selection:$w.section) {name in Text(name).padding(.vertical,7).tag(name)}.listStyle(.sidebar)
                HStack {Button("New",action:w.newProject);Button("Open",action:w.openProject)}
                Text("Development edition · M4").font(.caption).foregroundStyle(.secondary)
            }.padding(18).navigationSplitViewColumnWidth(240)
        } detail: {
            VStack(spacing:0) {
                HStack {
                    VStack(alignment:.leading) {Text(w.section).font(.title.bold());Text(w.project.isEmpty ? "Create a production to begin" : w.project).font(.caption).foregroundStyle(.secondary).lineLimit(1)}
                    Spacer()
                    if w.busy {ProgressView().controlSize(.small)}
                    Button("Refresh",systemImage:"arrow.clockwise") {w.perform {try await w.refresh()}}.disabled(w.project.isEmpty || w.busy)
                    Button("Export handoff",systemImage:"square.and.arrow.up") {w.perform {_ = try await w.handoff()}}.disabled(w.project.isEmpty || w.busy)
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
            }.background(Color(nsColor:.windowBackgroundColor))
        }.tint(.mint)
        .alert("Action needs attention",isPresented:Binding(get:{w.error != nil},set:{if !$0 {w.error=nil}})) {Button("OK"){w.error=nil}} message:{Text(w.error ?? "")}
    }
}
