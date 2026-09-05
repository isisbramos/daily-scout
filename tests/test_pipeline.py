"""
Tests for pipeline.py::fetch_all_sources — fetch paralelo com graceful degradation.
"""

import time
from unittest.mock import patch

import pipeline
from sources.base import SourceItem


class FakeSource:
    """Stand-in de BaseSource: expõe só o que fetch_all_sources usa."""

    def __init__(self, source_id, items=None, delay=0.0, raises=None):
        self.source_id = source_id
        self._items = items or []
        self._delay = delay
        self._raises = raises

    def safe_fetch(self):
        time.sleep(self._delay)
        if self._raises:
            raise self._raises
        return self._items


class TestFetchAllSources:
    def test_aggregates_items_from_all_sources(self):
        fakes = [
            FakeSource("a", [SourceItem(title="t1", url="u1", source_id="a", source_label="A")]),
            FakeSource("b", [SourceItem(title="t2", url="u2", source_id="b", source_label="B")]),
        ]
        with patch("pipeline.SourceRegistry.create_sources", return_value=fakes):
            items = pipeline.fetch_all_sources({})

        assert len(items) == 2
        assert {i.source_id for i in items} == {"a", "b"}

    def test_runs_sources_concurrently(self):
        """Regressão: fetch sequencial de N fontes com delay soma os delays.
        Em paralelo, o tempo total fica perto de um único delay."""
        delay = 0.3
        fakes = [FakeSource(f"s{i}", delay=delay) for i in range(5)]

        with patch("pipeline.SourceRegistry.create_sources", return_value=fakes):
            start = time.time()
            pipeline.fetch_all_sources({})
            elapsed = time.time() - start

        assert elapsed < delay * len(fakes) * 0.6

    def test_one_source_erroring_does_not_drop_others(self):
        """safe_fetch() já não deveria deixar exceção escapar, mas se
        escapar (bug futuro em alguma source), as outras não podem sumir."""
        fakes = [
            FakeSource("ok1", [SourceItem(title="t1", url="u1", source_id="ok1", source_label="OK1")]),
            FakeSource("broken", raises=RuntimeError("boom")),
            FakeSource("ok2", [SourceItem(title="t2", url="u2", source_id="ok2", source_label="OK2")]),
        ]
        with patch("pipeline.SourceRegistry.create_sources", return_value=fakes):
            items = pipeline.fetch_all_sources({})

        assert {i.source_id for i in items} == {"ok1", "ok2"}

    def test_empty_sources_returns_empty_list(self):
        with patch("pipeline.SourceRegistry.create_sources", return_value=[]):
            items = pipeline.fetch_all_sources({})
        assert items == []
