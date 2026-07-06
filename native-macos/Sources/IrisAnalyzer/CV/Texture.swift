import Foundation
import Accelerate

/// Extração de características de textura sobre a íris normalizada:
/// LBP, GLCM (Haralick), energia de Gabor e nitidez.
enum Texture {

    // MARK: - LBP (Local Binary Patterns) uniforme, raio 1, 8 vizinhos
    static func lbpUniformity(_ img: GrayImage) -> Double {
        var uniform = 0, total = 0
        let n = [( -1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)]
        for y in 1 ..< img.height - 1 {
            for x in 1 ..< img.width - 1 {
                let c = img.at(x, y)
                var code = 0
                for (k, (dx, dy)) in n.enumerated() {
                    if img.at(x + dx, y + dy) >= c { code |= (1 << k) }
                }
                // uniformidade = nº de transições 0<->1 no padrão circular <= 2
                var transitions = 0
                for k in 0 ..< 8 {
                    let b0 = (code >> k) & 1
                    let b1 = (code >> ((k + 1) % 8)) & 1
                    if b0 != b1 { transitions += 1 }
                }
                if transitions <= 2 { uniform += 1 }
                total += 1
            }
        }
        return total > 0 ? Double(uniform) / Double(total) : 0
    }

    // MARK: - GLCM (Gray-Level Co-occurrence Matrix), 8 níveis, offset (1,0)
    static func glcm(_ img: GrayImage) -> (contrast: Double, energy: Double,
                                           homogeneity: Double, correlation: Double) {
        let levels = 8
        var m = [Double](repeating: 0, count: levels * levels)
        func q(_ v: Float) -> Int { min(levels - 1, max(0, Int(v / 256.0 * Float(levels)))) }
        var pairs = 0.0
        for y in 0 ..< img.height {
            for x in 0 ..< img.width - 1 {
                let i = q(img.at(x, y))
                let j = q(img.at(x + 1, y))
                m[i * levels + j] += 1
                m[j * levels + i] += 1   // simétrica
                pairs += 2
            }
        }
        guard pairs > 0 else { return (0, 0, 0, 0) }
        for k in 0 ..< m.count { m[k] /= pairs }

        var contrast = 0.0, energy = 0.0, homogeneity = 0.0
        var mu_i = 0.0, mu_j = 0.0
        for i in 0 ..< levels {
            for j in 0 ..< levels {
                let p = m[i * levels + j]
                let di = Double(i - j)
                contrast += di * di * p
                energy += p * p
                homogeneity += p / (1 + abs(di))
                mu_i += Double(i) * p
                mu_j += Double(j) * p
            }
        }
        var sd_i = 0.0, sd_j = 0.0
        for i in 0 ..< levels {
            for j in 0 ..< levels {
                let p = m[i * levels + j]
                sd_i += (Double(i) - mu_i) * (Double(i) - mu_i) * p
                sd_j += (Double(j) - mu_j) * (Double(j) - mu_j) * p
            }
        }
        sd_i = sqrt(sd_i); sd_j = sqrt(sd_j)
        var correlation = 0.0
        if sd_i > 1e-6 && sd_j > 1e-6 {
            for i in 0 ..< levels {
                for j in 0 ..< levels {
                    let p = m[i * levels + j]
                    correlation += ((Double(i) - mu_i) * (Double(j) - mu_j) * p) / (sd_i * sd_j)
                }
            }
        }
        return (contrast, energy, homogeneity, correlation)
    }

    // MARK: - Energia de Gabor (banco pequeno de orientações)
    static func gaborEnergy(_ img: GrayImage) -> Double {
        let orientations = [0.0, Double.pi/4, Double.pi/2, 3*Double.pi/4]
        let lambda = 6.0, sigma = 3.0, gamma = 0.5
        let k = 5 // kernel 11x11
        var totalEnergy = 0.0
        for theta in orientations {
            // gera kernel de Gabor (parte real)
            var kernel = [Double]()
            kernel.reserveCapacity((2*k+1)*(2*k+1))
            for yy in -k ... k {
                for xx in -k ... k {
                    let xr =  Double(xx) * cos(theta) + Double(yy) * sin(theta)
                    let yr = -Double(xx) * sin(theta) + Double(yy) * cos(theta)
                    let g = exp(-(xr*xr + gamma*gamma*yr*yr) / (2*sigma*sigma))
                        * cos(2 * Double.pi * xr / lambda)
                    kernel.append(g)
                }
            }
            // convolução esparsa (subamostrada) para eficiência
            var e = 0.0, n = 0.0
            let stepPix = 2
            for y in stride(from: k, to: img.height - k, by: stepPix) {
                for x in stride(from: k, to: img.width - k, by: stepPix) {
                    var acc = 0.0
                    var ki = 0
                    for yy in -k ... k {
                        for xx in -k ... k {
                            acc += Double(img.at(x + xx, y + yy)) * kernel[ki]
                            ki += 1
                        }
                    }
                    e += acc * acc
                    n += 1
                }
            }
            if n > 0 { totalEnergy += e / n }
        }
        return totalEnergy / Double(orientations.count)
    }

    // MARK: - Nitidez por variância do Laplaciano
    static func sharpness(_ img: GrayImage) -> Double {
        var lap = [Double]()
        lap.reserveCapacity(img.width * img.height)
        for y in 1 ..< img.height - 1 {
            for x in 1 ..< img.width - 1 {
                let v = 4 * Double(img.at(x, y))
                    - Double(img.at(x-1, y)) - Double(img.at(x+1, y))
                    - Double(img.at(x, y-1)) - Double(img.at(x, y+1))
                lap.append(v)
            }
        }
        guard lap.count > 1 else { return 0 }
        let mean = lap.reduce(0, +) / Double(lap.count)
        let varr = lap.reduce(0) { $0 + ($1 - mean) * ($1 - mean) } / Double(lap.count)
        return varr
    }

    // MARK: - Reflexo especular (fração de pixels muito brilhantes)
    static func specularRatio(_ img: GrayImage) -> Double {
        let (mean, std) = img.meanStd()
        let thr = min(250.0, mean + 2.5 * std)
        var bright = 0
        for p in img.pixels where Double(p) > thr { bright += 1 }
        return Double(bright) / Double(max(1, img.pixels.count))
    }
}
