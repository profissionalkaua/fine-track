# Operação do piloto Pulso

## Ambiente F2 isolado

O coletor aceita `PULSO_F2_PYTHON_PATH`, apontando para o executável Python de um ambiente virtual com F2. A máquina do piloto foi preparada em `.runtime/probes/f2-venv`, a partir da revisão `f6be8c0ffba9a127075bbeafe4838716650b6325` do repositório `Johnserf-Seed/f2`. O campo de versão do pacote nessa revisão é `0.0.1.7`. A configuração local registra o caminho do interpretador.

Para preparar uma instalação nova no Windows, execute da raiz do projeto os comandos abaixo. O F2 é executado em processo separado. As dependências da API continuam sendo instaladas pelo arquivo de requisitos da aplicação.

```powershell
git clone https://github.com/Johnserf-Seed/f2.git .runtime/sources/f2
git -C .runtime/sources/f2 checkout f6be8c0ffba9a127075bbeafe4838716650b6325
.venv/Scripts/python.exe -m venv .runtime/probes/f2-venv
.runtime/probes/f2-venv/Scripts/python.exe -m pip install .runtime/sources/f2
```

Configure `PULSO_F2_PYTHON_PATH` com o caminho absoluto de `.runtime/probes/f2-venv/Scripts/python.exe`. Em Linux, use `bin/python` no ambiente correspondente. `PULSO_COLLECTION_ENABLED` continua sendo o controle explícito de coleta. `Settings.testing()` usa a configuração de teste isolada. Para avaliar a fonte manualmente, uma instância `Settings(collection_enabled=True)` habilita somente aquele processo.

O processo recebe fonte, referência e quantidade por stdin. Consulta apenas caminhos fixos em `www.tiktok.com`, verifica DNS público e fixa o endereço na conexão direta com TLS ativo. Redirecionamentos são recusados. Um callback limita a resposta a 8 MB durante a transferência. Cada requisição tem timeout de 20 s e o processo inteiro tem timeout de 90 s. Recomendações, hashtags e criadores retornam até 50 itens da primeira página. O coletor usa uma recomendação pública para inicializar a sessão antes das consultas de perfil ou hashtag.

HTTP 401/403 e exigência de login interrompem a coleta. HTTP 429 preserva a espera indicada por `Retry-After`, incluindo data HTTP. Uma falha de importação, timeout ou resposta inválida produz indisponibilidade pela interface existente. A procedência inclui `f2-public-web` e a versão F2. Parâmetros de região da requisição ficam fora da evidência geográfica. Os três vídeos da repetição chegaram sem país verificável.

A pesquisa, a revisão instalada e os resultados observados estão em [Coletores TikTok no GitHub](research/github-tiktok-collectors.md). Estabilidade, paginação, cobertura BR, classificação humana e sete dias seguem como critérios de aceitação do piloto.

## Modelos locais nesta máquina

Ollama portátil `0.40.18` está em `.runtime/ollama`, escutando somente em `127.0.0.1:11434`. Inicie novamente com `powershell -File scripts/ollama-local.ps1`. O launcher desativa a nuvem e limita a um modelo carregado e uma inferência simultânea. Não instala serviço nem altera drivers. ROCm não aceitou o driver AMD; o backend Vulkan da própria distribuição reconheceu a RX 6600 com 8 GB de VRAM. Medições iniciais usaram CPU; as avaliações finais dos modelos 4B usaram Vulkan na GPU.

