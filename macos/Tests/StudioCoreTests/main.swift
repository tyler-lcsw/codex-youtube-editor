import Foundation
func XCTAssertTrue(_ value: @autoclosure () -> Bool) { precondition(value()) }
func XCTAssertFalse(_ value: @autoclosure () -> Bool) { precondition(!value()) }
func XCTAssertNil<T>(_ value: T?) { precondition(value == nil) }
func XCTAssertEqual<T: Equatable>(_ a: T, _ b: T) { precondition(a == b, "\(a) != \(b)") }
func XCTAssertThrowsError<T>(_ body: @autoclosure () throws -> T) { do { _ = try body(); fatalError("Expected error") } catch {} }
func XCTUnwrap<T>(_ value: T?) throws -> T { guard let value else { throw NSError(domain:"Checks",code:1) }; return value }
try testHelpValidation()
try testHelpSearchAndSection()
try testHelpRepositoryAndFallback()
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
    do { try await testAccountCheckShowsSignedOutAndFailureResults(); try await testManualAccountCheckReportsProgressAndResult(); try await testArchivedConversationResumesWithoutLosingAuthentication(); try await testUnrelatedResumeErrorsDoNotRestoreConversations(); try await testAccountCheckCannotClearAnInFlightLoginStart(); try await testLoginStartTimeoutClosesUnownedCallback(); try await testLoginSuccessClearsLinkAndRefreshesAccount(); try await testCancelAndRetryIgnoreOldCompletion(); try await testLoginRefreshFailureIsVisible(); try await testLoginFailureIsVisible(); try await testRepeatedSignInDoesNotReplacePendingCallback(); try await testExistingSubscriptionSkipsBrowserLogin(); try await testTransportDisconnectResolvesPendingRequests(); try await testAccountSwitchToAPIPreventsTurnDispatch(); try await testUncertainDispatchKeepsTurnLockAndPersistsThreadFirst(); try await testFailedProjectOpenPreservesIdentityAndRejectsOverlap(); try await testObservedCompletionWinsOverDelayedDispatchTimeout(); print("28 native core checks passed"); exit(0) }
    catch { print(error); exit(1) }
}
RunLoop.main.run()
