import Foundation

public enum PodcastQualificationStatus:String,Equatable {
    case succeeded,failed,interrupted
}

public struct PodcastQualificationBindings:Equatable {
    public let sourcePath:String?
    public let sourceSHA256:String?
    public let contractPath:String?
    public let outputPath:String?
    public let outputSHA256:String?
    public let visualScoreRevisionID:String?
    public let reviewedStageCurrent:Bool
    public let target:PodcastQualificationTarget?
}

public struct PodcastQualificationTarget:Equatable {
    public let durationMS:Int
    public let fps:Double
    public let width:Int
    public let height:Int
    public let expectedFrameCount:Int
    public let durationToleranceMS:Int
    public let audioDurationToleranceMS:Int
    public let frameCountTolerance:Int
    public let fpsTolerance:Double
}

public struct PodcastQualificationPerformance:Equatable {
    public let wallSeconds:Double?
    public let peakRSSBytes:Int?
    public let sampleCount:Int?
    public let pressureBeforePercent:Double?
    public let pressureAfterPercent:Double?
    public let minimumFreePercent:Double?
    public let pressureBeforeLevel:Int?
    public let pressureAfterLevel:Int?
    public let peakPressureLevel:Int?
}

public struct PodcastQualificationDelivery:Equatable {
    public let formatName:String?
    public let videoCodec:String?
    public let audioCodec:String?
    public let audioDurationSeconds:Double?
    public let durationSeconds:Double?
    public let width:Int?
    public let height:Int?
    public let frameRate:String?
    public let frameCount:Int?
    public let sizeBytes:Int?
}

public struct PodcastQualificationDecode:Equatable {
    public let status:String
    public let exitCode:Int?
    public let tail:String
}

public struct PodcastQualificationInterruption:Equatable {
    public let status:String
    public let recoveryStatus:String
    public init(status:String,recoveryStatus:String) {self.status=status;self.recoveryStatus=recoveryStatus}
    public var recoveryLabel:String {
        switch recoveryStatus {
        case "child_process_terminated":return "Launched child process terminated and reaped"
        case "child_process_termination_failed":return "Child-process cleanup was attempted but termination could not be verified"
        case "not_needed":return "No live child required cleanup"
        case "not_exercised":return "No interruption cleanup was exercised"
        default:return "Unsupported recovery state"
        }
    }
}

public struct PodcastQualificationReviews:Equatable {
    public let technicalValidation:String
    public let visualInspection:String
    public let normalSpeedListening:String
    public let ownerAcceptance:String
    public let creativeAcceptance:Bool
}

public struct PodcastQualificationSafety:Equatable {
    public let networkUsed:Bool
    public let publicationUsed:Bool
    public let modelsUsed:Bool
}

public struct PodcastQualificationFailure:Equatable {
    public let type:String
    public let message:String
}

public struct PodcastQualificationAttempt:Equatable,Identifiable {
    public var id:String {attemptID}
    public let attemptID:String
    public let status:PodcastQualificationStatus
    public let startedAt:String
    public let finishedAt:String?
    public let qualityActionID:String?
    public let platform:String
    public let bindings:PodcastQualificationBindings
    public let cacheSummary:String
    public let performance:PodcastQualificationPerformance
    public let delivery:PodcastQualificationDelivery
    public let decode:PodcastQualificationDecode
    public let interruption:PodcastQualificationInterruption
    public let reviews:PodcastQualificationReviews
    public let safety:PodcastQualificationSafety
    public let failure:PodcastQualificationFailure?
    public let preservationSummary:String

    public var isComplete:Bool {false}
    public var summary:String {
        switch status {
        case .succeeded:return "Saved technical long-form evidence succeeded at run time; human review pending."
        case .failed:return "Qualification failed; inspect the recorded failure and preservation state."
        case .interrupted:return "Qualification was interrupted; inspect the recorded recovery and preservation state."
        }
    }

