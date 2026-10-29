"""
Daily Scout — Dashboard interno v2.0

Painel operacional/editorial pra uso interno (Isis). NÃO é publicado no site —
gera um HTML único e self-contained em output/dashboard.html (fora do git,
já ignorado). Reaproveita as camadas determinísticas do content_report.py
(aggregate_content, aggregate_quality, deterministic_insights) em vez de
duplicar a lógica de agregação — este arquivo só cuida da renderização.

Organizado por "job to be done", não por tipo de dado:
  ① Ação agora   — insights + recorrências com evidência (edições) e severidade
  ② Tendência     — score de qualidade ao longo do tempo (não só um antes/depois)
  ③ Conteúdo      — temas/entidades/fontes/epistêmico/feedback
  ④ Operação      — cadência de publicação + saúde da suíte de testes
  ⑤ Log           — tabelas grandes de referência, colapsadas por padrão

Cor nas barras é sempre amarrada a um limiar que já existe em
content_report.py::deterministic_insights — nunca um threshold novo inventado
só pra visual, senão a cor vira ruído em vez de sinal.

Uso:
  python dashboard.py                      # últimas 30 edições, abre no navegador
  python dashboard.py --last 60
  python dashboard.py --all
  python dashboard.py --no-open            # só gera o arquivo, sem abrir
  python dashboard.py --editions-file tests/fixtures/sample_editions.jsonl
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import webbrowser
from datetime import datetime

from content_report import (
    EDITIONS_PATH,
    _DIMS,
    aggregate_content,
    aggregate_quality,
    deterministic_insights,
    load_audits,
    load_editions,
    load_enabled_sources,
)
from arch_stats import (
    COV_BAD,
    COV_WARN,
    FN_CC_BAD,
    FN_CC_WARN,
    FN_PER_ITEM_BAD,
    INSTABILITY_FRAGILE,
    WORKFLOW_OK_PCT,
    aggregate_architecture,
    aggregate_workflows,
    load_actions_runs,
    source_performance,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("dashboard")

ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(ROOT, "output", "dashboard.html")
TEST_RUNS_PATH = os.path.join(ROOT, "ci", "test_runs.jsonl")

FEEDBACK_EMOJI = {"fire": "🔥", "solid": "👍", "meh": "😐"}

# Limiares reaproveitados de content_report.py::deterministic_insights — a cor
# de uma barra só existe se corresponder a uma regra que já dispara um insight.
DIM_WEAK_THRESHOLD = 3.5          # dimensão <= isso é "ponto fraco"
CONCENTRATION_THRESHOLD = 0.5     # tema em >=50% das edições é "monotonia"
ESPECULATIVO_THRESHOLD = 50       # >=50% especulativo dilui confiabilidade


def _esc(s) -> str:
    return html.escape(str(s), quote=True)


def _bar(label: str, value: float, max_value: float, display: str | None = None, bad: bool = False) -> str:
    pct = max(0, min(100, round(100 * value / max_value))) if max_value else 0
    disp = display if display is not None else str(value)
    fill_class = "bar-fill bad" if bad else "bar-fill"
    return (
        '<div class="bar-row">'
        f'<span class="bar-label">{_esc(label)}</span>'
        f'<div class="bar-track"><div class="{fill_class}" style="width:{pct}%"></div></div>'
        f'<span class="bar-count">{_esc(disp)}</span>'
        "</div>"
    )


def render_counter_bars(counter, top_n: int = 10, warn_share_of: int | None = None) -> str:
    """warn_share_of: se passado, marca a barra do topo como 'bad' quando ela
    sozinha responde por >=CONCENTRATION_THRESHOLD do total — mesma regra de
    'concentração temática' do deterministic_insights."""
    if not counter:
        return "<p class='empty'>sem dados</p>"
    items = counter.most_common(top_n)
    maxc = items[0][1]
    bars = []
    for i, (label, c) in enumerate(items):
        bad = bool(i == 0 and warn_share_of and c / warn_share_of >= CONCENTRATION_THRESHOLD)
        bars.append(_bar(label, c, maxc, display=str(c), bad=bad))
    return "".join(bars)


def render_dim_bars(dim_avg: dict) -> str:
    if not dim_avg:
        return "<p class='empty'>sem audits ainda — rode audit_agent.py</p>"
    rows = []
    for key, label in _DIMS:
        if key in dim_avg:
            avg = dim_avg[key]
            rows.append(_bar(label, avg, 5, display=f"{avg}/5", bad=avg <= DIM_WEAK_THRESHOLD))
    return "".join(rows)


def render_epistemic_bars(epistemic_pct: dict) -> str:
    if not epistemic_pct:
        return "<p class='empty'>sem claim_status registrado</p>"
    rows = [
        _bar(label, pct, 100, display=f"{pct}%",
             bad=(label == "especulativo" and pct >= ESPECULATIVO_THRESHOLD))
        for label, pct in sorted(epistemic_pct.items(), key=lambda kv: -kv[1])
    ]
    return "".join(rows)


def render_feedback_bars(feedback: dict) -> str:
    if not feedback:
        return "<p class='empty'>sem ratings ainda (feedback_join.py não rodou ou lista vazia)</p>"
    maxc = max(feedback.values())
    rows = [
        _bar(f"{FEEDBACK_EMOJI.get(k, k)} {k}", v, maxc, display=str(v))
        for k, v in feedback.items()
    ]
    return "".join(rows)


def compute_cadence(editions: list[dict]) -> dict:
    """Gaps entre datas consecutivas — proxy de consistência de publicação
    (sem depender de dado externo do GitHub Actions)."""
    parsed = []
    for e in editions:
        d = e.get("date")
        if not d:
            continue
        try:
            parsed.append(datetime.strptime(d, "%Y-%m-%d"))
        except ValueError:
            continue
    parsed.sort()
    gaps = [
        {"from": a.strftime("%Y-%m-%d"), "to": b.strftime("%Y-%m-%d"), "days": (b - a).days}
        for a, b in zip(parsed, parsed[1:])
        if (b - a).days > 1
    ]
    span_days = (parsed[-1] - parsed[0]).days + 1 if parsed else 0
    return {"n_dates": len(parsed), "span_days": span_days, "gaps": gaps}


def render_cadence(cadence: dict) -> str:
    if not cadence["n_dates"]:
        return "<p class='empty'>sem datas</p>"
    pct = round(100 * cadence["n_dates"] / cadence["span_days"]) if cadence["span_days"] else 0
    out = [
        f"<p><strong>{cadence['n_dates']}</strong> edições em "
        f"<strong>{cadence['span_days']}</strong> dias de janela ({pct}% de cobertura diária).</p>"
    ]
    if cadence["gaps"]:
        out.append(f"<p class='warn'>{len(cadence['gaps'])} lacuna(s) detectada(s):</p><ul>")
        for g in cadence["gaps"]:
            out.append(f"<li>{g['from']} → {g['to']} ({g['days']} dias sem edição registrada)</li>")
        out.append("</ul>")
    else:
        out.append("<p class='ok'>Nenhuma lacuna — publicação diária consistente na janela.</p>")
    return "".join(out)


def load_test_runs(path: str = TEST_RUNS_PATH, last: int = 20) -> list[dict]:
    """Lê ci/test_runs.jsonl (histórico de execuções do tests.yml). Tolerante
    a arquivo ausente (nenhuma run ainda) ou linha corrompida, igual
    load_editions em content_report.py — nunca quebra o dashboard."""
    if not os.path.exists(path):
        return []
    runs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                runs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return runs[-last:]


def render_ci_health(runs: list[dict]) -> str:
    if not runs:
        return "<p class='empty'>sem runs registradas ainda — tests.yml roda em push/PR/schedule (ver ci/README.md)</p>"

    latest = runs[-1]
    n_failed = sum(1 for r in runs if r.get("conclusion") != "passed")
    summary = (
        f"<p><strong>última run:</strong> {_esc(latest.get('conclusion', '?'))} "
        f"({_esc(latest.get('passed', '?'))}/{_esc(latest.get('total', '?'))} passou, "
        f"{_esc(latest.get('duration_s', '?'))}s, pytest {_esc(latest.get('pytest_version', '?'))}) — "
        f"{n_failed} falha(s) nas últimas {len(runs)} runs.</p>"
    )

    rows = "".join(
        f"<tr><td>{_esc(r.get('date', '?')[:16].replace('T', ' '))}</td>"
        f"<td>{_esc(r.get('trigger', '?'))}</td>"
        f"<td class='{'ok' if r.get('conclusion') == 'passed' else 'warn'}'>{_esc(r.get('conclusion', '?'))}</td>"
        f"<td>{_esc(r.get('passed', '?'))}/{_esc(r.get('total', '?'))}</td>"
        f"<td>{_esc(r.get('duration_s', '?'))}s</td>"
        f"<td>{_esc(r.get('pytest_version', '?'))}</td>"
        f"<td>{_esc(r.get('commit_sha', '?'))}</td></tr>"
        for r in reversed(runs)
    )
    table = (
        "<table><thead><tr><th>Data (UTC)</th><th>Gatilho</th><th>Resultado</th>"
        f"<th>Passou</th><th>Duração</th><th>pytest</th><th>Commit</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )
    return summary + table


def render_score_trend(by_edition: list) -> str:
    """Sparkline SVG do overall_score por edição auditada — substitui o
    antes/depois grosseiro por uma linha real, ponto a ponto, com um limiar
    tracejado no valor que já define 'dimensão fraca' em outros painéis."""
    if len(by_edition) < 2:
        return "<p class='empty'>precisa de pelo menos 2 edições auditadas pra traçar tendência</p>"

    scores = [a.get("overall_score", 0) for _, a in by_edition]
    n = len(scores)
    w, h, pad = 640, 110, 12

    def x(i):
        return pad + i * (w - 2 * pad) / (n - 1)

    def y(v):
        return pad + (5 - v) * (h - 2 * pad) / 5

    def dot_color(v):
        if v <= 2:
            return "#ff6b6b"
        if v == 3:
            return "#ffb454"
        return "#1FE070"

    points = " ".join(f"{x(i):.1f},{y(s):.1f}" for i, s in enumerate(scores))
    dots = "".join(
        f'<circle cx="{x(i):.1f}" cy="{y(s):.1f}" r="3.2" fill="{dot_color(s)}">'
        f"<title>ed.{_esc(by_edition[i][0])}: {s}/5</title></circle>"
        for i, s in enumerate(scores)
    )
    ref_y = y(DIM_WEAK_THRESHOLD)
    first_ed, last_ed = by_edition[0][0], by_edition[-1][0]

    svg = (
        f'<svg viewBox="0 0 {w} {h}" width="100%" height="{h}" preserveAspectRatio="none">'
        f'<line x1="{pad}" y1="{ref_y:.1f}" x2="{w - pad}" y2="{ref_y:.1f}" '
        f'stroke="#3a4a42" stroke-dasharray="4,4" stroke-width="1"/>'
        f'<polyline points="{points}" fill="none" stroke="#4FAE74" stroke-width="1.5"/>'
        f"{dots}</svg>"
    )
    caption = (
        f"<p class='empty'>ed.{_esc(first_ed)} → ed.{_esc(last_ed)} · linha tracejada = limiar de "
        f"{DIM_WEAK_THRESHOLD} · passe o mouse num ponto pra ver a edição</p>"
    )
    return svg + caption


def render_quality_table(by_edition: list, date_by_edition: dict) -> str:
    if not by_edition:
        return "<p class='empty'>sem audits ainda</p>"
    rows = []
    for edition, audit in reversed(by_edition):  # mais recente primeiro
        date = date_by_edition.get(edition, "?")
        score = audit.get("overall_score", "?")
        summary = (audit.get("top_issues_summary") or "")[:140]
        rows.append(
            f"<tr><td>#{_esc(edition)}</td><td>{_esc(date)}</td>"
            f"<td class='score-cell'>{_esc(score)}/5</td><td>{_esc(summary)}…</td></tr>"
        )
    return (
        "<table><thead><tr><th>Edição</th><th>Data</th><th>Score</th>"
        f"<th>Resumo</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def render_recurring_with_evidence(counter, editions_by_key: dict, col_label: str,
                                    min_count: int = 2, max_ed: int = 6, chronic_at: int = 4) -> str:
    """Como render_recurring_table, mas cada linha mostra EM QUAIS edições
    aconteceu (não só a contagem) e um selo de severidade — 🔴 quando já virou
    padrão crônico (>=chronic_at ocorrências), 🟠 quando é recorrente mas
    ainda recente. Sem isso, 'recorrente' não dizia onde ir investigar."""
    recurring = [(k, c) for k, c in counter.most_common() if c >= min_count]
    if not recurring:
        return f"<p class='empty'>nada recorrente (≥{min_count}×) na janela</p>"
    rows = []
    for k, c in recurring:
        eds = list(dict.fromkeys(editions_by_key.get(k, [])))  # dedup preservando ordem
        shown = ", ".join(f"#{e}" for e in eds[:max_ed])
        if len(eds) > max_ed:
            shown += f" +{len(eds) - max_ed}"
        badge = "🔴" if c >= chronic_at else "🟠"
        rows.append(
            f"<tr><td>{badge}</td><td>{_esc(k)}</td><td>{c}×</td>"
            f"<td class='evidence'>{_esc(shown)}</td></tr>"
        )
    return (
        f"<table><thead><tr><th></th><th>{_esc(col_label)}</th><th>Freq.</th>"
        f"<th>Edições</th></tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def render_repeats(repeats: list, show_last: int = 15) -> str:
    """Em janelas longas isso cresce O(n²) — entidades como 'OpenAI'/'China' aparecem
    quase toda edição, então a lista completa vira ruído. Mostra só os pares mais
    recentes (mais acionáveis pra revisar agora); a nota diz quantos ficaram de fora."""
    if not repeats:
        return "<p class='empty'>nenhuma sobreposição de entidades (≥2) entre edições na janela</p>"
    shown = repeats[-show_last:]
    note = ""
    if len(repeats) > show_last:
        note = f"<p class='empty'>mostrando os {show_last} pares mais recentes de {len(repeats)} no total</p>"
    rows = "".join(
        f"<tr><td>{_esc(r['a'])}</td><td>{_esc(r['b'])}</td><td>{_esc(', '.join(r['shared']))}</td></tr>"
        for r in shown
    )
    return note + f"<table><thead><tr><th>Edição A</th><th>Edição B</th><th>Entidades em comum</th></tr></thead><tbody>{rows}</tbody></table>"


def render_feedback_by_theme(fbt: dict, edge_n: int = 8) -> str:
    """Só os extremos (melhor/pior recepção) — a lista completa costuma ter dezenas
    de temas empatados (N=1 cada) e não cabe render revelar todos com sinal igual."""
    if not fbt:
        return "<p class='empty'>sem correlação feedback × tema computável ainda</p>"
    ordered = sorted(fbt.items(), key=lambda kv: -kv[1])
    if len(ordered) <= edge_n * 2:
        shown = ordered
        note = ""
    else:
        shown = ordered[:edge_n] + ordered[-edge_n:]
        note = (
            f"<p class='empty'>mostrando os {edge_n} melhores e {edge_n} piores de "
            f"{len(ordered)} temas com feedback</p>"
        )
    bars = "".join(_bar(theme, avg, 2, display=str(avg)) for theme, avg in shown)
    return note + bars


# ════════════════════════════════════════════════════════════════════════
# Camada de arquitetura — ⑤ Fontes e ⑥ Arquitetura
#
# Os limiares de cor vêm todos de arch_stats (FN_CC_*, COV_*, WORKFLOW_OK_PCT,
# FN_PER_ITEM_BAD), pelo mesmo motivo que os de conteúdo vêm do
# content_report: cor sem regra atrás vira decoração.
# ════════════════════════════════════════════════════════════════════════

def _cov_cell(pct: float | None) -> str:
    if pct is None:
        return "<td class='empty-cell'>—</td>"
    cls = "bad" if pct <= COV_BAD else ("warn" if pct < COV_WARN else "ok")
    return f"<td class='{cls}'>{pct:.0f}%</td>"


def render_module_risk(modules: list[dict], top_n: int = 14) -> str:
    """Módulos por ordem de atenção. Risco é exposição (tamanho × complexidade ×
    quantos dependem) descontada pela cobertura — ordem de olhar, não nota."""
    core = [m for m in modules if not m["is_script"]][:top_n]
    if not core:
        return "<p class='empty'>nenhum módulo analisado</p>"
    rows = []
    for m in core:
        cc_cls = "bad" if m["max_cc"] >= FN_CC_BAD else ("warn" if m["max_cc"] >= FN_CC_WARN else "")
        rows.append(
            f"<tr><td>{_esc(m['module'])}</td>"
            f"<td>{m['loc']}</td><td>{m['sum_cc']}</td>"
            f"<td class='{cc_cls}'>{m['max_cc']}</td>"
            f"<td>{m['fan_in']}</td><td>{m['fan_out']}</td>"
            f"{_cov_cell(m['coverage_pct'])}"
            f"<td class='score-cell'>{m['risk']}</td></tr>"
        )
    return (
        "<table><thead><tr><th>Módulo</th><th>LOC</th><th>CC</th><th>Pior fn</th>"
        "<th>Dep. de</th><th>Importa</th><th>Cob.</th><th>Risco</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        f"<p class='empty'>Pior fn = complexidade da função mais complexa do módulo "
        f"(🟠 ≥{FN_CC_WARN}, 🔴 ≥{FN_CC_BAD}). Dep. de = quantos módulos importam este.</p>"
    )


def render_hotspots(modules: list[dict], top_n: int = 10) -> str:
    """As funções individuais mais complexas, com arquivo:linha pra ir direto."""
    flat = []
    for m in modules:
        if m["is_script"]:
            continue
        for fn in m["hotspots"]:
            flat.append((m["path"], fn))
    flat.sort(key=lambda t: -t[1]["cc"])
    if not flat:
        return f"<p class='ok'>nenhuma função acima de CC {FN_CC_WARN}</p>"
    rows = "".join(
        f"<tr><td>{'🔴' if fn['cc'] >= FN_CC_BAD else '🟠'}</td>"
        f"<td class='evidence'>{_esc(path)}:{fn['line']}</td>"
        f"<td>{_esc(fn['name'])}</td><td>{fn['cc']}</td>"
        f"<td>{fn['loc']}</td><td>{fn['nesting']}</td></tr>"
        for path, fn in flat[:top_n]
    )
    note = ""
    if len(flat) > top_n:
        note = f"<p class='empty'>mostrando as {top_n} mais complexas de {len(flat)}</p>"
    return (
        "<table><thead><tr><th></th><th>Arquivo</th><th>Função</th><th>CC</th>"
        f"<th>LOC</th><th>Aninh.</th></tr></thead><tbody>{rows}</tbody></table>{note}"
    )


def render_coupling(modules: list[dict], top_n: int = 12) -> str:
    """Quem depende de quem. Instabilidade alta + fan_out alto = quebra quando
    qualquer dependência muda; instabilidade baixa + fan_in alto = caro de mexer."""
    core = [m for m in modules if not m["is_script"] and (m["fan_in"] or m["fan_out"])]
    if not core:
        return "<p class='empty'>sem imports entre módulos</p>"
    core.sort(key=lambda m: -(m["fan_in"] + m["fan_out"]))
    maxv = max(max(m["fan_in"], m["fan_out"]) for m in core) or 1
    rows = []
    for m in core[:top_n]:
        fragile = m["instability"] >= INSTABILITY_FRAGILE and m["fan_out"] >= 3
        left = round(100 * m["fan_in"] / maxv)
        right = round(100 * m["fan_out"] / maxv)
        rows.append(
            "<div class='split-row'>"
            f"<span class='split-in'><span class='split-bar in' style='width:{left}%'></span>"
            f"<span class='split-n'>{m['fan_in']}</span></span>"
            f"<span class='split-label'>{_esc(m['module'])}</span>"
            f"<span class='split-out'><span class='split-n'>{m['fan_out']}</span>"
            f"<span class='split-bar out{' bad' if fragile else ''}' style='width:{right}%'></span></span>"
            "</div>"
        )
    return (
        "<div class='split-head'><span>← dependem dele</span><span>importa →</span></div>"
        + "".join(rows)
        + f"<p class='empty'>🔴 instabilidade ≥{INSTABILITY_FRAGILE} com 3+ dependências — "
          "muda junto com tudo que importa.</p>"
    )


def render_workflow_health(agg: dict) -> str:
    """Saúde dos workflows que você escreveu, do snapshot do Actions."""
    wfs = agg.get("workflows") or []
    if not wfs:
        return (
            "<p class='empty'>sem snapshot do Actions. Gere com:<br>"
            "<code>python scripts/fetch_actions_runs.py</code></p>"
        )
    rows = []
    for w in wfs:
        pct = w["success_pct"]
        cls = "bad" if (pct is not None and pct < WORKFLOW_OK_PCT) else "ok"
        streak_cls = "bad" if w["streak_kind"] == "failure" else ""
        last_cls = "ok" if w["last_conclusion"] == "success" else "bad"
        pct_txt = "—" if pct is None else f"{pct}%"
        med_txt = "—" if w["median_s"] is None else f"{round(w['median_s'])}s"
        streak_txt = f"{w['streak']}× " + ("ok" if w["streak_kind"] == "success" else "falha")
        last_txt = "ok" if w["last_conclusion"] == "success" else "falha"
        rows.append(
            f"<tr><td>{_esc(w['name'][:34])}</td><td>{w['n']}</td>"
            f"<td class='{cls}'>{pct_txt}</td>"
            f"<td>{w['n_failures']}</td><td>{med_txt}</td>"
            f"<td class='{streak_cls}'>{streak_txt}</td>"
            f"<td class='{last_cls}'>{last_txt}</td></tr>"
        )
    rng = agg.get("range")
    note = (f"<p class='empty'>{agg['n_runs']} runs · {rng[0]} → {rng[1]} · "
            f"vermelho = sucesso abaixo de {WORKFLOW_OK_PCT}%. Workflows do próprio "
            "GitHub (pages, dependabot) ficam fora.</p>") if rng else ""
    return (
        "<table><thead><tr><th>Workflow</th><th>Runs</th><th>Sucesso</th><th>Falhas</th>"
        "<th>Mediana</th><th>Sequência</th><th>Último</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>{note}"
    )


def render_source_performance(rows: list[dict]) -> str:
    """Contribuição real contra cegueira do judge, por fonte."""
    if not rows:
        return "<p class='empty'>sem dados de fonte</p>"
    n_used = rows[0].get("_n_with_used") or 0
    n_item = rows[0].get("_n_item_window") or 0
    out = []
    for r in rows:
        fpi = r["fn_per_item"]
        fpi_cls = "bad" if (fpi is not None and fpi >= FN_PER_ITEM_BAD) else ""
        badge = "🔴" if r["idle"] else ("🟠" if fpi_cls else "")
        out.append(
            f"<tr><td>{badge}</td><td>{_esc(r['source'])}</td>"
            f"<td>{'—' if r['weight'] is None else r['weight']}</td>"
            f"<td>{r['used_count']}</td><td>{r['used_pct']}%</td>"
            f"<td>{r['main_find']}</td><td>{r['quick_finds']}</td>"
            f"<td>{r['false_negatives']}</td>"
            f"<td class='{fpi_cls}'>{'—' if fpi is None else fpi}</td></tr>"
        )
    return (
        "<table><thead><tr><th></th><th>Fonte</th><th>Peso</th><th>Edições</th><th>Uso</th>"
        "<th>Main</th><th>Quick</th><th>FN</th><th>FN/item</th></tr></thead>"
        f"<tbody>{''.join(out)}</tbody></table>"
        f"<p class='empty'>🔴 nunca contribuiu · 🟠 mais de {FN_PER_ITEM_BAD} false negatives "
        f"por item entregue. <strong>Edições</strong> e <strong>Uso</strong> cobrem as "
        f"{n_used} edições com <code>sources_used</code>; <strong>Main</strong> e "
        f"<strong>Quick</strong> só as {n_item} com <code>source</code> por item "
        "(gravado a partir da ed. 198), então não compare as duas janelas.</p>"
    )


def _hint(text: str) -> str:
    return f"<p class='hint'>{text}</p>"


def _stat(n, label: str, hint: str) -> str:
    return (
        f"<div class='stat'><span class='n'>{_esc(n)}</span>"
        f"<span class='l'>{_esc(label)}</span><span class='h'>{hint}</span></div>"
    )


def render_insights(insights: list[str]) -> str:
    items = "".join(f"<li>{_esc(b).replace('**', '')}</li>" for b in insights)
    items = items.replace("**", "")
    return f"<ul class='insights'>{items}</ul>"


CSS = """
:root {
  --bg: #0b0f0d; --panel: #121815; --border: #223028;
  --ink: #eef2ee; --mute: #8a9690; --accent: #1FE070;
  --warn: #ffb454; --ok: #6fd08a; --bad: #ff6b6b;
  font-size: 15px;
}
* { box-sizing: border-box; }
body {
  background: var(--bg); color: var(--ink); margin: 0; padding: 0 24px 80px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif;
  max-width: 980px; margin-inline: auto;
}
h1.page-title { font-size: 1.6rem; margin: 32px 0 4px; }
.section-title {
  font-size: .95rem; color: var(--mute); text-transform: uppercase; letter-spacing: .08em;
  margin: 40px 0 14px; padding-top: 24px; border-top: 1px solid var(--border);
}
.section-title:first-of-type { border-top: none; padding-top: 0; margin-top: 8px; }
h2 { font-size: 1.05rem; color: var(--accent); text-transform: uppercase; letter-spacing: .04em;
     margin: 0 0 14px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
.meta { color: var(--mute); font-size: .85rem; margin-bottom: 20px; }
nav.toc {
  position: sticky; top: 0; background: var(--bg); padding: 12px 0; z-index: 10;
  display: flex; gap: 18px; flex-wrap: wrap; border-bottom: 1px solid var(--border);
}
nav.toc a {
  color: var(--mute); text-decoration: none; font-size: .78rem; text-transform: uppercase;
  letter-spacing: .05em;
}
nav.toc a:hover { color: var(--accent); }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 820px) { .grid { grid-template-columns: 1fr; } }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
         padding: 20px; margin-bottom: 20px; }
