import Foundation
import StudioCore
// Bounded opt-in live integration check; no media, files, or tools requested.
Task { @MainActor in
    let client=CodexClient()
    do {
        try await client.connect(binary:"/Applications/ChatGPT.app/Contents/Resources/codex")
        print("Connection: \(client.accountLabel)")
        guard client.subscription else {throw StudioError("ChatGPT sign-in required")}
        let root=FileManager.default.currentDirectoryPath
        let models=ProcessInfo.processInfo.arguments.contains("--account-only") ? [] : ["gpt-6-astra","gpt-5.6-sol"]
        for model in models {
            let id=try await client.send(text:"This is a bounded Codex Media Studio subscription integration test. Do not use tools, read files, change files, or produce media. Reply with exactly STUDIO_SUBSCRIPTION_OK.",engine:root,project:root,model:model,readOnly:true)
            let deadline=Date().addingTimeInterval(120)
            while client.running && Date()<deadline {try await Task.sleep(nanoseconds:200_000_000)}
            guard !client.running else {try? await client.interrupt();throw StudioError("Model probe timed out")}
            if let error=client.lastError {throw StudioError(error)}
            guard client.lastAgentResponse.trimmingCharacters(in:.whitespacesAndNewlines)=="STUDIO_SUBSCRIPTION_OK" else {throw StudioError("Model response missing")}
            print("\(model): completed task \(id)")
        }
        client.disconnect();exit(0)
    } catch {print("Probe failed: \(error.localizedDescription)");client.disconnect();exit(1)}
}
RunLoop.main.run()
