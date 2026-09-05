import SwiftUI
import AppKit
import StudioCore
struct UnderstandingView:View {
    @EnvironmentObject var w:Workspace
    @State private var stage="intake"
    @State private var reason=""
    @State private var evidence=[String]()
    var stages:[[String:Any]] {w.workflow["stages"] as? [[String:Any]] ?? []}
    var body:some View {
        ScrollView {VStack(alignment:.leading,spacing:20) {
            Text("Understand first. Edit with reasons.").font(.title2.bold())
            Text("Each stage records evidence against the current footage, brief, rules, and workflow. A changed input makes the affected review stale.").foregroundStyle(.secondary)
            ForEach(stages.indices,id:\.self) {i in let row=stages[i]
                GroupBox {
                    VStack(alignment:.leading,spacing:8) {
                        HStack {Text(row["label"] as? String ?? "Stage").font(.headline);Spacer();Text(row["status"] as? String ?? "pending").foregroundStyle(.mint)}
                        Text("Requires: \((row["requires"] as? [String] ?? []).joined(separator:", "))").font(.caption).foregroundStyle(.secondary)
                        if let review=row["review"] as? [String:Any] {Text(review["reason"] as? String ?? "").textSelection(.enabled)}
                    }.frame(maxWidth:.infinity,alignment:.leading).padding(10)
                }
            }
            GroupBox("Record completed stage evidence") {
                VStack(alignment:.leading,spacing:12) {
                    Picker("Stage",selection:$stage) {ForEach(stages.indices,id:\.self) {i in Text(stages[i]["label"] as? String ?? "").tag(stages[i]["id"] as? String ?? "")}}
                    TextField("What was established, and where is it documented?",text:$reason,axis:.vertical).textFieldStyle(.roundedBorder)
                    Button("Select evidence files") {let p=NSOpenPanel();p.allowsMultipleSelection=true;if p.runModal() == .OK {evidence=p.urls.map(\.path)}}
                    Text(evidence.joined(separator:"\n")).font(.caption).textSelection(.enabled)
                    Button("Record evidence") {let s=stage,r=reason,e=evidence;w.perform {try await w.request("record_stage",["stage":s,"reason":r,"evidence":e]);try await w.refresh()}}.disabled(w.project.isEmpty || evidence.isEmpty || reason.isEmpty)
                    Text("This records an assessment. It does not manufacture evidence or replace final audiovisual QA.").font(.caption).foregroundStyle(.secondary)
                }.padding(12)
            }
            Button("Open authoritative workflow") {NSWorkspace.shared.open(URL(fileURLWithPath:w.engine+"/config/studio-workflow.json"))}
        }.padding(24)}
    }
}
