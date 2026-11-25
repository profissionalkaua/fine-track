# Pulso: desenho de implementação

Status: proposta para aprovação. Nenhum código de produto foi implementado.

Revisão de viabilidade de planejamento: revisor independente não identificou lacunas importantes pendentes. A aprovação do usuário continua pendente, inclusive das fronteiras de teste e da divisão em tickets.

## Intenção e requisitos

Construir um SaaS para criadores, equipes de marketing e agências descobrirem vídeos em crescimento, acompanharem referências e produzirem ideias originais com evidências rastreáveis. O guia de requisitos é `../../../saas-inteligencia-viral-tiktok.md`, versão 1.3. Este desenho organiza sua implementação; a aprovação do desenho não valida os fatos da pesquisa histórica contida no guia.

O usuário escolheu entregas completas por funcionalidade, com persistência, API, interface e testes em cada entrega. Também aprovou tickets locais em `.scratch/pulso/`, rótulos padrão e instruções em `AGENTS.md`.

## Abordagens

1. **Entregas completas por funcionalidade, escolhida pelo usuário:** um monólito modular, com cada comportamento disponível de ponta a ponta antes do seguinte. Detecta problemas de contrato, persistência e execução cedo. Exige infraestrutura local desde a primeira entrega.
2. **Protótipo de interface primeiro, alternativa considerada:** facilita validar as telas rapidamente, mas adia integração, isolamento e funcionamento dos workers. O usuário escolheu a primeira abordagem.

## Resultado esperado

- Quatro áreas em português: Vídeos em alta, Criadores, Regras da marca e Gerar ideias.
- País inicial BR, todos os países ISO 3166-1 alfa-2 disponíveis, preferências persistidas, instantes em UTC e apresentação em America/Sao_Paulo.
- Resultados reais somente quando houver observações elegíveis; cobertura parcial, coleta, ausência de dados e indisponibilidade são estados distintos.
- Rankings por crescimento reproduzíveis, regras versionadas, execuções assíncronas e resultados com referências verificáveis.
- Ambiente local reproduzível, migrações, testes e instruções de operação. A comprovação da disponibilidade contínua da fonte e do desempenho por sete dias exige um piloto posterior com acesso autorizado.

## Arquitetura proposta pelo implementador

Adotar a stack sugerida pelo guia: Next.js com TypeScript e Tailwind no frontend; FastAPI, Pydantic, SQLAlchemy e Alembic no backend; PostgreSQL; Celery com RabbitMQ; adaptador TikTok-Api com Playwright; geração estruturada e visão por Ollama; processamento de mídia com FFmpeg, Whisper, OCR e MediaPipe. As versões e APIs externas serão verificadas na implementação antes de fixar dependências. Não presumir a validade dos números de versão citados no guia.

Separar os módulos por responsabilidade de produto: identidade e workspaces; observações e ranking; criadores; regras; execuções; evidências e geração. O navegador consome apenas a API de produto. Coletor, modelos e processamento de mídia ficam atrás de adaptadores substituíveis.

Docker Compose proverá os serviços do piloto. O frontend e a API também terão comandos de desenvolvimento. Esta máquina tem Node, Python e Git disponíveis; Docker não foi localizado no PATH. A configuração Compose será entregue, mas sua execução será reportada como pendente se o runtime continuar ausente.

## Identidade, autorização e persistência

Proposta do implementador para a lacuna de autenticação do guia: acesso inicial por email e senha, criação do proprietário por comando administrativo local e cadastro público desativado. Hash de senha com biblioteca própria para esse fim; sessões opacas revogáveis no servidor, cookie HttpOnly, SameSite e Secure em produção, e proteção de operações mutáveis contra CSRF. Provisionar usuários e associações inicialmente por comando administrativo, sem depender de serviço externo de email.

Cada sessão seleciona um workspace autorizado; a API verifica associação e papel owner/editor/viewer. Viewer pode consultar e exportar seus resultados; editor e owner podem alterar referências, regras e iniciar/cancelar execuções. Somente owner administra associações. O identificador enviado pelo navegador nunca constitui autorização.

