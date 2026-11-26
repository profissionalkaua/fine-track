# Coleta pública com ambiente F2 isolado

Blocked by: 13
Status: resolved

O usuário autorizou pesquisar e configurar uma alternativa do GitHub. A sondagem F2 na revisão f6be8c0ffba9a127075bbeafe4838716650b6325 devolveu um item em recomendações, publicações de criador e hashtag.

## Implementação

Adicionar configuração opcional do interpretador F2 isolado. O Collector existente envia somente fonte, referência e quantidade por stdin a um processo com script versionado. Esse processo usa sessão pública temporária, destinos TikTok fixos, TLS validado, limite de resposta e timeout. O processo principal reutiliza a normalização existente, registra a procedência e respeita a chave de coleta desativada. País desconhecido segue sem elegibilidade BR.

Verificar primeiro o contrato público Collector com transporte simulado, incluindo fonte desligada e erros. Implementar o subprocesso, repetir as três rotas reais e executar testes e revisão antes de publicar. A instalação isolada usa o código F2 revisado em .runtime e preserva as dependências da aplicação.

## Aceitação

- [x] Configuração opcional e execução limitada pela interface existente.
- [x] Dados normalizados com procedência, sem atribuição geográfica por parâmetros da requisição.
- [x] Três rotas exercitadas pelo Collector real.
- [x] Erros, testes, revisão e documentação de limites verificados.

## Comments

75 testes de backend passaram com extratores opcionais habilitados. Ruff e mypy passaram. A integração preserva bloqueio de coleta, normalização e procedência. Recomendações, hashtag, publicações de criador e perfil passaram após inicialização da sessão pública. Três registros por repetição foram persistidos localmente com país desconhecido.

Spec identificou limite de resposta aplicado após download, DNS interno e perda de Retry-After. Standards aprofundou o limite de fila interna e proxies herdados do transporte. Os pontos foram corrigidos com callback de transferência, endereço público fixado, conexão direta e propagação da espera. As regressões incluem resposta excessiva, loopback, HTTP429900s e envelope inválido. Revisões finais sem achados materiais pendentes. Duplicação pequena no mapeamento de perfil foi registrada como melhoria opcional.
