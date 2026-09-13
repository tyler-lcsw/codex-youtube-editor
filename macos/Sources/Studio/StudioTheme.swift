import SwiftUI
import AppKit
import StudioCore

// Precision Cut identity. Coral text uses a darker accessible shade on ivory.
enum StudioTheme {
    static let ivory = Color(red:245/255,green:235/255,blue:221/255)
    static let coral = Color(red:243/255,green:107/255,blue:79/255)
    static let graphite = Color(red:48/255,green:50/255,blue:52/255)
    static let canvas = adaptive(light:0xF5EBDD,dark:0x242628)
    static let panel = adaptive(light:0xFFF9F1,dark:0x303234)
    static let text = adaptive(light:0x303234,dark:0xF5EBDD)
    static let accent = adaptive(light:0xA93420,dark:0xFF947C)
    static let button = Color(red:169/255,green:52/255,blue:32/255)
    static let border = adaptive(light:0xD6C9B9,dark:0x626160)
    static func adaptive(light:Int,dark:Int)->Color {
        Color(nsColor:NSColor(name:nil,dynamicProvider:{appearance in
            let value=appearance.bestMatch(from:[.darkAqua,.aqua]) == .darkAqua ? dark : light
            return NSColor(srgbRed:Double((value>>16)&255)/255,green:Double((value>>8)&255)/255,blue:Double(value&255)/255,alpha:1)
        }))
    }
    static func symbol(for section:String)->String {
        switch section {
        case "Overview":return "square.grid.2x2"
        case "Brief":return "doc.text"
        case "Sources":return "tray.and.arrow.down"
        case "Revisions":return "film.stack"
        case "Feedback":return "text.bubble"
        case "Workflow Guide":return "point.topleft.down.to.point.bottomright.curvepath"
        case "Editing Styles":return "checklist"
        case "How to Use":return "questionmark.circle"
        case "Resources":return "slider.horizontal.3"
        case "Codex & QA":return "checkmark.shield"
        default:return "tray.and.arrow.down"
        }
    }
    static func helpSection(for navigation:StudioNavigationState)->String {
        switch navigation.destination {
        case .brief:return "Brief"
        case .sources:return "Sources"
        case .revisions,.feedback:return "Feedback"
        case .editingStyles:return "Editing Styles"
        case .resources:return "Resources"
        case .codex:return "Codex & QA"
        case .help:return "How to Use"
        case .workflowGuide:return "Workflow Guide"
        default:return "Getting started"
        }
    }
}

struct StudioPanelStyle:GroupBoxStyle {
    func makeBody(configuration:Configuration)->some View {
        VStack(alignment:.leading,spacing:10) {
            configuration.label.font(.headline)
            configuration.content.frame(maxWidth:.infinity,alignment:.leading)
        }.padding(16).background(StudioTheme.panel,in:RoundedRectangle(cornerRadius:12))
            .overlay(RoundedRectangle(cornerRadius:12).stroke(StudioTheme.border.opacity(0.6),lineWidth:1))
    }
}

struct StudioStatus:View {
    let status:String
    var symbol:String {
        switch status {
        case "complete","completed","passed","accepted":return "checkmark.circle"
        case "rejected":return "xmark.circle"
        case "base stage":return "rectangle"
        case "changes requested":return "arrow.triangle.2.circlepath"
        case "blocked","failed","stale":return "exclamationmark.triangle"
        case "addressed","ready_for_review":return "arrow.triangle.2.circlepath"
        default:return "circle.dotted"
        }
    }
    var body:some View {
        Label(status.replacingOccurrences(of:"_",with:" "),systemImage:symbol)
            .font(.caption).foregroundStyle(StudioTheme.text)
            .padding(.horizontal,8).padding(.vertical,4)
            .background(StudioTheme.accent.opacity(0.09),in:Capsule())
    }
}

struct StudioEmptyState:View {
    let symbol:String
    let title:String
    let detail:String
    var body:some View {
        VStack(spacing:8) {
            Image(systemName:symbol).font(.system(size:28,weight:.light)).foregroundStyle(StudioTheme.accent).accessibilityHidden(true)
            Text(title).font(.headline)
            Text(detail).font(.callout).foregroundStyle(.secondary).multilineTextAlignment(.center)
        }.frame(maxWidth:.infinity).padding(20)
    }
}
