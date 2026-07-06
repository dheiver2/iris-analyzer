import Foundation
import CoreGraphics

/// Orquestra o pipeline completo de análise de um quadro:
/// Vision → Daugman → normalização → features → qualidade → biometria.
enum AnalysisPipeline {

    static func analyze(cgImage: CGImage) -> FrameAnalysis {
        guard let gray = GrayImage(cgImage: cgImage) else { return .empty }
        let detected = IrisDetector.detect(in: cgImage)

        var eyes: [EyeAnalysis] = []
        for det in detected {
            if let analysis = analyzeEye(det, gray: gray, cgImage: cgImage) {
                eyes.append(analysis)
            }
        }

        let (comparacoes, confianca) = compare(eyes)
        return FrameAnalysis(timestamp: Date(), capturedImage: cgImage,
                             eyes: eyes, comparacoes: comparacoes, confianca: confianca)
    }

    private static func analyzeEye(_ det: DetectedEye, gray: GrayImage,
                                   cgImage: CGImage) -> EyeAnalysis? {
        // 1) Refina a borda da íris com Daugman em torno do centro do olho
        let rGuess = det.irisRadiusGuess
        guard rGuess > 6 else { return nil }
        let iris = Daugman.refine(
            gray, cx0: Double(det.eyeCenter.x), cy0: Double(det.eyeCenter.y),
            rMin: rGuess * 0.7, rMax: rGuess * 1.35, searchRadius: 6, samples: 180
        )
        // 2) Pupila real
        let pupil = PupilFinder.detect(gray, irisGuess: iris)
        let seg = IrisSegmentation(iris: iris, pupil: pupil)

        // 3) Normalização polar
        let (normalized, mask) = Normalization.unwrap(gray, seg: seg)

        // 4) Features de textura
        let glcm = Texture.glcm(normalized)
        let texture = TextureFeatures(
            gaborEnergy: Texture.gaborEnergy(normalized),
            lbpUniformity: Texture.lbpUniformity(normalized),
            glcmContrast: glcm.contrast, glcmEnergy: glcm.energy,
            glcmHomogeneity: glcm.homogeneity, glcmCorrelation: glcm.correlation,
            sharpness: Texture.sharpness(normalized),
            specularRatio: Texture.specularRatio(normalized)
        )

        // 5) Cor
        let color = ColorAnalysis.meanLab(cgImage: cgImage, seg: seg)

        // 6) Qualidade
        let quality = Quality.assess(full: gray, seg: seg,
                                     normalized: normalized, mask: mask, texture: texture)

        // 7) Biometria
        let bio = BiometricsEstimator.estimate(seg: seg)

        // 8) Imagens auxiliares (zoom + heatmap)
        let zoom = makeZoom(gray, seg: seg)
        let heat = Heatmap.make(normalized)

        // 9) Avisos
        var avisos: [String] = []
        if quality.score < 45 { avisos.append("Qualidade baixa — recapture com mais foco/luz.") }
        if texture.specularRatio > 0.03 { avisos.append("Reflexo especular detectado.") }
        if bio.pupillaryRatio > 0.7 { avisos.append("Pupila muito dilatada.") }

        return EyeAnalysis(
            eye: det.eye, segmentation: seg, color: color, texture: texture,
            quality: quality, biometrics: bio,
            normalizedImage: normalized.cgImage(), zoomImage: zoom,
            heatmapImage: heat, avisos: avisos
        )
    }

    private static func makeZoom(_ gray: GrayImage, seg: IrisSegmentation) -> CGImage? {
        let r = seg.iris.r
        let x = Int(seg.iris.cx - r), y = Int(seg.iris.cy - r)
        return gray.crop(x: x, y: y, w: Int(2 * r), h: Int(2 * r)).cgImage()
    }

    /// Comparação entre os dois olhos: simetria e heterocromia.
    private static func compare(_ eyes: [EyeAnalysis]) -> (comparacoes: [String], confianca: Double) {
        guard eyes.count == 2 else {
            let conf = eyes.first.map { $0.quality.score / 100 } ?? 0
            return (["Apenas um olho analisado."], conf)
        }
        var out: [String] = []
        let a = eyes[0], b = eyes[1]

        let ratioDiff = abs(a.biometrics.pupillaryRatio - b.biometrics.pupillaryRatio)
        out.append(String(format: "Simetria pupilar: diferença de razão %.2f %@",
                          ratioDiff, ratioDiff < 0.1 ? "(simétrica)" : "(assimétrica)"))

        // Heterocromia só quando a CLASSIFICAÇÃO de cor difere E há distância
        // grande em Lab — evita falso-positivo por reflexo/iluminação assimétrica.
        let colorDist = hypot(a.color.a - b.color.a, a.color.b - b.color.b)
        let heterocromia = a.color.descricao != b.color.descricao && colorDist > 25
        out.append(heterocromia ? "Possível heterocromia (cor difere entre os olhos)."
                                : "Cor semelhante entre os olhos.")

        let confianca = ((a.quality.score + b.quality.score) / 2) / 100
        return (out, confianca)
    }
}

/// Gera um mapa de calor colorido a partir da íris normalizada (marcas/densidade).
enum Heatmap {
    static func make(_ img: GrayImage) -> CGImage? {
        let w = img.width, h = img.height
        var rgba = [UInt8](repeating: 0, count: w * h * 4)
        let (mean, std) = img.meanStd()
        for i in 0 ..< w * h {
            // desvio local em relação à média => "intensidade" da marca
            let z = std > 1e-6 ? (Double(img.pixels[i]) - mean) / std : 0
            let t = max(0, min(1, (z + 2) / 4))   // normaliza -2..2 -> 0..1
            let (r, g, b) = jet(t)
            rgba[i*4+0] = r; rgba[i*4+1] = g; rgba[i*4+2] = b; rgba[i*4+3] = 255
        }
        let cs = CGColorSpaceCreateDeviceRGB()
        guard let ctx = CGContext(data: &rgba, width: w, height: h,
                                  bitsPerComponent: 8, bytesPerRow: w * 4, space: cs,
                                  bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)
        else { return nil }
        return ctx.makeImage()
    }

    /// Colormap tipo "jet".
    private static func jet(_ t: Double) -> (UInt8, UInt8, UInt8) {
        func clamp(_ v: Double) -> UInt8 { UInt8(max(0, min(255, v * 255))) }
        let r = clamp(min(4 * t - 1.5, -4 * t + 4.5))
        let g = clamp(min(4 * t - 0.5, -4 * t + 3.5))
        let b = clamp(min(4 * t + 0.5, -4 * t + 2.5))
        return (r, g, b)
    }
}
