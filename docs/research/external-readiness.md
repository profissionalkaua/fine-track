# Prontidão de fontes externas e análise local

Verificado em 25/11/2026. Pesquisa documental, sem acessar credenciais, executar coleta ou instalar modelos. Revisados `backend/pulso/adapters/tiktok.py`, `media.py` e `media_signals.py`.

## Decisão recomendada

Manter descoberta ampla desativada até existir autorização documentada que cubra coleta, armazenamento e uso comercial. Para um primeiro fluxo oficial, integrar criadores que autorizam o Pulso via Display API e aceitar arquivos locais cujo uso tenha sido autorizado. Trend discovery comercial amplo continua sendo uma dependência externa a resolver; não há uma API oficial geral equivalente às três rotas atuais demonstrada nas fontes consultadas.

## TikTok: o que cada opção realmente permite

| Opção | Alcance documentado | Ação necessária |
| --- | --- | --- |
| Display API + Login Kit | Perfil e vídeos públicos do usuário que autorizou o aplicativo; não fornece descoberta geral por hashtag ou trending | Conta de desenvolvedor, aplicativo aprovado, Login Kit/Display API, escopos aprovados, redirect URI e OAuth de cada criador |
| Research API | Consulta de conteúdo público por hashtag, usuário, país de registro e outros filtros | Projeto de pesquisa elegível aprovado; não serve de autorização para SaaS comercial |
| Commercial Content API | Anúncios e outros conteúdos comerciais da biblioteca; não equivale ao universo orgânico de vídeos | Candidatura e aprovação específicas; verificar países e cobertura do contrato |
| Creative Center | Interface oficial de tendências, incluindo filtros de país | Útil para investigação humana; acesso à página não comprova permissão de extração automatizada ou redistribuição |
| `TikTokApi` atual | Wrapper explicitamente não oficial para conteúdo acessível sem login | Exige decisão separada sobre autorização; instalar biblioteca e obter `msToken` não substitui aprovação oficial |

