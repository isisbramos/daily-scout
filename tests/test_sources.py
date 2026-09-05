"""
Tests for sources/ — parsers com HTTP mockado via unittest.mock.
Nenhuma chamada de rede real: tudo com fixtures de resposta.
"""

import time
import calendar
from unittest.mock import patch, MagicMock
from email.utils import formatdate

import pytest
import requests

from sources.base import SourceItem, fetch_feed, DEFAULT_FEED_TIMEOUT
from sources.hackernews import HackerNewsSource, _guess_hn_category
from sources.reddit import RedditSource, _categorize_subreddit
from sources.lobsters import LobstersSource, _categorize_lobsters
from sources.techcrunch import TechCrunchSource, _categorize_tc
from sources.rss_generic import AnthropicBlogSource, _fetch_rss, _categorize_by_title


# ── Helpers ──────────────────────────────────────────────────────────

class MockEntry:
    """Simula feedparser entry: suporta .get() e ['key'] access."""
    def __init__(self, **kwargs):
        self._data = kwargs

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __getitem__(self, key):
        return self._data[key]


def make_rss_entry(title="Test Post", link="https://example.com/post",
                   published_parsed=None, tags=None):
    return MockEntry(
        title=title,
        link=link,
        published_parsed=published_parsed or time.gmtime(),
        tags=tags or [],
    )


def make_feed(entries):
    """Cria um feed de feedparser mockado."""
    feed = MagicMock()
    feed.entries = entries
    feed.bozo = False
    feed.bozo_exception = None
    return feed


# ── fetch_feed (helper compartilhado de sources/base.py) ──────────────

