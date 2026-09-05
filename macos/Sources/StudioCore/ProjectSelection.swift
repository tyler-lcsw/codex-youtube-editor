import Foundation
@MainActor public final class ProjectSelection {
    public private(set) var path=""
    public private(set) var data=[String:Any]()
    public private(set) var loading=false
    public init() {}
    public func open(_ candidate:String,using bridge:EngineBridge,createTitle:String?=nil) async throws {
        guard !loading else {throw StudioError("A project change is already in progress")}
        loading=true;defer{loading=false}
        let params:[String:Any]=createTitle.map{["title":$0]} ?? [:]
        let loaded=try await bridge.request(createTitle==nil ? "open" : "create",project:candidate,params:params)
        // Publish identity and contents together only after a successful read/create.
        path=candidate;data=loaded
    }
}
