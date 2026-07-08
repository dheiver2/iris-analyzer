import SwiftUI

/// Cartão de resultados de um olho no estilo nativo (GroupBox + grid de métricas).
struct EyeCardView: View {
    let analysis: EyeAnalysis

    var body: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 10) {
                    thumb(analysis.zoomImage, caption: "Íris")
                    thumb(analysis.heatmapImage, caption: "Mapa de calor")
                    thumb(analysis.normalizedImage, caption: "Normalizada")
                }

                Divider()

                Grid(alignment: .leading, horizontalSpacing: 24, verticalSpacing: 8) {
                    GridRow {
                        metric("Cor", analysis.color.descricao)
                        metric("Íris", String(format: "%.1f mm", analysis.biometrics.irisDiameterMM))
                    }
                    GridRow {
                        metric("Pupila", String(format: "%.1f mm", analysis.biometrics.pupilDiameterMM))
                        metric("Razão P/I", String(format: "%.2f", analysis.biometrics.pupillaryRatio))
                    }
                    GridRow {
                        metric("Classe", analysis.biometrics.classificacao)
                        metric("Nitidez", String(format: "%.0f", analysis.texture.sharpness))
                    }
                    GridRow {
                        metric("GLCM contraste", String(format: "%.2f", analysis.texture.glcmContrast))
                        metric("Gabor", String(format: "%.0f", analysis.texture.gaborEnergy))
                    }
                }

                ForEach(analysis.avisos, id: \.self) { aviso in
                    Label(aviso, systemImage: "exclamationmark.triangle.fill")
                        .font(.caption).foregroundStyle(Brand.amber)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(6)
        } label: {
            HStack {
                Label("Olho \(analysis.eye.rawValue)", systemImage: "eye.fill")
                    .font(.headline)
                Spacer()
                qualityBadge
            }
        }
    }

    private var qualityBadge: some View {
        let s = analysis.quality.score
        return HStack(spacing: 5) {
            SwiftUI.Circle().fill(Brand.qualityColor(s)).frame(width: 7, height: 7)
            Text("\(Int(s))/100")
                .font(.caption.weight(.semibold).monospacedDigit())
                .foregroundStyle(Brand.qualityColor(s))
        }
        .padding(.horizontal, 9).padding(.vertical, 3)
        .background(Capsule().fill(Brand.qualityColor(s).opacity(0.15)))
    }

    private func thumb(_ image: CGImage?, caption: String) -> some View {
        VStack(spacing: 5) {
            Group {
                if let image {
                    Image(decorative: image, scale: 1, orientation: .up)
                        .resizable().aspectRatio(contentMode: .fill)
                } else {
                    Rectangle().fill(Brand.bgElev)
                }
            }
            .frame(width: 88, height: 88)
            .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
            .overlay(RoundedRectangle(cornerRadius: 8, style: .continuous)
                .strokeBorder(Brand.border, lineWidth: 1))
            Text(caption).font(.caption2).foregroundStyle(.secondary)
        }
    }

    private func metric(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(label.uppercased())
                .font(.system(size: 9, weight: .semibold)).tracking(0.4)
                .foregroundStyle(.secondary)
            Text(value).font(.callout).foregroundStyle(.primary)
        }
    }
}
