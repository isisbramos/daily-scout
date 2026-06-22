# AYA's Daily — Roadmap

> Framework: **Now / Next / Later**
> Última atualização: 22/06/2026

---

## ✅ Shipped — O que foi construído

### Semana 1 — Pipeline & Tone (23–25 mar)

| Data | Versão | O que foi feito |
|------|--------|----------------|
| 23/mar | v1 | Primeiro pipeline funcionando end-to-end: Reddit + HN → Gemini → email |
| 24/mar | v2 | Multi-source (+ TechCrunch, Lobsters) + primeiro fix de tom |
| 25/mar | v3 | Hallucination fix: system instruction separada + schema tipado (Pydantic) + `validate_tone()` |
| 25/mar | v3.1 | Régua PODE/NÃO PODE + few-shots contextuais — equilíbrio entre factual e seco |

**Problema resolvido:** pipeline gerava hallucination e sensacionalismo. v3 construiu 5 camadas de defesa (system instruction + temperatura 0.0 + schema + lembrete final + retry com hype detector).

---

### Semana 1 — Editorial Framework (26 mar)

| Data | Versão | O que foi feito |
|------|--------|----------------|
| 26/mar | v4 | Discovery editorial → AI Gate + pipeline de 5 steps + prompt audit (5.6 → 8.8/10) |

**Problema resolvido:** curadoria selecionava por tração, não por relevância. Prediction markets (539pts HN, zero ângulo AI) era main find enquanto Gemini importando chats ficava de fora.

---

### Semana 1 — Scale & Diversity (27 mar)

| Data | Versão | O que foi feito |
|------|--------|----------------|
| 27/mar | v5.0 | 10 sources: + arXiv AI, Anthropic/OpenAI/DeepMind blogs, SCMP Tech, Rest of World, TechNode |
| 27/mar | v5.0 | Pre-filter rewrite: z-score normalization + exponential recency decay + wild card zone |
| 27/mar | v5.2 | Geographic diversity cap (max 2 itens da mesma região) + weight rebalance |
| 27/mar | v5.2 | Seção RADAR — early signals que passaram no AI Gate mas ficaram fora da seleção principal |
| 27/mar | v5.3 | Prompt hygiene: 9 fixes (conflitos system↔user, few-shots desalinhados, schema stale) |

**Problema resolvido:** echo chamber ocidental + Reddit com conteúdo morno + over-representation de fontes asiáticas.

---

### Semana 2 — Feedback & Observability (26–27 mar)

| Item | O que foi feito |
|------|----------------|
| Feedback loop | Google Sheet + Apps Script + `feedback.html` (🔥/👍/😐 no footer de cada edição) |
| Audit agent | `audit_agent.py` — LLM-as-judge em 3 dimensões: editorial alignment, reasoning coherence, false negatives |
| DEBUG_SAVE | Salva `curation.json` + `items.json` por edição para análise posterior |
| GitHub Actions | Dois workflows: pipeline diário (7:55 BRT) + social posting (11:00 BRT) |

---

### Abril — Expansão de fontes + DeepSeek (19–29 abr)

| Data | O que foi feito |
|------|----------------|
| 19/abr | **Onda 1** — +4 fontes: Meta AI Blog, HuggingFace Blog, Simon Willison, MIT Tech Review |
| 19/abr | HuggingFace Papers habilitado (feed RSS confirmado) |
| 24/abr | **Migração DeepSeek** — Gemini 2.5 Flash → DeepSeek V3 (`deepseek-chat`, OpenAI SDK) |
| 27/abr | **Onda 2** — +4 fontes: Mistral Releases, Qwen Blog, Ethan Mollick, Stratechery |
| 27/abr | **v5.4** — framework editorial endurecido: STEP 1.5 expandido + critérios STEP 2 mais concretos + anti-signal STEP 3 com "opinião pessoal sem evento âncora" |
| 27/abr | **Onda 3** — +2 fontes BR/LatAm: Agência Brasil, MIT Tech Review Brasil |
| 29/abr | fix: enforce signal field nos quick_finds para compatibilidade com DeepSeek structured output |

**Resultado:** 10 → 22 fontes ativas. Stack custo-independente (sem lock-in Google). Framework editorial separa guardrails léxicos (anti-hype) de estruturais (anti-opinion).

---

### Maio — Produto empacotado (12–20 mai)

| Data | O que foi feito |
|------|----------------|
| 12/mai | **Product Spec v0.2 travada** — ICP (Tech Operator + Builder-Adjacent), 4 pillars editoriais, 8 métricas com gates (North Star: CTR ≥ 12%, engaged subs = 30% da lista) |
| 12/mai | Welcome email sequence v1 escrita (drip T+0 / T+3d / T+7d) |
| 20/mai | **Rebrand AYA como entidade autônoma** — avatar, paleta (neon green + olive + charcoal), princípio "marca não orbita fundadora" |

---

### Junho — Memória editorial (22 jun)

| Data | O que foi feito |
|------|----------------|
| 22/jun | **[JC-03] Memória editorial (Camada 1)** — pipeline deixou de ser stateless. `memory_store.py` + `memory/editions.jsonl` (store append-only com títulos/entities/themes por edição, commitado de volta no CI). Injeção das últimas 7 edições no prompt + guard determinístico que remove quick_finds repetidos (overlap ≥2 entidades). main_find repetido é logado. Tudo blindado — erro na memória nunca quebra a newsletter. |

**Escopo v1:** só evitar repetição. `entities`/`themes` acumulam como fundação para futuras análises de correlação e evolução da IA.

---

## 📦 Now — Fase atual (maio 2026)

