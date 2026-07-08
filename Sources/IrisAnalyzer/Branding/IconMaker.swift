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
        func rgb(_ r: Double, _ g: Double, _ b: Double, _ a: Double = 1) -> CGColor {
            CGColor(red: r, green: g, blue: b, alpha: a)
        }

        let center = CGPoint(x: sz/2, y: sz/2)
        let irisR = sz * 0.345
        let pupilR = irisR * 0.40

        // ── Fundo arredondado com leve gradiente vertical (mais vivo que chapado)
        ctx.saveGState()
        let bg = CGPath(roundedRect: CGRect(x: 0, y: 0, width: sz, height: sz),
                        cornerWidth: sz * 0.2237, cornerHeight: sz * 0.2237, transform: nil)
        ctx.addPath(bg); ctx.clip()
        if let bgGrad = CGGradient(colorsSpace: cs,
            colors: [rgb(0.09, 0.09, 0.11), rgb(0.035, 0.035, 0.045)] as CFArray,
            locations: [0, 1]) {
            ctx.drawLinearGradient(bgGrad, start: CGPoint(x: 0, y: sz),
                                   end: CGPoint(x: 0, y: 0), options: [])
        }
        // brilho da marca atrás da íris
        if let glow = CGGradient(colorsSpace: cs,
            colors: [rgb(0.545, 0.486, 1.0, 0.35), rgb(0.545, 0.486, 1.0, 0)] as CFArray,
            locations: [0, 1]) {
            ctx.drawRadialGradient(glow, startCenter: center, startRadius: 0,
                                   endCenter: center, endRadius: irisR * 1.9, options: [])
        }
        ctx.restoreGState()

        // ── Anel de brilho externo (aura da marca)
        ctx.setStrokeColor(rgb(0.545, 0.486, 1.0, 0.25))
        ctx.setLineWidth(sz * 0.02)
        ctx.addArc(center: center, radius: irisR * 1.12, startAngle: 0, endAngle: .pi*2, clockwise: false)
        ctx.strokePath()

        // ── Disco da íris: gradiente radial em camadas (centro claro → azul profundo)
        ctx.saveGState()
        ctx.addArc(center: center, radius: irisR, startAngle: 0, endAngle: .pi*2, clockwise: false)
        ctx.clip()
        let irisColors = [
            rgb(0.62, 0.56, 1.0),    // centro claro
            rgb(0.545, 0.486, 1.0),  // #8B7CFF
            rgb(0.42, 0.36, 0.88),   // #6B5CE0
            rgb(0.28, 0.42, 0.82),   // azul
            rgb(0.16, 0.22, 0.55),   // azul profundo (borda)
        ] as CFArray
        if let grad = CGGradient(colorsSpace: cs, colors: irisColors,
                                 locations: [0, 0.35, 0.6, 0.82, 1]) {
            ctx.drawRadialGradient(grad, startCenter: center, startRadius: pupilR * 0.6,
                                   endCenter: center, endRadius: irisR, options: [])
        }

        // fibras radiais finas com opacidade variável (textura da íris)
        for k in 0..<120 {
            let ang = CGFloat(k) * (.pi * 2 / 120)
            let jitter = CGFloat((k % 5)) * 0.006
            let alpha = 0.05 + Double(k % 3) * 0.035
            ctx.setStrokeColor(rgb(1, 1, 1, alpha))
            ctx.setLineWidth(sz * (0.0025 + jitter))
            let r0 = pupilR * 1.15
            let r1 = irisR * (0.9 + CGFloat(k % 4) * 0.02)
            ctx.move(to: CGPoint(x: center.x + cos(ang) * r0, y: center.y + sin(ang) * r0))
            ctx.addLine(to: CGPoint(x: center.x + cos(ang) * r1, y: center.y + sin(ang) * r1))
            ctx.strokePath()
        }

        // colarete (anel autonômico) + sombreamento interno junto à pupila
        ctx.setStrokeColor(rgb(1, 1, 1, 0.14))
        ctx.setLineWidth(sz * 0.006)
        ctx.addArc(center: center, radius: pupilR * 1.5, startAngle: 0, endAngle: .pi*2, clockwise: false)
        ctx.strokePath()
        ctx.restoreGState()

        // ── Anel límbico escuro na borda da íris (profundidade)
        ctx.setStrokeColor(rgb(0.07, 0.09, 0.2, 0.9))
        ctx.setLineWidth(sz * 0.022)
        ctx.addArc(center: center, radius: irisR - sz * 0.006, startAngle: 0, endAngle: .pi*2, clockwise: false)
        ctx.strokePath()
        // realce fino índigo por cima do limbo
        ctx.setStrokeColor(rgb(0.6, 0.55, 1.0, 0.6))
        ctx.setLineWidth(sz * 0.004)
        ctx.addArc(center: center, radius: irisR, startAngle: 0, endAngle: .pi*2, clockwise: false)
        ctx.strokePath()

        // ── Pupila com leve gradiente radial (não chapada)
        ctx.saveGState()
        ctx.addArc(center: center, radius: pupilR, startAngle: 0, endAngle: .pi*2, clockwise: false)
        ctx.clip()
        if let pgrad = CGGradient(colorsSpace: cs,
            colors: [rgb(0.06, 0.06, 0.09), rgb(0.01, 0.01, 0.02)] as CFArray, locations: [0, 1]) {
            ctx.drawRadialGradient(pgrad, startCenter: center, startRadius: 0,
                                   endCenter: center, endRadius: pupilR, options: [])
        }
        ctx.restoreGState()
        // aro sutil da pupila
        ctx.setStrokeColor(rgb(0, 0, 0, 0.8))
        ctx.setLineWidth(sz * 0.004)
        ctx.addArc(center: center, radius: pupilR, startAngle: 0, endAngle: .pi*2, clockwise: false)
        ctx.strokePath()

        // ── Reflexos especulares: um grande suave + um pequeno nítido
        let hi = CGPoint(x: center.x - pupilR*0.32, y: center.y + pupilR*0.42)
        ctx.saveGState()
        ctx.addArc(center: hi, radius: pupilR*0.42, startAngle: 0, endAngle: .pi*2, clockwise: false)
        ctx.clip()
        if let hgrad = CGGradient(colorsSpace: cs,
            colors: [rgb(1, 1, 1, 0.9), rgb(1, 1, 1, 0)] as CFArray, locations: [0, 1]) {
            ctx.drawRadialGradient(hgrad, startCenter: hi, startRadius: 0,
                                   endCenter: hi, endRadius: pupilR*0.42, options: [])
        }
        ctx.restoreGState()
        ctx.setFillColor(rgb(1, 1, 1, 0.95))
        ctx.addArc(center: CGPoint(x: center.x + pupilR*0.34, y: center.y - pupilR*0.3),
                   radius: pupilR*0.1, startAngle: 0, endAngle: .pi*2, clockwise: false)
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
