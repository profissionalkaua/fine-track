# Pulso

Aplicativo de inteligência de conteúdo para TikTok, com feed por crescimento observado, referências de criadores, regras de marca e análises com evidências. Implementação orientada pelas Matt Pocock Skills, com TDD nas fronteiras aprovadas.

## Executar no Windows

Pré-requisitos: Python 3.12 e Node 22. O projeto instala uma versão Node 22 compatível localmente para os subprocessos do Next.

Na raiz:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r backend/requirements.txt
npm.cmd ci
npm.cmd run db:local
```

O último comando mantém um PostgreSQL real em `127.0.0.1:55432`. Seus arquivos ficam em `.runtime/postgres`, ignorado pelo Git. A credencial `pulso-local-only` é exclusiva desse ambiente local, sem exposição à rede. O script usa caminhos curtos do Windows para suportar nomes de usuário com acentos.

Em outro terminal, na raiz:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pulso.admin migrate
..\.venv\Scripts\python.exe -m pulso.admin user --email voce@exemplo.com --workspace "Meu estúdio"
..\.venv\Scripts\python.exe -m uvicorn pulso.main:create_app --factory --host 127.0.0.1 --port 8000
```

A senha do proprietário é solicitada sem exibição. Em um terceiro terminal, na raiz:

```powershell
npm.cmd run dev
```

Abra **http://127.0.0.1:3000**. Para processar tarefas em desenvolvimento, mantenha outro terminal aberto em `backend`:

```powershell
..\.venv\Scripts\python.exe -m pulso.worker local
```

O executor local usa a mesma outbox, leases e etapas dos workers. Produção usa Celery/RabbitMQ.

## Demonstração e testes de navegador

Carga explícita de dados fictícios e conta local de demonstração:

```powershell
.\.venv\Scripts\python.exe scripts/prepare-e2e.py
```

Acesse com `demo@pulso.local` / `pulso-demo-local-2026`. Essa conta destina-se apenas à demonstração local. O comando é recusado fora do banco local de desenvolvimento. Os 28 vídeos são marcados como fictícios e não possuem links TikTok inventados.

O aplicativo inicia sem fixtures. Produção nunca recebe resultados fictícios automaticamente.

## Configuração das integrações

Copie `.env.example` para `.env` e configure somente os serviços necessários. A API sempre lê o arquivo na raiz do projeto, independentemente do diretório de execução.

- **Coleta:** `PULSO_COLLECTION_ENABLED=true` habilita o adaptador TikTok-Api. Configure `PULSO_MS_TOKEN` quando necessário para o acesso autorizado e instale o navegador com `.venv\Scripts\python.exe -m playwright install chromium`. O adaptador cobre recomendações, hashtags e perfis; não oferece filtro geográfico garantido. País incerto fica fora do feed estrito. Bloqueios suspendem a fonte; 429 e falhas transitórias geram espera e novas tentativas limitadas.
- **Geração:** configure `PULSO_OLLAMA_URL` e `PULSO_OLLAMA_MODEL` para um modelo já instalado no Ollama, com licença validada e suporte a JSON estruturado. Modelo ausente, resposta inválida ou referência inventada causam erro recuperável. Não há geração fictícia como fallback.
- **Visão:** configure `PULSO_VISION_MODEL` para um modelo multimodal local. Mídia autorizada é registrada pelo operador; a interface não aceita caminhos ou URLs arbitrários.
- **Transcrição e postura:** dependências opcionais em `backend/requirements-media.in`. Configure caminhos de pesos locais em `PULSO_WHISPER_MODEL_PATH` e `PULSO_POSE_MODEL_PATH`. O Whisper opera sem baixar pesos automaticamente. OCR requer Tesseract instalado no PATH.

O FFmpeg empacotado já extrai frames, timestamps e cortes. Sem os modelos opcionais, os campos dependentes permanecem indisponíveis e a análise informa o motivo.

O operador pode registrar mídia de sua titularidade ou com permissão documentada, dentro de `.runtime/media`:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pulso.admin attach-media --workspace-id ID --video-id ID_TIKTOK --file CAMINHO_LOCAL --rights-reference "Referência da autorização"
```

Classificação temática revisada no piloto:

```powershell
..\.venv\Scripts\python.exe -m pulso.admin review-category --video-id ID_TIKTOK --category "Culinária vegana"
```

Rótulos incertos não tornam um vídeo elegível para uma categoria estrita. A calibração automatizada por categoria depende do piloto com amostras humanas. Para retirar uma suspensão após revisão do acesso: `python -m pulso.admin resume-source`.

## Verificação

Com o PostgreSQL local ativo, na raiz:

```powershell
.\.venv\Scripts\python.exe -m pytest -c backend/pyproject.toml backend/tests
.\.venv\Scripts\python.exe -m mypy backend/pulso
.\.venv\Scripts\ruff.exe check backend
npm.cmd run typecheck
npm.cmd run build
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

Prepare os dados de demonstração antes do E2E. Os testes HTTP usam somente `pulso_test`, recriado entre cenários; o reset é recusado para qualquer outro banco. Os testes de navegador usam o banco local de desenvolvimento e criam referências e execuções nele. Executam desktop e celular com API real; provedores externos determinísticos existem somente nos testes Python.

## Docker Compose

Configure senhas próprias para `POSTGRES_PASSWORD`, `PULSO_APP_ROLE_PASSWORD` e `RABBITMQ_PASSWORD` em `.env`; use valores hexadecimais para evitar escapes em URLs. Para monitoramento, configure também `GRAFANA_PASSWORD`.

```powershell
docker compose up --build -d
docker compose run --rm migrate python -m pulso.admin user --email voce@exemplo.com --workspace "Meu estúdio"
docker compose --profile models --profile monitoring up -d
```

Compose usa PostgreSQL, RabbitMQ, API, frontend, coleta, análise e um único scheduler. O processo de migração tem credenciais próprias; a API e os workers recebem somente o papel de aplicação, sem bypass de RLS. Containers de aplicação executam sem root, sem capabilities e com privilégios limitados. A interface fica restrita a `127.0.0.1:3000`.

As imagens de infraestrutura usam tags de piloto. Antes de uma liberação pública, valide e fixe seus digests e a revisão dos modelos. O Docker Compose não foi executado nesta máquina porque não há runtime Docker disponível.

## Operação

Veja [o runbook](docs/operations.md) para métricas, agendamento, retenção, backup e restauração. A API publica `/health` e métricas Prometheus em `/metrics`, sem rótulos com nomes de usuários, workspaces ou categorias privadas.

Implementação e critérios: [desenho aprovado](docs/superpowers/specs/2026-11-25-pulso-design.md), [plano](docs/superpowers/plans/2026-11-25-pulso.md) e [tickets](.scratch/pulso/issues/).

O piloto real ainda deve validar permissão de coleta, disponibilidade das fontes, sinais geográficos, calibração temática, modelos em português e metas de cobertura/latência por sete dias. A referência visual da Library não pôde ser acessada nesta sessão; a interface segue os requisitos textuais, sem declaração de paridade pixel a pixel.
