"""
Tests for memory_store.py::record_social_outcome — patch pós-hoc do outcome de
post social (ex.: LinkedIn) no editions.jsonl, mesmo padrão de feedback_join.py.
"""

import json

import memory_store


def _write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class TestBuildMemoryRecord:
    def test_social_field_starts_as_none(self):
        record = memory_store.build_memory_record("100", {"main_find": {"title": "t"}})
        assert record["social"] is None


class TestRecordSocialOutcome:
    def test_updates_matching_edition(self, tmp_path, monkeypatch):
        path = tmp_path / "editions.jsonl"
        _write_jsonl(path, [
            {"edition": "099", "social": None},
            {"edition": "100", "social": None},
            {"edition": "101", "social": None},
        ])
        monkeypatch.setattr(memory_store, "EDITIONS_PATH", str(path))

        outcome = {"status": "posted", "post_id": "urn:li:share:123", "content": {"linkedin_post": "texto"}}
        ok = memory_store.record_social_outcome("100", "linkedin", outcome)

        assert ok is True
        records = _read_jsonl(path)
        assert records[0]["social"] is None
        assert records[1]["social"] == {"linkedin": outcome}
        assert records[2]["social"] is None

    def test_preserves_other_platforms_already_recorded(self, tmp_path, monkeypatch):
        """Uma edição que já tem outcome de outra plataforma não pode perder o dado
        anterior quando uma nova plataforma é registrada (merge, não overwrite)."""
        path = tmp_path / "editions.jsonl"
        _write_jsonl(path, [
            {"edition": "100", "social": {"twitter": {"status": "posted"}}},
        ])
        monkeypatch.setattr(memory_store, "EDITIONS_PATH", str(path))

        memory_store.record_social_outcome("100", "linkedin", {"status": "posted"})

        records = _read_jsonl(path)
        assert records[0]["social"] == {
            "twitter": {"status": "posted"},
            "linkedin": {"status": "posted"},
        }

    def test_edition_not_found_returns_false(self, tmp_path, monkeypatch):
        path = tmp_path / "editions.jsonl"
        _write_jsonl(path, [{"edition": "100", "social": None}])
        monkeypatch.setattr(memory_store, "EDITIONS_PATH", str(path))

        ok = memory_store.record_social_outcome("999", "linkedin", {"status": "posted"})

        assert ok is False
        # Arquivo não foi tocado.
        assert _read_jsonl(path) == [{"edition": "100", "social": None}]

    def test_missing_file_returns_false_without_raising(self, tmp_path, monkeypatch):
        path = tmp_path / "does_not_exist.jsonl"
        monkeypatch.setattr(memory_store, "EDITIONS_PATH", str(path))

        ok = memory_store.record_social_outcome("100", "linkedin", {"status": "posted"})

        assert ok is False

    def test_corrupted_line_ignored_not_fatal(self, tmp_path, monkeypatch):
        path = tmp_path / "editions.jsonl"
        path.write_text('{"edition": "099", "social": null}\nnot valid json\n{"edition": "100", "social": null}\n')
        monkeypatch.setattr(memory_store, "EDITIONS_PATH", str(path))

        ok = memory_store.record_social_outcome("100", "linkedin", {"status": "posted"})

        assert ok is True
        records = _read_jsonl(path)
        assert len(records) == 2
        assert records[1]["social"] == {"linkedin": {"status": "posted"}}

    def test_atomic_write_no_tmp_file_left_behind(self, tmp_path, monkeypatch):
        path = tmp_path / "editions.jsonl"
        _write_jsonl(path, [{"edition": "100", "social": None}])
        monkeypatch.setattr(memory_store, "EDITIONS_PATH", str(path))

        memory_store.record_social_outcome("100", "linkedin", {"status": "posted"})

        assert not (tmp_path / "editions.jsonl.tmp").exists()


class TestSourcePerItem:
    def test_records_source_for_main_and_quick_finds(self):
        content = {
            "main_find": {"title": "m", "url": "https://a/1"},
            "quick_finds": [{"title": "q1", "url": "https://b/2"}, {"title": "q2", "url": "https://x/9"}],
        }
        idx = {"https://a/1": "techcrunch", "https://b/2": "scmp_tech"}
        record = memory_store.build_memory_record("197", content, idx)
        assert record["main_find"]["source"] == "techcrunch"
        assert [q["source"] for q in record["quick_finds"]] == ["scmp_tech", ""]

    def test_source_empty_without_index(self):
        record = memory_store.build_memory_record(
            "197", {"main_find": {"title": "m", "url": "https://a/1"}, "quick_finds": []}
        )
        assert record["main_find"]["source"] == ""


