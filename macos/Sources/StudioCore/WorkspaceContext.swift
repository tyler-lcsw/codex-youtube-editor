import Foundation

public struct CodexDraft:Equatable {
    public let text:String
    public let projectID:String
    public let workflowID:String?
    public init(text:String,projectID:String,workflowID:String?) {
        self.text=text;self.projectID=projectID;self.workflowID=workflowID
    }
    public func isValid(projectID:String,workflowID:String?)->Bool {
        self.projectID == projectID && self.workflowID == workflowID
    }
}

public enum FeedbackSummary {
    public static func unresolvedCount(_ annotations:[[String:Any]])->Int {
        annotations.filter {($0["status"] as? String ?? "open") != "accepted"}.count
    }
}
