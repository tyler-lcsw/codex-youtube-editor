import SwiftUI
struct ResourcesView:View {
    @EnvironmentObject var w:Workspace
    let notes=["editorial":"Codex uses your ChatGPT subscription. Local PAIR is bounded assistance; full editorial equivalence is not qualified.","transcription":"Local Qwen MLX recognition and alignment. Check uncertain words against the recording.","cleanup":"Local DeepFilterNet. Compare with original audio before retaining cleanup.","images":"Local Klein is bounded to tested settings. Native Codex images require scoped approval and capability verification; no API fallback.","rendering":"Local FFmpeg and Remotion remain available together. This selects a preference, not removal of either engine."]
    var routes:[String:[String]] {w.workflow["routes"] as? [String:[String]] ?? [:]}
    var body:some View {
        ScrollView {VStack(alignment:.leading,spacing:20) {
            Text("Choose resources for each part of the work.").font(.title2.bold())
            Text("M4 · 24 GiB · one heavy local inference job at a time").foregroundStyle(.secondary)
            ForEach(routes.keys.sorted(),id:\.self) {task in
                GroupBox(task.capitalized) {
                    VStack(alignment:.leading,spacing:12) {
                        Picker("Provider preference",selection:Binding(get:{(w.data["routes"] as? [String:String])?[task] ?? routes[task]?.first ?? ""},set:{provider in w.perform {try await w.request("set_route",["task":task,"provider":provider])}})) {
                            ForEach(routes[task] ?? [],id:\.self) {Text($0).tag($0)}
                        }
                        Text(notes[task] ?? "").foregroundStyle(.secondary).fixedSize(horizontal:false,vertical:true)
                    }.padding(12)
                }
            }
            Text("Choices are saved with the project and included in each Codex handoff. Choosing a hosted image route does not grant generation approval. Downloads and remote-worker setup are never implicit.").font(.callout)
        }.padding(24)}
    }
}
