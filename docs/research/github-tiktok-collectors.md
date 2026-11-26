# Coletores TikTok no GitHub para o Pulso

Verificação em 26/11/2026. Uma sondagem isolada com assinatura do F2 e transporte `curl_cffi` devolveu um vídeo em cada uma das três superfícies do TikTok exigidas pelo Pulso. O resultado identifica um caminho funcional local para integração. Cobertura brasileira, paginação e estabilidade prolongada ainda precisam de validação.

## Adoção e manutenção

Estrelas e `pushed_at` são uma fotografia da API pública do GitHub. `pushed_at` indica atividade no repositório, podendo incluir branches diferentes da principal. Não comprova correção recente do coletor. Nenhum dos sete estava arquivado.

| Repositório | Estrelas | Último push UTC | Licença |
| --- | ---: | --- | --- |
| [davidteather/TikTok-Api](https://api.github.com/repos/davidteather/TikTok-Api) | 6.772 | 14/11/2026 | MIT |
| [Evil0ctal/Douyin_TikTok_Download_API](https://api.github.com/repos/Evil0ctal/Douyin_TikTok_Download_API) | 21.585 | 20/11/2026 | Apache-2.0 |
| [Russell-Newton/TikTokPy](https://api.github.com/repos/Russell-Newton/TikTokPy) | 238 | 04/07/2024 | MIT |
| [drawrowfly/tiktok-scraper](https://api.github.com/repos/drawrowfly/tiktok-scraper) | 5.270 | 19/05/2023 | API não identifica. [package.json declara MIT](https://github.com/drawrowfly/tiktok-scraper/blob/master/package.json) |
| [yt-dlp/yt-dlp](https://api.github.com/repos/yt-dlp/yt-dlp) | 210.916 | 24/11/2026 | Unlicense |
| [Johnserf-Seed/f2](https://api.github.com/repos/Johnserf-Seed/f2) | 2.756 | 19/10/2026 | Apache-2.0 |
| [JoeanAmier/TikTokDownloader](https://api.github.com/repos/JoeanAmier/TikTokDownloader) | 17.723 | 04/11/2026 | GPL-3.0 |

## Cobertura real do código

| Candidato | Recomendações TikTok | Hashtag TikTok | Criador TikTok | Sessão e avaliação |
| --- | --- | --- | --- | --- |
| TikTok-Api | Sim, `trending.videos` | Sim | Sim | Já instalado no Pulso. O [README](https://github.com/davidteather/TikTok-Api) aceita `ms_token=None` no exemplo, com Chromium e espera de 3 s. A sondagem local descrita abaixo falhou. |
| Evil0ctal v5 | **Não**: `/trending` é Douyin/Bilibili | Sim | Sim | API auto-hospedada com pool de identidades, armazenamento e console. Boa alternativa parcial, sem equivalência às três rotas. [Referência REST](https://github.com/Evil0ctal/Douyin_TikTok_Download_API/blob/main/documents/en/11-api.md). |
| TikTokPy | Não há método na API examinada | Sim, `challenge` | Sim, `user` | O projeto anuncia operação sem login/chave. Chromium lê páginas e a implementação espera `SIGI_STATE`. Atividade principal antiga reduz prioridade. [API](https://github.com/Russell-Newton/TikTokPy/blob/main/src/tiktokapipy/api.py), [implementação assíncrona](https://github.com/Russell-Newton/TikTokPy/blob/main/src/tiktokapipy/async_api.py). |
| tiktok-scraper | Declarado | Declarado | Declarado | README trata sessão como opcional e sugere sessão autenticada quando há bloqueio de IP. Dependências e manutenção antigas: baixa prioridade para uma nova integração. [README](https://github.com/drawrowfly/tiktok-scraper), [histórico principal](https://github.com/drawrowfly/tiktok-scraper/commits/master/). |
| yt-dlp | Não há extrator de recomendações no módulo | `TikTokTagIE` marcado `_WORKING=False` | Há `TikTokUserIE` | Útil para mídia/URLs conhecidas. Popularidade geral não demonstra descoberta TikTok completa. [Módulo TikTok](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/tiktok.py). |
| F2 | `HOME_RECOMMEND`, validado localmente | Catálogo próprio sem método. Assinador genérico validado nas rotas de hashtag | `USER_POST`, validado localmente | Melhor caminho observado para integrar. A sondagem combinou assinatura local do F2, endpoints web usados pelo TikTokApi e transporte `curl_cffi`. [Endpoints F2](https://github.com/Johnserf-Seed/f2/blob/v0.0.1.8-pw3/f2/apps/tiktok/api.py). |
| TikTokDownloader | Não documentado para TikTok | Não documentado para TikTok | Sim | A lista distingue busca/hot board de **Douyin**. README informa que algoritmos de assinatura deixaram de ser mantidos e pede implementação própria. Não oferece desbloqueio completo pronto. [README inglês](https://github.com/JoeanAmier/TikTokDownloader/blob/master/README_EN.md). |

## Sondagens locais e recomendação

O `main` do TikTok-Api ainda declara **7.3.5**, a versão já instalada. Sua implementação oferece `browser`, `executable_path`, `page_factory`, `browser_context_factory`, `context_options` e obtenção automática de `msToken` quando ausente. A própria documentação diz que essa obtenção não é garantida. Trocar o pacote pela mesma versão não constitui correção. [Versão](https://github.com/davidteather/TikTok-Api/blob/main/setup.py), [sessões](https://github.com/davidteather/TikTok-Api/blob/main/TikTokApi/tiktok.py).

Uma sondagem local isolada executada nesta investigação, pelo script `.runtime/pilot/probe_upstream_guest.py`, usou diretamente TikTokApi, sem o bloqueio de rede do adaptador Pulso, sem login, cookies fornecidos, token ou proxy. A sessão abriu. Recomendações com `count=1` devolveram **zero** itens em 15,05 s, hashtag `receitas` produziu `EmptyResponseException` aos 15,92 s cumulativos e publicações de `@tiktok` produziram `KeyError` aos 16,34 s cumulativos. Retirar o bloqueio de rede do produto não desbloqueou a coleta nesse ambiente. Isso não identifica sozinho a causa da resposta da plataforma.

O **F2 na branch `v0.0.1.8-pw3`** atualiza duas partes relevantes. Seu crawler usa transporte `curl_cffi` e assinatura local `XGnarlyManager`. O mantenedor relata respostas HTTP 200 vazias com transporte httpx mesmo com assinatura. O gerenciador aceita cookie vazio e deixa `msToken` vazio quando ausente. [Crawler](https://github.com/Johnserf-Seed/f2/blob/v0.0.1.8-pw3/f2/apps/tiktok/crawler.py), [assinatura](https://github.com/Johnserf-Seed/f2/blob/v0.0.1.8-pw3/f2/apps/tiktok/utils.py).

A sondagem `.runtime/pilot/probe_f2_guest.py` usou o commit [`f6be8c0ffba9a127075bbeafe4838716650b6325`](https://github.com/Johnserf-Seed/f2/commit/f6be8c0ffba9a127075bbeafe4838716650b6325), instalado em `.runtime/probes/f2-venv`. Combinou `XGnarlyManager`, `BaseRequestModel`, o User-Agent de `ClientConfManager` e `curl_cffi.Session(impersonate='chrome')`. O cookie passado ao assinador ficou vazio. Não foram fornecidos login, credenciais de navegador, cookies externos ou proxy. A verificação TLS permaneceu ativa.

| Superfície | Requisições | Resultado observado | Duração |
| --- | --- | --- | ---: |
| Recomendações | `/api/recommend/item_list/`, `count=1` | HTTP 200, código 0, um vídeo | 2,48 s |
| Criador `@tiktok` | `/api/user/detail/` e `/api/post/item_list/`, `count=1` | Perfil e um vídeo, HTTP 200 e código 0 | 1,20 s |
| Hashtag `receitas` | `/api/challenge/detail/` e `/api/challenge/item_list/`, `count=1` | Hashtag e um vídeo, HTTP 200 e código 0 | 1,67 s |

As rotas de hashtag não constam no catálogo próprio do F2. A experiência forneceu ao assinador genérico as rotas web usadas pelo TikTokApi e comprovou resposta naquele ambiente. O resumo está em `.runtime/pilot/f2-guest-summary.json`. As durações de criador e hashtag incluem a consulta inicial e a listagem. A sondagem não mediu paginação, estabilidade, cobertura de todos os nichos, origem brasileira ou crescimento dos contadores. [Rotas de hashtag TikTokApi](https://github.com/davidteather/TikTok-Api/blob/main/TikTokApi/api/hashtag.py).

O Evil0ctal é a opção parcial com mais adoção específica e infraestrutura pronta. Desde a versão 5.1.10 sua busca de publicações TikTok exige identidade autenticada. Seu catálogo continua sem tendências TikTok. [Releases](https://github.com/Evil0ctal/Douyin_TikTok_Download_API/releases).

O Pulso recebeu uma integração opcional com o interpretador F2 isolado. A validação pela interface `TikTokCollector` coletou e persistiu um vídeo por rota, preservou a procedência `f2-public-web` e confirmou o perfil público. As três observações chegaram com país desconhecido. A consulta de perfil em sessão recém-aberta retornou corpo vazio. Inicializar a sessão com uma recomendação pública antes de consultar perfil ou hashtag resolveu esse caso na repetição. Cookies dessa sessão são temporários e ficam no processo filho.

A integração valida DNS público, fixa o IP na conexão TLS direta, restringe destinos e redirecionamentos, limita a resposta por callback durante a transferência e preserva `Retry-After`. As rotas e o perfil passaram novamente após essas verificações. A aceitação do piloto depende de origem brasileira verificável, medições sucessivas e cobertura estável. Consulte a [configuração operacional](../operations.md#ambiente-f2-isolado). [Estado do piloto](pilot-discovery-status.md), [requisitos do produto](../../saas-inteligencia-viral-tiktok.md).
