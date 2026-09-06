import Foundation
import StudioCore
func testDurableDiagnosticsAndCrashRecovery() throws {
    let root=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer {try? FileManager.default.removeItem(at:root)}
    let source=root.appendingPathComponent("reports"),logs=root.appendingPathComponent("logs")
    try FileManager.default.createDirectory(at:source,withIntermediateDirectories:true)
    try Data("crash fixture".utf8).write(to:source.appendingPathComponent("CodexStudio-fixture.ips"))
    try Data("unrelated".utf8).write(to:source.appendingPathComponent("OtherApp-fixture.ips"))
    let logger=try Diagnostics(directory:logs)
    logger.record("tab_selected",detail:"Review")
    logger.importCrashReports(from:source);logger.importCrashReports(from:source)
    logger.record("session_ended")
    let files=try FileManager.default.contentsOfDirectory(at:logs,includingPropertiesForKeys:nil)
    XCTAssertEqual(files.filter{$0.pathExtension == "ips"}.count,1)
    let data=try String(contentsOf:files.first{$0.pathExtension == "jsonl"}!,encoding:.utf8)
    let entries=try data.split(separator:"\n").map{try JSONSerialization.jsonObject(with:Data($0.utf8)) as! [String:String]}
    XCTAssertEqual(entries.map{$0["event"]!},["session_started","tab_selected","crash_report_imported","session_ended"])
    XCTAssertEqual(entries[1]["detail"],"Review")
}
