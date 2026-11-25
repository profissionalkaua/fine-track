# Implementação e verificações

Data: 25/11/2026. Branch: `feat/pulso`. Base: `eaa3602` (`main`).

## Continuação após `c4c4c0e`

- Criadores exibem percentil por velocidade com no mínimo dez posts do próprio canal, mesma cobertura de janela e duração observada com diferença de até uma hora. Empates usam posição média. A amostra acompanha cada vídeo; amostras insuficientes produzem `null`.
- Resultados e exportações informam disponibilidade por referência; a lista agregada indica sinais ausentes em ao menos uma referência. Sem referências, todos ficam indisponíveis. Frames extraídos deixam de ser declarados ausentes mesmo quando visão está indisponível. Resultados parciais e falhas de geração preservam essa informação.
- CI da aplicação entregue com PostgreSQL, tipos, Ruff, build e 14 cenários de navegador. Playwright agora inicia servidores em Windows/Linux e recusa reutilizar processos desconhecidos na CI.
- CI de containers entregue com credenciais efêmeras, subida completa, consumo de job por broker e repetição após reinício. Consultas de saúde direcionam explicitamente os workers de análise e geração. **Ainda não executada no GitHub:** não houve push desta branch nesta etapa e não há Docker/WSL local. Isso não valida perda de mensagem durante processamento.
- Ollama portátil `0.40.18` instalado com SHA256 oficial conferido, nuvem desativada e API em loopback. Qwen2.5 `1.5b` Apache 2.0, digest `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`: adaptador real gerou um roteiro em 12,69 s e cinco ideias em 107,05 s, ambos com esquema e referências válidos. Uma análise individual via API → worker → modelo → exportação completou em 38,25 s. São medições sintéticas individuais, não p95 nem avaliação editorial.
- Transcrição CPU/int8 instalada por lock adicional com hashes; pesos MIT do Whisper tiny fixados por revisão. Regressão real offline confirmou que silêncio não produz fala. PyAV foi fixado em `18.1.0` após reproduzir a incompatibilidade do `19` com faster-whisper `1.2.1`. `pip check` e auditoria do lock opcional passaram, sem vulnerabilidades conhecidas na consulta.
- Fluxo completo com vídeo azul e áudio silencioso sintéticos autorizados: API → worker → FFmpeg → Whisper → geração → exportação completou em 22,11 s. Áudio e frames ficaram disponíveis; apenas `retention_analytics` permaneceu em `unavailable_signals`. Artefato: `.runtime/ollama/media-api-smoke.json`. Visão por modelo permanece indisponível, separadamente da extração de frames.
- Configuração local `.env` e worker atualizados; coleta externa e classificação calibrada continuam desativadas. Testes mantêm provedores externos desativados independentemente desses modelos locais.

Revisão independente Standards: nenhuma violação documentada; apontou que a CI não verificava especificamente o worker de geração. Corrigido com consulta direcionada e tentativas limitadas. Revisão Spec: apontou ausência de disponibilidade na saída parcial por amostra insuficiente. Corrigido com teste HTTP vermelho/verde. Nenhum crescimento de escopo identificado.

Detalhes de reprodução e limites: [operações](operations.md). Artefatos locais: `.runtime/ollama/smoke.json`, `smoke-general.json`, `api-smoke.json`, `.runtime/models/faster-whisper-tiny/manifest.json` e `.runtime/transcription-audit.json`.

## Entregue

Quatro áreas com frontend Next.js e API FastAPI, PostgreSQL durável, sessões, papéis e RLS; feed por velocidade observada e versões de ranking; criadores com prévia/confirmação, remoção e restauração; regras versionadas e rascunhos; análises gerais e individuais com idempotência, cancelamento, retomada e exportação.

Adaptadores TikTok-Api e Ollama, classificação por metadados, processamento autorizado de mídia, cache por identidade e versão, outbox/Celery, filas de coleta/classificação/análise/multimodal/geração, agendamento, retenção, Docker Compose e configuração de telemetria. Sem calibração humana, classificações automáticas permanecem abaixo do limiar de elegibilidade estrita. O operador pode registrar rótulos revisados.

## Evidências executadas

- **46 testes Python passaram** usando PostgreSQL real em banco isolado, incluindo o teste opcional com pesos locais do Whisper. Incluem ranking, cursors, métricas nulas, regras, RLS entre workspaces, permissões, idempotência, cancelamento durante geração, referências inventadas, falha de provedor, mídia sintética, percentis e regressões da revisão. Sem selecionar pesos opcionais, a suíte principal executa 45 testes e ignora um.
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
- **Modelos:** texto e transcrição instalados e exercitados com entradas sintéticas. Permanecem precisão de fala/qualidade editorial, visão, OCR/postura e custo/latência no hardware do piloto. Os testes executados não aprovam essas qualidades.
- **Docker/RabbitMQ:** Compose e configuração entregues; runtime Docker não disponível nesta máquina. Falha real de broker/worker, limites de container e subida completa permanecem para o piloto.
- **Aceitação longitudinal:** medir metas de cobertura e latência durante sete dias e calibrar os classificadores com amostra humana.
- **Referência visual:** a Library não pôde ser acessada; a interface segue os requisitos textuais. Não há verificação de paridade pixel a pixel.

O ticket 08 fica `ready-for-human` para essas validações e configurações. As evidências locais não são apresentadas como aprovação de operação pública ou de qualidade editorial dos modelos.
