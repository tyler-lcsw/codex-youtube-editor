// swift-tools-version: 6.3
import PackageDescription
let package = Package(name: "CodexStudio", platforms: [.macOS(.v14)], products: [
    .executable(name: "CodexStudio", targets: ["Studio"]),
    .library(name: "StudioCore", targets: ["StudioCore"])
], targets: [
    .target(name: "StudioCore"),
    .executableTarget(name: "Studio", dependencies: ["StudioCore"]),
    .executableTarget(name: "StudioProbe", dependencies: ["StudioCore"]),
    .executableTarget(name: "StudioChecks", dependencies: ["StudioCore"], path: "Tests/StudioCoreTests")
], swiftLanguageModes: [.v5])
