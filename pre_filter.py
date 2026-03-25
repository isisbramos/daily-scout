"""
Daily Scout — Pre-Filter Layer
Roda ANTES do Gemini: dedup, recency, scoring heurístico, token budget.
Garante que o LLM recebe input limpo e dentro do budget.
"""

import logging
import time
from difflib import SequenceMatcher

from sources.base import SourceItem

logger = logging.getLogger("daily-scout")


def run_pre_filter(
    items: list[SourceItem],
    config: dict,
) -> list[SourceItem]:
    """
    Pipeline de pré-filtragem:
    1. Dedup por URL exata
    2. Dedup por título similar (fuzzy)
    3. Recency filter
    4. Scoring heurístico
    5. Token budget trim
    """
    pf_config = config.get("pre_filter", {})
    scoring_config = config.get("scoring", {})

    logger.info(f"  Pre-filter input: {len(items)} items")

    # Step 1: URL dedup
    items = _dedup_by_url(items)
    logger.info(f"  After URL dedup: {len(items)}")

    # Step 2: Fuzzy title dedup
    threshold = pf_config.get("dedup_similarity_threshold", 0.7)
    items = _dedup_by_title(items, threshold)
    logger.info(f"  After title dedup: {len(items)}")

    # Step 3: Recency filter
    recency_hours = pf_config.get("recency_hours", 24)
    fallback_min = pf_config.get("recency_fallback_min_items", 10)
    items = _filter_recency(items, recency_hours, fallback_min)
    logger.info(f"  After recency filter: {len(items)}")

    # Step 4: Score and sort
    items = _score_and_sort(items, config)
    logger.info(f"  After scoring: {len(items)} (sorted by composite score)")

    # Step 5: Diversity re-ranking — impede que uma source monopolize o output
    max_source_pct = pf_config.get("max_per_source_pct", 0.4)
    items = _enforce_source_diversity(items, max_source_pct)
    logger.info(f"  After diversity enforcement: {len(items)}")

    # Step 6: Token budget trim
    max_items = pf_config.get("max_items_to_llm", 60)
    if len(items) > max_items:
        items = items[:max_items]
        logger.info(f"  After token budget trim: {len(items)}")

    # Step 7: Source diversity check
    _log_source_distribution(items)

    return items


def _normalize_url(url: str) -> str:
    """Normaliza URL pra dedup: strip protocol, www, tracking params, lowercase."""
    url = url.strip().rstrip("/")
    # Remove fragment e tracking params
    url = url.split("#")[0]
    url = url.split("?utm_")[0].split("?ref=")[0].split("?source=")[0].split("?via=")[0]
    url = url.rstrip("?").rstrip("/")
    # Strip protocol
    for prefix in ("https://", "http://"):
        if url.lower().startswith(prefix):
            url = url[len(prefix):]
            break
    # Strip www
    if url.lower().startswith("www."):
        url = url[4:]
    return url.lower()


def _dedup_by_url(items: list[SourceItem]) -> list[SourceItem]:
    """Remove duplicatas exatas por URL (com normalização robusta)."""
    seen_urls: set[str] = set()
    unique = []
    for item in items:
        clean_url = _normalize_url(item.url)
        if clean_url and clean_url not in seen_urls:
            seen_urls.add(clean_url)
            unique.append(item)
    return unique


def _dedup_by_title(
    items: list[SourceItem], threshold: float = 0.7
) -> list[SourceItem]:
    """Remove duplicatas semânticas por similaridade de título (fuzzy matching)."""
    unique: list[SourceItem] = []

    for item in items:
        title_lower = item.title.lower().strip()
        is_dup = False
        for existing in unique:
            existing_lower = existing.title.lower().strip()
            ratio = SequenceMatcher(None, title_lower, existing_lower).ratio()
            if ratio >= threshold:
                # Mantém o que tem maior engagement
                if item.raw_score > existing.raw_score:
                    unique.remove(existing)
                    unique.append(item)
                is_dup = True
                break
        if not is_dup:
            unique.append(item)

    return unique


def _filter_recency(
    items: list[SourceItem], hours: int, fallback_min: int
) -> list[SourceItem]:
    """Filtra por recência. Se ficar com poucos, usa tudo."""
    cutoff = time.time() - (hours * 3600)
    recent = [i for i in items if i.timestamp > cutoff]

    if len(recent) < fallback_min:
        logger.info(
            f"  Recency filter: {len(recent)} < {fallback_min} min, using all {len(items)}"
        )
        return items
    return recent