class TestMainFindBar:
    def _items(self, **kw):
        from sources.base import SourceItem
        return {u: SourceItem(title=u, url=u, source_id=sid, source_label=sid, cross_source_count=n)
                for u, (sid, n) in kw.items()}

    def test_uncorroborated_reddit_is_below_bar(self):
        items = self._items(r=("reddit", 1))
        assert "reddit" in memory_store.main_find_below_bar({"url": "r"}, items)

    def test_corroborated_reddit_passes(self):
        items = self._items(r=("reddit", 2))
        assert memory_store.main_find_below_bar({"url": "r"}, items) is None

    def test_other_sources_and_unknown_urls_pass(self):
        items = self._items(t=("techcrunch", 1))
        assert memory_store.main_find_below_bar({"url": "t"}, items) is None
        assert memory_store.main_find_below_bar({"url": "desconhecida"}, items) is None

    def test_eligible_quick_find_skips_reddit_and_repeats(self):
        items = self._items(a=("reddit", 1), b=("techcrunch", 1), c=("scmp_tech", 1))
        qfs = [{"url": "a", "entities": ["X"]},
               {"url": "b", "entities": ["OpenAI", "Nvidia"]},   # repete edição recente
               {"url": "c", "entities": ["Mistral"]}]
        recent = [{"edition": "196", "main_find": {"title": "m", "entities": ["OpenAI", "Nvidia"]},
                   "quick_finds": []}]
        assert memory_store.find_eligible_quick_find(qfs, items, recent) == 2
        assert memory_store.find_eligible_quick_find(qfs[:1], items, recent) is None


# ── Guard de repetição + exceção de follow-up ─────────────────────────

RECENT = [
    {"edition": "234",
     "main_find": {"title": "Alibaba abre preview do Qwen4-Max com janela de 1 milhão de tokens",
                   "entities": ["Alibaba", "Qwen4-Max"]},
     "quick_finds": []},
    {"edition": "235",
     "main_find": {"title": "Fireworks AI sofre ataque cibernético", "entities": ["Fireworks AI", "ataque"]},
     "quick_finds": [{"title": "Robin Li diz que a próxima fase da AI é organização inteligente",
                      "entities": ["Baidu", "Robin Li"]}]},
]


def _content(*quick_finds):
    return {"main_find": {"title": "Outro assunto", "entities": ["Apple", "China"]},
            "quick_finds": list(quick_finds)}


QWEN_FOLLOW_UP = {
    "title": "Alibaba lança o Qwen4-Max só como API fechada, 12 dias após prometer open source",
    "entities": ["Alibaba", "Qwen4-Max"],
    "follow_up": "prometeu open source e lançou só como API fechada",
}
ROBIN_FOLLOW_UP = {
    "title": "Robin Li alerta para bolha em IA: aplicações ficam atrás do gasto em infraestrutura",
    "entities": ["Baidu", "Robin Li"],
    "follow_up": "alerta de bolha por defasagem entre infraestrutura e aplicações",
}


class TestFollowUpExemptions:
    def _run(self, content):
        hits = memory_store.check_repetition(content, RECENT)
        return hits, memory_store.follow_up_exemptions(content, hits, RECENT)

    def test_repeat_without_follow_up_is_still_dropped(self):
        qf = {**QWEN_FOLLOW_UP, "follow_up": ""}
        hits, kept = self._run(_content(qf))
        assert [h["index"] for h in hits] == [0]
        assert kept == set()

    def test_follow_up_with_new_title_is_kept(self):
        _, kept = self._run(_content(QWEN_FOLLOW_UP))
        assert kept == {0}

    def test_follow_up_with_same_title_is_dropped(self):
        # mesma notícia reformulada: o campo follow_up não basta se o título repete a edição anterior
        qf = {**QWEN_FOLLOW_UP,
              "title": "Alibaba libera preview do Qwen4-Max com janela de 1 milhão de tokens"}
        _, kept = self._run(_content(qf))
        assert kept == set()

    def test_at_most_one_follow_up_per_edition(self):
        hits, kept = self._run(_content(QWEN_FOLLOW_UP, ROBIN_FOLLOW_UP))
        assert len(hits) == 2
        assert kept == {0}  # só o primeiro; o segundo segue removido

    def test_too_short_follow_up_does_not_count(self):
        qf = {**QWEN_FOLLOW_UP, "follow_up": "novo"}
        _, kept = self._run(_content(qf))
        assert kept == set()

    def test_main_find_is_never_exempted(self):
        content = {"main_find": {**QWEN_FOLLOW_UP}, "quick_finds": []}
        hits = memory_store.check_repetition(content, RECENT)
        assert [h["where"] for h in hits] == ["main_find"]
        assert memory_store.follow_up_exemptions(content, hits, RECENT) == set()

    def test_non_repeated_items_are_not_touched(self):
        clean = {"title": "NYC discute multar chatbots", "entities": ["Nova York", "chatbot"]}
        hits, kept = self._run(_content(clean))
        assert hits == [] and kept == set()


class TestMemoryBlockFollowUpRule:
    def test_block_explains_follow_up_contract(self):
        block = memory_store.format_memory_block(RECENT)
        assert "FOLLOW-UP" in block
        assert "follow_up" in block
        assert "nunca main_find" in block
