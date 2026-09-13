import Foundation

public enum WorkflowInputKind:String,Equatable {case text,choice,source,revision}
public enum WorkflowInputMode:String,Equatable {case selected;case allProject="all_project"}

public enum WorkflowTemplateKind:String,Equatable {
    case deliverable
    case supportingAction="supporting_action"

    public static func inferred(for templateID:String)->Self {
        ["clean_audio","tighten_silence"].contains(templateID) ? .supportingAction : .deliverable
    }
}

public struct WorkflowInputDefinition:Equatable,Identifiable {
    public let id:String
    public let label:String
    public let required:Bool
    public let kind:WorkflowInputKind
    public let options:[String]
    public init(id:String,label:String,required:Bool,kind:WorkflowInputKind,options:[String]) {
        self.id=id;self.label=label;self.required=required;self.kind=kind;self.options=options
    }
}

public struct WorkflowTemplate:Equatable,Identifiable {
    public let id:String
    public let name:String
    public let summary:String
    public let inputs:[WorkflowInputDefinition]
    public let kind:WorkflowTemplateKind
    public init(id:String,name:String,summary:String,inputs:[WorkflowInputDefinition],kind:WorkflowTemplateKind?=nil) {
        self.id=id;self.name=name;self.summary=summary;self.inputs=inputs;self.kind=kind ?? .inferred(for:id)
    }
    public func createPayload(name:String,values:[String:String]) throws -> [String:Any] {
        let cleanName=name.trimmingCharacters(in:.whitespacesAndNewlines)
        guard !cleanName.isEmpty else {throw WorkflowGuideError("Workflow name is required.")}
        for input in inputs where input.required {
            guard let value=values[input.id],!value.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else {
                throw WorkflowGuideError("\(input.label) is required.")
            }
        }
        return ["template_id":id,"name":cleanName,"inputs":values]
    }
    public func createPayload(name:String,assetIDs:[String],revisionIDs:[String],parentWorkflowID:String?=nil)->[String:Any] {
        var payload:[String:Any]=["template_id":id,"name":name.trimmingCharacters(in:.whitespacesAndNewlines),"inputs":["asset_ids":assetIDs,"revision_ids":revisionIDs,"annotation_ids":NSNull()]]
        if let parentWorkflowID {payload["parent_workflow_id"]=parentWorkflowID}
        return payload
    }
}

public enum WorkflowStepStatus:String,Equatable {
    case completed,ready,current,upcoming,blocked,needsAttention
    public var label:String {
        switch self {
        case .completed:return "Complete"
        case .ready:return "Ready"
        case .current:return "Current"
        case .upcoming:return "Not started"
        case .blocked:return "Blocked"
        case .needsAttention:return "Needs review"
        }
    }
    public var systemImage:String {
        switch self {
        case .completed:return "checkmark.circle.fill"
        case .ready,.current:return "arrow.right.circle.fill"
        case .blocked:return "lock.circle"
        case .needsAttention:return "exclamationmark.triangle.fill"
        case .upcoming:return "circle"
        }
    }
}

public struct WorkflowStep:Equatable,Identifiable {
    public let id:String
    public let label:String
    public let detail:String
    public let status:WorkflowStepStatus
    public let destination:StudioDestination
    public let prompt:String?
    public let staleReasons:[WorkflowStaleReason]
}

public struct WorkflowStaleReason:Equatable,Identifiable {
    public let code:String
    public let detail:String
    public var id:String {code+":"+detail}
    public init(code:String,detail:String) {self.code=code;self.detail=detail}
}

