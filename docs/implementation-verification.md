# Implementação e verificações

Data: 25/11/2026. Branch: `feat/pulso`. Base: `eaa3602` (`main`).

## Entregue

Quatro áreas com frontend Next.js e API FastAPI, PostgreSQL durável, sessões, papéis e RLS; feed por velocidade observada e versões de ranking; criadores com prévia/confirmação, remoção e restauração; regras versionadas e rascunhos; análises gerais e individuais com idempotência, cancelamento, retomada e exportação.

Adaptadores TikTok-Api e Ollama, classificação por metadados, processamento autorizado de mídia, cache por identidade e versão, outbox/Celery, filas de coleta/classificação/análise/multimodal/geração, agendamento, retenção, Docker Compose e configuração de telemetria. Sem calibração humana, classificações automáticas permanecem abaixo do limiar de elegibilidade estrita. O operador pode registrar rótulos revisados.

## Evidências executadas

- **43 testes Python passaram** usando PostgreSQL real em banco isolado. Incluem ranking, cursors, métricas nulas, regras, RLS entre workspaces, permissões, idempotência, cancelamento durante geração, referências inventadas, falha de provedor, mídia sintética e regressões da revisão.
- **14 testes Playwright passaram**, sete fluxos em desktop e celular, com API real. Incluem hashtags locais, rascunho, remover/desfazer, cancelar execução, modal/teclado/foco, troca de workspace e resposta tardia de paginação.
- TypeScript, mypy e Ruff passaram. O build de produção Next.js foi executado com sucesso.
- Auditoria axe de WCAG A/AA/2.1 AA nas quatro áreas em desktop e celular: **nenhuma violação detectada e nenhuma rolagem horizontal** nos oito cenários capturados. Isso não substitui uma avaliação humana completa de acessibilidade.
- `npm audit --omit=dev` e `pip-audit` do lock Python não encontraram vulnerabilidades conhecidas no momento da consulta. Dependências Python possuem hashes; npm usa lock e versões explícitas.
- FFmpeg processou vídeo sintético local de dois segundos: timestamps, frames e limpeza de temporários verificados. Campos dependentes de modelos ausentes permaneceram indisponíveis.
- Backup real criado e restaurado no banco novo `pulso_restore_20261125_verified`; revisão Alembic `0008`, tabelas e contagens conferidas. Nenhum banco existente foi sobrescrito.

Capturas e relatórios locais ficam em `.runtime/screenshots/`, `.runtime/accessibility.json` e `.runtime/pip-audit.json`, ignorados pelo Git por serem artefatos de execução.

## Revisão Standards

Revisor independente identificou três falhas funcionais e uma duplicação. Todas tratadas:

1. Regras antigas poderiam ser salvas em outro workspace durante uma troca. O formulário agora invalida o contexto, cancela cargas antigas e bloqueia edição até carregar o novo workspace. Requisições incluem o workspace esperado, conferido contra a sessão pelo servidor.
2. A lista de criadores poderia permanecer do workspace anterior. A área agora é remontada por workspace; a troca foi testada no navegador em desktop e celular.
3. Resolução de perfis ignorava a suspensão global da fonte. Saúde, suspensão e espera foram centralizadas na fronteira compartilhada de acesso externo; regressão HTTP verificada.
4. Fixtures e coleta usavam ingestões divergentes. Ambas agora usam `ingest_records`, incluindo a mesma proveniência e preservação de categorias.

## Revisão Spec

Revisor independente identificou quatro falhas funcionais. Todas tratadas:

1. Página antiga poderia substituir um recorte novo. Paginação agora é abortada e validada contra recorte e versão; regressão com resposta atrasada passou nos dois viewports.
2. Criadores além dos seis primeiros não seriam atualizados. O scheduler agora divide todos os perfis em lotes; teste com sete criadores passou.
3. Referências após a posição 50 eram rejeitadas. A seleção é validada contra a versão completa do ranking; teste com 60 vídeos e seleção da terceira página passou.
4. Falha do gerador textual ocultava mídia já processada. Evidências e análise visual são persistidas antes de gerar texto; exportação após falha preservou a mídia e seus timestamps.

## Pendências externas

- **TikTok:** configurar e validar acesso autorizado, rotas vivas, geografia e cobertura. A coleta real permanece desativada por padrão.
- **Modelos:** instalar pesos, validar licenças, português, visão, transcrição, OCR/postura e custo no hardware do piloto. Respostas reais desses modelos não foram avaliadas nesta máquina.
- **Docker/RabbitMQ:** Compose e configuração entregues; runtime Docker não disponível nesta máquina. Falha real de broker/worker, limites de container e subida completa permanecem para o piloto.
- **Aceitação longitudinal:** medir metas de cobertura e latência durante sete dias e calibrar os classificadores com amostra humana.
- **Referência visual:** a Library não pôde ser acessada; a interface segue os requisitos textuais. Não há verificação de paridade pixel a pixel.

O ticket 08 fica `ready-for-human` para essas validações e configurações. As evidências locais não são apresentadas como aprovação de operação pública ou de qualidade editorial dos modelos.
