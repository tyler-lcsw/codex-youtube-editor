import SwiftUI
import UniformTypeIdentifiers
import StudioCore
struct IntakeView:View {
    @EnvironmentObject var w:Workspace
    @State private var fields=[String:String]()
    @State private var baseline=""
    @State private var dirty=false
    var briefChanged:Bool {baseline != prettyJSON(w.data["brief"] ?? [:])}
    @State private var resourceURL=""
    @State private var resourceLabel=""
    @State private var resourceRole="reference"
    let labels=[("audience","Audience"),("purpose","What should the viewer understand?"),("target_length","Desired length"),("tone","Tone and pacing"),("required_content","Keep or emphasize"),("context","Context and editing instructions")]
    var body:some View {
        ScrollView {
            VStack(alignment:.leading,spacing:22) {
                Text("Start with your footage and intent.").font(.title2.weight(.semibold))
                Text("The source stays intact. Your brief and references guide the edit; the AI’s interpretation is reviewed before substantive cuts.").foregroundStyle(.secondary)
                GroupBox("Editing brief") {
                    VStack(alignment:.leading,spacing:14) {
                        ForEach(labels,id:\.0) {key,label in
                            VStack(alignment:.leading) {Text(label).font(.caption).foregroundStyle(.secondary)
                                TextField(label,text:Binding(get:{fields[key] ?? ""},set:{fields[key]=$0;dirty=true}),axis:.vertical).accessibilityLabel(label).lineLimit(key=="context" ? 4...8 : 1...3).textFieldStyle(.roundedBorder)
                            }
                        }
                        Button("Save brief") {let brief=fields;w.perform {try await w.request("update_brief",["brief":brief]);dirty=false;try await w.refresh();load();w.notice="Brief saved; dependent reviews reassessed."}}.accessibilityLabel("Save brief").disabled(w.project.isEmpty || (dirty && briefChanged))
                        if dirty && briefChanged {Text("The saved brief changed. Reload it before saving your draft.").foregroundStyle(.orange);Button("Reload saved brief"){load()}.accessibilityLabel("Reload saved brief")}
                    }.padding(12)
                }
                GroupBox("Footage and documents") {
                    VStack(alignment:.leading,spacing:12) {
                        Label("Drop files here, or choose files to import",systemImage:"square.and.arrow.down").frame(maxWidth:.infinity,minHeight:70).background(.mint.opacity(0.08)).clipShape(RoundedRectangle(cornerRadius:10))
                            .onDrop(of:[UTType.fileURL.identifier],isTargeted:nil) {providers in
                                guard !w.busy else {return false}
                                let group=DispatchGroup(),lock=NSLock();var urls=[URL]()
                                for provider in providers {
                                    group.enter()
                                    _ = provider.loadObject(ofClass:URL.self) {url,_ in
                                        if let url {lock.lock();urls.append(url);lock.unlock()};group.leave()
                                    }
                                }
                                group.notify(queue:.main){w.importURLs(urls)}
                                return true
                            }
                        Button("Import footage or documents") {w.importFiles()}.accessibilityLabel("Import footage or documents").disabled(w.project.isEmpty)
                        ForEach(w.assets.indices,id:\.self) {i in let a=w.assets[i]
                            HStack {Image(systemName:a["role"] as? String == "document" ? "doc.text" : "film");Text(a["label"] as? String ?? "Asset");Spacer();Text(a["role"] as? String ?? "source").foregroundStyle(.secondary)}
                        }
                    }.padding(12)
                }
                GroupBox("Resource links") {
                    VStack(alignment:.leading) {
                        TextField("Label",text:$resourceLabel).accessibilityLabel("Label").textFieldStyle(.roundedBorder)
                        TextField("https://…",text:$resourceURL).accessibilityLabel("https://…").textFieldStyle(.roundedBorder)
                        HStack {Picker("Use as",selection:$resourceRole) {Text("Reference").tag("reference");Text("Source").tag("source");Text("Background").tag("context")}.frame(width:260)
                            Button("Add link") {let url=resourceURL,label=resourceLabel,role=resourceRole;w.perform {try await w.request("add_resource",["url":url,"label":label,"role":role]);resourceURL="";resourceLabel=""}}.accessibilityLabel("Add link").disabled(w.project.isEmpty)
                        }
                        ForEach((w.data["resources"] as? [[String:Any]] ?? []).indices,id:\.self) {i in
                            let r=(w.data["resources"] as? [[String:Any]] ?? [])[i]
                            if let url=URL(string:r["url"] as? String ?? "") {Link(r["label"] as? String ?? url.absoluteString,destination:url)}
                        }
                    }.padding(12)
                }
            }.padding(24)
        }.onAppear {load()}.onChange(of:w.project){_,_ in load()}.onChange(of:w.dataRevision){_,_ in if !dirty {load()}}
    }
    func load() {dirty=false;baseline=prettyJSON(w.data["brief"] ?? [:]);fields=(w.data["brief"] as? [String:Any] ?? [:]).compactMapValues{$0 as? String}}
}
