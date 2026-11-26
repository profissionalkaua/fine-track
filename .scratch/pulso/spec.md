# Pulso: especificação de implementação

Status: ready-for-agent

## Problem Statement

Criadores e equipes precisam descobrir conteúdo em crescimento, acompanhar referências e transformar evidências em ideias originais, distinguindo cobertura real, sinais observados e hipóteses.

## Solution

Entregar as quatro áreas do Pulso em fatias completas, com persistência, API, interface e testes. O guia original é `../../saas-inteligencia-viral-tiktok.md`; o desenho aprovado é `../../docs/superpowers/specs/2026-11-25-pulso-design.md`.

## User Stories

1. Como usuário, quero entrar com uma sessão segura para acessar meu workspace.
2. Como proprietário, quero provisionar usuários e papéis para controlar o acesso.
3. Como usuário, quero consultar o feed com BR como padrão.
4. Como usuário, quero escolher qualquer país ISO para mudar o recorte.
5. Como usuário, quero alternar janelas de 24 horas, sete dias e 30 dias.
6. Como usuário, quero manter meu país preferido entre visitas.
7. Como usuário, quero diferenciar coleta, cobertura parcial, ausência de resultados e fonte indisponível.
8. Como usuário, quero ver crescimento medido e métricas acumuladas com seus horários.
9. Como usuário, quero distinguir janela parcial e dados ausentes.
10. Como usuário, quero carregar páginas sem repetir vídeos.
11. Como usuário, quero filtrar hashtags dos itens carregados preservando o ranking.
12. Como usuário, quero abrir detalhes e o link original do vídeo.
13. Como usuário, quero salvar referências por handle ou URL.
14. Como usuário, quero confirmar a identidade de um perfil antes de acompanhá-lo.
15. Como usuário, quero consultar vídeos recentes e mais performáticos.
16. Como usuário, quero remover e desfazer a remoção de um criador.
17. Como usuário, quero definir uma categoria livre ou descobrir todos os nichos.
18. Como usuário, quero definir público, tom, formato e elementos de análise.
19. Como usuário, quero preservar rascunhos ao navegar.
20. Como usuário, quero salvar, limpar ou descartar alterações com efeitos distintos.
21. Como usuário, quero receber conflito se outra pessoa alterar a revisão que editei.
22. Como usuário, quero analisar referências do feed e dos criadores com evidências.
23. Como usuário, quero acompanhar, cancelar e retomar execuções.
24. Como usuário, quero preservar o recorte original depois de mudar meus filtros.
25. Como usuário, quero receber cinco conceitos com roteiros e referências existentes.
26. Como usuário, quero copiar e exportar os resultados.
27. Como usuário, quero produzir um roteiro a partir de um único card.
28. Como usuário, quero consultar análise visual com timestamps e confiança.
29. Como usuário, quero saber quando mídia, modelo ou evidência estiverem indisponíveis.
30. Como usuário de celular ou teclado, quero completar os mesmos fluxos com foco e controles acessíveis.
31. Como operador, quero jobs idempotentes, limites, métricas, retenção e restauração verificável.

## Implementation Decisions

Monólito modular com Next.js/TypeScript, FastAPI, PostgreSQL, Alembic, Celery/RabbitMQ, TikTok-Api isolado e Ollama local. Autenticação por sessão opaca e papéis owner/editor/viewer; isolamento por autorização e RLS. Rankings materializados, regras versionadas, entrada de runs congelada, outbox transacional e jobs com lease. Fonte real e mídia exigem configuração autorizada. Dados sintéticos são opt-in de desenvolvimento. Detalhes e critérios numéricos seguem o desenho aprovado.

## Testing Decisions

Fronteiras aprovadas: HTTP com PostgreSQL e execução controlada de jobs; navegador com API real; contratos públicos dos adaptadores com fixtures. Um teste vermelho, implementação mínima, teste verde por comportamento. Sem testes de detalhes internos. Não há testes anteriores. Tipos e testes focados durante cada entrega; suíte completa e revisão Standards/Spec ao final.

## Out of Scope

Pagamentos, publicação pública automática, promessa de ranking exaustivo, comprovação fictícia de cobertura ou qualidade dos modelos.

## Further Notes

Piloto real de sete dias, calibração geográfica/temática e licenças dos modelos dependem de ambiente e evidência externos. Reportar verificações não executadas.
