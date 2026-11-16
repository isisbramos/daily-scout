# Estado atual do pipeline

> last-reviewed: 2026-11-15 · Gerado a partir do código (`llm_config.py`, `sources_config.json`, `.github/workflows/`), não do `docs/historico/CURRENT_STATE.md` (esse é de maio e ficou parado). Quando este arquivo e o código discordarem, o código vence — rode `python scripts/source_stats.py` para a contagem real de fontes.

## Modelo

DeepSeek, modelo `deepseek-v4-flash` (via env var `DEEPSEEK_MODEL`, default em código), SDK OpenAI-compatível, endpoint `https://api.deepseek.com`. Thinking desligado (`DEEPSEEK_EXTRA_BODY`) para não consumir o orçamento de `max_tokens` com reasoning tokens. Centralizado em `llm_config.py`.

O judge (`audit_agent.py`) usa o mesmo modelo por padrão; pode trocar por env vars (`AUDIT_BASE_URL`/`AUDIT_MODEL`) sem tocar o código.

## Framework editorial

Versão v5.4, em `prompts/curation_template.txt` + `prompts/system_instruction.txt`. Pipeline de curadoria:

| Step | O que faz |
| --- | --- |
| STEP 1 | AI Gate (obrigatório — sem ângulo de IA, não entra) |
| STEP 1.5 | Source Bias Check (blogs corporativos/pessoais) — exceção para arXiv e HuggingFace Papers, tratados como fonte primária |
| STEP 2 | Critérios acionáveis (pelo menos 2 de 3) |
| STEP 3 | Anti-signal expandido (funding sem produto, panorama sem evento, opinião sem evento, tema saturado na memória editorial) |
| STEP 4 | Ranking (main_find = mais acionável) |
| STEP 4.5 | RADAR — early signals fora da seleção principal (0–2 itens) |
| STEP 4.75 | Checagem antibajulação — confere se a edição cobre produto/lançamento, pesquisa/dado e regulação/crítica |
| STEP 5 | Teste final (completion task) |

Pós-processamento: `validate_tone()` (hype detector léxico).

**Revisor final** (`final_reviewer.py`, Rec. 1 do plano de melhoria editorial): modo `shadow` em `sources_config.json` → `final_review.mode` — roda e só registra o veredito em `debug/edition_N_review.json`, não altera a edição. Promoção para `enforce` depende de medição (ver `data/roadmap.md`).

**Coerência de troca de destaque** (`coherence.py`): toda vez que um guard troca o main_find (repetição, barra do Reddit, revisor em enforce), reescreve o reasoning e a introdução para não contradizer a edição publicada.

**Memória editorial** (`memory_store.py` + `memory/editions.jsonl`): injeta as últimas edições no prompt e bloqueia quick_finds repetidos (overlap ≥2 entidades) e temas saturados.

## Fontes

23 fontes habilitadas em `sources_config.json` (confirme com `python scripts/source_stats.py`) + 1 desabilitada (`qwen_blog` — feed parado desde set/2025, blog migrou para site sem RSS, PR #46).

Pesos (`weight`) variam de 0.7 a 1.3; `arxiv_ai` e `huggingface_papers` têm tier `T1` (pesquisa acadêmica original, isenta do STEP 1.5). Algumas fontes têm `recency_hours` próprio (`apple_ml_research`, `github_blog`: 168h; `ethan_mollick`: 72h) em vez do padrão de 24h.

## Pre-filter e scoring (`pre_filter.py` + `sources_config.json`)

- Recência: janela 24h, fallback mínimo 10 itens.
- Dedup: similaridade ≥ 0.7.
- Scoring: engagement (0.4) + recência com decay exponencial (0.3, constante 8) + diversidade de fonte (0.2) + categoria (0.1).
- `funding_penalty`: 0.5× no score de títulos de rodada/valuation/IPO sem lançamento de produto (Rec. 3) — rebaixa, não exclui.
- Caps: máx. 25% de itens da mesma fonte, máx. 30% de qualquer região geográfica.
- Wild card: 5 slots aleatórios do pool descartado.
- Saída: 40 itens para o LLM.

## Social posting

`SOCIAL_ENABLED` é `false` por padrão em `pipeline.py` e explicitamente setado como `'false'` em `daily-scout.yml` — a geração de conteúdo social está desligada na produção atual. O workflow `social-post.yml` roda todo dia mesmo assim, mas sem conteúdo para postar (ver risco de cross-workflow download em `data/roadmap.md`, achado da revisão dos PRs #17/#18 do Dependabot).

## Tracking de clique (Camada 2, desligado)

`pipeline.py` tem um filtro Jinja `track` que embrulha URLs dos achados num redirect rastreável, controlado por `TRACK_BASE_URL` (secret). Sem essa env var, devolve a URL crua — é a situação hoje. Se ligado, dá sinal de CTR por achado complementar ao analytics do Buttondown.

## Automação (GitHub Actions)

| Workflow | Trigger | O que faz |
| --- | --- | --- |
| `daily-scout.yml` | disparo externo 7h55 BRT via `workflow_dispatch` (setup feito em 16/11/2026; 1º envio real a validar em 17/11; ver `ops/disparo-externo.md`) + cron nativo 06:37 UTC como fallback (atrasa 4,5–10h) + manual | job `guard` (`scripts/edition_guard.py`: pula se a edição já está em `memory/editions.jsonl`, ou se o "transmissão parcial" do dia já saiu, em `memory/fallbacks.jsonl`) → pipeline completo: busca → filtro → curadoria → envio. Persiste memória editorial, avisos e nota do vault de volta pro repo (cada passo isolado, `continue-on-error`). |
| `content-report.yml` | semanal, segunda 12:00 UTC | junta feedback da planilha, baixa artifacts `debug-N` via `gh api` direto (não usa a action `download-artifact`), roda o audit agent, gera o relatório em `reports/`. |
| `social-post.yml` | cron diário 14:00 UTC | baixa artifact `edition-N` (`actions/download-artifact`) e posta no LinkedIn se houver conteúdo social — hoje nunca encontra o artifact (ver nota acima) e sempre pula. |
| `security.yml` | semanal + PRs que tocam deps | `pip-audit`. |
| `codeql.yml` | semanal + push/PR em `.py` | CodeQL. |
| `tests.yml` | semanal + push/PR em `.py`/deps | `pytest tests/`. |

`DEBUG_SAVE=true` no `daily-scout.yml` salva `curation.json` + `items.json` em `debug/` por edição (consumido pelo audit agent).

## Dependências externas

DeepSeek (P0, curadoria), Buttondown (P0, entrega), GitHub Actions (P0, automação), Reddit API (P1, 1 de 23 fontes), GitHub Pages (P2, feedback.html + archive), Google Sheets + Apps Script (P2, armazenamento de feedback), LinkedIn API (desligado — ver Social posting acima).
