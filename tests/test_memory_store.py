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
