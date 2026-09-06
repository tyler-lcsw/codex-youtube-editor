import Foundation
public struct EngineBridge {
    public let root: String
    public let python: String
    public init(root: String, python: String) {self.root=root;self.python=python}
    public func request(_ method: String, project: String, params:[String:Any]=[:]) async throws -> [String:Any] {
        Diagnostics.shared?.record("engine_request",detail:method)
        let bytes=try JSONSerialization.data(withJSONObject:["method":method,"project":project,"params":params])
        return try await Task.detached {
            let process=Process();process.executableURL=URL(fileURLWithPath:python)
            process.currentDirectoryURL=URL(fileURLWithPath:root);process.arguments=["-m","tools.studio"]
            var env=ProcessInfo.processInfo.environment
            env["PATH"]="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:"+(env["PATH"] ?? "")
            process.environment=env
            let input=Pipe(),output=Pipe();process.standardInput=input;process.standardOutput=output
            process.standardError=FileHandle.nullDevice
            try process.run();try input.fileHandleForWriting.write(contentsOf:bytes);try input.fileHandleForWriting.close()
            let data=output.fileHandleForReading.readDataToEndOfFile();process.waitUntilExit()
            Diagnostics.shared?.record("engine_exit",detail:"\(method) status=\(process.terminationStatus)")
            guard let response=(try? JSONSerialization.jsonObject(with:data)) as? [String:Any] else {throw StudioError("Engine returned no valid response (exit \(process.terminationStatus)). Check engine and Python paths.")}
            guard response["ok"] as? Bool == true else {throw StudioError(response["error"] as? String ?? "Engine request failed")}
            return response["result"] as? [String:Any] ?? [:]
        }.value
    }
}
