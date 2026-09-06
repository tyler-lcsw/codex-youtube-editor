import Foundation

public struct HelpArticle: Codable, Identifiable, Equatable {
    public let id: String
    public let section: String
    public let title: String
    public let summary: String
    public let status: String
    public let steps: [String]
    public let notes: [String]
    public let prompt: String?
}

public struct HelpGuide: Codable, Equatable {
    public static let sections = ["Getting started", "Brief & sources", "Understanding", "Review", "Resources", "Codex & QA", "How to Use", "Production skills", "Troubleshooting"]
    public let schemaVersion: Int
    public let title: String
    public let articles: [HelpArticle]
    enum CodingKeys: String, CodingKey {case schemaVersion = "schema_version", title, articles}

    public init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        schemaVersion = try values.decode(Int.self, forKey: .schemaVersion)
        title = try values.decode(String.self, forKey: .title)
        articles = try values.decode([HelpArticle].self, forKey: .articles)
        guard schemaVersion == 1 else {throw HelpGuideError("Unsupported guide version \(schemaVersion).")}
        guard Self.nonempty(title), !articles.isEmpty else {throw HelpGuideError("Guide title and articles are required.")}
        var ids = Set<String>()
        for article in articles {
            guard article.id.range(of: "^[a-z0-9]+(?:-[a-z0-9]+)*$", options: .regularExpression) != nil,
                  ids.insert(article.id).inserted else {throw HelpGuideError("Invalid or duplicate article ID: \(article.id).")}
            guard Self.sections.contains(article.section),
                  [article.title, article.summary, article.status].allSatisfy(Self.nonempty),
                  !article.steps.isEmpty, article.steps.allSatisfy(Self.nonempty),
                  article.notes.allSatisfy(Self.nonempty),
                  article.prompt.map(Self.nonempty) ?? true else {
                throw HelpGuideError("Article \(article.id) has an invalid section or empty required text.")
            }
        }
    }
    private static func nonempty(_ text: String) -> Bool {!text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty}
    public static func decode(_ data: Data) throws -> HelpGuide {try JSONDecoder().decode(HelpGuide.self, from: data)}
    public func filtered(section: String?, query: String) -> [HelpArticle] {
        let query = query.trimmingCharacters(in: .whitespacesAndNewlines)
        return articles.filter {article in
            (section == nil || article.section == section) && (query.isEmpty ||
                ([article.id, article.section, article.title, article.summary, article.status] + article.steps + article.notes + [article.prompt ?? ""])
                .contains {$0.localizedStandardContains(query)})
        }
    }
    public static func load(repositoryURL: URL, bundledURL: URL?) throws -> LoadedHelpGuide {
        do {return LoadedHelpGuide(guide: try decode(Data(contentsOf: repositoryURL)), source: .repository, url: repositoryURL, fallbackReason: nil)}
        catch {
            let reason = "Repository guide unavailable at \(repositoryURL.path): \(error.localizedDescription)"
            guard let bundledURL else {throw HelpGuideError("\(reason) No bundled guide was found. Restore docs/user-guide.json in the engine repository or reinstall the app, then choose Reload help.")}
            do {return LoadedHelpGuide(guide: try decode(Data(contentsOf: bundledURL)), source: .bundled, url: bundledURL, fallbackReason: reason)}
            catch {throw HelpGuideError("\(reason) Bundled guide also failed: \(error.localizedDescription) Restore docs/user-guide.json or reinstall the app, then choose Reload help.")}
        }
    }
}
public enum HelpGuideSource: String {case repository = "Repository guide", bundled = "Bundled guide"}
public struct LoadedHelpGuide {
    public let guide: HelpGuide
    public let source: HelpGuideSource
    public let url: URL
    public let fallbackReason: String?
}
public struct HelpGuideError: LocalizedError {
    public let errorDescription: String?
    public init(_ message: String) {errorDescription = message}
}