def _score_and_sort(
    items: list[SourceItem], config: dict
) -> list[SourceItem]:
    """
    Scoring heurístico cross-source:
    - Engagement normalizado (raw_score relativo ao max da source)
    - Recency decay (mais recente = maior score)
    - Source weight (do config)
    """
    scoring = config.get("scoring", {})
    sources_config = config.get("sources", {})
    engagement_w = scoring.get("engagement_weight", 0.4)
    recency_w = scoring.get("recency_weight", 0.3)
    source_w = scoring.get("source_diversity_weight", 0.2)
    category_w = scoring.get("category_weight", 0.1)
    decay_hours = scoring.get("recency_decay_hours", 12)

    now = time.time()

    # Calcula max score por source (pra normalização)
    max_scores: dict[str, int] = {}
    for item in items:
        current_max = max_scores.get(item.source_id, 0)
        if item.raw_score > current_max:
            max_scores[item.source_id] = item.raw_score

    # Identifica RSS-only sources (max_score == 0 = sem dados de engagement)
    # Essas sources recebem engagement neutro (0.5) em vez de zero
    rss_only_sources: set[str] = {
        sid for sid, ms in max_scores.items() if ms == 0
    }
    if rss_only_sources:
        logger.debug(f"  RSS-only sources (engagement neutro): {rss_only_sources}")

    # Conta items por source (pra diversity bonus)
    source_counts: dict[str, int] = {}
    for item in items:
        source_counts[item.source_id] = source_counts.get(item.source_id, 0) + 1
    total_items = len(items)

    scored_items: list[tuple[float, SourceItem]] = []

    for item in items:
        # Engagement score normalizado [0, 1]
        # RSS-only sources (sem raw_score) recebem 0.5 (neutro)
        # pra não serem penalizadas vs sources com engagement data
        if item.source_id in rss_only_sources:
            engagement_score = 0.5
        else:
            max_s = max_scores.get(item.source_id, 1) or 1
            engagement_score = item.raw_score / max_s

        # Recency score [0, 1] — decay exponencial
        age_hours = max(0, (now - item.timestamp) / 3600) if item.timestamp else decay_hours
        recency_score = max(0, 1.0 - (age_hours / (decay_hours * 2)))

        # Source weight do config
        source_weight = sources_config.get(item.source_id, {}).get("weight", 1.0)

        # Diversity bonus — sources com menos items ganham boost
        source_pct = source_counts.get(item.source_id, 1) / total_items
        diversity_score = 1.0 - source_pct  # Menos representada = maior bonus

        # Composite score
        composite = (
            engagement_score * engagement_w
            + recency_score * recency_w
            + diversity_score * source_w
            + (0.5 * category_w)  # Category neutral por agora
        ) * source_weight

        scored_items.append((composite, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_items]


def _enforce_source_diversity(
    items: list[SourceItem], max_pct: float = 0.4
) -> list[SourceItem]:
    """
    Diversity re-ranking: nenhuma source pode ter mais que max_pct do output.
    Items excedentes vão pro final da lista (não são removidos).
    Usa round-robin interleaving pra garantir representação de todas as sources.
    """
    if not items or max_pct >= 1.0:
        return items

    total = len(items)
    max_per_source = max(1, int(total * max_pct))

    # Separa items por source, mantendo a ordem do scoring
    by_source: dict[str, list[SourceItem]] = {}
    for item in items:
        by_source.setdefault(item.source_id, []).append(item)

    # Round-robin: pega items alternando entre sources
    result: list[SourceItem] = []
    source_counts: dict[str, int] = {sid: 0 for sid in by_source}
    overflow: list[SourceItem] = []

    # Primeiro pass: interleave com cap
    source_queues = {sid: list(items_list) for sid, items_list in by_source.items()}
    active_sources = list(source_queues.keys())

    while active_sources:
        next_round_sources = []
        for sid in active_sources:
            queue = source_queues[sid]
            if not queue:
                continue
            item = queue.pop(0)
            if source_counts[sid] < max_per_source:
                result.append(item)
                source_counts[sid] += 1
                if queue and source_counts[sid] < max_per_source:
                    next_round_sources.append(sid)
            else:
                overflow.append(item)
                # Drain remaining
                overflow.extend(queue)
                queue.clear()
        active_sources = next_round_sources

    # Overflow vai pro final (ainda disponível pro Gemini, mas com menor prioridade)
    result.extend(overflow)

    capped = {sid: c for sid, c in source_counts.items() if c >= max_per_source}
    if capped:
        logger.info(f"  Diversity cap applied: {capped} (max {max_per_source} per source)")

    return result


def _log_source_distribution(items: list[SourceItem]) -> None:
    """Loga distribuição de sources no output filtrado."""
    dist: dict[str, int] = {}
    for item in items:
        dist[item.source_id] = dist.get(item.source_id, 0) + 1
    parts = [f"{sid}: {count}" for sid, count in sorted(dist.items())]
    logger.info(f"  Source distribution: {' | '.join(parts)}")
