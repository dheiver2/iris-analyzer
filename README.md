# Iris Analyzer — Nativo macOS (Swift)

Reescrita **100% nativa** do Iris Analyzer em **Swift + SwiftUI**, sem Python,
sem Qt, sem MediaPipe. Pipeline de visão computacional reimplementado sobre
frameworks da Apple.

> ⚠️ A iridologia **não é reconhecida pela ciência** como método de diagnóstico.
> Este app é **educacional/bem-estar** e não substitui avaliação médica.

## Stack nativa

| Camada | Original (Python) | Nativo (este projeto) |
|---|---|---|
| UI | PyQt6 | **SwiftUI** (tema escuro rebrandizado, acento índigo/ciano) |
| Câmera | OpenCV/AVFoundation | **AVFoundation** direto |
| Landmarks faciais | MediaPipe FaceLandmarker | **Vision.framework** (`VNDetectFaceLandmarksRequest`) |
| Segmentação (Daugman) | OpenCV/NumPy | **Swift + Accelerate** (`Daugman.swift`) |
| Normalização polar | NumPy | **Swift** (`Normalization.swift`) |
| Textura (LBP/GLCM/Gabor) | scikit-image | **Swift + Accelerate** (`Texture.swift`) |
| Cor Lab | OpenCV | **Core Graphics** (`ColorFeatures.swift`) |
| Qualidade multi-fator | Python | **Swift** (`Quality.swift`) |
| Laudo PDF | ReportLab | **Core Graphics/AppKit PDF** (`PDFReport.swift`) |

## Como compilar e rodar

Requer apenas **Command Line Tools** (não precisa Xcode completo):

```bash
swift build -c release       # compila
bash build_app.sh            # monta "Iris Analyzer.app" na Área de Trabalho
```

Primeira execução: clique com o botão direito no app → **Abrir** (não notarizado).
Autorize a câmera quando solicitado.

Para desenvolvimento rápido:

```bash
swift run                    # roda direto (a câmera pode exigir o bundle .app)
```

## Estrutura

```
Sources/IrisAnalyzer/
├── App.swift                 # @main SwiftUI App
├── Branding/Theme.swift      # identidade visual (rebranding)
├── Models/Analysis.swift     # tipos de dados do domínio
├── Camera/CameraController.swift   # AVFoundation
├── Vision/IrisDetector.swift # Vision (olhos/pupilas)
├── CV/
│   ├── GrayImage.swift        #   buffer de cinza + amostragem subpixel
│   ├── Daugman.swift          #   operador integro-diferencial
│   ├── Normalization.swift    #   rubber-sheet + pupila real
│   ├── Texture.swift          #   LBP, GLCM, Gabor, nitidez, reflexo
│   ├── ColorFeatures.swift    #   médias Lab
│   ├── Quality.swift          #   qualidade multi-fator + biometria
│   └── Pipeline.swift         #   orquestração + heatmap + comparação
├── Report/PDFReport.swift    # laudo PDF nativo
└── UI/                        # RootView, CameraPreview, EyeCardView, ViewModel
```

## Distribuição para licitação (próximos passos)

Hoje o app é assinado **ad-hoc**. Para distribuição/edital:

1. **Developer ID Application** (conta Apple Developer): troque `--sign -` por
   `--sign "Developer ID Application: SEU NOME (TEAMID)"` no `build_app.sh`.
2. **Notarização**:
   ```bash
   ditto -c -k --keepParent "Iris Analyzer.app" IrisAnalyzer.zip
   xcrun notarytool submit IrisAnalyzer.zip --apple-id ... --team-id ... --wait
   xcrun stapler staple "Iris Analyzer.app"
   ```
3. Gerar **.dmg** (`create-dmg`) para instalação.

## Estado atual (fase 1)

Compila e roda como app nativo. O pipeline de CV está implementado em primeira
versão funcional; os parâmetros (Daugman, Gabor, limiares de qualidade) ainda
precisam de **calibração comparando com a referência Python** para paridade de
resultados. Ver `CHANGELOG` do commit.
