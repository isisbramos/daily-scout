"""Sinais novos do content_report: concentração de fonte por item e juiz × leitor."""

from content_report import aggregate_content, judge_vs_feedback


def _ed(n, sources, fb=None):
    items = [{"title": f"t{i}", "source": s} for i, s in enumerate(sources)]
    return {"edition": str(n), "main_find": items[0], "quick_finds": items[1:],
            "feedback_score": fb}


def test_flags_three_items_from_same_source():
    eds = [_ed(197, ["techcrunch", "techcrunch", "techcrunch", "scmp_tech"]),
           _ed(198, ["techcrunch", "scmp_tech", "hackernews"])]
    c = aggregate_content(eds, set())
    assert c["n_with_item_source"] == 2
    assert c["source_concentration"] == [{"edition": "197", "source": "techcrunch", "items": 3}]


def test_old_editions_without_item_source_are_ignored():
    c = aggregate_content([{"edition": "150", "main_find": {"title": "x"}, "quick_finds": []}], set())
    assert c["n_with_item_source"] == 0 and c["source_concentration"] == []


def test_judge_vs_feedback_pairs_and_skips_old_editions():
    fb = lambda avg: {"n": 3, "avg": avg}
    eds = [_ed(n, ["a"], fb(avg)) for n, avg in
           [(170, 0.5), (171, 0.8), (172, 1.0), (173, 1.5), (174, 2.0), (150, 2.0)]]
    audits = {str(n): {"overall_score": s} for n, s in
              [(170, 1), (171, 2), (172, 2), (173, 3), (174, 4), (150, 5)]}
    j = judge_vs_feedback(eds, audits)
    assert j["n_pairs"] == 5            # ed.150 (<169) fora
    assert j["avg_feedback_by_score"][2] == 0.9
    assert j["correlation"] > 0.9


def test_judge_vs_feedback_handles_missing_feedback():
    j = judge_vs_feedback([_ed(170, ["a"], None)], {"170": {"overall_score": 2}})
    assert j["n_pairs"] == 0 and j["correlation"] is None


def test_reviewer_vs_audit_agreement(tmp_path, monkeypatch):
    import json
    import content_report as cr
    monkeypatch.setattr(cr, "DEBUG_DIR", str(tmp_path))
    ed = {"edition": "200", "main_find": {"title": "Main"},
          "quick_finds": [{"title": "Funding X"}, {"title": "Bom"}]}
    (tmp_path / "edition_200_review.json").write_text(json.dumps({
        "mode": "shadow", "verdicts": [{"idx": 1, "verdict": "FAIL"}, {"idx": 2, "verdict": "PASS"}],
        "missed": [{}], "contradictions": []}), encoding="utf-8")
    audits = {"200": {"false_positives": [{"title": "Funding X"}, {"title": "Outro"}]}}
    r = cr.reviewer_vs_audit([ed], audits)
    assert (r["n"], r["review_fail"], r["audit_fp"], r["both"]) == (1, 1, 2, 1)


def test_reviewer_vs_audit_ignores_editions_without_review(tmp_path, monkeypatch):
    import content_report as cr
    monkeypatch.setattr(cr, "DEBUG_DIR", str(tmp_path))
    assert cr.reviewer_vs_audit([{"edition": "1", "main_find": {}}], {"1": {}})["rows"] == []
