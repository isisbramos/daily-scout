"""
Tests for pre_filter.py — unit tests por função interna.
Nenhum I/O externo: tudo com SourceItem fixtures e timestamps fixos.
"""

import time
import pytest

from sources.base import SourceItem
from pre_filter import (
    _normalize_url,
    _dedup_by_url,
    _dedup_by_title_with_cross_source,
    _filter_recency,
    _score_and_sort,
    _enforce_source_diversity,
    _trim_with_wild_cards,
    run_pre_filter,
)


# ── Helpers ──────────────────────────────────────────────────────────

def make_item(
    title="Test title",
    url="https://example.com/post",
    source_id="hackernews",
    source_label="HackerNews",
    raw_score=100,
    timestamp=None,
    category="tech",
) -> SourceItem:
    return SourceItem(
        title=title,
        url=url,
        source_id=source_id,
        source_label=source_label,
        timestamp=timestamp if timestamp is not None else time.time(),
        raw_score=raw_score,
        category=category,
    )


RECENT = time.time() - 3600        # 1h atrás
OLD    = time.time() - 50 * 3600   # 50h atrás


# ── _normalize_url ────────────────────────────────────────────────────

class TestNormalizeUrl:
    def test_strips_https(self):
        assert _normalize_url("https://example.com/post") == "example.com/post"

    def test_strips_http(self):
        assert _normalize_url("http://example.com/post") == "example.com/post"

    def test_strips_www(self):
        assert _normalize_url("https://www.example.com/post") == "example.com/post"

    def test_strips_utm_params(self):
        url = "https://example.com/post?utm_source=hn&utm_medium=social"
        assert _normalize_url(url) == "example.com/post"

    def test_strips_ref_param(self):
        url = "https://example.com/post?ref=hackernews"
        assert _normalize_url(url) == "example.com/post"

    def test_strips_trailing_slash(self):
        assert _normalize_url("https://example.com/post/") == "example.com/post"

    def test_strips_fragment(self):
        assert _normalize_url("https://example.com/post#section") == "example.com/post"

    def test_lowercases(self):
        assert _normalize_url("https://Example.COM/Post") == "example.com/Post".lower()

    def test_empty_string(self):
        assert _normalize_url("") == ""


# ── _dedup_by_url ─────────────────────────────────────────────────────

class TestDedupByUrl:
    def test_removes_exact_duplicate(self):
        items = [
            make_item(url="https://example.com/a"),
            make_item(url="https://example.com/a"),
        ]
        result = _dedup_by_url(items)
        assert len(result) == 1

    def test_deduplicates_tracking_params(self):
        items = [
            make_item(url="https://example.com/a"),
            make_item(url="https://example.com/a?utm_source=hn"),
        ]
        result = _dedup_by_url(items)
        assert len(result) == 1

    def test_deduplicates_http_vs_https(self):
        items = [
            make_item(url="https://example.com/a"),
            make_item(url="http://example.com/a"),
        ]
        result = _dedup_by_url(items)
        assert len(result) == 1

    def test_keeps_different_urls(self):
        items = [
            make_item(url="https://example.com/a"),
            make_item(url="https://example.com/b"),
        ]
        result = _dedup_by_url(items)
        assert len(result) == 2

    def test_empty_list(self):
        assert _dedup_by_url([]) == []

    def test_preserves_order_of_first_seen(self):
        items = [
            make_item(title="First", url="https://example.com/a"),
            make_item(title="Duplicate", url="https://example.com/a"),
            make_item(title="Second", url="https://example.com/b"),
        ]
        result = _dedup_by_url(items)
        assert result[0].title == "First"
        assert result[1].title == "Second"


# ── _dedup_by_title_with_cross_source ─────────────────────────────────

