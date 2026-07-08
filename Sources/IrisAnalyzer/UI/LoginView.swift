import SwiftUI

/// Tela de login rebrandizada (tema escuro + acento índigo). Credenciais
/// padrão: admin / admin (ver `Auth`).
struct LoginView: View {
    @EnvironmentObject private var auth: Auth
    @State private var user = ""
    @State private var pass = ""
    @FocusState private var focus: Field?
    private enum Field { case user, pass }

    var body: some View {
        ZStack {
            Brand.bg.ignoresSafeArea()
            // brilho radial de fundo
            RadialGradient(colors: [Brand.accent.opacity(0.18), .clear],
                           center: .top, startRadius: 10, endRadius: 420)
                .ignoresSafeArea()

            VStack(spacing: 22) {
                logo
                VStack(spacing: 3) {
                    Text("IRIS ANALYZER")
                        .font(.system(size: 20, weight: .bold)).tracking(2)
                        .foregroundStyle(Brand.text)
                    Text("acesso restrito")
                        .font(.system(size: 11)).tracking(0.5)
                        .foregroundStyle(Brand.muted)
                }

                VStack(spacing: 12) {
                    field(icon: "person", placeholder: "Usuário", text: $user,
                          secure: false, field: .user, next: .pass)
                    field(icon: "lock", placeholder: "Senha", text: $pass,
                          secure: true, field: .pass, next: nil)

                    if let err = auth.error {
                        Label(err, systemImage: "exclamationmark.circle.fill")
                            .font(.system(size: 11)).foregroundStyle(Brand.red)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    Button(action: submit) {
                        Label("Entrar", systemImage: "arrow.right.circle.fill")
                    }
                    .buttonStyle(PrimaryButtonStyle())
                    .padding(.top, 4)
                }
                .frame(width: 300)

                Text("Ferramenta educacional de bem-estar — não é dispositivo médico.")
                    .font(.system(size: 9)).foregroundStyle(Brand.faint)
                    .multilineTextAlignment(.center).frame(width: 280)
            }
            .padding(36)
            .frame(width: 380)
            .brandCard(highlighted: true)
        }
        .onAppear { focus = .user }
    }

    private var logo: some View {
        ZStack {
            SwiftUI.Circle().fill(Brand.brandGradient).frame(width: 64, height: 64)
                .shadow(color: Brand.accent.opacity(0.5), radius: 20)
            SwiftUI.Circle().stroke(Brand.bg, lineWidth: 6).frame(width: 30, height: 30)
            SwiftUI.Circle().fill(Brand.bg).frame(width: 18, height: 18)
            SwiftUI.Circle().fill(.white.opacity(0.9)).frame(width: 6, height: 6)
                .offset(x: -4, y: -4)
        }
    }

    private func field(icon: String, placeholder: String, text: Binding<String>,
                       secure: Bool, field: Field, next: Field?) -> some View {
        HStack(spacing: 10) {
            Image(systemName: icon).font(.system(size: 13))
                .foregroundStyle(Brand.muted).frame(width: 16)
            Group {
                if secure {
                    SecureField(placeholder, text: text).onSubmit(submit)
                } else {
                    TextField(placeholder, text: text)
                        .onSubmit { if next != nil { focus = next } }
                }
            }
            .textFieldStyle(.plain)
            .font(.system(size: 13))
            .focused($focus, equals: field)
        }
        .padding(.horizontal, 12).padding(.vertical, 11)
        .background(Brand.bgElev)
        .clipShape(RoundedRectangle(cornerRadius: 9))
        .overlay(RoundedRectangle(cornerRadius: 9)
            .stroke(focus == field ? Brand.accent : Brand.border, lineWidth: 1))
    }

    private func submit() {
        auth.login(user: user, pass: pass)
    }
}
