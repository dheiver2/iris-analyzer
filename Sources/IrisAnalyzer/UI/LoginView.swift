import SwiftUI

/// Tela de login no estilo macOS nativo moderno (material translúcido, controles
/// do sistema). Credenciais padrão: admin / admin (ver `Auth`).
struct LoginView: View {
    @EnvironmentObject private var auth: Auth
    @State private var user = ""
    @State private var pass = ""
    @FocusState private var focus: Field?
    private enum Field { case user, pass }

    var body: some View {
        ZStack {
            VisualEffectBackground(material: .underWindowBackground).ignoresSafeArea()
            RadialGradient(colors: [Brand.accent.opacity(0.22), .clear],
                           center: .top, startRadius: 10, endRadius: 460)
                .ignoresSafeArea()

            VStack(spacing: 20) {
                IrisMark(size: 68)
                    .shadow(color: Brand.accent.opacity(0.4), radius: 18)

                VStack(spacing: 3) {
                    Text("Iris Analyzer").font(.title2.weight(.bold))
                    Text("Acesso restrito").font(.callout).foregroundStyle(.secondary)
                }

                VStack(spacing: 12) {
                    TextField("Usuário", text: $user)
                        .textFieldStyle(.roundedBorder)
                        .focused($focus, equals: .user)
                        .onSubmit { focus = .pass }
                    SecureField("Senha", text: $pass)
                        .textFieldStyle(.roundedBorder)
                        .focused($focus, equals: .pass)
                        .onSubmit(submit)

                    if let err = auth.error {
                        Label(err, systemImage: "exclamationmark.circle.fill")
                            .font(.caption).foregroundStyle(Brand.red)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    Button(action: submit) {
                        Text("Entrar").frame(maxWidth: .infinity)
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                    .tint(Brand.accent)
                    .keyboardShortcut(.defaultAction)
                    .padding(.top, 2)
                }
                .frame(width: 280)

                Text("Ferramenta educacional de bem-estar — não é dispositivo médico.")
                    .font(.caption2).foregroundStyle(.secondary)
                    .multilineTextAlignment(.center).frame(width: 260)
            }
            .padding(34)
            .frame(width: 360)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 18, style: .continuous)
                .strokeBorder(Brand.border, lineWidth: 1))
            .shadow(color: .black.opacity(0.25), radius: 30, y: 12)
        }
        .onAppear { focus = .user }
    }

    private func submit() { auth.login(user: user, pass: pass) }
}
