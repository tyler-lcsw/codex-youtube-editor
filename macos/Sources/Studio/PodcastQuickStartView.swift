import SwiftUI
import StudioCore

struct PodcastQuickStartView:View {
    @EnvironmentObject var w:Workspace

    var body:some View {
        ScrollView {
            VStack(alignment:.leading,spacing:22) {
                Label("Solo audio-first podcast",systemImage:"waveform")
                    .font(.title2.weight(.semibold))
                Text(PodcastQuickStartContent.workflowExplanation).foregroundStyle(.secondary)
                GroupBox("Start here") {
                    VStack(alignment:.leading,spacing:14) {
                        ForEach(PodcastQuickStartAction.allCases,id:\.self) {action in
                            Button {w.open(action.route)} label: {
                                HStack(alignment:.top,spacing:12) {
                                    Image(systemName:action.systemImage).font(.title2).frame(width:30)
                                    VStack(alignment:.leading,spacing:4) {
                                        Text(action.title).font(.headline)
                                        Text(action.detail).font(.callout).foregroundStyle(.secondary)
                                    }
                                    Spacer()
                                    Image(systemName:"chevron.right").foregroundStyle(.secondary)
                                }.contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                            .accessibilityLabel(action.accessibilityLabel)
                            .disabled(w.busy)
                            if action != PodcastQuickStartAction.allCases.last {Divider()}
                        }
                    }.padding(12)
                }
                GroupBox("What this mode supports") {
                    VStack(alignment:.leading,spacing:10) {
                        Label("Audio-only or optional associated camera video",systemImage:"waveform")
                        Label("Branded dynamic waveform and continuous base stage",systemImage:"waveform.path.ecg")
                        Label("Chapter cards, key points, lists, comparisons, and image/source cards",systemImage:"rectangle.stack")
                        Label("Currentness checks and explicit owner decisions",systemImage:"checkmark.shield")
                    }.padding(12)
                }
                Text("Current scope: one speaker. Multiple speakers, diarization, multicamera direction, avatars, and publication are not part of this mode.")
                    .font(.caption).foregroundStyle(.secondary)
            }.padding(24)
        }
    }
}
