import Foundation
import StudioCore

// Exercise the real client and JSON-line transport without touching stored credentials.
@MainActor
func withAuthServer(_ body:String, test:(CodexClient,URL) async throws -> Void) async throws {
    let dir=FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    try FileManager.default.createDirectory(at:dir,withIntermediateDirectories:true)
    defer {try? FileManager.default.removeItem(at:dir)}
    let script=dir.appendingPathComponent("server.py"),log=dir.appendingPathComponent("calls")
    try ("""
    #!/usr/bin/python3
    import sys,json
    reads=0
    starts=0
    logged_in=False
    def emit(method,params):
        print(json.dumps({'method':method,'params':params}),flush=True)
    for line in sys.stdin:
        m=json.loads(line);method=m.get('method','')
        with open(\(String(reflecting:log.path)),'a') as f:f.write(method+'\\n')
        if 'id' not in m:continue
        result={}
        if method=='account/read':
            reads+=1
            result={'account':{'type':'chatgpt','planType':'pro'} if logged_in else None}
        if method=='model/list':result={'data':[{'model':'gpt-6-astra'}]}
        if method=='account/login/start':
            starts+=1
            result={'type':'chatgpt','loginId':'login-'+str(starts),'authUrl':'https://auth.openai.com/test'}
        if method=='account/login/cancel':result={'status':'canceled'}
    """ + "\n" + body.split(separator:"\n",omittingEmptySubsequences:false).map{"    "+$0}.joined(separator:"\n") + "\n    print(json.dumps({'id':m['id'],'result':result}),flush=True)\n").write(to:script,atomically:true,encoding:.utf8)
    try FileManager.default.setAttributes([.posixPermissions:0o700],ofItemAtPath:script.path)
    let client=CodexClient(requestTimeout:1);defer{client.disconnect()}
    try await client.connect(binary:script.path)
    try await test(client,log)
}

@MainActor
func testLoginFailureIsVisible() async throws {
    try await withAuthServer("""
    if method=='account/login/start':
        print(json.dumps({'id':m['id'],'result':result}),flush=True)
        emit('account/login/completed',{'loginId':'login-1','success':False,'error':'Local callback failed'})
        continue
    """) { client,_ in
        _ = try await client.signIn()
        for _ in 0..<100 {if client.lastError != nil {break};try await Task.sleep(nanoseconds:10_000_000)}
        XCTAssertTrue(client.lastError?.contains("Local callback failed") == true)
        XCTAssertFalse(client.subscription)
    }
}

@MainActor
func testRepeatedSignInDoesNotReplacePendingCallback() async throws {
    try await withAuthServer("") {client,log in
        _ = try await client.signIn()
        do {_ = try await client.signIn()} catch {}
        let calls=try String(contentsOf:log)
        XCTAssertEqual(calls.components(separatedBy:"account/login/start").count-1,1)
    }
}

@MainActor
func testExistingSubscriptionSkipsBrowserLogin() async throws {
    try await withAuthServer("if method=='account/read':result={'account':{'type':'chatgpt','planType':'pro'}}") {client,log in
        _ = try await client.signIn()
        XCTAssertTrue(client.subscription)
        let calls=try String(contentsOf:log);XCTAssertFalse(calls.contains("account/login/start"))
    }
}

@MainActor
func testLoginSuccessClearsLinkAndRefreshesAccount() async throws {
    try await withAuthServer("""
    if method=='account/login/start':
        logged_in=True
        emit('account/login/completed',{'loginId':'login-1','success':True,'error':None})
    """) {client,_ in
        _ = try await client.signIn()
        for _ in 0..<100 {if client.subscription {break};try await Task.sleep(nanoseconds:10_000_000)}
        XCTAssertTrue(client.subscription);XCTAssertFalse(client.signingIn);XCTAssertNil(client.loginURL)
    }
}

@MainActor
func testCancelAndRetryIgnoreOldCompletion() async throws {
    try await withAuthServer("""
    if method=='account/login/cancel' and m['params']['loginId']!='login-1':sys.exit(3)
    if method=='account/login/start' and starts==2:
        emit('account/login/completed',{'loginId':'login-1','success':False,'error':'stale failure'})
    """) {client,log in
        _ = try await client.signIn();try await client.cancelSignIn()
        XCTAssertNil(client.loginURL);XCTAssertFalse(client.signingIn)
        _ = try await client.signIn()
        XCTAssertTrue(client.signingIn);XCTAssertTrue(client.loginURL != nil);XCTAssertNil(client.lastError)
        let calls=try String(contentsOf:log);XCTAssertTrue(calls.contains("account/login/cancel"))
    }
}

@MainActor
func testLoginRefreshFailureIsVisible() async throws {
    try await withAuthServer("""
    if method=='account/login/start':
        emit('account/login/completed',{'loginId':'login-1','success':True,'error':None})
    if method=='account/read' and reads>2:
        print(json.dumps({'id':m['id'],'error':{'code':-1,'message':'Account read failed'}}),flush=True)
        continue
    """) {client,_ in
        _ = try await client.signIn()
        for _ in 0..<100 {if client.lastError != nil {break};try await Task.sleep(nanoseconds:10_000_000)}
        XCTAssertTrue(client.lastError?.contains("Account read failed") == true)
        XCTAssertFalse(client.subscription);XCTAssertNil(client.loginURL)
    }
}

@MainActor
func testLoginStartTimeoutClosesUnownedCallback() async throws {
    try await withAuthServer("if method=='account/login/start':continue") {client,_ in
        do {_ = try await client.signIn();fatalError("Expected timeout")} catch {}
        XCTAssertFalse(client.connected)
        XCTAssertFalse(client.signingIn);XCTAssertNil(client.loginURL)
    }
}

@MainActor
func testAccountCheckCannotClearAnInFlightLoginStart() async throws {
    try await withAuthServer("""
    if method=='account/login/start':
        import threading
        def reply(request_id=m['id'],response=result):
            print(json.dumps({'id':request_id,'result':response}),flush=True)
        threading.Timer(0.3,reply).start()
        continue
    if method=='account/read' and starts>0:result={'account':{'type':'chatgpt','planType':'pro'}}
    """) {client,log in
        let start=Task {try await client.signIn()}
        for _ in 0..<100 {
            if (try? String(contentsOf:log).contains("account/login/start"))==true {break}
            try await Task.sleep(nanoseconds:1_000_000)
        }
        var rejected=false
        do {try await client.checkSignIn()} catch {rejected=true}
        _ = try await start.value
        XCTAssertTrue(rejected)
        XCTAssertTrue(client.signingIn);XCTAssertTrue(client.loginURL != nil)
    }
}
