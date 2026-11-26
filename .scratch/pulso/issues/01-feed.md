# 01: Acesso ao workspace e feed

What to build: Acesso ao workspace e feed de ponta a ponta, conforme a especificação e o desenho aprovado.

Blocked by: None

Status: resolved

- [x] Sessão segura, CSRF e contexto de workspace para autorização.
- [x] Feed persistido com países ISO, períodos, métricas nulas, ranking por velocidade e cursor.
- [x] Interface responsiva, hashtags locais e fixture opt-in de desenvolvimento.

## Comments

Fronteiras de teste e critérios detalhados: desenho aprovado e plano de implementação.

Verificação: 7 testes HTTP com PostgreSQL passaram; fluxo Playwright passou em desktop e celular; TypeScript, mypy e build Next passaram. O isolamento das tabelas privadas adicionais é validado nos tickets que as introduzem.
