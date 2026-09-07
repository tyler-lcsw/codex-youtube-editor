import Foundation
import CryptoKit

public struct PodcastEpisodeChapter:Equatable,Identifiable {
    public let id:String
    public let title:String
    public let startMS:Int
    public let endMS:Int
}

public struct PodcastEpisodeMap:Equatable {
    public let durationMS:Int
    public let chapters:[PodcastEpisodeChapter]

    public static func decode(_ data:Data) throws -> PodcastEpisodeMap {
        let root=try PodcastVisualScoreJSON.object(data)
        try PodcastVisualScoreJSON.version(root,name:"episode map")
        guard let rows=root["chapters"] as? [[String:Any]],!rows.isEmpty else {
            throw PodcastVisualScoreError("The episode map has no chapters.")
        }
        var previousEnd=0
        let chapters=try rows.map {row in
            let id=try PodcastVisualScoreJSON.text(row["id"],name:"chapter ID")
            let title=try PodcastVisualScoreJSON.text(row["title"],name:"chapter title")
            let start=try PodcastVisualScoreJSON.integer(row["start_ms"],name:"chapter start")
            let end=try PodcastVisualScoreJSON.integer(row["end_ms"],name:"chapter end")
            guard start >= previousEnd,end > start else {
                throw PodcastVisualScoreError("Episode-map chapters must be ordered and non-overlapping.")
            }
            previousEnd=end
            return PodcastEpisodeChapter(id:id,title:title,startMS:start,endMS:end)
        }
        let primaryAudio=root["primary_audio"] as? [String:Any]
        let duration=(root["duration_ms"] as? Int) ?? (primaryAudio?["duration_ms"] as? Int) ?? chapters.last!.endMS
        guard duration >= chapters.last!.endMS else {
            throw PodcastVisualScoreError("The episode duration ends before its final chapter.")
        }
        return PodcastEpisodeMap(durationMS:duration,chapters:chapters)
    }
}

public struct PodcastVisualPreview:Equatable,Identifiable {
    public var id:String {chapterID+"\u{0}"+path}
    public let chapterID:String
    public let path:String
    public let sha256:String
}

public struct PodcastVisualEvent:Equatable,Identifiable {
    public let id:String
    public let type:String
    public let chapterID:String
    public let startMS:Int
    public let endMS:Int
    public let purpose:String
    public let treatmentSummary:String
    public let provenanceSummary:String
    public let cameraPolicySummary:String
    public let transcriptAnchorSummary:String

    public var isSupported:Bool {
        ["base","chapter_card","quote","progressive_list","comparison","image_source"].contains(type)
    }
    public var typeLabel:String {
        switch type {
        case "base":return "Base stage"
        case "chapter_card":return "Chapter card"
        case "quote":return treatmentSummary.contains("key_point") ? "Key point" : "Quote"
        case "progressive_list":return "Progressive list"
        case "comparison":return "Comparison"
        case "image_source":return "Image or source card"
        default:return "Unsupported proposal: \(type)"
        }
    }
}

public struct PodcastVisualScore:Equatable {
    public let revisionID:String
    public let episodeMapSHA256:String?
    public let visualDensity:PodcastVisualDensity
    public let events:[PodcastVisualEvent]
    public let previews:[PodcastVisualPreview]

