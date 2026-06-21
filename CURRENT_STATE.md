# AYA's Daily — Current State

> Snapshot do pipeline em produção. Atualizar sempre que houver mudança de versão, fonte ou arquitetura.
> **Última atualização:** 20/05/2026 — Pipeline v5.4

---

## Status geral

| Item | Status |
|------|--------|
| Pipeline principal | ✅ Ativo — roda diariamente às 7:55 BRT |
| Social posting | ⏸ Pausado — workflow existe mas não está operando |
| Feedback loop | ✅ Ativo — Google Sheet + Apps Script + feedback.html |
| Fase atual | 📦 Produto estabilizado — v5.4 validado, Product Spec v0.2 travada, executando backlog de distribuição |
| DEBUG_SAVE | ✅ Ativo — salva `curation.json` + `items.json` em `debug/` a cada edição |

---

## Versão atual: Pipeline v5.4

**Branch:** `main`
**Modelo:** DeepSeek V3 (`deepseek-chat` via OpenAI SDK, `https://api.deepseek.com`)
**Framework editorial:** v5.4 (AI Gate + filtro léxico anti-hype + filtro estrutural anti-opinion)

---

## Arquitetura do pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  COLETA — 22 fontes ativas                                      │
│                                                                 │
│  Community (4)      │  Research T1 (2)    │  AI Labs (4)        │
│  Reddit     w=1.0   │  arXiv AI   w=1.3   │  Anthropic  w=0.8  │
│  HN         w=1.2   │  HF Papers  w=1.3   │  OpenAI     w=0.8  │
│  TechCrunch w=1.1   │                     │  DeepMind   w=0.7  │
│  Lobsters   w=0.9   │  Europe/China (2)   │  Meta AI    w=0.8  │
│                     │  Mistral    w=0.7   │                     │
│  Tooling (1)        │  Qwen       w=0.9   │  Geographic (3)     │
│  HF Blog    w=1.0   │                     │  SCMP Tech  w=0.9  │
│                     │  Voice (3)          │  RestWorld  w=0.9  │
│  Journalism (1)     │  S.Willison w=1.1   │  TechNode   w=0.8  │
│  MIT TR     w=1.0   │  E.Mollick  w=0.9   │                     │
│                     │  Stratechery w=0.9  │  Brasil/LatAm (2)  │
│                     │                     │  Ag.Brasil  w=0.8  │
│                     │                     │  MIT TR BR  w=0.9  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ ~300+ itens/dia
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  PRE-FILTER (pre_filter.py)                                     │
│                                                                 │
│  1. Dedup  — similarity_threshold: 0.7                         │
│  2. Recency — janela 24h, fallback mínimo 10 itens             │
│  3. Z-score — normalização de engagement por source            │
│  4. Recency decay — e^(-age/8), half-life ≈ 5.5h              │
│  5. Source cap — max 25% itens da mesma source                 │
│  6. Geographic cap — max 30% de qualquer região (latam/asia)   │
│  7. Wild card — 5 slots aleatórios do pool descartado          │
│                                                                 │
│  Output: 40 itens para o LLM                                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ 40 itens
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  CURADORIA — AYA (pipeline.py)                                  │
│                                                                 │
│  Model: DeepSeek V3 (deepseek-chat)                             │
│  SDK: openai (OpenAI-compatible)                                │
│  Temperature: 0.0                                               │
│  Max output tokens: 16384                                       │
│  Output mode: Structured (Pydantic schema)                      │
│                                                                 │
│  Framework editorial v5.4 — 5 steps + 2 filtros paralelos:     │
│  STEP 1   AI Gate (obrigatório)                                 │
│  STEP 1.5 Source Bias Check + filtro estrutural anti-opinion    │
│             (descarta manifestos pessoais sem evento âncora)    │
│  STEP 2   Critérios acionáveis (workflow impact concreto req.)  │
│  STEP 3   Anti-signal expandido (incl. opinião sem evento)      │
│  STEP 4   Ranking (main_find = mais acionável; tração = tie)   │
│  STEP 4.5 RADAR (early signals — 0, 1 ou 2 itens)             │
│  STEP 5   Teste final (completion task)                         │
│                                                                 │
│  Pós-processamento: validate_tone() — hype detector léxico     │
│  Max retries: 5 │ Finish reason guard ativo                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │ CurationOutput (JSON validado)
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  ENTREGA                                                        │
│                                                                 │
│  Email  → Jinja2 (templates/email.html) → Buttondown API       │
│  Social → content_adapter.py → LinkedIn API (+3h delay)        │
│  Output → output/ (artifacts GitHub Actions, 30 dias)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fontes ativas

**22 fontes ativas** em `sources_config.json` (adicionadas em ondas: v5.0 base → Onda 1 → Onda 2 → Onda 3)

