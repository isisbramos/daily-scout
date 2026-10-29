"""
Testes da camada de arquitetura do dashboard.

O que importa travar aqui não é o número exato de LOC do repo — isso muda todo
commit. É o comportamento das regras que viram decisão: a CC sobe com desvio de
fluxo, o acoplamento aponta pro lado certo, o risco cai quando há cobertura, as
duas janelas de fonte não se misturam, e nada disso quebra quando o dado está
ausente ou corrompido.
"""

from __future__ import annotations

import json
import textwrap

import pytest

import arch_stats
from arch_stats import (
    COV_BAD,
    FN_PER_ITEM_BAD,
    aggregate_architecture,
    aggregate_workflows,
    analyze_modules,
    load_actions_runs,
    load_coverage,
    module_risk,
    source_performance,
)


# ── fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def mini_repo(tmp_path):
    """Dois módulos, um importando o outro, mais um teste que deve ser marcado."""
    (tmp_path / "alpha.py").write_text(textwrap.dedent("""
        import os
        from beta import helper

        def simple(x):
            return x + 1

        def branchy(x, y):
            if x and y:
                for i in range(x):
                    if i % 2:
                        return i
            elif x:
                return y
            try:
                return helper(x)
            except ValueError:
                return 0
    """), encoding="utf-8")

    (tmp_path / "beta.py").write_text(textwrap.dedent("""
        def helper(x):
            return x * 2
    """), encoding="utf-8")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_alpha.py").write_text("def test_nothing():\n    assert True\n",
                                             encoding="utf-8")
    return tmp_path


# ── ① análise de módulos ────────────────────────────────────────────────

def test_analyze_modules_finds_modules_and_marks_tests(mini_repo):
    mods = analyze_modules(str(mini_repo))
    assert set(mods) >= {"alpha", "beta", "tests.test_alpha"}
    assert mods["tests.test_alpha"]["is_test"] is True
    assert mods["alpha"]["is_test"] is False


def test_cyclomatic_grows_with_branching(mini_repo):
    mods = analyze_modules(str(mini_repo))
    fns = {f["name"]: f for f in mods["alpha"]["hotspots"]}
    # `simple` não tem desvio nenhum, então não pode ser hotspot
    assert "simple" not in fns
    # e a complexidade do módulo tem de vir sobretudo de branchy
    assert mods["alpha"]["max_cc"] > 1
    assert mods["beta"]["max_cc"] == 1


def test_local_imports_become_edges_not_external(mini_repo):
    mods = analyze_modules(str(mini_repo))
    assert mods["alpha"]["imports"] == ["beta"]
    assert mods["beta"]["imported_by"] == ["alpha"]
    # os se os externos não viram aresta
    assert "os" in mods["alpha"]["imports_external"]
    assert "os" not in mods["alpha"]["imports"]


def test_fan_in_out_and_instability(mini_repo):
    mods = analyze_modules(str(mini_repo))
    # alpha só importa: instável (depende, ninguém depende dele)
    assert mods["alpha"]["fan_out"] == 1
    assert mods["alpha"]["fan_in"] == 0
    assert mods["alpha"]["instability"] == 1.0
    # beta só é importado: estável, mas caro de mudar
    assert mods["beta"]["fan_in"] == 1
    assert mods["beta"]["fan_out"] == 0
    assert mods["beta"]["instability"] == 0.0


def test_syntax_error_does_not_break_analysis(mini_repo):
    (mini_repo / "broken.py").write_text("def nope(:\n", encoding="utf-8")
    mods = analyze_modules(str(mini_repo))
    assert "broken" not in mods
    assert "alpha" in mods          # o resto segue analisado


def test_skips_non_production_dirs(mini_repo):
    archive = mini_repo / "archive"
    archive.mkdir()
    (archive / "old.py").write_text("x = 1\n", encoding="utf-8")
    mods = analyze_modules(str(mini_repo))
    assert not any(m.startswith("archive") for m in mods)


# ── risco ───────────────────────────────────────────────────────────────

def _mod(loc=500, cc=100, fan_in=4):
    return {"loc": loc, "sum_cc": cc, "fan_in": fan_in}


def test_risk_falls_as_coverage_rises():
    m = _mod()
    assert module_risk(m, 100.0) == 0.0
    assert module_risk(m, 50.0) < module_risk(m, 0.0)


def test_risk_treats_unknown_coverage_as_worst_case():
    """Sem dado de cobertura não é o mesmo que coberto — assume 0%."""
    m = _mod()
    assert module_risk(m, None) == module_risk(m, 0.0)


