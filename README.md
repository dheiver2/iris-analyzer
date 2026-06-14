# Iris Analyzer (educacional)

Abre a webcam, tira uma foto e analisa a íris usando técnicas de visão
computacional inspiradas na **iridologia** (cores, padrões e textura).

> ⚠️ **Aviso importante**
> A iridologia **não é reconhecida pela ciência** como método de diagnóstico.
> Revisões sistemáticas (ex.: Ernst, 2000) concluíram que ela não detecta
> doenças de forma confiável. Este projeto é **educacional/experimental**:
> extrai características objetivas da imagem e as descreve. **Nada aqui é
> diagnóstico médico.** Procure sempre um profissional de saúde.

## Instalação

```bash
cd iris-analyzer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

O projeto tem **duas versões**:

| | V1 (`app.py`) | V2 (`app_v2.py`) — recomendada |
|---|---|---|
| Detecção da íris | Círculos de Hough (frágil) | **MediaPipe FaceLandmarker** (478 landmarks, sub-pixel) |
| Robustez a ângulo/luz | baixa | alta |
| Normalização | — | **Daugman rubber-sheet** (íris desenrolada em polar) |
| Features | bordas + cor HSV | **Gabor + LBP + GLCM + cor Lab** |
| Qualidade da foto | — | nitidez (Laplaciano) + reflexos |

## Uso

```bash
# V2 (recomendada): webcam (ESPAÇO foto, ESC cancela) -> análise
python app_v2.py
python app_v2.py --imagem olho.jpg   # ou imagem existente

# V1 (protótipo simples)
python app.py
```

No macOS, autorize o acesso à câmera em
*Ajustes → Privacidade e Segurança → Câmera*.

> **Modelo:** a V2 usa `face_landmarker.task` (MediaPipe). Se faltar, baixe:
> ```bash
> curl -sL -o face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
> ```

## O que a V2 gera

- `*_anotada.jpg` — íris/pupila/landmarks marcados
- `*_daugman_direito.jpg` / `*_daugman_esquerdo.jpg` — íris normalizada (polar)
- Relatório no terminal: cor (Lab), Gabor, LBP, GLCM, densidade de fibras,
  nitidez, % de reflexo e checagem de qualidade

## Arquivos

- `capture.py` — captura pela webcam
- `iris_segmentation.py` — **V2** segmentação com MediaPipe
- `iris_features.py` — **V2** Daugman + features (Gabor/LBP/GLCM/Lab/qualidade)
- `app_v2.py` — **V2** fluxo principal
- `iris_analysis.py` / `app.py` — V1 (protótipo)

## Boas fotos

Olho centralizado, bem aberto, boa iluminação difusa (sem flash direto),
câmera próxima e foco nítido na íris.
