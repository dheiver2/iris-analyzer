import SwiftUI
import CoreGraphics

/// View-model que liga câmera, pipeline de análise e estado da UI.
@MainActor
final class AnalysisViewModel: ObservableObject {
    @Published var frame: FrameAnalysis = .empty
    @Published var analyzing = false
    @Published var clientName = ""
    @Published var observations = ""
    @Published var autoCapture = false
    @Published var lastPDFURL: URL?
    @Published var statusMessage = "Posicione o rosto e clique em Capturar."

    let camera = CameraController()
    private var autoTick = 0

    func start() { camera.requestAndStart() }
    func stop() { camera.stop() }

    /// Captura o quadro atual e roda o pipeline (fora da main thread).
    func capture() {
        guard let cg = camera.snapshot(), !analyzing else {
            statusMessage = "Câmera ainda não pronta."
            return
        }
        analyzing = true
        statusMessage = "Analisando…"
        Task.detached(priority: .userInitiated) {
            let result = AnalysisPipeline.analyze(cgImage: cg)
            await MainActor.run {
                self.frame = result
                self.analyzing = false
                if result.eyes.isEmpty {
                    self.statusMessage = "Nenhum olho detectado. Aproxime-se e centralize."
                } else {
                    let q = Int(result.eyes.map(\.quality.score).reduce(0, +)
                                / Double(result.eyes.count))
                    self.statusMessage = "Análise concluída · qualidade média \(q)/100"
                }
            }
        }
    }

    /// Chamado periodicamente pela UI para auto-captura quando ligada.
    func tickAutoCapture() {
        guard autoCapture, !analyzing else { return }
        autoTick += 1
        if autoTick % 30 == 0 { capture() }   // ~a cada 30 ticks
    }

    func generatePDF() {
        guard !frame.eyes.isEmpty else {
            statusMessage = "Capture uma análise antes de gerar o laudo."
            return
        }
        do {
            let url = try PDFReport.generate(frame: frame, client: clientName,
                                             observations: observations)
            lastPDFURL = url
            statusMessage = "Laudo salvo: \(url.lastPathComponent)"
        } catch {
            statusMessage = "Falha ao gerar PDF: \(error.localizedDescription)"
        }
    }
}
