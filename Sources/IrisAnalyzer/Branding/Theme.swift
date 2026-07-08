import SwiftUI

/// Identidade visual no padrão de app macOS nativo moderno: cores **semânticas
/// adaptativas** (claro/escuro automático) + materiais translúcidos do sistema,
/// com um acento índigo/violeta (temático da íris) como `tint`.
enum Brand {
    // Acentos da marca
    static let accent    = Color(hex: 0x7C5CFF)   // índigo-violeta (tint principal)
    static let accent2   = Color(hex: 0x22C1A6)   // teal — positivo / qualidade alta
    static let amber     = Color(hex: 0xD9A521)   // atenção
    static let red       = Color(hex: 0xE0524D)   // erro / qualidade baixa

    // Cores semânticas (adaptam a claro/escuro)
    static let text      = Color.primary
    static let muted     = Color.secondary
    static let faint     = Color.secondary.opacity(0.65)
    static let bg        = Color(nsColor: .windowBackgroundColor)
    static let bgElev    = Color(nsColor: .underPageBackgroundColor)
    static let card      = Color(nsColor: .controlBackgroundColor)
    static let border    = Color(nsColor: .separatorColor)

    /// Gradiente da marca (header, logo, botão primário).
    static let brandGradient = LinearGradient(
        colors: [Color(hex: 0x8B7CFF), Color(hex: 0x6B5CE0), Color(hex: 0x4E86E0)],
        startPoint: .topLeading, endPoint: .bottomTrailing
    )

    /// Cor de qualidade em função do score 0–100.
    static func qualityColor(_ score: Double) -> Color {
        switch score {
        case 70...:   return accent2
        case 45..<70: return amber
        default:      return red
        }
    }
}

extension Color {
    init(hex: UInt32, alpha: Double = 1) {
        self.init(.sRGB,
                  red:   Double((hex >> 16) & 0xFF) / 255,
                  green: Double((hex >> 8) & 0xFF) / 255,
                  blue:  Double(hex & 0xFF) / 255,
                  opacity: alpha)
    }
}

// MARK: - Materiais e componentes nativos reutilizáveis

extension View {
    /// Rótulo de seção discreto (caption em maiúsculas).
    func sectionLabel() -> some View {
        self.font(.caption2.weight(.semibold))
            .tracking(0.6)
            .foregroundStyle(.secondary)
            .textCase(.uppercase)
    }
}

/// Efeito de material translúcido nativo (NSVisualEffectView) — usado em painéis.
struct VisualEffectBackground: NSViewRepresentable {
    var material: NSVisualEffectView.Material = .sidebar
    var blending: NSVisualEffectView.BlendingMode = .behindWindow
    func makeNSView(context: Context) -> NSVisualEffectView {
        let v = NSVisualEffectView()
        v.material = material
        v.blendingMode = blending
        v.state = .active
        return v
    }
    func updateNSView(_ v: NSVisualEffectView, context: Context) {
        v.material = material
        v.blendingMode = blending
    }
}
