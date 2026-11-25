# 10: Configurar e validar dependências externas

What to build: Executar o piloto técnico da infraestrutura e dos adaptadores, preservando evidências e limites reais.

Blocked by: None

Status: claimed

- [x] Revisar histórico e arquivos sensíveis antes da publicação autorizada.
- [x] Publicar `feat/pulso` e executar CI de aplicação e containers.
- [x] Instalar OCR português e postura com dependências fixadas e testes reais dos adaptadores.
- [x] Avaliar candidatos de visão sem habilitar um modelo reprovado no orçamento.
- [x] Sondar TikTok-Api indicado no guia sem credenciais nem insistência após falha.
- [x] Iniciar observação horária por até 168 horas, excluindo fixtures da cobertura real.
- [ ] Verificar recuperação da fila após encerramento forçado de broker e worker na CI ampliada.
- [ ] Obter sessão válida da fonte e amostra autorizada para avaliação editorial/geográfica.
- [ ] Medir sete dias reais de cobertura/latência e concluir calibração humana.
- [ ] Inspecionar o frame original da Library ou sua exportação.

## Comments

Usuário autorizou resolver as dependências e publicar as correções verificadas na branch pública após revisão de sensíveis. A `main` não foi alterada. A varredura dos 208 blobs históricos e revisão independente não encontraram credenciais reais rastreadas. A primeira CI revelou falta de libatomic no Dockerfile; corrigida em `cad09c0`, cuja CI passou nos dois jobs. `f064c9d` antecipa o commit transacional para antes da resposta HTTP.

O observador é diagnóstico; a primeira amostra registrou zero elegíveis reais, excluiu 28 exemplos sintéticos e marcou fonte desativada. Não iniciou uma aceitação aprovada nem substitui sete dias corridos com dados reais. OCR e postura passaram; a visão com múltiplos quadros excedeu o orçamento CPU e permanece desativada. Consulte `docs/implementation-verification.md`.
