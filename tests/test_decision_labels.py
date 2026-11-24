"""Rótulo de decisão P/T/C: coleta de itens, chamada ao juiz (com cliente falso),
calibração e agregação no Content Report. Nenhum teste chama LLM."""

import json
import os
from types import SimpleNamespace

import pytest

import content_report as cr
import decision_labels as dl


def _client(*texts):
    """Cliente falso: devolve `texts` em sequência, um por chamada."""
    calls = iter(texts)

    def create(**kwargs):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=next(calls)))])

    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


CURATION = {
    "main_find": {"title": "Main", "body": "corpo"},
    "quick_finds": [{"title": "Q0", "signal": "sinal 0"}, {"title": "Q1", "signal": "sinal 1"}],
    "radar": [{"title": "R0", "why_watch": "vale acompanhar"}],
}


def test_collect_items_covers_main_quick_and_radar():
    items = dl.collect_items(CURATION)
    assert [i["field"] for i in items] == ["main_find", "quick_finds[0]", "quick_finds[1]", "radar[0]"]
    assert items[1]["text"] == "sinal 0" and items[3]["text"] == "vale acompanhar"


def test_label_items_merges_labels_by_idx():
    items = dl.collect_items(CURATION)
    out = dl.label_items(items, client=_client(json.dumps({"items": [
        {"idx": 0, "label": "P", "decision": "PM revisa fornecedor"},
        {"idx": 1, "label": "T", "decision": ""},
        {"idx": 2, "label": "C", "decision": ""},
        {"idx": 3, "label": "T", "decision": ""},
    ]})))
    assert [i["label"] for i in out] == ["P", "T", "C", "T"]
    assert out[0]["title"] == "Main" and out[0]["decision"] == "PM revisa fornecedor"


def test_label_items_retries_when_an_idx_is_missing():
    items = dl.collect_items(CURATION)[:2]
    partial = json.dumps({"items": [{"idx": 0, "label": "P"}]})
    full = json.dumps({"items": [{"idx": 0, "label": "P"}, {"idx": 1, "label": "C"}]})
    out = dl.label_items(items, client=_client(partial, full))
    assert [i["label"] for i in out] == ["P", "C"]


def test_label_items_rejects_label_outside_p_t_c():
    items = dl.collect_items(CURATION)[:1]
    bad = json.dumps({"items": [{"idx": 0, "label": "X"}]})
    with pytest.raises(ValueError):
        dl.label_items(items, client=_client(bad, bad, bad))


def test_save_labels_has_no_model_name(tmp_path, monkeypatch):
    monkeypatch.setattr(dl, "DEBUG_DIR", str(tmp_path))
    labeled = [{"field": "main_find", "title": "Main", "text": "x", "label": "P", "decision": "d"}]
    path = dl.save_labels("247", labeled, "curation")
    doc = json.load(open(path, encoding="utf-8"))
    assert doc["edition"] == "247" and doc["source"] == "curation"
    assert "model" not in json.dumps(doc).lower()  # o repo é público: nunca expor o modelo
    assert "text" not in doc["items"][0]


# ── Linha de base humana (#234–#247) ──────────────────────────────────
def _human():
    with open(dl.HUMAN_LABELS_PATH, encoding="utf-8") as f:
        return json.load(f)["labels"]


def test_human_baseline_is_locked():
    h = _human()
    flat = [r["label"] for rows in h.values() for r in rows]
    assert len(h) == 14 and len(flat) == 65
    assert (flat.count("P"), flat.count("T"), flat.count("C")) == (27, 20, 18)


def test_human_baseline_titles_match_edition_memory():
    mem = {}
    with open(dl.EDITIONS_PATH, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                mem[rec["edition"]] = [rec["main_find"]["title"]] + [q["title"] for q in rec["quick_finds"]]
    for ed, rows in _human().items():
        assert [r["title"] for r in rows] == mem[ed], f"títulos da #{ed} divergem do editions.jsonl"


def test_fewshot_examples_agree_with_human_labels():
    flat = {r["title"]: r["label"] for rows in _human().values() for r in rows}
    for title, label in dl.FEWSHOT.items():
        assert flat[title] == label


def test_calibrate_skips_fewshot_and_counts_disagreements():
    human = {"1": [{"title": "A", "label": "P"}, {"title": "B", "label": "T"},
                   {"title": next(iter(dl.FEWSHOT)), "label": "P"}]}
    judge = {"1": {"items": [{"title": "A", "label": "P"}, {"title": "B", "label": "C"},
                             {"title": next(iter(dl.FEWSHOT)), "label": "C"}]}}
    r = dl.calibrate(human, judge)
    assert (r["n"], r["agree"]) == (2, 1)
    assert r["confusion"]["T"]["C"] == 1
    assert r["disagreements"] == [("B", "T", "C")]


# ── Agregação no Content Report ───────────────────────────────────────
def _doc(*pairs):
    return {"items": [{"field": f, "title": "t", "label": l} for f, l in pairs]}


def test_aggregate_decision_counts_and_excludes_radar():
    labels = {
        "246": _doc(("main_find", "T"), ("quick_finds[0]", "T"), ("quick_finds[1]", "T"), ("radar[0]", "P")),
        "247": _doc(("main_find", "P"), ("quick_finds[0]", "P"), ("quick_finds[1]", "C")),
    }
    d = cr.aggregate_decision(labels)
    assert d["totals"] == {"P": 2, "T": 3, "C": 1} and d["n_items"] == 6
    assert d["radar"]["P"] == 1  # radar fica à parte
    assert d["lede"] == {"P": 1, "T": 1, "C": 0}
    assert d["editions_t_over"] == ["246"]
    assert d["pct_p"] == 33


def test_aggregate_decision_reproduces_baseline_from_human_labels():
    labels = {ed: {"items": [{"field": "main_find" if i == 0 else f"quick_finds[{i - 1}]", "label": r["label"]}
                             for i, r in enumerate(rows)]} for ed, rows in _human().items()}
    d = cr.aggregate_decision(labels)
    assert d["totals"] == {"P": 27, "T": 20, "C": 18}
    assert d["pct_p"] == 42 and d["lede"] == {"P": 11, "T": 2, "C": 1}


def test_decision_block_handles_empty_and_filled():
    assert "Nenhum rótulo" in "\n".join(cr._decision_block(None))
    d = cr.aggregate_decision({"247": _doc(("main_find", "P"), ("quick_finds[0]", "T"))})
    text = "\n".join(cr._decision_block(d))
    assert "## 2b. Relevância para PM" in text and "| #247 | 1 | 1 | 0 | P |" in text
    assert "hipótese" in text  # alvos de partida marcados como hipótese
