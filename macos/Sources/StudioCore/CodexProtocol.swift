import Foundation
public enum CodexProtocol {
    public static let arguments = ["-c", "forced_login_method=\"chatgpt\"", "-c", "model_provider=\"openai\"", "app-server", "--listen", "stdio://"]
    public static func canRun(account: [String: Any]?) -> Bool { account?["type"] as? String == "chatgpt" }
    public static func environment(_ input: [String:String]) -> [String:String] {
        input.filter { !$0.key.uppercased().contains("API_KEY") && !["OPENAI_BASE_URL", "OPENAI_API_BASE", "OPENAI_AUTH_TOKEN"].contains($0.key) }
    }
    public static func approvalResult(method: String, allow: Bool) -> [String:Any]? {
        switch method {
        case "item/commandExecution/requestApproval", "item/fileChange/requestApproval": return ["decision":allow ? "accept" : "decline"]
        default: return nil
        }
    }
}
public final class JSONLines {
    private var buffer = Data()
    public init() {}
    public func append(_ data: Data) throws -> [[String:Any]] {
        buffer.append(data)
        guard buffer.count < 32 * 1024 * 1024 else { throw StudioError("Codex message exceeded 32 MiB") }
        var messages = [[String:Any]]()
        while let index = buffer.firstIndex(of: 10) {
            let line = buffer[..<index]; buffer.removeSubrange(...index)
            if line.isEmpty { continue }
            guard let value = try JSONSerialization.jsonObject(with: line) as? [String:Any] else { throw StudioError("Expected a JSON object") }
            messages.append(value)
        }
        return messages
    }
}
public struct StudioError: LocalizedError {
    public let message: String
    public let uncertain: Bool
    public init(_ message: String, uncertain: Bool = false) { self.message = message; self.uncertain = uncertain }
    public var errorDescription: String? { message }
}
public func prettyJSON(_ value: Any) -> String {
    guard JSONSerialization.isValidJSONObject(value), let data = try? JSONSerialization.data(withJSONObject:value, options:[.prettyPrinted,.sortedKeys]), let text = String(data:data,encoding:.utf8) else { return String(describing:value) }
    return text
}
