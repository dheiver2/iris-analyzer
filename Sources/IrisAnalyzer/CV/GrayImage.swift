import Foundation
import CoreGraphics
import Accelerate

/// Imagem em tons de cinza (0–255) em layout linear row-major.
/// Base para todo o pipeline de CV nativo.
struct GrayImage {
    var width: Int
    var height: Int
    var pixels: [Float]        // valores 0–255

    init(width: Int, height: Int, pixels: [Float]) {
        self.width = width
        self.height = height
        self.pixels = pixels
    }

    @inline(__always)
    func at(_ x: Int, _ y: Int) -> Float {
        guard x >= 0, y >= 0, x < width, y < height else { return 0 }
        return pixels[y * width + x]
    }

    /// Amostra bilinear (subpixel) — usada por Daugman e normalização.
    @inline(__always)
    func sample(_ x: Double, _ y: Double) -> Double {
        let x0 = Int(floor(x)), y0 = Int(floor(y))
        let x1 = x0 + 1, y1 = y0 + 1
        let fx = x - Double(x0), fy = y - Double(y0)
        let p00 = Double(at(x0, y0)), p10 = Double(at(x1, y0))
        let p01 = Double(at(x0, y1)), p11 = Double(at(x1, y1))
        let top = p00 * (1 - fx) + p10 * fx
        let bot = p01 * (1 - fx) + p11 * fx
        return top * (1 - fy) + bot * fy
    }

    /// Constrói a partir de um CGImage (converte para luminância).
    init?(cgImage: CGImage) {
        let w = cgImage.width, h = cgImage.height
        guard w > 0, h > 0 else { return nil }
        var rgba = [UInt8](repeating: 0, count: w * h * 4)
        let cs = CGColorSpaceCreateDeviceRGB()
        guard let ctx = CGContext(
            data: &rgba, width: w, height: h,
            bitsPerComponent: 8, bytesPerRow: w * 4, space: cs,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else { return nil }
        ctx.draw(cgImage, in: CGRect(x: 0, y: 0, width: w, height: h))

        var gray = [Float](repeating: 0, count: w * h)
        // Luminância Rec.601
        for i in 0 ..< w * h {
            let r = Float(rgba[i * 4 + 0])
            let g = Float(rgba[i * 4 + 1])
            let b = Float(rgba[i * 4 + 2])
            gray[i] = 0.299 * r + 0.587 * g + 0.114 * b
        }
        self.init(width: w, height: h, pixels: gray)
    }

    /// Recorta uma região retangular (clampeada aos limites).
    func crop(x: Int, y: Int, w: Int, h: Int) -> GrayImage {
        let x0 = max(0, x), y0 = max(0, y)
        let x1 = min(width, x + w), y1 = min(height, y + h)
        let cw = max(0, x1 - x0), ch = max(0, y1 - y0)
        var out = [Float](repeating: 0, count: cw * ch)
        for row in 0 ..< ch {
            for col in 0 ..< cw {
                out[row * cw + col] = at(x0 + col, y0 + row)
            }
        }
        return GrayImage(width: cw, height: ch, pixels: out)
    }

    /// Converte para CGImage em escala de cinza (para exibição).
    func cgImage() -> CGImage? {
        var bytes = [UInt8](repeating: 0, count: width * height)
        for i in 0 ..< width * height {
            bytes[i] = UInt8(max(0, min(255, pixels[i])))
        }
        let cs = CGColorSpaceCreateDeviceGray()
        guard let ctx = CGContext(
            data: &bytes, width: width, height: height,
            bitsPerComponent: 8, bytesPerRow: width, space: cs,
            bitmapInfo: CGImageAlphaInfo.none.rawValue
        ) else { return nil }
        return ctx.makeImage()
    }

    /// Média e desvio-padrão (via Accelerate).
    func meanStd() -> (mean: Double, std: Double) {
        var mean: Float = 0, std: Float = 0
        vDSP_normalize(pixels, 1, nil, 1, &mean, &std, vDSP_Length(pixels.count))
        return (Double(mean), Double(std))
    }
}