    public static func decode(_ data:Data) throws -> PodcastQualificationAttempt {
        let root=try QualificationJSON.object(data)
        guard root["schema_version"] as? Int == 1 else {throw PodcastQualificationError("Unsupported podcast qualification report schema version.")}
        guard let status=PodcastQualificationStatus(rawValue:try QualificationJSON.text(root["status"],name:"qualification status")) else {
            throw PodcastQualificationError("Unsupported podcast qualification status.")
        }
        guard let platform=root["platform"] as? [String:Any],let cache=root["cache"] as? [String:Any],
              let interruption=root["interruption"] as? [String:Any],let reviews=root["reviews"] as? [String:Any],
              let safety=root["safety"] as? [String:Any],let preservation=root["preservation"] as? [String:Any] else {
            throw PodcastQualificationError("Qualification report is missing required evidence sections.")
        }
        let finishedAt=try QualificationJSON.text(root["finished_at"],name:"qualification finish time")
        let qualityActionID=try QualificationJSON.text(root["quality_action_id"],name:"production-quality action ID")
        let bindings=root["bindings"] as? [String:Any] ?? [:]
        let source=bindings["source"] as? [String:Any] ?? [:]
        let contract=bindings["contract"] as? [String:Any] ?? [:]
        let output=bindings["output"] as? [String:Any] ?? [:]
        let target=bindings["qualification_target"] as? [String:Any]
        let performance=root["performance"] as? [String:Any] ?? [:]
        let pressure=performance["memory_pressure"] as? [String:Any] ?? [:]
        let delivery=root["delivery"] as? [String:Any] ?? [:]
        let decode=root["decode"] as? [String:Any] ?? [:]
        let failure:PodcastQualificationFailure?
        if let value=root["failure"] as? [String:Any] {
            failure=PodcastQualificationFailure(
                type:try QualificationJSON.text(value["type"],name:"failure type"),
                message:try QualificationJSON.text(value["message"],name:"failure message")
            )
        } else {failure=nil}
        let parsedReviews=PodcastQualificationReviews(
            technicalValidation:QualificationJSON.status(reviews["technical_validation"],fallback:"pending"),
            visualInspection:QualificationJSON.status(reviews["visual_inspection"],fallback:"pending"),
            normalSpeedListening:QualificationJSON.status(reviews["normal_speed_listening"],fallback:"pending"),
            ownerAcceptance:QualificationJSON.status(reviews["owner_acceptance"],fallback:"pending"),
            creativeAcceptance:QualificationJSON.boolean(reviews["creative_acceptance"]) == true
        )
        guard ["passed","failed"].contains(parsedReviews.technicalValidation),parsedReviews.visualInspection == "pending",
              parsedReviews.normalSpeedListening == "pending",parsedReviews.ownerAcceptance == "pending",!parsedReviews.creativeAcceptance else {
            throw PodcastQualificationError("Version 1 qualification reports cannot record visual, listening, owner, or creative acceptance (technical \(parsedReviews.technicalValidation), visual \(parsedReviews.visualInspection), listening \(parsedReviews.normalSpeedListening), owner \(parsedReviews.ownerAcceptance), creative \(parsedReviews.creativeAcceptance)).")
        }
        let parsedSafety=PodcastQualificationSafety(
            networkUsed:QualificationJSON.boolean(safety["network_invoked"]) == true,
            publicationUsed:QualificationJSON.boolean(safety["publication_invoked"]) == true,
            modelsUsed:QualificationJSON.boolean(safety["models_invoked"]) == true
        )
        guard !parsedSafety.networkUsed,!parsedSafety.publicationUsed,!parsedSafety.modelsUsed else {
            throw PodcastQualificationError("Version 1 qualification reports cannot claim network, publication, or model activity.")
        }
        guard QualificationJSON.boolean(safety["network_invoked"]) == false,
              QualificationJSON.boolean(safety["publication_invoked"]) == false,
              QualificationJSON.boolean(safety["models_invoked"]) == false,
              QualificationJSON.boolean(preservation["prior_output_preserved"]) != nil,
              QualificationJSON.boolean(preservation["prior_report_preserved"]) != nil else {
            throw PodcastQualificationError("Qualification safety and preservation fields must be explicitly recorded.")
        }
        let interruptionStatus=QualificationJSON.status(interruption["status"],fallback:"")
        let recoveryStatus=QualificationJSON.status(interruption["recovery"],fallback:"")
        guard ["not_interrupted","interrupted","timeout"].contains(interruptionStatus),
              ["not_exercised","not_needed","child_process_terminated","child_process_termination_failed"].contains(recoveryStatus) else {
            throw PodcastQualificationError("Qualification interruption and recovery status must be explicitly recorded.")
        }
        if status == .succeeded {
            guard root["bindings"] is [String:Any],root["performance"] is [String:Any],root["delivery"] is [String:Any],
                  root["decode"] is [String:Any],QualificationJSON.boolean(bindings["reviewed_stage_current"]) == true,
                  QualificationJSON.status(decode["status"],fallback:"") == "passed",QualificationJSON.integer(decode["exit_code"]) == 0,
                  QualificationJSON.validFile(source),QualificationJSON.validFile(contract),QualificationJSON.validFile(output),
                  QualificationJSON.validSHA256(bindings["visual_score_revision_id"]),
                  QualificationJSON.double(performance["wall_time_seconds"]).map({$0 >= 0}) == true,
                  QualificationJSON.integer(performance["rss_sample_count"]).map({$0 >= 0}) == true,
                  QualificationJSON.optionalText(delivery["format_name"]) != nil,
                  QualificationJSON.integer(delivery["size_bytes"]).map({$0 > 0}) == true,
                  parsedReviews.technicalValidation == "passed",failure == nil else {
                throw PodcastQualificationError("A successful qualification report requires current technical evidence.")
            }
            try QualificationJSON.validateLongFormTarget(target,delivery:delivery)
        } else if failure == nil || parsedReviews.technicalValidation != "failed" {
            throw PodcastQualificationError("Failed or interrupted qualification attempts require a technical failure record.")
        }
        return PodcastQualificationAttempt(
            attemptID:try QualificationJSON.text(root["attempt_id"],name:"qualification attempt ID"),status:status,
            startedAt:try QualificationJSON.text(root["started_at"],name:"qualification start time"),
            finishedAt:finishedAt,qualityActionID:qualityActionID,
            platform:QualificationJSON.summary(platform),
            bindings:PodcastQualificationBindings(
                sourcePath:QualificationJSON.optionalText(source["path"]),sourceSHA256:QualificationJSON.optionalText(source["sha256"]),
                contractPath:QualificationJSON.optionalText(contract["path"]),outputPath:QualificationJSON.optionalText(output["path"]),
                outputSHA256:QualificationJSON.optionalText(output["sha256"]),visualScoreRevisionID:QualificationJSON.optionalText(bindings["visual_score_revision_id"]),
                reviewedStageCurrent:QualificationJSON.boolean(bindings["reviewed_stage_current"]) == true,
                target:QualificationJSON.target(target)
            ),
            cacheSummary:QualificationJSON.summary(cache),
            performance:PodcastQualificationPerformance(
                wallSeconds:QualificationJSON.double(performance["wall_time_seconds"]),peakRSSBytes:QualificationJSON.integer(performance["peak_child_tree_rss_bytes"]),
                sampleCount:QualificationJSON.integer(performance["rss_sample_count"]),pressureBeforePercent:QualificationJSON.double(pressure["before_free_percent"]),
                pressureAfterPercent:QualificationJSON.double(pressure["after_free_percent"]),minimumFreePercent:QualificationJSON.double(pressure["minimum_free_percent"]),
                pressureBeforeLevel:QualificationJSON.integer(pressure["before_level"]),pressureAfterLevel:QualificationJSON.integer(pressure["after_level"]),
                peakPressureLevel:QualificationJSON.integer(pressure["peak_level"])
            ),
            delivery:PodcastQualificationDelivery(
                formatName:QualificationJSON.optionalText(delivery["format_name"]),videoCodec:QualificationJSON.stream(delivery,type:"video")?["codec"] as? String,
                audioCodec:QualificationJSON.stream(delivery,type:"audio")?["codec"] as? String,
                audioDurationSeconds:QualificationJSON.double(QualificationJSON.stream(delivery,type:"audio")?["duration_ms"]).map {$0/1000},
                durationSeconds:QualificationJSON.double(delivery["duration_ms"]).map {$0/1000},
                width:QualificationJSON.integer(QualificationJSON.stream(delivery,type:"video")?["width"]),
                height:QualificationJSON.integer(QualificationJSON.stream(delivery,type:"video")?["height"]),
                frameRate:QualificationJSON.optionalText(QualificationJSON.stream(delivery,type:"video")?["avg_frame_rate"]),
                frameCount:QualificationJSON.integer(QualificationJSON.stream(delivery,type:"video")?["frame_count"]),sizeBytes:QualificationJSON.integer(delivery["size_bytes"])
            ),
            decode:PodcastQualificationDecode(
                status:QualificationJSON.status(decode["status"],fallback:"not recorded"),exitCode:QualificationJSON.integer(decode["exit_code"]),
                tail:decode["stderr_tail"] as? String ?? ""
            ),
            interruption:PodcastQualificationInterruption(
                status:interruptionStatus,recoveryStatus:recoveryStatus
            ),
            reviews:parsedReviews,safety:parsedSafety,failure:failure,preservationSummary:QualificationJSON.summary(preservation)
        )
    }
}

