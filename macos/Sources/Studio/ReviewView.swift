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
    @State private var markerReady=false
    @State private var selectedHasVideo=false
    @State private var drafts=AnnotationDrafts()
    @State private var reviewContext:AnnotationContext?
    @State private var integrityError:String?
    @State private var validatedID=""
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
                    Button("Add revision") {w.importFiles(revision:true)}.accessibilityLabel("Add revision").disabled(w.project.isEmpty)
                }
                GeometryReader {geometry in
                    ZStack {
                        if asset == nil {
                            StudioEmptyState(symbol:"play.rectangle",title:"Choose media to review",detail:"Import a source in Brief & sources, or choose an existing source or revision above.")
                                .frame(maxWidth:.infinity,maxHeight:.infinity).background(StudioTheme.panel)
                        } else {
                            NativeReviewPlayer(player:player)
                            if validatedID == selected && !selectedHasVideo {
                                Label("Audio-only source",systemImage:"waveform").foregroundStyle(.white).padding(10).background(.black.opacity(0.65),in:RoundedRectangle(cornerRadius:8)).accessibilityLabel("Audio-only source; use playback controls and mark a time to annotate")
                            }
                        }
                        if draw {AnnotationOverlay(videoSize:videoSize,selection:$rect)}
                        if !draw,let rect=reviewContext?.rect ?? rect {
                            let bounds=ReviewGeometry.videoRect(container:geometry.size,video:videoSize)
                            Rectangle().stroke(StudioTheme.coral,lineWidth:3).frame(width:rect.width*bounds.width,height:rect.height*bounds.height).position(x:bounds.minX+rect.midX*bounds.width,y:bounds.minY+rect.midY*bounds.height).allowsHitTesting(false)
                        }
                    }.background(.black)
                }.frame(minHeight:280)
                HStack {
                    Button(selectedHasVideo ? "Pause & capture frame" : "Pause & mark time",systemImage:"pause.circle") {capture()}.accessibilityLabel(selectedHasVideo ? "Pause and capture frame" : "Pause and mark audio time").disabled(asset==nil || validatedID != selected || w.busy)
                    Toggle("Draw region",isOn:$draw).accessibilityLabel("Draw region").toggleStyle(.button).disabled(!selectedHasVideo || capturePath.isEmpty)
                    Button("Clear region"){rect=nil}.accessibilityLabel("Clear region").disabled(!selectedHasVideo || rect == nil)
                    Text(String(format:"%.3f s",Double(markerMS)/1000)).monospacedDigit()
                }
                if let integrityError {Text("Historical feedback only: \(integrityError)").foregroundStyle(StudioTheme.accent)}
                if !capturePath.isEmpty {Label("Frame captured for this version",systemImage:"checkmark.circle").font(.caption).foregroundStyle(StudioTheme.accent)}
                else if markerReady {Label("Audio time marked for this version",systemImage:"checkmark.circle").font(.caption).foregroundStyle(StudioTheme.accent)}
                TextField("Optional range end (seconds)",text:$endSeconds).accessibilityLabel("Optional range end (seconds)").textFieldStyle(.roundedBorder)
                TextField("What should change here, and why?",text:$comment,axis:.vertical).accessibilityLabel("What should change here, and why?").lineLimit(3...6).textFieldStyle(.roundedBorder)
                Button("Save annotation",systemImage:"text.bubble") {saveAnnotation()}.accessibilityLabel("Save annotation").buttonStyle(.borderedProminent).tint(StudioTheme.button).disabled(!markerReady || comment.isEmpty || w.busy)
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
                Text("\(w.annotations.filter{$0["status"] as? String != "accepted"}.count) unresolved across this production. Select the original reviewed version to see its notes.").font(.caption).foregroundStyle(.secondary)
                if feedback.isEmpty {StudioEmptyState(symbol:"text.bubble",title:"No feedback on this version",detail:"Pause the selected media to add a frame, region, moment, or time-range note.")}
                ForEach(feedback.indices,id:\.self) {i in let note=feedback[i];let noteID=note["id"] as? String ?? ""
                    GroupBox {
                        VStack(alignment:.leading,spacing:10) {
                            HStack {Button(String(format:"%.3f s",Double(note["time_ms"] as? Int ?? 0)/1000)) {reviewContext=AnnotationContext(note);draw=false;player.seek(to:CMTime(value:Int64(note["time_ms"] as? Int ?? 0),timescale:1000));player.pause()};Spacer();StudioStatus(status:(integrityError == nil ? "" : "historical · ")+(note["status"] as? String ?? "open"))}
                            Text(note["text"] as? String ?? "").textSelection(.enabled)
                            if let path=note["frame_path"] as? String,let image=NSImage(contentsOfFile:path) {MarkedFrame(image:image,rect:AnnotationContext(note).rect).frame(height:130)}
                            if let end=note["end_ms"] as? Int {Text(String(format:"Range ends at %.3f s",Double(end)/1000)).font(.caption)}
                            if let anchors=note["transcript_ids"] as? [String],!anchors.isEmpty {Text("Transcript: \(anchors.joined(separator:", "))").font(.caption)}
                            DisclosureGroup("Resolve or reopen") {
                                Picker("Replacement revision",selection:Binding(get:{drafts.revision(for:noteID,fallback:note["resolution_revision_id"] as? String)},set:{drafts.setRevision($0,for:noteID)})) {Text("Choose revision").tag("");ForEach(w.revisions.indices,id:\.self) {j in Text(w.revisions[j]["label"] as? String ?? "Revision").tag(w.revisions[j]["id"] as? String ?? "")}}
                                Text("Add resolution notes before changing status.").font(.caption).foregroundStyle(.secondary)
                                TextField("Resolution notes",text:Binding(get:{drafts.note(for:noteID)},set:{drafts.setNote($0,for:noteID)}),axis:.vertical).accessibilityLabel("Resolution notes").textFieldStyle(.roundedBorder)
                                HStack {Button("Addressed"){transition(note,"addressed")}.accessibilityLabel("Addressed").disabled(!canTransition(note,"addressed"));Button("Ready for review"){transition(note,"ready_for_review")}.accessibilityLabel("Ready for review").disabled(!canTransition(note,"ready_for_review"))}
                                HStack {Button("Accept correction"){transition(note,"accepted")}.accessibilityLabel("Accept correction").disabled(!canTransition(note,"accepted"));Button("Reopen"){transition(note,"open")}.accessibilityLabel("Reopen").disabled(!canTransition(note,"open"))}
                            }
                            DisclosureGroup("History") {Text(prettyJSON(note["history"] ?? [])).font(.caption).textSelection(.enabled)}
                        }.padding(8)
                    }
                }
            }.padding(18)}.frame(minWidth:300,idealWidth:340,maxWidth:450)
        }.onChange(of:selected){_,_ in loadMedia()}.onChange(of:w.project){_,_ in selected="";drafts=AnnotationDrafts();reviewContext=nil;player.replaceCurrentItem(with:nil)}
        .onDisappear {player.pause()}
    }
    func loadMedia() {
        player.pause();player.replaceCurrentItem(with:nil);capturePath="";markerReady=false;selectedHasVideo=false;rect=nil;draw=false;selectedWords=[];transcriptWords=[];reviewContext=nil;integrityError=nil;validatedID=""
        guard let a=asset,let id=a["id"] as? String else {return}
        let project=w.project,bridge=w.bridge
        Task {
            do {
                let checked=try await bridge.request("validate_asset",project:project,params:["asset_id":id])
                guard selected==id,w.project==project,let path=checked["path"] as? String else{return}
                let av=AVURLAsset(url:URL(fileURLWithPath:path))
                if let track=try await av.loadTracks(withMediaType:.video).first {
                    let size=try await track.load(.naturalSize),transform=try await track.load(.preferredTransform)
                    let transformed=size.applying(transform)
                    guard selected==id,w.project==project else{return}
                    videoSize=CGSize(width:abs(transformed.width),height:abs(transformed.height));selectedHasVideo=true
                }
                guard selected==id,w.project==project else{return}
                validatedID=id;player.replaceCurrentItem(with:AVPlayerItem(asset:av))
                if let bytes=try? Data(contentsOf:URL(fileURLWithPath:project+"/work/edited-transcript.json")),let d=(try? JSONSerialization.jsonObject(with:bytes)) as? [String:Any],d["master_sha256"] as? String == a["sha256"] as? String {transcriptWords=d["words"] as? [[String:Any]] ?? []}
            } catch {if selected==id,w.project==project {integrityError=error.localizedDescription}}
        }
    }
    func capture() {
        player.pause();draw=false;rect=nil;reviewContext=nil
        let time=player.currentTime().seconds
        guard let id=asset?["id"] as? String,let action=ReviewMarkerDecision.action(seconds:time,hasVideo:selectedHasVideo) else {return}
        switch action {
        case .markTime(let ms):
            markerMS=ms;capturePath="";markerReady=true
            w.notice="Audio time marked. Add a note, optional range, or transcript anchors."
        case .captureFrame(let ms):
            capturePath="";markerReady=false
            w.perform {
                let result=try await w.bridge.request("capture_frame",project:w.project,params:["asset_id":id,"time_ms":ms])
                guard selected==id else {return}
                markerMS=result["time_ms"] as? Int ?? ms;capturePath=result["path"] as? String ?? "";markerReady = !capturePath.isEmpty;await player.seek(to:CMTime(value:Int64(markerMS),timescale:1000));w.notice="Paused frame captured. Add a note or draw a region."
            }
        }
    }
    func saveAnnotation() {
        guard let id=asset?["id"] as? String else {return}
        var params:[String:Any]=["asset_id":id,"time_ms":markerMS,"text":comment,"transcript_ids":Array(selectedWords).sorted()]
        if !capturePath.isEmpty {params["frame_path"]=capturePath}
        if !endSeconds.isEmpty {guard let end=Double(endSeconds),end.isFinite else {w.error="Enter a valid end time in seconds.";return};params["end_ms"]=Int((end*1000).rounded())}
        if let rect {params["rect"]=["x":rect.minX,"y":rect.minY,"width":rect.width,"height":rect.height]}
        w.perform {try await w.request("add_annotation",params);comment="";capturePath="";markerReady=false;endSeconds="";rect=nil;draw=false;selectedWords=[];w.notice="Annotation saved against this exact revision."}
    }
    func canTransition(_ note:[String:Any],_ status:String)->Bool {
        guard !w.busy,let id=note["id"] as? String,!drafts.note(for:id).trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else{return false}
        let allowed=["open":["addressed"],"addressed":["open","ready_for_review"],"ready_for_review":["open","addressed","accepted"],"accepted":["open"]]
        guard allowed[note["status"] as? String ?? ""]?.contains(status) == true else{return false}
        return status == "open" || !drafts.revision(for:id,fallback:note["resolution_revision_id"] as? String).isEmpty
    }
    func transition(_ note:[String:Any],_ status:String) {
        guard let id=note["id"] as? String else{return}
        let revision=drafts.revision(for:id,fallback:note["resolution_revision_id"] as? String)
        var p:[String:Any]=["id":id,"status":status,"note":drafts.note(for:id),"user_action":true]
        if !revision.isEmpty {p["resolution_revision_id"]=revision}
        w.perform {try await w.request("update_annotation",p);drafts.setNote("",for:id)}
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
                if let r=selection {Rectangle().fill(StudioTheme.coral.opacity(0.15)).overlay(Rectangle().stroke(StudioTheme.coral,lineWidth:3)).frame(width:r.width*bounds.width,height:r.height*bounds.height).position(x:bounds.minX+r.midX*bounds.width,y:bounds.minY+r.midY*bounds.height)}
            }.contentShape(Rectangle()).gesture(DragGesture(minimumDistance:2).onChanged {value in selection=ReviewGeometry.selection(from:value.startLocation,to:value.location,in:bounds)})
        }
    }
}