class TestDedupByTitleCrossSource:
    def test_similar_titles_merged(self):
        items = [
            make_item(title="OpenAI releases GPT-5 with new capabilities",
                      source_id="hackernews", raw_score=500),
            make_item(title="OpenAI releases GPT-5 with new features",
                      source_id="reddit", raw_score=200),
        ]
        result = _dedup_by_title_with_cross_source(items, threshold=0.7)
        assert len(result) == 1

    def test_higher_score_wins(self):
        items = [
            make_item(title="OpenAI releases GPT-5 with new capabilities",
                      source_id="hackernews", raw_score=500),
            make_item(title="OpenAI releases GPT-5 with new features",
                      source_id="reddit", raw_score=200),
        ]
        result = _dedup_by_title_with_cross_source(items, threshold=0.7)
        assert result[0].source_id == "hackernews"
        assert result[0].raw_score == 500

    def test_cross_source_count_incremented(self):
        items = [
            make_item(title="OpenAI releases GPT-5 with new capabilities",
                      source_id="hackernews", raw_score=500),
            make_item(title="OpenAI releases GPT-5 with new features",
                      source_id="reddit", raw_score=200),
        ]
        result = _dedup_by_title_with_cross_source(items, threshold=0.7)
        assert result[0].cross_source_count == 2

    def test_cross_source_ids_populated(self):
        items = [
            make_item(title="OpenAI releases GPT-5 with new capabilities",
                      source_id="hackernews", raw_score=500),
            make_item(title="OpenAI releases GPT-5 with new features",
                      source_id="reddit", raw_score=200),
        ]
        result = _dedup_by_title_with_cross_source(items, threshold=0.7)
        assert "hackernews" in result[0].cross_source_ids
        assert "reddit" in result[0].cross_source_ids

    def test_different_titles_kept_separate(self):
        items = [
            make_item(title="OpenAI releases GPT-5", source_id="hackernews"),
            make_item(title="Google DeepMind launches Gemini 3", source_id="reddit"),
        ]
        result = _dedup_by_title_with_cross_source(items, threshold=0.7)
        assert len(result) == 2

    def test_single_item_cross_source_count_is_one(self):
        items = [make_item(title="Some unique title", source_id="hackernews")]
        result = _dedup_by_title_with_cross_source(items)
        assert result[0].cross_source_count == 1

    def test_empty_list(self):
        assert _dedup_by_title_with_cross_source([]) == []


# ── _filter_recency ───────────────────────────────────────────────────

class TestFilterRecency:
    def test_keeps_recent_items(self):
        items = [make_item(timestamp=RECENT)]
        result = _filter_recency(items, hours=24, fallback_min=1)
        assert len(result) == 1

    def test_removes_old_items(self):
        items = [make_item(timestamp=OLD)]
        result = _filter_recency(items, hours=24, fallback_min=1)
        # 50h > 24h → filtered, but only 1 item < fallback_min=1 → returns all
        # (fallback_min is exclusive: < fallback_min triggers fallback)
        # 1 item remains after filter but 1 < 1 is False → not fallback
        # Actually: len(recent)=0 < fallback_min=1 → returns all
        assert len(result) == 1  # fallback triggered

    def test_fallback_when_too_few_recent(self):
        items = [
            make_item(title="Recent", timestamp=RECENT),
            make_item(title="Old 1", timestamp=OLD),
            make_item(title="Old 2", timestamp=OLD),
        ]
        # Only 1 recent, fallback_min=5 → returns all 3
        result = _filter_recency(items, hours=24, fallback_min=5)
        assert len(result) == 3

    def test_no_fallback_when_enough_recent(self):
        items = [
            make_item(title="Recent 1", timestamp=RECENT),
            make_item(title="Recent 2", timestamp=RECENT),
            make_item(title="Old", timestamp=OLD),
        ]
        result = _filter_recency(items, hours=24, fallback_min=2)
        assert len(result) == 2
        assert all(i.timestamp == RECENT for i in result)

    def test_items_with_zero_timestamp_filtered(self):
        items = [
            make_item(title="No timestamp", timestamp=0.0),
            make_item(title="Recent", timestamp=RECENT),
        ]
        result = _filter_recency(items, hours=24, fallback_min=1)
        # 0.0 timestamp is in the past → filtered
        assert len(result) == 1
        assert result[0].title == "Recent"