public struct PodcastQualificationSnapshot:Equatable {
    public let report:PodcastQualificationAttempt?
    public let attempts:[PodcastQualificationAttempt]
    public var availability:String {report == nil ? "No successful long-form qualification report is available." : "A qualification report is available."}

    public static func load(projectPath:String) throws -> PodcastQualificationSnapshot {
        let root=URL(fileURLWithPath:projectPath,isDirectory:true).appendingPathComponent("work/podcast/qualification",isDirectory:true)
        let reportURL=root.appendingPathComponent("report.json")
        let report:PodcastQualificationAttempt?
        if FileManager.default.fileExists(atPath:reportURL.path) {
            let value=try PodcastQualificationAttempt.decode(Data(contentsOf:reportURL))
            guard value.status == .succeeded else {throw PodcastQualificationError("The canonical qualification report is not a successful attempt.")}
            report=value
        } else {report=nil}
        let attemptsURL=root.appendingPathComponent("attempts",isDirectory:true)
        let urls=(try? FileManager.default.contentsOfDirectory(at:attemptsURL,includingPropertiesForKeys:nil)) ?? []
        let attempts=try urls.filter {$0.pathExtension == "json"}.map {try PodcastQualificationAttempt.decode(Data(contentsOf:$0))}
            .sorted {$0.startedAt > $1.startedAt}
        return PodcastQualificationSnapshot(report:report,attempts:attempts)
    }
}

