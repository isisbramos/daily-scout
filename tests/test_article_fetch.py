"""article_fetch: trecho do artigo para os itens do topo (pós ed. 242)."""

from unittest.mock import MagicMock, patch

import article_fetch
import pipeline
from article_fetch import enrich_with_excerpts, extract_text
from sources.base import SourceItem

PAGE = """
<html><head><meta name="description" content="Meta do Neon."></head><body>
<nav><p>Menu menu menu menu menu menu menu menu menu menu</p></nav>
<article>
<p>Curto.</p>
<p>O Gemini 4 Neon custa US$ 0,10 por milhão de tokens de entrada na API.</p>
<p>O limite padrão é de 2.000 requisições por minuto &amp; os dados não treinam o modelo.</p>
</article>
<footer><p>Copyright Google LLC todos os direitos reservados aqui</p></footer>
<script>var p = "<p>não é texto</p>";</script>
</body></html>
"""


def _item(url="https://blog.google/neon", sid="deepmind_blog"):
    return SourceItem(title="Introducing Gemini 4 Neon", url=url, source_id=sid, source_label=sid)


def _resp(text=PAGE, ctype="text/html; charset=utf-8"):
    r = MagicMock()
    r.text, r.headers = text, {"Content-Type": ctype}
    r.raise_for_status.return_value = None
    return r


class TestExtractText:
    def test_keeps_article_paragraphs_and_drops_chrome(self):
        out = extract_text(PAGE, 1000)
        assert "US$ 0,10 por milhão" in out and "2.000 requisições" in out
        assert "& os dados" in out
        assert "Menu" not in out and "Copyright" not in out and "não é texto" not in out
        assert "Curto." not in out

    def test_falls_back_to_meta_description(self):
        assert extract_text('<meta property="og:description" content="Só a meta.">', 500) == "Só a meta."

    def test_truncates_at_word_boundary(self):
        out = extract_text(PAGE, 60)
        assert out.endswith("…") and len(out) <= 61

    def test_empty_page_returns_empty(self):
        assert extract_text("<html></html>", 500) == ""


class TestEnrich:
    def test_disabled_by_default_does_nothing(self):
        items = [_item()]
        with patch("article_fetch.requests.get") as get:
            stats = enrich_with_excerpts(items, None)
        get.assert_not_called()
        assert stats["enabled"] is False and "article_excerpt" not in items[0].extra

    def test_enriches_top_n_only(self):
        items = [_item(f"https://site{i}.com/a") for i in range(4)]
        with patch("article_fetch.requests.get", return_value=_resp()) as get:
            stats = enrich_with_excerpts(items, {"enabled": True, "top_n": 2})
        assert get.call_count == 2 and stats["ok"] == 2
        assert "article_excerpt" in items[0].extra and "article_excerpt" not in items[3].extra

    def test_skips_discussion_and_paper_hosts(self):
        items = [_item("https://news.ycombinator.com/item?id=1", "hackernews"),
                 _item("https://arxiv.org/abs/1", "arxiv_ai"),
                 _item("https://old.reddit.com/r/x", "reddit")]
        with patch("article_fetch.requests.get") as get:
            stats = enrich_with_excerpts(items, {"enabled": True})
        get.assert_not_called()
        assert stats["skipped"] == 3

    def test_fails_open_on_error_and_non_html(self):
        items = [_item("https://a.com/1"), _item("https://b.com/2")]
        def fake_get(url, **kw):
            if "a.com" in url:
                raise TimeoutError("lento")
            return _resp(ctype="application/pdf")
        with patch("article_fetch.requests.get", side_effect=fake_get):
            stats = enrich_with_excerpts(items, {"enabled": True})
        assert stats["failed"] == 2 and stats["ok"] == 0
        assert all("article_excerpt" not in i.extra for i in items)

    def test_keeps_existing_extra(self):
        it = _item()
        it.extra = {"summary": "do feed"}
        with patch("article_fetch.requests.get", return_value=_resp()):
            enrich_with_excerpts([it], {"enabled": True})
        assert it.extra["summary"] == "do feed" and "Neon custa" in it.extra["article_excerpt"]


class TestPipelineWiring:
    def test_prompt_entry_carries_excerpt(self):
        it = _item()
        it.extra = {"article_excerpt": "palavra " * 400}
        entry = pipeline._prompt_entry(it)
        assert entry["excerpt"].endswith("…")
        assert len(entry["excerpt"]) <= pipeline.PROMPT_EXCERPT_CHARS + 1

    def test_filter_items_calls_enrich_with_config(self):
        items = [_item()]
        with patch("pipeline.run_pre_filter", return_value=items), \
             patch("pipeline.enrich_with_excerpts") as enrich:
            out = pipeline.filter_items(items, {"article_fetch": {"enabled": True}})
        assert out == items
        enrich.assert_called_once_with(items, {"enabled": True})

    def test_config_has_article_fetch(self):
        cfg = pipeline.load_config()
        assert cfg["article_fetch"]["enabled"] is True