public struct WorkflowInstance:Equatable,Identifiable {
    public let id:String
    public let templateID:String
    public let name:String
    public let kind:WorkflowTemplateKind
    public let parentWorkflowID:String?
    public let inputMode:WorkflowInputMode
    public let inputs:WorkflowInputs
    public let steps:[WorkflowStep]
    public let staleReasons:[WorkflowStaleReason]
    public var isSoloPodcast:Bool {templateID == WorkflowTemplateIdentifiers.soloPodcast}
    public init(id:String,templateID:String,name:String,kind:WorkflowTemplateKind?=nil,parentWorkflowID:String?=nil,inputMode:WorkflowInputMode = .selected,inputs:WorkflowInputs,steps:[WorkflowStep],staleReasons:[WorkflowStaleReason]) {
        self.id=id;self.templateID=templateID;self.name=name;self.kind=kind ?? .inferred(for:templateID);self.parentWorkflowID=parentWorkflowID;self.inputMode=inputMode;self.inputs=inputs;self.steps=steps;self.staleReasons=staleReasons
    }
}

public enum WorkflowTemplateIdentifiers {
    public static let soloPodcast="solo_podcast"
}

public struct WorkflowInputs:Equatable {
    public let assetIDs:[String]
    public let revisionIDs:[String]
    public let annotationIDs:[String]?
    public init(assetIDs:[String]=[],revisionIDs:[String]=[],annotationIDs:[String]?=nil) {self.assetIDs=assetIDs;self.revisionIDs=revisionIDs;self.annotationIDs=annotationIDs}
    public var payload:[String:Any] {["asset_ids":assetIDs,"revision_ids":revisionIDs,"annotation_ids":annotationIDs ?? NSNull()]}
    public func addingRevisionIDs(_ identifiers:[String])->WorkflowInputs {
        WorkflowInputs(assetIDs:assetIDs,revisionIDs:Array(Set(revisionIDs+identifiers)).sorted(),annotationIDs:annotationIDs)
    }
}

public struct WorkflowGuideSnapshot:Equatable {
    public let templates:[WorkflowTemplate]
    public let workflows:[WorkflowInstance]
    public let activeWorkflowID:String?
    public let isLegacyFallback:Bool
    public var activeWorkflow:WorkflowInstance? {
        guard let activeWorkflowID else{return workflows.first}
        return workflows.first {$0.id == activeWorkflowID}
    }
    public var isActiveSoloPodcast:Bool {activeWorkflow?.isSoloPodcast == true}
    public var deliverables:[WorkflowInstance] {workflows.filter {kind(for:$0) == .deliverable}}
    public var supportingActions:[WorkflowInstance] {workflows.filter {kind(for:$0) == .supportingAction}}
    public var standaloneActions:[WorkflowInstance] {supportingActions.filter {$0.parentWorkflowID == nil}}
    public func template(for workflow:WorkflowInstance)->WorkflowTemplate? {templates.first {$0.id == workflow.templateID}}
    public func kind(for workflow:WorkflowInstance)->WorkflowTemplateKind {template(for:workflow)?.kind ?? workflow.kind}
    public func actions(parentedTo workflowID:String)->[WorkflowInstance] {supportingActions.filter {$0.parentWorkflowID == workflowID}}
    public func supportingActions(parentedTo workflowID:String)->[WorkflowInstance] {actions(parentedTo:workflowID)}
    public var nextStep:WorkflowStep? {
        let steps=activeWorkflow?.steps ?? []
        return steps.first { [.needsAttention,.current,.ready].contains($0.status) }
            ?? steps.first {$0.status != .completed}
    }
    // Completion is evidence based. The native guide deliberately does not derive a percentage.
    public var percentComplete:Int? {nil}

    public static func inputPayload(workflowID:String,inputs:WorkflowInputs)->[String:Any] {
        ["workflow_id":workflowID,"inputs":inputs.payload]
    }

    public static func parentPayload(workflowID:String,parentWorkflowID:String?)->[String:Any] {
        ["workflow_id":workflowID,"parent_workflow_id":parentWorkflowID ?? NSNull()]
    }