public struct PodcastQualificationError:LocalizedError {
    public let errorDescription:String?
    public init(_ message:String) {errorDescription=message}
}

public enum PodcastQualificationStaleReason:String,Equatable {
    case reportMissing="report_missing"
    case reportInvalid="report_invalid"
    case reportNotSucceeded="report_not_succeeded"
    case reviewedStageStale="reviewed_stage_stale"
    case sourceChanged="source_changed"
    case contractChanged="contract_changed"
    case visualScoreChanged="visual_score_changed"
    case qualificationTargetChanged="qualification_target_changed"
    case outputMissing="output_missing"
    case outputChanged="output_changed"

    public var label:String {
        switch self {
        case .reportMissing:return "Successful qualification report is missing"
        case .reportInvalid:return "Qualification report is invalid"
        case .reportNotSucceeded:return "Saved report is not a successful run"
        case .reviewedStageStale:return "Reviewed podcast stage is stale"
        case .sourceChanged:return "Source audio changed"
        case .contractChanged:return "Reviewed-stage contract changed"
        case .visualScoreChanged:return "Visual-score revision changed"
        case .qualificationTargetChanged:return "Long-form qualification target changed"
        case .outputMissing:return "Qualified output is missing"
        case .outputChanged:return "Qualified output changed"
        }
    }
}