| Source | Tipo | Weight | Região | Onda |
|--------|------|--------|--------|------|
| HackerNews | Community | 1.2 | US | v5.0 |
| TechCrunch | Community | 1.1 | US | v5.0 |
| Reddit | Community | 1.0 | Global | v5.0 |
| Lobsters | Community | 0.9 | US | v5.0 |
| arXiv AI (cs.AI/LG/CL) | Research T1 | 1.3 | Global | v5.0 |
| HuggingFace Papers | Research T1 | 1.3 | Global | v5.0 |
| Anthropic Blog | AI Lab | 0.8 | US | v5.0 |
| OpenAI Blog | AI Lab | 0.8 | US | v5.0 |
| DeepMind Blog | AI Lab | 0.7 | US | v5.0 |
| SCMP Tech | Geographic | 0.9 | Ásia | v5.0 |
| Rest of World | Geographic | 0.9 | Global South | v5.0 |
| TechNode | Geographic | 0.8 | Ásia | v5.0 |
| Meta AI Blog | AI Lab | 0.8 | US | Onda 1 |
| HuggingFace Blog | Tooling | 1.0 | Global | Onda 1 |
| Simon Willison | Voice | 1.1 | Global | Onda 1 |
| MIT Tech Review | Journalism | 1.0 | US | Onda 1 |
| Mistral Releases | Europe | 0.7 | EU | Onda 2 |
| Qwen Blog | China Lab | 0.9 | CN | Onda 2 |
| Ethan Mollick | Voice | 0.9 | Global | Onda 2 |
| Stratechery | Voice | 0.9 | Global | Onda 2 |
| Agência Brasil | Brasil/LatAm | 0.8 | LatAm | Onda 3 |
| MIT Tech Review Brasil | Brasil/LatAm | 0.9 | LatAm | Onda 3 |

**Notas de weights:**
- Research T1 (arXiv, HF Papers) têm peso máximo (1.3) — signal acadêmico mais limpo
- Community sources (HN, TechCrunch) têm peso alto por engagement orgânico
- Voice sources (Simon Willison, Mollick) são pré-curados por editores humanos — sinal confiável
- AI Labs (0.7–0.8) — blogs corporativos são marketing-heavy, STEP 1.5 mitiga bias
- LatAm e Ásia: cap geográfico de 30% por região para evitar over-representation

---

## Schemas de output (Pydantic)

```python
CurationOutput
  └── reasoning: Reasoning          # observability — ai_gate_passed, rejected_sample, rationale
  └── meta: Meta                    # edition_number, edition_date, correspondent_intro
  └── main_find: MainFind           # title, body, bullets, source, url, display_url
  └── quick_finds: list[QuickFind]  # title, body, bullets, source, url, display_url
  └── radar: list[RadarItem]        # title, source, why_watch, url, display_url (0–2 itens)
```

---

## Automação (GitHub Actions)

| Workflow | Trigger | Horário | O que faz | Status |
|----------|---------|---------|-----------|--------|
| `daily-scout.yml` | Cron + manual | 10:00 UTC (7:55 BRT) | Pipeline completo: fetch → filter → curadoria → email | ✅ Ativo |
| `social-post.yml` | Cron | 14:00 UTC (11:00 BRT) | Post LinkedIn (+3h após email) | ⏸ Pausado |

**Secrets configurados:**
- `DEEPSEEK_API_KEY` — DeepSeek V3 (migrado de `GEMINI_API_KEY` em 24/04/2026)
- `BUTTONDOWN_API_KEY` — entrega de email
- `FEEDBACK_BASE_URL` — URL do feedback collector

**Artifacts gerados por edição (GitHub Actions, 30 dias):**
- `edition-XXX/` — HTML do email + social content
- `debug-XXX/` — `edition_XXX_curation.json` + `edition_XXX_items.json` (para audit)

**Manual trigger disponível:** `workflow_dispatch` com parâmetros `edition_number` e `dry_run`

---

## Feedback loop

| Componente | Tecnologia | Status |
|-----------|-----------|--------|
| Collector | `feedback.html` (GitHub Pages) | ✅ Ativo |
| Ratings | 🔥 Fire / 👍 Solid / 😐 Meh | — |
| Storage | Google Sheet "Daily Scout Feedback" | ✅ Ativo |
| Backend | Google Apps Script (web app pública) | ✅ Ativo |
| Integração | Link no footer de cada edição | ✅ Ativo |

Sheet ID: `1ToD2eW-owhGsdE0cswVHNGiX8yHJH87Mdtviz-l6kuM`

---

## Estrutura de arquivos

