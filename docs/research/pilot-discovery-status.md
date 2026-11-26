# Descoberta e cobertura do piloto brasileiro

Verificação de 26 de novembro de 2026, entre 17h16 e 17h20 de Brasília. O recorte solicitado é Brasil, todos os nichos. Até esse levantamento, **nenhuma verificação horária integrou uma janela válida de aceitação**. A última sondagem de recomendações devolveu zero vídeos.

## Acesso à fonte e origem dos vídeos

| Superfície do TikTokApi 7.3.5 | Verificação com limite de um resultado | Evidência |
| --- | --- | --- |
| Recomendações | A sondagem isolada de 26/11 terminou em 18,58 s com zero itens. Usou o adaptador do Pulso, Chromium e uma sessão sem token configurado. A tentativa anterior após o ajuste do CDN também retornou zero. | [Adaptador](../../backend/pulso/adapters/tiktok.py), [API de recomendações do mantenedor](https://davidteather.github.io/TikTok-Api/api/trending.html) |
| Hashtag | Última sondagem registrada de `receitas` devolveu `unavailable` em 12,61 s. | [Registro da avaliação anterior](../implementation-verification.md), [API de hashtags](https://davidteather.github.io/TikTok-Api/api/hashtag.html) |
| Criador | Última sondagem registrada das publicações de `@tiktok` devolveu `unavailable` em 11,30 s. A consulta separada aos dados do perfil teve o mesmo estado em 12,05 s. | [Registro da avaliação anterior](../implementation-verification.md), [API de perfis](https://davidteather.github.io/TikTok-Api/api/user.html) |

A configuração efetiva mantinha a coleta desligada, sem token configurado. A habilitação usada para a sondagem durou apenas o processo. O banco registrava a fonte `tiktok` com `suspended=false`. Uma resposta vazia e um erro genérico têm causas possíveis distintas. Os registros disponíveis não identificam o motivo da indisponibilidade.

No banco da aplicação, uma consulta somente leitura encontrou três vídeos reais, todos vindos de `tiktok-public-page`, cada um com país nulo e uma única medição de contadores. Quatro manifestos disponíveis em disco, incluindo um ainda fora dessa contagem do banco, traziam `country=null` e evidência `unknown`. O banco continha também 28 vídeos sintéticos marcados BR. Os três vídeos reais carecem de país verificável e de um segundo ponto para calcular o crescimento. [Avaliação das páginas públicas](../real-tiktok-evaluation.md), [regras do feed](../../saas-inteligencia-viral-tiktok.md)

O adaptador lê o campo `region` da resposta e registra a fonte. Para validar a atribuição no piloto, o revisor precisa conferir o significado do campo nessa superfície ou documentar evidência pública explícita de origem. O campo `region_code` da Research API designa o país de registro da conta em outro produto. Idioma e hashtag isolados não estabelecem a origem exigida. [Adaptador](../../backend/pulso/adapters/tiktok.py), [definição de region_code pelo TikTok](https://developers.tiktok.com/docs/en/research-api-specs-query-videos), [requisitos de geografia](../../saas-inteligencia-viral-tiktok.md)

## Observador e latência

O arquivo local `.runtime/pilot/samples.jsonl` continha seis amostras de pré-verificação. Todos os horários abaixo são UTC. As janelas Dia, Semana e Mês consultaram a mesma base. [Implementação do observador](../../scripts/observe-pilot.py)

| Instantes | Resultado |
| --- | --- |
| 25/11 às 20h12 e 20h15, 26/11 às 00h37 | Três leituras de ranking, cada uma com zero elegíveis reais nos seis recortes de BR e PT. BR excluiu 28 entradas sintéticas em cada janela. |
| 25/11 às 21h15, 22h17 e 23h19 | Três `OperationalError` sem dados de ranking. A cobertura nesses instantes é desconhecida. |

Os três arquivos locais `.runtime/pilot/metrics-*.prom` não continham contagens do histograma de duração HTTP. A última amostra era de 26/11 às 00h37 UTC. Na inspeção do host havia conexão TCP com PostgreSQL (55432) e Ollama (11434). A API (8000), a interface (3000) e a porta AMQP padrão (5672) recusaram conexão. A consulta aos processos Python não encontrou o observador ativo. A série disponível não sustenta p95 do feed ou de runs de metadados. [Instrumentação do serviço](../../backend/pulso/monitoring.py), [operação do piloto](../operations.md)

## Condições para iniciar os sete dias

Às 17h28 de Brasília em 26/11, o observador foi reiniciado por 168 horas com os serviços locais ativos. A primeira amostra consultou PostgreSQL e métricas sem erro, manteve `preflight_source_disabled` e encontrou zero elegíveis reais em BR nas três janelas. O processo depende da máquina ligada. Essa observação documenta o estado atual e a janela de aceitação aguarda fonte e histórico válidos.

1. O responsável pelo acesso precisa indicar um ambiente ou sessão autorizados em que as três rotas devolvam exemplares reais. Se a sessão exigir um segredo, o operador o configura localmente. O teste de aceitação das rotas deve registrar quantidade, versão, procedência e evidência de país para cada superfície. Os requisitos do produto pedem confirmação dos usos previstos antes da coleta em produção. [Guia do produto](../../saas-inteligencia-viral-tiktok.md), [documentação do mantenedor](https://github.com/davidteather/TikTok-Api)
2. A equipe editorial precisa revisar a atribuição geográfica em uma amostra do recorte BR e a classificação quando houver categoria. O histórico de contadores deve permitir comparar medições dentro de cada janela. [Critérios de cobertura e ranking](../../saas-inteligencia-viral-tiktok.md)
3. Com fonte e histórico válidos, manter os serviços e uma instância do observador ativos. O comando `.venv\Scripts\python.exe scripts/observe-pilot.py --country BR --hours 168` acompanha todos os nichos na configuração atual. Registrar cada hora prevista, as falhas e lacunas. A meta é pelo menos 20 elegíveis em 95% das verificações por combinação validada, durante sete dias consecutivos. Reunir também latências de consultas reais com ranking pronto e dos runs de metadados, com contagem de observações junto ao p95. [Procedimento de observação](../operations.md), [metas de serviço](../../saas-inteligencia-viral-tiktok.md)
