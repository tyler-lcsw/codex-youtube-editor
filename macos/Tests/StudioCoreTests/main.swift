import Foundation
func XCTAssertTrue(_ value: @autoclosure () -> Bool) { precondition(value()) }
func XCTAssertFalse(_ value: @autoclosure () -> Bool) { precondition(!value()) }
func XCTAssertNil<T>(_ value: T?) { precondition(value == nil) }
func XCTAssertEqual<T: Equatable>(_ a: T, _ b: T) { precondition(a == b, "\(a) != \(b)") }
func XCTAssertThrowsError<T>(_ body: @autoclosure () throws -> T) { do { _ = try body(); fatalError("Expected error") } catch {} }
func XCTUnwrap<T>(_ value: T?) throws -> T { guard let value else { throw NSError(domain:"Checks",code:1) }; return value }
try testDurableDiagnosticsAndCrashRecovery()
let p = ProtocolTests()
p.testSubscriptionGateRejectsAPIAndMissingAccount()
try p.testFramerPreservesSplitUnicodeAndMultipleMessages()
p.testMalformedJSONIsAnErrorRatherThanSilentLoss()
p.testInheritedAPIKeysAreRemovedAndSubscriptionForced()
p.testUnknownApprovalCannotBecomeAnAcceptance()
try ReviewTests().testLetterboxCoordinatesAndReverseDrag()
testAnnotationDraftsAndSavedContextStayIndependent()
Task { @MainActor in
    do { try await testTransportDisconnectResolvesPendingRequests(); try await testAccountSwitchToAPIPreventsTurnDispatch(); try await testUncertainDispatchKeepsTurnLockAndPersistsThreadFirst(); try await testFailedProjectOpenPreservesIdentityAndRejectsOverlap(); try await testObservedCompletionWinsOverDelayedDispatchTimeout(); print("13 native core checks passed"); exit(0) }
    catch { print(error); exit(1) }
}
RunLoop.main.run()
