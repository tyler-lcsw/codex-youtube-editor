import Foundation

public enum StudioDestination:String,CaseIterable,Codable {
    case overview="Overview"
    case brief="Brief"
    case sources="Sources"
    case revisions="Revisions"
    case feedback="Feedback"
    case workflowGuide="Workflow Guide"
    case editingStyles="Editing Styles"
    case resources="Resources"
    case codex="Codex & QA"
    case help="How to Use"

    public init(title:String) {
        switch title {
        case "Brief & sources":self = .brief
        case "Podcast":self = .sources
        case "Understanding":self = .workflowGuide
        case "Review":self = .feedback
        case "Editing styles":self = .editingStyles
        default:self=Self.allCases.first {$0.rawValue == title} ?? .overview
        }
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

    public init(destination:StudioDestination = .overview,reviewArea:StudioReviewArea = .media) {
        self.destination=destination;self.reviewArea=reviewArea
        self.route=StudioRoute(deepLink:Self.defaultDeepLink(destination,reviewArea),destination:destination,reviewArea:reviewArea)
    }

    @discardableResult public mutating func open(deepLink:String)->Bool {
        let next:StudioRoute
        switch deepLink {
        case "podcast/setup":next=StudioRoute(deepLink:deepLink,destination:.sources)
        case "review/podcast":next=StudioRoute(deepLink:deepLink,destination:.feedback,reviewArea:.podcast)
        case "workflow/source_understanding":next=StudioRoute(deepLink:deepLink,destination:.workflowGuide)
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
        destination == .feedback && reviewArea == .podcast ? "review/podcast" : destination.rawValue
    }
}

public struct StudioNavigationItem:Equatable,Identifiable {
    public let destination:StudioDestination
    public let title:String
    public let systemImage:String
    public var id:String {destination.rawValue}
}

public struct StudioNavigationSection:Equatable,Identifiable {
    public let title:String
    public let items:[StudioNavigationItem]
    public var id:String {title}
    public init(title:String,items:[StudioNavigationItem]) {self.title=title;self.items=items}
}

public enum StudioNavigationContract {
    public static let sections:[StudioNavigationSection]=[
        .init(title:"Project",items:[
            .init(destination:.overview,title:"Overview",systemImage:"square.grid.2x2"),
            .init(destination:.brief,title:"Brief",systemImage:"doc.text"),
            .init(destination:.sources,title:"Sources",systemImage:"tray.and.arrow.down"),
            .init(destination:.revisions,title:"Revisions",systemImage:"film.stack"),
            .init(destination:.feedback,title:"Feedback",systemImage:"text.bubble"),
        ]),
        .init(title:"Work",items:[
            .init(destination:.workflowGuide,title:"Workflow Guide",systemImage:"point.topleft.down.to.point.bottomright.curvepath"),
        ]),
        .init(title:"Project Setup",items:[
            .init(destination:.editingStyles,title:"Editing Styles",systemImage:"checklist"),
            .init(destination:.resources,title:"Resources",systemImage:"slider.horizontal.3"),
        ]),
        .init(title:"System",items:[
            .init(destination:.codex,title:"Codex & QA",systemImage:"checkmark.shield"),
            .init(destination:.help,title:"How to Use",systemImage:"questionmark.circle"),
        ]),
    ]
    public static let sidebarItems=sections.flatMap(\.items)
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
            ? StudioRoute(deepLink:"podcast/setup",destination:.sources)
            : StudioRoute(deepLink:"review/podcast",destination:.feedback,reviewArea:.podcast)
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
