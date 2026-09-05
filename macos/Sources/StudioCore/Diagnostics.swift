import Foundation
import Darwin

/// Local diagnostics only. Callers supply operation labels, never prompts or credentials.
public final class Diagnostics: @unchecked Sendable {
    public static let shared = try? Diagnostics(directory:FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Library/Logs/Codex Studio"))
    public let directory:URL
    private let handle:FileHandle
    private let lock=NSLock()
    private let id=UUID().uuidString
    public init(directory:URL) throws {
        self.directory=directory
        let fm=FileManager.default
        try fm.createDirectory(at:directory,withIntermediateDirectories:true,attributes:[.posixPermissions:0o700])
        let files=try fm.contentsOfDirectory(at:directory,includingPropertiesForKeys:[.contentModificationDateKey])
            .filter{["jsonl","stderr","ips"].contains($0.pathExtension)}
            .sorted{((try? $0.resourceValues(forKeys:[.contentModificationDateKey]).contentModificationDate) ?? .distantPast) > ((try? $1.resourceValues(forKeys:[.contentModificationDateKey]).contentModificationDate) ?? .distantPast)}
        for file in files.dropFirst(40) {try? fm.removeItem(at:file)}
        let url=directory.appendingPathComponent("session-\(id).jsonl")
        guard fm.createFile(atPath:url.path,contents:nil,attributes:[.posixPermissions:0o600]) else {throw CocoaError(.fileWriteUnknown)}
        handle=try FileHandle(forWritingTo:url)
        record("session_started",detail:"pid=\(ProcessInfo.processInfo.processIdentifier) os=\(ProcessInfo.processInfo.operatingSystemVersionString)")
    }
    public func record(_ event:String,detail:String="") {
        lock.lock();defer{lock.unlock()}
        let entry=["time":ISO8601DateFormatter().string(from:Date()),"event":event,"detail":detail]
        if var data=try? JSONSerialization.data(withJSONObject:entry,options:[.sortedKeys]) {
            data.append(10);try? handle.write(contentsOf:data);try? handle.synchronize()
        }
    }
    public func captureRuntimeErrors() {
        let path=directory.appendingPathComponent("session-\(id).stderr").path
        let fd=Darwin.open(path,O_WRONLY|O_CREAT|O_APPEND,0o600)
        if fd >= 0 {dup2(fd,STDERR_FILENO);Darwin.close(fd)}
        else {record("stderr_capture_failed")}
    }
    public func importCrashReports(from source:URL) {
        let fm=FileManager.default
        let files=((try? fm.contentsOfDirectory(at:source,includingPropertiesForKeys:nil)) ?? [])
            .filter{$0.lastPathComponent.hasPrefix("CodexStudio-") && $0.pathExtension == "ips"}.sorted{$0.lastPathComponent > $1.lastPathComponent}.prefix(10)
        for file in files {
            let target=directory.appendingPathComponent(file.lastPathComponent)
            if !fm.fileExists(atPath:target.path) {
                do {try fm.copyItem(at:file,to:target);try fm.setAttributes([.posixPermissions:0o600],ofItemAtPath:target.path);record("crash_report_imported",detail:file.lastPathComponent)}
                catch {record("crash_report_import_failed")}
            }
        }
    }
}
