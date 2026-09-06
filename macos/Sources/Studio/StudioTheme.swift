import SwiftUI
import AppKit

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
        case "Understanding":return "text.magnifyingglass"
        case "Review":return "play.rectangle"
        case "Resources":return "slider.horizontal.3"
        case "Codex & QA":return "checkmark.shield"
        default:return "tray.and.arrow.down"
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
