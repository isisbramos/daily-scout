"""
Daily Scout — Dashboard interno v1.0

Painel operacional/editorial pra uso interno (Isis). NÃO é publicado no site —
gera um HTML único e self-contained em output/dashboard.html (fora do git,
já ignorado). Reaproveita as camadas determinísticas do content_report.py
(aggregate_content, aggregate_quality, deterministic_insights) em vez de
duplicar a lógica de agregação — este arquivo só cuida da renderização.

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


def _esc(s) -> str:
    return html.escape(str(s), quote=True)


def _bar(label: str, value: float, max_value: float, display: str | None = None) -> str:
    pct = max(0, min(100, round(100 * value / max_value))) if max_value else 0
    disp = display if display is not None else str(value)
    return (
        '<div class="bar-row">'
        f'<span class="bar-label">{_esc(label)}</span>'
        f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>'
        f'<span class="bar-count">{_esc(disp)}</span>'
        "</div>"
    )


def render_counter_bars(counter, top_n: int = 10) -> str:
    if not counter:
        return "<p class='empty'>sem dados</p>"
    items = counter.most_common(top_n)
    maxc = items[0][1]
    return "".join(_bar(label, c, maxc, display=str(c)) for label, c in items)


def render_dim_bars(dim_avg: dict) -> str:
    if not dim_avg:
        return "<p class='empty'>sem audits ainda — rode audit_agent.py</p>"
    rows = []
    for key, label in _DIMS:
        if key in dim_avg:
            rows.append(_bar(label, dim_avg[key], 5, display=f"{dim_avg[key]}/5"))
    return "".join(rows)


def render_epistemic_bars(epistemic_pct: dict) -> str:
    if not epistemic_pct:
        return "<p class='empty'>sem claim_status registrado</p>"
    rows = [
        _bar(label, pct, 100, display=f"{pct}%")
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


def render_recurring_table(counter, col_label: str, min_count: int = 2) -> str:
    recurring = [(k, c) for k, c in counter.most_common() if c >= min_count]
    if not recurring:
        return "<p class='empty'>nada recorrente (≥2×) na janela</p>"
    rows = "".join(f"<tr><td>{_esc(k)}</td><td>{c}×</td></tr>" for k, c in recurring)
    return f"<table><thead><tr><th>{_esc(col_label)}</th><th>Freq.</th></tr></thead><tbody>{rows}</tbody></table>"


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


def _hint(text: str) -> str:
    return f"<p class='hint'>{text}</p>"


def _stat(n, label: str, hint: str) -> str:
    return (
        f"<div class='stat'><span class='n'>{_esc(n)}</span>"
        f"<span class='l'>{_esc(label)}</span><span class='h'>{hint}</span></div>"
    )


def render_insights(insights: list[str]) -> str:
    items = "".join(f"<li>{_esc(b).replace('**', '')}</li>" for b in insights)
    # negrito simples: **texto** -> <strong>
    items = items.replace("**", "")
    return f"<ul class='insights'>{items}</ul>"


CSS = """
:root {
  --bg: #0b0f0d; --panel: #121815; --border: #223028;
  --ink: #eef2ee; --mute: #8a9690; --accent: #1FE070;
  --warn: #ffb454; --ok: #6fd08a;
  font-size: 15px;
}
* { box-sizing: border-box; }
body {
  background: var(--bg); color: var(--ink); margin: 0; padding: 32px 24px 80px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif;
  max-width: 980px; margin-inline: auto;
}
h1 { font-size: 1.6rem; margin-bottom: 4px; }
h2 { font-size: 1.05rem; color: var(--accent); text-transform: uppercase; letter-spacing: .04em;
     margin: 0 0 14px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
.meta { color: var(--mute); font-size: .85rem; margin-bottom: 28px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width: 820px) { .grid { grid-template-columns: 1fr; } }
.panel { background: var(--panel); border: 1px solid var(--border); border-radius: 10px;
         padding: 20px; margin-bottom: 20px; }
.panel.full { grid-column: 1 / -1; }
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
.bar-count { width: 48px; text-align: right; color: var(--mute); font-variant-numeric: tabular-nums; }
table { width: 100%; border-collapse: collapse; font-size: .85rem; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }
th { color: var(--mute); font-weight: 500; text-transform: uppercase; font-size: .72rem; letter-spacing: .04em; }
.score-cell { font-variant-numeric: tabular-nums; }
.empty { color: var(--mute); font-style: italic; font-size: .88rem; }
.warn { color: var(--warn); }
.ok { color: var(--ok); }
ul.insights { padding-left: 20px; margin: 0; }
ul.insights li { margin-bottom: 10px; line-height: 1.45; }
.trend-up { color: var(--ok); } .trend-down { color: #ff6b6b; }
"""


def render_html(content: dict, quality: dict, insights: list[str], cadence: dict, meta: dict, test_runs: list[dict]) -> str:
    date_by_edition = meta["date_by_edition"]
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
  <h1>AYA — Dashboard interno</h1>
  <p class="meta">
    Janela: {_esc(content['date_range'][0])} → {_esc(content['date_range'][1])} ·
    {content['n_editions']} edições · gerado em {meta['generated_at']} ·
    <strong>uso interno — não publicar</strong>
  </p>

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

  <div class="panel full">
    <h2>Insights ({len(insights)})</h2>
    {_hint("Recomendações determinísticas (sem LLM) — regras aplicadas sobre os dados abaixo. "
           "Só aparecem quando o sinal é forte o bastante (content_report.py::deterministic_insights).")}
    {render_insights(insights)}
  </div>

  <div class="panel full">
    <h2>Consistência de publicação</h2>
    {_hint("Lacunas entre datas consecutivas de edição registrada. É um proxy calculado a partir do "
           "editions.jsonl — não lê o histórico do GitHub Actions diretamente.")}
    {render_cadence(cadence)}
  </div>

  <div class="panel full">
    <h2>Saúde de CI (testes)</h2>
    {_hint("Histórico de execuções do tests.yml (ci/test_runs.jsonl) — se a suíte passa, quanto demora, "
           "e com qual versão do pytest. Engenharia, não editorial: útil pra notar um bump de dependência "
           "que mudou tempo de execução ou passou a falhar.")}
    {render_ci_health(test_runs)}
  </div>

  <div class="grid">
    <div class="panel">
      <h2>Temas mais frequentes</h2>
      {_hint("Quantas edições trouxeram cada tema (campo themes da curadoria). Concentração alta demais "
             "num único tema é sinal de monotonia editorial.")}
      {render_counter_bars(content['themes'])}
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
      {_hint("Proporção de itens por grau de certeza: confirmado / especulativo / em_andamento. Muito "
             "'especulativo' dilui a confiabilidade editorial.")}
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

  <div class="panel full">
    <h2>Scorecard de qualidade — dimensões</h2>
    {_hint("Média de cada dimensão avaliada pelo audit_agent (0-5): Editorial (alinhamento com critérios "
           "de seleção), Tom (acurácia/anti-hype), Diversidade (fontes e geografia), Intro (abertura da "
           "correspondente), Reasoning (coerência do raciocínio da AYA). A linha abaixo compara a 1ª "
           "metade com a 2ª metade das edições auditadas na janela.")}
    {trend_html}
    {render_dim_bars(quality.get('dim_avg', {}))}
  </div>

  <div class="panel full">
    <h2>Scorecard por edição</h2>
    {_hint("Score geral e resumo dos principais problemas apontados pelo audit_agent, edição por edição "
           "— mais recente primeiro.")}
    {render_quality_table(quality.get('by_edition', []), date_by_edition)}
  </div>

  <div class="grid">
    <div class="panel">
      <h2>False negatives recorrentes por fonte</h2>
      {_hint("Fontes cujos itens bons ficaram de fora da curadoria mais de uma vez, segundo o audit_agent "
             "— sinaliza fonte sistematicamente subestimada.")}
      {render_recurring_table(quality.get('fn_by_source', {}), 'Fonte')}
    </div>
    <div class="panel">
      <h2>Hipóteses de prompt recorrentes</h2>
      {_hint("Hipóteses do audit_agent sobre por que a curadoria errou, agrupadas quando o texto se "
             "repete — 2+ ocorrências é candidata forte a virar ajuste de prompt.")}
      {render_recurring_table(quality.get('hypotheses', {}), 'Hipótese')}
    </div>
  </div>

  <div class="panel full">
    <h2>Repetição entre edições (≥2 entidades em comum)</h2>
    {_hint("Pares de edições que compartilham 2+ entidades nos itens selecionados. Pode ser cobertura "
           "legítima de um tema em desenvolvimento, ou sinal de que a memória editorial não está "
           "barrando repetição o suficiente.")}
    {render_repeats(content['repeats'])}
  </div>

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

    meta = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "date_by_edition": {e.get("edition"): e.get("date", "?") for e in editions},
    }

    doc = render_html(content, quality, insights, cadence, meta, test_runs)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(doc)
    logger.info("Dashboard salvo: %s", OUTPUT_PATH)

    if not args.no_open:
        webbrowser.open(f"file://{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