def test_risk_grows_with_size_complexity_and_dependents():
    base = module_risk(_mod(), 0.0)
    assert module_risk(_mod(loc=1000), 0.0) > base
    assert module_risk(_mod(cc=200), 0.0) > base
    assert module_risk(_mod(fan_in=10), 0.0) > base


# ── cobertura ───────────────────────────────────────────────────────────

def test_load_coverage_missing_file_returns_empty(tmp_path):
    assert load_coverage(str(tmp_path / "nope.json")) == {}


def test_load_coverage_corrupt_file_returns_empty(tmp_path):
    bad = tmp_path / "coverage.json"
    bad.write_text("{not json", encoding="utf-8")
    assert load_coverage(str(bad)) == {}


def test_load_coverage_reads_percentages(tmp_path):
    path = tmp_path / "coverage.json"
    path.write_text(json.dumps({
        "files": {"alpha.py": {"summary": {"percent_covered": 83.456}},
                  "beta.py": {"summary": {}}}
    }), encoding="utf-8")
    cov = load_coverage(str(path))
    assert cov["alpha.py"] == 83.5
    assert "beta.py" not in cov     # sem percent_covered não entra


def test_aggregate_architecture_flags_zero_coverage(mini_repo):
    cov = mini_repo / "coverage.json"
    cov.write_text(json.dumps({
        "files": {"alpha.py": {"summary": {"percent_covered": 0.0}},
                  "beta.py": {"summary": {"percent_covered": 90.0}}}
    }), encoding="utf-8")
    arch = aggregate_architecture(str(mini_repo), str(cov))
    assert "alpha" in arch["no_coverage"]
    assert "beta" not in arch["no_coverage"]
    assert arch["has_coverage_data"] is True
    # ordenado por risco: alpha (0% de cobertura) antes de beta
    assert [m["module"] for m in arch["modules"]][0] == "alpha"


def test_aggregate_architecture_without_coverage_data(mini_repo):
    arch = aggregate_architecture(str(mini_repo), str(mini_repo / "absent.json"))
    assert arch["has_coverage_data"] is False
    assert arch["avg_coverage"] is None
    assert arch["no_coverage"] == []    # desconhecido ≠ zero: não acusa
    assert arch["n_modules"] >= 2


def test_architecture_excludes_tests_from_modules(mini_repo):
    arch = aggregate_architecture(str(mini_repo), str(mini_repo / "absent.json"))
    assert not any(m["module"].startswith("tests") for m in arch["modules"])
    assert arch["n_tests_files"] == 1


# ── ② workflows ─────────────────────────────────────────────────────────

def _run(path, conclusion, created, dur=30.0, name=None):
    return {"path": path, "conclusion": conclusion, "created_at": created,
            "duration_s": dur, "name": name or path, "head_sha": "abc1234",
            "display_title": "t"}


def test_aggregate_workflows_empty():
    agg = aggregate_workflows([])
    assert agg["workflows"] == []
    assert agg["n_runs"] == 0


def test_aggregate_workflows_filters_github_own_workflows():
    runs = [
        _run(".github/workflows/tests.yml", "success", "2026-01-01T00:00:00Z"),
        _run("dynamic/pages/pages-build-deployment", "failure", "2026-01-02T00:00:00Z"),
    ]
    agg = aggregate_workflows(runs)
    assert agg["n_runs"] == 1
    assert [w["path"] for w in agg["workflows"]] == [".github/workflows/tests.yml"]
    # com own_only=False os dois entram
    assert aggregate_workflows(runs, own_only=False)["n_runs"] == 2


def test_success_rate_ignores_cancelled():
    runs = [
        _run(".github/workflows/a.yml", "success", "2026-01-01T00:00:00Z"),
        _run(".github/workflows/a.yml", "failure", "2026-01-02T00:00:00Z"),
        _run(".github/workflows/a.yml", "cancelled", "2026-01-03T00:00:00Z"),
    ]
    w = aggregate_workflows(runs)["workflows"][0]
    assert w["n"] == 3                 # conta todos os runs
    assert w["success_pct"] == 50.0    # mas a taxa só olha decididos
    assert w["n_failures"] == 1


