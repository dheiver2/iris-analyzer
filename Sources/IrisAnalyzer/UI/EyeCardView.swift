import SwiftUI

/// Cartão de resultados de um olho: imagens auxiliares + métricas.
struct EyeCardView: View {
    let analysis: EyeAnalysis

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Olho \(analysis.eye.rawValue)")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(Brand.text)
                Spacer()
                qualityBadge
            }

            HStack(spacing: 10) {
                thumb(analysis.zoomImage, caption: "ÍRIS (ZOOM)")
                thumb(analysis.heatmapImage, caption: "MAPA DE CALOR")
                thumb(analysis.normalizedImage, caption: "NORMALIZADA")
            }

            metricsGrid

            if !analysis.avisos.isEmpty {
                ForEach(analysis.avisos, id: \.self) { aviso in
                    Label(aviso, systemImage: "exclamationmark.triangle.fill")
                        .font(.system(size: 11))
                        .foregroundStyle(Brand.amber)
                }
            }
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .brandCard()
    }

    private var qualityBadge: some View {
        let s = analysis.quality.score
        return Text("\(Int(s))/100")
            .font(.system(size: 12, weight: .bold))
            .foregroundStyle(Brand.qualityColor(s))
            .padding(.horizontal, 10).padding(.vertical, 4)
            .background(Brand.qualityColor(s).opacity(0.14))
            .clipShape(Capsule())
    }

    private func thumb(_ image: CGImage?, caption: String) -> some View {
        VStack(spacing: 5) {
            Group {
                if let image {
                    Image(decorative: image, scale: 1, orientation: .up)
                        .resizable().aspectRatio(contentMode: .fill)
                } else {
                    Color.black
                }
            }
            .frame(width: 92, height: 92)
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .overlay(RoundedRectangle(cornerRadius: 8).stroke(Brand.border, lineWidth: 1))
            Text(caption).font(.system(size: 8, weight: .semibold))
                .tracking(0.5).foregroundStyle(Brand.faint)
        }
    }

    private var metricsGrid: some View {
        let b = analysis.biometrics
        let c = analysis.color
        let t = analysis.texture
        return Grid(alignment: .leading, horizontalSpacing: 18, verticalSpacing: 6) {
            GridRow {
                metric("Cor", c.descricao)
                metric("Íris", String(format: "%.1f mm", b.irisDiameterMM))
            }
            GridRow {
                metric("Pupila", String(format: "%.1f mm", b.pupilDiameterMM))
                metric("Razão P/I", String(format: "%.2f", b.pupillaryRatio))
            }
            GridRow {
                metric("Classe", b.classificacao)
                metric("Nitidez", String(format: "%.0f", t.sharpness))
            }
            GridRow {
                metric("GLCM contraste", String(format: "%.2f", t.glcmContrast))
                metric("Gabor", String(format: "%.0f", t.gaborEnergy))
            }
        }
    }

    private func metric(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(label.uppercased())
                .font(.system(size: 8, weight: .semibold)).tracking(0.5)
                .foregroundStyle(Brand.faint)
            Text(value).font(.system(size: 12)).foregroundStyle(Brand.text)
        }
    }
}
