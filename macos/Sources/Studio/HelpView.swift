import SwiftUI
import AppKit
import StudioCore

struct HelpView: View {
    let engine: String
    @State private var section: String
    @State private var query = ""
    @State private var loaded: LoadedHelpGuide?
    @State private var error: String?
    @State private var copyNotice = ""

    init(engine: String, initialSection: String? = nil) {
        self.engine = engine
        _section = State(initialValue: initialSection ?? "All sections")
    }
    private func reload() {
        copyNotice = ""
        do {
            loaded = try HelpGuide.load(
                repositoryURL: URL(fileURLWithPath: engine).appendingPathComponent("docs/user-guide.json"),
                bundledURL: Bundle.main.url(forResource: "user-guide", withExtension: "json"))
            error = nil
        } catch {loaded = nil; self.error = error.localizedDescription}
    }
    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                TextField("Search help", text: $query).textFieldStyle(.roundedBorder)
                    .accessibilityLabel("Search help")
                Button("Clear search") {query = ""}.accessibilityLabel("Clear search").disabled(query.isEmpty)
                Picker("Section", selection: $section) {
                    Text("All sections").tag("All sections")
                    ForEach(HelpGuide.sections, id: \.self) {Text($0).tag($0)}
                }.frame(width: 270).accessibilityLabel("Help section")
                Button("Reload help", action: reload).accessibilityLabel("Reload help")
            }
            if let loaded {
                Text(loaded.guide.title).font(.title2.bold())
                Text("\(loaded.source.rawValue) · \(loaded.url.path)").font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
                if let reason = loaded.fallbackReason {
                    Label(reason, systemImage: "info.circle").font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
                }
                let articles = loaded.guide.filtered(section: section == "All sections" ? nil : section, query: query)
                Text("\(articles.count) articles").font(.caption).foregroundStyle(.secondary)
                if !copyNotice.isEmpty {Text(copyNotice).font(.caption).accessibilityLabel(copyNotice)}
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 16) {
                        if articles.isEmpty {
                            StudioEmptyState(symbol: "magnifyingglass", title: "No matching help", detail: "Clear the search or choose All sections to see more articles.")
                        }
                        ForEach(articles) {article in
                            GroupBox {
                                VStack(alignment: .leading, spacing: 10) {
                                    Text(article.summary).textSelection(.enabled)
                                    ForEach(Array(article.steps.enumerated()), id: \.offset) {index, step in
                                        HStack(alignment: .top) {
                                            Text("\(index + 1).").monospacedDigit().frame(width: 28, alignment: .trailing)
                                            Text(step).frame(maxWidth: .infinity, alignment: .leading).textSelection(.enabled)
                                        }
                                    }
                                    ForEach(Array(article.notes.enumerated()), id: \.offset) {_, note in
                                        Text("Note: \(note)").font(.callout).foregroundStyle(.secondary).textSelection(.enabled)
                                    }
                                    if let prompt = article.prompt {
                                        Text("Example request").font(.subheadline.bold())
                                        Text(prompt).textSelection(.enabled)
                                        Button("Copy example") {
                                            NSPasteboard.general.clearContents()
                                            if NSPasteboard.general.setString(prompt, forType: .string) {
                                                copyNotice = "Example copied: \(article.title)"
                                            } else {copyNotice = "Could not copy the example. Select its text and copy it manually."}
                                        }.accessibilityLabel("Copy example for \(article.title)")
                                    }
                                }
                            } label: {
                                VStack(alignment: .leading, spacing: 5) {
                                    Text(article.section).font(.caption).foregroundStyle(.secondary)
                                    Text(article.title).font(.headline)
                                    Text(article.status).font(.caption).foregroundStyle(.secondary)
                                }
                            }
                        }
                    }.padding(.trailing, 8)
                }
            } else if let error {
                StudioEmptyState(symbol: "exclamationmark.triangle", title: "Help could not be loaded", detail: error)
                Spacer()
            } else {ProgressView("Loading help"); Spacer()}
        }.padding(24).task {reload()}.onChange(of: engine) {_, _ in reload()}
    }
}
