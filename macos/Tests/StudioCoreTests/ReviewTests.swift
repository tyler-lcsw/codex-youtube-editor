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
