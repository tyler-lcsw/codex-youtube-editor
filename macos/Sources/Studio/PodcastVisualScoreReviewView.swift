import SwiftUI
import AppKit
import StudioCore

private struct PendingPodcastDecision:Identifiable {
    let id=UUID()
    let event:PodcastVisualEvent
    let action:PodcastVisualDecisionAction
    let note:String
}

struct PodcastVisualScoreReviewView:View {
    @EnvironmentObject var w:Workspace
    @State private var artifacts:PodcastVisualScoreArtifacts?
    @State private var unavailable=""
    @State private var loadError:String?
    @State private var bindingCurrent:Bool?
    @State private var bindingError:String?
    @State private var selectedChapterID=""
    @State private var loadedRevision=""
    @State private var notes=[String:String]()
    @State private var pending:PendingPodcastDecision?

    var chapterEvents:[PodcastVisualEvent] {artifacts?.score.events.filter {$0.chapterID == selectedChapterID} ?? []}

    var body:some View {
        ScrollView {
            VStack(alignment:.leading,spacing:20) {
                Text("Review the visual score before rendering").font(.title2.bold())
                Text("These are chapter-scoped proposals for the continuous podcast stage. A proposal is not a rendered result, and no model output is accepted until you record an explicit decision for this exact score revision.").foregroundStyle(.secondary)
                if w.project.isEmpty {
                    StudioEmptyState(symbol:"waveform.path",title:"Open a production",detail:"Podcast visual-score artifacts belong to one saved Studio production.")
                } else if let loadError {
                    StudioEmptyState(symbol:"exclamationmark.triangle",title:"Podcast review artifacts need attention",detail:loadError)
                } else if !unavailable.isEmpty {
                    StudioEmptyState(symbol:"text.badge.plus",title:"No visual score to review",detail:unavailable)
                } else if let artifacts {
                    scoreSummary(artifacts)
                    chapterReview(artifacts)
                } else {
                    ProgressView("Reading podcast review artifacts…").accessibilityLabel("Reading podcast review artifacts")
                }
            }.padding(24)
        }
        .onAppear {load()}
        .onChange(of:w.project){_,_ in load()}
        .onChange(of:w.dataRevision){_,_ in load()}
        .alert("Record owner decision?",isPresented:Binding(get:{pending != nil},set:{if !$0 {pending=nil}})) {
            Button("Cancel",role:.cancel){pending=nil}.accessibilityLabel("Cancel owner decision")
            Button(pending?.action.label ?? "Record") {recordPendingDecision()}.accessibilityLabel("Confirm owner decision")
        } message: {
            Text("This appends a decision for score revision \(shortRevision(artifacts?.score.revisionID ?? "")). It does not approve a model, a render, or the finished episode.")
        }
    }

    @ViewBuilder func scoreSummary(_ artifacts:PodcastVisualScoreArtifacts)->some View {
        GroupBox("Whole-episode visual density") {
            VStack(alignment:.leading,spacing:12) {
                HStack {
                    StudioStatus(status:artifacts.score.visualDensity.label.lowercased())
                    Text("\(artifacts.score.events.count) proposed moments across \(artifacts.episodeMap.chapters.count) chapters")
                    Spacer()
                    Text("Revision \(shortRevision(artifacts.score.revisionID))").font(.caption).monospaced().textSelection(.enabled)
                }
                PodcastVisualDensityTimeline(events:artifacts.score.events,durationMS:artifacts.episodeMap.durationMS)
                if bindingCurrent == nil {
                    ProgressView("Checking score binding…").controlSize(.small).accessibilityLabel("Checking visual score binding")
                } else if bindingCurrent == false {
                    Label(bindingError ?? "This score no longer matches the current podcast settings, source, or episode map. Decisions are disabled.",systemImage:"exclamationmark.triangle")
                        .font(.caption).foregroundStyle(StudioTheme.accent)
                }
                ForEach(artifacts.score.events) {event in
                    HStack(alignment:.firstTextBaseline) {
                        Text(timeRange(event.startMS,event.endMS)).monospacedDigit().frame(width:112,alignment:.leading)
                        Text(event.typeLabel)
                        Spacer()
                        Text(chapterTitle(event.chapterID,artifacts:artifacts)).foregroundStyle(.secondary)
                    }.font(.caption).accessibilityElement(children:.combine)
                }
                Text("Density is shown from actual proposal ranges; it is not an effects-per-minute target.").font(.caption).foregroundStyle(.secondary)
            }.padding(12)
        }
    }

