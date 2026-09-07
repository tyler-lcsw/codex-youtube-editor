import SwiftUI
import StudioCore

struct PodcastQualificationView:View {
    @EnvironmentObject var w:Workspace
    let currentVisualScoreRevisionID:String?
    @State private var snapshot:PodcastQualificationSnapshot?
    @State private var loadError:String?

    var body:some View {
        GroupBox("Long-form qualification") {
            VStack(alignment:.leading,spacing:12) {
                HStack(alignment:.firstTextBaseline) {
                    Text("Read-only evidence from measured qualification attempts. Studio cannot mark a review complete or create owner acceptance from this report.")
                        .foregroundStyle(.secondary)
                    Spacer()
                    Button("Reload qualification",systemImage:"arrow.clockwise") {load()}
                        .accessibilityLabel("Reload podcast qualification evidence")
                }
                if let loadError {
                    Label(loadError,systemImage:"exclamationmark.triangle").foregroundStyle(StudioTheme.accent).textSelection(.enabled)
                } else if let snapshot {
                    if let report=snapshot.report {
                        qualificationReport(report)
                    } else {
                        StudioEmptyState(symbol:"gauge.with.dots.needle.33percent",title:"No successful technical report",detail:snapshot.availability+" Failed or interrupted attempts remain visible below when recorded.")
                    }
                    attemptHistory(snapshot.attempts)
                } else {
                    ProgressView("Reading qualification evidence…").accessibilityLabel("Reading podcast qualification evidence")
                }
            }.padding(12)
        }
        .onAppear {load()}
        .onChange(of:w.project){_,_ in load()}
        .onChange(of:w.dataRevision){_,_ in load()}
    }

    @ViewBuilder func qualificationReport(_ report:PodcastQualificationAttempt)->some View {
        VStack(alignment:.leading,spacing:14) {
            HStack {
                Label("Technical long-form qualification succeeded",systemImage:"checkmark.circle").font(.headline)
                Spacer()
                Text("Attempt \(report.attemptID)").font(.caption).monospaced().textSelection(.enabled)
            }
            Text(report.summary).font(.callout)
            GroupBox("Recorded technical metrics") {
                VStack(alignment:.leading,spacing:7) {
                    metric("Runtime",report.performance.wallSeconds.map {duration($0)} ?? "Not recorded")
                    metric("Peak child-process memory",report.performance.peakRSSBytes.map {bytes($0)} ?? "Not recorded")
                    metric("Memory samples",report.performance.sampleCount.map(String.init) ?? "Not recorded")
                    metric("Free memory before / after / minimum",pressure(report.performance))
                    metric("Pressure level before / after / peak",pressureLevels(report.performance))
                    metric("Delivery",delivery(report.delivery))
                    metric("Full decode",report.decode.status+(report.decode.exitCode.map {" · exit \($0)"} ?? ""))
                    metric("Cache",report.cacheSummary)
                }.padding(10)
            }
            GroupBox("Evidence binding") {
                VStack(alignment:.leading,spacing:7) {
                    metric("Reviewed stage current",report.bindings.reviewedStageCurrent ? "yes" : "no")
                    metric("Matches displayed score revision",scoreBinding(report))
                    metric("Qualification target",qualificationTarget(report.bindings.target))
                    metric("Visual-score revision",report.bindings.visualScoreRevisionID ?? "Not recorded")
                    metric("Source",boundFile(report.bindings.sourcePath,report.bindings.sourceSHA256))
                    metric("Contract",report.bindings.contractPath ?? "Not recorded")
                    metric("Output",boundFile(report.bindings.outputPath,report.bindings.outputSHA256))
                }.padding(10).textSelection(.enabled)
            }
            GroupBox("Reviews still required") {
                VStack(alignment:.leading,spacing:7) {
                    review("Technical validation",report.reviews.technicalValidation)
                    review("Visual inspection",report.reviews.visualInspection)
                    review("Normal-speed listening",report.reviews.normalSpeedListening)
                    review("Owner acceptance",report.reviews.ownerAcceptance)
                    metric("Creative acceptance",report.reviews.creativeAcceptance ? "recorded" : "not recorded")
                }.padding(10)
            }
            Label("Network: \(used(report.safety.networkUsed)) · Publication: \(used(report.safety.publicationUsed)) · Models: \(used(report.safety.modelsUsed))",systemImage:"lock.shield")
                .font(.caption).accessibilityLabel("Safety record. Network \(used(report.safety.networkUsed)). Publication \(used(report.safety.publicationUsed)). Models \(used(report.safety.modelsUsed)).")
            Text("Started \(report.startedAt) · Finished \(report.finishedAt ?? "not recorded") · \(report.platform)").font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
            Text("Production-quality action: \(report.qualityActionID ?? "not recorded")").font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
        }
    }

