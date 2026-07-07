import Foundation
import CoreGraphics
import ImageIO

/// Runner de testes em Swift puro, acionado por `IrisAnalyzer --test`.
/// Não depende de XCTest/Swift Testing (indisponíveis apenas com Command Line
/// Tools). Cobre os componentes determinísticos do pipeline de CV.
enum SelfTest {
    private static var passed = 0
    private static var failed = 0
    private static var currentSuite = ""

    private static func suite(_ name: String, _ body: () -> Void) {
        currentSuite = name
        print("▸ \(name)")
        body()
    }

    private static func expect(_ cond: Bool, _ name: String, _ detail: String = "") {
        if cond {
            passed += 1
            print("  ✓ \(name)")
        } else {
            failed += 1
            print("  ✗ \(name)  \(detail)")
        }
    }

    private static func near(_ a: Double, _ b: Double, _ tol: Double) -> Bool { abs(a - b) <= tol }
    private static func near(_ a: Float, _ b: Float, _ tol: Float) -> Bool { abs(a - b) <= tol }

    /// Executa toda a suíte; retorna código de saída (0 = tudo passou).
    static func run() -> Int32 {
        passed = 0; failed = 0
        print("=== Iris Analyzer — testes do pipeline ===\n")
        grayImage()
        daugman()
        texture()
        qualityBiometrics()
        normalizationAndColor()
        icon()
        print("\n=== \(passed) passaram · \(failed) falharam ===")
        return failed == 0 ? 0 : 1
    }

    // MARK: GrayImage
    private static func grayImage() {
        suite("GrayImage") {
            let img = GrayImage(width: 2, height: 2, pixels: [10, 20, 30, 40])
            expect(img.at(0, 0) == 10 && img.at(1, 1) == 40, "at() indexa correto")
            expect(img.at(-1, 0) == 0 && img.at(5, 5) == 0, "at() fora dos limites = 0")
            expect(near(img.sample(0.5, 0.5), 25, 1e-6), "amostra bilinear no centro = 25")
            expect(near(img.sample(0, 0), 10, 1e-6), "amostra no vértice = valor exato")

            let big = GrayImage(width: 3, height: 3, pixels: [1,2,3, 4,5,6, 7,8,9])
            let c = big.crop(x: 1, y: 1, w: 2, h: 2)
            expect(c.width == 2 && c.height == 2 && c.pixels == [5,6,8,9], "crop recorta correto")
            let clamp = GrayImage(width: 2, height: 2, pixels: [1,2,3,4]).crop(x: -1, y: -1, w: 10, h: 10)
            expect(clamp.width == 2 && clamp.height == 2, "crop clampeia aos limites")

            let (m, s) = Synth.constant(w: 8, h: 8, value: 100).meanStd()
            expect(near(m, 100, 1e-3) && near(s, 0, 1e-3), "meanStd de imagem constante")

            let cg = Synth.disk(w: 32, h: 24, cx: 16, cy: 12, r: 6, bg: 30, fg: 200).cgImage()
            expect(cg?.width == 32 && cg?.height == 24, "cgImage preserva dimensões")
        }
    }

    // MARK: Daugman + pupila
    private static func daugman() {
        suite("Daugman & pupila") {
            let R = 30.0
            let disk = Synth.disk(w: 160, h: 160, cx: 80, cy: 80, r: R, bg: 30, fg: 210)
            let (r, resp) = Daugman.bestRadius(disk, cx: 80, cy: 80, rMin: 10, rMax: 60, samples: 240)
            expect(near(r, R, 3.0) && resp > 0, "bestRadius acha borda de raio \(Int(R))",
                   "achou r=\(String(format: "%.1f", r))")

            let disk2 = Synth.disk(w: 200, h: 200, cx: 100, cy: 100, r: 40, bg: 25, fg: 200)
            let circ = Daugman.refine(disk2, cx0: 104, cy0: 97, rMin: 25, rMax: 60,
                                      searchRadius: 6, samples: 180)
            expect(near(circ.r, 40, 4.0) && near(circ.cx, 100, 6.0) && near(circ.cy, 100, 6.0),
                   "refine recupera centro e raio",
                   "r=\(String(format: "%.1f", circ.r)) c=(\(Int(circ.cx)),\(Int(circ.cy)))")

            let eye = Synth.eye(w: 220, h: 220, cx: 110, cy: 110, irisR: 60, pupilR: 22)
            let pup = PupilFinder.detect(eye, irisGuess: Circle(cx: 110, cy: 110, r: 60))
            expect(near(pup.cx, 110, 10) && near(pup.cy, 110, 10)
                   && pup.r > 9 && pup.r < 51, "PupilFinder acha pupila escura central",
                   "r=\(String(format: "%.1f", pup.r))")
        }
    }