    public static func decode(_ data:Data) throws -> PodcastVisualScore {
        let root=try PodcastVisualScoreJSON.object(data)
        try PodcastVisualScoreJSON.version(root,name:"visual score")
        let revision=try PodcastVisualScoreJSON.text(root["revision_id"],name:"score revision")
        guard let density=PodcastVisualDensity(rawValue:root["visual_density"] as? String ?? "") else {
            throw PodcastVisualScoreError("The visual score has an unsupported density.")
        }
        guard let rows=root["visual_events"] as? [[String:Any]] else {
            throw PodcastVisualScoreError("The visual score has no event list.")
        }
        var ids=Set<String>()
        let events=try rows.map {row in
            let id=try PodcastVisualScoreJSON.text(row["id"],name:"visual event ID")
            guard ids.insert(id).inserted else {throw PodcastVisualScoreError("Visual event IDs must be unique.")}
            let type=try PodcastVisualScoreJSON.text(row["type"],name:"visual event type")
            let chapter=try PodcastVisualScoreJSON.text(row["chapter_id"],name:"visual event chapter")
            let start=try PodcastVisualScoreJSON.integer(row["start_ms"],name:"visual event start")
            let end=try PodcastVisualScoreJSON.integer(row["end_ms"],name:"visual event end")
            guard start >= 0,end > start else {throw PodcastVisualScoreError("Visual event ranges must have a positive duration.")}
            return PodcastVisualEvent(
                id:id,type:type,chapterID:chapter,startMS:start,endMS:end,
                purpose:try PodcastVisualScoreJSON.text(row["purpose"],name:"visual event purpose"),
                treatmentSummary:PodcastVisualScoreJSON.summary(row["treatment"]),
                provenanceSummary:PodcastVisualScoreJSON.summary(row["provenance"]),
                cameraPolicySummary:PodcastVisualScoreJSON.summary(row["camera_policy"]),
                transcriptAnchorSummary:PodcastVisualScoreJSON.summary(row["transcript_anchor"])
            )
        }
        let previews=try (root["representative_previews"] as? [[String:Any]] ?? []).map {row in
            let chapter=try PodcastVisualScoreJSON.text(row["chapter_id"],name:"representative preview chapter")
            let path=try PodcastVisualScoreJSON.text(row["path"],name:"representative preview path")
            guard PodcastVisualScoreJSON.isSafeRelativePath(path) else {
                throw PodcastVisualScoreError("Representative preview paths must stay inside the project.")
            }
            let sha256=try PodcastVisualScoreJSON.text(row["sha256"],name:"representative preview SHA-256")
            guard PodcastVisualScoreJSON.isSHA256(sha256) else {
                throw PodcastVisualScoreError("Representative preview SHA-256 is invalid.")
            }
            return PodcastVisualPreview(chapterID:chapter,path:path,sha256:sha256)
        }
        return PodcastVisualScore(
            revisionID:revision,episodeMapSHA256:PodcastVisualScoreJSON.optionalText(root["episode_map_sha256"]),
            visualDensity:density,events:events,previews:previews
        )
    }
}

public enum PodcastVisualDecisionAction:String,Equatable {
    case accept,reject
    case useBase="use_base"
    case requestChanges="request_changes"

    public var label:String {
        switch self {
        case .accept:return "Accepted proposal"
        case .reject:return "Rejected proposal"
        case .useBase:return "Keep base stage"
        case .requestChanges:return "Requested changes"
        }
    }
}

public struct PodcastVisualScoreDecision:Equatable,Identifiable {
    public let id:String
    public let revisionID:String
    public let eventID:String
    public let action:PodcastVisualDecisionAction
    public let note:String
    public let decidedAt:String
}

