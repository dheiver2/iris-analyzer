import SwiftUI

struct IrisAnalyzerApp: App {
    @StateObject private var auth = Auth()

    var body: some Scene {
        WindowGroup {
            Group {
                if auth.isAuthenticated {
                    RootView()
                        .frame(minWidth: 1080, minHeight: 720)
                } else {
                    LoginView()
                        .frame(minWidth: 480, minHeight: 560)
                }
            }
            .environmentObject(auth)
            .preferredColorScheme(.dark)
        }
        .windowStyle(.hiddenTitleBar)
        .defaultSize(width: 1160, height: 760)
    }
}