    public static func parse(_ raw:[String:Any]) throws -> Self {
        let templates=try parseTemplates(raw["templates"])
        var instances=try parseInstances(raw["workflow_instances"] ?? raw["instances"])
        let activeObject=raw["active_workflow"] as? [String:Any]
        if let activeObject,let parsed=try parseInstance(activeObject),!instances.contains(where:{$0.id == parsed.id}) {instances.append(parsed)}
        let activeID=(raw["active_workflow_id"] as? String) ?? (activeObject?["id"] as? String)
        if !instances.isEmpty {
            if let activeID,!instances.contains(where:{$0.id == activeID}) {throw WorkflowGuideError("The active workflow is missing.")}
            let stages=try parseSteps(raw["stages"])
            if !stages.isEmpty,let index=instances.firstIndex(where:{$0.id == activeID}) ?? (instances.isEmpty ? nil : instances.startIndex),instances[index].steps.isEmpty {
                let item=instances[index]
                instances[index]=WorkflowInstance(id:item.id,templateID:item.templateID,name:item.name,kind:item.kind,parentWorkflowID:item.parentWorkflowID,inputMode:item.inputMode,inputs:item.inputs,steps:stages,staleReasons:item.staleReasons)
            }
            return Self(templates:templates,workflows:instances,activeWorkflowID:activeID,isLegacyFallback:false)
        }
        let stages=try parseSteps(raw["stages"])
        guard !stages.isEmpty else {return Self(templates:templates,workflows:[],activeWorkflowID:nil,isLegacyFallback:false)}
        let fallback=WorkflowInstance(id:"legacy-project-workflow",templateID:"legacy",name:"Standard production",inputs:WorkflowInputs(),steps:stages,staleReasons:[])
        return Self(templates:templates,workflows:[fallback],activeWorkflowID:fallback.id,isLegacyFallback:true)
    }

    private static func parseTemplates(_ value:Any?) throws->[WorkflowTemplate] {
        guard let records=value as? [[String:Any]] else{return []}
        return try records.map {record in
            let id=try text(record["id"],"workflow template ID")
            let name=try text(record["name"] ?? record["label"],"workflow template name")
            let summary=(record["description"] as? String) ?? (record["summary"] as? String) ?? ""
            let inputs=try (record["inputs"] as? [[String:Any]] ?? []).map {input in
                let inputID=try text(input["id"] ?? input["key"],"workflow input ID")
                let label=try text(input["label"] ?? input["name"] ?? inputID,"workflow input label")
                let rawKind=(input["kind"] as? String) ?? (input["type"] as? String) ?? "text"
                let kind=WorkflowInputKind(rawValue:rawKind) ?? ((input["options"] as? [String])?.isEmpty == false ? .choice : .text)
                return WorkflowInputDefinition(id:inputID,label:label,required:input["required"] as? Bool == true,kind:kind,options:input["options"] as? [String] ?? [])
            }
            let kind:WorkflowTemplateKind
            if let rawKind=record["kind"] as? String {
                guard let parsed=WorkflowTemplateKind(rawValue:rawKind) else {throw WorkflowGuideError("Invalid workflow template kind.")}
                kind=parsed
            } else {kind = .inferred(for:id)}
            return WorkflowTemplate(id:id,name:name,summary:summary,inputs:inputs,kind:kind)
        }
    }

    private static func parseInstances(_ value:Any?) throws->[WorkflowInstance] {
        guard let records=value as? [[String:Any]] else{return []}
        return try records.compactMap(parseInstance)
    }

