import Foundation

/// Sintetiza imagens com formas conhecidas para os testes (`--test`).
enum Synth {
    /// GrayImage com fundo `bg` e um disco cheio de valor `fg`, raio `r` no centro.
    static func disk(w: Int, h: Int, cx: Double, cy: Double, r: Double,
                     bg: Float, fg: Float) -> GrayImage {
        var px = [Float](repeating: bg, count: w * h)
        for y in 0 ..< h {
            for x in 0 ..< w where hypot(Double(x) - cx, Double(y) - cy) <= r {
                px[y * w + x] = fg
            }
        }
        return GrayImage(width: w, height: h, pixels: px)
    }

    /// Íris (disco claro) com pupila (disco escuro) concêntricos sobre fundo escuro.
    static func eye(w: Int, h: Int, cx: Double, cy: Double,
                    irisR: Double, pupilR: Double) -> GrayImage {
        var px = [Float](repeating: 40, count: w * h)
        for y in 0 ..< h {
            for x in 0 ..< w {
                let d = hypot(Double(x) - cx, Double(y) - cy)
                if d <= pupilR { px[y * w + x] = 20 }
                else if d <= irisR { px[y * w + x] = 150 }
            }
        }
        return GrayImage(width: w, height: h, pixels: px)
    }

    /// Imagem constante.
    static func constant(w: Int, h: Int, value: Float) -> GrayImage {
        GrayImage(width: w, height: h, pixels: [Float](repeating: value, count: w * h))
    }
}
