# Reutilização da análise individual

Continuidade do guia, seção 7.1, e do ticket local 11. Piloto: Brasil, todos os nichos.

O modal consulta `GET /v1/runs/available` para recuperar uma execução do workspace sem depender das vinte entradas recentes. Recupera trabalho ativo, resultado concluído ou estado terminal com opção de nova tentativa. Aberturas sem resultado usam `POST /v1/runs/video/open`, que serializa a seleção/criação por workspace e assinatura; duas aberturas simultâneas compartilham a execução. A tentativa manual usa a criação explícita existente.

A compatibilidade inclui referência, regras, mídia autorizada, provedor/modelos e configuração de processamento, inclusive limites de duração/tamanho. A assinatura de mídia é compartilhada com o cache visual. Somente hashes são persistidos para a configuração local. Alterar o conteúdo de pesos mantendo a mesma identificação/caminho exige versionar o modelo/configuração; não há leitura de todos os pesos a cada abertura.

Consultas são permitidas a viewers; criação continua exigindo editor. O modal cancela requisições e descarta respostas de contextos encerrados. Execuções anteriores à assinatura continuam disponíveis pelo histórico/exportação; não são reutilizadas automaticamente.

## Verificação

- API com PostgreSQL real: **55 aprovados, quatro adaptadores opcionais não executados**. Inclui histórico além de vinte entradas, recuperação ativa/concluída, mudanças de regras/modelo/orçamento/referência/mídia, consultas de viewer, isolamento e concorrência de duas aberturas.
- Navegador: **16 cenários aprovados**, desktop/celular, incluindo reabertura sem criar trabalho.
- TypeScript, mypy, Ruff e build de produção aprovados.
- A ausência de mídia permanece coberta na API. O teste de abas/foco do navegador aceita mídia autorizada já registrada no piloto.

## Standards

Revisão independente desde `93cda94` identificou entrada inválida causando exceção interna e duplicação da seleção de configuração. Restrições na fronteira HTTP retornam 422; assinatura compartilhada em `MediaAnalyzer.cache_key` elimina a duplicação. Revisão posterior: nenhum achado pendente.

## Spec

Revisão independente identificou invalidação incompleta ao mudar o orçamento de mídia. Teste reproduziu a reutilização indevida; os limites agora participam da assinatura compartilhada. Revisão posterior: nenhum achado pendente ou ampliação de escopo.

Essas verificações não alteram as pendências de coleta real, qualidade editorial/fala e aceitação longitudinal registradas em `implementation-verification.md`.
