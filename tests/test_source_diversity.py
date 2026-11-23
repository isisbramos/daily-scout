"""Trava de diversidade por fonte na saída + preenchimento de quick finds (higiene, 23/11/2026)."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

import pipeline
from sources.base import SourceItem
from tests.test_curate_and_write import _fake_openai, _response


def _qf(title, source, url=""):
    return {"title": title, "source": source, "url": url or f"https://x/{title}", "signal": "s. → No seu trabalho: x."}


def _ri(title, source, url=""):
    return {"title": title, "source": source, "url": url or f"https://x/{title}", "display_url": "x/…",
            "why_watch": f"por que olhar {title}"}


def _content(main_src, quick, radar):
    return {"main_find": {"title": "M", "source": main_src, "url": "https://x/M"},
            "quick_finds": quick, "radar": radar}


class TestEnforceSourceDiversity:
    def test_edicao_246_technode_tres_vezes(self):
        """Caso real da ed. 246: TechNode no achado, num quick find e no radar."""
        c = _content("TechNode",
                     [_qf("q1", "HuggingFace Papers"), _qf("q2", "HuggingFace Papers"),
                      _qf("q3", "TechNode"), _qf("q4", "arXiv (CS.AI)")],
                     [_ri("r1", "TechNode"), _ri("r2", "SCMP Tech")])
        dropped = pipeline.enforce_source_diversity(c)
        assert [d["title"] for d in dropped] == ["r1"]
        assert [r["title"] for r in c["radar"]] == ["r2"]
        assert len(c["quick_finds"]) == 4
        assert c["source_caps"][0]["where"] == "radar"

    def test_dry_run_15_11_apple_tres_vezes(self):
        """Dry run de 15/11: Apple no achado e nos 2 itens do radar."""
        c = _content("Apple Machine Learning Research",
                     [_qf("q1", "TechCrunch"), _qf("q2", "HackerNews")],
                     [_ri("r1", "Apple Machine Learning Research"), _ri("r2", "Apple Machine Learning Research")])
        pipeline.enforce_source_diversity(c)
        assert [r["title"] for r in c["radar"]] == ["r1"]

    def test_quick_finds_alem_do_limite_saem_em_ordem(self):
        c = _content("TechCrunch", [_qf("q1", "TechCrunch"), _qf("q2", "TechCrunch"), _qf("q3", "Lobsters")], [])
        pipeline.enforce_source_diversity(c)
        assert [q["title"] for q in c["quick_finds"]] == ["q1", "q3"]

    def test_radar_maximo_um_por_fonte_mesmo_sem_estourar_edicao(self):
        c = _content("TechCrunch", [], [_ri("r1", "SCMP Tech"), _ri("r2", "SCMP Tech")])
        pipeline.enforce_source_diversity(c)
        assert [r["title"] for r in c["radar"]] == ["r1"]

    def test_main_find_nunca_sai(self):
        c = _content("TechCrunch", [_qf("q1", "TechCrunch"), _qf("q2", "TechCrunch")], [])
        pipeline.enforce_source_diversity(c, max_per_source=1)
        assert c["main_find"]["title"] == "M" and c["quick_finds"] == []

    def test_fonte_vem_da_url_do_input_quando_existe(self):
        """Rótulos diferentes da mesma fonte contam juntos quando a url aponta para o input."""
        items = {"https://a/1": SourceItem(title="t", url="https://a/1", source_id="technode", source_label="TechNode"),
                 "https://a/2": SourceItem(title="t", url="https://a/2", source_id="technode", source_label="TechNode")}
        c = _content("TechNode", [_qf("q1", "Technode CN", url="https://a/1"), _qf("q2", "TN", url="https://a/2")], [])
        pipeline.enforce_source_diversity(c, items)
        assert [q["title"] for q in c["quick_finds"]] == ["q1"]

    def test_item_sem_fonte_nao_conta(self):
        c = _content("", [_qf("q1", ""), _qf("q2", ""), _qf("q3", "")], [])
        assert pipeline.enforce_source_diversity(c) == []
        assert len(c["quick_finds"]) == 3

    def test_edicao_diversa_fica_intacta(self):
        c = _content("A", [_qf("q1", "B"), _qf("q2", "C"), _qf("q3", "D")], [_ri("r1", "E"), _ri("r2", "A")])
        before = json.dumps(c, sort_keys=True)
        assert pipeline.enforce_source_diversity(c) == []
        assert json.dumps(c, sort_keys=True) == before


class TestRefillQuickFinds:
    def test_completa_ate_tres_a_partir_do_radar(self):
        c = _content("A", [_qf("q1", "B"), _qf("q2", "C")], [_ri("r1", "D"), _ri("r2", "E")])
        promoted = pipeline.refill_quick_finds(c)
        assert promoted == ["r1"]
        assert [q["title"] for q in c["quick_finds"]] == ["q1", "q2", "r1"]
        assert c["quick_finds"][2]["signal"] == "por que olhar r1"
        assert c["quick_finds"][2]["refilled_from"] == "radar"
        assert [r["title"] for r in c["radar"]] == ["r2"]
        assert c["quick_refills"] == ["r1"]

    def test_sem_radar_nao_inventa_item(self):
        c = _content("A", [_qf("q1", "B")], [])
        assert pipeline.refill_quick_finds(c) == []
        assert len(c["quick_finds"]) == 1

    def test_ja_com_tres_nao_mexe(self):
        c = _content("A", [_qf("q1", "B"), _qf("q2", "C"), _qf("q3", "D")], [_ri("r1", "E")])
        assert pipeline.refill_quick_finds(c) == []
        assert len(c["radar"]) == 1


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    monkeypatch.setattr(pipeline, "DEEPSEEK_API_KEY", "fake-key")
    monkeypatch.setattr(pipeline, "load_recent_editions", lambda n=7: [])
    monkeypatch.setattr(pipeline.time, "sleep", lambda *a, **k: None)


class TestIntegracaoCurateAndWrite:
    ITEMS = [SourceItem(title=f"t{i}", url=f"https://s/{i}", source_id=sid, source_label=lbl)
             for i, (sid, lbl) in enumerate([("technode", "TechNode")] * 4 + [("hf", "HF"), ("scmp", "SCMP")])]

    def test_trava_e_preenchimento_rodam_no_fim_da_curadoria(self):
        content = {
            "main_find": {"title": "M", "source": "TechNode", "url": "https://s/0", "body": "b", "bullets": []},
            "quick_finds": [_qf("q1", "TechNode", "https://s/1"), _qf("q2", "TechNode", "https://s/2"),
                            _qf("q3", "HF", "https://s/4")],
            "radar": [_ri("r1", "TechNode", "https://s/3"), _ri("r2", "SCMP", "https://s/5")],
            "correspondent_intro": "intro",
        }
        with patch("openai.OpenAI", _fake_openai([_response(content)])):
            out = pipeline.curate_and_write(self.ITEMS)
        # q2 e r1 estouram TechNode (máx. 2); r2 sobe do radar para completar 3 quick finds.
        assert [q["title"] for q in out["quick_finds"]] == ["q1", "q3", "r2"]
        assert out["radar"] == []
        assert {d["title"] for d in out["source_caps"]} == {"q2", "r1"}
        sources = [out["main_find"]["source"]] + [q["source"] for q in out["quick_finds"]]
        assert sources.count("TechNode") == 2