```
daily-scout-v3/
│
├── pipeline.py              ← Pipeline principal (v5.3)
├── pre_filter.py            ← Pre-filter estatístico
├── schemas.py               ← Pydantic schemas (CurationOutput)
├── delivery.py              ← Buttondown API + fallback
├── exceptions.py            ← FetchError, CurationError, DeliveryError
├── social_post.py           ← Post LinkedIn (delayed)
│
├── sources/                 ← Módulos plugáveis de coleta
│   ├── base.py              ← SourceRegistry + SourceItem
│   ├── reddit.py
│   ├── hackernews.py
│   ├── techcrunch.py
│   ├── lobsters.py
│   └── rss_generic.py       ← AI labs + geographic + arXiv
│
├── prompts/
│   ├── system_instruction.txt   ← "Constituição" da Aya (identidade + PODE/NÃO PODE)
│   └── curation_template.txt    ← User prompt (framework 5-step + few-shots + dados)
│
├── templates/
│   └── email.html           ← Template Jinja2 (main_find + quick_finds + radar)
│
├── social/
│   ├── content_adapter.py   ← Adaptação pra LinkedIn
│   └── linkedin.py          ← LinkedIn API
│
├── apps-script/
│   └── Code.gs              ← Google Apps Script do feedback loop
│
├── .github/workflows/
│   ├── daily-scout.yml      ← Workflow principal (cron diário)
│   └── social-post.yml      ← Workflow LinkedIn (delayed)
│
├── sources_config.json      ← Config das fontes (on/off, pesos, regiões)
├── requirements.txt         ← google-genai, pydantic, requests, jinja2, feedparser
│
├── test_dry_run.py          ← Teste sem LLM (fetch → filter → render)
├── audit_agent.py           ← Debug agent para análise de curadoria
│
├── feedback.html            ← 1-click feedback (🔥/👍/😐)
├── index.html               ← Newsletter archive UI
├── mobile-preview.html      ← Preview mobile do template
├── aya-avatar.png           ← Avatar da Aya
│
│   — Documentação —
├── PRODUCT.md               ← Visão de produto, audience, métricas
├── CURRENT_STATE.md         ← Este documento
├── ROADMAP.md               ← Shipped + backlog
├── RUNBOOK.md               ← Operations + troubleshooting
├── DOC_PROCESSO_DAILY_SCOUT.md   ← Journey técnica (v1 → v5.3)
├── EDITORIAL_RETROSPECTIVE.md    ← Evolução editorial v4 → v5.2
├── FEEDBACK_SETUP.md             ← Quick reference feedback loop
│
├── blueprint/               ← Template para novos projetos (cookiecutter)
├── output/                  ← Artifacts de cada edição (ignorado pelo git)
├── debug/                   ← DEBUG_SAVE outputs (ignorado pelo git)
└── archive/                 ← Docs históricos e visualizações React
```

---

## Dependências externas

| Serviço | Uso | Criticidade |
|---------|-----|-------------|
| DeepSeek V3 (`deepseek-chat`) | Curadoria editorial (LLM) | 🔴 P0 — pipeline falha sem ele |
| Buttondown | Entrega de email | 🔴 P0 — newsletter não sai |
| Reddit API | Coleta community | 🟡 P1 — 1 de 22 fontes |
| GitHub Actions | Automação diária | 🔴 P0 — pipeline não dispara |
| GitHub Pages | feedback.html + archive | 🟢 P2 — feedback degradado |
| Google Sheets + Apps Script | Feedback storage | 🟢 P2 — coleta degradada |
| LinkedIn API | Social posting | ⏸ Pausado — workflow existe, não está ativo |

---

## Itens pendentes / backlog técnico

| Item | Prioridade | Contexto |
|------|-----------|---------|
| Welcome email sequence → Buttondown | P1 | Copy pronto desde 12/05, aguarda execução manual no Buttondown |
| Ativar analytics Buttondown (open rate / CTR) | P1 | Pronto para ativar, necessário para acompanhar North Star metrics |
| Reativar LinkedIn social posting | P2 | Workflow construído — verificar `LINKEDIN_ACCESS_TOKEN` e `LINKEDIN_PERSON_URN` |
| Asset migration rebrand (logo, avatar, email footer, Apps Script) | P2 | Decisão de rebrand em 20/05; aguarda versões finais do avatar |
| [JC-03] Editorial memory block | P3 | Sprint futura — AYA injetar resumo das últimas 3-5 edições no prompt |
| Calibração de pesos via feedback loop | P3 | Aguardar volume de dados suficiente (90 dias) |

---

*Para o histórico de como chegamos até aqui → [`DOC_PROCESSO_DAILY_SCOUT.md`](DOC_PROCESSO_DAILY_SCOUT.md)*
*Para decisões editoriais → [`EDITORIAL_RETROSPECTIVE.md`](EDITORIAL_RETROSPECTIVE.md)*