PostgreSQL é o armazenamento durável de produção e integração. IDs TikTok são strings nos contratos; métricas são inteiros anuláveis. Tabelas privadas possuem RLS e o papel da aplicação não pode contorná-la. O contexto de workspace é aplicado por transação, inclusive nos workers. Migrações são executadas por papel distinto.

Observações públicas reutilizáveis ficam separadas de regras, referências salvas e resultados privados. Transações incluem a outbox; leases, chaves únicas e upserts garantem reexecução idempotente. Testes de integração do banco devem rodar em PostgreSQL para verificar RLS e concorrência.

## Feed e ranking

Aplicar país, janela móvel e categoria salva antes de ordenar. Um país precisa de evidência explícita de associação, observada ou inferida; idioma, hashtag ampla ou configuração da consulta não bastam. Categoria exige revisão ou confiança mínima inicial de 0,80. País e categoria incertos não entram no recorte estrito.

Calcular velocidade por delta de views e horas entre medições válidas. Exigir cobertura mínima de 75% da janela para vídeos anteriores à janela; vídeos novos precisam de observação mínima de duas horas no Dia e 12 horas na Semana/Mês, com selo de janela parcial. Proposta para concretizar a meta de atualização: última observação com até duas horas de idade; tornar o limite configurável e exibir desatualização quando excedido. Quedas de contadores colocam o par em quarentena. Desempatar por delta, observação mais recente e ID; não preencher ranking por crescimento com views acumuladas.

Persistir versões de ranking publicadas atomicamente. Cada cursor referencia versão, recorte e posição; cursor inválido/expirado gera erro recuperável. Entregar até 20 por página e manter os itens anteriores no frontend. Hashtags derivam de todas as páginas já carregadas e refinam localmente sem coleta, preservando a posição original. Separar quantidade filtrada de cobertura elegível. Exibir métricas globais do vídeo, publicação, observação e limites da janela.

País e período ficam na URL; preferência de país é persistida. Limpar filtros restaura BR/Dia/todas as hashtags e preserva a categoria salva. Modificar a consulta invalida páginas anteriores e mantém uma hashtag somente se existir na nova base.

## Coleta e fontes

Implementar um único contrato de adaptação para recomendações, hashtags e perfis. Normalizar dados e proveniência, guardar versão da fonte e erros e deduplicar por identidade TikTok. Respeitar backoff, Retry-After e suspensão por bloqueio; agendamento com um único scheduler, orçamento e limites por host.

Proposta do implementador: coleta externa desativada por padrão até configurar o acesso autorizado descrito no guia. Isso não bloqueia implementar e testar o produto: fixtures sintéticas exercitam o mesmo caminho de normalização, persistência e publicação em um ambiente de desenvolvimento explicitamente identificado. O comando de carga dessas fixtures será opt-in e impedido em produção. O feed vazio de produção não recebe resultados inventados.

Credenciais e cookies ficam fora do banco de observações, do navegador e dos logs. URLs e redirecionamentos são validados, e o worker tem egress restrito contra destinos internos. Não efetuar coleta de produção nem declarar viabilidade comercial comprovada nesta etapa.

## Criadores e regras

Adicionar por handle ou URL validada, resolver ID canônico, apresentar pendência ou prévia e confirmar vínculo idempotente no workspace. Remover desativa o vínculo; Desfazer restaura o mesmo criador. Históricos permanecem associados aos runs. Abas mostram recentes ou crescimento com janela explícita; views acumuladas têm ordenação distinta.

Regras são opcionais e versionadas por PATCH com revisão esperada; conflito retorna 409. Categoria aceita texto livre, preserva grafia para exibição e usa chave normalizada para descoberta. Vazio ou null remove categoria. O frontend mantém o rascunho entre áreas, distingue salvar/limpar/descartar e informa alterações pendentes. A categoria salva redefine o recorte do feed e dos próximos runs.

## Execuções, ideias e evidências

Criar runs por POST com Idempotency-Key e resposta 202. Mesma chave e mesma entrada retornam a execução original; mesma chave com conteúdo diferente retorna conflito. Congelar país, período, categoria, hashtag, regras, ranking e referências de entrada. No feed, combinar até 20 referências carregadas com até cinco posts por criador, limitados a 30 de concorrentes, deduplicando e preservando ambas as origens. Posts fora da categoria ficam somente no agrupamento do criador, com aviso, e não contam para o resumo temático.

