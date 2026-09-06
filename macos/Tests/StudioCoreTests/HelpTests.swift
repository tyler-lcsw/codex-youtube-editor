import Foundation
import StudioCore

private func helpFixture() -> [String:Any] {
    ["schema_version":1,"title":"Studio guide","articles":[
        ["id":"review-basics","section":"Review","title":"Watch output","summary":"Inspect a revision","status":"Available","steps":["Play the video"],"notes":["Check audio"],"prompt":"Please inspect timing"],
        ["id":"resource-basics","section":"Resources","title":"Choose resources","summary":"Select routes","status":"Limited","steps":["Choose a provider"],"notes":["Check readiness"]]
    ]]
}
private func helpData(_ value:[String:Any]) throws -> Data {try JSONSerialization.data(withJSONObject:value)}
func testHelpValidation() throws {
    let fixture=helpFixture()
    XCTAssertEqual(try HelpGuide.decode(helpData(fixture)).articles.count,2)
    for key in ["id","section","title","summary","status"] {
        var bad=fixture;var articles=bad["articles"] as! [[String:Any]];articles[0][key]="  ";bad["articles"]=articles
        XCTAssertThrowsError(try HelpGuide.decode(helpData(bad)))
    }
    for badID in ["Bad-ID","bad_id","-bad","bad--id"] {
        var bad=fixture;var articles=bad["articles"] as! [[String:Any]];articles[0]["id"]=badID;bad["articles"]=articles
        XCTAssertThrowsError(try HelpGuide.decode(helpData(bad)))
    }
    var bad=fixture;bad["schema_version"]=2;XCTAssertThrowsError(try HelpGuide.decode(helpData(bad)))
    bad=fixture;bad["title"]="";XCTAssertThrowsError(try HelpGuide.decode(helpData(bad)))
    bad=fixture;var articles=bad["articles"] as! [[String:Any]];articles.append(articles[0]);bad["articles"]=articles
    XCTAssertThrowsError(try HelpGuide.decode(helpData(bad)))
    for steps in [[],[""]] as [[String]] {
        bad=fixture;articles=bad["articles"] as! [[String:Any]];articles[0]["steps"]=steps;bad["articles"]=articles
        XCTAssertThrowsError(try HelpGuide.decode(helpData(bad)))
    }
    bad=fixture;articles=bad["articles"] as! [[String:Any]];articles[0]["section"]="Unknown section";bad["articles"]=articles
    XCTAssertThrowsError(try HelpGuide.decode(helpData(bad)))
    bad=fixture;articles=bad["articles"] as! [[String:Any]];articles[0].removeValue(forKey:"notes");bad["articles"]=articles
    XCTAssertThrowsError(try HelpGuide.decode(helpData(bad)))
    let decoded=try HelpGuide.decode(helpData(fixture))
    XCTAssertEqual(try HelpGuide.decode(JSONEncoder().encode(decoded)),decoded)
    XCTAssertThrowsError(try HelpGuide.decode(Data("invalid".utf8)))
}
func testHelpSearchAndSection() throws {
    let guide=try HelpGuide.decode(helpData(helpFixture()))
    for query in ["WATCH","revision","available","video","audio","timing","review-basics","Review"] {
        XCTAssertEqual(guide.filtered(section:"Review",query:query).map(\.id),["review-basics"])
    }
    XCTAssertEqual(guide.filtered(section:"Resources",query:"audio").count,0)
    XCTAssertEqual(guide.filtered(section:nil,query:"  ").count,2)
    XCTAssertEqual(guide.filtered(section:nil,query:"readiness").map(\.id),["resource-basics"])
}
func testHelpRepositoryAndFallback() throws {
    let root=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer {try? FileManager.default.removeItem(at:root)}
    try FileManager.default.createDirectory(at:root,withIntermediateDirectories:true)
    let repo=root.appendingPathComponent("repository.json"),bundle=root.appendingPathComponent("bundled.json")
    try helpData(helpFixture()).write(to:bundle)
    let missing=try HelpGuide.load(repositoryURL:repo,bundledURL:bundle)
    XCTAssertEqual(missing.source,.bundled);XCTAssertTrue(missing.fallbackReason != nil)
    try Data("broken".utf8).write(to:repo)
    let invalid=try HelpGuide.load(repositoryURL:repo,bundledURL:bundle)
    XCTAssertEqual(invalid.source,.bundled);XCTAssertTrue(invalid.fallbackReason != nil)
    try helpData(helpFixture()).write(to:repo)
    let preferred=try HelpGuide.load(repositoryURL:repo,bundledURL:bundle)
    XCTAssertEqual(preferred.source,.repository);XCTAssertNil(preferred.fallbackReason)
    try FileManager.default.removeItem(at:repo)
    XCTAssertThrowsError(try HelpGuide.load(repositoryURL:repo,bundledURL:nil))
    try Data("broken".utf8).write(to:bundle)
    XCTAssertThrowsError(try HelpGuide.load(repositoryURL:repo,bundledURL:bundle))
}