    // MARK: Textura
    private static func texture() {
        suite("Textura") {
            expect(near(Texture.sharpness(Synth.constant(w: 40, h: 40, value: 128)), 0, 1e-6),
                   "nitidez = 0 em imagem constante")
            let flat = Synth.constant(w: 60, h: 60, value: 128)
            let d = Synth.disk(w: 60, h: 60, cx: 30, cy: 30, r: 12, bg: 20, fg: 220)
            expect(Texture.sharpness(d) > Texture.sharpness(flat), "nitidez maior com bordas")

            let g = Texture.glcm(Synth.constant(w: 32, h: 32, value: 100))
            expect(near(g.contrast, 0, 1e-6) && g.energy > 0.9, "GLCM constante: contraste 0, energia alta")

            let u = Texture.lbpUniformity(Synth.disk(w: 40, h: 40, cx: 20, cy: 20, r: 10, bg: 30, fg: 200))
            expect(u >= 0 && u <= 1, "LBP uniformidade em [0,1]")

            var px = [Float](repeating: 40, count: 40*40)
            for y in 18...21 { for x in 18...21 { px[y*40+x] = 255 } }
            let ratio = Texture.specularRatio(GrayImage(width: 40, height: 40, pixels: px))
            expect(ratio > 0 && ratio < 0.2, "reflexo especular detecta ponto brilhante")

            let ge = Texture.gaborEnergy(Synth.disk(w: 48, h: 48, cx: 24, cy: 24, r: 14, bg: 30, fg: 200))
            expect(ge >= 0, "energia de Gabor não-negativa")
        }
    }

    // MARK: Qualidade & biometria
    private static func qualityBiometrics() {
        func seg(_ irisR: Double, _ pupilR: Double, offset: Double = 0) -> IrisSegmentation {
            IrisSegmentation(iris: Circle(cx: 100, cy: 100, r: irisR),
                             pupil: Circle(cx: 100 + offset, cy: 100, r: pupilR))
        }
        func offAngle(_ s: IrisSegmentation) -> Double {
            let img = Synth.eye(w: 220, h: 220, cx: 100, cy: 100, irisR: 80, pupilR: 32)
            let (norm, mask) = Normalization.unwrap(img, seg: s)
            let g = Texture.glcm(norm)
            let tex = TextureFeatures(gaborEnergy: 0, lbpUniformity: 0, glcmContrast: g.contrast,
                glcmEnergy: g.energy, glcmHomogeneity: g.homogeneity, glcmCorrelation: g.correlation,
                sharpness: 100, specularRatio: 0)
            return Quality.assess(full: img, seg: s, normalized: norm, mask: mask, texture: tex).offAngle
        }

        suite("Qualidade & biometria") {
            expect(near(seg(100, 40).pupillaryRatio, 0.4, 1e-9), "razão pupilar = 0.4")

            let normal = BiometricsEstimator.estimate(seg: seg(100, 40))
            expect(near(normal.irisDiameterMM, BiometricsEstimator.hvidMM, 1e-6)
                   && near(normal.pupilDiameterMM, BiometricsEstimator.hvidMM * 0.4, 1e-6)
                   && normal.classificacao == "normal", "biometria escala por HVID; razão 0.4 = normal")
            expect(BiometricsEstimator.estimate(seg: seg(100, 20)).classificacao.contains("miose"),
                   "razão 0.2 = miose")
            expect(BiometricsEstimator.estimate(seg: seg(100, 60)).classificacao.contains("midríase"),
                   "razão 0.6 = midríase")

            let s = seg(80, 32)
            let img = Synth.eye(w: 220, h: 220, cx: 100, cy: 100, irisR: 80, pupilR: 32)
            let (norm, mask) = Normalization.unwrap(img, seg: s)
            let g = Texture.glcm(norm)
            let tex = TextureFeatures(gaborEnergy: Texture.gaborEnergy(norm),
                lbpUniformity: Texture.lbpUniformity(norm), glcmContrast: g.contrast,
                glcmEnergy: g.energy, glcmHomogeneity: g.homogeneity, glcmCorrelation: g.correlation,
                sharpness: Texture.sharpness(norm), specularRatio: Texture.specularRatio(norm))
            let q = Quality.assess(full: img, seg: s, normalized: norm, mask: mask, texture: tex)
            let factorsOk = [q.focus, q.occlusion, q.reflection, q.offAngle, q.dilation, q.size]
                .allSatisfy { $0 >= 0 && $0 <= 1 }
            expect(q.score >= 0 && q.score <= 100 && factorsOk, "score em [0,100] e fatores em [0,1]")

            expect(offAngle(seg(80, 32, offset: 0)) > offAngle(seg(80, 32, offset: 40)),
                   "concentricidade melhora o fator off-angle")
        }
    }