Para análise geral, menos de cinco referências elegíveis produz saída partial com motivo de amostra insuficiente e opção de retomar; a análise individual dispensa esse mínimo. Proposta de contrato adicional: POST /v1/runs/{id}/resume cria uma nova execução ligada à anterior, congelando novamente a entrada escolhida sem alterar o histórico original. Repetição idempotente não duplica essa retomada.

Fluxo: queued, collecting, analyzing, generating e completed, com saídas partial, failed e cancelled. Progresso é persistido por etapa e contagem, consultado por polling. Cancelar bloqueia agendamento de novas etapas; etapas já em andamento verificam cancelamento antes de publicar. Resultados parciais válidos permanecem disponíveis. Retries não duplicam ideias.

Ollama recebe dados normalizados tratados como dados, sem ferramentas de rede ou segredos, e devolve JSON validado. Entregar cinco conceitos por rodada geral e uma proposta por análise individual. Cada conceito inclui premissa, justificativa, referências, intenção criativa, gancho, blocos de roteiro, texto na tela, CTA e duração estimada. Validar IDs contra o corpus e similaridade com transcrições disponíveis. Separar evidências observadas, hipóteses editoriais e sugestões; retenção real permanece indisponível sem analytics autorizados.

O modelo local será configurável por nome e versão; selecionar e documentar um padrão somente após validar licença, português e custo no hardware disponível. Modelo ausente ou saída inválida é estado recuperável, sem substituir silenciosamente por texto apresentado como geração real. Usar um adaptador determinístico exclusivamente nos testes automatizados.

## Mídia e análise visual

Processar somente mídia cujo acesso e uso estejam autorizados, com limites de tamanho, duração e recursos. Extrair frames com timestamps, cortes, transcrição e OCR; usar pose para sequências corporais e modelo multimodal para cena. Persistir intervalos em milissegundos, identidade da mídia, versão do analisador, observações, inferências, confiança e motivos de ausência. Preservar os timestamps originais em recortes.

Nome de dança precisa de evidência adicional e pode ser declarado na legenda ou não identificado. Pessoas são descritas por presença/contagem visível, sem identificação. Sem mídia ou modelo, deixar campos dependentes indisponíveis. Metadados suficientes ainda permitem uma hipótese editorial explicitamente identificada. Cache respeita versão de mídia, modelo e escopo autorizado; temporários são removidos ao finalizar e em até 24 horas após interrupção.

## Interface e acessibilidade

Reproduzir os controles e comportamentos das seções 1.1, 1.2 e 11.1 do guia: superfícies claras, navegação e faixa de ranking escuras, destaque violeta, navegação lateral em desktop e empilhamento em celular. Filtros com rótulos, foco visível, estado ativo perceptível, feedback acessível e movimento reduzido.

Modais de detalhes e ideias têm fundo opaco claro, texto escuro, Escape, foco contido e retorno ao acionador. A janela individual identifica vídeo/criador uma vez, oferece Roteiro e Análise visual, cópia e JSON; o link por ideia de referência fica na análise geral. Navegação interna e voltar do navegador preservam rascunhos.

O frame da Library é uma referência externa mencionada no guia, ainda não inspecionada. Tentar acessá-lo na implementação da interface. Caso não esteja disponível nesta sessão, aplicar os requisitos textuais e declarar a paridade visual exata pendente, sem alegar reprodução verificada do frame.

## Fronteiras de teste propostas para aprovação

1. **API HTTP de produto com PostgreSQL e executor de jobs controlado:** principal fronteira; cobre autorização/RLS, filtros, ranking, paginação, regras, concorrência, idempotência, progresso, cancelamento e exportação. Relógio e provedores externos controlados permitem resultados verificáveis. Não comprova disponibilidade real do TikTok nem qualidade do modelo instalado.
2. **Navegador com frontend e API reais:** fluxos críticos em desktop e celular; cobre hashtags sem nova consulta, rascunhos, histórico de navegação, remover/desfazer, congelamento do recorte, modais, teclado, copiar/exportar e estados de falha. Não substitui calibração humana de inferências.
3. **Contrato público dos adaptadores de coleta, geração e mídia:** fixtures independentes e mídia sintética autorizada cobrem normalização, esquema, proveniência, ausência de campos, bloqueio, evidências e timestamps. Testes vivos são opt-in no piloto e não fazem parte da suíte padrão.

