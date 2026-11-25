# Operação do piloto Pulso

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