struct MarkedFrame:View {
    let image:NSImage
    let rect:CGRect?
    var body:some View {
        GeometryReader {g in
            let bounds=ReviewGeometry.videoRect(container:g.size,video:image.size)
            ZStack {
                Image(nsImage:image).resizable().aspectRatio(contentMode:.fit).frame(width:g.size.width,height:g.size.height)
                if let r=rect {Rectangle().stroke(StudioTheme.coral,lineWidth:2).frame(width:r.width*bounds.width,height:r.height*bounds.height).position(x:bounds.minX+r.midX*bounds.width,y:bounds.minY+r.midY*bounds.height)}
            }
        }
    }
}

// Avoid _AVKit_SwiftUI.VideoPlayerView metadata initialization, which aborts on
// the qualified M4 runtime. Keep AVKit controls through its public AppKit view.
private struct NativeReviewPlayer:NSViewRepresentable {
    let player:AVPlayer
    func makeNSView(context:Context)->AVPlayerView {
        let view=AVPlayerView();view.controlsStyle = .inline;view.videoGravity = .resizeAspect;view.player=player
        return view
    }
    func updateNSView(_ view:AVPlayerView,context:Context) {if view.player !== player {view.player=player}}
    static func dismantleNSView(_ view:AVPlayerView,coordinator:()) {view.player=nil}
}
