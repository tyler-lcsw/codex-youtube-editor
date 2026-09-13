import Foundation

public enum StudioDestination:String,CaseIterable,Codable {
    case projectHome="Project Home"
    case currentWork="Current Work"
    case projectSettings="Project Settings"
    case help="Help"

    public init(title:String) {
        switch title {
        case "Project Home","Overview":self = .projectHome
        case "Current Work","Brief","Brief & sources","Sources","Podcast","Understanding","Review","Revisions","Feedback","Workflow Guide","Codex & QA":self = .currentWork
        case "Project Settings","Editing Styles","Editing styles","Resources":self = .projectSettings
        case "Help","How to Use":self = .help
        default:self = .projectHome
        }
    }
}

public enum StudioReviewArea:String,Codable {
    case media
    case podcast
}

public enum StudioProjectSettingsSection:String,CaseIterable {
    case editing="Editing Style"
    case resources="Resources"
    case application="Application"

    public static func permitsTransition(hasUnsavedStyleDraft:Bool,to next:Self)->Bool {
        !hasUnsavedStyleDraft || next == .editing
    }
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

    public init(destination:StudioDestination = .projectHome,reviewArea:StudioReviewArea = .media) {
        self.destination=destination;self.reviewArea=reviewArea
        self.route=StudioRoute(deepLink:Self.defaultDeepLink(destination,reviewArea),destination:destination,reviewArea:reviewArea)
    }

    @discardableResult public mutating func open(deepLink:String)->Bool {
        let next:StudioRoute
        switch deepLink {
        case "podcast/setup":next=StudioRoute(deepLink:deepLink,destination:.currentWork)
        case "review/podcast":next=StudioRoute(deepLink:deepLink,destination:.currentWork,reviewArea:.podcast)
        case "workflow/source_understanding":next=StudioRoute(deepLink:deepLink,destination:.currentWork)
        case "Overview","Project Home":next=StudioRoute(deepLink:deepLink,destination:.projectHome)
        case "Brief","Brief & sources","Sources","Podcast","Understanding","Review","Revisions","Feedback","Workflow Guide","Codex & QA","Current Work":next=StudioRoute(deepLink:deepLink,destination:.currentWork)
        case "Editing Styles","Editing styles","Resources","Project Settings":next=StudioRoute(deepLink:deepLink,destination:.projectSettings)
        case "How to Use","Help":next=StudioRoute(deepLink:deepLink,destination:.help)
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
        destination == .currentWork && reviewArea == .podcast ? "review/podcast" : destination.rawValue
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
            .init(destination:.projectHome,title:"Project Home",systemImage:"square.grid.2x2"),
        ]),
        .init(title:"Settings",items:[
            .init(destination:.projectSettings,title:"Project Settings",systemImage:"slider.horizontal.3"),
        ]),
        .init(title:"System",items:[
            .init(destination:.help,title:"Help",systemImage:"questionmark.circle"),
        ]),
    ]
    public static let sidebarItems=sections.flatMap(\.items)
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
