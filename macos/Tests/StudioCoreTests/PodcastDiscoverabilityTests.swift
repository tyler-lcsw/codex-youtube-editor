import Foundation
import StudioCore

func testPodcastNavigationContractKeepsPodcastContextWithoutPermanentDestination() {
    let titles=StudioNavigationContract.sidebarItems.map(\.title)
    XCTAssertFalse(titles.contains("Podcast"))
    XCTAssertFalse(titles.contains("Sources"))
    XCTAssertTrue(titles.contains("Project Home"))
}

func testPodcastReviewRouteUsesSharedDeepLinkableState() {
    var state=StudioNavigationState()
    XCTAssertTrue(state.open(deepLink:"review/podcast"))
    XCTAssertEqual(state.destination.rawValue,"Current Work")
    XCTAssertEqual(state.reviewArea,.podcast)
    XCTAssertEqual(state.route.deepLink,"review/podcast")
}

func testStudioBuildIdentityDistinguishesInstalledBundles() {
    let label=StudioBuildIdentity.visible(shortVersion:"0.1.0",build:"20",revision:"dc42fca")
    XCTAssertTrue(label.contains("0.1.0"))
    XCTAssertTrue(label.contains("20"))
    XCTAssertTrue(label.contains("dc42fca"))
}

func testPodcastDestinationHasContextualHelpSection() {
    XCTAssertTrue(HelpGuide.sections.contains("Current Work"))
    XCTAssertFalse(HelpGuide.sections.contains("Podcast"))
}
