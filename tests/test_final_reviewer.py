"""Rec. 1 — revisor final: shadow não altera a edição; enforce remove com guardrails; falha aberta."""

from __future__ import annotations

import copy
import json
from types import SimpleNamespace

import final_reviewer as fr
from sources.base import SourceItem


def _item(n, source_id="techcrunch", label="TechCrunch"):
    return SourceItem(title=f"cand {n}", url=f"https://x/{n}", source_id=source_id, source_label=label)


CANDS = [_item(i) for i in range(1, 8)]


def _content():
    return {
        "reasoning": {"main_find_rationale": "escolhi o main", "ai_gate_rejected_sample": []},
        "main_find": {"title": "Main", "url": "https://x/1", "body": "b", "bullets": ["b1"], "source": "TechCrunch"},
        "quick_finds": [
            {"title": f"QF{i}", "url": f"https://x/{i + 1}", "source": "TechCrunch",
             "signal": f"Sinal {i}. → Importa.", "entities": [f"E{i}"]}
            for i in range(1, 5)
        ],
    }


def _client(payload):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    create = lambda **kw: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def _v(idx, verdict="PASS", rule="none"):
    return {"idx": idx, "verdict": verdict, "rule": rule, "why": "x"}


class TestModes:
    def test_off_does_nothing(self):
        assert fr.run_final_review(_content(), CANDS, {"mode": "off"}, client=_client({})) is None
        assert fr.run_final_review(_content(), CANDS, None, client=_client({})) is None

    def test_shadow_records_but_never_changes_content(self):
        content, before = _content(), copy.deepcopy(_content())
        payload = {"verdicts": [_v(0), _v(1, "FAIL", "funding"), _v(2), _v(3), _v(4)],
                   "missed": [{"candidate": "C6", "why": "evento forte"}]}
        review = fr.run_final_review(content, CANDS, {"mode": "shadow"}, client=_client(payload))
        assert content == before
        assert review["verdicts"][1]["rule"] == "funding"
        assert review["missed"][0]["title"] == "cand 6"
        assert "actions" not in review

    def test_enforce_removes_failed_quick_find(self):
        content = _content()
        payload = {"verdicts": [_v(0), _v(1, "FAIL", "panorama"), _v(2), _v(3), _v(4)], "missed": []}
        review = fr.run_final_review(content, CANDS, {"mode": "enforce"}, client=_client(payload))
        assert [q["title"] for q in content["quick_finds"]] == ["QF2", "QF3", "QF4"]
        assert review["actions"][0]["action"] == "quick_removed"


class TestGuardrails:
    def test_keeps_minimum_quick_finds(self):
        content = _content()
        v = [_v(0)] + [_v(i, "FAIL", "funding") for i in range(1, 5)]
        review = fr.run_final_review(content, CANDS, {"mode": "enforce", "max_removals": 9}, client=_client({"verdicts": v}))
        assert len(content["quick_finds"]) == 3
        assert any(a["action"] == "kept_by_guardrail" for a in review["actions"])

    def test_caps_removals(self):
        content = _content()
        content["quick_finds"].append({"title": "QF5", "url": "https://x/6", "source": "TC", "signal": "s", "entities": []})
        v = [_v(0)] + [_v(i, "FAIL", "opinion") for i in range(1, 4)] + [_v(4), _v(5)]
        fr.run_final_review(content, CANDS, {"mode": "enforce", "max_removals": 1, "min_quick_finds": 1}, client=_client({"verdicts": v}))
        assert len(content["quick_finds"]) == 4  # só 1 remoção de 3 FAIL

    def test_failed_main_is_replaced_by_passing_quick_find(self):
        content = _content()
        v = [_v(0, "FAIL", "unverified"), _v(1, "FAIL", "funding"), _v(2), _v(3), _v(4)]
        review = fr.run_final_review(content, CANDS, {"mode": "enforce"}, client=_client({"verdicts": v}))
        assert content["main_find"]["title"] == "QF2"          # 1º quick_find PASS
        # QF1 (FAIL) fica porque remover deixaria < 3 quick_finds (guardrail)
        assert [q["title"] for q in content["quick_finds"]] == ["QF1", "QF3", "QF4"]
        assert any(a["action"] == "kept_by_guardrail" for a in review["actions"])
        assert review["actions"][0]["action"] == "main_replaced"

    def test_failed_main_without_replacement_is_kept(self):
        content = _content()
        v = [_v(0, "FAIL", "unverified")] + [_v(i, "FAIL", "funding") for i in range(1, 5)]
        review = fr.run_final_review(content, CANDS, {"mode": "enforce"}, client=_client({"verdicts": v}))
        assert content["main_find"]["title"] == "Main"
        assert review["actions"][0]["action"] == "main_kept_no_replacement"