def test_streak_counts_from_the_most_recent_run():
    runs = [
        _run(".github/workflows/a.yml", "failure", "2026-01-01T00:00:00Z"),
        _run(".github/workflows/a.yml", "success", "2026-01-02T00:00:00Z"),
        _run(".github/workflows/a.yml", "success", "2026-01-03T00:00:00Z"),
    ]
    w = aggregate_workflows(runs)["workflows"][0]
    assert (w["streak"], w["streak_kind"]) == (2, "success")
    assert w["last_conclusion"] == "success"


def test_streak_detects_current_failure_run():
    runs = [
        _run(".github/workflows/a.yml", "success", "2026-01-01T00:00:00Z"),
        _run(".github/workflows/a.yml", "failure", "2026-01-02T00:00:00Z"),
        _run(".github/workflows/a.yml", "failure", "2026-01-03T00:00:00Z"),
    ]
    w = aggregate_workflows(runs)["workflows"][0]
    assert (w["streak"], w["streak_kind"]) == (2, "failure")


def test_durations_report_median_and_p90():
    runs = [_run(".github/workflows/a.yml", "success",
                 f"2026-01-{i:02d}T00:00:00Z", dur=float(i)) for i in range(1, 11)]
    w = aggregate_workflows(runs)["workflows"][0]
    assert w["median_s"] == 6.0
    assert w["p90_s"] == 10.0


def test_load_actions_runs_missing_and_corrupt(tmp_path):
    assert load_actions_runs(str(tmp_path / "nope.json")) == []
    bad = tmp_path / "actions_runs.json"
    bad.write_text("{oops", encoding="utf-8")
    assert load_actions_runs(str(bad)) == []


def test_load_actions_runs_accepts_both_shapes(tmp_path):
    wrapped = tmp_path / "wrapped.json"
    wrapped.write_text(json.dumps({"runs": [{"path": "a"}]}), encoding="utf-8")
    assert load_actions_runs(str(wrapped)) == [{"path": "a"}]
    bare = tmp_path / "bare.json"
    bare.write_text(json.dumps([{"path": "b"}]), encoding="utf-8")
    assert load_actions_runs(str(bare)) == [{"path": "b"}]


# ── ③ performance por fonte ─────────────────────────────────────────────

CONFIG = {"sources": {
    "techcrunch": {"enabled": True, "weight": 1.1},
    "simon_willison": {"enabled": True, "weight": 1.1},
    "qwen_blog": {"enabled": True, "weight": 0.9},
    "_comment_foo": "não é fonte",
}}


def test_source_performance_separates_the_two_windows():
    """`sources_used` cobre tudo; `source` por item só as edições novas. Uma
    fonte usada há muito tempo não pode parecer improdutiva por isso."""
    editions = [
        # edição antiga: só sources_used, sem source por item
        {"edition": "100", "sources_used": ["techcrunch", "simon_willison"],
         "main_find": {"title": "x"}, "quick_finds": [{"title": "y"}]},
        # edição nova: as duas coisas
        {"edition": "200", "sources_used": ["techcrunch"],
         "main_find": {"title": "x", "source": "techcrunch"},
         "quick_finds": [{"title": "y", "source": "techcrunch"}]},
    ]
    rows = {r["source"]: r for r in source_performance(editions, {}, CONFIG)}

    tc = rows["techcrunch"]
    assert tc["used_count"] == 2           # janela longa: as duas edições
    assert tc["main_find"] == 1            # janela de item: só a 200
    assert tc["quick_finds"] == 1
    assert tc["_n_item_window"] == 1       # só uma edição tem source por item

    sw = rows["simon_willison"]
    assert sw["used_count"] == 1           # contribuiu…
    assert sw["items"] == 0                # …mas sem item na janela nova
    assert sw["idle"] is False             # e por isso NÃO é ociosa


def test_idle_source_is_one_that_never_contributed():
    editions = [{"edition": "1", "sources_used": ["techcrunch"], "quick_finds": []}]
    rows = {r["source"]: r for r in source_performance(editions, {}, CONFIG)}
    assert rows["qwen_blog"]["idle"] is True
    assert rows["qwen_blog"]["used_count"] == 0
    assert rows["techcrunch"]["idle"] is False


def test_comment_keys_are_not_counted_as_sources():
    rows = source_performance([], {}, CONFIG)
    assert {r["source"] for r in rows} == {"techcrunch", "simon_willison", "qwen_blog"}