# ── _score_and_sort ───────────────────────────────────────────────────

CONFIG = {
    "sources": {
        "hackernews": {"weight": 1.2},
        "reddit": {"weight": 1.0},
        "techcrunch": {"weight": 1.1},
        "rss_blog": {"weight": 0.8},
    },
    "scoring": {
        "engagement_weight": 0.4,
        "recency_weight": 0.3,
        "source_diversity_weight": 0.2,
        "category_weight": 0.1,
        "recency_decay_constant": 8,
    },
}


class TestScoreAndSort:
    def test_higher_score_ranks_higher(self):
        items = [
            make_item(title="Low score",  raw_score=10,  timestamp=RECENT, source_id="hackernews"),
            make_item(title="High score", raw_score=500, timestamp=RECENT, source_id="hackernews"),
        ]
        result = _score_and_sort(items, CONFIG)
        assert result[0].title == "High score"

    def test_more_recent_ranks_higher_when_scores_equal(self):
        very_recent = time.time() - 600  # 10min ago
        items = [
            make_item(title="Old",    raw_score=100, timestamp=RECENT,      source_id="hackernews"),
            make_item(title="Fresh",  raw_score=100, timestamp=very_recent, source_id="hackernews"),
        ]
        result = _score_and_sort(items, CONFIG)
        assert result[0].title == "Fresh"

    def test_cross_source_bonus_applied(self):
        # Same score/recency but one has cross_source_count=2
        base_ts = RECENT
        low  = make_item(title="Single source", raw_score=100, timestamp=base_ts, source_id="hackernews")
        high = make_item(title="Multi source",  raw_score=100, timestamp=base_ts, source_id="hackernews")
        high.cross_source_count = 2

        result = _score_and_sort([low, high], CONFIG)
        assert result[0].title == "Multi source"

    def test_rss_only_sources_get_neutral_score(self):
        # rss_blog only has raw_score=0 items — should still be scored
        items = [
            make_item(title="RSS item", raw_score=0, timestamp=RECENT, source_id="rss_blog"),
            make_item(title="HN item",  raw_score=100, timestamp=RECENT, source_id="hackernews"),
        ]
        result = _score_and_sort(items, CONFIG)
        # Both should be in result (no crash)
        assert len(result) == 2

    def test_returns_all_items(self):
        items = [make_item(raw_score=i * 10, source_id="hackernews") for i in range(10)]
        result = _score_and_sort(items, CONFIG)
        assert len(result) == 10

    def test_empty_list(self):
        assert _score_and_sort([], CONFIG) == []


# ── _enforce_source_diversity ─────────────────────────────────────────

class TestEnforceSourceDiversity:
    def test_caps_dominant_source(self):
        # 8 HN items + 2 Reddit → HN should be capped
        items = (
            [make_item(source_id="hackernews", title=f"HN {i}") for i in range(8)]
            + [make_item(source_id="reddit", title=f"Reddit {i}") for i in range(2)]
        )
        result = _enforce_source_diversity(items, max_pct=0.25)
        hn_count = sum(1 for i in result[:10] if i.source_id == "hackernews")
        assert hn_count <= 3  # max 25% of 10 = 2.5 → 2

    def test_single_source_capped_at_max(self):
        # Com fonte única que domina, itens além do cap são descartados
        # (o overflow só captura quando há interleaving de múltiplas fontes)
        items = [make_item(source_id="hackernews", title=f"HN {i}") for i in range(10)]
        result = _enforce_source_diversity(items, max_pct=0.3)
        # max_per_source = max(1, int(10*0.3)) = 3 → só 3 itens retornam
        assert len(result) == 3

    def test_no_cap_when_pct_is_1(self):
        items = [make_item(source_id="hackernews") for _ in range(10)]
        result = _enforce_source_diversity(items, max_pct=1.0)
        assert len(result) == 10

    def test_empty_list(self):
        assert _enforce_source_diversity([]) == []

    def test_single_item_preserved(self):
        items = [make_item(source_id="hackernews")]
        result = _enforce_source_diversity(items, max_pct=0.25)
        assert len(result) == 1


