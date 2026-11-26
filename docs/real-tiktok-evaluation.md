# Avaliação com vídeos reais do TikTok

Executada localmente após solicitação do usuário para substituir entradas sintéticas por vídeos públicos reais. Recorte pretendido do piloto é Brasil, todos os nichos. A avaliação inicial usou três vídeos do mesmo criador. Uma quarta amostra pública escolhida pelo operador foi acrescentada à repetição temporal. A amostra continua insuficiente para representar esse universo.

## Fontes e execução

As páginas públicas forneceram metadados incorporados e endereços públicos de reprodução. Downloads foram limitados a 30 MB/180 segundos, com destinos HTTPS públicos verificados, sem conta, cookies privados, proxy ou contorno de bloqueios. Não foi necessário instalar outro downloader. Mídia, quadros, transcrições e exportações completas ficam exclusivamente em `.runtime/`, ignorado pelo Git.

Cada avaliação usou um workspace local separado, sem alterar as regras dos workspaces anteriores. O corpus entrou como dado sem autoridade, preservando os IDs e métricas fornecidas pela fonte. O campo de país não foi retornado; os registros mantêm país desconhecido e não entram na cobertura BR.

| Amostra pública | Duração medida | Resultado após correção | Tempo observado |
| --- | --- | --- | --- |
| [Contagem binária e memória](https://www.tiktok.com/@manualdomundo/video/6985162794849127685) | 129,75 s | Uma ideia, visão, fala, OCR e postura processados | 166,92 s |
| [Demonstração prática](https://www.tiktok.com/@manualdomundo/video/6912907102075784453) | 14,96 s | Uma ideia, visão, fala, OCR e postura processados | 160,72 s |
| [Microscopia e células](https://www.tiktok.com/@manualdomundo/video/6971120192600476934) | 57,20 s | Uma ideia, visão, fala, OCR e postura processados | 145,72 s |

Tempos incluem espera na fila e carregamento dos modelos; as duas últimas avaliações compartilharam o worker sequencial. Não são latências isoladas de inferência nem p95. A disponibilidade dos extratores indica execução, sem comprovar precisão.

## Falha reproduzida e correção

O primeiro ensaio falhou: 455 registros de postura foram enviados integralmente aos modelos. O gerador textual recusou 66.206 tokens para uma janela de 16.384. A visão também ultrapassou sua janela.

A visão agora recebe até oito observações de postura distribuídas no tempo, incluindo primeira/última e descrição explícita da amostragem. O editor recebe segmentos visuais, OCR e cortes, sem duplicar transcrição, postura bruta ou hashes de quadros. As evidências completas permanecem no resultado/exportação. `media-v3` e `text-v2` invalidam a reutilização dos contratos anteriores.

A repetição da primeira amostra concluiu com entrada textual de 2.456 tokens e entrada visual de 4.312 tokens. Foram preservados 455 registros de postura e 21 trechos de fala. A comparação foi feita contra os relatórios anteriores mantidos localmente.

Regressões na fronteira HTTP dos provedores falharam antes da mudança e passaram depois. Suíte final: **57 aprovados, quatro adaptadores opcionais não executados**; mypy e Ruff aprovados. Os modelos reais e os extratores instalados foram exercitados separadamente pelas três execuções acima.

## Qualidade da avaliação inicial

Comparação assistida com quadros de referência e inspeção das saídas encontrou:

- **Movimento:** as três saídas afirmam ausência de movimento, inclusive em cenas com manipulação de objetos/gestos. Dois quadros enviados à visão não sustentam conclusões contínuas sobre todo o vídeo.
- **Tempo:** a amostra de microscopia recebeu intervalos sobrepostos e atribuição de apresentador/células a extensões incompatíveis. O schema aceita os intervalos numéricos, mas não valida sua correspondência com a cena.
- **Fala:** o tema foi recuperado, mas há erros em números e termos técnicos. Não há transcrição humana de referência; nenhuma taxa WER foi calculada.
- **OCR:** cenas sem texto editorial produziram ruído de leitura. Execução concluída não equivale a texto confiável.
- **Editorial:** houve roteiro estruturado com ID correto, mas também imprecisão conceitual e uma proposta de exercício incoerente. Similaridade automática não substitui revisão editorial/factual.
- **Confiança:** valores elevados devolvidos pela visão não são calibrados; não devem ser usados como aprovação de qualidade.

Essas falhas motivaram a repetição descrita abaixo. A aprovação dos modelos para o piloto final depende de referência anotada e medidas de acerto e custo no hardware local.

## Standards

Revisão independente do delta desde `6ff16d4`: nenhuma violação documental ou smell acionável. A retirada de postura bruta do editor foi registrada como observação e encaminhada ao eixo Spec.

## Spec

Nenhum requisito exige enviar postura bruta ao editor quando a interpretação visual falha. A amostragem identificada, preservação da exportação e repetição real atendem ao ticket 12. A revisão confirmou fechamento da validação técnica, mantendo a reprovação qualitativa separada.

## Pendências preservadas

A leitura direta dessas páginas não valida as rotas de descoberta por trending/hashtag/criador do TikTokApi. Coleta automática continua desativada. Continuam pendentes cobertura geográfica, calibração humana, sete dias de aceitação e paridade com o frame original da Library.

## Repetição temporal de 26 de novembro de 2026

O contrato `media-v4.1` usa timestamps do FFmpeg. Cada chamada de visão recebe um único quadro e a aplicação fixa a observação nesse instante. Movimento, dança e movimento de câmera exigem evidência temporal adicional e recebem valor ausente nessa descrição. Ambiente, figurino e contagem de pessoas continuam sujeitos a erro. A confiança é exibida como estimativa sem calibração.

Uma passagem independente mede diferenças de luminância a cada 250 ms. Cortes, luz e movimento podem produzir o mesmo sinal. A comparação de postura registra mudanças na quantidade estimada de punhos acima dos ombros entre amostras adjacentes, com uma pessoa, visibilidade mínima de 0,8 e sem corte detectado entre elas. Essa heurística exige validação humana. O modal exibe essas medições mesmo quando faltam descrições do modelo.

O OCR mantém palavras com confiança do Tesseract a partir de 85. O editor `text-v3` distingue declaração do autor, observação pontual e hipótese editorial. A configuração local passou para quatro quadros e Whisper `small`. A preparação reproduzível usa `python scripts/prepare-transcription.py --model small`, com revisão fixa e verificação SHA-256 dos pesos. Consulte a [comparação com tiny](research/portuguese-asr-pilot.md).

A quarta amostra pública, escolhida pelo operador, concluiu pela API em **85,66 s**, com uma ideia gerada. A mídia tem 8,45 s. Foram preservados 12 quadros amostrados, 33 diferenças de imagem e 32 estimativas de postura. A visão descreveu instantes em 0,161, 3,094, 5,294 e 8,184 s. O último corresponde ao cartão final do TikTok. Houve zero segmentos de fala reconhecidos e zero mudanças de punhos aprovadas pela heurística. Esses zeros exigem inspeção humana para avaliar falsos negativos. A descrição do autor diverge do ambiente mostrado, e o resultado preserva essa distinção.

As descrições visuais dessa execução saíram em inglês apesar da instrução em português. Precisão editorial, idioma das descrições e reconhecimento de dança continuam sem aprovação. Manifesto, mídia e exportação completa dessa amostra ficam localmente, fora do Git.

A repetição final da microscopia concluiu em **105,69 s**, com uma ideia, 17 segmentos de fala e quatro observações visuais em 0,000, 19,186, 33,575 e 52,761 s. Visão, OCR e postura concluíram. Essa execução usou `media-v4.1` e Whisper `small`. País continua desconhecido nas duas repetições.

Há um orçamento compartilhado para iniciar chamadas de visão. Após 180 s, novos quadros deixam de ser solicitados e observações válidas são preservadas como resultado parcial. O timeout de HTTPX limita espera de rede por operação e permite variação no tempo total.

Standards revisou o delta desde `149733d` sem violações documentais ou smells acionáveis. Spec identificou a ocultação de medições no modal quando faltavam descrições. A correção recebeu regressão desktop e mobile, com falha reproduzida usando a condição anterior.

Verificação final local com pesos e executáveis opcionais habilitados teve **65 testes de backend aprovados**. Ruff, mypy, TypeScript e build de produção também passaram. Os 16 cenários de navegador existentes passaram, e a nova regressão passou em desktop e mobile.
