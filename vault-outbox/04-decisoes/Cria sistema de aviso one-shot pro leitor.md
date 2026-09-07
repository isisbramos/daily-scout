---
tipo: decisao
criado: 2026-09-06
tags: [decisao]
temas: [Product Thinking]
projetos: [AYA]
---

# Cria sistema de aviso one-shot pro leitor

Queria anunciar aos assinantes que a curadoria mudou (linguagem simples, "notou diferença? conta pra gente"), sem criar um canal de feedback novo — reusar os botões 🔥/👍/😐 que já existem no rodapé de todo email.

Primeira versão seria uma env var fixa no workflow do GitHub Actions — funcionava, mas exigia lembrar de tirar depois, senão o aviso ia em toda edição futura, não só na de anúncio.

**Decisão:** mecanismo auto-limpante em vez de depender de memória humana. `notices/pending.json` guarda o aviso; `pipeline.py` usa o texto na próxima edição REAL enviada (dry run não conta), registra em `notices/sent_log.jsonl` (histórico permanente de todo aviso já feito) e apaga o pending sozinho. Workflow ganha um passo de persistência espelhando o já usado pra memória editorial.

Fluxo daqui pra frente: pedir o aviso no chat → Claude escreve o pending.json → sai uma vez, sozinho, sem esquecer de desligar.

---
**Temas:** [[Product Thinking]]
**Projeto:** [[AYA]]
**Daily:** [[2026-09-06]]