A distribuição vem do [release oficial](https://github.com/ollama/ollama/releases/tag/v0.40.18). O ZIP Windows teve SHA256 conferido contra `sha256sum.txt`: `ca97292ac1e9acc77fcf473bb2741fa6acd12e3798f261b419680068b7cc4c16`. Foram extraídos executável, bibliotecas CPU/Vulkan e licenças. O cache do ZIP foi removido após extração para liberar espaço. Binários e pesos são ignorados pelo Git.

O `.env` local seleciona `qwen3:4b-instruct` para texto e `qwen3-vl:4b-instruct` para visão, ambos Apache-2.0, em avaliação do piloto. O `qwen2.5:1.5b` anterior continua instalado como alternativa leve. O adaptador real validou formatos e referências, mas o ensaio editorial revelou que respostas válidas ainda podem descumprir uma restrição alimentar do briefing. Isso não comprova qualidade editorial, resistência completa a prompt injection ou a meta de latência do piloto. Não altere `PULSO_CLASSIFIER_CALIBRATED=false` sem calibração humana.

Digest instalado: `65ec06548149b04c096a120e4a6da9d4017ea809c91734ea5631e89f96ddc57b`. O launcher não baixa nem atualiza o modelo ao iniciar; confira o digest de `/api/tags` antes de avaliar outra versão.

Para reproduzir a transcrição opcional, na raiz:

```powershell
.venv\Scripts\python.exe -m pip install --require-hashes -r backend/requirements-transcription.txt
.venv\Scripts\python.exe scripts/prepare-transcription.py
```

Defina `PULSO_WHISPER_MODEL_PATH` no `.env` com o caminho absoluto de `.runtime/models/faster-whisper-tiny` e reinicie API e workers. O script baixa somente arquivos de pesos/configuração do [Systran/faster-whisper-tiny](https://huggingface.co/Systran/faster-whisper-tiny), licença MIT, revisão `d90ca5fe260221311c53c58e660288d3deb8d356`, e grava manifesto com hashes. A inferência usa CPU/int8 e `local_files_only=True`. O lock fixa PyAV `18.1.0`: faster-whisper `1.2.1` ainda usa um argumento [removido no PyAV 19](https://github.com/SYSTRAN/faster-whisper/issues/1589).

Teste opcional dos pesos instalados:

```powershell
$env:PULSO_TEST_WHISPER_PATH = (Resolve-Path .runtime/models/faster-whisper-tiny).Path
.venv\Scripts\python.exe -m pytest -c backend/pyproject.toml backend/tests/test_media.py -q -k offline
```

O teste usa silêncio sintético; não mede precisão de transcrição de fala. O lock de transcrição é adicional ao backend; o Dockerfile padrão não o instala nem incorpora pesos.

### OCR e postura configurados localmente

`backend/requirements-media.txt` adiciona MediaPipe `0.10.35`, OpenCV Contrib `4.14.0.94` e dependências com hashes, preservando o lock da transcrição. Não instalar simultaneamente `opencv-python-headless`: as distribuições compartilham `cv2`.

O OCR foi extraído, sem executar o instalador, em `.runtime/tesseract`. Distribuição UB Mannheim indicada pela documentação Tesseract, SHA256 do instalador conferido contra winget: `c885fff6998e0608ba4bb8ab51436e1c6775c2bafc2559a19b423e18678b60c9`. Pesos portugueses `tessdata_fast/4.1.0/por.traineddata`, SHA256 `c4932b937207a9514b7514d518b931a99938c02a28a5a5a553f8599ed58b7deb`. O `.env` define `PULSO_OCR_EXECUTABLE` com o caminho absoluto do executável e `PULSO_OCR_LANGUAGES=por+eng`. Nenhum PATH global foi alterado.

Pose Lite: [bundle oficial Google, versão 1](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task), licença Apache-2.0, SHA256 `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a`. Arquivo local `.runtime/models/pose/pose_landmarker_lite.task`; `PULSO_POSE_MODEL_PATH` aponta para seu caminho absoluto. A carga por buffer evita perda de acentos em caminhos Windows. Resultado informa quantos quadros foram realmente decodificados.

Testes opcionais adicionais usam `PULSO_TEST_TESSERACT_PATH` e `PULSO_TEST_POSE_PATH` com esses caminhos absolutos. O OCR reconheceu um título conhecido e conservou timestamp. A postura processou oito quadros negativos sem pessoas e oito positivos com uma pessoa no [exemplo público do MediaPipe](https://storage.googleapis.com/mediapipe-assets/pose.jpg). Não são uma avaliação ampla de precisão. Binários, amostras, pesos e relatórios permanecem em `.runtime/`, fora do Git.

Os candidatos visuais Moondream/2B foram reprovados e removidos. A variante genérica Qwen3-VL `2b` apontava para um modelo de raciocínio que esgotava a saída sem JSON; o piloto selecionou explicitamente `qwen3-vl:4b-instruct`. Na GPU, o exemplo com uma pessoa na praia completou em 9,09 s e o quadro azul retornou zero pessoas, sem roupas inventadas. Isso valida somente exemplos estáticos. `PULSO_VISION_MAX_FRAMES=2` no `.env` limita amostragem uniforme incluindo extremos; `vision_frame_timestamps_ms` registra os quadros enviados. As descrições textuais são solicitadas em português; consistência de idioma e movimentos complexos ainda exigem avaliação. A inferência tem contexto/saída limitados e retorna parcial quando falha. Campos vazios não qualificam como evidência; nomes inventados são rejeitados e respostas sem sinais úteis permanecem parciais. Vídeo sem faixa de áudio preserva o restante da análise. O analisador `media-v2` invalida o cache do contrato anterior.

Digests instalados: texto `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`; visão `84f7ed8042fa7cdbd902f7dcb7d0370e032095047cc3244179f263b77b5bc318`. A análise individual completa via API/worker/FFmpeg/Whisper/OCR/postura/visão/geração/exportação completou em 46,16 s com vídeo sintético autorizado. Essa execução não estima p95.

### Observação longitudinal

`scripts/observe-pilot.py` lê rankings e métricas agregadas, sem gravar no banco nem solicitar novas coletas. Uma observação por hora, por até 168 horas, foi iniciada em processo oculto. PID e logs: `.runtime/pilot/observer.pid`, `observer.log`, `observer-error.log`; amostras em `samples.jsonl` e métricas em arquivos `.prom`. Para encerrar, identifique o processo do script antes de terminá-lo; o PID salvo pode referir-se ao launcher Windows.

Para reproduzir uma amostra: `.venv\Scripts\python.exe scripts/observe-pilot.py --once`. Para acompanhar sete dias: remova `--once`; BR/PT e três períodos são o padrão, e `--country BR --category culinária` permite escolher outro recorte. Use uma única instância por diretório de saída. A máquina e PostgreSQL/API precisam permanecer ativos. O script relê a configuração em cada ciclo e distingue pré-verificação com fonte desativada; ignora exemplos sintéticos para a cobertura real e nunca aprova aceitação automaticamente. A primeira amostra registrou zero elegíveis reais. Persistir esses diagnósticos não substitui fonte funcional, sete dias consecutivos, p95 calculado com amostra suficiente e revisão humana de país/categoria.

## Integração contínua

`.github/workflows/application.yml` verifica tipos Python/TypeScript, Ruff, testes com PostgreSQL real, build e navegador desktop/celular. Fixtures são sintéticas e coleta/modelos externos ficam desativados. O teste opcional de pesos não é exigido na CI principal.

Outro job sobe o Compose com credenciais efêmeras, cria um workspace isolado e verifica HTTP → outbox → RabbitMQ → análise. Repete o consumo após reiniciar broker e workers e consulta explicitamente análise e geração. Não testa geração por modelo nem queda durante uma inferência. Credenciais administrativas ficam no serviço de migração; o workspace de smoke não recebe dados reais. Nenhum segredo ou modelo é necessário no GitHub. O job usa um projeto Compose efêmero e remove apenas seus próprios volumes ao terminar.

Esta máquina não tem Docker nem WSL instalado. A [CI do commit 02fe4b7](https://github.com/profissionalkaua/fine-track/actions/runs/45695402744) passou em aplicação e containers no runner Linux, incluindo subida completa, reinício e recuperação de mensagem pendente durante SIGKILL de worker e broker. A primeira execução ampliada havia perdido a mensagem: a publicação agora aguarda confirmação de persistência do RabbitMQ antes de marcar a outbox enviada. Esse cenário não comprova retomada no meio de uma inferência.

## Processos e filas

API e frontend servem o produto; Celery executa filas `collection`, `classification`, `analysis`, `multimodal` e `generation`. Um único processo beat publica outbox a cada cinco segundos, avalia agendamentos a cada cinco minutos e aplica retenção diariamente. Execute uma instância do scheduler; workers podem crescer por fila. Jobs usam entrega tardia, lease e chave idempotente. Acesso público ao TikTok é serializado por advisory lock no PostgreSQL e reaproveita cache entre workspaces.

Perfis são reobservados em janelas de seis horas, hashtags em quatro horas e recomendações em duas horas. Coletores respeitam orçamento por fonte e limitações globais. A adição de um criador pode gerar uma coleta inicial fora do ciclo periódico. Perfis removidos são conferidos novamente antes de enfileirar consultas exclusivas.

Regras, referências, jobs privados, execuções, mídia autorizada e caches de análises têm contexto de workspace e políticas RLS. A outbox compartilhada contém somente IDs, fila e horários. Credenciais de migração não são usadas no processamento de jobs.

## Métricas e diagnóstico

- `pulso_http_requests_total` e `pulso_http_duration_seconds`: erros e p95 por rota estável, sem IDs ou query strings como rótulos.
- `pulso_eligible_videos`: distribuição de cobertura por país e período. A associação geográfica precisa ser validada no piloto.
- `/health`: processo HTTP disponível.
- `PULSO_TELEMETRY_ENABLED=true`: spans OTLP enviados ao endpoint configurado em `OTEL_EXPORTER_OTLP_ENDPOINT`.

Prometheus e Grafana estão no profile `monitoring`. Exemplo de consulta p95: `histogram_quantile(0.95, sum by (le,route) (rate(pulso_http_duration_seconds_bucket[5m])))`. Monitore idade dos rankings e estados de jobs no banco administrativo; não exponha tabelas privadas em dashboards públicos.

Os logs HTTP registram método, rota normalizada, status e duração. Não registram cookies, tokens, senhas, corpos de prompts ou payloads coletados.

Se a fonte bloquear o acesso, revise a condição antes de `python -m pulso.admin resume-source`. O sistema não fornece resolução de CAPTCHA, rotatividade de contas ou proxies para insistir após um bloqueio.

Se um worker cair, o RabbitMQ pode reenviar a mensagem. Uma execução com lease ativo não é processada simultaneamente. Em interrupção prolongada, aguarde a expiração do lease de 15 minutos antes de reenviar o envelope pelo operador. Uma retomada solicitada no produto cria outra execução e preserva o histórico.

## Retenção

- Snapshots e proveniência detalhada: 35 dias.
- Versões antigas de ranking: dois dias; cursors de feed expiram em 24 horas.
- Cache de coleta: expira por janela de fonte.
- Sessões expiradas e registros antigos de tentativas de login: removidos na rotina diária.
- Runs concluídos e análises: 90 dias por padrão, configuráveis em `PULSO_RETENTION_DAYS`.
- Temporários de mídia: removidos ao concluir, com limpeza de diretórios interrompidos após 24 horas.

Regras salvas e registros de autorização de mídia permanecem para manter a configuração do workspace. Pedidos de exclusão e revogação exigem revisão dos dados derivados e backups conforme a política aplicável; não há prazo de atendimento legal inferido nesta implementação.

## Backup e verificação de restauração

Use credenciais administrativas apenas no terminal de manutenção. Na pasta `backend`, com PostgreSQL local ativo:

```powershell
..\.venv\Scripts\python.exe -m pulso.backup create ../.runtime/backups/pulso.dump
..\.venv\Scripts\python.exe -m pulso.backup check ../.runtime/backups/pulso.dump pulso_restore_verificacao
```

O primeiro comando recusa sobrescrever um arquivo existente e grava manifesto. O segundo cria somente um banco novo cujo nome começa por `pulso_restore_`; recusa sobrescrever um banco existente. Valida a revisão Alembic e a leitura de tabelas após a restauração. Ferramentas `pg_dump`/`pg_restore` precisam ser compatíveis com o servidor e estar no PATH. O pacote mínimo embedded-postgres não inclui esses clientes. Nesta sessão, os clientes oficiais foram extraídos em `.runtime/postgresql-tools/pgsql/bin`, caminho alternativo reconhecido pelo comando.

Armazene backups protegidos e fora da máquina antes de atender um piloto real. A restauração de teste contém dados privados: restrinja seu acesso e gerencie sua retenção com os mesmos cuidados do banco de origem.

## Condições de liberação

Validar o Compose em ambiente com Docker; fixar digests; testar perda de broker/worker e recuperar backup fora da máquina; confirmar acesso autorizado à fonte e tratamento dos dados; medir cobertura, classificação, geração e latência reais. Instalação de modelos e licenças são decisões do ambiente. Dados sintéticos e testes de contrato não comprovam qualidade editorial, viabilidade comercial nem cobertura contínua.
