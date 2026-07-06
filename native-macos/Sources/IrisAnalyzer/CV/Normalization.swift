import Foundation

/// Normalização "rubber sheet" de Daugman: desenrola o anel da íris (entre a
/// borda da pupila e a borda da íris) num retângulo polar de dimensão fixa.
enum Normalization {

    static let radialResolution = 64   // amostras entre pupila e íris (r)
    static let angularResolution = 240 // amostras angulares (θ)

    /// Retorna a imagem normalizada (angular x radial) e uma máscara booleana de
    /// pixels válidos (fora de reflexos/oclusão grosseira por limiar).
    static func unwrap(_ img: GrayImage, seg: IrisSegmentation)
        -> (image: GrayImage, mask: [Bool]) {
        let R = radialResolution, A = angularResolution
        var out = [Float](repeating: 0, count: R * A)
        var mask = [Bool](repeating: true, count: R * A)

        let p = seg.pupil, iris = seg.iris
        for i in 0 ..< A {
            let theta = 2.0 * Double.pi * Double(i) / Double(A)
            let ct = cos(theta), st = sin(theta)
            // ponto na borda da pupila e na borda da íris para este ângulo
            let px = p.cx + p.r * ct,  py = p.cy + p.r * st
            let ix = iris.cx + iris.r * ct, iy = iris.cy + iris.r * st
            for j in 0 ..< R {
                let frac = Double(j) / Double(R - 1)
                let x = px + (ix - px) * frac
                let y = py + (iy - py) * frac
                let v = img.sample(x, y)
                let idx = j * A + i
                out[idx] = Float(v)
                // reflexo especular muito brilhante => inválido
                if v > 240 { mask[idx] = false }
            }
        }
        return (GrayImage(width: A, height: R, pixels: out), mask)
    }
}

/// Detecção da pupila "real" dentro do disco da íris via limiar + circularidade,
/// substituindo a estimativa geométrica quando encontra algo melhor.
enum PupilFinder {

    /// Procura a região escura central compatível com uma pupila.
    static func detect(_ img: GrayImage, irisGuess: Circle) -> Circle {
        // Recorte ao redor do centro da íris
        let r = irisGuess.r
        let x0 = Int(irisGuess.cx - r), y0 = Int(irisGuess.cy - r)
        let size = Int(2 * r)
        guard size > 4 else { return fallback(irisGuess) }
        let roi = img.crop(x: x0, y: y0, w: size, h: size)
        let (mean, std) = roi.meanStd()
        // limiar adaptativo: pupila costuma ser bem mais escura que a média
        let thr = max(20.0, mean - 1.2 * std)

        // centróide dos pixels escuros próximos ao centro
        var sx = 0.0, sy = 0.0, n = 0.0
        let cxLocal = Double(size) / 2, cyLocal = Double(size) / 2
        let maxDist = r * 0.7
        for y in 0 ..< roi.height {
            for x in 0 ..< roi.width {
                if Double(roi.at(x, y)) < thr {
                    let d = hypot(Double(x) - cxLocal, Double(y) - cyLocal)
                    if d < maxDist {
                        sx += Double(x); sy += Double(y); n += 1
                    }
                }
            }
        }
        guard n > 8 else { return fallback(irisGuess) }
        let pcx = Double(x0) + sx / n
        let pcy = Double(y0) + sy / n
        // raio da pupila via área (n ≈ π r²)
        var pr = sqrt(n / Double.pi)
        // refina a borda da pupila com Daugman (transição pupila->íris)
        let refined = Daugman.refine(img, cx0: pcx, cy0: pcy,
                                     rMin: max(3, pr * 0.6), rMax: min(r * 0.85, pr * 1.6),
                                     searchRadius: 4, samples: 120)
        pr = refined.r
        // sanidade: pupila deve estar entre 20% e 80% do raio da íris
        let ratio = pr / r
        if ratio < 0.15 || ratio > 0.85 { return fallback(irisGuess) }
        return refined
    }

    private static func fallback(_ iris: Circle) -> Circle {
        Circle(cx: iris.cx, cy: iris.cy, r: iris.r * 0.4)
    }
}
