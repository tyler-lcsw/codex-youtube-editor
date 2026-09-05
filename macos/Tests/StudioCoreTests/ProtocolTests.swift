import Foundation
import StudioCore
final class ProtocolTests {
    func testSubscriptionGateRejectsAPIAndMissingAccount() {
        XCTAssertFalse(CodexProtocol.canRun(account: nil))
        XCTAssertFalse(CodexProtocol.canRun(account: ["type": "apiKey"]))
        XCTAssertTrue(CodexProtocol.canRun(account: ["type": "chatgpt"]))
    }
    func testFramerPreservesSplitUnicodeAndMultipleMessages() throws {
        let f = JSONLines(); let bytes = Array("{\"text\":\"é\"}\n{\"id\":2}\n".utf8)
        XCTAssertEqual(try f.append(Data(bytes.prefix(10))).count, 0)
        let result = try f.append(Data(bytes.dropFirst(10)))
        XCTAssertEqual(result[0]["text"] as? String, "é")
        XCTAssertEqual(result[1]["id"] as? Int, 2)
    }
    func testMalformedJSONIsAnErrorRatherThanSilentLoss() {
        XCTAssertThrowsError(try JSONLines().append(Data("broken\n".utf8)))
    }
    func testInheritedAPIKeysAreRemovedAndSubscriptionForced() {
        let env = CodexProtocol.environment(["OPENAI_API_KEY":"secret", "AZURE_OPENAI_API_KEY":"secret", "PATH":"/bin"])
        XCTAssertNil(env["OPENAI_API_KEY"]); XCTAssertNil(env["AZURE_OPENAI_API_KEY"])
        XCTAssertEqual(env["PATH"], "/bin")
        XCTAssertTrue(CodexProtocol.arguments.contains("forced_login_method=\"chatgpt\""))
    }
    func testUnknownApprovalCannotBecomeAnAcceptance() {
        XCTAssertNil(CodexProtocol.approvalResult(method: "unknown", allow: true))
        XCTAssertEqual(CodexProtocol.approvalResult(method: "item/commandExecution/requestApproval", allow: false)?["decision"] as? String, "decline")
    }
}

@MainActor
func testTransportDisconnectResolvesPendingRequests() async throws {
    let path=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString+".py")
    let script="#!/usr/bin/python3\nimport sys\nsys.stdin.readline()\n"
    try script.write(to:path,atomically:true,encoding:.utf8)
    try FileManager.default.setAttributes([.posixPermissions:0o700],ofItemAtPath:path.path)
    defer {try? FileManager.default.removeItem(at:path)}
    let client=CodexClient()
    do {try await client.connect(binary:path.path);fatalError("Disconnected initialize should fail")}
    catch {XCTAssertFalse(client.connected)}
}

@MainActor
func testAccountSwitchToAPIPreventsTurnDispatch() async throws {
    let folder=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    try FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true)
    defer{try? FileManager.default.removeItem(at:folder)}
    let script=folder.appendingPathComponent("server.py"),log=folder.appendingPathComponent("calls.txt")
    try """
    #!/usr/bin/python3
    import sys,json
    reads=0
    for line in sys.stdin:
        msg=json.loads(line);method=msg.get('method','')
        with open(\(String(reflecting:log.path)),'a') as f:f.write(method+'\\n')
        if 'id' not in msg:continue
        result={}
        if method=='account/read':
            reads+=1
            result={'account':{'type':'chatgpt' if reads==1 else 'apiKey','planType':'pro'}}
        if method=='model/list':result={'data':[{'model':'gpt-6-astra'}]}
        print(json.dumps({'id':msg['id'],'result':result}),flush=True)
    """.write(to:script,atomically:true,encoding:.utf8)
    try FileManager.default.setAttributes([.posixPermissions:0o700],ofItemAtPath:script.path)
    let client=CodexClient();defer{client.disconnect()}
    try await client.connect(binary:script.path);XCTAssertTrue(client.subscription)
    do {_ = try await client.send(text:"Should be blocked",engine:folder.path,project:folder.path,model:"gpt-6-astra");fatalError("API account dispatched")}
    catch {XCTAssertFalse(client.running)}
    let calls=try String(contentsOf:log)
    XCTAssertFalse(calls.contains("thread/start"))
}

