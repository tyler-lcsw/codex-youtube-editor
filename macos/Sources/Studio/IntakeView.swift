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
    @State private var podcast=PodcastConfiguration(primaryAudioAssetID:"",cameraAssetID:nil,visualDensity:.balanced)
    @State private var podcastBaseline=""
    @State private var podcastDirty=false
    @State private var podcastError:String?
    @State private var podcastMedia=[PodcastMediaOption]()
    var podcastChanged:Bool {podcastBaseline != prettyJSON(w.data["podcast"] ?? NSNull())}
    var podcastConfigured:Bool {w.data["podcast"] is [String:Any]}
    var audioOptions:[PodcastMediaOption] {podcastMedia.filter(\.canBePrimaryAudio)}
    var cameraOptions:[PodcastMediaOption] {podcastMedia.filter(\.canBeCamera)}
    let labels=[("audience","Audience"),("purpose","What should the viewer understand?"),("target_length","Desired length"),("tone","Tone and pacing"),("required_content","Keep or emphasize"),("context","Context and editing instructions")]
    var body:some View {
        ScrollView {
            VStack(alignment:.leading,spacing:22) {
                if w.project.isEmpty {StudioEmptyState(symbol:"folder.badge.plus",title:"Create your first production",detail:"Choose New to make a project, or Open to continue an existing production.")}
                Text("Start with your media and intent.").font(.title2.weight(.semibold))
                Text("The source stays intact. Your brief and references guide the edit; the AI’s interpretation is reviewed before substantive cuts.").foregroundStyle(.secondary)
                GroupBox("Editing brief") {
                    VStack(alignment:.leading,spacing:14) {
                        ForEach(labels,id:\.0) {key,label in
                            VStack(alignment:.leading) {Text(label).font(.caption).foregroundStyle(.secondary)
                                TextField(label,text:Binding(get:{fields[key] ?? ""},set:{fields[key]=$0;dirty=true}),axis:.vertical).accessibilityLabel(label).lineLimit(key=="context" ? 4...8 : 1...3).textFieldStyle(.roundedBorder)
                            }
                        }
                        Button("Save brief") {let brief=fields;w.perform {try await w.request("update_brief",["brief":brief]);dirty=false;try await w.refresh();load();w.notice="Brief saved; dependent reviews reassessed."}}.accessibilityLabel("Save brief").disabled(w.project.isEmpty || (dirty && briefChanged))
                        if dirty && briefChanged {Text("The saved brief changed. Reload it before saving your draft.").foregroundStyle(StudioTheme.accent);Button("Reload saved brief"){load()}.accessibilityLabel("Reload saved brief")}
                    }.padding(12)
                }
                GroupBox("Media and documents") {
                    VStack(alignment:.leading,spacing:12) {
                        Label("Drop files here, or choose files to import",systemImage:"square.and.arrow.down").frame(maxWidth:.infinity,minHeight:70).background(StudioTheme.coral.opacity(0.08)).clipShape(RoundedRectangle(cornerRadius:10))
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
                        Button("Import media or documents") {w.importFiles()}.accessibilityLabel("Import media or documents").disabled(w.project.isEmpty)
                        ForEach(w.assets.indices,id:\.self) {i in let a=w.assets[i]
                            HStack {Image(systemName:a["role"] as? String == "document" ? "doc.text" : "film");Text(a["label"] as? String ?? "Asset");Spacer();Text(a["role"] as? String ?? "source").foregroundStyle(.secondary)}
                        }
                    }.padding(12)
                }
                GroupBox("Solo podcast visuals") {
                    VStack(alignment:.leading,spacing:12) {
                        Text("Choose the canonical audio for a one-speaker episode. Camera footage is optional and remains a separate, unverified association.").foregroundStyle(.secondary)
                        if let podcastError {
                            Label(podcastError,systemImage:"exclamationmark.triangle").foregroundStyle(StudioTheme.accent).textSelection(.enabled)
                        }
                        if audioOptions.isEmpty {
                            StudioEmptyState(symbol:"waveform",title:"Import audio first",detail:"Import an audio-bearing file before configuring podcast visuals.")
                        } else {
                            Picker("Primary audio",selection:Binding(get:{podcast.primaryAudioAssetID},set:{podcast=PodcastConfiguration(primaryAudioAssetID:$0,cameraAssetID:podcast.cameraAssetID,visualDensity:podcast.visualDensity);podcastDirty=true})) {
                                Text("Choose canonical audio").tag("")
                                ForEach(audioOptions) {asset in Text(asset.label+(asset.needsCapabilityValidation ? " · validate on save" : "")).tag(asset.id)}
                            }.accessibilityLabel("Primary podcast audio")
                            Picker("Optional camera",selection:Binding(get:{podcast.cameraAssetID ?? ""},set:{podcast=PodcastConfiguration(primaryAudioAssetID:podcast.primaryAudioAssetID,cameraAssetID:$0.isEmpty ? nil : $0,visualDensity:podcast.visualDensity);podcastDirty=true})) {
                                Text("No camera").tag("")
                                ForEach(cameraOptions) {asset in Text(asset.label+(asset.needsCapabilityValidation ? " · validate on save" : "")).tag(asset.id)}
                            }.accessibilityLabel("Optional podcast camera")
                            Picker("Visual density",selection:Binding(get:{podcast.visualDensity},set:{podcast=PodcastConfiguration(primaryAudioAssetID:podcast.primaryAudioAssetID,cameraAssetID:podcast.cameraAssetID,visualDensity:$0);podcastDirty=true})) {
                                ForEach(PodcastVisualDensity.allCases,id:\.self) {density in Text(density.label).tag(density)}
                            }.accessibilityLabel("Podcast visual density")
                            Text("Restrained, balanced, and illustrative are editorial preferences—not fixed effect intervals.").font(.caption).foregroundStyle(.secondary)
                            HStack {
                                Button("Save podcast setup") {savePodcast()}.accessibilityLabel("Save podcast setup").disabled(w.project.isEmpty || w.busy || podcast.primaryAudioAssetID.isEmpty || podcastError != nil || (podcastDirty && podcastChanged))
                                Button("Clear podcast setup") {clearPodcast()}.accessibilityLabel("Clear podcast setup").disabled(w.project.isEmpty || w.busy || !podcastConfigured || podcastError != nil || (podcastDirty && podcastChanged))
                            }
                            if podcastDirty && podcastChanged {
                                Text("The saved podcast setup changed. Reload it before saving your draft.").foregroundStyle(StudioTheme.accent)
                                Button("Reload saved podcast setup"){loadPodcast()}.accessibilityLabel("Reload saved podcast setup")
                            }
                        }
                        Text("Setup only: waveform rendering and semantic visual proposals are not generated yet. Camera synchronization is not inferred or verified.").font(.caption).foregroundStyle(.secondary)
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
        }.onAppear {load();loadPodcast()}.onChange(of:w.project){_,_ in load();loadPodcast()}.onChange(of:w.dataRevision){_,_ in
            if !dirty {load()}
            loadPodcast(preservingDraft:podcastDirty)
        }
    }
    func load() {dirty=false;baseline=prettyJSON(w.data["brief"] ?? [:]);fields=(w.data["brief"] as? [String:Any] ?? [:]).compactMapValues{$0 as? String}}
    func loadPodcast(preservingDraft:Bool=false) {
        podcastMedia=[]
        do {
            try refreshPodcastMedia()
            if !preservingDraft {try reloadPodcastDraft()}
            podcastError=nil
        } catch {podcastError=error.localizedDescription}
    }
    func refreshPodcastMedia() throws {
        podcastMedia=try PodcastMediaOption.options(from:w.assets)
    }
    func reloadPodcastDraft() throws {
        podcast=try PodcastConfiguration.from(project:w.data) ?? PodcastConfiguration(primaryAudioAssetID:"",cameraAssetID:nil,visualDensity:.balanced)
        podcastBaseline=prettyJSON(w.data["podcast"] ?? NSNull());podcastDirty=false
    }
    func savePodcast() {
        do {
            let payload=try podcast.patchPayload()
            w.perform {try await w.request("set_podcast_settings",payload);podcastDirty=false;loadPodcast();w.notice="Podcast setup saved; dependent reviews reassessed."}
        } catch {podcastError=error.localizedDescription}
    }
    func clearPodcast() {
        w.perform {try await w.request("clear_podcast_settings");podcastDirty=false;loadPodcast();w.notice="Podcast setup cleared; dependent reviews reassessed."}
    }
}