.panel.full { grid-column: 1 / -1; }
details.panel { padding: 0; }
details.panel > summary {
  cursor: pointer; padding: 20px; list-style: none; font-size: 1.05rem; color: var(--accent);
  text-transform: uppercase; letter-spacing: .04em;
}
details.panel > summary::-webkit-details-marker { display: none; }
details.panel > summary::before { content: '▸ '; }
details.panel[open] > summary::before { content: '▾ '; }
details.panel > summary::after {
  content: '(clique pra expandir)'; float: right; color: var(--mute); text-transform: none;
  font-size: .75rem; letter-spacing: 0;
}
details.panel[open] > summary::after { content: ''; }
.details-body { padding: 0 20px 20px; }
.stat-row { display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 4px; }
.stat { max-width: 175px; }
.stat .n { font-size: 1.6rem; font-weight: 600; color: var(--accent); display: block; }
.stat .l { font-size: .75rem; color: var(--mute); text-transform: uppercase; letter-spacing: .04em; display: block; margin-top: 2px; }
.stat .h { font-size: .7rem; color: var(--mute); line-height: 1.35; margin-top: 4px; text-transform: none; letter-spacing: 0; display: block; }
.hint { color: var(--mute); font-size: .82rem; line-height: 1.45; margin: -6px 0 14px; }
.bar-row { display: flex; align-items: center; gap: 10px; margin: 7px 0; font-size: .88rem; }
.bar-label { width: 190px; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--ink); }
.bar-track { flex: 1; background: #0e1512; border-radius: 4px; height: 10px; overflow: hidden; }
.bar-fill { background: var(--accent); height: 100%; border-radius: 4px; }
.bar-fill.bad { background: var(--bad); }
.bar-count { width: 48px; text-align: right; color: var(--mute); font-variant-numeric: tabular-nums; }
table { width: 100%; border-collapse: collapse; font-size: .85rem; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }
th { color: var(--mute); font-weight: 500; text-transform: uppercase; font-size: .72rem; letter-spacing: .04em; }
.score-cell { font-variant-numeric: tabular-nums; }
.evidence { color: var(--mute); font-variant-numeric: tabular-nums; }
.empty { color: var(--mute); font-style: italic; font-size: .88rem; }
.warn { color: var(--warn); }
.ok { color: var(--ok); }
ul.insights { padding-left: 20px; margin: 0; }
ul.insights li { margin-bottom: 10px; line-height: 1.45; }
.trend-up { color: var(--ok); } .trend-down { color: var(--bad); }
svg circle { cursor: default; }

/* Acoplamento: barra dupla saindo do nome, fan_in à esquerda e fan_out à direita. */
.split-head { display: flex; justify-content: space-between; color: var(--mute);
              font-size: .78rem; margin-bottom: 6px; }
.split-row { display: grid; grid-template-columns: 1fr minmax(8rem, 11rem) 1fr;
             align-items: center; gap: 8px; margin-bottom: 4px; }
.split-label { text-align: center; font-size: .82rem; overflow: hidden;
               text-overflow: ellipsis; white-space: nowrap; }
.split-in, .split-out { display: flex; align-items: center; gap: 6px; min-width: 0; }
.split-in { justify-content: flex-end; }
.split-bar { height: 9px; border-radius: 3px; display: block; }
.split-bar.in { background: var(--mute); }
.split-bar.out { background: var(--accent); opacity: .75; }
.split-bar.out.bad { background: var(--bad); opacity: 1; }
.split-n { font-size: .75rem; color: var(--mute); font-variant-numeric: tabular-nums;
           min-width: 1.2rem; text-align: center; }

td.empty-cell { color: var(--mute); }
code { background: var(--bg); padding: 1px 4px; border-radius: 3px; font-size: .85em; }
"""


def render_html(content: dict, quality: dict, insights: list[str], cadence: dict, meta: dict,
                 test_runs: list[dict], arch: dict | None = None,
                 workflows: dict | None = None, sources: list[dict] | None = None) -> str:
    date_by_edition = meta["date_by_edition"]
    arch = arch or {}
    workflows = workflows or {}
    sources = sources or []
    modules = arch.get("modules") or []
    trend = quality.get("trend")
    trend_html = ""
    if trend:
        cls = "trend-down" if trend["delta"] < 0 else "trend-up"
        arrow = "↓" if trend["delta"] < 0 else "↑"
        trend_html = (
            f"<p class='{cls}'>{arrow} {trend['first']} → {trend['second']} "
            f"(Δ {trend['delta']:+.2f}) 1ª vs 2ª metade das edições auditadas</p>"
        )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>AYA — Dashboard interno</title>
<style>{CSS}</style>
</head>
<body>
  <h1 class="page-title">AYA — Dashboard interno</h1>
  <p class="meta">
    Janela: {_esc(content['date_range'][0])} → {_esc(content['date_range'][1])} ·
    {content['n_editions']} edições · gerado em {meta['generated_at']} ·
    <strong>uso interno — não publicar</strong>
  </p>

  <nav class="toc">
    <a href="#acao">① Ação agora</a>
    <a href="#tendencia">② Tendência</a>
    <a href="#conteudo">③ Conteúdo</a>
    <a href="#operacao">④ Operação</a>
    <a href="#fontes">⑤ Fontes</a>
    <a href="#arquitetura">⑥ Arquitetura</a>
    <a href="#log">⑦ Log</a>
  </nav>

  <div class="panel full">
    <div class="stat-row">
      {_stat(content['n_editions'], "Edições na janela",
             "Quantas edições publicadas caem no período analisado (memory/editions.jsonl).")}
      {_stat(quality.get('n', 0), "Editions auditadas",
             "Quantas dessas edições já têm audit do audit_agent.py — a auditoria não roda pra todas.")}
      {_stat(quality.get('overall_avg', '—'), "Score médio (0-5)",
             "Média do overall_score dado pelo audit_agent — julgamento de um LLM revisor, não uma nota objetiva.")}
      {_stat(content['n_rated'], "Editions com feedback",
             "Edições com pelo menos 1 rating 🔥/👍/😐 de assinante, puxado via feedback_join.py.")}
      {_stat(f"{len(content['never_used_sources'])}/{content['n_enabled_sources']}", "Fontes ociosas",
             "Fontes habilitadas em sources_config.json que não tiveram nenhum item selecionado nesta janela.")}
    </div>
  </div>

  <h2 id="acao" class="section-title">① Ação agora</h2>

  <div class="panel full">
    <h2>Insights</h2>
    {_hint("Recomendações determinísticas (sem LLM) — regras aplicadas sobre os dados abaixo. "
           "Só aparecem quando o sinal é forte o bastante (content_report.py::deterministic_insights).")}
    {render_insights(insights)}
  </div>

  <div class="grid">
    <div class="panel">
      <h2>Hipóteses de prompt recorrentes</h2>
      {_hint("🔴 já virou padrão crônico (4+ edições) · 🟠 recorrente mas ainda recente (2-3). "
             "A coluna Edições diz exatamente onde ir olhar a evidência.")}
      {render_recurring_with_evidence(quality.get('hypotheses', {}), quality.get('hypothesis_editions', {}), 'Hipótese')}
    </div>
    <div class="panel">
      <h2>False negatives recorrentes por fonte</h2>
      {_hint("Fontes cujos itens bons ficaram de fora da curadoria mais de uma vez — mesma leitura de "
             "severidade: 🔴 crônico, 🟠 recorrente recente.")}
      {render_recurring_with_evidence(quality.get('fn_by_source', {}), quality.get('fn_editions_by_source', {}), 'Fonte')}
    </div>
  </div>

  <h2 id="tendencia" class="section-title">② Tendência de qualidade</h2>

  <div class="panel full">
    <h2>Score por edição</h2>
    {_hint("overall_score do audit_agent ao longo do tempo — verde ≥4, âmbar =3, vermelho ≤2. "
           "A linha tracejada é o mesmo limiar (3.5) que marca 'dimensão fraca' abaixo.")}
    {render_score_trend(quality.get('by_edition', []))}
  </div>

  <div class="panel full">
    <h2>Dimensões</h2>
    {_hint("Média de cada dimensão avaliada pelo audit_agent (0-5): Editorial (alinhamento com critérios "
           "de seleção), Tom (acurácia/anti-hype), Diversidade (fontes e geografia), Intro (abertura da "
           "correspondente), Reasoning (coerência do raciocínio da AYA). Vermelho = média ≤3.5.")}
    {trend_html}
    {render_dim_bars(quality.get('dim_avg', {}))}
  </div>

  <h2 id="conteudo" class="section-title">③ Conteúdo editorial</h2>

  <div class="grid">
    <div class="panel">
      <h2>Temas mais frequentes</h2>
      {_hint("Quantas edições trouxeram cada tema. Vermelho no topo = um único tema domina "
             "≥50% das edições da janela (risco de monotonia).")}
      {render_counter_bars(content['themes'], warn_share_of=content['n_editions'])}
    </div>
    <div class="panel">
      <h2>Entidades mais citadas</h2>
      {_hint("Contagem de menções de cada entidade (empresa, produto, pessoa) nos main_finds e "
             "quick_finds da janela.")}
      {render_counter_bars(content['entities'])}
    </div>
    <div class="panel">
      <h2>Mix de fontes selecionadas</h2>
      {_hint("De onde vêm os itens que a AYA escolheu publicar — não é volume coletado, é o que passou "
             "pela curadoria (sources_used por edição).")}
      {render_counter_bars(content['sources'])}
    </div>
    <div class="panel">
      <h2>Mix epistêmico (claim_status)</h2>
      {_hint("Proporção de itens por grau de certeza. Vermelho = 'especulativo' em ≥50%, o "
             "limiar que dilui confiabilidade editorial.")}
      {render_epistemic_bars(content['epistemic_pct'])}
    </div>
    <div class="panel">
      <h2>Feedback (🔥/👍/😐)</h2>
      {_hint("Distribuição total de ratings dados pelos assinantes no footer do email (Google Sheet → "
             "feedback_join.py).")}
      {render_feedback_bars(content['feedback'])}
    </div>
    <div class="panel">
      <h2>Feedback médio por tema</h2>
      {_hint("Recepção média por tema (fire=2, solid=1, meh=0), só nas edições com rating. Mostra os "
             "extremos porque a maioria dos temas tem poucos ratings (N baixo) pra ser conclusivo.")}
      {render_feedback_by_theme(content['feedback_by_theme'])}
    </div>
  </div>

  <h2 id="operacao" class="section-title">④ Operação</h2>

  <div class="grid">
    <div class="panel">
      <h2>Consistência de publicação</h2>
      {_hint("Lacunas entre datas consecutivas de edição registrada — proxy calculado a partir do "
             "editions.jsonl, não lê o histórico do GitHub Actions diretamente.")}
      {render_cadence(cadence)}
    </div>
    <div class="panel">
      <h2>Saúde de CI (testes)</h2>
      {_hint("Histórico de execuções do tests.yml (ci/test_runs.jsonl) — se a suíte passa, quanto "
             "demora, e com qual versão do pytest.")}
      {render_ci_health(test_runs)}
    </div>
  </div>

  <div class="panel full">
    <h2>Saúde dos workflows</h2>
    {_hint("Todos os runs do GitHub Actions, do snapshot em ci/actions_runs.json. "
           "Um workflow que vive vermelho para de ser sinal — é a diferença entre uma "
           "falha pra investigar e um check que todo mundo aprendeu a ignorar.")}
    {render_workflow_health(workflows)}
  </div>

  <h2 id="fontes" class="section-title">⑤ Performance das fontes</h2>

  <div class="panel full">
    <h2>Contribuição contra cegueira</h2>
    {_hint("Cruza o que cada fonte entregou com as vezes que o judge disse que ela tinha algo "
           "bom que ficou de fora. Uma fonte muito usada E muito apontada é problema de "
           "critério de seleção, não de peso; pouco usada E muito apontada é peso. "
           "Nunca usada e nunca apontada é fetch quebrado ou feed morto.")}
    {render_source_performance(sources)}
  </div>

  <h2 id="arquitetura" class="section-title">⑥ Arquitetura</h2>

  <div class="panel full">
    <div class="stat-row">
      {_stat(arch.get('n_modules', '—'), "Módulos de produção",
             "Módulos .py fora de tests/ e scripts/ — o que roda em produção.")}
      {_stat(arch.get('total_loc', '—'), "Linhas de código",
             "Soma das linhas desses módulos, comentários e brancos incluídos.")}
      {_stat(f"{arch['avg_coverage']}%" if arch.get('avg_coverage') is not None else "—",
             "Cobertura média",
             "Média da cobertura por módulo (pytest --cov --cov-report=json). "
             "'—' = sem coverage.json gerado.")}
      {_stat(len(arch.get('no_coverage') or []), "Módulos em 0%",
             "Módulos que nenhum teste executa — o caso binário, não uma questão de grau.")}
      {_stat(len(arch.get('fragile') or []), "Módulos frágeis",
             f"Instabilidade ≥{INSTABILITY_FRAGILE} com 3+ dependências: mudam junto com "
             "tudo que importam.")}
    </div>
  </div>

  <div class="panel full">
    <h2>Risco por módulo</h2>
    {_hint("Risco = tamanho × complexidade × quantos módulos dependem dele, descontado pela "
           "cobertura. É ordem de atenção, não nota: um módulo grande e complexo mas testado "
           "não é a primeira coisa a mexer; o mesmo módulo sem teste é.")}
    {render_module_risk(modules)}
  </div>

  <div class="grid">
    <div class="panel">
      <h2>Acoplamento</h2>
      {_hint("À esquerda, quantos módulos dependem deste; à direita, quantos ele importa. "
             "Muita gente dependendo dele = caro de mudar. Ele dependendo de muita gente = "
             "quebra fácil.")}
      {render_coupling(modules)}
    </div>
    <div class="panel">
      <h2>Funções mais complexas</h2>
      {_hint(f"Complexidade ciclomática por função: 🟠 ≥{FN_CC_WARN} (limite clássico de "
             f"McCabe, acima disso os caminhos passam do que se testa à mão), 🔴 ≥{FN_CC_BAD}. "
             "Arquivo:linha pra ir direto.")}
      {render_hotspots(modules)}
    </div>
  </div>

  <h2 id="log" class="section-title">⑦ Log / referência</h2>

  <details class="panel full">
    <summary>Scorecard por edição</summary>
    <div class="details-body">
      {_hint("Score geral e resumo dos principais problemas apontados pelo audit_agent, edição por "
             "edição — mais recente primeiro. É log, não conclusão — use a Tendência (②) pra isso.")}
      {render_quality_table(quality.get('by_edition', []), date_by_edition)}
    </div>
  </details>

  <details class="panel full">
    <summary>Repetição entre edições (≥2 entidades em comum)</summary>
    <div class="details-body">
      {_hint("Pares de edições que compartilham 2+ entidades nos itens selecionados. Pode ser cobertura "
             "legítima de um tema em desenvolvimento, ou a memória editorial não barrando o suficiente.")}
      {render_repeats(content['repeats'])}
    </div>
  </details>

</body>
</html>"""


def main():
    p = argparse.ArgumentParser(description="AYA Dashboard — painel interno (não publicado).")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--last", type=int, default=30, help="Quantas edições recentes analisar (default: 30)")
    g.add_argument("--all", action="store_true", help="Analisar todas as edições disponíveis")
    p.add_argument("--editions-file", default=EDITIONS_PATH, help="Caminho do editions.jsonl")
    p.add_argument("--no-open", action="store_true", help="Não abrir no navegador ao terminar")
    args = p.parse_args()

    last = None if args.all else args.last
    editions = load_editions(args.editions_file, last)
    if not editions:
        logger.error("Nenhuma edição encontrada em: %s", args.editions_file)
        raise SystemExit(1)

    logger.info("Analisando %d edições…", len(editions))
    enabled_sources = load_enabled_sources()
    content = aggregate_content(editions, enabled_sources)
    audits = load_audits(editions)
    quality = aggregate_quality(audits)
    cadence = compute_cadence(editions)
    insights = deterministic_insights(content, quality)
    test_runs = load_test_runs()

    # Camada de arquitetura. Tudo local e tolerante a dado ausente: sem
    # coverage.json a coluna de cobertura fica vazia, sem ci/actions_runs.json a
    # seção de workflows diz como gerar. Nenhum dos dois impede o painel.
    arch = aggregate_architecture()
    workflows = aggregate_workflows(load_actions_runs())
    sources = source_performance(editions, audits)
    logger.info("Arquitetura: %d módulos, %d LOC, %d em 0%% de cobertura",
                arch["n_modules"], arch["total_loc"], len(arch["no_coverage"]))

    meta = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "date_by_edition": {e.get("edition"): e.get("date", "?") for e in editions},
    }

    doc = render_html(content, quality, insights, cadence, meta, test_runs,
                      arch=arch, workflows=workflows, sources=sources)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(doc)
    logger.info("Dashboard salvo: %s", OUTPUT_PATH)

    if not args.no_open:
        webbrowser.open(f"file://{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
