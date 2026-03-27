# Editorial Retrospective — Daily Scout v4 → v5.2

*De "tração alta = notícia boa" até pipeline editorial com 10 sources, radar section e geographic diversity cap.*

---

## TL;DR

Em 48h (26-27 março 2026), o Daily Scout evoluiu de um prompt genérico que selecionava prediction markets como achado do dia para um pipeline editorial de 5 steps com 10 sources, pre-filter estatístico, seção Radar de early signals e geographic diversity cap. Este documento é o registro do journey completo.

---

## Capítulo 1 — O Problema (26/03, manhã)

A edição #001 do Daily Scout saiu e o julgamento da AYA não batia com o meu. O achado do dia era prediction markets — 539 pontos no HackerNews, zero ângulo AI. Netflix subindo preço entrou como quick find. Enquanto isso, "Gemini permite importar chats de outros chatbots" (acionável, AI-first, sinal de mercado) ficou relegado.

**Root cause:** O critério editorial vigente era genérico demais — "2 de 3 entre Tração, Impacto, Novidade". Tração alta sozinha garantia entrada. Não havia filtro de relevância temática nem exemplos de descarte.

### O que eu sabia
- A seleção estava errada
- Prediction markets não deveria ser main find
- Netflix não deveria estar na newsletter

### O que eu NÃO sabia
- Qual era o critério certo
- Como articular o que tornava uma notícia "boa" pro Daily Scout
- Como traduzir intuição editorial em instrução pra modelo

---

## Capítulo 2 — Discovery Editorial (26/03, v4)

### Abordagem: entrevista, não definição

Em vez de reescrever o prompt direto, rodamos um discovery em 3 rodadas de perguntas estruturadas. O processo de ser entrevistada sobre o próprio produto revelou critérios que eu não tinha articulado:

**Rodada 1 — O que é bom vs ruim:**
- Main find preferido: Gemini importando chats (não prediction markets)
- Signal: afeta uso de AI hoje + mostra direção do mercado + é acionável
- Anti-signal: genérico demais (Netflix, série B sem ângulo AI)

**Rodada 2 — Posicionamento:**
- Escopo: "AI como lente" (qualquer tech news, mas sempre pelo ângulo AI)
- Persona: curious professionals (não só tech workers)
- Tração: sinal, não filtro (indica tema quente, não garante entrada)

**Rodada 3 — Testes de edge case:**
- So what test: "sabia que agora dá pra..." (leitor sai com algo prático)
- Off-topic: sem ângulo AI, só entra se for impactante demais pra ignorar
- Netflix como quick find: incomodou — não deveria entrar de jeito nenhum

### O framework v4 que saiu desse discovery

Pipeline sequencial em 5 steps:

```
STEP 1 — AI GATE (obrigatório)
  Tem conexão com AI? SIM → continua. NÃO → só se excepcional.

STEP 2 — CRITÉRIOS (2 de 3)
  Acionável / Sinal de mercado / Afeta workflows

STEP 3 — ANTI-SIGNAL (descarte imediato)
  Preço consumer / Funding genérico / Crypto sem AI / UI cosmético

STEP 4 — RANKING
  main_find = mais acionável. Tração = tiebreaker.

STEP 5 — TESTE FINAL (completion task)
  "Agora é possível [X]" ou "[Player] está [movendo pra] [Y]"
```

---

## Capítulo 3 — Prompt Audit (26/03, v4)

O draft v4 foi avaliado com rigor de prompt engineering. Score: 5.6/10 (igual ao v3). Melhor intenção, mas regressões técnicas:

| Problema | Severidade | O que era |
|----------|-----------|-----------|
| Few-shots desalinhados | P0 | Exemplos ensinavam TOM mas não SELEÇÃO. Wine/DirectX passaria no prompt antigo mas falharia no novo (zero AI). |
| Conflito system ↔ user | P1 | SYSTEM diz "tech & AI" (equilibrado), CURATION diz "AI como lente" (AI-first). Modelo sofre conflito nos edge cases. |
| Overlap de critérios | P1 | "Afeta uso de AI" e "Acionável" têm ~70% de overlap. Modelo conta 2 quando é 1. |
| So what como simulação | P2 | "Imagine o leitor contando pro colega" pede ao modelo simular 2 personas. Modelos são ruins nisso. |
| Anti-signal subjetivo | P2 | "Genérico demais" sem heurísticas concretas. |
| Pipeline sem ordem | P2 | 4 camadas de filtragem sem ordem explícita. |