public struct PodcastVisualScoreDecisionLog:Equatable {
    public let decisions:[PodcastVisualScoreDecision]
    public static func decode(_ data:Data) throws -> PodcastVisualScoreDecisionLog {
        let root=try PodcastVisualScoreJSON.object(data)
        try PodcastVisualScoreJSON.version(root,name:"visual-score decision log")
        guard let rows=root["decisions"] as? [[String:Any]] else {
            throw PodcastVisualScoreError("The visual-score decision log has no decision list.")
        }
        let decisions=try rows.map {row in
            guard row["owner_action"] as? Bool == true else {
                throw PodcastVisualScoreError("A visual-score decision is not recorded as an explicit owner action.")
            }
            guard let action=PodcastVisualDecisionAction(rawValue:row["action"] as? String ?? "") else {
                throw PodcastVisualScoreError("A visual-score decision has an unsupported action.")
            }
            return PodcastVisualScoreDecision(
                id:try PodcastVisualScoreJSON.text(row["id"],name:"decision ID"),
                revisionID:try PodcastVisualScoreJSON.text(row["revision_id"],name:"decision revision"),
                eventID:try PodcastVisualScoreJSON.text(row["event_id"],name:"decision event"),action:action,
                note:row["note"] as? String ?? "",decidedAt:try PodcastVisualScoreJSON.text(row["decided_at"],name:"decision time")
            )
        }
        return PodcastVisualScoreDecisionLog(decisions:decisions)
    }
    public func latest(for eventID:String,revisionID:String)->PodcastVisualScoreDecision? {
        decisions.last {$0.eventID == eventID && $0.revisionID == revisionID}
    }
}

public struct PodcastVisualScoreArtifacts:Equatable {
    public let episodeMap:PodcastEpisodeMap
    public let score:PodcastVisualScore
    public let decisions:PodcastVisualScoreDecisionLog

    public static func load(projectPath:String) throws -> PodcastVisualScoreLoadResult {
        let project=URL(fileURLWithPath:projectPath,isDirectory:true)
        let podcast=project.appendingPathComponent("work/podcast",isDirectory:true)
        let episodeMapURL=podcast.appendingPathComponent("episode-map.json")
        guard FileManager.default.fileExists(atPath:episodeMapURL.path) else {
            return .unavailable("No episode map is available yet. Ask Codex to create the transcript-bound episode map first.")
        }
        let currentURL=podcast.appendingPathComponent("visual-score/current.json")
        guard FileManager.default.fileExists(atPath:currentURL.path) else {
            return .unavailable("No visual-score revision is available yet. Nothing has been proposed for owner review.")
        }
        let pointer=try PodcastVisualScoreJSON.object(Data(contentsOf:currentURL))
        guard let revision=PodcastVisualScoreJSON.optionalText(pointer["revision_id"] ?? pointer["current_revision_id"]),
              PodcastVisualScoreJSON.isSHA256(revision) else {
            throw PodcastVisualScoreError("The current visual-score pointer has no revision ID.")
        }
        let scoreURL=podcast.appendingPathComponent("visual-score/revisions/\(revision).json")
        guard FileManager.default.fileExists(atPath:scoreURL.path) else {
            throw PodcastVisualScoreError("The current visual-score revision file is missing.")
        }
        let episodeMap=try PodcastEpisodeMap.decode(Data(contentsOf:episodeMapURL))
        let score=try PodcastVisualScore.decode(Data(contentsOf:scoreURL))
        guard score.revisionID == revision else {
            throw PodcastVisualScoreError("The visual-score pointer and revision file do not match.")
        }
        let decisionsURL=podcast.appendingPathComponent("visual-score/decisions.json")
        let decisions:PodcastVisualScoreDecisionLog
        if FileManager.default.fileExists(atPath:decisionsURL.path) {
            decisions=try PodcastVisualScoreDecisionLog.decode(Data(contentsOf:decisionsURL))
        } else {decisions=PodcastVisualScoreDecisionLog(decisions:[])}
        return .loaded(PodcastVisualScoreArtifacts(episodeMap:episodeMap,score:score,decisions:decisions))
    }
}

public enum PodcastVisualScoreLoadResult:Equatable {
    case unavailable(String)
    case loaded(PodcastVisualScoreArtifacts)
}

public enum PodcastVisualScoreDecisionPayload {
    public static func build(revisionID:String,eventID:String,action:PodcastVisualDecisionAction,note:String) throws -> [String:Any] {
        let revision=try PodcastVisualScoreJSON.text(revisionID,name:"score revision")
        guard PodcastVisualScoreJSON.isSHA256(revision) else {throw PodcastVisualScoreError("The score revision must be a SHA-256 identifier.")}
        let event=try PodcastVisualScoreJSON.text(eventID,name:"visual event")
        return ["revision_id":revision,"event_id":event,"action":action.rawValue,"note":note.trimmingCharacters(in:.whitespacesAndNewlines),"owner_action":true]
    }
}

