# 09: Percentis, sinais e validação contínua

What to build: Completar os requisitos pendentes do MVP e preparar inferência local verificável.

Blocked by: None

Status: resolved

- [x] Percentil por vídeo com dez posts comparáveis do mesmo criador; mostrar amostra e método.
- [x] Disponibilidade real de sinais em resultados completos e parciais, incluindo exportação.
- [x] CI para tipos, API/PostgreSQL, build e desktop/celular; configuração compatível com Linux.
- [x] CI para subida do Compose, consumo via broker e verificação de workers após reinício.
- [x] Inferência textual local e transcrição offline com versões e pesos rastreáveis.
- [x] Verificação final e revisão independente Standards/Spec.

## Comments

Continuação autorizada pelo usuário em 25/11/2026. Fronteiras de teste mantidas: API HTTP, exportação, navegador e adaptadores externos. Base da revisão: `c4c4c0e`. A execução do job de containers ainda depende de publicar a branch e executar GitHub Actions; não foi apresentada como validação já realizada.

Evidências: 46 testes Python, 14 de navegador, tipos, Ruff e build passaram. Texto real gerou um roteiro e cinco ideias; mídia sintética autorizada percorreu API, worker, FFmpeg, transcrição, geração e exportação em 22,11 s. Revisores independentes apontaram dois ajustes, ambos corrigidos: contrato dos resultados parciais e verificação direcionada dos workers na CI. Consulte `docs/implementation-verification.md`. A aceitação externa do piloto permanece no ticket 08.
