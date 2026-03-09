// swift-tools-version: 5.10
import PackageDescription

let package = Package(
    name: "Clawzy",
    platforms: [.iOS(.v17)],
    products: [
        .library(name: "Clawzy", targets: ["Clawzy"]),
    ],
    dependencies: [
        .package(url: "https://github.com/kishikawakatsumi/KeychainAccess.git", from: "4.2.2"),
    ],
    targets: [
        .target(
            name: "Clawzy",
            dependencies: ["KeychainAccess"],
            path: "."
        ),
    ]
)