class TestFailOpen:
    def test_invalid_json_is_nonblocking(self):
        content, before = _content(), copy.deepcopy(_content())
        review = fr.run_final_review(content, CANDS, {"mode": "enforce"}, client=_client("isto não é json"))
        assert content == before and "error" in review

    def test_llm_exception_is_nonblocking(self):
        def boom(**kw):
            raise RuntimeError("API fora")
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=boom)))
        content, before = _content(), copy.deepcopy(_content())
        review = fr.run_final_review(content, CANDS, {"mode": "enforce"}, client=client)
        assert content == before and "API fora" in review["error"]

    def test_malformed_verdicts_are_ignored(self):
        payload = {"verdicts": [{"idx": 99, "verdict": "FAIL"}, {"idx": "x"}, {"idx": 1, "verdict": "talvez"}, _v(2, "FAIL", "inventada")]}
        review = fr.run_final_review(_content(), CANDS, {"mode": "shadow"}, client=_client(payload))
        assert [v["idx"] for v in review["verdicts"]] == [2] and review["verdicts"][0]["rule"] == "other"


class TestContradictions:
    def test_published_item_listed_as_rejected_is_flagged(self):
        content = _content()
        content["reasoning"]["ai_gate_rejected_sample"] = ["QF2 (sem ângulo AI)", "Outra coisa"]
        found = fr.find_contradictions(content)
        assert [c["title"] for c in found] == ["QF2"]

    def test_no_sample_no_contradictions(self):
        assert fr.find_contradictions(_content()) == []


class TestTolerantParsing:
    """Regressão da ed.198: 'str' object has no attribute 'get' com a resposta real do modelo."""

    def test_verdicts_as_indexed_dict(self):
        payload = {"verdicts": {"0": {"verdict": "PASS", "rule": "none", "why": "ok"},
                                "1": {"verdict": "FAIL", "rule": "funding", "why": "x"}}}
        review = fr.run_final_review(_content(), CANDS, {"mode": "shadow"}, client=_client(payload))
        assert "error" not in review
        assert [(v["idx"], v["verdict"]) for v in review["verdicts"]] == [(0, "PASS"), (1, "FAIL")]

    def test_missed_as_plain_strings(self):
        payload = {"verdicts": [_v(0)], "missed": ["C6", "C3: evento forte", "lixo"]}
        review = fr.run_final_review(_content(), CANDS, {"mode": "shadow"}, client=_client(payload))
        assert "error" not in review
        assert [m["candidate"] for m in review["missed"]] == ["C6", "C3"]

    def test_string_entries_inside_verdicts_are_skipped(self):
        payload = {"verdicts": ["texto solto", _v(1, "FAIL", "opinion")], "missed": "nenhum"}
        review = fr.run_final_review(_content(), CANDS, {"mode": "shadow"}, client=_client(payload))
        assert "error" not in review and len(review["verdicts"]) == 1 and review["missed"] == []

    def test_non_object_response_reports_error_with_location_and_raw(self):
        review = fr.run_final_review(_content(), CANDS, {"mode": "shadow"}, client=_client("[1, 2]"))
        assert "ValueError" in review["error"] and "final_reviewer.py" in review["error"]
        assert review["raw_response"] == "[1, 2]"

    def test_reasoning_as_plain_string_does_not_break(self):
        content = _content()
        content["reasoning"] = "texto corrido em vez de objeto"
        review = fr.run_final_review(content, CANDS, {"mode": "shadow"}, client=_client({"verdicts": [_v(0)]}))
        assert "error" not in review and review["contradictions"] == []
