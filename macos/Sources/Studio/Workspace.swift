import SwiftUI
import Combine
import AppKit
import UniformTypeIdentifiers
import StudioCore

@MainActor final class Workspace: ObservableObject {
    @Published var engine: String
    @Published var python: String
    @Published var codexBinary: String
    @Published var project=""
    @Published var data=[String:Any]()
    @Published var workflow=[String:Any]()
    @Published var quality=[String:Any]()
    @Published var busy=false
    @Published var dataRevision=0
    @Published var error: String?
    @Published var notice=""
    @Published var navigation=StudioNavigationState()
    @Published var hasUnsavedStyleDraft=false
    @Published var codexPrompt="" {
        didSet {if !codexPrompt.isEmpty {codexDraftProject=project;codexDraftWorkflowID=activeWorkflowID}}
    }
    @Published private(set) var codexDraftProject=""
    @Published private(set) var codexDraftWorkflowID:String?
    @Published var reviewSelectionID=""
    @Published var requestAddWorkflow=false
    let codex=CodexClient()
    private let selection=ProjectSelection()
    private var codexObserver:AnyCancellable?
    private var refreshPending=false
    var bridge:EngineBridge {EngineBridge(root:engine,python:python)}
    var assets:[[String:Any]] {data["assets"] as? [[String:Any]] ?? []}
    var revisions:[[String:Any]] {data["revisions"] as? [[String:Any]] ?? []}
    var annotations:[[String:Any]] {data["annotations"] as? [[String:Any]] ?? []}
    var activeWorkflow:WorkflowInstance? {(try? WorkflowGuideSnapshot.parse(workflow))?.activeWorkflow}
    var activeWorkflowID:String? {activeWorkflow?.id}
    var codexPromptIsCurrent:Bool {
        guard let activeWorkflowID,!codexPrompt.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else{return false}
        return CodexDraft(text:codexPrompt,projectID:codexDraftProject,workflowID:codexDraftWorkflowID).isValid(projectID:project,workflowID:activeWorkflowID)
    }
    var hasSoloPodcastContext:Bool {
        if let guide=try? WorkflowGuideSnapshot.parse(workflow),!guide.workflows.isEmpty {return guide.isActiveSoloPodcast}
        return data["podcast"] is [String:Any]
    }
    var unresolvedFeedbackCount:Int {FeedbackSummary.unresolvedCount(annotations)}
    var title:String {data["title"] as? String ?? "New production"}
    init() {
        let defaults=UserDefaults.standard
        let args=ProcessInfo.processInfo.arguments
        func argument(_ name:String)->String? {guard let i=args.firstIndex(of:name),i+1<args.count else{return nil};return args[i+1]}
        let root=argument("--engine") ?? defaults.string(forKey:"engine") ?? Bundle.main.object(forInfoDictionaryKey:"StudioEnginePath") as? String ?? ""
        engine=root
        python=argument("--python") ?? defaults.string(forKey:"python") ?? (root+"/.venv/bin/python")
        codexBinary=defaults.string(forKey:"codexBinary") ?? "/Applications/ChatGPT.app/Contents/Resources/codex"
        project=argument("--project") ?? defaults.string(forKey:"project") ?? ""
        navigation.select(StudioDestination(title:argument("--section") ?? "Overview"))
        codexObserver=codex.$running.removeDuplicates().dropFirst().sink { [weak self] running in
            if !running {Task { @MainActor [weak self] in self?.requestRefresh()}}
        }
    }
    var section:String {navigation.destination.rawValue}
    func open(_ route:StudioRoute) {
        guard !hasUnsavedStyleDraft || route.destination == .editingStyles else {error="Save or reload the editing style before leaving this screen.";return}
        Diagnostics.shared?.record("tab_selected",detail:route.deepLink)
        navigation.open(route)
    }
    func select(_ destination:StudioDestination) {
        guard !hasUnsavedStyleDraft || destination == .editingStyles else {error="Save or reload the editing style before leaving this screen.";return}
        Diagnostics.shared?.record("tab_selected",detail:destination.rawValue)
        navigation.select(destination)
    }
    func showAddWorkflow() {
        select(.workflowGuide)
        guard navigation.destination == .workflowGuide else{return}
        requestAddWorkflow=true
    }
    func updateCodexPrompt(_ text:String) {
        codexPrompt=text
    }
    func clearCodexPrompt() {codexPrompt="";codexDraftProject="";codexDraftWorkflowID=nil}
    func clearProjectDrafts() {clearCodexPrompt();reviewSelectionID="";navigation.selectReviewArea(.media)}
    func reconcileContext() {
        if !codexPrompt.isEmpty,!CodexDraft(text:codexPrompt,projectID:codexDraftProject,workflowID:codexDraftWorkflowID).isValid(projectID:project,workflowID:activeWorkflowID) {clearCodexPrompt()}
        if !hasSoloPodcastContext,navigation.reviewArea == .podcast {navigation.selectReviewArea(.media)}
        if !reviewSelectionID.isEmpty,!revisions.contains(where:{$0["id"] as? String == reviewSelectionID}) {reviewSelectionID=""}
    }
    func openFeedback(reviewing revisionID:String) {
        reviewSelectionID=revisionID;navigation.selectReviewArea(.media);select(.feedback)
    }
    func persist() {let d=UserDefaults.standard;d.set(engine,forKey:"engine");d.set(python,forKey:"python");d.set(codexBinary,forKey:"codexBinary");d.set(project,forKey:"project")}
    func perform(_ body:@escaping () async throws -> Void) {
        guard !busy else {return};busy=true;error=nil
        Task {
            do {try await body();persist()}catch{Diagnostics.shared?.record("action_failed",detail:String(reflecting:type(of:error)));self.error=error.localizedDescription}
            busy=false
            if refreshPending {refreshPending=false;requestRefresh()}
        }
    }
    func requestRefresh() {
        guard !project.isEmpty else{return}
        if busy {refreshPending=true;return}
        perform {try await self.refresh()}
    }
    func request(_ method:String,_ params:[String:Any]=[:]) async throws {
        // Invalidate visible assessments before any potentially state-changing request.
        workflow=[:];quality=[:]
        do {
            let nextData=try await bridge.request(method,project:project,params:params)
            var nextWorkflow=try await bridge.request("workflow",project:project)
            if let contexts=try? await bridge.request("workflow_instances",project:project) {
                nextWorkflow.merge(contexts) {_,context in context}
            }
            let nextQuality=try await bridge.request("quality",project:project)
            data=nextData;workflow=nextWorkflow;quality=nextQuality;dataRevision += 1
            reconcileContext()
        } catch {
            clearCodexPrompt()
            throw error
        }
    }
    func refresh() async throws {
        try await request("open")
    }
    func newProject() {
        guard !hasUnsavedStyleDraft else {error="Save or reload the editing style before changing projects.";return}
        guard !busy && !codex.running else {error="Wait for the current action or stop the Codex task before changing projects.";return}
        let panel=NSSavePanel();panel.title="Create production folder";panel.nameFieldStringValue="Untitled Production"
        let base=FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Movies/Codex Studio")
        try? FileManager.default.createDirectory(at:base,withIntermediateDirectories:true);panel.directoryURL=base;panel.canCreateDirectories=true
        guard panel.runModal() == .OK,let url=panel.url else{return}
        let candidate=url.path
        perform {
            try await self.selection.open(candidate,using:self.bridge,createTitle:url.lastPathComponent)
            self.clearProjectDrafts()
            self.data=self.selection.data;self.project=self.selection.path;self.dataRevision += 1;try await self.refresh()
        }
    }
    func openProject() {
        guard !hasUnsavedStyleDraft else {error="Save or reload the editing style before changing projects.";return}
        guard !busy && !codex.running else {error="Wait for the current action or stop the Codex task before changing projects.";return}
        let panel=NSOpenPanel();panel.canChooseDirectories=true;panel.canChooseFiles=false;panel.title="Open production folder"
        guard panel.runModal() == .OK,let url=panel.url else{return}
        let candidate=url.path
        perform {
            try await self.selection.open(candidate,using:self.bridge)
            self.clearProjectDrafts()
            self.data=self.selection.data;self.project=self.selection.path;self.dataRevision += 1;try await self.refresh()
        }
    }
    func importFiles(role:String="source",revision:Bool=false,attachToActiveWorkflow:Bool=false) {
        let panel=NSOpenPanel();panel.allowsMultipleSelection=true;panel.title=revision ? "Add rendered revision" : "Import sources"
        if panel.runModal() == .OK {importURLs(panel.urls,role:role,revision:revision,attachToActiveWorkflow:attachToActiveWorkflow)}
    }
    func importURLs(_ urls:[URL],role:String="source",revision:Bool=false,attachToActiveWorkflow:Bool=false) {
        guard !project.isEmpty else {error="Create or open a production first.";return}
        let workflowAtImport=activeWorkflow
        guard !revision || !attachToActiveWorkflow || workflowAtImport != nil else {error="Add or select an active workflow before importing a revision.";return}
        perform {
            for url in urls {
                let document=["pdf","txt","md","docx","json","csv"].contains(url.pathExtension.lowercased())
                var params:[String:Any]=["path":url.path,"role":document ? "document" : role]
                if revision,attachToActiveWorkflow,let workflowAtImport {params["workflow_id"]=workflowAtImport.id}
                try await self.request(revision ? "add_revision" : "import_media",params)
            }
            try await self.refresh();self.notice=attachToActiveWorkflow && revision && workflowAtImport != nil ? "Imported \(urls.count) revision(s) and attached them to the active workflow." : "Imported \(urls.count) file(s). Originals preserved."
        }
    }
    func handoff(copy:Bool=true) async throws -> [String:Any] {
        let result=try await bridge.request("export_handoff",project:project)
        if copy,let text=result["text"] as? String {NSPasteboard.general.clearContents();NSPasteboard.general.setString(text,forType:.string);notice="Handoff copied for Codex."}
        return result
    }
}
