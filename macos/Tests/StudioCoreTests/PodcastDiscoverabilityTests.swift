import Foundation
import StudioCore

func testPodcastNavigationContractExposesVisibleSidebarDestination() {
    let item=StudioNavigationContract.sidebarItems.first {$0.destination == .podcast}
    XCTAssertEqual(item?.title,"Podcast")
    XCTAssertFalse(item?.systemImage.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty ?? true)
}

func testPodcastQuickStartActionsHaveAccessibleDeepLinks() {
    let actions=PodcastQuickStartAction.allCases
    XCTAssertEqual(actions.map(\.route.deepLink),["podcast/setup","review/podcast"])
    XCTAssertTrue(actions.allSatisfy {!$0.accessibilityLabel.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty})
}

func testPodcastReviewRouteUsesSharedDeepLinkableState() {
    var state=StudioNavigationState()
    XCTAssertTrue(state.open(deepLink:"review/podcast"))
    XCTAssertEqual(state.destination,.review)
    XCTAssertEqual(state.reviewArea,.podcast)
    XCTAssertEqual(state.route.deepLink,"review/podcast")
}

func testPodcastQuickStartCopyDescribesActualCodexAndExplicitReviewWorkflow() {
    let copy=PodcastQuickStartContent.workflowExplanation
    XCTAssertTrue(copy.contains("Codex & QA"))
    XCTAssertTrue(copy.localizedCaseInsensitiveContains("generate"))
    XCTAssertTrue(copy.localizedCaseInsensitiveContains("render"))
    XCTAssertTrue(copy.localizedCaseInsensitiveContains("explicit review"))
    XCTAssertFalse(copy.contains("not generated yet"))
}

func testStudioBuildIdentityDistinguishesInstalledBundles() {
    let label=StudioBuildIdentity.visible(shortVersion:"0.1.0",build:"20",revision:"dc42fca")
    XCTAssertTrue(label.contains("0.1.0"))
    XCTAssertTrue(label.contains("20"))
    XCTAssertTrue(label.contains("dc42fca"))
}

func testPodcastDestinationHasContextualHelpSection() {
    XCTAssertTrue(HelpGuide.sections.contains("Podcast"))
}
