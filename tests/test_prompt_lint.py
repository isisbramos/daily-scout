"""Testes do lint determinístico (scripts/prompt_lint.py) e do replay (scripts/prompt_replay.py)."""

import json
from pathlib import Path

from scripts import prompt_lint as lint
from scripts import prompt_replay as replay

FIXTURES = Path(__file__).parent / "fixtures" / "replay"

ITEMS = [
    {"title": "Apple adds compliance filings", "url": "https://technode.com/a", "source": "TechNode"},
    {"title": "Qwen4-Max dropped as closed API", "url": "https://www.reddit.com/r/x/1", "source": "r/artificial"},
    {"title": "Termination Lag", "url": "https://huggingface.co/papers/1", "source": "HuggingFace Papers",
     "summary": "We study five models across 3 datasets."},
]


def _curation(**over):
    base = {
        "main_find": {"title": "T", "url": "https://technode.com/a", "primary_audience": "product managers e fundadores",
                      "body": "A Apple mudou algo. → No seu trabalho: revise o fluxo.", "bullets": ["x"],
                      "entities": ["Apple"]},
        "quick_finds": [],
        "radar": [],
    }
    base.update(over)
    return base


class TestLintCuration:
    def test_clean_curation_has_no_violations(self):
        m = lint.lint_curation(_curation(), ITEMS)
        for k in lint.HIGHER_IS_WORSE:
            assert m[k] == 0, k
        assert m["itens"] == 1

    def test_radar_without_url_and_speculation_and_meta(self):
        radar = [{"title": "R", "why_watch": "O título só anuncia — pode antecipar mudanças."}]
        m = lint.lint_curation(_curation(radar=radar), ITEMS)
        assert m["radar_sem_url"] == 1
        assert m["radar_especula"] == 1
        assert m["meta_linguagem"] == 1

    def test_meta_language_in_body_is_caught(self):
        c = _curation()
        c["main_find"]["body"] = "A edição anterior cobriu isso. → No seu trabalho: revise."
        assert lint.lint_curation(c, ITEMS)["meta_linguagem"] == 1

    def test_arrow_opening_and_missing_arrow(self):
        c = _curation(quick_finds=[
            {"url": "https://www.reddit.com/r/x/1", "signal": "Algo. → No seu trabalho: se sua equipe usa X, revise.",
             "entities": ["Alibaba", "TechCrunch"], "primary_audience": "desenvolvedores", "follow_up": "mudou a licença"},
            {"url": "https://huggingface.co/papers/1", "signal": "Sem linha final.", "entities": []},
        ])
        m = lint.lint_curation(c, ITEMS)
        assert m["linha_abre_com_se"] == 1
        assert m["sem_linha_trabalho"] == 1
        assert m["entidade_e_fonte"] == 1
        assert m["audiencia_dev"] == 1
        assert m["so_reddit"] == 1
        assert m["papers"] == 1
        assert m["follow_ups"] == 1

    def test_invented_number_is_flagged_but_input_number_is_not(self):
        ok = _curation(); ok["main_find"]["body"] = "Cinco modelos em 3 datasets. → No seu trabalho: revise."
        c = _curation(quick_finds=[{"url": "https://huggingface.co/papers/1",
                                    "signal": "Reduz 40% do custo. → No seu trabalho: teste.", "entities": []}])
        assert lint.lint_curation(ok, ITEMS)["numero_fora_do_input"] == 0
        assert lint.lint_curation(c, ITEMS)["numero_fora_do_input"] == 1

    def test_format_table_has_one_row_per_metric(self):
        table = lint.format_table({"a": lint.lint_curation(_curation(), ITEMS)})
        assert len(table.splitlines()) == 1 + len(lint.METRICS)


class TestReplay:
    def test_real_fixtures_load_with_summaries(self):
        files = sorted(FIXTURES.glob("*_items.json"))
        assert len(files) >= 3
        raw, items = replay.load_fixture(files[-1])
        assert len(raw) == len(items) > 20
        assert any(i.extra.get("summary") for i in items)  # a entrada mais nova carrega resumos de paper

    def test_run_replay_aggregates_means_and_counts_failures(self, tmp_path):
        calls = {"n": 0}

        def fake_curate(items, raw_count=0):
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("LLM caiu")
            return _curation(radar=[{"title": "R", "why_watch": "ok"}])  # radar sem url

        result = replay.run_replay(FIXTURES, runs=2, curate_fn=fake_curate, save_dir=tmp_path)
        n_fix = len(result["fixtures"])
        assert sum(e["failures"] for e in result["fixtures"].values()) == 1
        assert result["mean"]["radar_sem_url"] == 1.0  # toda execução bem-sucedida tinha 1
        assert len(list(tmp_path.glob("*_run*.json"))) == n_fix * 2 - 1

    def test_report_flags_regression_against_baseline(self):
        now = {"fixtures": {"x": {"runs": [{}], "failures": 0}}, "mean": {k: 0 for k, _ in lint.METRICS}}
        base = {"mean": {k: 0 for k, _ in lint.METRICS}}
        now["mean"]["meta_linguagem"] = 1.0
        report = replay.format_report(now, base)
        line = next(l for l in report.splitlines() if "meta-linguagem" in l)
        assert "⚠" in line
        assert "⚠" not in next(l for l in report.splitlines() if l.startswith("radar sem url"))

    def test_main_requires_api_key(self, monkeypatch, capsys):
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        assert replay.main(["--label", "x"]) == 2
