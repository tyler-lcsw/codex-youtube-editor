import Foundation
import CoreGraphics
public struct AnnotationContext {
    public let timeMS:Int
    public let endMS:Int?
    public let rect:CGRect?
    public let transcriptIDs:[String]
    public init(_ record:[String:Any]) {
        timeMS=record["time_ms"] as? Int ?? 0;endMS=record["end_ms"] as? Int
        transcriptIDs=record["transcript_ids"] as? [String] ?? []
        if let r=record["rect"] as? [String:Double],let x=r["x"],let y=r["y"],let width=r["width"],let height=r["height"] {rect=CGRect(x:x,y:y,width:width,height:height)}else{rect=nil}
    }
}
public struct AnnotationDrafts {
    private var revisions=[String:String](),notes=[String:String]()
    public init() {}
    public func revision(for id:String,fallback:String?)->String {revisions[id] ?? fallback ?? ""}
    public func note(for id:String)->String {notes[id] ?? ""}
    public mutating func setRevision(_ revision:String,for id:String) {revisions[id]=revision}
    public mutating func setNote(_ note:String,for id:String) {notes[id]=note}
}
