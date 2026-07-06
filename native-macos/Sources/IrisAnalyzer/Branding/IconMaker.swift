import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

/// Gera o ícone do app (1024×1024 PNG) desenhando a marca — uma íris estilizada
/// com o gradiente índigo→azul sobre fundo escuro. Nativo (CoreGraphics).
enum IconMaker {
    static func write(to path: String) {
        let S = 1024
        let cs = CGColorSpaceCreateDeviceRGB()
        guard let ctx = CGContext(data: nil, width: S, height: S, bitsPerComponent: 8,
                                  bytesPerRow: 0, space: cs,
                                  bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)
        else { print("✗ contexto falhou"); return }

        let sz = CGFloat(S)
        // Fundo arredondado escuro
        ctx.setFillColor(CGColor(red: 0.043, green: 0.043, blue: 0.047, alpha: 1))
        let bg = CGPath(roundedRect: CGRect(x: 0, y: 0, width: sz, height: sz),
                        cornerWidth: sz * 0.22, cornerHeight: sz * 0.22, transform: nil)
        ctx.addPath(bg); ctx.fillPath()

        let center = CGPoint(x: sz/2, y: sz/2)
        let irisR = sz * 0.34

        // Disco da íris com gradiente radial índigo→azul
        ctx.saveGState()
        ctx.addArc(center: center, radius: irisR, startAngle: 0, endAngle: .pi*2, clockwise: false)
        ctx.clip()
        let colors = [
            CGColor(red: 0.545, green: 0.486, blue: 1.0, alpha: 1),   // #8B7CFF
            CGColor(red: 0.42, green: 0.36, blue: 0.88, alpha: 1),    // #6B5CE0
            CGColor(red: 0.30, green: 0.52, blue: 0.88, alpha: 1),    // #4E86E0
        ] as CFArray
        if let grad = CGGradient(colorsSpace: cs, colors: colors, locations: [0, 0.6, 1]) {
            ctx.drawRadialGradient(grad, startCenter: center, startRadius: irisR*0.2,
                                   endCenter: center, endRadius: irisR, options: [])
        }
        ctx.restoreGState()

        // Fibras radiais da íris (linhas sutis)
        ctx.setStrokeColor(CGColor(red: 1, green: 1, blue: 1, alpha: 0.10))
        ctx.setLineWidth(sz * 0.006)
        let pupilR = irisR * 0.42
        for k in 0..<48 {
            let ang = CGFloat(k) * .pi / 24
            let x0 = center.x + cos(ang) * pupilR * 1.1
            let y0 = center.y + sin(ang) * pupilR * 1.1
            let x1 = center.x + cos(ang) * irisR * 0.95
            let y1 = center.y + sin(ang) * irisR * 0.95
            ctx.move(to: CGPoint(x: x0, y: y0)); ctx.addLine(to: CGPoint(x: x1, y: y1))
        }
        ctx.strokePath()

        // Anel externo (limbo)
        ctx.setStrokeColor(CGColor(red: 0.545, green: 0.486, blue: 1.0, alpha: 0.9))
        ctx.setLineWidth(sz * 0.012)
        ctx.addArc(center: center, radius: irisR, startAngle: 0, endAngle: .pi*2, clockwise: false)
        ctx.strokePath()

        // Pupila escura
        ctx.setFillColor(CGColor(red: 0.02, green: 0.02, blue: 0.03, alpha: 1))
        ctx.addArc(center: center, radius: pupilR, startAngle: 0, endAngle: .pi*2, clockwise: false)
        ctx.fillPath()

        // Reflexo especular
        ctx.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 0.85))
        ctx.addArc(center: CGPoint(x: center.x - pupilR*0.35, y: center.y + pupilR*0.35),
                   radius: pupilR*0.22, startAngle: 0, endAngle: .pi*2, clockwise: false)
        ctx.fillPath()

        guard let img = ctx.makeImage() else { print("✗ imagem falhou"); return }
        let url = URL(fileURLWithPath: path)
        guard let dst = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil)
        else { print("✗ destino falhou"); return }
        CGImageDestinationAddImage(dst, img, nil)
        if CGImageDestinationFinalize(dst) {
            print("✓ Ícone gerado: \(path)")
        } else {
            print("✗ falha ao salvar ícone")
        }
    }
}
