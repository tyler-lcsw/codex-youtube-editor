import Foundation
import CoreGraphics

import StudioCore
final class ReviewTests {
    func testLetterboxCoordinatesAndReverseDrag() throws {
        let bounds = ReviewGeometry.videoRect(container: CGSize(width:800,height:600), video: CGSize(width:1920,height:1080))
        XCTAssertEqual(bounds, CGRect(x:0,y:75,width:800,height:450))
        XCTAssertNil(ReviewGeometry.normalizedPoint(CGPoint(x:400,y:50), in:bounds))
        XCTAssertEqual(ReviewGeometry.normalizedPoint(CGPoint(x:400,y:300), in:bounds), CGPoint(x:0.5,y:0.5))
        let rect = try XCTUnwrap(ReviewGeometry.selection(from: CGPoint(x:600,y:412.5), to: CGPoint(x:200,y:187.5), in:bounds))
        XCTAssertEqual(rect, CGRect(x:0.25,y:0.25,width:0.5,height:0.5))
    }
}

func testAnnotationDraftsAndSavedContextStayIndependent() {
    var drafts=AnnotationDrafts()
    drafts.setRevision("revision-a",for:"note-a")
    drafts.setRevision("revision-b",for:"note-b")
    drafts.setNote("Correction A",for:"note-a")
    XCTAssertEqual(drafts.revision(for:"note-b",fallback:nil),"revision-b")
    XCTAssertEqual(drafts.note(for:"note-b"),"")
    let context=AnnotationContext(["time_ms":1200,"end_ms":2400,"rect":["x":0.1,"y":0.2,"width":0.3,"height":0.4],"transcript_ids":["word-1"]])
    XCTAssertEqual(context.timeMS,1200);XCTAssertEqual(context.endMS,2400)
    XCTAssertEqual(context.rect,CGRect(x:0.1,y:0.2,width:0.3,height:0.4))
    XCTAssertEqual(context.transcriptIDs,["word-1"])
}
