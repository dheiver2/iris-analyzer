import Foundation
import AppKit

/// Ponto de entrada. Suporta um modo headless de teste do pipeline de CV:
///
///   IrisAnalyzer --analyze <caminho-da-imagem>
///
/// usado para validar/calibrar a análise sem abrir a câmera. Sem argumentos,
/// abre a interface gráfica normal.
@main
struct Main {
    static func main() {
        let args = CommandLine.arguments
        if let i = args.firstIndex(of: "--analyze"), i + 1 < args.count {
            CLIRunner.run(imagePath: args[i + 1])
            exit(0)
        }
        if let i = args.firstIndex(of: "--make-icon"), i + 1 < args.count {
            IconMaker.write(to: args[i + 1])
            exit(0)
        }
        if args.contains("--test") {
            exit(SelfTest.run())
        }
        IrisAnalyzerApp.main()
    }
}

enum CLIRunner {
    static func run(imagePath: String) {
        guard let nsimg = NSImage(contentsOfFile: imagePath),
              let cg = nsimg.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
            print("✗ Não consegui carregar a imagem: \(imagePath)")
            return
        }
        print("▶ Imagem \(cg.width)x\(cg.height) — rodando pipeline nativo…\n")
        let frame = AnalysisPipeline.analyze(cgImage: cg)

        if frame.eyes.isEmpty {
            print("✗ Nenhum olho detectado pelo Vision.")
            return
        }
        print("✓ Olhos detectados: \(frame.eyes.count)")
        print(String(format: "  Confiança geral: %.0f%%\n", frame.confianca * 100))
        for e in frame.eyes {
            let s = e.segmentation, b = e.biometrics, q = e.quality, t = e.texture
            print("── Olho \(e.eye.rawValue) ──")
            print(String(format: "  Íris:   centro (%.0f, %.0f)  r=%.1f px", s.iris.cx, s.iris.cy, s.iris.r))
            print(String(format: "  Pupila: centro (%.0f, %.0f)  r=%.1f px  (razão %.2f)",
                         s.pupil.cx, s.pupil.cy, s.pupil.r, s.pupillaryRatio))
            print("  Cor:    \(e.color.descricao)  "
                  + String(format: "(L*%.0f a*%.0f b*%.0f)", e.color.L, e.color.a, e.color.b))
            print(String(format: "  Biometria: íris %.1f mm · pupila %.1f mm · %@",
                         b.irisDiameterMM, b.pupilDiameterMM, b.classificacao))
            print(String(format: "  Qualidade: %.0f/100  (foco %.2f · oclusão %.2f · reflexo %.2f · ângulo %.2f)",
                         q.score, q.focus, q.occlusion, q.reflection, q.offAngle))
            print(String(format: "  Textura: nitidez %.0f · Gabor %.0f · LBP-unif %.2f · GLCM-contraste %.2f",
                         t.sharpness, t.gaborEnergy, t.lbpUniformity, t.glcmContrast))
            if !e.avisos.isEmpty { print("  Avisos: \(e.avisos.joined(separator: "; "))") }
            print("")
        }
        for c in frame.comparacoes { print("• \(c)") }
    }
}
