# Contribuindo com o Iris Analyzer

Obrigado pelo interesse! Este é um projeto educacional/de bem-estar (não
médico — veja o aviso no [README](README.md)). Contribuições de código,
documentação, testes e revisão de literatura são bem-vindas.

## Como rodar localmente

```bash
git clone https://github.com/dheiver2/iris-analyzer.git
cd iris-analyzer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python3 download_model.py
pre-commit install
pytest -q
```

## Fluxo de contribuição

1. Abra uma issue descrevendo o bug/ideia antes de mudanças grandes, para
   alinhar escopo.
2. Crie um branch a partir de `main`: `git checkout -b minha-mudanca`.
3. Escreva/atualize testes em `tests/` para qualquer mudança de
   comportamento (o CI roda `pytest` em Python 3.9 e 3.11).
4. Rode `ruff check .` e `pytest -q` antes de abrir o PR — o `pre-commit`
   já faz isso automaticamente no commit.
5. Abra o Pull Request preenchendo o template. PRs pequenos e focados são
   revisados mais rápido.

## Estilo de código

- Python 3.9+, type hints em código novo (`from __future__ import annotations`
  já é usado no projeto).
- Nomes de funções/variáveis em português (convenção já usada no código:
  `detectar_face`, `avaliar_qualidade` etc.) — mantenha a consistência.
- Sem `except Exception: pass` silencioso; logue com `logging` quando o erro
  for esperado/recuperável (veja `iris_analyzer/server.py` como referência).
- Não adicione comentários óbvios; comente apenas decisões não triviais.

## Escopo científico

Qualquer texto/feature que sugira valor diagnóstico da iridologia será
recusado — o projeto é explícito sobre não ter validação científica como
método diagnóstico (Ernst, 2000). Melhorias em qualidade de imagem,
segmentação, biometria e engenharia de software são o foco.

## Dúvidas de segurança/privacidade

Não abra issue pública para vulnerabilidades — veja [SECURITY.md](SECURITY.md).
