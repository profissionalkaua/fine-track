# Processar evidência de vídeos reais no orçamento dos modelos

Type: task
Status: claimed
Blocked by: 11

Origem: avaliação solicitada pelo usuário com vídeo público real do TikTok. O primeiro vídeo de 129 segundos produziu 455 registros de postura; o gerador recebeu 66.206 tokens para janela de 16.384 e falhou. Visão também excedeu sua janela.

## Acceptance criteria

- [ ] Prompts de visão usam amostra temporal identificada de postura; resultados/exportação preservam todas as evidências.
- [ ] Texto recebe os sinais visuais relevantes sem duplicar áudio e centenas de registros de postura.
- [ ] Regressão na fronteira HTTP dos modelos e repetição da avaliação real.
- [ ] Qualidade, cobertura geográfica e validação humana continuam reportadas separadamente de sucesso técnico.

## Comments

- Vídeo público do Manual do Mundo: https://www.tiktok.com/@manualdomundo/video/6985162794849127685.
- Origem/hash, mídia e resultados completos permanecem em `.runtime/`, fora do Git. Campo de país ausente; não conta como cobertura BR.