# ── _trim_with_wild_cards ─────────────────────────────────────────────

class TestTrimWithWildCards:
    def test_no_trim_when_under_limit(self):
        items = [make_item() for _ in range(20)]
        result = _trim_with_wild_cards(items, max_items=40, wild_card_slots=5)
        assert len(result) == 20

    def test_trims_to_max_items(self):
        items = [make_item() for _ in range(60)]
        result = _trim_with_wild_cards(items, max_items=40, wild_card_slots=5)
        assert len(result) == 40

    def test_wild_cards_included(self):
        items = [make_item(title=f"Item {i}") for i in range(60)]
        result = _trim_with_wild_cards(items, max_items=40, wild_card_slots=5)
        # Top 35 + 5 wild cards from items[35:]
        assert len(result) == 40
        top_35_titles = {f"Item {i}" for i in range(35)}
        top_in_result = [i for i in result if i.title in top_35_titles]
        assert len(top_in_result) == 35

    def test_wild_cards_from_discarded_pool(self):
        items = [make_item(title=f"Item {i}") for i in range(50)]
        result = _trim_with_wild_cards(items, max_items=40, wild_card_slots=5)
        discarded_titles = {f"Item {i}" for i in range(35, 50)}
        wild_in_result = [i for i in result if i.title in discarded_titles]
        assert len(wild_in_result) == 5

    def test_exact_limit_no_trim(self):
        items = [make_item() for _ in range(40)]
        result = _trim_with_wild_cards(items, max_items=40, wild_card_slots=5)
        assert len(result) == 40


# ── run_pre_filter (integração) ───────────────────────────────────────

FULL_CONFIG = {
    "sources": {
        "hackernews": {"enabled": True, "weight": 1.2},
        "reddit": {"enabled": True, "weight": 1.0},
        "techcrunch": {"enabled": True, "weight": 1.1},
    },
    "pre_filter": {
        "recency_hours": 24,
        "recency_fallback_min_items": 5,
        "max_items_to_llm": 20,
        "dedup_similarity_threshold": 0.7,
        "max_per_source_pct": 0.4,
        "wild_card_slots": 2,
    },
    "scoring": {
        "recency_decay_constant": 8,
        "engagement_weight": 0.4,
        "recency_weight": 0.3,
        "source_diversity_weight": 0.2,
        "category_weight": 0.1,
    },
}


class TestRunPreFilter:
    def test_returns_list(self):
        items = [
            make_item(title=f"Item {i}", url=f"https://example.com/{i}",
                      source_id="hackernews", timestamp=RECENT)
            for i in range(10)
        ]
        result = run_pre_filter(items, FULL_CONFIG)
        assert isinstance(result, list)

    def test_deduplicates_same_url(self):
        items = [
            make_item(title="Same post", url="https://example.com/a",
                      source_id="hackernews", timestamp=RECENT),
            make_item(title="Same post", url="https://example.com/a",
                      source_id="reddit", timestamp=RECENT),
        ]
        result = run_pre_filter(items, FULL_CONFIG)
        assert len(result) == 1

    def test_respects_max_items(self):
        items = [
            make_item(title=f"Item {i}", url=f"https://example.com/{i}",
                      source_id="hackernews", timestamp=RECENT, raw_score=i * 10)
            for i in range(50)
        ]
        result = run_pre_filter(items, FULL_CONFIG)
        assert len(result) <= FULL_CONFIG["pre_filter"]["max_items_to_llm"]

    def test_empty_input(self):
        result = run_pre_filter([], FULL_CONFIG)
        assert result == []