A Display API documenta `/v2/user/info/`, `/v2/video/list/` e `/v2/video/query/`. Os pré-requisitos incluem aprovação e os escopos `user.info.basic` e `video.list`; cada usuário ainda precisa consentir. Para username/bio e estatísticas de perfil, verificar respectivamente `user.info.profile` e `user.info.stats`, pois o escopo básico é mais restrito. Segredos e tokens devem ficar no servidor. Fontes: [visão geral](https://developers.tiktok.com/docs/en/display-api-overview), [início](https://developers.tiktok.com/docs/en/display-api-get-started), [consentimento por escopo](https://developers.tiktok.com/docs/en/scopes-overview), [campos de perfil](https://developers.tiktok.com/bulletin/user-info-scope-migration), [gestão de tokens](https://developers.tiktok.com/docs/en/login-kit-manage-user-access-tokens).

A FAQ da Research API exclui expressamente criadores, anunciantes e usuários comerciais e exige aprovação para um projeto específico. A página de produto anuncia pesquisadores qualificados nos EUA, Europa, Canadá e Brasil; estar no Brasil ou ter conta de desenvolvedor não basta. Quando elegível, o projeto recebe client key/secret e gera client access token. Fontes: [FAQ](https://developers.tiktok.com/docs/en/research-api-faq/), [elegibilidade](https://developers.tiktok.com/products/research-api/), [credenciais de pesquisa](https://developers.tiktok.com/docs/en/research-api-get-started).

A Commercial Content API exige candidatura e cobre sua biblioteca comercial, com lista própria de países. Creative Center mostra tendências e popularidade regional; não foi localizada documentação de API pública que autorize usar essa interface como backend de descoberta do Pulso. Fontes: [produto comercial](https://developers.tiktok.com/products/commercial-content-api), [países](https://developers.tiktok.com/docs/en/commercial-content-api-supported-countries), [Trends](https://ads-useast2a.tiktok.com/resources/help/article/how-to-use-trends?redirected=2).

O próprio mantenedor descreve `TikTokApi` como não oficial e sem suporte a rotas autenticadas. O adaptador usa Chromium e token de sessão; não implementa OAuth oficial nem verifica concessão contratual. A classificação atual de CAPTCHA/403 como bloqueio é apropriada: interromper e informar indisponibilidade, sem contornar CAPTCHA, restrições de conta ou bloqueios. Uma resposta HTTP acessível comprova alcance técnico, não autorização de produção. Fonte da biblioteca: [README do mantenedor](https://github.com/davidteather/TikTok-Api).

## País e proveniência

Na Research API, `region_code` significa o país onde o criador registrou a conta. Isso não comprova local de filmagem, residência atual, nacionalidade ou país da audiência. O campo `region` do wrapper atual não deve herdar automaticamente essa semântica: conservar valor bruto, origem e significado específico da fonte. `confidence=1` pode indicar somente que o campo foi recebido, nunca certeza sobre origem física. Não inferir país de idioma, hashtag, IP do coletor ou feed regional. Quando não houver evidência com significado verificável, registrar desconhecido. Fontes: [Query Videos](https://developers.tiktok.com/docs/en/research-api-specs-query-videos), [codebook](https://developers.tiktok.com/docs/en/research-api-codebook).

## Modelos locais: caminho compatível com o orçamento

Ambiente informado: CPU, RX 6600 com driver antigo, 14 GB de RAM total e aproximadamente 3 GB livres; Ollama informado como `0.40.18`, Qwen2.5 1.5B e Whisper tiny instalados. Versão exata, desempenho e consumo não foram medidos nesta pesquisa. Tamanho do download não é RAM de inferência.

| Função | Escolha inicial | Licença e integração |
| --- | --- | --- |
| OCR | Tesseract + `tessdata_fast`, `por` e `eng` | Engine e pesos Apache-2.0. Diagnóstico inicial: português não era selecionado. Remediação nesta implementação: executável configurável e `-l por+eng`, com regressão real de OCR |
| Postura | MediaPipe Pose Landmarker Lite, bundle `.task` de aproximadamente 5,78 MB | Model card ligada pela documentação oficial declara Apache-2.0; já existe integração MediaPipe Tasks com caminho local |
| Visão descritiva | Testar `moondream:1.8b`, 1,7 GB, em CPU e um quadro por vez | Tag do Ollama declara Apache-2.0 e mínimo Ollama 0.1.33; é candidato de teste, não garantia de execução com 3 GB livres |
| Áudio | Reutilizar Whisper tiny multilíngue em formato CTranslate2, CPU int8 | Whisper código/pesos MIT; `faster-whisper` precisa de diretório no formato suportado, não apenas qualquer arquivo chamado tiny |

Fontes: [Tesseract](https://tesseract-ocr.github.io/tessdoc/Home.html), [pesos rápidos](https://github.com/tesseract-ocr/tessdata_fast), [licença dos pesos](https://github.com/tesseract-ocr/tessdata_fast/blob/main/LICENSE), [Pose Landmarker oficial](https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker), [model card Lite ligada pelo Google](https://huggingface.co/litert-community/MediaPipe-PoseLandmarker-Lite), [tag Moondream com licença](https://ollama.com/library/moondream:1.8b), [Whisper](https://github.com/openai/whisper), [formato faster-whisper](https://github.com/SYSTRAN/faster-whisper).

Recomendação operacional: executar áudio, OCR, postura e visão sequencialmente, descarregar o modelo textual antes da visão e medir memória/latência em um arquivo curto autorizado. O adaptador atual envia todos os quadros e exige um JSON complexo; não assumir que Moondream obedecerá a esse contrato, produzirá português consistente ou resumirá movimento temporal. Validar primeiro um quadro, depois a resposta estruturada e finalmente múltiplos quadros. Ausência de modelo deve continuar retornando estado parcial.

Não contar com aceleração RX 6600: ela não consta na lista ROCm Windows atual do Ollama. A documentação atual também descreve Vulkan, mas isso não demonstra disponibilidade no runtime instalado ou compatibilidade com seu driver. Planejar CPU; eventual atualização de runtime/driver deve ser verificada separadamente. Fonte: [suporte de hardware do Ollama](https://github.com/ollama/ollama/blob/main/docs/gpu.mdx).

Antes de distribuir pesos, fixar versão/hash, preservar licença e avisos correspondentes ao artefato efetivamente baixado. Não houve download nesta pesquisa. Para testar a mídia, ainda é necessário um vídeo local autorizado; metadados e embed da Display API não devem ser tratados como uma licença geral de download do audiovisual.