public struct PodcastQualificationLiveStatus:Equatable {
    public let current:Bool
    public let reasons:[String]
    public let reportAttemptID:String?
    public let reportVisualScoreRevisionID:String?

    public static func decode(_ root:[String:Any]) throws ->PodcastQualificationLiveStatus {
        guard root["schema_version"] as? Int == 1,let current=QualificationJSON.boolean(root["current"]),
              let rawReasons=root["reasons"] as? [String],rawReasons.count <= 10 else {
            throw PodcastQualificationError("Qualification live status has an unsupported response shape.")
        }
        let reasons=try rawReasons.map {raw ->String in
            guard PodcastQualificationStaleReason(rawValue:raw) != nil else {
                throw PodcastQualificationError("Qualification live status has an unsupported stale reason.")
            }
            return raw
        }
        guard Set(reasons).count == reasons.count,!current || reasons.isEmpty,!(!current && reasons.isEmpty) else {
            throw PodcastQualificationError("Qualification live status is internally inconsistent.")
        }
        return PodcastQualificationLiveStatus(
            current:current,reasons:reasons,reportAttemptID:QualificationJSON.optionalText(root["report_attempt_id"]),
            reportVisualScoreRevisionID:QualificationJSON.optionalText(root["report_visual_score_revision_id"])
        )
    }
}

public struct PodcastQualificationPresentation:Equatable {
    public let isCurrent:Bool
    public let headline:String
    public let detail:String

    public init(report:PodcastQualificationAttempt,live:PodcastQualificationLiveStatus?,verificationError:String?) {
        let sameAttempt=live?.reportAttemptID == report.attemptID
        let sameRevision=live?.reportVisualScoreRevisionID == report.bindings.visualScoreRevisionID
        if live?.current == true,sameAttempt,sameRevision {
            isCurrent=true
            headline="Current technical long-form qualification"
            detail="Backend revalidation confirms the saved report still matches the current source, reviewed stage, visual score, target, and output. Human reviews remain pending."
        } else {
            isCurrent=false
            headline="Saved at-run evidence — current status not established"
            if let verificationError {
                detail="Live backend revalidation failed: \(verificationError)"
            } else if let live,live.current {
                detail="Live status applies to a different saved report or visual-score revision."
            } else if let live {
                detail=live.reasons.compactMap {PodcastQualificationStaleReason(rawValue:$0)?.label}.joined(separator:" · ")
            } else {
                detail="Live backend revalidation is pending."
            }
        }
    }
}

