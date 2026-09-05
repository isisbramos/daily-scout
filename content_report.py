"""
Daily Scout — Content Report v1.0

Rotina de avaliação editorial da AYA *através das edições* (não uma de cada vez).
Onde o audit_agent.py audita UMA edição (qualidade do julgamento, false negatives,
hipóteses de prompt), este script olha a SÉRIE: o que a AYA vem cobrindo, com qual
diversidade, como o feedback se comporta e como a qualidade evolui — e sintetiza
insights priorizados de como melhorá-la.

Três camadas, combinadas num único relatório Markdown:

  1. TENDÊNCIAS DE CONTEÚDO  ← memory/editions.jsonl  (determinístico, sem LLM)
       temas recorrentes, entidades quentes, mix epistêmico (claim_status),
       diversidade de fontes, fontes configuradas que nunca são selecionadas,
       repetição entre edições e correlação feedback × conteúdo.

  2. SCORECARD DE QUALIDADE  ← debug/edition_*_audit.json  (gerado pelo audit_agent)
       scores por edição e por dimensão, tendência (melhorando/piorando),
       false negatives recorrentes por fonte, hipóteses de prompt recorrentes.

  3. INSÍGHTS DE COMO MELHORAR
       síntese determinística (regras sobre as camadas 1+2) +, opcionalmente,
       uma passada de LLM (DeepSeek) que prioriza recomendações acionáveis.

Uso:
  python content_report.py                      # últimas 14 edições, com síntese LLM
  python content_report.py --last 30            # janela maior
  python content_report.py --all                # tudo que houver
  python content_report.py --no-llm             # só camadas determinísticas
  python content_report.py --editions-file tests/fixtures/sample_editions.jsonl

Saída:
  reports/content_report_YYYYMMDD.md
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import glob
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta

from llm_config import DEEPSEEK_MODEL, DEEPSEEK_EXTRA_BODY
from audit_agent import AUDIT_DIMENSIONS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("content-report")

# ── Paths ──────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
EDITIONS_PATH = os.path.join(ROOT, "memory", "editions.jsonl")
DEBUG_DIR = os.path.join(ROOT, "debug")
REPORTS_DIR = os.path.join(ROOT, "reports")
SOURCES_CONFIG_PATH = os.path.join(ROOT, "sources_config.json")

_BRT = timezone(timedelta(hours=-3))

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")


# ── Carregamento de dados ──────────────────────────────────────────────
def load_editions(path: str, last: int | None) -> list[dict]:
    """Lê o editions.jsonl (uma edição por linha, mais antiga primeiro).

    Tolerante a linhas corrompidas — ignora e segue. Retorna [] se não há arquivo.
    `last` recorta a janela final (None = tudo).
    """
    if not os.path.exists(path):
        return []
    records: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("linha inválida ignorada em %s", path)
    return records[-last:] if last else records


def load_audits(editions: list[dict]) -> dict[str, dict]:
    """Lê os audits que o audit_agent.py já gerou (debug/edition_XXX_audit.json).

    Só retorna audits cujas edições estão na janela. Edições sem audit ficam de fora
    (o relatório sinaliza a cobertura). Não chama LLM aqui — apenas consome.
    """
    audits: dict[str, dict] = {}
    wanted = {e.get("edition") for e in editions}
    for f in sorted(glob.glob(os.path.join(DEBUG_DIR, "edition_*_audit.json"))):
        edition = os.path.basename(f).split("_")[1]
        if wanted and edition not in wanted:
            continue
        try:
            with open(f, encoding="utf-8") as fh:
                audits[edition] = json.load(fh)
        except (json.JSONDecodeError, OSError):
            logger.warning("audit inválido ignorado: %s", f)
    return audits


def load_enabled_sources() -> set[str]:
    """Nomes das fontes habilitadas no sources_config.json (ignora chaves _comment)."""
    try:
        with open(SOURCES_CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
    except (json.JSONDecodeError, OSError):
        return set()
    out = set()
    for name, conf in cfg.get("sources", {}).items():
        if name.startswith("_comment"):
            continue
        if isinstance(conf, dict) and conf.get("enabled"):
            out.add(name)
    return out


# ── Camada 1: tendências de conteúdo (determinístico) ──────────────────
def _all_items(ed: dict) -> list[dict]:
    """main_find + quick_finds de uma edição como lista plana de dicts."""
    items = []
    mf = ed.get("main_find")
    if isinstance(mf, dict):
        items.append(mf)
    items.extend(qf for qf in ed.get("quick_finds", []) if isinstance(qf, dict))
    return items


def aggregate_content(editions: list[dict], enabled_sources: set[str]) -> dict:
    """Agrega sinais de conteúdo ao longo da janela de edições."""
    themes = Counter()
    entities = Counter()
    sources = Counter()
    claim_status = Counter()
    feedback = Counter()                                   # distribuição total fire/solid/meh
    feedback_by_theme: dict[str, list[float]] = defaultdict(list)
    n_rated = 0

    # feedback_score preenchido pelo feedback_join.py é um dict {fire,solid,meh,n,avg}.
    # Mantemos tolerância a um escalar legado (emoji/label) só por robustez.
    fb_map = {"🔥": 2, "fire": 2, "👍": 1, "solid": 1, "up": 1, "😐": 0, "meh": 0}

    for ed in editions:
        for t in ed.get("themes", []) or []:
            themes[t] += 1
        for it in _all_items(ed):
            for e in it.get("entities", []) or []:
                entities[e] += 1
            cs = it.get("claim_status")
            if cs:
                claim_status[cs] += 1
        for s in ed.get("sources_used", []) or []:
            sources[s] += 1

        fb = ed.get("feedback_score")
        ed_avg = None
        if isinstance(fb, dict):
            for k in ("fire", "solid", "meh"):
                if fb.get(k):
                    feedback[k] += fb[k]
            ed_avg = fb.get("avg")
        elif fb not in (None, ""):
            label = str(fb).lower()
            feedback[label] += 1
            ed_avg = fb_map.get(label)
        if ed_avg is not None:
            n_rated += 1
            for t in ed.get("themes", []) or []:
                feedback_by_theme[t].append(ed_avg)

    # Repetição entre edições: sobreposição de entidades (≥2) entre pares de edições.
    # Reaproveita a heurística da memória editorial (check_repetition usa o mesmo limiar).
    repeats = []
    seen: list[tuple[str, set]] = []
    for ed in editions:
        ed_ents = set()
        for it in _all_items(ed):
            ed_ents |= {e.lower() for e in (it.get("entities") or [])}
        label = f"ed.{ed.get('edition', '?')} ({ed.get('date', '?')})"
        for prev_label, prev_ents in seen:
            shared = ed_ents & prev_ents
            if len(shared) >= 2:
                repeats.append({"a": prev_label, "b": label, "shared": sorted(shared)})
        seen.append((label, ed_ents))

    # Fontes configuradas que nunca foram selecionadas na janela (sinal de ruído/desperdício).
    never_used = sorted(enabled_sources - set(sources)) if enabled_sources else []

    # Mix epistêmico em %
    total_cs = sum(claim_status.values())
    epistemic_pct = (
        {k: round(100 * v / total_cs) for k, v in claim_status.items()} if total_cs else {}
    )

    return {
        "n_editions": len(editions),
        "date_range": (
            (editions[0].get("date", "?"), editions[-1].get("date", "?")) if editions else (None, None)
        ),
        "themes": themes,
        "entities": entities,
        "sources": sources,
        "claim_status": claim_status,
        "epistemic_pct": epistemic_pct,
        "feedback": feedback,
        "n_rated": n_rated,
        "feedback_by_theme": {
            t: round(sum(v) / len(v), 2) for t, v in feedback_by_theme.items() if v
        },
        "repeats": repeats,
        "never_used_sources": never_used,
        "n_enabled_sources": len(enabled_sources),
    }


# ── Camada 2: scorecard de qualidade (consome audits) ──────────────────
# (campo, label curto) — derivado de AUDIT_DIMENSIONS (audit_agent.py), a fonte única
# do schema do AuditReport. Sem isso, uma dimensão nova no audit_agent não apareceria
# aqui até alguém lembrar de atualizar esta lista manualmente.
_DIMS = [(key, short) for key, _long, short in AUDIT_DIMENSIONS]


def aggregate_quality(audits: dict[str, dict]) -> dict:
    """Agrega os audits por edição em médias por dimensão, tendência e padrões recorrentes."""
    if not audits:
        return {"n": 0}

    by_edition = sorted(audits.items())  # [(edition, audit), ...]
    dim_scores: dict[str, list[int]] = defaultdict(list)
    overall = []
    fn_by_source = Counter()           # false negatives recorrentes por fonte
    hypotheses = Counter()             # hipóteses de prompt recorrentes (texto curto)

    for _, a in by_edition:
        overall.append(a.get("overall_score", 0))
        for key, _label in _DIMS:
            d = a.get(key) or {}
            if isinstance(d, dict) and isinstance(d.get("score"), int):
                dim_scores[key].append(d["score"])
        for fn in a.get("false_negatives", []) or []:
            src = (fn.get("source") or "?").strip()
            fn_by_source[src] += 1
        for ph in a.get("prompt_hypotheses", []) or []:
            h = (ph.get("hypothesis") or "").strip()
            if h:
                # normaliza pra agrupar hipóteses parecidas (primeiras ~12 palavras)
                hypotheses[" ".join(h.split()[:12])] += 1

    dim_avg = {
        key: round(sum(v) / len(v), 2) for key, v in dim_scores.items() if v
    }

    # Tendência simples: média da 1ª metade vs 2ª metade das edições auditadas.
    trend = None
    if len(overall) >= 4:
        mid = len(overall) // 2
        first = sum(overall[:mid]) / mid
        second = sum(overall[mid:]) / (len(overall) - mid)
        delta = round(second - first, 2)
        trend = {"first": round(first, 2), "second": round(second, 2), "delta": delta}

    return {
        "n": len(by_edition),
        "by_edition": by_edition,
        "dim_avg": dim_avg,
        "overall_avg": round(sum(overall) / len(overall), 2) if overall else None,
        "trend": trend,
        "fn_by_source": fn_by_source,
        "hypotheses": hypotheses,
    }


# ── Camada 3a: insights determinísticos ────────────────────────────────
def deterministic_insights(content: dict, quality: dict) -> list[str]:
    """Regras simples sobre as camadas 1+2 → bullets de 'como melhorar'.

    Conservador de propósito: só dispara quando o sinal é claro o bastante pra
    virar uma recomendação. Sem dado suficiente, devolve menos (não inventa)."""
    out: list[str] = []
    n = content["n_editions"]

    # Concentração temática
    if n >= 5 and content["themes"]:
        top_theme, cnt = content["themes"].most_common(1)[0]
        if cnt / n >= 0.5:
            out.append(
                f"**Concentração temática:** «{top_theme}» aparece em {cnt}/{n} edições "
                f"({round(100*cnt/n)}%). Risco de monotonia — considere ampliar ângulos ou rebalancear fontes."
            )

    # Fontes que nunca contribuem (responde direto o ROADMAP P2)
    nu = content["never_used_sources"]
    if nu and content["n_enabled_sources"]:
        out.append(
            f"**Fontes ociosas:** {len(nu)} de {content['n_enabled_sources']} fontes habilitadas "
            f"nunca foram selecionadas na janela ({', '.join(nu[:8])}{'…' if len(nu) > 8 else ''}). "
            f"Avalie se geram ruído no pre-filter ou se o peso precisa de ajuste."
        )

    # Mix epistêmico desequilibrado
    ep = content["epistemic_pct"]
    if ep.get("especulativo", 0) >= 50:
        out.append(
            f"**Excesso de especulação:** {ep['especulativo']}% dos itens são `especulativo`. "
            f"Muito rumor/'may' dilui a confiabilidade — priorize itens `confirmado` no ranking."
        )

    # Repetição entre edições
    if content["repeats"]:
        out.append(
            f"**Repetição entre edições:** {len(content['repeats'])} par(es) de edições com sobreposição "
            f"≥2 entidades. A memória editorial barra quick_finds, mas main_finds repetidos só são logados — "
            f"vale revisar se a regra precisa endurecer."
        )

    # Correlação feedback × tema (quando há feedback preenchido)
    fbt = content["feedback_by_theme"]
    if fbt:
        best = max(fbt.items(), key=lambda kv: kv[1])
        worst = min(fbt.items(), key=lambda kv: kv[1])
        if best[1] - worst[1] >= 1:
            out.append(
                f"**Feedback × tema:** «{best[0]}» tem a melhor média ({best[1]}) e «{worst[0]}» a pior "
                f"({worst[1]}). Sinal pra dobrar no que engaja e revisar o que não pega."
            )
    elif content["feedback"]:
        out.append(
            "**Feedback sem tema:** há ratings coletados mas sem correlação por tema computável "
            "(temas ausentes ou feedback_score em formato inesperado)."
        )

    # Camada de qualidade
    q = quality
    if q.get("n"):
        if q.get("trend") and q["trend"]["delta"] <= -0.5:
            out.append(
                f"**Qualidade caindo:** overall foi de {q['trend']['first']} → {q['trend']['second']} "
                f"(Δ {q['trend']['delta']}) entre a 1ª e a 2ª metade das edições auditadas. Investigar regressão."
            )
        # Dimensão mais fraca
        if q.get("dim_avg"):
            weak_key = min(q["dim_avg"], key=q["dim_avg"].get)
            weak_label = dict(_DIMS)[weak_key]
            if q["dim_avg"][weak_key] <= 3.5:
                out.append(
                    f"**Dimensão mais fraca:** «{weak_label}» tem média {q['dim_avg'][weak_key]}/5 — "
                    f"o ponto de maior alavancagem pra subir a qualidade geral."
                )
        # False negatives recorrentes por fonte
        if q.get("fn_by_source"):
            src, c = q["fn_by_source"].most_common(1)[0]
            if c >= 2:
                out.append(
                    f"**Cego recorrente:** «{src}» é a fonte mais frequente em false negatives ({c}×). "
                    f"A AYA pode estar subestimando essa fonte sistematicamente."
                )
        # Hipóteses de prompt recorrentes
        if q.get("hypotheses"):
            h, c = q["hypotheses"].most_common(1)[0]
            if c >= 2:
                out.append(
                    f"**Hipótese de prompt recorrente ({c}×):** “{h}…” — candidata forte a virar fix de prompt."
                )

    if not out:
        out.append(
            "Sem sinais fortes o suficiente pra recomendação determinística nesta janela "
            "(pouco dado acumulado ou métricas saudáveis). Rode novamente com mais edições."
        )
    return out


# ── Camada 3b: síntese via LLM (opcional) ──────────────────────────────
def llm_insights(content: dict, quality: dict) -> str | None:
    """Passa as agregações pro DeepSeek e pede recomendações priorizadas.

    Retorna None se não há chave ou se a chamada falhar — o relatório segue
    com a camada determinística."""
    if not DEEPSEEK_API_KEY:
        logger.info("DEEPSEEK_API_KEY ausente — pulando síntese LLM.")
        return None
    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai SDK ausente — pulando síntese LLM.")
        return None

    # Compacta as agregações pra um payload enxuto (sem despejar tudo).
    payload = {
        "n_editions": content["n_editions"],
        "top_themes": content["themes"].most_common(8),
        "top_entities": content["entities"].most_common(12),
        "source_distribution": content["sources"].most_common(),
        "never_used_sources": content["never_used_sources"],
        "epistemic_pct": content["epistemic_pct"],
        "feedback_distribution": dict(content["feedback"]),
        "feedback_by_theme": content["feedback_by_theme"],
        "n_repeats": len(content["repeats"]),
        "quality_dim_avg": quality.get("dim_avg", {}),
        "quality_overall_avg": quality.get("overall_avg"),
        "quality_trend": quality.get("trend"),
        "false_negatives_by_source": dict(quality.get("fn_by_source", Counter())),
        "recurring_prompt_hypotheses": dict(quality.get("hypotheses", Counter())),
    }

    system = (
        "Você é o editor-chefe da AYA, uma newsletter diária de IA. Recebe estatísticas "
        "agregadas de várias edições e produz um diagnóstico editorial. Seja específico e "
        "acionável: cada recomendação deve apontar O QUE mudar (prompt, fontes, pesos, regra "
        "de memória) e POR QUÊ, ancorado nos números. Não invente dados além dos fornecidos. "
        "Não elogie por elogiar. Máximo 5 recomendações, priorizadas por impacto."
    )
    user = (
        "Estatísticas agregadas das edições da AYA (JSON):\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2, default=str)
        + "\n\nProduza:\n"
        "1. Um diagnóstico de 2-3 frases (o quadro geral).\n"
        "2. Até 5 recomendações priorizadas (P0/P1/P2), cada uma com a alavanca concreta.\n"
        "Responda em Markdown, sem preâmbulo."
    )

    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
        logger.info("Chamando DeepSeek para síntese de insights…")
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.3,
            max_tokens=1500,
            extra_body=DEEPSEEK_EXTRA_BODY,
        )
        return (resp.choices[0].message.content or "").strip() or None
    except Exception as e:  # noqa: BLE001 — síntese é best-effort, nunca quebra o relatório
        logger.warning("Síntese LLM falhou (%s) — seguindo só com a camada determinística.", e)
        return None


# ── Render do Markdown ─────────────────────────────────────────────────
def _bar(count: int, maxc: int, width: int = 16) -> str:
    if not maxc:
        return ""
    filled = round(width * count / maxc)
    return "█" * filled + "·" * (width - filled)


def build_markdown(content: dict, quality: dict, det_insights: list[str], llm_text: str | None) -> str:
    now = datetime.now(_BRT)
    d0, d1 = content["date_range"]
    L: list[str] = [
        "# AYA — Relatório de Conteúdo",
        "",
        f"**Gerado:** {now.strftime('%Y-%m-%d %H:%M')} BRT  ",
        f"**Janela:** {content['n_editions']} edições"
        + (f" ({d0} → {d1})" if d0 else ""),
        "",
        "> Avaliação editorial da AYA *através das edições*: o que cobre, com qual "
        "diversidade, como o feedback responde e como a qualidade evolui.",
        "",
        "---",
        "",
        "## 1. Tendências de Conteúdo",
        "",
    ]

    # Temas
    if content["themes"]:
        maxc = content["themes"].most_common(1)[0][1]
        L += ["### Temas recorrentes", "", "| Tema | Edições | |", "|---|---|---|"]
        for t, c in content["themes"].most_common(10):
            L.append(f"| {t} | {c} | `{_bar(c, maxc)}` |")
        L.append("")

    # Entidades
    if content["entities"]:
        L += ["### Entidades mais citadas", "",
              "`" + "` · `".join(f"{e} ({c})" for e, c in content["entities"].most_common(12)) + "`",
              ""]

    # Fontes
    if content["sources"]:
        maxc = content["sources"].most_common(1)[0][1]
        L += ["### Distribuição de fontes", "", "| Fonte | Usos | |", "|---|---|---|"]
        for s, c in content["sources"].most_common():
            L.append(f"| {s} | {c} | `{_bar(c, maxc)}` |")
        L.append("")
    if content["never_used_sources"]:
        L += [
            f"**Fontes habilitadas nunca selecionadas ({len(content['never_used_sources'])}/"
            f"{content['n_enabled_sources']}):** "
            + ", ".join(f"`{s}`" for s in content["never_used_sources"]),
            "",
        ]

    # Mix epistêmico
    if content["epistemic_pct"]:
        L += ["### Mix epistêmico (claim_status)", "",
              " · ".join(f"**{k}** {v}%" for k, v in content["epistemic_pct"].items()), ""]

    # Feedback
    if content["feedback"]:
        emoji = {"fire": "🔥", "solid": "👍", "meh": "😐"}
        dist = " · ".join(f"{emoji.get(k, k)} {v}" for k, v in content["feedback"].items())
        L += ["### Feedback coletado", "",
              f"{dist}  ({content.get('n_rated', 0)} edições com rating)", ""]
        if content["feedback_by_theme"]:
            L += ["", "_Média de feedback por tema:_", ""]
            for t, avg in sorted(content["feedback_by_theme"].items(), key=lambda kv: -kv[1]):
                L.append(f"- {t}: **{avg}**")
            L.append("")
    else:
        L += ["_Feedback ainda não preenchido nas edições (pendente do loop 🔥/👍/😐)._", ""]

    # Repetição
    if content["repeats"]:
        L += ["### Repetição entre edições", "",
              f"{len(content['repeats'])} par(es) com sobreposição ≥2 entidades:", ""]
        for r in content["repeats"][:8]:
            L.append(f"- {r['a']} ↔ {r['b']} — compartilham: {', '.join(r['shared'])}")
        L.append("")

    # ── Qualidade ──
    L += ["---", "", "## 2. Scorecard de Qualidade", ""]
    if not quality.get("n"):
        L += [
            "_Nenhum audit encontrado em `debug/`._ Rode o audit_agent primeiro para popular esta seção:",
            "",
            "```bash",
            "python audit_agent.py --all      # precisa de DEBUG_SAVE=true no pipeline",
            "```",
            "",
        ]
    else:
        # Tabela por edição
        L += ["### Por edição", "",
              "| Edição | Overall | " + " | ".join(lbl for _, lbl in _DIMS) + " |",
              "|---|---|" + "---|" * len(_DIMS)]
        for ed, a in quality["by_edition"]:
            cells = []
            for key, _ in _DIMS:
                d = a.get(key) or {}
                cells.append(str(d.get("score", "—")))
            L.append(f"| #{ed} | {a.get('overall_score', '—')}/5 | " + " | ".join(cells) + " |")
        L.append("")

        # Médias
        if quality["dim_avg"]:
            L += ["### Médias por dimensão", "",
                  " · ".join(f"**{dict(_DIMS)[k]}** {v}/5" for k, v in quality["dim_avg"].items()),
                  f"  \n**Overall médio:** {quality['overall_avg']}/5", ""]
        if quality.get("trend"):
            t = quality["trend"]
            arrow = "↑" if t["delta"] > 0 else ("↓" if t["delta"] < 0 else "→")
            L += [f"**Tendência:** {t['first']} → {t['second']} ({arrow} Δ {t['delta']})", ""]

        # Padrões recorrentes
        if quality["fn_by_source"]:
            L += ["### False negatives recorrentes (por fonte)", ""]
            for s, c in quality["fn_by_source"].most_common(8):
                L.append(f"- {s}: {c}×")
            L.append("")
        if quality["hypotheses"]:
            L += ["### Hipóteses de prompt recorrentes", ""]
            for h, c in quality["hypotheses"].most_common(6):
                L.append(f"- ({c}×) {h}…")
            L.append("")

    # ── Insights ──
    L += ["---", "", "## 3. Insights — Como Melhorar a AYA", "",
          "### Diagnóstico determinístico", ""]
    for b in det_insights:
        L.append(f"- {b}")
    L.append("")
    if llm_text:
        L += ["### Síntese editorial (DeepSeek)", "", llm_text, ""]

    L += ["---", "", "*Gerado por `content_report.py` — Daily Scout Content Report v1.0*"]
    return "\n".join(L)


# ── Console summary ────────────────────────────────────────────────────
def print_summary(content: dict, quality: dict, det_insights: list[str], path: str):
    print(f"\n{'='*60}")
    print(f"AYA — CONTENT REPORT  ({content['n_editions']} edições)")
    print(f"{'='*60}")
    if content["themes"]:
        print("Top temas:   " + ", ".join(f"{t}×{c}" for t, c in content["themes"].most_common(3)))
    if content["sources"]:
        print("Top fontes:  " + ", ".join(f"{s}×{c}" for s, c in content["sources"].most_common(3)))
    if content["never_used_sources"]:
        print(f"Fontes ociosas: {len(content['never_used_sources'])}/{content['n_enabled_sources']}")
    if quality.get("n"):
        print(f"Qualidade:   overall médio {quality['overall_avg']}/5  ({quality['n']} audits)")
    print(f"\nInsights ({len(det_insights)}):")
    for b in det_insights:
        # tira markdown bold do console
        print("  • " + b.replace("**", ""))
    print(f"\n→ Relatório salvo em: {path}")
    print(f"{'='*60}\n")


# ── Main ───────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="AYA Content Report — avaliação editorial através das edições.")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--last", type=int, default=14, help="Quantas edições recentes analisar (default: 14)")
    g.add_argument("--all", action="store_true", help="Analisar todas as edições disponíveis")
    p.add_argument("--editions-file", default=EDITIONS_PATH, help="Caminho do editions.jsonl (default: memory/editions.jsonl)")
    p.add_argument("--no-llm", action="store_true", help="Pular a síntese via DeepSeek (só camadas determinísticas)")
    p.add_argument("--quiet", action="store_true", help="Não imprimir resumo no console")
    args = p.parse_args()

    last = None if args.all else args.last
    editions = load_editions(args.editions_file, last)

    if not editions:
        logger.error("Nenhuma edição encontrada em: %s", args.editions_file)
        logger.error("A memória editorial popula esse arquivo conforme o pipeline roda em produção.")
        logger.error("Para testar agora, use: --editions-file tests/fixtures/sample_editions.jsonl")
        raise SystemExit(1)

    logger.info("Analisando %d edições…", len(editions))
    enabled_sources = load_enabled_sources()
    content = aggregate_content(editions, enabled_sources)
    audits = load_audits(editions)
    quality = aggregate_quality(audits)
    if audits:
        logger.info("Audits encontrados para %d/%d edições.", len(audits), len(editions))
    else:
        logger.info("Nenhum audit em debug/ — scorecard de qualidade ficará vazio (rode audit_agent).")

    det = deterministic_insights(content, quality)
    llm_text = None if args.no_llm else llm_insights(content, quality)

    md = build_markdown(content, quality, det, llm_text)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    fname = f"content_report_{datetime.now(_BRT).strftime('%Y%m%d')}.md"
    out_path = os.path.join(REPORTS_DIR, fname)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    logger.info("Relatório salvo: %s", out_path)

    if not args.quiet:
        print_summary(content, quality, det, out_path)


if __name__ == "__main__":
    main()
