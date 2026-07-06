// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "IrisAnalyzer",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "IrisAnalyzer",
            path: "Sources/IrisAnalyzer"
        )
    ]
)