def test_false_negatives_match_judge_display_names_to_config_ids():
    """O judge escreve 'Simon Willison' e 'r/artificial'; a config usa ids."""
    config = {"sources": {"simon_willison": {"enabled": True, "weight": 1.1},
                          "reddit": {"enabled": True, "weight": 1.0}}}
    audits = {"200": {"false_negatives": [
        {"source": "Simon Willison"},
        {"source": "r/artificial"},
        {"source": "r/LocalLLaMA"},
    ]}}
    rows = {r["source"]: r for r in source_performance([], audits, config)}
    assert rows["simon_willison"]["false_negatives"] == 1
    assert rows["reddit"]["false_negatives"] == 2


def test_fn_per_item_is_none_without_items_not_zero():
    """Dividir por zero itens não é 'ótimo desempenho' — é indefinido."""
    audits = {"200": {"false_negatives": [{"source": "Simon Willison"}]}}
    rows = {r["source"]: r for r in source_performance([], audits, CONFIG)}
    assert rows["simon_willison"]["items"] == 0
    assert rows["simon_willison"]["fn_per_item"] is None


def test_fn_per_item_flags_systematically_missed_source():
    editions = [{"edition": "200", "sources_used": ["simon_willison"],
                 "main_find": {"source": "simon_willison"}, "quick_finds": []}]
    audits = {str(i): {"false_negatives": [{"source": "Simon Willison"}]}
              for i in range(10)}
    rows = {r["source"]: r for r in source_performance(editions, audits, CONFIG)}
    sw = rows["simon_willison"]
    assert sw["items"] == 1
    assert sw["fn_per_item"] == 10.0
    assert sw["fn_per_item"] >= FN_PER_ITEM_BAD


def test_source_performance_survives_malformed_editions():
    editions = [
        {"edition": "1"},                                   # sem campo nenhum
        {"edition": "2", "sources_used": None, "quick_finds": None},
        {"edition": "3", "main_find": None, "quick_finds": [None, {}]},
    ]
    rows = source_performance(editions, {}, CONFIG)
    assert all(r["used_count"] == 0 for r in rows)


def test_source_performance_defaults_to_repo_config():
    """Sem config explícita lê sources_config.json — é como o dashboard chama."""
    rows = source_performance([], {})
    assert rows
    assert all("_comment" not in r["source"] for r in rows)


# ── limiares ────────────────────────────────────────────────────────────

def test_thresholds_are_coherent():
    assert arch_stats.FN_CC_WARN < arch_stats.FN_CC_BAD
    assert COV_BAD < arch_stats.COV_WARN
    assert 0 < arch_stats.INSTABILITY_FRAGILE <= 1
    assert 0 < arch_stats.WORKFLOW_OK_PCT <= 100


# ── render: a camada de arquitetura do dashboard ────────────────────────
#
# dashboard.py é só renderização, mas é o que você lê pra decidir — e um render
# que explode com dado ausente derruba o painel inteiro, não só um painel. Estes
# testes cobrem o contrato mínimo: não levanta, não injeta HTML, e diz o que
# fazer quando o dado não existe.

import dashboard


def test_render_module_risk_empty():
    assert "nenhum módulo" in dashboard.render_module_risk([])


def test_render_module_risk_marks_complexity_and_coverage():
    mods = [{
        "module": "big", "is_script": False, "loc": 800, "sum_cc": 200,
        "max_cc": 20, "fan_in": 3, "fan_out": 2, "coverage_pct": 0.0,
        "risk": 40.0, "hotspots": [], "instability": 0.4,
    }]
    html_out = dashboard.render_module_risk(mods)
    assert "big" in html_out
    assert "class='bad'" in html_out          # CC 20 >= FN_CC_BAD e cobertura 0


def test_render_module_risk_hides_unknown_coverage_as_dash():
    mods = [{
        "module": "m", "is_script": False, "loc": 10, "sum_cc": 1, "max_cc": 1,
        "fan_in": 0, "fan_out": 0, "coverage_pct": None, "risk": 0.1,
        "hotspots": [], "instability": 0.0,
    }]
    assert "empty-cell" in dashboard.render_module_risk(mods)


def test_render_module_risk_skips_scripts():
    mods = [{
        "module": "scripts.thing", "is_script": True, "loc": 10, "sum_cc": 1,
        "max_cc": 1, "fan_in": 0, "fan_out": 0, "coverage_pct": 50.0,
        "risk": 0.1, "hotspots": [], "instability": 0.0,
    }]
    assert "nenhum módulo" in dashboard.render_module_risk(mods)


def test_render_hotspots_reports_clean_repo():
    mods = [{"path": "a.py", "is_script": False, "hotspots": []}]
    assert "nenhuma função acima" in dashboard.render_hotspots(mods)