**Score pós-fix: 8.8/10.** O v4 foi deployado com todas as correções.

### Before vs After — Edição #001

**ANTES (prompt v3):**
- Main find: Prediction Markets — impacto negativo (539pts HN) — sem ângulo AI, genérico, entrou por tração
- Quick finds incluíam Netflix sobe preço (noise)
- Gemini importa chats relegado a quick find

**DEPOIS (dry run v4):**
- Main find: Gemini permite importar histórico de chat de outros chatbots — acionável + sinal de mercado + AI-first
- Prediction markets removido (AI gate: falhou)
- Netflix removido (anti-signal: serviço consumer)

**Learning:** Intuição editorial boa + prompt ruim = resultado ruim. Tratar prompt como feature: discovery → spec → audit → test → deploy.

---

## Capítulo 4 — Scaling Sources (27/03, v5.0)

### O problema seguinte

Com o framework editorial resolvido, o próximo bottleneck era a diversidade de fontes. 4 sources (Reddit, HN, TechCrunch, Lobsters) significava echo chamber ocidental, community-driven, anglófona.

### 6 novas sources

**AI Lab Blogs (3):** Anthropic Blog, OpenAI Blog, DeepMind Blog
- Rationale: cobertura first-party de lançamentos de produto + research
- Risk mitigado: STEP 1.5 Source Bias Check — descarta marketing/thought-leadership sem novidade concreta

**Geographic Diversity (3):** SCMP Tech, Rest of World, TechNode
- Rationale: quebrar echo chamber ocidental — perspectivas da Ásia e Global South
- Weights iniciais: SCMP 1.1, Rest of World 1.0, TechNode 0.9

### Arquitetura: `rss_generic.py`

Módulo genérico de RSS com 6 classes registradas no SourceRegistry. Config-driven via `sources_config.json` — liga/desliga fontes sem mudar código.

### Pre-filter rewrite (v5)

O pre-filter anterior era simples demais pra 10 sources. Reescrita completa:

**Z-score normalization:** Engagement comparável entre sources. HN tem scores na casa dos 500, RSS blogs têm 0. Sigmoid normaliza tudo pra [0, 1].

**Exponential recency decay:** `e^(-age/8)` — modela ciclo real de notícias em vez de cutoff hard de 24h. Constant=8 significa half-life de ~5.5h.

**Cross-source signal:** Dedup marca duplicatas com `cross_source_count` em vez de deletar. Se o mesmo tema aparece em HN e TechCrunch, a AYA sabe e pode mencionar.

**Wild card zone:** 5 slots dos 40 enviados ao LLM são aleatórios do pool descartado. Exploration vs exploitation — gems que o scoring heurístico perdeu.

### Prompt engineering v5.0

**10 few-shot examples:** Cobertura de seleção + descarte + tom + geographic + cross-source (vs 5 no v4).

**STEP 1.5 Source Bias Check:** Generalizado pra QUALQUER blog corporativo — não só os 3 AI labs.

**STEP 5 expandido:** 4 templates de completion task (vs 2 no v4).

**Reasoning schema:** `ai_gate_passed`, `rejected_sample`, `rationale`, `perspective_check` — observability do julgamento editorial.

**Shuffle anti-bias:** Items enviados ao LLM em ordem aleatória. Remove position bias.

**Context injection:** AYA sabe total de items e source breakdown antes de decidir.

### Dry run #38
- 10 sources operacionais
- 266 items coletados
- Pipeline processou sem erros
- Pre-filter entregou 40 items diversificados ao Gemini

---

## Capítulo 5 — Feedback Loop #1 (27/03, v5.2)

Após o dry run #38, dois feedbacks claros:

### Feedback 1: "Muito conteúdo sobre China"

O weight de SCMP (1.1) estava acima de HackerNews (1.2) e TechCrunch (1.1), o que na prática dava às fontes asiáticas representação desproporcional.

**Fix — weight rebalance:**
- SCMP: 1.1 → 0.9
- Rest of World: 1.0 → 0.9
- TechNode: 0.9 → 0.8