class TestFetchFeed:
    """Uma fonte lenta/fora do ar não pode travar o fetch_all_sources
    inteiro — fetch_feed existe pra garantir timeout explícito em toda
    chamada de RSS (feedparser.parse(url) sozinho não tem timeout)."""

    def test_passes_timeout_to_requests(self):
        with patch("sources.base.requests.get") as mock_get, \
             patch("sources.base.feedparser.parse") as mock_parse:
            mock_get.return_value = MagicMock(content=b"<rss></rss>")
            fetch_feed("https://example.com/feed", timeout=7)

        assert mock_get.call_args.kwargs["timeout"] == 7
        mock_parse.assert_called_once_with(b"<rss></rss>")

    def test_default_timeout_used_when_not_specified(self):
        with patch("sources.base.requests.get") as mock_get, \
             patch("sources.base.feedparser.parse"):
            mock_get.return_value = MagicMock(content=b"<rss></rss>")
            fetch_feed("https://example.com/feed")

        assert mock_get.call_args.kwargs["timeout"] == DEFAULT_FEED_TIMEOUT

    def test_http_error_propagates(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("500")

        with patch("sources.base.requests.get", return_value=mock_resp):
            with pytest.raises(requests.HTTPError):
                fetch_feed("https://example.com/feed")

    def test_timeout_propagates(self):
        with patch("sources.base.requests.get", side_effect=requests.Timeout("slow")):
            with pytest.raises(requests.Timeout):
                fetch_feed("https://example.com/feed")


# ── HackerNewsSource ──────────────────────────────────────────────────

class TestHackerNewsSource:
    def _mock_hn_responses(self, story_ids, stories):
        """Configura mock para topstories + itens individuais."""
        responses = []

        # Primeira resposta: lista de IDs
        top_resp = MagicMock()
        top_resp.raise_for_status = MagicMock()
        top_resp.json.return_value = story_ids

        responses.append(top_resp)

        # Respostas subsequentes: cada story
        for story in stories:
            sr = MagicMock()
            sr.status_code = 200
            sr.json.return_value = story
            responses.append(sr)

        return responses

    def test_fetch_returns_source_items(self):
        story_ids = [1, 2]
        stories = [
            {"title": "OpenAI launches new model", "url": "https://example.com/1",
             "score": 500, "time": int(time.time()), "descendants": 120},
            {"title": "Rust 2.0 released", "url": "https://example.com/2",
             "score": 200, "time": int(time.time()), "descendants": 45},
        ]

        with patch("sources.hackernews.requests.get") as mock_get:
            mock_get.side_effect = self._mock_hn_responses(story_ids, stories)
            source = HackerNewsSource({"limit": 2})
            items = source.fetch()

        assert len(items) == 2
        assert all(isinstance(i, SourceItem) for i in items)

    def test_fields_mapped_correctly(self):
        story_ids = [42]
        stories = [
            {"title": "Anthropic releases Claude 4",
             "url": "https://anthropic.com/blog/claude4",
             "score": 847, "time": 1700000000, "descendants": 230},
        ]

        with patch("sources.hackernews.requests.get") as mock_get:
            mock_get.side_effect = self._mock_hn_responses(story_ids, stories)
            source = HackerNewsSource({"limit": 1})
            items = source.fetch()

        item = items[0]
        assert item.title == "Anthropic releases Claude 4"
        assert item.url == "https://anthropic.com/blog/claude4"
        assert item.raw_score == 847
        assert item.timestamp == 1700000000.0
        assert item.num_comments == 230
        assert item.source_id == "hackernews"
        assert item.source_label == "HackerNews"

    def test_story_without_title_skipped(self):
        story_ids = [1, 2]
        stories = [
            {"title": "",    "url": "https://example.com/1", "score": 100, "time": int(time.time())},
            {"title": "OK",  "url": "https://example.com/2", "score": 200, "time": int(time.time())},
        ]

        with patch("sources.hackernews.requests.get") as mock_get:
            mock_get.side_effect = self._mock_hn_responses(story_ids, stories)
            source = HackerNewsSource({"limit": 2})
            items = source.fetch()

        assert len(items) == 1
        assert items[0].title == "OK"

    def test_failed_story_fetch_skipped(self):
        story_ids = [1, 2]

        top_resp = MagicMock()
        top_resp.raise_for_status = MagicMock()
        top_resp.json.return_value = story_ids

        bad_resp = MagicMock()
        bad_resp.status_code = 500  # falha

        good_resp = MagicMock()
        good_resp.status_code = 200
        good_resp.json.return_value = {
            "title": "Good story", "url": "https://example.com/2",
            "score": 100, "time": int(time.time()), "descendants": 10,
        }

        with patch("sources.hackernews.requests.get") as mock_get:
            mock_get.side_effect = [top_resp, bad_resp, good_resp]
            source = HackerNewsSource({"limit": 2})
            items = source.fetch()

        assert len(items) == 1
        assert items[0].title == "Good story"

    def test_respects_limit(self):
        story_ids = list(range(30))
        stories = [
            {"title": f"Story {i}", "url": f"https://example.com/{i}",
             "score": 100, "time": int(time.time()), "descendants": 10}
            for i in range(5)
        ]

        with patch("sources.hackernews.requests.get") as mock_get:
            mock_get.side_effect = self._mock_hn_responses(story_ids[:5], stories)
            source = HackerNewsSource({"limit": 5})
            items = source.fetch()

        assert len(items) == 5

    def test_safe_fetch_returns_empty_on_network_error(self):
        with patch("sources.hackernews.requests.get", side_effect=ConnectionError("timeout")):
            source = HackerNewsSource({"limit": 5})
            items = source.safe_fetch()
        assert items == []


class TestGuessHnCategory:
    def test_ai_keywords(self):
        story = {"title": "OpenAI releases new LLM", "url": ""}
        assert _guess_hn_category(story) == "ai"

    def test_startup_keywords(self):
        story = {"title": "YCombinator W24 batch announced", "url": ""}
        assert _guess_hn_category(story) == "startup"

    def test_opensource_keywords(self):
        story = {"title": "New open source tool for devs", "url": "github.com/something"}
        assert _guess_hn_category(story) == "opensource"

    def test_dev_keywords(self):
        story = {"title": "Rust 2.0 ships with async improvements", "url": ""}
        assert _guess_hn_category(story) == "dev"

    def test_default_tech(self):
        story = {"title": "Apple announces new iPad", "url": ""}
        assert _guess_hn_category(story) == "tech"


# ── RedditSource ──────────────────────────────────────────────────────

class TestRedditSource:
    def _make_reddit_entry(self, title, link, published_parsed=None):
        return MockEntry(
            title=title,
            link=link,
            published_parsed=published_parsed or time.gmtime(),
        )

    def test_fetch_returns_items(self):
        entries = [
            self._make_reddit_entry("GPT-5 discussion thread", "https://reddit.com/r/artificial/post1"),
            self._make_reddit_entry("Meta releases open model", "https://reddit.com/r/artificial/post2"),
        ]
        mock_feed = make_feed(entries)

        with patch("sources.reddit.fetch_feed", return_value=mock_feed):
            with patch("sources.reddit.time.sleep"):
                source = RedditSource({"subreddits": ["artificial"], "limit_per_sub": 10})
                items = source.fetch()

        assert len(items) == 2
        assert all(isinstance(i, SourceItem) for i in items)

    def test_source_label_includes_subreddit(self):
        entries = [self._make_reddit_entry("Some post", "https://reddit.com/post")]
        mock_feed = make_feed(entries)

        with patch("sources.reddit.fetch_feed", return_value=mock_feed):
            with patch("sources.reddit.time.sleep"):
                source = RedditSource({"subreddits": ["MachineLearning"], "limit_per_sub": 5})
                items = source.fetch()

        assert items[0].source_label == "r/MachineLearning"

    def test_source_id_is_reddit(self):
        entries = [self._make_reddit_entry("Test", "https://reddit.com/post")]
        mock_feed = make_feed(entries)

        with patch("sources.reddit.fetch_feed", return_value=mock_feed):
            with patch("sources.reddit.time.sleep"):
                source = RedditSource({"subreddits": ["artificial"], "limit_per_sub": 5})
                items = source.fetch()

        assert items[0].source_id == "reddit"

    def test_rss_score_is_zero(self):
        entries = [self._make_reddit_entry("Test", "https://reddit.com/post")]
        mock_feed = make_feed(entries)

        with patch("sources.reddit.fetch_feed", return_value=mock_feed):
            with patch("sources.reddit.time.sleep"):
                source = RedditSource({"subreddits": ["artificial"], "limit_per_sub": 5})
                items = source.fetch()

        assert items[0].raw_score == 0

    def test_broken_feed_skipped(self):
        broken_feed = MagicMock()
        broken_feed.bozo = True
        broken_feed.entries = []

        with patch("sources.reddit.fetch_feed", return_value=broken_feed):
            with patch("sources.reddit.time.sleep"):
                source = RedditSource({"subreddits": ["artificial"], "limit_per_sub": 5})
                items = source.fetch()

        assert items == []


class TestCategorizeSub:
    def test_ai_subreddits(self):
        for sub in ["artificial", "MachineLearning", "ChatGPT", "LocalLLaMA"]:
            assert _categorize_subreddit(sub) == "ai", f"Failed for {sub}"

    def test_dev_subreddits(self):
        assert _categorize_subreddit("programming") == "dev"
        assert _categorize_subreddit("compsci") == "dev"

    def test_startup_subreddits(self):
        assert _categorize_subreddit("startups") == "startup"
        assert _categorize_subreddit("SideProject") == "startup"

    def test_unknown_defaults_to_tech(self):
        assert _categorize_subreddit("unknownsubreddit") == "tech"


# ── LobstersSource ──────────────────────────────────────────────────

class TestLobstersSource:
    def _make_lobsters_entry(self, title="Test Post", link="https://example.com/post",
                              comments="https://lobste.rs/s/abc123", tags=None,
                              published_parsed=None):
        return MockEntry(
            title=title,
            link=link,
            comments=comments,
            tags=tags or [],
            published_parsed=published_parsed or time.gmtime(),
        )

    def test_fetch_maps_fields(self):
        entry = self._make_lobsters_entry(
            title="Formalizing Fermat's Last Theorem",
            link="https://blog.example.com/flt",
            comments="https://lobste.rs/s/xyz789",
            tags=[{"term": "math"}],
        )
        mock_feed = make_feed([entry])

        with patch("sources.lobsters.fetch_feed", return_value=mock_feed) as mock_fetch:
            source = LobstersSource({"rss_url": "https://lobste.rs/rss"})
            items = source.fetch()

        mock_fetch.assert_called_once_with("https://lobste.rs/rss")
        assert len(items) == 1
        item = items[0]
        assert item.title == "Formalizing Fermat's Last Theorem"
        assert item.url == "https://blog.example.com/flt"
        assert item.source_id == "lobsters"
        assert item.source_label == "Lobsters"
        assert item.raw_score == 0
        assert item.num_comments == 0

    def test_comments_url_kept_separate_from_article_url(self):
        """Lobsters distingue a URL do artigo (pode ser externa) da URL da
        discussão — o template usa extra['comments_url'] pro link de discussão."""
        entry = self._make_lobsters_entry(
            link="https://external-blog.com/post",
            comments="https://lobste.rs/s/abc123",
        )
        mock_feed = make_feed([entry])

        with patch("sources.lobsters.fetch_feed", return_value=mock_feed):
            source = LobstersSource()
            items = source.fetch()

        assert items[0].url == "https://external-blog.com/post"
        assert items[0].extra["comments_url"] == "https://lobste.rs/s/abc123"

    def test_tags_captured_in_extra(self):
        entry = self._make_lobsters_entry(tags=[{"term": "rust"}, {"term": "compilers"}])
        mock_feed = make_feed([entry])

        with patch("sources.lobsters.fetch_feed", return_value=mock_feed):
            source = LobstersSource()
            items = source.fetch()

        assert items[0].extra["tags"] == ["rust", "compilers"]

    def test_respects_limit(self):
        entries = [self._make_lobsters_entry(title=f"Post {i}") for i in range(10)]
        mock_feed = make_feed(entries)

        with patch("sources.lobsters.fetch_feed", return_value=mock_feed):
            source = LobstersSource({"limit": 3})
            items = source.fetch()

        assert len(items) == 3

    def test_timestamp_parsed_from_published(self):
        ts_struct = time.strptime("2024-01-15 10:00:00", "%Y-%m-%d %H:%M:%S")
        entry = self._make_lobsters_entry(published_parsed=ts_struct)
        mock_feed = make_feed([entry])

        with patch("sources.lobsters.fetch_feed", return_value=mock_feed):
            source = LobstersSource()
            items = source.fetch()

        assert items[0].timestamp == calendar.timegm(ts_struct)

    def test_broken_feed_raises(self):
        """Diferente de reddit/techcrunch/rss_generic, LobstersSource.fetch()
        levanta em vez de engolir — é safe_fetch() (BaseSource) quem degrada."""
        broken_feed = MagicMock()
        broken_feed.bozo = True
        broken_feed.bozo_exception = "malformed XML"
        broken_feed.entries = []

        with patch("sources.lobsters.fetch_feed", return_value=broken_feed):
            source = LobstersSource()
            with pytest.raises(RuntimeError, match="Lobsters RSS parse failed"):
                source.fetch()

    def test_safe_fetch_returns_empty_on_broken_feed(self):
        broken_feed = MagicMock()
        broken_feed.bozo = True
        broken_feed.bozo_exception = "malformed XML"
        broken_feed.entries = []

        with patch("sources.lobsters.fetch_feed", return_value=broken_feed):
            source = LobstersSource()
            items = source.safe_fetch()

        assert items == []

    def test_custom_rss_url_from_config(self):
        entry = self._make_lobsters_entry()
        mock_feed = make_feed([entry])

        with patch("sources.lobsters.fetch_feed", return_value=mock_feed) as mock_fetch:
            source = LobstersSource({"rss_url": "https://custom.example.com/rss"})
            source.fetch()

        mock_fetch.assert_called_once_with("https://custom.example.com/rss")


class TestCategorizeLobsters:
    def test_ai_keywords(self):
        assert _categorize_lobsters(["machine-learning"], "some title") == "ai"
        assert _categorize_lobsters([], "New LLM architecture released") == "ai"

    def test_dev_keywords(self):
        assert _categorize_lobsters(["rust"], "some title") == "dev"
        # Nota: "explained" contém "ai" como substring ("expl-AI-ned") — título
        # sem "ai" pra testar o branch "dev" isoladamente.
        assert _categorize_lobsters([], "New compiler techniques in Python") == "dev"

    def test_infra_keywords(self):
        assert _categorize_lobsters(["linux"], "some title") == "infra"
        assert _categorize_lobsters([], "Networking devops guide") == "infra"

    def test_opensource_keywords(self):
        assert _categorize_lobsters(["opensource"], "some title") == "opensource"

    def test_default_tech(self):
        assert _categorize_lobsters([], "Apple announces new product") == "tech"

    def test_ai_takes_priority_over_dev(self):
        # "ai" é checado antes de "rust"/"python" — tag com ambos cai em "ai"
        assert _categorize_lobsters(["rust", "ai"], "some title") == "ai"


# ── TechCrunchSource ──────────────────────────────────────────────────

class TestTechCrunchSource:
    def test_fetch_maps_fields(self):
        ts_struct = time.strptime("2024-01-15 10:00:00", "%Y-%m-%d %H:%M:%S")
        entry = MockEntry(
            title="OpenAI acquires startup for $500M",
            link="https://techcrunch.com/story/1",
            published_parsed=ts_struct,
            tags=[{"term": "Artificial Intelligence"}, {"term": "funding"}],
        )
        mock_feed = make_feed([entry])

        with patch("sources.techcrunch.fetch_feed", return_value=mock_feed):
            source = TechCrunchSource({"limit": 10, "feeds": {"main": "https://techcrunch.com/feed/"}})
            items = source.fetch()

        assert len(items) == 1
        item = items[0]
        assert item.title == "OpenAI acquires startup for $500M"
        assert item.source_id == "techcrunch"
        assert item.source_label == "TechCrunch"
        assert item.raw_score == 0

    def test_category_inferred_from_tags(self):
        # Tag "funding" triggers "startup" — no "ai" substring in title/tags
        entry = MockEntry(
            title="Company secured Series B capital",
            link="https://techcrunch.com/story",
            published_parsed=time.gmtime(),
            tags=[{"term": "funding"}, {"term": "series"}],
        )
        mock_feed = make_feed([entry])

        with patch("sources.techcrunch.fetch_feed", return_value=mock_feed):
            source = TechCrunchSource({"limit": 5, "feeds": {"main": "url"}})
            items = source.fetch()

        assert items[0].category == "startup"


class TestCategorizeTc:
    def test_ai_from_tags(self):
        assert _categorize_tc(["Artificial Intelligence"], "some title") == "ai"

    def test_ai_from_title(self):
        assert _categorize_tc([], "OpenAI releases new LLM model") == "ai"

    def test_startup_from_title(self):
        # Nota: títulos com "raises" contêm "ai" como substring ("r-AI-ses")
        # então o AI check dispara primeiro — usar título sem "ai"
        assert _categorize_tc([], "Company secured Series B funding") == "startup"

    def test_opensource_from_title(self):
        assert _categorize_tc([], "New open source project on GitHub") == "opensource"

    def test_default_tech(self):
        assert _categorize_tc([], "Apple announces new product") == "tech"


# ── AnthropicBlogSource (RSS Generic) ────────────────────────────────

class TestAnthropicBlogSource:
    def test_source_id_and_label(self):
        ts = time.strptime("2024-01-15 10:00:00", "%Y-%m-%d %H:%M:%S")
        entry = MockEntry(
            title="Claude 3 safety improvements",
            link="https://anthropic.com/blog/claude3",
            published_parsed=ts,
            tags=[],
        )
        mock_feed = make_feed([entry])

        with patch("sources.rss_generic.fetch_feed", return_value=mock_feed):
            source = AnthropicBlogSource({"limit": 5, "rss_url": "https://anthropic.com/feed"})
            items = source.fetch()

        assert items[0].source_id == "anthropic_blog"
        assert items[0].source_label == "Anthropic Blog"

    def test_disabled_source_returns_empty(self):
        source = AnthropicBlogSource({"enabled": False})
        items = source.safe_fetch()
        assert items == []

    def test_broken_feed_returns_empty(self):
        broken = MagicMock()
        broken.bozo = True
        broken.entries = []

        with patch("sources.rss_generic.fetch_feed", return_value=broken):
            source = AnthropicBlogSource({"limit": 5})
            items = source.fetch()

        assert items == []


class TestCategorizaByTitle:
    def test_ai_keyword_in_title(self):
        assert _categorize_by_title("OpenAI releases GPT-5", [], "tech") == "ai"

    def test_ai_from_categories(self):
        assert _categorize_by_title("Some post", ["machine learning"], "tech") == "ai"

    def test_funding_keyword(self):
        # "raises" contém "ai" como substring — usar título sem "ai" para testar startup
        assert _categorize_by_title("Company secured Series B funding", [], "tech") == "startup"

    def test_opensource_keyword(self):
        assert _categorize_by_title("Apache 2.0 license release", [], "tech") == "opensource"

    def test_regulation_keyword(self):
        # "EU AI Act" contém "ai" → categoria "ai" (AI check tem prioridade)
        assert _categorize_by_title("EU AI Act compliance update", [], "tech") == "ai"
        # Título sem "ai": usa "gdpr" para acionar "regulation"
        assert _categorize_by_title("EU GDPR compliance update", [], "tech") == "regulation"

    def test_default_returned_when_no_match(self):
        assert _categorize_by_title("Some random news", [], "ai") == "ai"
        assert _categorize_by_title("Some random news", [], "tech") == "tech"