@MainActor
func testUncertainDispatchKeepsTurnLockAndPersistsThreadFirst() async throws {
    let folder=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    try FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true)
    defer{try? FileManager.default.removeItem(at:folder)}
    let script=folder.appendingPathComponent("server.py"),saved=folder.appendingPathComponent("thread.txt")
    try """
    #!/usr/bin/python3
    import sys,json,os
    for line in sys.stdin:
        m=json.loads(line);method=m.get('method','')
        if 'id' not in m:continue
        result={}
        if method=='account/read':result={'account':{'type':'chatgpt','planType':'pro'}}
        if method=='model/list':result={'data':[{'model':'gpt-6-astra'}]}
        if method=='thread/start':result={'thread':{'id':'thread-fixture'}}
        if method=='turn/start':
            if not os.path.exists(\(String(reflecting:saved.path))):sys.exit(3)
            print(json.dumps({'method':'turn/started','params':{'turn':{'id':'turn-fixture'}}}),flush=True)
            continue
        print(json.dumps({'id':m['id'],'result':result}),flush=True)
    """.write(to:script,atomically:true,encoding:.utf8)
    try FileManager.default.setAttributes([.posixPermissions:0o700],ofItemAtPath:script.path)
    let client=CodexClient(requestTimeout:0.5);defer{client.disconnect()}
    try await client.connect(binary:script.path)
    do {_ = try await client.send(text:"Start",engine:folder.path,project:folder.path,model:"gpt-6-astra",onThreadReady:{id in try id.write(to:saved,atomically:true,encoding:.utf8)});fatalError("Expected withheld response timeout")}
    catch {XCTAssertTrue(client.running)}
    let persisted=try String(contentsOf:saved);XCTAssertEqual(persisted,"thread-fixture")
    do {_ = try await client.send(text:"Second",engine:folder.path,project:folder.path,model:"gpt-6-astra");fatalError("Second turn should be blocked")}
    catch {XCTAssertTrue(client.running)}
}

@MainActor
func testFailedProjectOpenPreservesIdentityAndRejectsOverlap() async throws {
    let root=FileManager.default.currentDirectoryPath
    let temp=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer{try? FileManager.default.removeItem(at:temp)}
    let bridge=EngineBridge(root:root,python:root+"/.venv/bin/python")
    let first=temp.appendingPathComponent("first").path
    _ = try await bridge.request("create",project:first,params:["title":"Same title"])
    let selection=ProjectSelection()
    try await selection.open(first,using:bridge)
    do {try await selection.open(temp.appendingPathComponent("missing").path,using:bridge);fatalError("Bad project should fail")}
    catch {XCTAssertEqual(selection.path,first);XCTAssertEqual(selection.data["title"] as? String,"Same title")}
    let task=Task {try await selection.open(first,using:bridge)}
    await Task.yield()
    if selection.loading {
        do {try await selection.open(first,using:bridge);fatalError("Overlap should fail")}
        catch {XCTAssertTrue(selection.loading)}
    } else {fatalError("Expected in-flight bridge request")}
    try await task.value
}

@MainActor
func testObservedCompletionWinsOverDelayedDispatchTimeout() async throws {
    let folder=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    try FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true)
    defer{try? FileManager.default.removeItem(at:folder)}
    let script=folder.appendingPathComponent("server.py"),saved=folder.appendingPathComponent("thread.txt")
    try """
    #!/usr/bin/python3
    import sys,json,os
    for line in sys.stdin:
        m=json.loads(line);method=m.get('method','')
        if 'id' not in m:continue
        result={}
        if method=='account/read':result={'account':{'type':'chatgpt','planType':'pro'}}
        if method=='model/list':result={'data':[{'model':'gpt-6-astra'}]}
        if method=='thread/start':result={'thread':{'id':'thread-fixture'}}
        if method=='turn/start':
            if not os.path.exists(\(String(reflecting:saved.path))):sys.exit(3)
            print(json.dumps({'method':'turn/started','params':{'turn':{'id':'turn-fixture'}}}),flush=True)
            print(json.dumps({'method':'turn/completed','params':{'turn':{'id':'turn-fixture','status':'completed','error':None}}}),flush=True)
            continue
        print(json.dumps({'id':m['id'],'result':result}),flush=True)
    """.write(to:script,atomically:true,encoding:.utf8)
    try FileManager.default.setAttributes([.posixPermissions:0o700],ofItemAtPath:script.path)
    let client=CodexClient(requestTimeout:0.5);defer{client.disconnect()}
    try await client.connect(binary:script.path)
    do {_ = try await client.send(text:"Start",engine:folder.path,project:folder.path,model:"gpt-6-astra",onThreadReady:{id in try id.write(to:saved,atomically:true,encoding:.utf8)});fatalError("Expected withheld response timeout")}
    catch {XCTAssertFalse(client.running)}
    let persisted=try String(contentsOf:saved);XCTAssertEqual(persisted,"thread-fixture")
}
