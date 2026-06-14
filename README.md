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
python3 download_model.py
```

## Uso

```bash
python3 run.py
```

No macOS, autorize o acesso à câmera em
*Ajustes → Privacidade e Segurança → Câmera*.

Com a **captura guiada** ligada, encaixe o rosto no oval; quando a imagem está
boa (íris grande, nítida, centralizada, sem reflexo) o app captura e analisa
sozinho. Preencha os dados do cliente e clique em **Gerar Laudo PDF**.

## Como funciona

- **Segmentação** da íris/pupila com **MediaPipe FaceLandmarker** (478 landmarks),
  com **ajuste de círculo por mínimos quadrados** e **refino de borda pelo
  operador integro-diferencial de Daugman** (precisão sub-pixel)
- **Pupila real** detectada por limiar + circularidade; **CLAHE** para iluminação
- **Normalização de Daugman** (íris desenrolada em coordenadas polares)
- **Features**: cor (Lab), Gabor, LBP, GLCM, nitidez, reflexo
- **Marcas**: lacunas como blobs + fibras via **filtro de Frangi**; **mapa de calor**
- **Qualidade multi-fator** (0–100): foco por alta-frequência (FFT), oclusão,
  reflexo especular (limiar adaptativo), off-angle, dilatação pupilar e tamanho
- **Mapa de zonas** (relógio de 12 setores da iridologia tradicional) com
  máscara de pálpebra/cílio e limiar absoluto — *sem valor diagnóstico*

### Base nos métodos da literatura

A avaliação de qualidade segue os fatores consagrados em reconhecimento de íris
(foco/desfoco, oclusão, reflexo especular, ângulo, dilatação, contagem de pixels):
- Daugman, *How Iris Recognition Works* (2004) — foco por energia de alta frequência
- Kalka et al. — estimação e fusão de fatores de qualidade da íris
- Literatura de remoção de reflexo especular em imagens de íris (limiar adaptativo)

## Estrutura

```
iris-analyzer/
├── run.py                  # inicia o app  (python3 run.py)
├── download_model.py       # baixa o modelo do MediaPipe
├── iris_analyzer/          # pacote
│   ├── desktop_app.py      #   aplicativo principal (PyQt6)
│   ├── iris_segmentation.py#   segmentação íris/pupila (MediaPipe)
│   ├── iris_features.py     #   Daugman + features + qualidade
│   ├── iris_advanced.py     #   pupila real, CLAHE, Frangi, lacunas, heatmap
│   ├── iris_quality.py      #   qualidade multi-fator
│   ├── iris_map.py          #   mapa de zonas (iridologia)
│   ├── captura_guiada.py    #   guia de captura + auto-disparo
│   ├── pdf_report.py        #   laudo PDF
│   ├── config.py            #   configuração central
│   └── validation.py        #   validações e exceções
├── tests/                  # pytest
└── docs/                   # GitHub Pages
```

## Desenvolvimento

```bash
pip install -r requirements.txt pytest
pytest -q          # roda a suíte de testes
```

Estrutura de qualidade:
- `config.py` — configuração central (sobrescreve por env `IRIS_*`)
- `validation.py` — validações de entrada e exceções (`IrisError` e subclasses)
- `tests/` — testes com pytest (validação, features, mapa, técnicas, PDF)
- CI em `.github/workflows/tests.yml`

## Boas fotos

Olho centralizado, bem aberto, boa iluminação difusa (sem flash direto),
câmera próxima e foco nítido na íris.
