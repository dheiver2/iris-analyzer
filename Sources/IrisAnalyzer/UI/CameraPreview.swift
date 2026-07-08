import SwiftUI
import AppKit
import CoreGraphics

/// Exibe o quadro atual da câmera com overlay dos círculos detectados.
struct CameraPreview: View {
    let image: CGImage?
    let eyes: [EyeAnalysis]

    var body: some View {
        GeometryReader { geo in
            ZStack {
                if let image {
                    Image(decorative: image, scale: 1, orientation: .up)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .overlay(overlay(imageSize: CGSize(width: image.width, height: image.height),
                                         container: geo.size))
                } else {
                    VStack(spacing: 12) {
                        Image(systemName: "camera.metering.center.weighted")
                            .font(.system(size: 40, weight: .thin))
                            .foregroundStyle(Brand.faint)
                        Text("Iniciando câmera…")
                            .foregroundStyle(Brand.muted)
                    }
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(Color.black)
        }
    }

    /// Desenha íris (acento) e pupila (ciano) sobre o preview, respeitando o
    /// aspect-fit da imagem.
    private func overlay(imageSize: CGSize, container: CGSize) -> some View {
        Canvas { ctx, size in
            let scale = min(size.width / imageSize.width, size.height / imageSize.height)
            let offX = (size.width - imageSize.width * scale) / 2
            let offY = (size.height - imageSize.height * scale) / 2
            func map(_ p: CGPoint) -> CGPoint {
                CGPoint(x: offX + p.x * scale, y: offY + p.y * scale)
            }
            for e in eyes {
                let iris = e.segmentation.iris, pupil = e.segmentation.pupil
                let irisRect = CGRect(
                    x: map(CGPoint(x: iris.cx - iris.r, y: iris.cy - iris.r)).x,
                    y: map(CGPoint(x: iris.cx - iris.r, y: iris.cy - iris.r)).y,
                    width: iris.r * 2 * scale, height: iris.r * 2 * scale)
                ctx.stroke(Path(ellipseIn: irisRect),
                           with: .color(Brand.accent), lineWidth: 2)
                let pupRect = CGRect(
                    x: map(CGPoint(x: pupil.cx - pupil.r, y: pupil.cy - pupil.r)).x,
                    y: map(CGPoint(x: pupil.cx - pupil.r, y: pupil.cy - pupil.r)).y,
                    width: pupil.r * 2 * scale, height: pupil.r * 2 * scale)
                ctx.stroke(Path(ellipseIn: pupRect),
                           with: .color(Brand.accent2), lineWidth: 1.5)
            }
        }
    }
}
