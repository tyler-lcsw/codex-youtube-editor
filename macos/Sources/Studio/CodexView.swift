import SwiftUI
import AppKit
import StudioCore
struct CodexView:View {
    @EnvironmentObject var w:Workspace
    @ObservedObject var client:CodexClient
    @State private var prompt=""
    @State private var model="gpt-6-astra"
    @State private var answers=[String:String]()
    @State private var connecting=false
    var body:some View {
        ScrollView {VStack(alignment:.leading,spacing:18) {
            GroupBox("ChatGPT subscription") {
                VStack(alignment:.leading,spacing:12) {
                    HStack {Label(client.accountLabel,systemImage:client.subscription ? "checkmark.seal" : "person.crop.circle");Spacer()
                        Button(connecting ? "Connecting…" : "Connect") {connect()}.disabled(connecting || client.running)
                        Button("Sign in with ChatGPT") {Task {do {if !client.connected {try await client.connect(binary:w.codexBinary)};let url=try await client.signIn();NSWorkspace.shared.open(url)} catch {w.error=error.localizedDescription}}}.disabled(client.running || connecting)
                    }
                    Text("Subscription access only. No API key or API billing fallback.").font(.caption).foregroundStyle(.secondary)
                    DisclosureGroup("Local application paths") {
                        TextField("Engine repository",text:$w.engine).textFieldStyle(.roundedBorder)
                        TextField("Python executable",text:$w.python).textFieldStyle(.roundedBorder)
                        TextField("Codex executable",text:$w.codexBinary).textFieldStyle(.roundedBorder)
                        Button("Save paths") {w.persist()}
                    }.disabled(client.running)
                }.padding(12)
            }
            GroupBox("Production task") {
                VStack(alignment:.leading,spacing:12) {
                    Picker("Codex model",selection:$model) {Text("GPT-6 Astra").tag("gpt-6-astra");Text("GPT-5.6 Sol").tag("gpt-5.6-sol")}.disabled(client.running)
                    TextField("Describe the next edit or ask Codex to analyze the footage…",text:$prompt,axis:.vertical).lineLimit(3...8).textFieldStyle(.roundedBorder)
                    HStack {
                        Button("Send to Codex",systemImage:"arrow.up.circle.fill") {send()}.buttonStyle(.borderedProminent).disabled(!client.subscription || client.running || w.project.isEmpty || w.busy || prompt.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty)
                        Button("Stop task") {Task {do {try await client.interrupt()}catch {w.error=error.localizedDescription}}}.disabled(!client.running)
                        if client.running {ProgressView().controlSize(.small);Text("Working…").foregroundStyle(.secondary)}
                    }
                    if let id=client.threadID {Text("Task \(id)").font(.caption).textSelection(.enabled)}
                    if let error=client.lastError {Text(error).foregroundStyle(.orange).textSelection(.enabled)}
                    Text(client.messages.isEmpty ? "Your brief, sources, provider choices, and version-bound feedback accompany each task." : client.messages).textSelection(.enabled).frame(maxWidth:.infinity,alignment:.leading).padding(12).background(.black.opacity(0.12)).clipShape(RoundedRectangle(cornerRadius:8))
                }.padding(12)
            }
            ForEach(client.questions) {question in
                GroupBox("Codex needs your response") {
                    VStack(alignment:.leading,spacing:10) {
                        Text(question.method).font(.headline)
                        Text(prettyJSON(question.params)).font(.system(.caption,design:.monospaced)).textSelection(.enabled)
                        if question.method=="item/tool/requestUserInput" {
                            let fields=question.params["questions"] as? [[String:Any]] ?? []
                            ForEach(fields.indices,id:\.self) {i in
                                let field=fields[i],id=field["id"] as? String ?? String(i)
                                TextField(field["question"] as? String ?? "Your answer",text:Binding(get:{answers[id] ?? ""},set:{answers[id]=$0}),axis:.vertical).textFieldStyle(.roundedBorder)
                            }
                            Button("Send answers") {do {try client.answer(question,allow:false,responses:answers);answers=[:]}catch{w.error=error.localizedDescription}}

                        } else {
                            HStack {Button("Approve this action") {respond(question,true)};Button("Decline") {respond(question,false)}}
                        }
                    }.padding(12)
                }
            }
            GroupBox("Final production QA") {
                VStack(alignment:.leading,spacing:12) {
                    Text("Technical validation, visual inspection, listening, and your acceptance remain separate. No automatic approval from a successful render.").foregroundStyle(.secondary)
                    ForEach(["before","during","after"],id:\.self) {phase in
                        let gate=(w.quality["gates"] as? [String:Any])?[phase] as? [String:Any] ?? [:]
                        DisclosureGroup("\(phase.capitalized): \(gate["passed"] as? Bool == true ? "passed" : "pending / findings")") {
                            Text(prettyJSON(gate["failures"] ?? [])).font(.system(.caption,design:.monospaced)).textSelection(.enabled)
                        }
                    }
                    Button("Open authoritative rules") {NSWorkspace.shared.open(URL(fileURLWithPath:w.engine+"/docs/production-rules.md"))}
                }.padding(12)
            }
        }.padding(24)}
        .onChange(of:client.running) {old,new in if old && !new && !w.project.isEmpty {w.perform {try await w.refresh()}}}
    }
    func connect() {connecting=true;Task {defer{connecting=false};do {try await client.connect(binary:w.codexBinary)}catch{w.error=error.localizedDescription}}}
    func respond(_ q:CodexQuestion,_ allow:Bool) {do {try client.answer(q,allow:allow)}catch{w.error=error.localizedDescription}}
    func send() {
        let instruction=prompt,project=w.project,engine=w.engine
        w.perform {
            let handoff=try await w.handoff(copy:false)
            let handoffPath=handoff["path"] as? String ?? ""
            let id=try await client.send(text:"Read the current production handoff at \(handoffPath). User request:\n\(instruction)",engine:engine,project:project,model:model,existingThread:w.data["thread_id"] as? String)
            try await w.request("set_thread",["thread_id":id]);prompt=""
        }
    }
}
