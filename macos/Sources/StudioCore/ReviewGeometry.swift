import Foundation
import CoreGraphics
public enum ReviewGeometry {
    public static func videoRect(container: CGSize, video: CGSize) -> CGRect {
        guard video.width > 0, video.height > 0, container.width > 0, container.height > 0 else { return .zero }
        let scale = min(container.width / video.width, container.height / video.height)
        let size = CGSize(width:video.width * scale,height:video.height * scale)
        return CGRect(x:(container.width-size.width)/2,y:(container.height-size.height)/2,width:size.width,height:size.height)
    }
    public static func normalizedPoint(_ point: CGPoint, in bounds: CGRect) -> CGPoint? {
        guard bounds.width > 0, bounds.height > 0, point.x >= bounds.minX, point.x <= bounds.maxX, point.y >= bounds.minY, point.y <= bounds.maxY else { return nil }
        return CGPoint(x:(point.x-bounds.minX)/bounds.width,y:(point.y-bounds.minY)/bounds.height)
    }
    public static func selection(from start: CGPoint, to end: CGPoint, in bounds: CGRect) -> CGRect? {
        guard let a=normalizedPoint(start,in:bounds), let b=normalizedPoint(end,in:bounds) else {return nil}
        let r=CGRect(x:min(a.x,b.x),y:min(a.y,b.y),width:abs(a.x-b.x),height:abs(a.y-b.y))
        return r.width > 0.002 && r.height > 0.002 ? r : nil
    }
}
