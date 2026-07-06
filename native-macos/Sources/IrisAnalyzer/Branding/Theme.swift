import SwiftUI

/// Identidade visual do Iris Analyzer — tema escuro refinado com acento índigo/violeta
/// (temático da íris) e um secundário ciano para estados positivos/qualidade.
enum Brand {
    // Superfícies
    static let bg        = Color(hex: 0x0B0B0C)   // fundo principal
    static let bgElev    = Color(hex: 0x111114)   // fundo elevado
    static let card      = Color(hex: 0x151519)   // cartões / painéis
    static let cardHi    = Color(hex: 0x1C1C22)   // cartão em destaque
    static let border    = Color(hex: 0x26262C)   // bordas sutis
    static let borderHi  = Color(hex: 0x3A3A44)   // borda em foco

    // Texto
    static let text      = Color(hex: 0xF2F2F5)   // primário
    static let muted     = Color(hex: 0x8A8A92)   // secundário
    static let faint     = Color(hex: 0x55555C)   // terciário

    // Acentos (rebranding: substitui o branco por índigo/violeta)
    static let accent    = Color(hex: 0x8B7CFF)   // índigo-violeta (íris)
    static let accentDim = Color(hex: 0x6B5CE0)
    static let cyan      = Color(hex: 0x54E0C7)   // positivo / qualidade alta
    static let amber     = Color(hex: 0xF0C060)   // atenção
    static let red       = Color(hex: 0xF06A6A)   // erro / qualidade baixa

    // Gradiente da marca (usado em header e botão primário)
    static let brandGradient = LinearGradient(
        colors: [Color(hex: 0x8B7CFF), Color(hex: 0x6B5CE0), Color(hex: 0x4E86E0)],
        startPoint: .leading, endPoint: .trailing
    )

    static let font = "SF Pro Display"

    /// Cor de qualidade em função do score 0–100.
    static func qualityColor(_ score: Double) -> Color {
        switch score {
        case 70...:  return cyan
        case 45..<70: return amber
        default:     return red
        }
    }
}

extension Color {
    init(hex: UInt32, alpha: Double = 1) {
        self.init(
            .sRGB,
            red:   Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue:  Double(hex & 0xFF) / 255,
            opacity: alpha
        )
    }
}

// MARK: - Componentes de estilo reutilizáveis

/// Cartão padrão da UI (fundo, borda, cantos arredondados).
struct CardModifier: ViewModifier {
    var highlighted = false
    func body(content: Content) -> some View {
        content
            .background(highlighted ? Brand.cardHi : Brand.card)
            .overlay(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .stroke(highlighted ? Brand.borderHi : Brand.border, lineWidth: 1)
            )
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }
}

extension View {
    func brandCard(highlighted: Bool = false) -> some View {
        modifier(CardModifier(highlighted: highlighted))
    }

    /// Rótulo de seção em caixa alta espaçada (estilo do app original, mais polido).
    func sectionLabel() -> some View {
        self.font(.system(size: 10, weight: .semibold))
            .tracking(1.2)
            .foregroundStyle(Brand.muted)
            .textCase(.uppercase)
    }
}

/// Botão primário com gradiente da marca.
struct PrimaryButtonStyle: ButtonStyle {
    var enabled = true
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 13, weight: .semibold))
            .foregroundStyle(.white)
            .padding(.vertical, 11).padding(.horizontal, 18)
            .frame(maxWidth: .infinity)
            .background(
                Group {
                    if enabled { Brand.brandGradient } else { Color(hex: 0x1A1A1E) }
                }
            )
            .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
            .opacity(configuration.isPressed ? 0.82 : 1)
            .foregroundStyle(enabled ? .white : Brand.faint)
    }
}

/// Botão secundário (contorno).
struct GhostButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 13, weight: .medium))
            .foregroundStyle(Brand.text)
            .padding(.vertical, 11).padding(.horizontal, 18)
            .frame(maxWidth: .infinity)
            .overlay(
                RoundedRectangle(cornerRadius: 10, style: .continuous)
                    .stroke(Brand.border, lineWidth: 1)
            )
            .opacity(configuration.isPressed ? 0.7 : 1)
    }
}