    @ViewBuilder func attemptHistory(_ attempts:[PodcastQualificationAttempt])->some View {
        DisclosureGroup("Attempt history (\(attempts.count))") {
            if attempts.isEmpty {
                Text("No qualification attempts are recorded.").font(.caption).foregroundStyle(.secondary)
            } else {
                VStack(alignment:.leading,spacing:10) {
                    ForEach(attempts) {attempt in
                        DisclosureGroup {
                            VStack(alignment:.leading,spacing:6) {
                                Text(attempt.summary)
                                metric("Interruption",attempt.interruption.status)
                                metric("Recovery",attempt.interruption.recoveryStatus)
                                if let failure=attempt.failure {
                                    Label("\(failure.type): \(failure.message)",systemImage:"exclamationmark.triangle").foregroundStyle(StudioTheme.accent)
                                }
                                metric("Preservation",attempt.preservationSummary)
                                Text("Started \(attempt.startedAt) · Finished \(attempt.finishedAt ?? "not recorded")").font(.caption).foregroundStyle(.secondary)
                            }.padding(.vertical,6).textSelection(.enabled)
                        } label: {
                            HStack {Text(attempt.attemptID).monospaced();Spacer();StudioStatus(status:attempt.status.rawValue)}
                        }
                    }
                }.padding(.top,8)
            }
        }.accessibilityLabel("Qualification attempt history, \(attempts.count) attempts")
    }

    @ViewBuilder func metric(_ label:String,_ value:String)->some View {
        HStack(alignment:.firstTextBaseline) {Text(label).fontWeight(.semibold);Spacer();Text(value).multilineTextAlignment(.trailing)}
            .font(.caption).accessibilityElement(children:.combine)
    }
    @ViewBuilder func review(_ label:String,_ status:String)->some View {
        HStack {Text(label);Spacer();StudioStatus(status:status)}.accessibilityElement(children:.combine)
    }
    func load() {
        snapshot=nil;loadError=nil
        guard !w.project.isEmpty else{return}
        do {snapshot=try PodcastQualificationSnapshot.load(projectPath:w.project)}
        catch {loadError=error.localizedDescription}
    }
    func pressure(_ performance:PodcastQualificationPerformance)->String {
        let values=[performance.pressureBeforePercent,performance.pressureAfterPercent,performance.minimumFreePercent]
        return values.map {$0.map {String(format:"%.1f%%",$0)} ?? "not recorded"}.joined(separator:" / ")
    }
    func pressureLevels(_ performance:PodcastQualificationPerformance)->String {
        [performance.pressureBeforeLevel,performance.pressureAfterLevel,performance.peakPressureLevel]
            .map {$0.map(String.init) ?? "not recorded"}.joined(separator:" / ")
    }
    func scoreBinding(_ report:PodcastQualificationAttempt)->String {
        guard let currentVisualScoreRevisionID,let reportRevision=report.bindings.visualScoreRevisionID else{return "not verified"}
        return currentVisualScoreRevisionID == reportRevision ? "yes" : "no — report is for another score revision"
    }
    func delivery(_ delivery:PodcastQualificationDelivery)->String {
        var parts=[String]()
        if let duration=delivery.durationSeconds {parts.append(self.duration(duration))}
        if let width=delivery.width,let height=delivery.height {parts.append("\(width)×\(height)")}
        if let codec=delivery.videoCodec {parts.append(codec)}
        if let codec=delivery.audioCodec {parts.append(codec)}
        if let frames=delivery.frameCount {parts.append("\(frames) frames")}
        if let rate=delivery.frameRate {parts.append(rate+" fps")}
        if let size=delivery.sizeBytes {parts.append(bytes(size))}
        return parts.isEmpty ? "Not recorded" : parts.joined(separator:" · ")
    }
    func boundFile(_ path:String?,_ sha256:String?)->String {
        guard let path else{return "Not recorded"}
        return path+(sha256.map {" · \(String($0.prefix(12)))…"} ?? "")
    }
    func qualificationTarget(_ target:PodcastQualificationTarget?)->String {
        guard let target else{return "Not recorded"}
        return "\(duration(Double(target.durationMS)/1000)) · \(target.width)×\(target.height) · \(target.fps.formatted()) fps · \(target.expectedFrameCount) frames"
    }
    func duration(_ seconds:Double)->String {String(format:"%.1f minutes",seconds/60)}
    func bytes(_ value:Int)->String {ByteCountFormatter.string(fromByteCount:Int64(value),countStyle:.memory)}
    func used(_ value:Bool)->String {value ? "invoked" : "not invoked"}
}
