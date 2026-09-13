import Foundation

public struct EditingStyleRule:Codable,Equatable,Identifiable {
    public let id:String
    public var enabled:Bool
    public var text:String

    public init(id:String,enabled:Bool,text:String) {
        self.id=id;self.enabled=enabled;self.text=text
    }
}

public struct EditingStyleProfile:Codable,Equatable,Identifiable {
    public let id:String
    public var name:String
    public let sourceMasterSHA256:String
    public var rules:[EditingStyleRule]

    enum CodingKeys:String,CodingKey {
        case id,name,rules
        case sourceMasterSHA256="source_master_sha256"
    }

    public func savePayload(name:String?=nil,expectedRevision:Int?=nil)->[String:Any] {
        var payload:[String:Any]=[
            "style_id":id,
            "name":name ?? self.name,
            "rules":rules.map {["id":$0.id,"enabled":$0.enabled,"text":$0.text]},
        ]
        if let expectedRevision {payload["expected_revision"]=expectedRevision}
        return payload
    }
}

public struct EditingStyleConfiguration:Codable,Equatable {
    public let schemaVersion:Int
    public let selectedStyleID:String
    public let revision:Int
    public let styles:[EditingStyleProfile]
    public let masterChanged:Bool
    public let materialized:Bool
    public let sha256:String

    enum CodingKeys:String,CodingKey {
        case styles,revision,materialized,sha256
        case schemaVersion="schema_version"
        case selectedStyleID="selected_style_id"
        case masterChanged="master_changed"
    }

    public var selectedStyle:EditingStyleProfile? {styles.first {$0.id == selectedStyleID}}

    public static func parse(_ raw:[String:Any]) throws -> Self {
        let data=try JSONSerialization.data(withJSONObject:raw)
        let result=try JSONDecoder().decode(Self.self,from:data)
        guard result.schemaVersion == 1,
              result.revision >= 0,
              !result.styles.isEmpty,
              result.selectedStyle != nil,
              result.sha256.range(of:"^[0-9a-f]{64}$",options:.regularExpression) != nil,
              Set(result.styles.map(\.id)).count == result.styles.count,
              Set(result.styles.map {$0.name.lowercased()}).count == result.styles.count
        else {throw StudioError("Invalid editing-style state")}
        for style in result.styles {
            guard !style.name.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty,
                  style.sourceMasterSHA256.range(of:"^[0-9a-f]{64}$",options:.regularExpression) != nil,
                  !style.rules.isEmpty,
                  Set(style.rules.map(\.id)).count == style.rules.count,
                  style.rules.allSatisfy({!$0.text.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty})
            else {throw StudioError("Invalid editing-style rule state")}
        }
        return result
    }
}
