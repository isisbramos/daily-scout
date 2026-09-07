"""
HuggingFace Papers Source — busca via API JSON oficial (zero auth).

Não existe RSS oficial pra huggingface.co/papers (issue aberta há anos no
repo huggingface/blog, nunca implementada). A API JSON /api/daily_papers é
o endpoint que a própria página usa pra renderizar a lista — mais confiável
que depender de um scraper RSS não-oficial de terceiro.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

from sources.base import BaseSource, SourceItem, SourceRegistry

logger = logging.getLogger("daily-scout")

HF_PAPERS_API = "https://huggingface.co/api/daily_papers"


@SourceRegistry.register
class HuggingFacePapersSource(BaseSource):
    source_id = "huggingface_papers"
    source_name = "HuggingFace Papers"

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.limit = self.config.get("limit", 20)
        self.timeout = self.config.get("timeout", 15)
        self.api_url = self.config.get("api_url", HF_PAPERS_API)

    def fetch(self) -> list[SourceItem]:
        try:
            resp = requests.get(
                self.api_url,
                timeout=self.timeout,
                headers={"User-Agent": "Mozilla/5.0 (compatible; DailyScoutBot/1.0)"},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.debug(f"    HuggingFace Papers: fetch error — {e}")
            return []

        items = []
        for entry in data[:self.limit]:
            paper = entry.get("paper", {}) or {}
            title = entry.get("title") or paper.get("title", "")
            if not title:
                continue

            arxiv_id = paper.get("id", "")
            url = f"https://huggingface.co/papers/{arxiv_id}" if arxiv_id else ""

            # submittedOnDailyAt = quando entrou na lista "daily papers" da HF —
            # mais relevante pro pipeline que a data original de publicação no
            # arXiv (um paper de semanas atrás pode só hoje ganhar destaque).
            ts = _parse_iso(paper.get("submittedOnDailyAt")) or _parse_iso(entry.get("publishedAt"))

            items.append(SourceItem(
                title=title,
                url=url,
                source_id=self.source_id,
                source_label="HuggingFace Papers",
                timestamp=ts or 0.0,
                raw_score=paper.get("upvotes", 0) or 0,
                num_comments=entry.get("numComments", 0) or 0,
                category="ai",
                extra={"summary": entry.get("summary") or paper.get("summary", "")},
            ))

        logger.debug(f"    HuggingFace Papers: {len(items)} posts fetched")
        return items


def _parse_iso(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).timestamp()
    except ValueError:
        return None
