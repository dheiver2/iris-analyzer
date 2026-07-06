import Foundation
import AppKit
import CoreGraphics

/// Gera o laudo em PDF nativamente com Core Graphics/AppKit (sem ReportLab).
enum PDFReport {

    enum ReportError: Error { case contextFailed }

    static func generate(frame: FrameAnalysis, client: String,
                         observations: String) throws -> URL {
        let pageW: CGFloat = 595, pageH: CGFloat = 842   // A4 em pontos
        var mediaBox = CGRect(x: 0, y: 0, width: pageW, height: pageH)

        let stamp = Int(Date().timeIntervalSince1970)
        let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("laudo_iris_\(stamp).pdf")

        guard let ctx = CGContext(url as CFURL, mediaBox: &mediaBox, nil) else {
            throw ReportError.contextFailed
        }
        ctx.beginPDFPage(nil)

        let nsCtx = NSGraphicsContext(cgContext: ctx, flipped: false)
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = nsCtx

        var y = pageH - 60

        // Cabeçalho com faixa da marca
        ctx.setFillColor(CGColor(red: 0.545, green: 0.486, blue: 1.0, alpha: 1))
        ctx.fill(CGRect(x: 0, y: pageH - 90, width: pageW, height: 90))
        drawText("IRIS ANALYZER", x: 40, y: pageH - 55, size: 22, bold: true, color: .white)
        drawText("Laudo de análise de imagem da íris — bem-estar",
                 x: 40, y: pageH - 78, size: 11, color: NSColor(white: 1, alpha: 0.85))
        y = pageH - 120

        // Dados do cliente
        let df = DateFormatter(); df.dateFormat = "dd/MM/yyyy HH:mm"
        drawText("Cliente: \(client.isEmpty ? "—" : client)", x: 40, y: y, size: 12, bold: true)
        y -= 18
        drawText("Data: \(df.string(from: frame.timestamp))", x: 40, y: y, size: 11)
        y -= 16
        drawText("Confiança da análise: \(Int(frame.confianca * 100))%", x: 40, y: y, size: 11)
        y -= 28

        // Por olho
        for eye in frame.eyes {
            drawText("Olho \(eye.eye.rawValue)", x: 40, y: y, size: 14, bold: true,
                     color: NSColor(red: 0.42, green: 0.36, blue: 0.88, alpha: 1))
            y -= 20

            if let zoom = eye.zoomImage {
                ctx.draw(zoom, in: CGRect(x: 40, y: y - 90, width: 90, height: 90))
            }
            if let heat = eye.heatmapImage {
                ctx.draw(heat, in: CGRect(x: 140, y: y - 90, width: 90, height: 90))
            }

            let b = eye.biometrics, c = eye.color, t = eye.texture
            let lines = [
                "Cor da íris: \(c.descricao)  (L*\(String(format: "%.0f", c.L)))",
                "Diâmetro íris: \(String(format: "%.1f", b.irisDiameterMM)) mm · "
                    + "pupila: \(String(format: "%.1f", b.pupilDiameterMM)) mm",
                "Razão pupilar: \(String(format: "%.2f", b.pupillaryRatio)) — \(b.classificacao)",
                "Qualidade: \(Int(eye.quality.score))/100 · nitidez \(String(format: "%.0f", t.sharpness))",
                "GLCM contraste \(String(format: "%.2f", t.glcmContrast)) · "
                    + "homogeneidade \(String(format: "%.2f", t.glcmHomogeneity))",
            ]
            var ly = y
            for line in lines {
                drawText(line, x: 250, y: ly, size: 10); ly -= 15
            }
            y -= 110
        }

        // Comparações
        if !frame.comparacoes.isEmpty {
            drawText("Comparação entre olhos", x: 40, y: y, size: 12, bold: true); y -= 18
            for c in frame.comparacoes { drawText("• \(c)", x: 48, y: y, size: 10); y -= 14 }
            y -= 10
        }

        // Observações
        if !observations.isEmpty {
            drawText("Observações", x: 40, y: y, size: 12, bold: true); y -= 16
            drawText(observations, x: 48, y: y, size: 10, maxWidth: pageW - 88); y -= 30
        }

        // Rodapé/disclaimer
        drawText("A iridologia não é reconhecida cientificamente como método diagnóstico. "
                 + "Documento educacional/bem-estar; não substitui avaliação médica.",
                 x: 40, y: 40, size: 8, color: NSColor(white: 0.4, alpha: 1), maxWidth: pageW - 80)

        NSGraphicsContext.restoreGraphicsState()
        ctx.endPDFPage()
        ctx.closePDF()
        return url
    }

    private static func drawText(_ text: String, x: CGFloat, y: CGFloat, size: CGFloat,
                                 bold: Bool = false, color: NSColor = NSColor(white: 0.1, alpha: 1),
                                 maxWidth: CGFloat = 500) {
        let font = bold ? NSFont.boldSystemFont(ofSize: size) : NSFont.systemFont(ofSize: size)
        let attrs: [NSAttributedString.Key: Any] = [.font: font, .foregroundColor: color]
        let rect = CGRect(x: x, y: y - size, width: maxWidth, height: size * 4)
        (text as NSString).draw(in: rect, withAttributes: attrs)
    }
}