def test_render_hotspots_lists_file_and_line():
    mods = [{"path": "a.py", "is_script": False,
             "hotspots": [{"name": "f", "line": 42, "cc": 20, "loc": 60, "nesting": 4}]}]
    out = dashboard.render_hotspots(mods)
    assert "a.py:42" in out
    assert "🔴" in out            # cc 20 >= FN_CC_BAD


def test_render_coupling_empty_and_populated():
    assert "sem imports" in dashboard.render_coupling([])
    mods = [{"module": "m", "is_script": False, "fan_in": 2, "fan_out": 5,
             "instability": 0.9}]
    out = dashboard.render_coupling(mods)
    assert "split-row" in out
    assert "out bad" in out       # instabilidade 0.9 com 5 dependências


def test_render_workflow_health_tells_how_to_generate_snapshot():
    out = dashboard.render_workflow_health({})
    assert "fetch_actions_runs" in out


def test_render_workflow_health_colors_low_success():
    agg = {"n_runs": 10, "range": ("2026-01-01", "2026-02-01"), "workflows": [{
        "name": "Security", "path": ".github/workflows/security.yml", "n": 10,
        "success_pct": 50.0, "n_failures": 5, "median_s": 25.0, "p90_s": 30.0,
        "last_conclusion": "failure", "streak": 2, "streak_kind": "failure",
        "last_run": "2026-02-01", "failures": [],
    }]}
    out = dashboard.render_workflow_health(agg)
    assert "class='bad'" in out
    assert "2× falha" in out


def test_render_workflow_health_handles_missing_duration():
    agg = {"n_runs": 1, "range": None, "workflows": [{
        "name": "A", "path": ".github/workflows/a.yml", "n": 1,
        "success_pct": None, "n_failures": 0, "median_s": None, "p90_s": None,
        "last_conclusion": "success", "streak": 1, "streak_kind": "success",
        "last_run": "2026-01-01", "failures": [],
    }]}
    assert "—" in dashboard.render_workflow_health(agg)


def test_render_source_performance_empty():
    assert "sem dados" in dashboard.render_source_performance([])


def test_render_source_performance_badges_idle_and_missed():
    rows = [
        {"source": "dead_feed", "weight": 0.9, "used_count": 0, "used_pct": 0.0,
         "main_find": 0, "quick_finds": 0, "false_negatives": 0,
         "fn_per_item": None, "idle": True, "_n_with_used": 125, "_n_item_window": 23},
        {"source": "missed", "weight": 1.1, "used_count": 5, "used_pct": 4.0,
         "main_find": 0, "quick_finds": 1, "false_negatives": 13,
         "fn_per_item": 13.0, "idle": False, "_n_with_used": 125,
         "_n_item_window": 23},
    ]
    out = dashboard.render_source_performance(rows)
    assert "🔴" in out and "🟠" in out
    # a nota tem de dizer que as janelas são diferentes, senão alguém compara
    assert "125" in out and "23" in out


def test_render_source_performance_escapes_source_names():
    rows = [{"source": "<script>x</script>", "weight": 1.0, "used_count": 1,
             "used_pct": 1.0, "main_find": 0, "quick_finds": 0,
             "false_negatives": 0, "fn_per_item": None, "idle": False,
             "_n_with_used": 1, "_n_item_window": 1}]
    out = dashboard.render_source_performance(rows)
    assert "<script>" not in out


def test_render_html_works_without_the_architecture_layer():
    """Os três argumentos novos são opcionais: um painel gerado sem eles tem de
    sair inteiro, só sem as seções novas preenchidas."""
    from collections import Counter
    doc = dashboard.render_html(
        content={"date_range": ("2026-01-01", "2026-01-02"), "n_editions": 1,
                 "themes": Counter(), "entities": Counter(), "sources": Counter(),
                 "epistemic_pct": {}, "feedback": {}, "n_rated": 0,
                 "feedback_by_theme": {}, "repeats": [], "never_used_sources": [],
                 "n_enabled_sources": 22},
        quality={"hypotheses": Counter(), "fn_by_source": Counter(),
                 "hypothesis_editions": {}, "fn_editions_by_source": {}},
        insights=[],
        cadence={"n_dates": 1, "span_days": 1, "gaps": []},
        meta={"generated_at": "2026-01-02 10:00", "date_by_edition": {}},
        test_runs=[],
    )
    assert "⑥ Arquitetura" in doc
    assert "fetch_actions_runs" in doc       # diz como preencher
    assert doc.rstrip().endswith("</html>")
