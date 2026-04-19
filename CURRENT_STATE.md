# AYA's Daily — Current State

> Snapshot do pipeline em produção. Atualizar sempre que houver mudança de versão, fonte ou arquitetura.
> **Última atualização:** 19/04/2026 — Pipeline v5.3

---

## Status geral

| Item | Status |
|------|--------|
| Pipeline principal | ✅ Ativo — roda diariamente às 7:55 BRT |
| Social posting | ⏸ Pausado — workflow existe mas não está operando |
| Feedback loop | ✅ Ativo — Google Sheet + Apps Script + feedback.html |
| Fase atual | 🔍 Monitoramento — aguardando dados de 2-3 edições antes de nova iteração editorial |
| DEBUG_SAVE | ✅ Ativo — salva `curation.json` + `items.json` em `debug/` a cada edição |

---

## Versão atual: Pipeline v5.3

**Branch:** `main`
**Modelo:** Gemini 2.5 Flash (`gemini-2.5-flash`)
**Framework editorial:** v5.3 (AI Gate + 5-step pipeline + Radar section)

---

## Arquitetura do pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  COLETA — 10 fontes ativas                                      │
│                                                                 │
│  Community (4)    │  AI Labs (3)        │  Geographic (3)       │
│  Reddit   w=1.0   │  Anthropic  w=0.8   │  SCMP Tech  w=0.9    │
│  HN       w=1.2   │  OpenAI     w=0.8   │  RestWorld  w=0.9    │
│  TechCrunch w=1.1 │  DeepMind   w=0.7   │  TechNode   w=0.8    │
│  Lobsters w=0.9   │                     │                       │
│                   │  Research (1 ativo) │                       │
│                   │  arXiv AI   w=1.3   │                       │
└──────────────────────────────┬──────────────────────────────────┘
                               │ ~300 itens/dia
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  PRE-FILTER (pre_filter.py)                                     │
│                                                                 │
│  1. Dedup  — similarity_threshold: 0.7                         │
│  2. Recency — janela 24h, fallback mínimo 10 itens             │
│  3. Z-score — normalização de engagement por source            │
│  4. Recency decay — e^(-age/8), half-life ≈ 5.5h              │
│  5. Source cap — max 25% itens da mesma source                 │
│  6. Wild card — 5 slots aleatórios do pool descartado          │
│                                                                 │
│  Output: 40 itens para o LLM                                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │ 40 itens
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  CURADORIA — AYA (pipeline.py)                                  │
│                                                                 │
│  Model: Gemini 2.5 Flash                                        │
│  Temperature: 0.0                                               │
│  Max output tokens: 16384                                       │
│  Output mode: Structured (Pydantic schema)                      │
│                                                                 │
│  Framework editorial — 5 steps:                                 │
│  STEP 1   AI Gate (obrigatório)                                 │
│  STEP 1.5 Source Bias Check (blogs corporativos)               │
│  STEP 2   Critérios (2 de 3: acionável/mercado/workflows)      │
│  STEP 3   Anti-signal (descarte imediato)                       │
│  STEP 4   Ranking (main_find = mais acionável; tração = tie)   │
│  STEP 4.5 RADAR (early signals — 0, 1 ou 2 itens)             │
│  STEP 5   Teste final (completion task)                         │
│                                                                 │
│  Pós-processamento: validate_tone() — hype detector            │
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

| Source | Tipo | Weight | Região | Status |
|--------|------|--------|--------|--------|
| HackerNews | Community | 1.2 | US | ✅ Ativo |
| TechCrunch | Community | 1.1 | US | ✅ Ativo |
| Reddit | Community | 1.0 | Global | ✅ Ativo |
| Lobsters | Community | 0.9 | US | ✅ Ativo |
| arXiv AI | Research (T1) | 1.3 | Global | ✅ Ativo |
| Anthropic Blog | AI Lab | 0.8 | US | ✅ Ativo |
| OpenAI Blog | AI Lab | 0.8 | US | ✅ Ativo |
| DeepMind Blog | AI Lab | 0.7 | US | ✅ Ativo |
| SCMP Tech | Geographic | 0.9 | Ásia | ✅ Ativo |
| Rest of World | Geographic | 0.9 | Global South | ✅ Ativo |
| TechNode | Geographic | 0.8 | Ásia | ✅ Ativo |
| HuggingFace Papers | Research (T1) | 1.3 | Global | ⏸ Desabilitado (feed URL pendente) |

**Notas de weights:**
- Community sources têm peso maior por sinal de engagement orgânico
- AI Labs têm peso menor (0.7–0.8) — blogs corporativos são marketing-heavy, STEP 1.5 mitiga bias
- Geographic diversity cap: máx 2 itens da mesma região no output final

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
- `GEMINI_API_KEY` — Gemini 2.5 Flash
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
| Gemini 2.5 Flash | Curadoria editorial (LLM) | 🔴 P0 — pipeline falha sem ele |
| Buttondown | Entrega de email | 🔴 P0 — newsletter não sai |
| Reddit API | Coleta community | 🟡 P1 — 1 de 10 fontes |
| GitHub Actions | Automação diária | 🔴 P0 — pipeline não dispara |
| GitHub Pages | feedback.html + archive | 🟢 P2 — feedback degradado |
| Google Sheets + Apps Script | Feedback storage | 🟢 P2 — coleta degradada |
| LinkedIn API | Social posting | ⏸ Pausado — workflow existe, não está ativo |

---

## Itens pendentes / backlog técnico

| Item | Prioridade | Contexto |
|------|-----------|---------|
| HuggingFace Papers — confirmar feed URL | P2 | Source desabilitada desde v5.0 |
| [JC-03] Editorial memory block | P3 | Sprint futura — AYA ter memória de edições anteriores |
| Calibração de pesos via feedback loop | P3 | Aguardar volume de dados suficiente |
| Dry run v5.3 em prod (radar + geographic cap) | P1 | Validar outputs reais antes de iterar |

---

*Para o histórico de como chegamos até aqui → [`DOC_PROCESSO_DAILY_SCOUT.md`](DOC_PROCESSO_DAILY_SCOUT.md)*
*Para decisões editoriais → [`EDITORIAL_RETROSPECTIVE.md`](EDITORIAL_RETROSPECTIVE.md)*