public enum PodcastVisualScoreBinding {
    public static func isCurrent(_ state:[String:Any],revisionID:String)->Bool {
        state["binding_current"] as? Bool == true && state["current_revision_id"] as? String == revisionID
    }
}

public enum PodcastVisualPreviewAccess {
    public static func openableURL(_ preview:PodcastVisualPreview,projectPath:String)->URL? {
        guard PodcastVisualScoreJSON.isSafeRelativePath(preview.path),PodcastVisualScoreJSON.isSHA256(preview.sha256) else{return nil}
        let root=URL(fileURLWithPath:projectPath,isDirectory:true).resolvingSymlinksInPath().standardizedFileURL
        let candidate=root.appendingPathComponent(preview.path).resolvingSymlinksInPath().standardizedFileURL
        guard candidate.path.hasPrefix(root.path+"/") else{return nil}
        var isDirectory:ObjCBool=false
        guard FileManager.default.fileExists(atPath:candidate.path,isDirectory:&isDirectory),!isDirectory.boolValue,
              let data=try? Data(contentsOf:candidate) else{return nil}
        let digest=SHA256.hash(data:data).map {String(format:"%02x",$0)}.joined()
        return digest == preview.sha256 ? candidate : nil
    }
}

public struct PodcastVisualScoreError:LocalizedError {
    public let errorDescription:String?
    public init(_ message:String) {errorDescription=message}
}

private enum PodcastVisualScoreJSON {
    static func object(_ data:Data) throws -> [String:Any] {
        guard let root=try JSONSerialization.jsonObject(with:data) as? [String:Any] else {
            throw PodcastVisualScoreError("Podcast review artifact must be a JSON object.")
        }
        return root
    }
    static func version(_ root:[String:Any],name:String) throws {
        guard root["schema_version"] as? Int == 1 else {
            throw PodcastVisualScoreError("Unsupported \(name) schema version.")
        }
    }
    static func text(_ value:Any?,name:String) throws -> String {
        guard let text=optionalText(value) else {throw PodcastVisualScoreError("Missing \(name).")}
        return text
    }
    static func optionalText(_ value:Any?)->String? {
        guard let text=value as? String else{return nil}
        let trimmed=text.trimmingCharacters(in:.whitespacesAndNewlines)
        return trimmed.isEmpty ? nil : trimmed
    }
    static func integer(_ value:Any?,name:String) throws -> Int {
        guard let number=value as? NSNumber,CFGetTypeID(number) != CFBooleanGetTypeID() else {
            throw PodcastVisualScoreError("Missing or invalid \(name).")
        }
        let double=number.doubleValue
        guard double.isFinite,double.rounded() == double,let integer=Int(exactly:double) else {
            throw PodcastVisualScoreError("Missing or invalid \(name).")
        }
        return integer
    }
    static func summary(_ value:Any?)->String {
        if let text=optionalText(value) {return text}
        guard let value,JSONSerialization.isValidJSONObject(value),
              let data=try? JSONSerialization.data(withJSONObject:value,options:[.sortedKeys]),
              let text=String(data:data,encoding:.utf8) else{return "Not specified"}
        return text
    }
    static func isSHA256(_ value:String)->Bool {
        value.count == 64 && value.allSatisfy {("0"..."9").contains($0) || ("a"..."f").contains($0)}
    }
    static func isSafeRelativePath(_ value:String)->Bool {
        guard !value.hasPrefix("/") else{return false}
        let parts=value.split(separator:"/",omittingEmptySubsequences:false)
        return !parts.isEmpty && parts.allSatisfy {!$0.isEmpty && $0 != "." && $0 != ".."}
    }
}
