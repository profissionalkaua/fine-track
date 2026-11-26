# Reutilizar análises individuais disponíveis

Type: task
Status: resolved
Blocked by: None

Origem: guia do produto, seção 7.1; continuidade do ticket 06.

Ao abrir um vídeo, recuperar a execução disponível no workspace, inclusive em andamento e além das vinte entradas recentes. Reutilizar somente entradas compatíveis com as regras, referência e configuração de análise atuais. Resultados com falha permitem nova tentativa explícita. Respostas atrasadas não podem substituir o vídeo aberto.

## Acceptance criteria

- [x] Consulta dedicada sem criar trabalho, isolada por workspace e sem limite do histórico recente.
- [x] Reutilização de execução ativa ou concluída compatível; alterações relevantes invalidam a reutilização.
- [x] Modal acompanha a execução recuperada e protege alterações de contexto.
- [x] Verificação pela API pública e navegador; revisão Standards/Spec.

## Comments

- Recorte do piloto confirmado: Brasil, todos os nichos. Não restringe filtros do produto.
- API: recuperação além das vinte entradas recentes, execução concluída, mudança de regras/modelo/orçamento/referência/mídia, viewer, isolamento e duas aberturas concorrentes. 55 testes aprovados; quatro adaptadores opcionais não executados nesta rodada.
- Navegador: 16 cenários aprovados em desktop/celular. Tipos, Ruff e build de produção aprovados.
- Standards: validação dos parâmetros corrigida (422, evitando 500); assinatura de mídia centralizada. Revisor confirmou resolução, sem novos achados.
- Spec: orçamento de mídia incluído na invalidação após reprodução pela API. Revisor confirmou resolução, sem novos achados.
- Execuções antigas sem assinatura permanecem no histórico/exportação; a primeira abertura após esta atualização gera uma execução compatível.
