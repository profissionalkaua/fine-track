# 10: Configurar e validar dependências externas

What to build: Executar o piloto técnico da infraestrutura e dos adaptadores, preservando evidências e limites reais.

Blocked by: None

Status: ready-for-human

- [x] Revisar histórico e arquivos sensíveis antes da publicação autorizada.
- [x] Publicar `feat/pulso` e executar CI de aplicação e containers.
- [x] Instalar OCR português e postura com dependências fixadas e testes reais dos adaptadores.
- [x] Avaliar candidatos de visão sem habilitar um modelo reprovado no orçamento.
- [x] Sondar TikTok-Api indicado no guia sem credenciais nem insistência após falha.
- [x] Iniciar observação horária por até 168 horas, excluindo fixtures da cobertura real.
- [x] Verificar recuperação da fila após encerramento forçado de broker e worker na CI ampliada.
- [x] Validar ambiente público de coleta e obter amostras reais para avaliação editorial/geográfica.
- [ ] Medir sete dias reais de cobertura/latência e concluir calibração humana.
- [ ] Inspecionar o frame original da Library ou sua exportação.

## Comments

- Em 26/11, o F2 isolado passou nas três rotas pelo Collector do Pulso e no perfil público. O ticket 14 registra integração e revisão. As amostras continuaram sem país verificável, e a aceitação BR segue pendente.

Continuidade: o usuário solicitou vídeos reais do TikTok. Três páginas/mídias públicas foram acessadas e processadas em workspaces de avaliação, com correção do excesso de contexto revelado pelo primeiro vídeo. Isso atende à obtenção de amostras reais, mas não valida sessão/rotas amplas nem geografia. Qualidade reprovada por erros de movimento, fala, OCR e edição. Consulte `docs/real-tiktok-evaluation.md` e ticket 12.

Usuário autorizou resolver as dependências e publicar as correções verificadas na branch pública após revisão de sensíveis. A `main` não foi alterada. A varredura dos 208 blobs históricos e revisão independente não encontraram credenciais reais rastreadas. A primeira CI revelou falta de libatomic no Dockerfile; corrigida em `cad09c0`, cuja CI passou nos dois jobs. `f064c9d` antecipa o commit transacional para antes da resposta HTTP.

O observador é diagnóstico; a primeira amostra registrou zero elegíveis reais, excluiu 28 exemplos sintéticos e marcou fonte desativada. Não iniciou uma aceitação aprovada nem substitui sete dias corridos com dados reais. Na avaliação inicial, OCR/postura passaram e a visão foi desativada após exceder o orçamento CPU; a atualização abaixo registra a escolha final com Vulkan. Consulte `docs/implementation-verification.md`.

Atualização: o teste SIGKILL revelou mensagem perdida antes da confirmação do broker. Corrigido em `02fe4b7` com confirmação de publicação e entrega persistente; [CI 45695402744](https://github.com/profissionalkaua/fine-track/actions/runs/45695402744) passou em ambos os jobs, incluindo recuperação da mensagem pendente e reinício. Vulkan foi habilitado a partir da distribuição já verificada, sem alterar drivers; a RX 6600 foi reconhecida. Após rejeitar candidatos menores, Qwen3-VL 4B Instruct passou nos exemplos estáticos positivo/negativo. A API com texto e visão 4B completou em 46,16 s usando mídia sintética autorizada. Qualidade editorial, vídeo real e calibração humana seguem pendentes; não há aprovação de produção.
