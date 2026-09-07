import Foundation

public enum PodcastVisualDensity:String,CaseIterable,Equatable {
    case restrained,balanced,illustrative
    public var label:String {rawValue.capitalized}
}

public struct PodcastConfiguration:Equatable {
    public let primaryAudioAssetID:String
    public let cameraAssetID:String?
    public let visualDensity:PodcastVisualDensity
    public init(primaryAudioAssetID:String,cameraAssetID:String?,visualDensity:PodcastVisualDensity) {
        self.primaryAudioAssetID=primaryAudioAssetID
        self.cameraAssetID=cameraAssetID
        self.visualDensity=visualDensity
    }
    public static func from(project:[String:Any]) throws -> PodcastConfiguration? {
        guard let value=project["podcast"],!(value is NSNull) else{return nil}
        guard let record=value as? [String:Any],record["schema_version"] as? Int == 1,
              record["kind"] as? String == "solo_audio_first" else {
            throw PodcastConfigurationError("Unsupported podcast settings in this project.")
        }
        let primary=try requiredText(record["primary_audio_asset_id"],name:"primary audio asset")
        let camera:String?
        if record["camera_asset_id"] == nil || record["camera_asset_id"] is NSNull {camera=nil}
        else {camera=try requiredText(record["camera_asset_id"],name:"camera asset")}
        let densityText=record["visual_density"] as? String ?? PodcastVisualDensity.balanced.rawValue
        guard let density=PodcastVisualDensity(rawValue:densityText) else {
            throw PodcastConfigurationError("Unsupported podcast visual density: \(densityText)")
        }
        return PodcastConfiguration(primaryAudioAssetID:primary,cameraAssetID:camera,visualDensity:density)
    }
    public func patchPayload() throws -> [String:Any] {
        let primary=try Self.requiredText(primaryAudioAssetID,name:"primary audio asset")
        let camera:Any
        if let cameraAssetID {camera=try Self.requiredText(cameraAssetID,name:"camera asset")}
        else {camera=NSNull()}
        return ["primary_audio_asset_id":primary,"camera_asset_id":camera,"visual_density":visualDensity.rawValue]
    }
    fileprivate static func requiredText(_ value:Any?,name:String) throws -> String {
        guard let text=value as? String,!text.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else {
            throw PodcastConfigurationError("Podcast \(name) must be selected.")
        }
        return text
    }
}

public struct PodcastMediaOption:Equatable,Identifiable {
    public let id:String
    public let label:String
    public let streamTypes:Set<String>?
    public var needsCapabilityValidation:Bool {streamTypes == nil}
    public var canBePrimaryAudio:Bool {streamTypes?.contains("audio") ?? true}
    public var canBeCamera:Bool {streamTypes?.contains("video") ?? true}

    public static func options(from records:[[String:Any]]) throws -> [PodcastMediaOption] {
        try records.compactMap {record in
            if record["role"] as? String == "document" || record["role"] as? String == "revision" {return nil}
            let id=try PodcastConfiguration.requiredText(record["id"],name:"media ID")
            let label=try PodcastConfiguration.requiredText(record["label"],name:"media label")
            let streams:Set<String>?
            if let raw=record["stream_types"] {
                guard let values=raw as? [String],!values.isEmpty,
                      values.allSatisfy({$0 == "audio" || $0 == "video"}) else {
                    throw PodcastConfigurationError("Media \(label) has invalid stream metadata.")
                }
                streams=Set(values)
            } else {streams=nil}
            return PodcastMediaOption(id:id,label:label,streamTypes:streams)
        }
    }
}

public enum ReviewMarkerAction:Equatable {
    case markTime(Int)
    case captureFrame(Int)
}

public enum ReviewMarkerDecision {
    public static func action(seconds:Double,hasVideo:Bool)->ReviewMarkerAction? {
        guard seconds.isFinite,seconds >= 0 else{return nil}
        let roundedMilliseconds=(seconds*1000).rounded()
        guard roundedMilliseconds.isFinite,
              let milliseconds=Int(exactly:roundedMilliseconds) else{return nil}
        return hasVideo ? .captureFrame(milliseconds) : .markTime(milliseconds)
    }
}

public struct PodcastConfigurationError:LocalizedError {
    public let errorDescription:String?
    public init(_ message:String) {errorDescription=message}
}
