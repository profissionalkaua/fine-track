# Implementação e verificações

Data: 25/11/2026. Branch: `feat/pulso`. Base: `eaa3602` (`main`).

## Continuação após `c4c4c0e`

- Criadores exibem percentil por velocidade com no mínimo dez posts do próprio canal, mesma cobertura de janela e duração observada com diferença de até uma hora. Empates usam posição média. A amostra acompanha cada vídeo; amostras insuficientes produzem `null`.
- Resultados e exportações informam disponibilidade por referência; a lista agregada indica sinais ausentes em ao menos uma referência. Sem referências, todos ficam indisponíveis. Frames extraídos deixam de ser declarados ausentes mesmo quando visão está indisponível. Resultados parciais e falhas de geração preservam essa informação.
- CI da aplicação entregue com PostgreSQL, tipos, Ruff, build e 14 cenários de navegador. Playwright agora inicia servidores em Windows/Linux e recusa reutilizar processos desconhecidos na CI.
- CI de containers entregue com credenciais efêmeras, subida completa, consumo de job por broker e repetição após reinício. Consultas de saúde direcionam explicitamente os workers de análise e geração. Naquela etapa ainda não havia sido executada no GitHub; execução posterior e limites constam em **Pendências externas**.
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

- **54 testes Python passaram** usando PostgreSQL real em banco isolado, incluindo quatro testes opcionais com Whisper/OCR/postura instalados. Incluem ranking, cursors, métricas nulas, regras, RLS entre workspaces, permissões, idempotência, cancelamento durante geração, referências inventadas, falha de provedor, mídia sintética, percentis, ausência de áudio, evidências visuais vazias e bootstrap do coletor. Sem selecionar adaptadores opcionais, a suíte principal executa 50 testes e ignora quatro.
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

- **TikTok — fonte ainda sem dados:** usado TikTokApi `7.3.5`, conforme o guia e a orientação do usuário. A primeira sondagem falhou em 66,59 s. O diagnóstico detectou um CDN do bootstrap indevidamente bloqueado; `ttwstatic.com` foi permitido mantendo HTTPS e DNS público, com regressão de bloqueio a loopback. Depois disso o trending respondeu sem itens, e perfil/hashtag/posts continuaram sem dados utilizáveis. Artefatos `.runtime/tiktok-live-probe.json`, `tiktok-network-probe.json` e `tiktok-routes-probe.json`. Não houve troca de contas, proxies ou contorno de CAPTCHA. Coleta contínua permanece desativada; é necessário disponibilizar uma sessão válida ou ambiente em que as rotas respondam para validar país/categoria e cobertura. Tokens ficam no `.env` local, nunca no chat ou Git.
- **Modelos — configurados para o piloto:** Tesseract portátil `5.4.0.20240606` com português/inglês, MediaPipe Pose Lite, Whisper tiny, Qwen3 `4b-instruct` e Qwen3-VL `4b-instruct`. OCR leu o título conhecido no timestamp esperado. Pose analisou oito quadros negativos e oito positivos com uma pessoa no exemplo do Google. A RX 6600 opera via Vulkan, sem mudança de drivers. A visão 4B descreveu corretamente os exemplos estáticos e a execução completa pela API terminou em 46,16 s. Foram rejeitados/removidos candidatos visuais menores; descrições vazias e mídia sem áudio receberam regressões. O lock multimodal tem hashes, usa somente um pacote OpenCV e passou na auditoria consultada. Qualidade editorial, fala real, consistência de idioma e movimento em vídeos representativos ainda não estão aprovados; ver os limites abaixo.
- **Docker/RabbitMQ — recuperação verificada:** a [execução 45695402744](https://github.com/profissionalkaua/fine-track/actions/runs/45695402744) passou em aplicação e containers, incluindo SIGKILL de worker/broker com mensagem pendente e conclusão após recuperar os processos. O primeiro teste de crash revelou perda de mensagem: `02fe4b7` adicionou confirmação de publicação antes de marcar a outbox enviada e entrega persistente. Também foram verificados migração, stack completo, HTTP/outbox/broker/worker, reinício e consumo posterior; corrigida falta de `libatomic1` no Playwright. A validação ocorreu no runner Linux sem instalar Docker/WSL no Windows. Não simula interrupção no meio da inferência nem aprova limites de memória dos modelos nos containers.
- **Aceitação longitudinal — observação iniciada:** `scripts/observe-pilot.py` está configurado por 168 horas, com amostras horárias de BR/PT nas três janelas e captura das métricas agregadas. Relatórios em `.runtime/pilot/`. Exclui fixtures: primeira observação registrou zero elegíveis reais e 28 sintéticos excluídos. Está em pré-verificação com fonte desativada, sem alegar aceitação. Precisa de máquina/processos ativos, acesso à fonte, histórico suficiente e sete dias efetivos; lacunas por suspensão/reinicialização não contam como verificações bem-sucedidas. A calibração humana continua pendente.
- **Referência visual — depende do artefato:** busca nos documentos conectados não encontrou o Pulso; navegador integrado retornou host indisponível e tentativa de leitura direta da Library falhou. É necessária uma exportação HTML ou capturas do frame original para verificar paridade.

Atualização dos modelos: o backend Vulkan do ZIP oficial reconheceu a RX 6600 com 8 GB de VRAM sem atualizar drivers; `/api/ps` confirmou modelos residentes na GPU. Após os candidatos anteriores reprovarem, o piloto selecionou explicitamente Qwen3 `4b-instruct` para texto e Qwen3-VL `4b-instruct` para visão, ambos Apache-2.0. A visão descreveu corretamente a pessoa/roupa/praia no exemplo público em 9,09 s e retornou zero pessoas no quadro azul. O contrato agora exige os campos anuláveis, restringe nomes de evidência, normaliza textos vazios, deixa resultados sem sinais úteis parciais e trata vídeo sem áudio sem derrubar a análise. `media-v2` invalida caches antigos. A execução completa pela API com mídia sintética completou em 46,16 s, com texto e visão reais e exportação. Artefatos: `.runtime/ollama/pilot-api-smoke.json`, `vision-positive-probe.json` e `full-media-4b-instruct-smoke.json`. O ensaio editorial de três casos gerou estruturas válidas, mas uma saída descumpriu restrição alimentar; portanto qualidade editorial não está aprovada. Cenas dinâmicas, fala real e consistência de idioma ainda dependem de amostras representativas. Os tempos citados não são p95.

Verificação local ampliada inclui Whisper/OCR/postura reais, contrato visual e ausência de áudio. Tipos Python e Ruff passaram; o cenário de troca de workspace passou em cinco repetições. As validações Linux de tipos, API, build e 14 cenários de navegador passaram na CI. Publicação foi precedida por varredura de 208 blobs históricos e revisão independente de arquivos sensíveis: nenhum bloqueador encontrado; `.env`, backups, pesos e mídia seguem ignorados. `main` preservada.

O ticket 08 fica `ready-for-human` para essas validações e configurações. As evidências locais não são apresentadas como aprovação de operação pública ou de qualidade editorial dos modelos.
