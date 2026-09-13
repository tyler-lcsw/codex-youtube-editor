import Foundation
import StudioCore

func testEditingStyleConfigurationParsesSelectionAndBuildsExactSavePayload() throws {
    let raw:[String:Any] = [
        "schema_version":1,
        "selected_style_id":"style-a",
        "revision":2,
        "master_changed":false,
        "materialized":true,
        "sha256":String(repeating:"b",count:64),
        "styles":[[
            "id":"style-a", "name":"Quiet documentary", "source_master_sha256":String(repeating:"a",count:64),
            "rules":[
                ["id":"R01", "enabled":false, "text":"DO hold the opening."],
                ["id":"R02", "enabled":true, "text":"DO show evidence."],
            ],
        ]],
    ]
    let configuration = try EditingStyleConfiguration.parse(raw)
    let selected = try XCTUnwrap(configuration.selectedStyle)
    XCTAssertEqual(selected.name, "Quiet documentary")
    XCTAssertEqual(selected.rules.first?.enabled, false)

    let payload = selected.savePayload(name:"Measured")
    XCTAssertEqual(payload["style_id"] as? String, "style-a")
    XCTAssertEqual(payload["name"] as? String, "Measured")
    let rules = try XCTUnwrap(payload["rules"] as? [[String:Any]])
    XCTAssertEqual(rules.count, 2)
    XCTAssertEqual(rules[0]["enabled"] as? Bool, false)
}

func testEditingStyleConfigurationRejectsMalformedRuleState() {
    let malformed:[String:Any] = [
        "schema_version":1, "selected_style_id":"style-a", "revision":0, "master_changed":false, "materialized":true, "sha256":String(repeating:"b",count:64),
        "styles":[["id":"style-a", "name":"Broken", "source_master_sha256":"bad", "rules":[["id":"R01", "enabled":"yes", "text":"DO something."]]]],
    ]
    XCTAssertThrowsError(try EditingStyleConfiguration.parse(malformed))
}
