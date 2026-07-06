import Foundation
import Vision
import CoreGraphics

/// Localiza os olhos e pupilas usando o Vision.framework (nativo), fornecendo
/// centros e raios iniciais que o operador de Daugman refina depois.
struct DetectedEye {
    var eye: Eye
    var eyeCenter: CGPoint      // em pixels (origem no topo-esquerda)
    var pupilCenter: CGPoint
    var irisRadiusGuess: Double
}

enum IrisDetector {

    /// Executa a detecção facial e retorna os olhos encontrados (0, 1 ou 2).
    static func detect(in cgImage: CGImage) -> [DetectedEye] {
        let w = Double(cgImage.width), h = Double(cgImage.height)
        let request = VNDetectFaceLandmarksRequest()
        let handler = VNImageRequestHandler(cgImage: cgImage, orientation: .up, options: [:])
        do {
            try handler.perform([request])
        } catch {
            return []
        }
        guard let face = (request.results?.first) else { return [] }
        guard let landmarks = face.landmarks else { return [] }

        // Converte pontos normalizados (Vision: origem inferior-esquerda) para pixels.
        func toPixels(_ region: VNFaceLandmarkRegion2D?, box: CGRect) -> [CGPoint] {
            guard let region else { return [] }
            return region.normalizedPoints.map { p in
                let x = (box.origin.x + p.x * box.size.width) * w
                let yBottom = (box.origin.y + p.y * box.size.height) * h
                return CGPoint(x: x, y: h - yBottom)   // flip Y para origem no topo
            }
        }

        var result: [DetectedEye] = []
        let box = face.boundingBox

        func buildEye(_ eyePts: [CGPoint], pupilPts: [CGPoint], side: Eye) {
            guard eyePts.count >= 4 else { return }
            let cx = eyePts.map(\.x).reduce(0, +) / Double(eyePts.count)
            let cy = eyePts.map(\.y).reduce(0, +) / Double(eyePts.count)
            // largura do olho => estimativa do raio da íris
            let xs = eyePts.map(\.x)
            let eyeWidth = (xs.max() ?? cx) - (xs.min() ?? cx)
            let irisR = eyeWidth * 0.42     // íris ~ 42% da fissura palpebral
            let pupil: CGPoint = pupilPts.first ?? CGPoint(x: cx, y: cy)
            result.append(DetectedEye(eye: side, eyeCenter: CGPoint(x: cx, y: cy),
                                      pupilCenter: pupil, irisRadiusGuess: irisR))
        }

        // Vision "left/right" é da perspectiva do sujeito; mapeamos para o rótulo do usuário.
        buildEye(toPixels(landmarks.leftEye, box: box),
                 pupilPts: toPixels(landmarks.leftPupil, box: box), side: .right)
        buildEye(toPixels(landmarks.rightEye, box: box),
                 pupilPts: toPixels(landmarks.rightPupil, box: box), side: .left)
        return result
    }
}