**Modo:** Produto estabilizado. Executando backlog de distribuição e crescimento.

| Item | Status | Detalhe |
|------|--------|---------|
| Pipeline v5.4 em prod | ✅ Rodando | Diariamente às 7:55 BRT |
| 22 fontes ativas | ✅ Configurado | Ondas 1, 2, 3 completas |
| Feedback loop | ✅ Ativo | Coletando ratings por edição |
| Product Spec v0.2 | ✅ Travada | ICP, pillars, métricas definidas |
| Welcome email sequence | ⏸ Pendente | Copy pronto — aguarda execução no Buttondown |
| Analytics Buttondown | ⏸ Pendente | Necessário para acompanhar CTR / open rate |
| Rebrand assets | ⏸ Pendente | Aguarda versões finais do avatar (Midjourney) |
| Social posting (LinkedIn) | ⏸ Pausado | Workflow existe — reativar quando assets prontos |

**Foco agora:** destravar os P1s de distribuição (welcome email + analytics) antes de qualquer nova iteração editorial.

---

## 🔜 Next — Próximas iterações (backlog priorizado)

### P1 — Welcome email + analytics (pronto pra executar)

Copy do drip já escrito (`welcome-sequence-v1.md` no vault). Falta executar no Buttondown:
- [ ] Criar sequência de automação no Buttondown (T+0, T+3d, T+7d)
- [ ] Ativar analytics (open rate, CTR por edição)
- [ ] Configurar alertas de falha no pipeline (GitHub Actions → email)

---

### P1 — Rebrand assets

Decisão de visual identity travada (20/05). Falta produzir e migrar:
- [ ] Gerar versões finais do avatar (prompts Midjourney prontos no vault)
- [ ] Atualizar `aya-avatar.png` no repo
- [ ] Atualizar template de email (`templates/email.html`) com nova paleta + avatar
- [ ] Atualizar Apps Script do feedback loop (footer do email)
- [ ] Atualizar `index.html` (archive page)

---

### P2 — Reativar social posting

O workflow `social-post.yml` está construído. Falta:
- [ ] Verificar status das secrets `LINKEDIN_ACCESS_TOKEN` e `LINKEDIN_PERSON_URN`
- [ ] Validar `content_adapter.py` com uma edição real em dry-run
- [ ] Mudar `SOCIAL_ENABLED` de volta para `true` no workflow
- Dependência: rebrand assets prontos primeiro (avatar + paleta no template)

---

### P2 — Subscriber growth

Métricas gate definidas: +10 novos subs/semana até 250; CTR ≥ 12%; open rate ≥ 40%.
- [ ] Distribuição orgânica (LinkedIn, comunidades BR de produto/eng)
- [ ] Criar landing page de aquisição clara (`index.html` atual é archive, não acquisition)
- [ ] Referral program (unlock após 250+ engaged subs + 90 dias de dados)

---

### P2 — Análise de dados acumulados

Com DEBUG_SAVE ativo desde abril, já há semanas de artifacts. Rodar `audit_agent.py`:
- A AYA está selecionando bem com DeepSeek? Algum false negative recorrente?
- O feedback (🔥/😐) correlaciona com tipo de conteúdo ou fonte?
- As 12 novas fontes (Ondas 1–3) estão contribuindo ou gerando ruído?

**Output esperado:** hipóteses para v5.5 ou v6 (não mexer antes de ter dados).

---

### P3 — [JC-03] Editorial memory block ✅ Shipped 22/jun

Concluído — ver seção "Junho — Memória editorial" em Shipped. Evolução futura (correlações,
análise de evolução da IA sobre `entities`/`themes` acumulados) fica como aposta separada.

---

## 🔭 Later — Apostas de médio/longo prazo

| Iniciativa | Hipótese | O que precisaria ser verdade |
|-----------|---------|------------------------------|
| **Monetização** | Newsletter com audiência qualificada em AI tem valor para sponsors relevantes | Ter 500+ subscribers ativos com open rate > 40% |
| **Weekly digest** | Leitores que não abrem diariamente ainda querem o sinal semanal | Validar via pesquisa com subscribers inativos |
| **Personalização por persona** | Leitores técnicos vs. líderes de produto querem ângulos diferentes | Ter volume suficiente para segmentar sem fragmentar |
| **API / dados abertos** | Os dados coletados (10 fontes, 300 itens/dia, pre-filter scores) têm valor além da newsletter | Definir modelo: open data, paid API, ou B2B |
| **Multi-idioma** | Cobertura de SCMP e TechNode em inglês perde nuance — edição em mandarim ou espanhol | Validar demanda antes de qualquer desenvolvimento |

---

## O que NÃO está no roadmap (e por quê)

| Item | Decisão |
|------|---------|
| App mobile | Distribuição via email é suficiente na fase atual. Custo de desenvolvimento não justifica. |
| Curadoria humana em cima da AYA | Negaria o pressuposto do produto. O desafio é melhorar a AYA, não compensar com esforço manual. |
| Mudar de DeepSeek agora | Migração de Gemini já feita (24/04). Stack atual funciona. Reavaliar só com degradação documentada. |
| Aumentar frequência (> 1x/dia) | Volume já é alto. Mais frequência sem mais subscribers = mais custo sem mais impacto. |
| Substack / social como canal primário | AYA é produto independente com domínio próprio (`assineaya.com.br`). Canais externos são distribuição, não sede. |

---

*Para o histórico completo de decisões → [`EDITORIAL_RETROSPECTIVE.md`](EDITORIAL_RETROSPECTIVE.md)*
*Para o estado atual do pipeline → [`CURRENT_STATE.md`](CURRENT_STATE.md)*
