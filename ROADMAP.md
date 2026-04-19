# AYA's Daily — Roadmap

> Framework: **Now / Next / Later**
> Última atualização: 19/04/2026

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

## 🔍 Now — Fase atual (abril 2026)

**Modo:** Monitoramento. Aguardando dados de 2–3 semanas antes de nova iteração editorial.

| Item | Status | Detalhe |
|------|--------|---------|
| Pipeline v5.3 em prod | ✅ Rodando | Diariamente às 7:55 BRT sem intervenção manual |
| DEBUG_SAVE ativo | ✅ Habilitado | Artifacts `debug-XXX` no GitHub Actions a partir de hoje |
| Feedback loop | ✅ Ativo | Coletando ratings por edição |
| Social posting (LinkedIn) | ⏸ Pausado | Workflow existe — reativar quando pronto |
| HuggingFace Papers | ⏸ Desabilitado | Feed URL pendente de confirmação |

**Foco agora:** deixar o pipeline rodar e acumular dados de feedback antes de mexer no prompt.

---

## 🔜 Next — Próximas iterações (backlog priorizado)

### P1 — Análise de dados acumulados

Depois de 2–3 semanas de `DEBUG_SAVE` ativo, rodar `audit_agent.py` para identificar padrões:
- A AYA está selecionando bem? Quais são os false negatives recorrentes?
- O feedback (🔥/😐) correlaciona com algum tipo de conteúdo ou fonte?
- Alguma fonte está sistematicamente entregando ruído?

**Output esperado:** hipóteses concretas para a próxima iteração do prompt (v5.4 ou v6).

---

### P1 — Reativar social posting

O workflow `social-post.yml` está construído e testado. Falta:
- [ ] Verificar status das secrets `LINKEDIN_ACCESS_TOKEN` e `LINKEDIN_PERSON_URN`
- [ ] Validar `content_adapter.py` com uma edição real em dry-run
- [ ] Mudar `SOCIAL_ENABLED` de volta para `true` no workflow

---

### P2 — HuggingFace Papers

Source T1 desabilitada desde v5.0. Alta relevância (papers com tração na comunidade = signal forte de mercado).
- [ ] Confirmar URL do feed RSS: `https://huggingface.co/papers.rss`
- [ ] Habilitar em `sources_config.json` e validar coleta
- [ ] Monitorar representação na seleção final (pode precisar de weight adjustment)

---

### P2 — Subscriber growth

Produto está rodando — momento de crescer audiência.
- [ ] Definir estratégia de distribuição (LinkedIn orgânico, comunidades, referral)
- [ ] Criar landing page de inscrição clara (o `index.html` atual é archive, não acquisition)
- [ ] Definir meta de subscribers para o próximo quarter

---

### P3 — [JC-03] Editorial memory block

A AYA não tem memória entre edições. Ela pode selecionar o mesmo tema em dias consecutivos sem saber.
- Solução: injetar no prompt um resumo das últimas 3–5 edições (títulos + sources)
- Impacto: evita repetição, melhora percepção de curadoria fresca
- Dependência: requer armazenamento das edições anteriores (JSON ou arquivo simples no repo)

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
| Curadoria humana em cima da Aya | Negaria o pressuposto do produto. O desafio é melhorar a Aya, não compensar com esforço manual. |
| Mudar de Gemini Flash | Custo/qualidade está bom. Reavaliar só se houver degradação de qualidade documentada. |
| Aumentar frequência (> 1x/dia) | Volume já é alto. Mais frequência sem mais subscribers = mais custo sem mais impacto. |

---

*Para o histórico completo de decisões → [`EDITORIAL_RETROSPECTIVE.md`](EDITORIAL_RETROSPECTIVE.md)*
*Para o estado atual do pipeline → [`CURRENT_STATE.md`](CURRENT_STATE.md)*
