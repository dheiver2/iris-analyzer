import Foundation
import CoreGraphics

/// Extrai características de cor médias no espaço CIE-Lab do anel da íris.
enum ColorAnalysis {

    /// Calcula L*, a*, b* médios amostrando o anel da íris a partir do CGImage RGB.
    static func meanLab(cgImage: CGImage, seg: IrisSegmentation) -> ColorFeatures {
        let w = cgImage.width, h = cgImage.height
        var rgba = [UInt8](repeating: 0, count: w * h * 4)
        let cs = CGColorSpaceCreateDeviceRGB()
        guard let ctx = CGContext(
            data: &rgba, width: w, height: h,
            bitsPerComponent: 8, bytesPerRow: w * 4, space: cs,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return ColorFeatures(L: 0, a: 0, b: 0, descricao: "indeterminada")
        }
        ctx.draw(cgImage, in: CGRect(x: 0, y: 0, width: w, height: h))

        var sL = 0.0, sa = 0.0, sb = 0.0, n = 0.0
        let iris = seg.iris, pup = seg.pupil
        // amostra o anel (entre 1.1*pupila e 0.9*íris)
        let rInner = pup.r * 1.1, rOuter = iris.r * 0.9
        let stepA = 64, stepR = 12
        for ai in 0 ..< stepA {
            let theta = 2 * Double.pi * Double(ai) / Double(stepA)
            for ri in 0 ..< stepR {
                let frac = Double(ri) / Double(stepR - 1)
                let rr = rInner + (rOuter - rInner) * frac
                let x = Int(iris.cx + rr * cos(theta))
                let y = Int(iris.cy + rr * sin(theta))
                guard x >= 0, y >= 0, x < w, y < h else { continue }
                let idx = (y * w + x) * 4
                let R = Double(rgba[idx]) / 255
                let G = Double(rgba[idx + 1]) / 255
                let B = Double(rgba[idx + 2]) / 255
                let (L, a, b) = rgbToLab(R, G, B)
                sL += L; sa += a; sb += b; n += 1
            }
        }
        guard n > 0 else { return ColorFeatures(L: 0, a: 0, b: 0, descricao: "indeterminada") }
        let L = sL / n, a = sa / n, b = sb / n
        return ColorFeatures(L: L, a: a, b: b, descricao: classify(L: L, a: a, b: b))
    }

    private static func rgbToLab(_ r: Double, _ g: Double, _ b: Double)
        -> (Double, Double, Double) {
        func inv(_ c: Double) -> Double {
            c > 0.04045 ? pow((c + 0.055) / 1.055, 2.4) : c / 12.92
        }
        let R = inv(r), G = inv(g), B = inv(b)
        // sRGB -> XYZ (D65)
        let X = (R * 0.4124 + G * 0.3576 + B * 0.1805) / 0.95047
        let Y =  R * 0.2126 + G * 0.7152 + B * 0.0722
        let Z = (R * 0.0193 + G * 0.1192 + B * 0.9505) / 1.08883
        func f(_ t: Double) -> Double {
            t > 0.008856 ? pow(t, 1.0/3.0) : (7.787 * t + 16.0/116.0)
        }
        let fx = f(X), fy = f(Y), fz = f(Z)
        let L = 116 * fy - 16
        let a = 500 * (fx - fy)
        let bb = 200 * (fy - fz)
        return (L, a, bb)
    }

    private static func classify(L: Double, a: Double, b: Double) -> String {
        // heurística simples baseada em luminância e tom (b: azul<->amarelo)
        if L < 30 { return "castanha escura" }
        if b < -5 { return "azulada" }
        if b > 15 && L > 45 { return "âmbar/mel" }
        if L > 55 { return "clara (verde/avelã)" }
        return "castanha"
    }
}
