# Processar evidência de vídeos reais no orçamento dos modelos

Type: task
Status: resolved
Blocked by: 11

Origem: avaliação solicitada pelo usuário com vídeo público real do TikTok. O primeiro vídeo de 129 segundos produziu 455 registros de postura; o gerador recebeu 66.206 tokens para janela de 16.384 e falhou. Visão também excedeu sua janela.

## Acceptance criteria

- [x] Prompts de visão usam amostra temporal identificada de postura; resultados/exportação preservam todas as evidências.
- [x] Texto recebe os sinais visuais relevantes sem duplicar áudio e centenas de registros de postura.
- [x] Regressão na fronteira HTTP dos modelos e repetição da avaliação real.
- [x] Qualidade, cobertura geográfica e validação humana continuam reportadas separadamente de sucesso técnico.

## Comments

- Vídeo público do Manual do Mundo: https://www.tiktok.com/@manualdomundo/video/6985162794849127685.
- Origem/hash, mídia e resultados completos permanecem em `.runtime/`, fora do Git. Campo de país ausente; não conta como cobertura BR.
- 57 testes aprovados, quatro adaptadores opcionais não executados; mypy/Ruff aprovados. Duas regressões HTTP falharam antes da correção e passaram depois.
- Repetição do vídeo original: `completed`, 166,92 s, uma ideia, visão concluída, entrada textual reduzida de 66.206 para 2.456 tokens; 455 registros de postura e 21 trechos ASR preservados.
- Duas amostras adicionais reais também concluíram. Detalhes e limitações em `docs/real-tiktok-evaluation.md`.
- Standards: nenhuma violação ou smell acionável; observação sobre postura bruta ausente no editor considerada pelo eixo Spec.
- Spec: nenhum requisito exige enviar postura bruta ao editor; validação real confirmou o contexto reduzido. Sem achados pendentes neste delta.
- Qualidade não aprovada: erros de fala/OCR, afirmações estáticas indevidas e segmentação temporal incorreta. Sucesso técnico não encerra a calibração dos modelos.
