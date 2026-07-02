# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
este projeto segue [SemVer](https://semver.org/lang/pt-BR/) (com um app
desktop/web, "release" se refere a tags do repositório, não a um pacote no
PyPI).

## [Não lançado]

### Adicionado
- `SECURITY.md` com política de privacidade (dados de rosto/olho não são
  persistidos nem enviados a terceiros) e processo de relato de
  vulnerabilidades.
- Limite de tamanho de upload e validação de content-type no backend web
  (`IRIS_MAX_UPLOAD_MB`).
- CORS explícito e desabilitado por padrão (`IRIS_CORS_ORIGINS`).
- Handler global de exceções no FastAPI: erros internos não vazam detalhes
  ao cliente.
- Endpoint `GET /health`.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `.env.example`, templates de
  issue/PR.
- Lint com `ruff` e hooks de `pre-commit`; job de lint no CI.
- `Dockerfile` para rodar a web app em contêiner.

### Corrigido
- Vazamento de diretório temporário no endpoint `/laudo`: arquivos gerados
  para montar o PDF agora são sempre removidos (`finally`), inclusive em
  caso de erro.

## [1.0.0] — 2026-06-17

### Adicionado
- Web app (FastAPI + câmera no navegador via `getUserMedia`), recomendada
  como forma principal de uso — elimina os problemas de permissão de
  câmera/assinatura do app desktop no macOS.
- App desktop (PyQt6) com captura guiada, malha facial e empacotamento
  `.app` para macOS.
- Segmentação da íris/pupila com MediaPipe FaceLandmarker + ajuste de
  círculo por mínimos quadrados + refino de borda por Daugman.
- Extração de features (cor Lab, Gabor, LBP, GLCM, nitidez, reflexo),
  detecção de lacunas/fibras (filtro de Frangi) e mapa de calor.
- Avaliação de qualidade multi-fator (foco, oclusão, reflexo, ângulo,
  dilatação, tamanho) baseada na literatura de reconhecimento de íris
  (Daugman 2004, Kalka et al.).
- Biometria estimada (diâmetro de íris/pupila via HVID, razão pupilar) e
  validações avançadas (simetria entre olhos, plausibilidade fisiológica,
  índice de confiança).
- Mapa de zonas (relógio de 12 setores da iridologia tradicional) — sem
  valor diagnóstico.
- Geração de laudo em PDF.
- Suíte de testes com pytest e CI no GitHub Actions.
