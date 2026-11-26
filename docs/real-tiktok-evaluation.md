# Avaliação com vídeos reais do TikTok

Executada localmente após solicitação do usuário para substituir entradas sintéticas por vídeos públicos reais. Recorte pretendido do piloto: Brasil, todos os nichos. Esta amostra tem somente três vídeos do mesmo criador e não representa esse universo.

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

## Qualidade: não aprovada

Comparação assistida com quadros de referência e inspeção das saídas encontrou:

- **Movimento:** as três saídas afirmam ausência de movimento, inclusive em cenas com manipulação de objetos/gestos. Dois quadros enviados à visão não sustentam conclusões contínuas sobre todo o vídeo.
- **Tempo:** a amostra de microscopia recebeu intervalos sobrepostos e atribuição de apresentador/células a extensões incompatíveis. O schema aceita os intervalos numéricos, mas não valida sua correspondência com a cena.
- **Fala:** o tema foi recuperado, mas há erros em números e termos técnicos. Não há transcrição humana de referência; nenhuma taxa WER foi calculada.
- **OCR:** cenas sem texto editorial produziram ruído de leitura. Execução concluída não equivale a texto confiável.
- **Editorial:** houve roteiro estruturado com ID correto, mas também imprecisão conceitual e uma proposta de exercício incoerente. Similaridade automática não substitui revisão editorial/factual.
- **Confiança:** valores elevados devolvidos pela visão não são calibrados; não devem ser usados como aprovação de qualidade.

Essas falhas impedem aprovação dos modelos para o piloto final. Próxima avaliação deve comparar maior cobertura temporal e candidatos de ASR/visão com referência anotada, medindo acerto e custo no hardware local. Nenhum score agregado de qualidade foi inventado.

## Standards

Revisão independente do delta desde `6ff16d4`: nenhuma violação documental ou smell acionável. A retirada de postura bruta do editor foi registrada como observação e encaminhada ao eixo Spec.

## Spec

Nenhum requisito exige enviar postura bruta ao editor quando a interpretação visual falha. A amostragem identificada, preservação da exportação e repetição real atendem ao ticket 12. A revisão confirmou fechamento da validação técnica, mantendo a reprovação qualitativa separada.

## Pendências preservadas

A leitura direta dessas páginas não valida as rotas de descoberta por trending/hashtag/criador do TikTokApi. Coleta automática continua desativada. Continuam pendentes cobertura geográfica, calibração humana, sete dias de aceitação e paridade com o frame original da Library.
