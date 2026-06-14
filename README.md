# Iris Analyzer

Aplicativo desktop para **análise de imagem da íris** (bem-estar e
autoconhecimento). Captura pela webcam com **captura guiada**, segmenta a íris,
extrai características e gera um **laudo em PDF**.

> ⚠️ **Aviso importante**
> A iridologia **não é reconhecida pela ciência** como método de diagnóstico.
> Revisões sistemáticas (ex.: Ernst, 2000) concluíram que ela não detecta
> doenças de forma confiável. Este projeto é **educacional/bem-estar**: extrai
> características objetivas de imagem e as descreve. **Nada aqui é diagnóstico
> médico.** Procure sempre um profissional de saúde.

## Instalação

```bash
cd iris-analyzer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Modelo do MediaPipe (necessário; ~3,7 MB)
curl -sL -o face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
```

## Uso

```bash
python3 desktop_app.py
```

No macOS, autorize o acesso à câmera em
*Ajustes → Privacidade e Segurança → Câmera*.

Com a **captura guiada** ligada, encaixe o rosto no oval; quando a imagem está
boa (íris grande, nítida, centralizada, sem reflexo) o app captura e analisa
sozinho. Preencha os dados do cliente e clique em **Gerar Laudo PDF**.

## Como funciona

- **Segmentação** da íris/pupila com **MediaPipe FaceLandmarker** (478 landmarks)
- **Pupila real** detectada por limiar + circularidade; **CLAHE** para iluminação
- **Normalização de Daugman** (íris desenrolada em coordenadas polares)
- **Features**: cor (Lab), Gabor, LBP, GLCM, nitidez, reflexo
- **Marcas**: lacunas como blobs + fibras via **filtro de Frangi**; **mapa de calor**
- **Mapa de zonas** (relógio de 12 setores da iridologia tradicional) com
  máscara de pálpebra/cílio e limiar absoluto — *sem valor diagnóstico*

## Arquivos

- `desktop_app.py` — aplicativo principal (PyQt6)
- `iris_segmentation.py` — segmentação da íris/pupila (MediaPipe)
- `iris_features.py` — Daugman + features + qualidade
- `iris_advanced.py` — pupila real, CLAHE, Frangi, lacunas, heatmap
- `iris_map.py` — mapa de zonas (iridologia)
- `captura_guiada.py` — guia de captura e auto-disparo por qualidade
- `pdf_report.py` — geração do laudo PDF

## Boas fotos

Olho centralizado, bem aberto, boa iluminação difusa (sem flash direto),
câmera próxima e foco nítido na íris.
