import Foundation
import CoreGraphics

/// Lado do olho.
enum Eye: String, CaseIterable, Sendable {
    case left = "Esquerdo"
    case right = "Direito"
}

/// Círculo detectado (centro + raio) em coordenadas de pixel da imagem.
struct Circle: Sendable, Equatable {
    var cx: Double
    var cy: Double
    var r: Double
    var center: CGPoint { CGPoint(x: cx, y: cy) }
}

/// Segmentação de um olho: íris e pupila.
struct IrisSegmentation: Sendable {
    var iris: Circle
    var pupil: Circle
    /// Razão pupila/íris (dilatação).
    var pupillaryRatio: Double {
        guard iris.r > 0 else { return 0 }
        return pupil.r / iris.r
    }
}

/// Características de cor no espaço Lab (médias).
struct ColorFeatures: Sendable {
    var L: Double
    var a: Double
    var b: Double
    /// Classificação simples de cor da íris a partir de a/b.
    var descricao: String
}

/// Características de textura.
struct TextureFeatures: Sendable {
    var gaborEnergy: Double        // energia média da resposta de Gabor
    var lbpUniformity: Double      // proporção de padrões LBP uniformes
    var glcmContrast: Double
    var glcmEnergy: Double
    var glcmHomogeneity: Double
    var glcmCorrelation: Double
    var sharpness: Double          // nitidez (energia de alta frequência)
    var specularRatio: Double      // fração de reflexo especular
}

/// Fatores de qualidade (cada um 0–1) e score consolidado 0–100.
struct QualityAssessment: Sendable {
    var focus: Double
    var occlusion: Double
    var reflection: Double
    var offAngle: Double
    var dilation: Double
    var size: Double
    var score: Double              // 0–100

    static let zero = QualityAssessment(
        focus: 0, occlusion: 0, reflection: 0, offAngle: 0,
        dilation: 0, size: 0, score: 0
    )
}

/// Biometria estimada.
struct Biometrics: Sendable {
    var irisDiameterMM: Double
    var pupilDiameterMM: Double
    var pupillaryRatio: Double
    var classificacao: String      // miose / normal / midríase
}

/// Resultado completo da análise de um olho.
struct EyeAnalysis: Sendable, Identifiable {
    let id = UUID()
    var eye: Eye
    var segmentation: IrisSegmentation
    var color: ColorFeatures
    var texture: TextureFeatures
    var quality: QualityAssessment
    var biometrics: Biometrics
    /// Recorte normalizado (rubber sheet) para exibição/mapa de calor.
    var normalizedImage: CGImage?
    var zoomImage: CGImage?
    var heatmapImage: CGImage?
    /// Avisos gerados na análise.
    var avisos: [String]
}

/// Resultado da análise de um quadro (um ou dois olhos).
struct FrameAnalysis: Sendable {
    var timestamp: Date
    var capturedImage: CGImage?
    var eyes: [EyeAnalysis]
    /// Comparações entre os dois olhos (simetria, heterocromia).
    var comparacoes: [String]
    var confianca: Double          // 0–1

    static let empty = FrameAnalysis(
        timestamp: Date(), capturedImage: nil, eyes: [],
        comparacoes: [], confianca: 0
    )
}
