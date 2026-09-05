import SwiftUI
import AVKit
import AppKit
import StudioCore

struct ReviewView:View {
    @EnvironmentObject var w:Workspace
    @State private var selected=""
    @State private var player=AVPlayer()
    @State private var videoSize=CGSize(width:1920,height:1080)
    @State private var markerMS=0
    @State private var endSeconds=""
    @State private var comment=""
    @State private var rect: CGRect?
    @State private var draw=false
    @State private var capturePath=""
    @State private var resolution=""
    @State private var resolutionNote=""
    @State private var transcriptWords=[[String:Any]]()
    @State private var selectedWords=Set<String>()
    var media:[[String:Any]] {(w.assets+w.revisions).filter{($0["role"] as? String) != "document"}}
    var asset:[String:Any]? {media.first{$0["id"] as? String == selected}}
    var feedback:[[String:Any]] {w.annotations.filter{$0["asset_id"] as? String == selected}}
    var body:some View {
        HSplitView {
            VStack(alignment:.leading,spacing:12) {
                HStack {
                    Picker("Viewing",selection:$selected) {Text("Choose a source or revision").tag("");ForEach(media.indices,id:\.self){i in Text(media[i]["label"] as? String ?? "Media").tag(media[i]["id"] as? String ?? "")}}
                    Button("Add revision") {w.importFiles(revision:true)}.disabled(w.project.isEmpty)
                }
                GeometryReader {geometry in
                    ZStack {
                        VideoPlayer(player:player)
                        if draw {AnnotationOverlay(videoSize:videoSize,selection:$rect)}
                        if !draw,let rect {
                            let bounds=ReviewGeometry.videoRect(container:geometry.size,video:videoSize)
                            Rectangle().stroke(.mint,lineWidth:3).frame(width:rect.width*bounds.width,height:rect.height*bounds.height).position(x:bounds.minX+rect.midX*bounds.width,y:bounds.minY+rect.midY*bounds.height).allowsHitTesting(false)
                        }
                    }.background(.black)
                }.frame(minHeight:280)
                HStack {
                    Button("Pause & annotate",systemImage:"pause.circle") {capture()}.disabled(asset==nil || w.busy)
                    Toggle("Draw region",isOn:$draw).toggleStyle(.button).disabled(capturePath.isEmpty)
                    Button("Clear region"){rect=nil}
                    Text(String(format:"%.3f s",Double(markerMS)/1000)).monospacedDigit()
                }
                if !capturePath.isEmpty {Label("Frame captured for this version",systemImage:"checkmark.circle").font(.caption).foregroundStyle(.mint)}
                TextField("Optional range end (seconds)",text:$endSeconds).textFieldStyle(.roundedBorder)
                TextField("What should change here, and why?",text:$comment,axis:.vertical).lineLimit(3...6).textFieldStyle(.roundedBorder)
                Button("Save annotation",systemImage:"text.bubble") {saveAnnotation()}.buttonStyle(.borderedProminent).disabled(capturePath.isEmpty || comment.isEmpty || w.busy)
                DisclosureGroup("Transcript anchors") {
                    if transcriptWords.isEmpty {Text("No matching render-derived transcript for this selected revision. Frame/time annotations remain available.").font(.caption).foregroundStyle(.secondary)}
                    else {ScrollView {LazyVStack(alignment:.leading) {ForEach(transcriptWords.indices,id:\.self) {i in let word=transcriptWords[i];let id=word["id"] as? String ?? String(i)
                        Toggle("\(word["text"] as? String ?? "") · \(word["start"] as? Int ?? 0) ms",isOn:Binding(get:{selectedWords.contains(id)},set:{if $0{selectedWords.insert(id)}else{selectedWords.remove(id)}}))
                    }}}.frame(maxHeight:130)}
                }
                Text("Choose another revision to compare. Feedback stays attached to the version you reviewed; it is never silently moved after cuts.").font(.caption).foregroundStyle(.secondary)
            }.padding(20).frame(minWidth:560)
            ScrollView {VStack(alignment:.leading,spacing:16) {
                Text("Feedback on this version").font(.title3.bold())
                if feedback.isEmpty {Text("Pause the video to leave a precise note.").foregroundStyle(.secondary)}
                ForEach(feedback.indices,id:\.self) {i in let note=feedback[i]
                    GroupBox {
                        VStack(alignment:.leading,spacing:10) {
                            HStack {Button(String(format:"%.3f s",Double(note["time_ms"] as? Int ?? 0)/1000)) {player.seek(to:CMTime(value:Int64(note["time_ms"] as? Int ?? 0),timescale:1000));player.pause()};Spacer();Text(note["status"] as? String ?? "open").font(.caption).foregroundStyle(.mint)}
                            Text(note["text"] as? String ?? "").textSelection(.enabled)
                            if let path=note["frame_path"] as? String,let image=NSImage(contentsOfFile:path) {Image(nsImage:image).resizable().aspectRatio(contentMode:.fit).frame(maxHeight:130)}
                            DisclosureGroup("Resolve or reopen") {
                                Picker("Replacement revision",selection:$resolution) {Text("Choose revision").tag("");ForEach(w.revisions.indices,id:\.self) {j in Text(w.revisions[j]["label"] as? String ?? "Revision").tag(w.revisions[j]["id"] as? String ?? "")}}
                                TextField("Resolution notes",text:$resolutionNote,axis:.vertical).textFieldStyle(.roundedBorder)
                                HStack {Button("Addressed"){transition(note,"addressed")};Button("Ready for review"){transition(note,"ready_for_review")}}
                                HStack {Button("Accept correction"){transition(note,"accepted")};Button("Reopen"){transition(note,"open")}}
                            }
                            DisclosureGroup("History") {Text(prettyJSON(note["history"] ?? [])).font(.caption).textSelection(.enabled)}
                        }.padding(8)
                    }
                }
            }.padding(18)}.frame(minWidth:300,idealWidth:340,maxWidth:450)
        }.onChange(of:selected){_,_ in loadMedia()}.onChange(of:w.project){_,_ in selected="";player.replaceCurrentItem(with:nil)}
        .onDisappear {player.pause()}
    }
    func loadMedia() {
        player.pause();capturePath="";rect=nil;draw=false;selectedWords=[];transcriptWords=[]
        guard let a=asset,let path=a["path"] as? String else {player.replaceCurrentItem(with:nil);return}
        let av=AVURLAsset(url:URL(fileURLWithPath:path));player.replaceCurrentItem(with:AVPlayerItem(asset:av))
        Task {if let track=try? await av.loadTracks(withMediaType:.video).first,let size=try? await track.load(.naturalSize),let transform=try? await track.load(.preferredTransform) {let s=size.applying(transform);videoSize=CGSize(width:abs(s.width),height:abs(s.height))}}
        if let bytes=try? Data(contentsOf:URL(fileURLWithPath:w.project+"/work/edited-transcript.json")),let d=(try? JSONSerialization.jsonObject(with:bytes)) as? [String:Any],d["master_sha256"] as? String == a["sha256"] as? String {transcriptWords=d["words"] as? [[String:Any]] ?? []}
    }
    func capture() {
        player.pause();draw=false;rect=nil
        let time=player.currentTime().seconds
        guard time.isFinite,let id=asset?["id"] as? String else {return}
        markerMS=max(0,Int((time*1000).rounded()));let ms=markerMS
        w.perform {
            let result=try await w.bridge.request("capture_frame",project:w.project,params:["asset_id":id,"time_ms":ms])
            guard selected==id else {return}
            markerMS=result["time_ms"] as? Int ?? ms;capturePath=result["path"] as? String ?? "";await player.seek(to:CMTime(value:Int64(markerMS),timescale:1000));w.notice="Paused frame captured. Add a note or draw a region."
        }
    }
    func saveAnnotation() {
        guard let id=asset?["id"] as? String else {return}
        var params:[String:Any]=["asset_id":id,"time_ms":markerMS,"text":comment,"frame_path":capturePath,"transcript_ids":Array(selectedWords).sorted()]
        if !endSeconds.isEmpty {guard let end=Double(endSeconds),end.isFinite else {w.error="Enter a valid end time in seconds.";return};params["end_ms"]=Int((end*1000).rounded())}
        if let rect {params["rect"]=["x":rect.minX,"y":rect.minY,"width":rect.width,"height":rect.height]}
        w.perform {try await w.request("add_annotation",params);comment="";capturePath="";endSeconds="";rect=nil;draw=false;selectedWords=[];w.notice="Annotation saved against this exact revision."}
    }
    func transition(_ note:[String:Any],_ status:String) {
        guard let id=note["id"] as? String else{return}
        var p:[String:Any]=["id":id,"status":status,"note":resolutionNote,"user_action":true]
        if !resolution.isEmpty {p["resolution_revision_id"]=resolution}
        w.perform {try await w.request("update_annotation",p);resolutionNote=""}
    }
}
struct AnnotationOverlay:View {
    let videoSize:CGSize
    @Binding var selection:CGRect?
    var body:some View {
        GeometryReader {geometry in
            let bounds=ReviewGeometry.videoRect(container:geometry.size,video:videoSize)
            ZStack {
                Color.black.opacity(0.001)
                if let r=selection {Rectangle().fill(.mint.opacity(0.15)).overlay(Rectangle().stroke(.mint,lineWidth:3)).frame(width:r.width*bounds.width,height:r.height*bounds.height).position(x:bounds.minX+r.midX*bounds.width,y:bounds.minY+r.midY*bounds.height)}
            }.contentShape(Rectangle()).gesture(DragGesture(minimumDistance:2).onChanged {value in selection=ReviewGeometry.selection(from:value.startLocation,to:value.location,in:bounds)})
        }
    }
}