Não há testes anteriores no projeto. Seguir TDD de Matt Pocock: um comportamento por ciclo vermelho-verde, somente nessas fronteiras após aprovação. Executar verificações de tipos e testes focados durante cada entrega; suíte completa, build e revisão Standards/Spec ao final. Fixtures de entrada e resultados esperados vêm de exemplos calculados independentemente, sem testar detalhes internos.

## Proposta de tickets e dependências

Estes são rascunhos para aprovação de granularidade; os tickets individuais serão publicados no tracker após aprovação.

| Nº | Entrega verificável de ponta a ponta | Bloqueada por |
| --- | --- | --- |
| 01 | Acessar o workspace e consultar o feed persistido, com filtros, ranking e estados honestos de cobertura; fixture de desenvolvimento opt-in para demonstração local. | Nenhuma |
| 02 | Descobrir e atualizar vídeos pelo adaptador real das três fontes; acompanhar no feed os estados de coleta e indisponibilidade, com outbox, filas e snapshots. | 01 |
| 03 | Adicionar, confirmar, consultar, remover e restaurar criadores, com vídeos recentes e mais performáticos. | 02 |
| 04 | Editar e salvar regras versionadas, preservar rascunho e observar categoria livre/remoção de categoria alterando feed e descoberta. | 02 |
| 05 | Iniciar, acompanhar, cancelar e retomar análise geral com entrada congelada, corpus deduplicado e evidências; gerar, copiar e exportar cinco ideias via modelo local. | 03, 04 |
| 06 | Abrir roteiro individual no card, acompanhar processamento, copiar e exportar; análise visual indisponível com motivo quando não há mídia. | 05 |
| 07 | Processar mídia autorizada e apresentar análise visual/transcrição/OCR/pose com timestamps, confiança e exportação, reutilizando resultados válidos. | 06 |
| 08 | Operar o piloto com limites, telemetria, retenção, restauração de backup e recuperação de falhas; concluir testes entre workspaces, SSRF, prompt injection e paridade de navegação desktop/celular. | 07 |

Cada ticket conterá critérios verificáveis, fronteiras de teste aplicáveis e evidência de conclusão. Ticket 01 inclui identidade e infraestrutura mínimas para ser demonstrável isoladamente; cada integração posterior estende uma ação do usuário e é validada no mesmo fluxo de produto. A aprovação autoriza implementação sequencial; paralelismo fica reservado à revisão prevista pelas skills.

## Operação, limites e liberação

Snapshots detalhados: 35 dias. Perfis: atualização inicial a cada seis horas; hashtags: quatro horas; candidatos de interesse: duas horas, sujeitos a orçamento e backoff. Exportar métricas de cobertura, latência, fila, erros, idade de ranking e duração por etapa; incluir logs estruturados sem segredos e configuração de OpenTelemetry, Prometheus e Grafana no piloto.

Entregar scripts e documentação de backup/restauração e verificar restauração em banco isolado quando houver runtime. Metas de p95 de 700 ms para ranking pronto, três minutos para run de metadados e 20 itens em 95% das verificações por sete dias são objetivos medidos no piloto, não promessas verificáveis com fixtures.

Cobrança, pagamentos, planos comerciais e analytics privados do TikTok não estão definidos no guia e ficam fora deste MVP. Implantação pública, ativação de coleta de produção e aquisição de infraestrutura exigem as configurações e condições reais do ambiente; a implementação local e seus testes seguem independentemente.

## Decisões deixadas ao implementador

Escolher organização interna dos módulos, bibliotecas de componentes acessíveis, versões verificadas das dependências, formatos de erros, limites configuráveis de recursos e exemplos sintéticos. Registrar decisões duráveis como ADRs quando implementadas. Manter os contratos descritos ou documentar extensões compatíveis. Informar testes não executados por ausência de runtime ou integração, sem tratá-los como aprovados.
