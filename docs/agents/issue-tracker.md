# Issue tracker: Local Markdown

As especificações e os tickets deste projeto vivem em `.scratch/`.

## Convenções

- Uma funcionalidade por diretório: `.scratch/<feature-slug>/`. O desenvolvimento inicial usa `.scratch/pulso/`.
- A especificação de implementação fica em `spec.md` nesse diretório e referencia o guia de requisitos original.
- Um arquivo por ticket em `issues/<NN>-<slug>.md`, numerado a partir de `01`, com os bloqueadores antes dos dependentes.
- Cada ticket descreve comportamento verificável de ponta a ponta e critérios de aceitação.
- `Blocked by:` lista os números dos tickets que bloqueiam o trabalho, ou `None`.
- `Status:` registra o estado do ticket. Consulte `triage-labels.md` para os rótulos de triagem.
- Comentários são acrescentados ao final do arquivo sob `## Comments`.

## Operações

Publicar significa criar um arquivo no diretório da funcionalidade. Buscar significa ler o arquivo indicado pelo caminho ou número.

A fronteira de trabalho contém tickets abertos, sem responsável e com todos os bloqueadores resolvidos. Trabalhe em ordem numérica entre os disponíveis.

Ao assumir um ticket, registre `Status: claimed`. Ao concluir os critérios e a verificação, registre `Status: resolved`, marque os critérios atendidos e acrescente a evidência de validação.

Para wayfinding, use `map.md` e um arquivo por decisão em `issues/`, com `Type: research`, `prototype`, `grilling` ou `task`. Registre a resposta em `## Answer` e um resumo com link no mapa.