    private static func parseInstance(_ record:[String:Any]) throws->WorkflowInstance? {
        guard record["id"] != nil else{return nil}
        let id=try text(record["id"],"workflow ID")
        let template=(record["template_id"] as? String) ?? (record["template"] as? String) ?? "custom"
        let name=try text(record["name"] ?? record["label"] ?? "Workflow","workflow name")
        let kind:WorkflowTemplateKind
        if let rawKind=record["kind"] as? String {
            guard let parsed=WorkflowTemplateKind(rawValue:rawKind) else {throw WorkflowGuideError("Invalid workflow kind.")}
            kind=parsed
        } else {kind = .inferred(for:template)}
        let parentWorkflowID:String?
        if record["parent_workflow_id"] == nil || record["parent_workflow_id"] is NSNull {parentWorkflowID=nil}
        else {parentWorkflowID=try text(record["parent_workflow_id"],"parent workflow ID")}
        let rawInputMode=record["input_mode"] as? String ?? WorkflowInputMode.selected.rawValue
        guard let inputMode=WorkflowInputMode(rawValue:rawInputMode) else {throw WorkflowGuideError("Invalid workflow input mode.")}
        let rawInputs=(record["effective_inputs"] as? [String:Any]) ?? (record["inputs"] as? [String:Any]) ?? [:]
        let inputs=WorkflowInputs(
            assetIDs:rawInputs["asset_ids"] as? [String] ?? [],
            revisionIDs:(rawInputs["revision_ids"] as? [String]) ?? (rawInputs["output_revision_ids"] as? [String]) ?? [],
            annotationIDs:rawInputs["annotation_ids"] is NSNull ? nil : rawInputs["annotation_ids"] as? [String]
        )
        return WorkflowInstance(id:id,templateID:template,name:name,kind:kind,parentWorkflowID:parentWorkflowID,inputMode:inputMode,inputs:inputs,steps:try parseSteps(record["steps"] ?? record["stages"]),staleReasons:parseStaleReasons(record["stale_reasons"] ?? record["stale_reason"]))
    }

    private static func parseSteps(_ value:Any?) throws->[WorkflowStep] {
        guard let records=value as? [[String:Any]] else{return []}
        return try records.map {record in
            let id=try text(record["id"],"workflow step ID")
            let label=try text(record["label"] ?? record["name"],"workflow step label")
            let rawStatus=(record["status"] as? String) ?? "pending"
            let status:WorkflowStepStatus
            switch rawStatus {
            case "complete","completed","passed":status = .completed
            case "ready":status = .ready
            case "current","in_progress","active":status = .current
            case "blocked":status = .blocked
            case "stale","failed","needs_review","needs_attention":status = .needsAttention
            case "pending":status = .ready
            default:status = .upcoming
            }
            let destination=StudioDestination(title:(record["destination"] as? String) ?? destinationTitle(for:id))
            var staleReasons=parseStaleReasons(record["stale_reasons"] ?? record["stale_reason"])
            if status == .needsAttention,staleReasons.isEmpty {
                staleReasons=[WorkflowStaleReason(code:"evidence_stale",detail:"Saved evidence no longer matches the current workflow inputs or required files.")]
            }
            return WorkflowStep(id:id,label:label,detail:(record["detail"] as? String) ?? (record["instructions"] as? String) ?? "",status:status,destination:destination,prompt:record["prompt"] as? String,staleReasons:staleReasons)
        }
    }

    private static func parseStaleReasons(_ value:Any?)->[WorkflowStaleReason] {
        if let values=value as? [[String:Any]] {
            return values.compactMap {item in
                guard let detail=(item["detail"] ?? item["message"] ?? item["label"]) as? String,!detail.isEmpty else{return nil}
                return WorkflowStaleReason(code:(item["code"] ?? item["id"] ?? item["type"]) as? String ?? "evidence_stale",detail:detail)
            }
        }
        if let values=value as? [String] {return values.filter{!$0.isEmpty}.map{WorkflowStaleReason(code:"evidence_stale",detail:$0)}}
        if let value=value as? String,!value.isEmpty {return [WorkflowStaleReason(code:"evidence_stale",detail:value)]}
        return []
    }

    private static func destinationTitle(for stepID:String)->String {
        switch stepID {
        case "intake","brief":return "Brief"
        case "sources":return "Sources"
        case "source_understanding","editorial_strategy":return "Workflow Guide"
        case "edit","render","revisions":return "Revisions"
        case "final_review","review","feedback":return "Feedback"
        default:return "Workflow Guide"
        }
    }

    private static func text(_ value:Any?,_ label:String)throws->String {
        guard let value=value as? String,!value.trimmingCharacters(in:.whitespacesAndNewlines).isEmpty else {throw WorkflowGuideError("Invalid \(label).")}
        return value
    }
}

public struct WorkflowGuideError:LocalizedError {
    public let errorDescription:String?
    public init(_ message:String) {errorDescription=message}
}
