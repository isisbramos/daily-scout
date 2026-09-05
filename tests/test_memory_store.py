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
