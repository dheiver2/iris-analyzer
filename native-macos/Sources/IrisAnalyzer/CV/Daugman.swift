import Foundation

/// Operador integro-diferencial de Daugman para refino sub-pixel de bordas
/// circulares (íris e pupila).
///
/// max_r | d/dr  ∮  I(x,y) / (2πr) ds |  suavizado por um gaussiano em r.
///
/// Referência: J. Daugman, "How Iris Recognition Works", IEEE TCSVT, 2004.
enum Daugman {

    /// Integral de contorno: média de intensidade no círculo (cx,cy,r).
    private static func contourAverage(_ img: GrayImage, cx: Double, cy: Double,
                                       r: Double, samples: Int) -> Double {
        var sum = 0.0
        var count = 0
        let step = 2.0 * Double.pi / Double(samples)
        for i in 0 ..< samples {
            let theta = Double(i) * step
            // Ignora setores das pálpebras (topo/baixo) para a íris:
            // aqui amostramos todo o círculo; a máscara é aplicada por quem chama.
            let x = cx + r * cos(theta)
            let y = cy + r * sin(theta)
            if x >= 0, y >= 0, x < Double(img.width - 1), y < Double(img.height - 1) {
                sum += img.sample(x, y)
                count += 1
            }
        }
        return count > 0 ? sum / Double(count) : 0
    }

    /// Busca o raio que maximiza |d/dr da integral de contorno| em torno de um
    /// centro, num intervalo [rMin, rMax]. Retorna (raio, resposta).
    static func bestRadius(_ img: GrayImage, cx: Double, cy: Double,
                           rMin: Double, rMax: Double,
                           samples: Int = 180) -> (r: Double, response: Double) {
        let rStep = 1.0
        var radii: [Double] = []
        var integ: [Double] = []
        var r = rMin
        while r <= rMax {
            radii.append(r)
            integ.append(contourAverage(img, cx: cx, cy: cy, r: r, samples: samples))
            r += rStep
        }
        guard integ.count >= 3 else { return (rMin, 0) }

        // Derivada discreta suavizada (diferença central + média de 3).
        var bestR = radii[1]
        var bestResp = 0.0
        for i in 1 ..< integ.count - 1 {
            let d = abs(integ[i + 1] - integ[i - 1]) / 2.0
            // suavização simples
            let dSmooth: Double
            if i >= 2 && i < integ.count - 2 {
                let d0 = abs(integ[i] - integ[i - 2]) / 2.0
                let d2 = abs(integ[i + 2] - integ[i]) / 2.0
                dSmooth = (d0 + d + d2) / 3.0
            } else {
                dSmooth = d
            }
            if dSmooth > bestResp {
                bestResp = dSmooth
                bestR = radii[i]
            }
        }
        return (bestR, bestResp)
    }

    /// Refina centro + raio buscando numa pequena vizinhança do centro inicial.
    /// Usado tanto para íris quanto para pupila (parâmetros diferentes).
    static func refine(_ img: GrayImage, cx0: Double, cy0: Double,
                       rMin: Double, rMax: Double,
                       searchRadius: Int = 5, samples: Int = 180) -> Circle {
        var best = Circle(cx: cx0, cy: cy0, r: (rMin + rMax) / 2)
        var bestResp = -Double.greatestFiniteMagnitude
        for dy in stride(from: -searchRadius, through: searchRadius, by: 2) {
            for dx in stride(from: -searchRadius, through: searchRadius, by: 2) {
                let cx = cx0 + Double(dx)
                let cy = cy0 + Double(dy)
                let (r, resp) = bestRadius(img, cx: cx, cy: cy,
                                           rMin: rMin, rMax: rMax, samples: samples)
                if resp > bestResp {
                    bestResp = resp
                    best = Circle(cx: cx, cy: cy, r: r)
                }
            }
        }
        return best
    }
}
