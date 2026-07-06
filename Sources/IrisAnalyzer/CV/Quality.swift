import Foundation

/// Avaliação de qualidade multi-fator (0–100) baseada na literatura de
/// reconhecimento de íris (Daugman 2004; Kalka et al.). Cada fator é 0–1.
enum Quality {

    /// `normalized` é o anel desenrolado; `mask` marca pixels válidos.
    /// `full` é a imagem original em cinza; `seg` a segmentação.
    static func assess(full: GrayImage, seg: IrisSegmentation,
                       normalized: GrayImage, mask: [Bool],
                       texture: TextureFeatures) -> QualityAssessment {

        // 1) Foco: nitidez normalizada (sigmoide para 0–1)
        let focus = sigmoid(texture.sharpness, mid: 120, slope: 0.02)

        // 2) Oclusão: proporção de máscara inválida (pálpebra/cílio/reflexo)
        let validFrac = Double(mask.filter { $0 }.count) / Double(max(1, mask.count))
        let occlusion = validFrac   // já é "quanto está visível"

        // 3) Reflexo especular: quanto menos, melhor
        let reflection = clamp(1.0 - texture.specularRatio * 8.0)

        // 4) Off-angle: excentricidade a partir de concentricidade pupila/íris
        let dx = seg.pupil.cx - seg.iris.cx
        let dy = seg.pupil.cy - seg.iris.cy
        let offset = hypot(dx, dy) / max(1, seg.iris.r)
        let offAngle = clamp(1.0 - offset * 2.0)

        // 5) Dilatação: penaliza razões pupilares fora da faixa fisiológica
        let ratio = seg.pupillaryRatio
        let dilation: Double = {
            if ratio < 0.2 || ratio > 0.7 { return 0.4 }
            // ótimo em torno de 0.3–0.5
            let d = abs(ratio - 0.4)
            return clamp(1.0 - d * 2.0)
        }()

        // 6) Tamanho: raio da íris em pixels (mais pixels = melhor até saturar)
        let size = sigmoid(seg.iris.r, mid: 70, slope: 0.04)

        // Combinação ponderada (pesos típicos da literatura)
        let w: [Double] = [0.30, 0.20, 0.15, 0.15, 0.10, 0.10]
        let f = [focus, occlusion, reflection, offAngle, dilation, size]
        let score = zip(w, f).map(*).reduce(0, +) * 100

        return QualityAssessment(
            focus: focus, occlusion: occlusion, reflection: reflection,
            offAngle: offAngle, dilation: dilation, size: size,
            score: clamp(score / 100) * 100
        )
    }

    private static func sigmoid(_ x: Double, mid: Double, slope: Double) -> Double {
        1.0 / (1.0 + exp(-slope * (x - mid)))
    }
    private static func clamp(_ x: Double) -> Double { max(0, min(1, x)) }
}

/// Biometria estimada a partir de HVID (Horizontal Visible Iris Diameter) médio.
enum BiometricsEstimator {
    /// HVID médio populacional ≈ 11.7 mm — usado como escala.
    static let hvidMM = 11.7

    static func estimate(seg: IrisSegmentation) -> Biometrics {
        let mmPerPixel = hvidMM / (2 * max(1, seg.iris.r))
        let irisMM = 2 * seg.iris.r * mmPerPixel
        let pupilMM = 2 * seg.pupil.r * mmPerPixel
        let ratio = seg.pupillaryRatio
        let classe: String
        switch ratio {
        case ..<0.25: classe = "miose (pupila contraída)"
        case 0.25..<0.55: classe = "normal"
        default: classe = "midríase (pupila dilatada)"
        }
        return Biometrics(irisDiameterMM: irisMM, pupilDiameterMM: pupilMM,
                          pupillaryRatio: ratio, classificacao: classe)
    }
}
