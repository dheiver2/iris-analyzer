import SwiftUI

/// Autenticação simples de acesso ao app.
///
/// ⚠️ As credenciais padrão são **admin / admin** e estão em texto no código —
/// adequado apenas para um gate local de demonstração. Para produção/edital,
/// troque por armazenamento no Keychain com hash (ver `expectedHash`) e,
/// idealmente, um provedor de identidade.
@MainActor
final class Auth: ObservableObject {
    @Published var isAuthenticated = false
    @Published var error: String?

    /// Credenciais padrão (podem ser sobrescritas por variáveis de ambiente
    /// IRIS_USER / IRIS_PASS sem recompilar).
    static var expectedUser: String {
        ProcessInfo.processInfo.environment["IRIS_USER"] ?? "admin"
    }
    static var expectedPass: String {
        ProcessInfo.processInfo.environment["IRIS_PASS"] ?? "admin"
    }

    func login(user: String, pass: String) {
        let u = user.trimmingCharacters(in: .whitespaces)
        if u == Self.expectedUser && pass == Self.expectedPass {
            isAuthenticated = true
            error = nil
        } else {
            error = "Usuário ou senha inválidos."
        }
    }

    func logout() {
        isAuthenticated = false
        error = nil
    }
}
