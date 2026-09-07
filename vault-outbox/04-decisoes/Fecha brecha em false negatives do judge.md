---
tipo: decisao
criado: 2026-09-06
tags: [decisao]
temas: [Editorial, Observability]
projetos: [AYA]
---

# Fecha brecha em false negatives do judge

Investigando por que HackerNews/TechCrunch lideravam o ranking de "false negatives recorrentes" no dashboard, achei que ~43% dos casos eram ruído do próprio `audit_agent`, não viés de fonte — ele marcava itens sem nenhuma conexão com AI (revival de engine de jogo RTS, decisão da Suprema Corte sobre geofence warrants) como "deveria ter sido incluído" só por terem tração alta, admitindo no próprio texto "não passa no AI Gate" e marcando como false negative mesmo assim.

Duas causas:
1. `AUDIT_SYSTEM` (audit_agent.py) mantém cópia própria das regras de curadoria, separada de `curation_template.txt` — estava desatualizada em relação ao fix de sinal de mercado feito no mesmo dia. Sincronizado.
2. A instrução de FALSE NEGATIVES nunca reaplicava o AI Gate + critérios de seleção (ao contrário da DIMENSÃO 1, que já faz isso pra false positives). Corrigido pra exigir a mesma régua nos dois sentidos.

Achei também um terceiro ponto — DIMENSÃO 3 (Diversidade) trata "máx 2 itens por fonte" como regra rígida, mas `curation_template.txt` só diz "prefira variedade" — sem número. Não mexi: sem evidência de julgamento errado (Diversidade está em 3.62/5, saudável), ficaria inventando ajuste sem prova.

---
**Temas:** [[Editorial]] · [[Observability]]
**Projeto:** [[AYA]]
**Daily:** [[2026-09-06]]