    @ViewBuilder func chapterReview(_ artifacts:PodcastVisualScoreArtifacts)->some View {
        GroupBox("Chapter decisions") {
            VStack(alignment:.leading,spacing:14) {
                Picker("Chapter",selection:$selectedChapterID) {
                    ForEach(artifacts.episodeMap.chapters) {chapter in
                        Text("\(chapter.title) · \(timeRange(chapter.startMS,chapter.endMS))").tag(chapter.id)
                    }
                }.accessibilityLabel("Podcast chapter to review")
                if chapterEvents.isEmpty {
                    StudioEmptyState(symbol:"waveform",title:"Base stage only",detail:"This chapter has no custom visual proposal. No decision is manufactured from that absence.")
                } else {
                    ForEach(chapterEvents) {event in eventReview(event,artifacts:artifacts)}
                }
            }.padding(12)
        }
    }

    @ViewBuilder func eventReview(_ event:PodcastVisualEvent,artifacts:PodcastVisualScoreArtifacts)->some View {
        let decision=artifacts.decisions.latest(for:event.id,revisionID:artifacts.score.revisionID)
        VStack(alignment:.leading,spacing:10) {
            HStack {
                Label(event.typeLabel,systemImage:event.type == "base" ? "rectangle" : "sparkles.rectangle.stack")
                    .font(.headline).accessibilityLabel("Proposal type: \(event.typeLabel)")
                Text(timeRange(event.startMS,event.endMS)).monospacedDigit().foregroundStyle(.secondary)
                Spacer()
                StudioStatus(status:decisionStatus(decision))
            }
            Text(event.purpose)
            DisclosureGroup("Proposal details") {
                VStack(alignment:.leading,spacing:6) {
                    detail("Treatment",event.treatmentSummary)
                    detail("Transcript anchor",event.transcriptAnchorSummary)
                    detail("Provenance",event.provenanceSummary)
                    detail("Camera policy",event.cameraPolicySummary)
                }.font(.caption).textSelection(.enabled)
            }
            if !event.isSupported {
                Label("This Studio build does not recognize the proposal type. Accept is disabled; reject it or explicitly keep the base stage.",systemImage:"exclamationmark.triangle").font(.caption).foregroundStyle(StudioTheme.accent)
            }
            if let preview=preview(for:event,artifacts:artifacts) {
                previewControl(preview)
            } else {
                Text("No representative preview path was recorded for this proposal.").font(.caption).foregroundStyle(.secondary)
            }
            TextField("Decision note (required)",text:Binding(get:{notes[event.id] ?? ""},set:{notes[event.id]=$0}),axis:.vertical)
                .accessibilityLabel("Decision note for \(event.typeLabel)").textFieldStyle(.roundedBorder).lineLimit(2...4)
            HStack {
                Button(event.type == "base" ? "Accept base stage" : "Accept proposal") {prepare(event,.accept)}
                    .accessibilityLabel(event.type == "base" ? "Accept base stage for this event" : "Accept this visual proposal")
                    .disabled(!event.isSupported || noteIsEmpty(event) || bindingCurrent != true || w.busy)
                if event.type != "base" {
                    Button("Keep base stage") {prepare(event,.useBase)}.accessibilityLabel("Keep the base stage instead of this proposal").disabled(noteIsEmpty(event) || bindingCurrent != true || w.busy)
                }
                Button("Reject proposal",role:.destructive) {prepare(event,.reject)}.accessibilityLabel("Reject this visual proposal").disabled(noteIsEmpty(event) || bindingCurrent != true || w.busy)
            }
            if let decision {
                Text("Latest decision for this revision: \(decision.action.label) · \(decision.decidedAt)\(decision.note.isEmpty ? "" : " · \(decision.note)")").font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
            }
        }.padding(14).background(StudioTheme.canvas,in:RoundedRectangle(cornerRadius:10))
            .overlay(RoundedRectangle(cornerRadius:10).stroke(StudioTheme.border.opacity(0.6)))
    }

