---
tipo: decisao
criado: 2026-09-06
tags: [decisao]
temas: [Editorial, Observability]
projetos: [AYA]
---

# Mantém DeepSeek como judge de curadoria

Testei dois modelos Gemini como candidato mais barato pro `audit_agent` (hoje usa o mesmo DeepSeek da curadoria):

- **Gemini 3.5 Flash Lite** — barato, mas complacente demais: achou só 20% dos false negatives que o DeepSeek achou nas mesmas 7 edições (0.6 vs 3.0 em média). Deu 5/5 pra uma edição que o DeepSeek tinha dado 3/5 com críticas concretas.
- **Gemini 3.8 Flash** — rigor bem mais próximo do DeepSeek (achou 66% dos false negatives), mas custa $0,75/$3,75 por milhão de tokens — 3 a 5× mais caro que o DeepSeek (~$0,22/$0,66/M). Também exigiu billing pago (free tier tem cota de 20 req/dia, insuficiente pro lote semanal).

**Decisão:** ficar no DeepSeek — já é o ponto ótimo de custo×rigor pra esse papel específico. Na escala atual de uso (poucas dezenas de tokens por edição), a diferença de preço é centavos/mês; o que importa é rigor, não custo.

Infra de troca de modelo (`AUDIT_MODEL`/`AUDIT_BASE_URL`/`AUDIT_API_KEY` em `llm_config.py`) ficou pronta e desacoplada da curadoria, caso surja um candidato melhor no futuro.

---
**Temas:** [[Editorial]] · [[Observability]]
**Projeto:** [[AYA]]
**Daily:** [[2026-09-06]]
