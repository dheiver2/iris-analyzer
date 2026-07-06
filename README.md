# Iris Analyzer — Nativo macOS (Swift)

App **100% nativo** de análise de imagem da íris (bem-estar), escrito em
**Swift + SwiftUI** sobre os frameworks da Apple. Sem dependências externas.

> ⚠️ A iridologia **não é reconhecida pela ciência** como método de diagnóstico.
> Este app é **educacional/bem-estar** e não substitui avaliação médica.

## Stack nativa

| Camada | Tecnologia |
|---|---|
| Interface | **SwiftUI** (tema escuro, acento índigo/ciano) |
| Câmera | **AVFoundation** |
| Landmarks faciais | **Vision.framework** (`VNDetectFaceLandmarksRequest`) |
| Segmentação (Daugman) | **Swift + Accelerate** (`Daugman.swift`) |
| Normalização polar | **Swift** (`Normalization.swift`) |
| Textura (LBP/GLCM/Gabor) | **Swift + Accelerate** (`Texture.swift`) |
| Cor Lab | **Core Graphics** (`ColorFeatures.swift`) |
| Qualidade multi-fator | **Swift** (`Quality.swift`) |
| Laudo PDF | **Core Graphics / AppKit** (`PDFReport.swift`) |

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

Compila e roda como app nativo. O pipeline de visão computacional está
implementado em primeira versão funcional; os parâmetros (Daugman, Gabor,
limiares de qualidade) ainda passam por **calibração** para refinar os
resultados. Há um modo headless para validar o pipeline em imagens:

```bash
swift run IrisAnalyzer --analyze /caminho/para/foto.jpg
```
