import SwiftUI

struct IrisAnalyzerApp: App {
    @StateObject private var auth = Auth()

    var body: some Scene {
        WindowGroup {
            Group {
                if auth.isAuthenticated {
                    RootView().frame(minWidth: 1000, minHeight: 660)
                } else {
                    LoginView().frame(minWidth: 460, minHeight: 540)
                }
            }
            .environmentObject(auth)
            .tint(Brand.accent)
        }
        .windowStyle(.titleBar)
        .windowToolbarStyle(.unified(showsTitle: true))
        .defaultSize(width: 1180, height: 780)
    }
}