private enum QualificationJSON {
    static func object(_ data:Data) throws -> [String:Any] {
        guard let root=try JSONSerialization.jsonObject(with:data) as? [String:Any] else {throw PodcastQualificationError("Podcast qualification artifact must be a JSON object.")}
        return root
    }
    static func text(_ value:Any?,name:String) throws -> String {
        guard let text=optionalText(value) else {throw PodcastQualificationError("Missing \(name).")}
        return text
    }
    static func optionalText(_ value:Any?)->String? {
        guard let text=value as? String else{return nil}
        let trimmed=text.trimmingCharacters(in:.whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
    static func status(_ value:Any?,fallback:String)->String {
        if let text=optionalText(value) {return text}
        if let object=value as? [String:Any],let text=optionalText(object["status"]) {return text}
        return fallback
    }
    static func double(_ value:Any?)->Double? {
        guard let number=value as? NSNumber,CFGetTypeID(number) != CFBooleanGetTypeID(),number.doubleValue.isFinite else{return nil}
        return number.doubleValue
    }
    static func integer(_ value:Any?)->Int? {
        guard let value=double(value),value.rounded() == value else{return nil}
        return Int(exactly:value)
    }
    static func boolean(_ value:Any?)->Bool? {
        guard let number=value as? NSNumber,CFGetTypeID(number) == CFBooleanGetTypeID() else{return nil}
        return number.boolValue
    }
    static func validSHA256(_ value:Any?)->Bool {
        guard let text=optionalText(value),text.count == 64 else{return false}
        return text.allSatisfy {("0"..."9").contains(String($0)) || ("a"..."f").contains(String($0))}
    }
    static func validFile(_ object:[String:Any])->Bool {
        optionalText(object["path"]) != nil && validSHA256(object["sha256"])
    }
    static func summary(_ value:Any?)->String {
        guard let value,JSONSerialization.isValidJSONObject(value),let data=try? JSONSerialization.data(withJSONObject:value,options:[.sortedKeys]),
              let text=String(data:data,encoding:.utf8) else{return "Not recorded"}
        return text
    }
    static func stream(_ delivery:[String:Any],type:String)->[String:Any]? {
        (delivery["streams"] as? [[String:Any]])?.first {$0["type"] as? String == type}
    }
    static func target(_ object:[String:Any]?)->PodcastQualificationTarget? {
        guard let object,let duration=integer(object["duration_ms"]),let fps=double(object["fps"]),
              let width=integer(object["width"]),let height=integer(object["height"]),
              let frames=integer(object["expected_frame_count"]),let durationTolerance=integer(object["duration_tolerance_ms"]),
              let audioDurationTolerance=integer(object["audio_duration_tolerance_ms"]),
              let frameTolerance=integer(object["frame_count_tolerance"]),let fpsTolerance=double(object["fps_tolerance"]) else{return nil}
        return PodcastQualificationTarget(durationMS:duration,fps:fps,width:width,height:height,expectedFrameCount:frames,
                                          durationToleranceMS:durationTolerance,audioDurationToleranceMS:audioDurationTolerance,
                                          frameCountTolerance:frameTolerance,fpsTolerance:fpsTolerance)
    }
    static func validateLongFormTarget(_ object:[String:Any]?,delivery:[String:Any]) throws {
        guard let target=target(object),target.durationMS >= 1_500_000,target.durationMS <= 2_700_000,
              target.fps == 30,target.width == 1920,target.height == 1080,target.durationToleranceMS == 40,target.audioDurationToleranceMS == 100,
              target.frameCountTolerance == 1,target.fpsTolerance == 0.001 else {
            throw PodcastQualificationError("A successful technical long-form qualification requires the recorded 25–45 minute 1080p30 target.")
        }
        let expected=Int(ceil(Double(target.durationMS)*target.fps/1000))
        let streams=delivery["streams"] as? [[String:Any]] ?? []
        let videos=streams.filter {$0["type"] as? String == "video"}
        let audios=streams.filter {$0["type"] as? String == "audio"}
        guard target.expectedFrameCount == expected,streams.count == 2,videos.count == 1,audios.count == 1,let video=videos.first,let audio=audios.first,
              let duration=integer(delivery["duration_ms"]),abs(Double(duration)-Double(target.durationMS)) <= Double(target.durationToleranceMS),
              let audioDuration=integer(audio["duration_ms"]),
              abs(Double(audioDuration)-Double(target.durationMS)) <= Double(target.audioDurationToleranceMS),
              abs(Double(audioDuration)-Double(duration)) <= Double(target.audioDurationToleranceMS),
              integer(video["width"]) == target.width,integer(video["height"]) == target.height,
              let rate=frameRate(video["avg_frame_rate"]),abs(rate-target.fps) <= target.fpsTolerance,
              let frames=integer(video["frame_count"]),abs(Double(frames)-Double(target.expectedFrameCount)) <= Double(target.frameCountTolerance),
              abs(Double(audioDuration)-(Double(frames)/rate*1000)) <= Double(target.audioDurationToleranceMS) else {
            throw PodcastQualificationError("Successful long-form qualification delivery does not agree with its recorded duration, dimensions, frame rate, or frame count target.")
        }
    }
    static func frameRate(_ value:Any?)->Double? {
        guard let text=optionalText(value) else{return nil}
        let pieces=text.split(separator:"/",omittingEmptySubsequences:false)
        if pieces.count == 1 {return Double(pieces[0]).flatMap {$0.isFinite ? $0 : nil}}
        guard pieces.count == 2,let numerator=Double(pieces[0]),let denominator=Double(pieces[1]),denominator != 0 else{return nil}
        let value=numerator/denominator
        return value.isFinite ? value : nil
    }
}
