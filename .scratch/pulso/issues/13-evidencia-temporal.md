# Evidência temporal e qualidade do piloto

Blocked by: 12
Status: resolved

Vincular descrições a quadros datados, medir variação de imagem, filtrar OCR de baixa confiança e reavaliar fala nos vídeos reais. A exportação e o modal devem identificar a base de cada observação. Verificar o vídeo fornecido pelo usuário e registrar limites no relatório.

## Verificação

- [x] Timestamps extraídos do FFmpeg e descrições restritas ao quadro fornecido.
- [x] Variação de luminância e mudanças estimadas de postura preservadas na exportação e exibidas independentemente da visão.
- [x] OCR por confiança e ASR small comparado com tiny em três vídeos reais.
- [x] Repetição pela API do vídeo escolhido pelo usuário e da microscopia com quatro quadros e media-v4.1.
- [x] Limites qualitativos e pendências externas registrados em docs/real-tiktok-evaluation.md.

## Comments

65 testes de backend passaram com os quatro testes opcionais habilitados. Ruff, mypy, TypeScript e build passaram. Os 16 testes de navegador existentes e a nova regressão em desktop/mobile passaram. A regressão do modal falhou com a condição anterior e passou com a correção.

Standards sem achados acionáveis. Spec identificou a ocultação de medições quando a visão falhava, corrigida e verificada. Aprovação qualitativa, acesso à descoberta, geografia, referência Library e sete dias continuam pendentes conforme relatórios.
