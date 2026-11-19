"""Trecho do texto do artigo para os itens do topo do pre-filter.

Sem isto o LLM escrevia o main_find só a partir do título (ed. 242, Gemini 4 Neon:
"nenhum desses pontos está no título"). O summary do feed (PR do summary) ajuda, mas
itens do HN e do Reddit não têm feed resumido, e muitos feeds trazem uma linha só.

Regras:
- Só os `top_n` primeiros itens do pre-filter (já vêm ordenados por score; os wild
  cards ficam no fim). Esses são os candidatos realistas a main_find.
- Falha aberta: timeout, erro HTTP, paywall ou página sem parágrafos → item segue sem
  trecho, com log. Nunca derruba a edição.
- Sem dependência nova: extração com html.parser da stdlib (parágrafos <p> fora de
  nav/header/footer/aside/script/style), com fallback para a meta description.
- O trecho é TEXTO DE TERCEIROS: contexto para o LLM, nunca instrução (o prompt diz isso).

Config em sources_config.json → "article_fetch":
  {"enabled": true, "top_n": 10, "max_chars": 1500, "timeout": 8, "max_workers": 5}
"""

from __future__ import annotations

import html
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests

from sources.base import SourceItem

logger = logging.getLogger(__name__)

DEFAULTS = {"enabled": False, "top_n": 10, "max_chars": 1500, "timeout": 8, "max_workers": 5}

USER_AGENT = "Mozilla/5.0 (compatible; DailyScoutBot/1.0)"

# Hosts onde buscar a página não traz texto útil: abstract já vem no summary
# (arXiv, HF Papers), discussão em vez de artigo (HN, Reddit, Lobsters) ou
# conteúdo que não é HTML legível (vídeo, X).
SKIP_HOSTS = (
    "arxiv.org", "huggingface.co", "news.ycombinator.com", "reddit.com",
    "lobste.rs", "youtube.com", "youtu.be", "x.com", "twitter.com",
)

MIN_PARAGRAPH_CHARS = 40
_SKIP_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form", "svg", "figure"}


class _ParagraphParser(HTMLParser):
    """Coleta o texto dos <p> fora de blocos de navegação e a meta description."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[str] = []
        self.meta_description = ""
        self._skip_depth = 0
        self._in_p = False
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag == "p" and not self._skip_depth:
            self._in_p = True
            self._buf = []
        elif tag == "meta" and not self.meta_description:
            a = {k.lower(): (v or "") for k, v in attrs}
            if a.get("name", "").lower() == "description" or a.get("property", "").lower() == "og:description":
                self.meta_description = a.get("content", "").strip()

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "p" and self._in_p:
            self._in_p = False
            text = " ".join("".join(self._buf).split())
            if len(text) >= MIN_PARAGRAPH_CHARS:
                self.paragraphs.append(text)

    def handle_data(self, data):
        if self._in_p and not self._skip_depth:
            self._buf.append(data)


def extract_text(page_html: str, max_chars: int) -> str:
    """Devolve os primeiros parágrafos do artigo (até max_chars) ou "" se não achar texto."""
    parser = _ParagraphParser()
    try:
        parser.feed(page_html)
    except Exception:  # HTML quebrado: usa o que já foi coletado
        pass
    parts = parser.paragraphs or ([parser.meta_description] if parser.meta_description else [])
    text = html.unescape(" ".join(parts))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:.") + "…"


def _should_skip(url: str) -> bool:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if not url.lower().startswith(("http://", "https://")):
        return True
    return any(host == h or host.endswith("." + h) for h in SKIP_HOSTS)


def fetch_excerpt(url: str, max_chars: int, timeout: int) -> str:
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    resp.raise_for_status()
    if "html" not in resp.headers.get("Content-Type", "html").lower():
        return ""
    return extract_text(resp.text, max_chars)


def enrich_with_excerpts(items: list[SourceItem], config: dict | None) -> dict:
    """Anexa extra["article_excerpt"] aos top_n itens. Muta os itens; devolve estatística."""
    cfg = {**DEFAULTS, **(config or {})}
    stats = {"enabled": bool(cfg["enabled"]), "tried": 0, "ok": 0, "skipped": 0, "failed": 0}
    if not cfg["enabled"]:
        return stats

    targets = []
    for item in items[: int(cfg["top_n"])]:
        if _should_skip(item.url):
            stats["skipped"] += 1
        else:
            targets.append(item)
    stats["tried"] = len(targets)

    def _one(item: SourceItem) -> tuple[SourceItem, str, str]:
        try:
            return item, fetch_excerpt(item.url, int(cfg["max_chars"]), int(cfg["timeout"])), ""
        except Exception as e:
            return item, "", f"{type(e).__name__}: {str(e)[:80]}"

    if targets:
        with ThreadPoolExecutor(max_workers=int(cfg["max_workers"])) as pool:
            for item, excerpt, err in pool.map(_one, targets):
                if excerpt:
                    item.extra = dict(item.extra or {}, article_excerpt=excerpt)
                    stats["ok"] += 1
                else:
                    stats["failed"] += 1
                    logger.info(f"  [EXCERPT] sem trecho: '{item.title[:60]}' {err}")

    logger.info(
        f"  Article excerpts: {stats['ok']}/{stats['tried']} ok, "
        f"{stats['failed']} sem texto, {stats['skipped']} pulados (host)"
    )
    return stats
