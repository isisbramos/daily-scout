# Daily Scout — AYA

![Daily Scout Pipeline](https://github.com/isisbramos/daily-scout/actions/workflows/daily-scout.yml/badge.svg)
![Security Audit](https://github.com/isisbramos/daily-scout/actions/workflows/security.yml/badge.svg)
![CodeQL](https://github.com/isisbramos/daily-scout/actions/workflows/codeql.yml/badge.svg)

Pipeline por trás da **AYA**, uma newsletter diária de tech & IA com curadoria automatizada e voz editorial própria. Roda sozinha todo dia via GitHub Actions: busca, filtra, cura com LLM, escreve e envia — sem intervenção manual.

📬 A newsletter em si: **[assineaya.com.br](https://assineaya.com.br)**

## Como funciona

```
sources/ (22 fontes habilitadas em sources_config.json)
    │   Reddit, HackerNews, Lobsters, TechCrunch, arXiv, blogs de labs de IA (Anthropic,
    │   OpenAI, DeepMind, Meta, Mistral, Qwen, HuggingFace...), fontes geográficas (Brasil,
    │   China, Rest of World)
    ▼
pre_filter.py
    │   dedup (URL + título cross-source) → filtro de recência → scoring por peso
    │   temático → diversidade de fonte/geografia/epistêmica → wild card zone
    ▼
DeepSeek (curate_and_write, em pipeline.py)
    │   saída estruturada (Pydantic) com anti-alucinação, injeção de memória
    │   editorial e guard de anti-redundância título↔corpo
    ▼
Jinja2 (render_email)  →  Buttondown (delivery.py)
    │
    ▼
memory_store.py (memória editorial) + vault_bridge.py (nota pro vault pessoal)
    + social_post.py (post social opcional)
```

Em paralelo, três sistemas auxiliares fecham o loop de qualidade:

- **`audit_agent.py`** — LLM-as-judge que audita uma edição por vez (alinhamento editorial, tom, diversidade, coerência do reasoning, false positives/negatives).
- **`content_report.py`** — relatório semanal que olha a *série* de edições: tendências de conteúdo, scorecard de qualidade agregado, e insights priorizados de como melhorar a AYA.
- **`feedback_join.py`** — junta o feedback de 1 clique (🔥/👍/😐) dos leitores com a memória editorial.

## Estrutura do repositório

```
pipeline.py           # orquestra o pipeline principal (fetch → filter → curate → render → send)
sources/              # fontes plugáveis (BaseSource + SourceRegistry)
pre_filter.py         # dedup, scoring, diversidade
schemas.py            # schemas Pydantic da saída estruturada do LLM
llm_config.py         # modelo DeepSeek centralizado (1 lugar pra trocar)
delivery.py           # envio via Buttondown
memory_store.py       # memória editorial entre edições
vault_bridge.py       # ponte pro vault pessoal
social_post.py        # gera post social a partir da edição
audit_agent.py        # LLM-as-judge por edição
content_report.py     # relatório semanal através das edições
feedback_join.py      # junta feedback dos leitores à memória
templates/            # template Jinja2 do e-mail
prompts/              # system instruction + template de curadoria (texto puro)
sources_config.json   # liga/desliga fontes sem mudar código
docs/                 # histórico de produto, arquitetura e decisões editoriais
scripts/              # scripts de validação manual (dry run local, sem LLM/Buttondown)
tests/                # suíte pytest
.github/workflows/    # cron diário, relatório semanal, post social, security audit, CodeQL
```

## Rodando localmente

```bash
cp .env.example .env
# preenche DEEPSEEK_API_KEY e BUTTONDOWN_API_KEY no .env

pip install -r requirements.txt        # dependências de produção
pip install -r requirements-dev.txt    # + pytest, python-dotenv, pillow (dev/scripts/testes)
```

Testar fetch + pre-filter + render **sem** chamar o LLM ou enviar e-mail:

```bash
python scripts/manual_dry_run.py
```

Rodar a suíte de testes:

```bash
pytest tests/
```

## CI/CD

| Workflow | Quando roda | O que faz |
|---|---|---|
| `daily-scout.yml` | diário, 06:37 UTC | pipeline completo — busca, cura, envia a edição |
| `content-report.yml` | semanal (segunda) | gera o relatório de conteúdo em `reports/` |
| `social-post.yml` | diário, 3h depois do envio | posta o resumo social da edição |
| `security.yml` | semanal + PRs que tocam deps | `pip-audit` nas dependências |
| `codeql.yml` | semanal + push/PR em `.py` | análise estática (CodeQL) do código Python |

Dependências são gerenciadas via Dependabot (`.github/dependabot.yml`), com versões pinadas em `requirements.txt`/`requirements-dev.txt` — os bumps chegam como PR em vez de silenciosos.

## Mais contexto

`docs/` tem o histórico completo: snapshot do estado atual (`CURRENT_STATE.md`), visão de produto (`PRODUCT.md`), evolução técnica (`DOC_PROCESSO_DAILY_SCOUT.md`), evolução editorial (`EDITORIAL_RETROSPECTIVE.md`), roadmap (`ROADMAP.md`) e o estudo de fontes (`SOURCES_STUDY.md`).

> `CURRENT_STATE.md` e `PRODUCT.md` são snapshots mantidos manualmente e podem ficar desatualizados (status de features, datas, backlog) — o código-fonte é sempre a referência final. A contagem de fontes acima é travada por `tests/test_docs_sync.py` contra `sources_config.json` — rode `python scripts/source_stats.py` pra conferir o número real.