    @ViewBuilder func detail(_ label:String,_ value:String)->some View {
        Text("\(label): ").bold()+Text(value)
    }
    @ViewBuilder func previewControl(_ preview:PodcastVisualPreview)->some View {
        let url=PodcastVisualPreviewAccess.openableURL(preview,projectPath:w.project)
        HStack {
            Label("Representative preview",systemImage:"photo")
            Text(preview.path).font(.caption).lineLimit(1).truncationMode(.middle).textSelection(.enabled)
            Spacer()
            Button("Open preview") {if let url {NSWorkspace.shared.open(url)}}.accessibilityLabel("Open representative preview")
                .disabled(url == nil)
        }
        if url == nil {Text("The preview is missing or its recorded SHA-256 no longer matches. Open is disabled.").font(.caption).foregroundStyle(StudioTheme.accent)}
    }
    func load() {
        artifacts=nil;unavailable="";loadError=nil;bindingCurrent=nil;bindingError=nil;pending=nil
        guard !w.project.isEmpty else{return}
        do {
            switch try PodcastVisualScoreArtifacts.load(projectPath:w.project) {
            case .unavailable(let message):unavailable=message
            case .loaded(let loaded):
                if !loadedRevision.isEmpty,loadedRevision != loaded.score.revisionID {notes=[:]}
                loadedRevision=loaded.score.revisionID
                artifacts=loaded
                checkBinding(project:w.project,revisionID:loaded.score.revisionID)
                if !loaded.episodeMap.chapters.contains(where:{$0.id == selectedChapterID}) {
                    selectedChapterID=loaded.episodeMap.chapters.first?.id ?? ""
                }
            }
        } catch {loadError=error.localizedDescription}
    }
    func checkBinding(project:String,revisionID:String) {
        let bridge=w.bridge
        Task {
            do {
                let state=try await bridge.request("podcast_visual_score",project:project)
                guard w.project == project,artifacts?.score.revisionID == revisionID else{return}
                bindingCurrent=PodcastVisualScoreBinding.isCurrent(state,revisionID:revisionID)
            } catch {
                guard w.project == project,artifacts?.score.revisionID == revisionID else{return}
                bindingCurrent=false;bindingError="The current score binding could not be verified: \(error.localizedDescription)"
            }
        }
    }
    func prepare(_ event:PodcastVisualEvent,_ action:PodcastVisualDecisionAction) {
        let note=notes[event.id]?.trimmingCharacters(in:.whitespacesAndNewlines) ?? ""
        guard !note.isEmpty else{return}
        pending=PendingPodcastDecision(event:event,action:action,note:note)
    }
    func recordPendingDecision() {
        guard let pending,let revision=artifacts?.score.revisionID else{return}
        do {
            let payload=try PodcastVisualScoreDecisionPayload.build(revisionID:revision,eventID:pending.event.id,action:pending.action,note:pending.note)
            self.pending=nil
            w.perform {
                _ = try await w.bridge.request("append_visual_score_decision",project:w.project,params:payload)
                try await w.refresh()
                notes[pending.event.id]="";load();w.notice="Owner decision appended for visual-score revision \(shortRevision(revision))."
            }
        } catch {loadError=error.localizedDescription}
    }
    func noteIsEmpty(_ event:PodcastVisualEvent)->Bool {notes[event.id]?.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty != false}
    func preview(for event:PodcastVisualEvent,artifacts:PodcastVisualScoreArtifacts)->PodcastVisualPreview? {
        artifacts.score.previews.last {$0.chapterID == event.chapterID}
    }
    func chapterTitle(_ id:String,artifacts:PodcastVisualScoreArtifacts)->String {artifacts.episodeMap.chapters.first {$0.id == id}?.title ?? id}
    func decisionStatus(_ decision:PodcastVisualScoreDecision?)->String {
        guard let action=decision?.action else{return "unreviewed"}
        switch action {
        case .accept:return "accepted"
        case .reject:return "rejected"
        case .useBase:return "base stage"
        case .requestChanges:return "changes requested"
        }
    }
    func shortRevision(_ value:String)->String {value.isEmpty ? "unknown" : String(value.prefix(12))}
    func timeRange(_ start:Int,_ end:Int)->String {"\(time(start))–\(time(end))"}
    func time(_ milliseconds:Int)->String {String(format:"%02d:%02d",milliseconds/60000,(milliseconds/1000)%60)}
}

private struct PodcastVisualDensityTimeline:View {
    let events:[PodcastVisualEvent]
    let durationMS:Int
    var body:some View {
        GeometryReader {geometry in
            ZStack(alignment:.leading) {
                RoundedRectangle(cornerRadius:4).fill(StudioTheme.border.opacity(0.3)).frame(height:24)
                ForEach(events) {event in
                    let start=CGFloat(event.startMS)/CGFloat(max(durationMS,1))*geometry.size.width
                    let width=max(2,CGFloat(event.endMS-event.startMS)/CGFloat(max(durationMS,1))*geometry.size.width)
                    RoundedRectangle(cornerRadius:3).fill(event.type == "base" ? StudioTheme.graphite.opacity(0.55) : StudioTheme.coral.opacity(0.85))
                        .frame(width:width,height:24).offset(x:start)
                }
            }
        }.frame(height:24).accessibilityElement(children:.ignore)
            .accessibilityLabel("Whole episode proposal timeline with \(events.count) visual events over \(durationMS) milliseconds")
    }
}