    // MARK: Normalização & cor
    private static func normalizationAndColor() {
        suite("Normalização & cor") {
            let img = Synth.eye(w: 220, h: 220, cx: 110, cy: 110, irisR: 70, pupilR: 28)
            let s = IrisSegmentation(iris: Circle(cx: 110, cy: 110, r: 70),
                                     pupil: Circle(cx: 110, cy: 110, r: 28))
            let (norm, mask) = Normalization.unwrap(img, seg: s)
            expect(norm.width == Normalization.angularResolution
                   && norm.height == Normalization.radialResolution
                   && mask.count == norm.width * norm.height && mask.allSatisfy { $0 },
                   "unwrap: dimensões corretas e máscara toda válida")

            var px = [Float](repeating: 150, count: 220*220)
            for y in 0..<220 { for x in 0..<220 {
                if hypot(Double(x)-110, Double(y)-110).rounded() == 50 { px[y*220+x] = 255 }
            }}
            let (_, mask2) = Normalization.unwrap(GrayImage(width: 220, height: 220, pixels: px), seg: s)
            expect(mask2.contains(false), "unwrap marca pixels saturados como inválidos")

            let heat = Heatmap.make(Synth.eye(w: 100, h: 60, cx: 50, cy: 30, irisR: 20, pupilR: 8))
            expect(heat?.width == 100 && heat?.height == 60, "heatmap preserva dimensões")

            // pipeline completo numa imagem sem rosto não deve quebrar
            if let cg = Synth.disk(w: 128, h: 128, cx: 64, cy: 64, r: 20, bg: 30, fg: 200).cgImage() {
                let frame = AnalysisPipeline.analyze(cgImage: cg)
                expect(frame.eyes.isEmpty && frame.confianca == 0,
                       "analyze() sem rosto retorna vazio sem crashar")
            } else { expect(false, "cgImage sintético") }

            // cinza neutro => a*,b* ~ 0
            let w = 100, h = 100
            var rgba = [UInt8](repeating: 0, count: w*h*4)
            for i in 0..<w*h { rgba[i*4]=128; rgba[i*4+1]=128; rgba[i*4+2]=128; rgba[i*4+3]=255 }
            let cs = CGColorSpaceCreateDeviceRGB()
            if let ctx = CGContext(data: &rgba, width: w, height: h, bitsPerComponent: 8,
                                   bytesPerRow: w*4, space: cs,
                                   bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue),
               let cg = ctx.makeImage() {
                let color = ColorAnalysis.meanLab(cgImage: cg,
                    seg: IrisSegmentation(iris: Circle(cx: 50, cy: 50, r: 40),
                                          pupil: Circle(cx: 50, cy: 50, r: 15)))
                expect(near(color.a, 0, 2.0) && near(color.b, 0, 2.0), "cor Lab de cinza é neutra (a,b≈0)")
            } else { expect(false, "contexto RGB de teste") }
        }
    }

    // MARK: Ícone
    private static func icon() {
        suite("IconMaker") {
            let path = NSTemporaryDirectory() + "iris_selftest_icon.png"
            IconMaker.write(to: path)
            var ok = FileManager.default.fileExists(atPath: path)
            if ok, let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
               let img = CGImageSourceCreateImageAtIndex(src, 0, nil) {
                ok = img.width == 1024 && img.height == 1024
            } else { ok = false }
            expect(ok, "gera PNG 1024×1024 válido")
            try? FileManager.default.removeItem(atPath: path)
        }
    }
}
