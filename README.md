# Iris Analyzer

[![tests](https://github.com/dheiver2/iris-analyzer/actions/workflows/tests.yml/badge.svg)](https://github.com/dheiver2/iris-analyzer/actions/workflows/tests.yml)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)

Aplicação para **análise de imagem da íris** (bem-estar e autoconhecimento).
Captura pela webcam, segmenta a íris, extrai características e gera um
**laudo em PDF**. Vem em duas formas: **web app (recomendada)** e app desktop.

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

## Uso — Web app (recomendado)

```bash
python3 run_web.py
```

Abre no navegador (`http://127.0.0.1:8000`). A **câmera fica no navegador**
(getUserMedia) — sem permissões de sistema, sem empacotamento, funciona em
qualquer SO. O Python só analisa a imagem (backend FastAPI). É a forma mais
estável: elimina os problemas de TCC/assinatura/arquitetura do app nativo.

Também dá para rodar via Docker (só a web app, sem PyQt6):

```bash
docker build -t iris-analyzer .
docker run --rm -p 8000:8000 iris-analyzer
```

## Uso — App desktop (opcional)

```bash
python3 run.py
```

No macOS, autorize o acesso à câmera em
*Ajustes → Privacidade e Segurança → Câmera*.

### App com ícone (macOS)

Para criar **"Iris Analyzer.app"** (com ícone) na Área de Trabalho:

```bash
bash packaging/build_macos_app.sh
```

Primeira execução: clique com o botão direito no app → **Abrir** (app não assinado).

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
- **Biometria** (estimativa): diâmetro de íris/pupila (mm via HVID), razão
  pupilar e classificação (miose/normal/midríase)
- **Validações avançadas**: simetria entre olhos, razão pupilar fisiológica,
  índice de confiança da análise e comparação (heterocromia)
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
├── run_web.py              # inicia a WEB APP (python3 run_web.py) — recomendado
├── run.py                  # inicia o app desktop (PyQt6)
├── download_model.py       # baixa o modelo do MediaPipe
├── web/index.html          # frontend web (câmera no navegador)
├── iris_analyzer/          # pacote
│   ├── server.py           #   backend web (FastAPI) — reusa a análise
│   ├── desktop_app.py      #   aplicativo desktop (PyQt6)
│   ├── iris_segmentation.py#   segmentação íris/pupila (MediaPipe)
│   ├── iris_features.py     #   Daugman + features + qualidade
│   ├── iris_advanced.py     #   pupila real, CLAHE, Frangi, lacunas, heatmap
│   ├── iris_quality.py      #   qualidade multi-fator
│   ├── iris_metrics.py      #   biometria, validações avançadas, comparação
│   ├── iris_map.py          #   mapa de zonas (iridologia)
│   ├── captura_guiada.py    #   guia de captura + auto-disparo
│   ├── pdf_report.py        #   laudo PDF
│   ├── config.py            #   configuração central
│   └── validation.py        #   validações e exceções
├── tests/                  # pytest
└── docs/                   # GitHub Pages
```

## Privacidade

Nenhuma imagem ou laudo é enviado a servidores de terceiros: a captura e a
análise rodam localmente (navegador + backend Python na própria máquina).
Nada é persistido em disco pelo servidor além de arquivos temporários que são
apagados antes da resposta. Detalhes e variáveis de configuração de
segurança (limite de upload, CORS, host/porta) em [SECURITY.md](SECURITY.md)
e [.env.example](.env.example).

## Desenvolvimento

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest -q                 # roda a suíte de testes
ruff check .              # lint
pre-commit install        # roda lint automaticamente antes de cada commit
```

Estrutura de qualidade:
- `config.py` — configuração central (sobrescreve por env `IRIS_*`)
- `validation.py` — validações de entrada e exceções (`IrisError` e subclasses)
- `tests/` — testes com pytest (validação, features, mapa, técnicas, PDF)
- CI em `.github/workflows/tests.yml` (testes + lint)

Quer contribuir? Veja [CONTRIBUTING.md](CONTRIBUTING.md) e o
[CHANGELOG.md](CHANGELOG.md). Este projeto segue um
[Código de Conduta](CODE_OF_CONDUCT.md).

## Boas fotos

Olho centralizado, bem aberto, boa iluminação difusa (sem flash direto),
câmera próxima e foco nítido na íris.
