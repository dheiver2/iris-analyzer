# Segurança e Privacidade

## Aviso de escopo

O Iris Analyzer **não é um dispositivo médico** e não realiza diagnóstico.
Veja o aviso completo no [README](README.md). Este documento trata apenas de
segurança de software e privacidade de dados, não de segurança clínica.

## Dados tratados pela aplicação

A aplicação processa **fotos do rosto/olho** capturadas pela câmera do
usuário, que podem ser consideradas dado biométrico sensível (LGPD, art. 5º,
II; GDPR, art. 9). Por isso:

- **Nenhum dado é enviado a servidores de terceiros.** Toda a captura e
  análise ocorrem localmente — no navegador (`getUserMedia`) e no backend
  Python rodando na máquina do próprio usuário (`127.0.0.1` por padrão).
- **Nada é persistido em disco pelo servidor por padrão.** O endpoint
  `/analisar` processa a imagem em memória. O endpoint `/laudo` grava
  arquivos temporários apenas para montar o PDF e os apaga (`shutil.rmtree`)
  antes de responder — inclusive em caso de erro.
- **O laudo em PDF só existe onde o usuário decidir salvá-lo.** É gerado sob
  demanda e entregue como download; o app não mantém histórico de laudos.
- Se você expuser o servidor além de `127.0.0.1` (ex.: `IRIS_WEB_HOST=0.0.0.0`
  ou atrás de um proxy), você passa a ser responsável por TLS, autenticação
  e pela base legal de tratamento desses dados perante LGPD/GDPR — isso não
  é fornecido pelo projeto.

## Boas práticas já aplicadas no backend web

- Limite de tamanho de upload (`IRIS_MAX_UPLOAD_MB`, padrão 15 MB) contra
  uploads abusivos.
- Validação do `content-type` declarado do upload antes de decodificar.
- CORS desabilitado por padrão (mesma-origem); habilitável apenas via
  `IRIS_CORS_ORIGINS` quando necessário.
- Handler global de exceções: erros internos nunca vazam stack trace/detalhes
  de implementação ao cliente — apenas uma mensagem genérica, com o detalhe
  completo indo para o log do servidor.
- Arquivos temporários por requisição, sempre removidos em `finally`.

## Relatar uma vulnerabilidade

Se você encontrar uma vulnerabilidade de segurança (não um bug funcional),
**não abra uma issue pública**. Em vez disso, envie um e-mail para o mantenedor
com uma descrição do problema e passos para reproduzir. Você pode esperar uma
resposta em até 5 dias úteis. Correções de severidade alta/crítica são
priorizadas; após o fix, a vulnerabilidade pode ser divulgada publicamente
com crédito ao relator (se desejado).
