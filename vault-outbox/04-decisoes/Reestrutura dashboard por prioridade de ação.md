---
tipo: decisao
criado: 2026-09-06
tags: [decisao]
temas: [Observability]
projetos: [AYA]
---

# Reestrutura dashboard por prioridade de ação

O dashboard interno (`dashboard.py`, local, não publicado) tinha os problemas clássicos de painel-por-tipo-de-dado: insights sem prioridade, sem tendência real (só um antes/depois grosseiro), barras sempre verdes independente de bom/ruim, e nenhuma evidência ligada às recorrências — pra achar as duas hipóteses de prompt de hoje, tive que grepar `debug/*.json` na mão.

Redesenhado por "job to be done": ① Ação agora → ② Tendência → ③ Conteúdo editorial → ④ Operação → ⑤ Log de referência (colapsado). Mudanças concretas:
- Cor nas barras amarrada aos mesmos limiares que já disparam insight determinístico (dimensão ≤3.5, tema ≥50%, especulativo ≥50%) — nunca um threshold novo só pro visual.
- Sparkline SVG do score por edição, substituindo o antes/depois.
- Tabelas de hipóteses/false-negatives recorrentes agora mostram **em quais edições** aconteceu, com selo de severidade (🔴 crônico 4+, 🟠 recorrente 2-3).

Validado: as duas hipóteses corrigidas hoje já apareciam como 🔴 no topo da tabela nova — prova de que o redesenho entrega o que a versão antiga não entregava.

---
**Temas:** [[Observability]]
**Projeto:** [[AYA]]
**Daily:** [[2026-09-06]]