**Fix — geographic diversity cap no STEP 4:**
- Campo `region` no `sources_config.json` (asia, global_south)
- Regra no prompt: max 2 items da mesma região geográfica entre main_find + quick_finds
- Se houver 3+ items asiáticos fortes, escolher os 2 melhores

### Feedback 2: "Reddit com conteúdo 'morno' em 24h"

Reddit em 24h frequentemente tem discussões incipientes — cedo demais pra ser achado, mas tarde demais pra ignorar.

**Fix — STEP 4.5 RADAR (early signals):**
- Após seleção de main_find + quick_finds, AYA olha items que passaram no AI Gate mas ficaram de fora
- Seleciona 1-2 items com tom "keep an eye": temas emergentes, sinais fracos
- `RadarItem` schema: title, source, why_watch, url, display_url
- Template HTML: seção RADAR com accent color amber (#FBBF24)
- Se nenhum item justifica radar, lista fica vazia — NÃO força items fracos

---

## Resumo da Evolução Técnica

| Aspecto | v3 (pré-intervenção) | v4 (editorial) | v5.0 (scale) | v5.2 (balance) |
|---------|---------------------|----------------|--------------|----------------|
| Sources | 4 | 4 | 10 | 10 |
| Critério | Tração/Impacto/Novidade | AI Gate + 5 steps | AI Gate + 5 steps + bias check | + geographic cap |
| Few-shots | 3 (só tom) | 5 (seleção + descarte) | 10 (+ geographic + cross-source) | 10 |
| Pre-filter | Dedup + recency | Dedup + recency | Z-score + decay + wild card | = |
| Observability | Nenhuma | Nenhuma | Reasoning schema | + Radar section |
| Geographic | Nenhuma | Nenhuma | 3 fontes não-ocidentais | + region cap |
| Prompt score | ~5.6/10 | 8.8/10 | 8.8/10 (+ sync fixes) | = |

---

## Aprendizados Acumulados

### De produto
1. **Discovery por entrevista > definição direta.** Responder perguntas estruturadas extraiu critérios que eu não conseguia articular escrevendo do zero.
2. **Prompt é feature.** discovery → spec → audit → test → deploy. Nunca reescrever e deployar direto.
3. **Feedback loop rápido muda tudo.** O dry run #38 gerou 2 feedbacks concretos (China overweight, Reddit morno) que viraram v5.2 em horas.
4. **Scale revela novos problemas.** 4→10 sources não é 2.5x mais do mesmo — é um tipo diferente de complexidade (bias, normalization, geographic balance).

### De prompt engineering
5. **Exemplos de descarte são tão importantes quanto exemplos de acerto.** O modelo precisa aprender a fronteira.
6. **Pipeline sequencial > lista flat.** Steps numerados geram consistência. AI Gate como step 1 elimina noise na raiz.
7. **Tração é context, não criteria.** Esse shift conceitual mudou todo o framework.
8. **Sync prompt ↔ pipeline é P0.** O prompt audit v5 encontrou que o schema listava 4 sources enquanto o pipeline tinha 10 — bug silencioso.
9. **Reasoning schema = observability.** Ver O QUE a AYA decidiu E POR QUÊ mudou a qualidade do debug.

### De operação
10. **Config-driven > hardcoded.** `sources_config.json` permite ligar/desligar sources sem deploy.
11. **Wild card zone = exploration.** 5 slots aleatórios do pool descartado dão chance pra gems que o scoring perdeu.
12. **Geographic cap no prompt > cap no pre-filter.** A AYA tem contexto editorial que o scoring heurístico não tem.

---

## Status Técnico

- **Branch:** `main` (v5.2 mergeado em 27/03/2026)
- **Sources:** 10 ativas (4 community + 3 AI labs + 3 geographic)
- **Dry run v5.2:** pendente validação em produção (radar + geographic cap)
- **Feedback loop:** Google Sheet + Apps Script + feedback.html deployado (branch `feat/feedback-loop`)

### Próximos passos
- [x] Editorial retrospective document (este documento)
- [ ] Dry run v5.2 — validar radar + geographic cap em prod
- [ ] [JC-03] Editorial memory block — sprint futura
- [ ] Calibração de pesos via feedback loop — futuro

---

*Documentado em 27/03/2026. Este é um documento vivo que será atualizado conforme o pipeline evolui.*
