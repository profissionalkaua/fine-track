# 08: Operação e validação do piloto

What to build: Operação e validação do piloto de ponta a ponta, conforme a especificação e o desenho aprovado.

Blocked by: 07

Status: ready-for-human

- [x] Compose, métricas, retenção e runbook de backup/restauração.
- [ ] Validar isolamento, SSRF, geração com dados hostis e recuperação de jobs.
- [x] Suíte, tipos, build, navegador desktop/celular e revisão Standards/Spec.

## Comments

Continuação em 25/11/2026: 46 testes Python (incluindo transcrição offline), 14 de navegador, tipos e build passaram. Texto e transcrição locais configurados. CI de aplicação/Compose preparada; execução de containers e avaliação longitudinal permanecem pendentes. Ver ticket 09 e `docs/implementation-verification.md`.

Fronteiras de teste e critérios detalhados: desenho aprovado e plano de implementação.

C?digo operacional entregue. Isolamento, URLs hostis, respostas inv?lidas, retries e falhas de provedor foram exercitados localmente. Backup restaurado em banco novo. Pendem valida??o de perda real de broker/worker e Compose em ambiente Docker, acesso autorizado ? fonte e avalia??o de modelos. Ver docs/implementation-verification.md.
