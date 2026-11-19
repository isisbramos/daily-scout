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


class TestPromptEntry:
    def _item(self, **kw):
        base = dict(title="T", url="https://x/1", source_id="arxiv_ai", source_label="arXiv (CS.AI)")
        base.update(kw)
        return SourceItem(**base)

    def test_research_item_carries_truncated_summary(self):
        item = self._item(extra={"summary": "palavra " * 200})
        entry = pipeline._prompt_entry(item)
        assert entry["summary"].endswith("…")
        assert len(entry["summary"]) <= pipeline.PROMPT_SUMMARY_CHARS + 1

    def test_news_item_also_carries_summary(self):
        item = self._item(source_id="hackernews", source_label="HackerNews",
                          extra={"summary": "Preço por uso e limites do modelo."})
        assert pipeline._prompt_entry(item)["summary"] == "Preço por uso e limites do modelo."

    def test_item_without_summary_keeps_original_shape(self):
        entry = pipeline._prompt_entry(self._item(source_id="hackernews", source_label="HackerNews"))
        assert set(entry) == {"title", "source", "score", "comments", "url"}

    def test_cross_source_signal_still_included(self):
        item = self._item(cross_source_count=2, cross_source_ids=["arxiv_ai", "hackernews"])
        assert pipeline._prompt_entry(item)["also_trending_on"] == ["hackernews"]


class TestSanitizeRadar:
    def _src(self, url):
        return SourceItem(title="T", url=url, source_id="technode", source_label="TechNode")

    def test_item_without_url_is_dropped(self):
        radar = [{"title": "Sem link", "why_watch": "x"}]
        assert pipeline.sanitize_radar(radar, {}) == []

    def test_non_http_url_is_dropped(self):
        assert pipeline.sanitize_radar([{"title": "t", "url": "javascript:alert(1)"}], {}) == []

    def test_url_outside_input_is_dropped_when_input_known(self):
        known = {"https://technode.com/a": self._src("https://technode.com/a")}
        radar = [{"title": "Inventada", "url": "https://exemplo.com/inventada"}]
        assert pipeline.sanitize_radar(radar, known) == []

    def test_missing_display_url_and_source_are_filled(self):
        known = {"https://technode.com/a": self._src("https://technode.com/a")}
        out = pipeline.sanitize_radar([{"title": "ok", "why_watch": "w", "url": "https://technode.com/a/"}], known)
        assert out[0]["display_url"] == "technode.com/…"
        assert out[0]["source"] == "TechNode"

    def test_existing_fields_are_kept(self):
        known = {"https://technode.com/a": self._src("https://technode.com/a")}
        item = {"title": "ok", "url": "https://technode.com/a", "display_url": "tn/…", "source": "Outra"}
        out = pipeline.sanitize_radar([item], known)
        assert out[0]["display_url"] == "tn/…" and out[0]["source"] == "Outra"

    def test_without_input_map_only_url_presence_is_checked(self):
        out = pipeline.sanitize_radar([{"title": "ok", "url": "https://x.com/p"}], None)
        assert len(out) == 1
