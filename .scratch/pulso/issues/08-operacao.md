# 08: Operação e validação do piloto

What to build: Operação e validação do piloto de ponta a ponta, conforme a especificação e o desenho aprovado.

Blocked by: 07

Status: ready-for-human

- [x] Compose, métricas, retenção e runbook de backup/restauração.
- [ ] Validar isolamento, SSRF, geração com dados hostis e recuperação de jobs.
- [ ] Suíte, tipos, build, navegador desktop/celular e revisão Standards/Spec.

## Comments

Fronteiras de teste e critérios detalhados: desenho aprovado e plano de implementação.

C?digo operacional entregue. Isolamento, URLs hostis, respostas inv?lidas, retries e falhas de provedor foram exercitados localmente. Backup restaurado em banco novo. Pendem valida??o de perda real de broker/worker e Compose em ambiente Docker, acesso autorizado ? fonte e avalia??o de modelos. Ver docs/implementation-verification.md.
