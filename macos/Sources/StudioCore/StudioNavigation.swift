import Foundation

public enum StudioDestination:String,CaseIterable,Codable {
    case brief="Brief & sources"
    case podcast="Podcast"
    case understanding="Understanding"
    case review="Review"
    case resources="Resources"
    case codex="Codex & QA"
    case help="How to Use"

    public init(title:String) {
        self=Self.allCases.first {$0.rawValue == title} ?? .brief
    }
}

public enum StudioReviewArea:String,Codable {
    case media
    case podcast
}

public struct StudioRoute:Equatable {
    public let deepLink:String
    public let destination:StudioDestination
    public let reviewArea:StudioReviewArea

    public init(deepLink:String,destination:StudioDestination,reviewArea:StudioReviewArea = .media) {
        self.deepLink=deepLink;self.destination=destination;self.reviewArea=reviewArea
    }
}

public struct StudioNavigationState:Equatable {
    public var destination:StudioDestination
    public var reviewArea:StudioReviewArea
    public private(set) var route:StudioRoute

    public init(destination:StudioDestination = .brief,reviewArea:StudioReviewArea = .media) {
        self.destination=destination;self.reviewArea=reviewArea
        self.route=StudioRoute(deepLink:Self.defaultDeepLink(destination,reviewArea),destination:destination,reviewArea:reviewArea)
    }

    @discardableResult public mutating func open(deepLink:String)->Bool {
        let next:StudioRoute
        switch deepLink {
        case "podcast/setup":next=StudioRoute(deepLink:deepLink,destination:.brief)
        case "review/podcast":next=StudioRoute(deepLink:deepLink,destination:.review,reviewArea:.podcast)
        default:return false
        }
        destination=next.destination;reviewArea=next.reviewArea;route=next
        return true
    }

    public mutating func open(_ route:StudioRoute) {
        destination=route.destination;reviewArea=route.reviewArea;self.route=route
    }

    public mutating func select(_ destination:StudioDestination) {
        self.destination=destination
        route=StudioRoute(deepLink:Self.defaultDeepLink(destination,reviewArea),destination:destination,reviewArea:reviewArea)
    }

    public mutating func selectReviewArea(_ reviewArea:StudioReviewArea) {
        self.reviewArea=reviewArea
        route=StudioRoute(deepLink:Self.defaultDeepLink(destination,reviewArea),destination:destination,reviewArea:reviewArea)
    }

    private static func defaultDeepLink(_ destination:StudioDestination,_ reviewArea:StudioReviewArea)->String {
        destination == .review && reviewArea == .podcast ? "review/podcast" : destination.rawValue
    }
}

public struct StudioNavigationItem:Equatable {
    public let destination:StudioDestination
    public let title:String
    public let systemImage:String
}

public enum StudioNavigationContract {
    public static let sidebarItems:[StudioNavigationItem]=[
        .init(destination:.brief,title:StudioDestination.brief.rawValue,systemImage:"tray.and.arrow.down"),
        .init(destination:.podcast,title:StudioDestination.podcast.rawValue,systemImage:"waveform"),
        .init(destination:.understanding,title:StudioDestination.understanding.rawValue,systemImage:"text.magnifyingglass"),
        .init(destination:.review,title:StudioDestination.review.rawValue,systemImage:"play.rectangle"),
        .init(destination:.resources,title:StudioDestination.resources.rawValue,systemImage:"slider.horizontal.3"),
        .init(destination:.codex,title:StudioDestination.codex.rawValue,systemImage:"checkmark.shield"),
        .init(destination:.help,title:StudioDestination.help.rawValue,systemImage:"questionmark.circle"),
    ]
}

public enum PodcastQuickStartAction:String,CaseIterable {
    case setup
    case review

    public var title:String {self == .setup ? "Set up podcast sources" : "Review podcast visuals"}
    public var detail:String {
        self == .setup
            ? "Choose one canonical audio source, an optional camera source, and visual density."
            : "Inspect chapter proposals, explicit decisions, and long-form qualification evidence."
    }
    public var accessibilityLabel:String {self == .setup ? "Set up solo podcast sources" : "Review solo podcast visuals"}
    public var systemImage:String {self == .setup ? "waveform.badge.plus" : "rectangle.stack.badge.play"}
    public var route:StudioRoute {
        self == .setup
            ? StudioRoute(deepLink:"podcast/setup",destination:.brief)
            : StudioRoute(deepLink:"review/podcast",destination:.review,reviewArea:.podcast)
    }
}

public enum PodcastQuickStartContent {
    public static let workflowExplanation="Import one speaker's audio, with optional camera video. Use Codex & QA to generate and render the branded waveform and chapter visuals, then complete explicit review before accepting an episode."
}

public struct StudioBuildIdentity:Equatable {
    public let shortVersion:String
    public let build:String
    public let revision:String

    public init(shortVersion:String,build:String,revision:String) {
        self.shortVersion=shortVersion;self.build=build;self.revision=revision
    }

    public static var current:StudioBuildIdentity {
        let info=Bundle.main.infoDictionary ?? [:]
        return .init(
            shortVersion:info["CFBundleShortVersionString"] as? String ?? "unknown",
            build:info["CFBundleVersion"] as? String ?? "unknown",
            revision:info["StudioEngineRevision"] as? String ?? "unavailable"
        )
    }

    public static func visible(shortVersion:String,build:String,revision:String)->String {
        "Version \(shortVersion) · build \(build) · \(revision)"
    }

    public var visibleLabel:String {Self.visible(shortVersion:shortVersion,build:build,revision:revision)}
}
