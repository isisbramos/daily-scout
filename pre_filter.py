"""
Daily Scout — Pre-Filter Layer (v5)
Roda ANTES do Gemini: dedup, recency, scoring heurístico, token budget.
Garante que o LLM recebe input limpo e dentro do budget.

v5 changes:
  - Cross-source signal: dedup marca duplicatas com cross_source_count em vez de deletar
  - Z-score normalization: engagement comparável entre sources
  - Exponential recency decay: modela ciclo real de notícias
  - Wild card zone: 5 slots reservados para items aleatórios do pool descartado
  - RSS engagement usa mediana real das sources com dados
"""

import logging
import math
import random
import statistics
import time
from difflib import SequenceMatcher

from sources.base import SourceItem

logger = logging.getLogger("daily-scout")


def run_pre_filter(
    items: list[SourceItem],
    config: dict,
) -> list[SourceItem]:
    """
    Pipeline de pré-filtragem (v5):
    1. Dedup por URL exata
    2. Dedup por título similar (fuzzy) — marca cross-source signal
    3. Recency filter
    4. Scoring heurístico (z-score + exponential decay)
    5. Diversity enforcement
    6. Token budget trim + wild card zone
    """
    pf_config = config.get("pre_filter", {})

    logger.info(f"  Pre-filter input: {len(items)} items")

    # Step 1: URL dedup
    items = _dedup_by_url(items)
    logger.info(f"  After URL dedup: {len(items)}")

    # Step 2: Fuzzy title dedup — v5: marca cross-source em vez de deletar
    threshold = pf_config.get("dedup_similarity_threshold", 0.7)
    items = _dedup_by_title_with_cross_source(items, threshold)
    logger.info(f"  After title dedup (cross-source): {len(items)}")

    # Step 3: Recency filter
    recency_hours = pf_config.get("recency_hours", 24)
    fallback_min = pf_config.get("recency_fallback_min_items", 10)
    items = _filter_recency(items, recency_hours, fallback_min)
    logger.info(f"  After recency filter: {len(items)}")

    # Step 4: Score and sort (v5: z-score + exponential decay)
    items = _score_and_sort(items, config)
    logger.info(f"  After scoring: {len(items)} (sorted by composite score)")

    # Step 5: Diversity re-ranking
    max_source_pct = pf_config.get("max_per_source_pct", 0.25)
    items = _enforce_source_diversity(items, max_source_pct)
    logger.info(f"  After diversity enforcement: {len(items)}")

    # Step 5.2: Geographic cap — evita over-representation de qualquer região
    geo_max_pct = pf_config.get("geographic_max_pct", 0.30)
    source_region_map = _build_region_map(config)
    items = _enforce_geographic_cap(items, source_region_map, geo_max_pct)
    logger.info(f"  After geographic cap: {len(items)}")

    # Step 5.5: Epistemic diversity enforcement
    max_items = pf_config.get("max_items_to_llm", 40)
    items = _ensure_epistemic_diversity(items, top_n=max_items, min_per_type=3)
    logger.info(f"  After epistemic diversity enforcement: {len(items)}")

    # Step 6: Token budget trim + wild card zone
    wild_card_slots = pf_config.get("wild_card_slots", 5)
    items = _trim_with_wild_cards(items, max_items, wild_card_slots)
    logger.info(f"  After token budget trim (with wild cards): {len(items)}")

    # Step 7: Source diversity check
    _log_source_distribution(items)

    return items


def _normalize_url(url: str) -> str:
    """Normaliza URL pra dedup: strip protocol, www, tracking params, lowercase."""
    url = url.strip().rstrip("/")
    url = url.split("#")[0]
    url = url.split("?utm_")[0].split("?ref=")[0].split("?source=")[0].split("?via=")[0]
    url = url.rstrip("?").rstrip("/")
    for prefix in ("https://", "http://"):
        if url.lower().startswith(prefix):
            url = url[len(prefix):]
            break
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


def _dedup_by_title_with_cross_source(
    items: list[SourceItem], threshold: float = 0.7
) -> list[SourceItem]:
    """
    v5: Dedup que MARCA cross-source signal em vez de deletar.
    Quando o mesmo tema aparece em múltiplas sources, mantém a melhor versão
    mas registra cross_source_count e cross_source_ids.
    """
    unique: list[SourceItem] = []

    for item in items:
        title_lower = item.title.lower().strip()
        merged = False

        for i, existing in enumerate(unique):
            existing_lower = existing.title.lower().strip()
            ratio = SequenceMatcher(None, title_lower, existing_lower).ratio()
            if ratio >= threshold:
                # Cross-source signal: registra que múltiplas fontes cobriram o tema
                new_count = existing.cross_source_count + 1
                new_ids = list(existing.cross_source_ids)
                if item.source_id not in new_ids:
                    new_ids.append(item.source_id)
                if existing.source_id not in new_ids:
                    new_ids.append(existing.source_id)

                # Mantém o com maior engagement, mas preserva o cross-source signal
                if item.raw_score > existing.raw_score:
                    item.cross_source_count = new_count
                    item.cross_source_ids = new_ids
                    unique[i] = item
                else:
                    existing.cross_source_count = new_count
                    existing.cross_source_ids = new_ids

                merged = True
                break

        if not merged:
            item.cross_source_ids = [item.source_id]
            unique.append(item)

    # Log cross-source signals
    cross_items = [it for it in unique if it.cross_source_count > 1]
    if cross_items:
        for it in cross_items:
            logger.info(
                f"  [CROSS-SOURCE] '{it.title[:60]}...' "
                f"x{it.cross_source_count} sources: {it.cross_source_ids}"
            )

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
    v5 Scoring heurístico cross-source:
    - Z-score normalization para engagement (comparável entre sources)
    - Exponential recency decay (modela ciclo real de notícias)
    - Cross-source bonus
    - Source weight (do config)
    """
    scoring = config.get("scoring", {})
    sources_config = config.get("sources", {})
    engagement_w = scoring.get("engagement_weight", 0.4)
    recency_w = scoring.get("recency_weight", 0.3)
    source_w = scoring.get("source_diversity_weight", 0.2)
    category_w = scoring.get("category_weight", 0.1)
    decay_constant = scoring.get("recency_decay_constant", 8)

    now = time.time()

    # ── v5: Z-score normalization cross-source ──
    # Coleta todos os raw_scores > 0 (ignora RSS-only)
    all_scores = [item.raw_score for item in items if item.raw_score > 0]

    if len(all_scores) >= 2:
        scores_mean = statistics.mean(all_scores)
        scores_stdev = statistics.stdev(all_scores)
        if scores_stdev == 0:
            scores_stdev = 1.0
    else:
        scores_mean = 0
        scores_stdev = 1.0

    # Mediana real das sources com dados — usado como engagement neutro pro RSS
    rss_neutral = 0.5
    if all_scores:
        median_zscore = (statistics.median(all_scores) - scores_mean) / scores_stdev
        # Converte z-score pra [0, 1] usando sigmoid
        rss_neutral = 1 / (1 + math.exp(-median_zscore))
        logger.info(f"  RSS-only engagement set to median: {rss_neutral:.3f}")

    # Identifica RSS-only sources
    max_scores: dict[str, int] = {}
    for item in items:
        current_max = max_scores.get(item.source_id, 0)
        if item.raw_score > current_max:
            max_scores[item.source_id] = item.raw_score
    rss_only_sources: set[str] = {
        sid for sid, ms in max_scores.items() if ms == 0
    }
    if rss_only_sources:
        logger.debug(f"  RSS-only sources: {rss_only_sources}")

    # Conta items por source (pra diversity bonus)
    source_counts: dict[str, int] = {}
    for item in items:
        source_counts[item.source_id] = source_counts.get(item.source_id, 0) + 1
    total_items = len(items)

    scored_items: list[tuple[float, SourceItem]] = []

    for item in items:
        # ── Engagement: z-score → sigmoid [0, 1] ──
        if item.source_id in rss_only_sources:
            engagement_score = rss_neutral
        else:
            z = (item.raw_score - scores_mean) / scores_stdev if scores_stdev else 0
            engagement_score = 1 / (1 + math.exp(-z))  # sigmoid

        # ── Recency: exponential decay ──
        age_hours = max(0, (now - item.timestamp) / 3600) if item.timestamp else decay_constant * 2
        recency_score = math.exp(-age_hours / decay_constant)

        # ── Source weight do config ──
        source_weight = sources_config.get(item.source_id, {}).get("weight", 1.0)

        # ── Diversity bonus — sources com menos items ganham boost ──
        source_pct = source_counts.get(item.source_id, 1) / total_items
        diversity_score = 1.0 - source_pct

        # ── v5: Cross-source bonus ──
        # Items que aparecem em múltiplas sources ganham boost
        cross_bonus = 1.0 + (0.15 * (item.cross_source_count - 1))

        # ── Category (placeholder — futuro: usar categorias reais) ──
        category_score = 0.5

        # ── Composite score ──
        composite = (
            engagement_score * engagement_w
            + recency_score * recency_w
            + diversity_score * source_w
            + category_score * category_w
        ) * source_weight * cross_bonus

        scored_items.append((composite, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_items]


def _enforce_source_diversity(
    items: list[SourceItem], max_pct: float = 0.25
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

    by_source: dict[str, list[SourceItem]] = {}
    for item in items:
        by_source.setdefault(item.source_id, []).append(item)

    result: list[SourceItem] = []
    source_counts: dict[str, int] = {sid: 0 for sid in by_source}
    overflow: list[SourceItem] = []

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
                overflow.extend(queue)
                queue.clear()
        active_sources = next_round_sources

    result.extend(overflow)

    capped = {sid: c for sid, c in source_counts.items() if c >= max_per_source}
    if capped:
        logger.info(f"  Diversity cap applied: {capped} (max {max_per_source} per source)")

    return result


def _trim_with_wild_cards(
    items: list[SourceItem],
    max_items: int = 40,
    wild_card_slots: int = 5,
) -> list[SourceItem]:
    """
    v5: Token budget trim com wild card zone.
    Reserva `wild_card_slots` dos `max_items` para items aleatórios do pool
    descartado. Isso dá ao LLM chance de encontrar gems que o scoring perdeu
    — equivalente estatístico de exploration vs exploitation.
    """
    if len(items) <= max_items:
        return items

    # Top items pelo scoring
    main_slots = max_items - wild_card_slots
    top_items = items[:main_slots]

    # Pool descartado — candidatos a wild card
    discarded = items[main_slots:]

    # Seleciona wild cards aleatórios do pool
    actual_wild_cards = min(wild_card_slots, len(discarded))
    if actual_wild_cards > 0:
        wild_cards = random.sample(discarded, actual_wild_cards)
        logger.info(
            f"  Wild card zone: {actual_wild_cards} random items from "
            f"discarded pool ({len(discarded)} candidates)"
        )
        for wc in wild_cards:
            logger.info(f"    [WILD CARD] '{wc.title[:60]}...' (source: {wc.source_id})")
        top_items.extend(wild_cards)
    else:
        logger.info("  Wild card zone: no discarded items available")

    return top_items


def _infer_content_type(title: str) -> str:
    """Classifica o tipo epistêmico do item por palavras-chave no título."""
    text = title.lower()
    if any(w in text for w in [
        "paper", "research", "study", "benchmark", "dataset",
        "technical report", "findings", "survey", "experiment",
        "evaluation", "new study", "arxiv", "model weights",
    ]):
        return "pesquisa"
    if any(w in text for w in [
        "regulation", "law", "ban", "policy", "gdpr", "ai act",
        "antitrust", "compliance", "fine", "lawsuit", "investigation",
        "government", "congress", "senate", "court", "ruling",
        "ftc", "doj", "watchdog", "regulator", "regulação", "lei",
    ]):
        return "regulacao"
    return "produto"


def _ensure_epistemic_diversity(
    items: list[SourceItem],
    top_n: int = 40,
    min_per_type: int = 3,
) -> list[SourceItem]:
    """
    Garante representação mínima por tipo epistêmico antes do token budget trim.
    Infere content_type de todos os items e, se 'pesquisa' ou 'regulacao' estiverem
    sub-representadas no topo da lista, troca com items de menor score do mesmo tipo
    que estejam na cauda.
    """
    for item in items:
        if item.content_type == "outro":
            item.content_type = _infer_content_type(item.title)

    top = items[:top_n]
    rest = items[top_n:]

    type_counts: dict[str, int] = {}
    for item in top:
        type_counts[item.content_type] = type_counts.get(item.content_type, 0) + 1

    for ep_type in ("pesquisa", "regulacao"):
        deficit = min_per_type - type_counts.get(ep_type, 0)
        if deficit <= 0:
            continue
        candidates = [i for i in rest if i.content_type == ep_type][:deficit]
        if candidates:
            top.extend(candidates)
            for c in candidates:
                rest.remove(c)
            logger.info(
                f"  [EPISTEMIC] Pulled {len(candidates)} '{ep_type}' item(s) "
                f"to meet min {min_per_type} — deficit was {deficit}"
            )

    final_dist: dict[str, int] = {}
    for item in top:
        final_dist[item.content_type] = final_dist.get(item.content_type, 0) + 1
    logger.info(f"  Epistemic distribution (pre-LLM): {final_dist}")

    return top + rest


def _build_region_map(config: dict) -> dict[str, str]:
    """
    Constrói mapa source_id → region a partir do sources_config.
    Sources sem campo 'region' são mapeadas para 'default' (sem cap geográfico).
    """
    region_map: dict[str, str] = {}
    sources = config.get("sources", {})
    for source_id, source_cfg in sources.items():
        if source_id.startswith("_comment"):
            continue
        if isinstance(source_cfg, dict) and "region" in source_cfg:
            region_map[source_id] = source_cfg["region"]
        else:
            region_map[source_id] = "default"
    return region_map


def _enforce_geographic_cap(
    items: list[SourceItem],
    source_region_map: dict[str, str],
    max_pct: float = 0.30,
) -> list[SourceItem]:
    """
    Geographic cap: nenhuma região (exceto 'default') pode ter mais que max_pct
    dos items no batch. Items excedentes vão pro overflow (final da lista).

    Resolve o problema de China over-representation: mesmo que SCMP + TechNode
    passem pelo source cap individualmente, o cap regional os agrupa e limita
    a representação total da região 'asia'.

    Nota: cobre apenas items vindos de fontes com region explícita no config.
    Items de Reddit/HN sobre China não são afetados (source_id='reddit' → region='default').
    """
    if not items or max_pct >= 1.0:
        return items

    total = len(items)
    max_per_region = max(1, int(total * max_pct))

    region_counts: dict[str, int] = {}
    result: list[SourceItem] = []
    overflow: list[SourceItem] = []

    for item in items:
        region = source_region_map.get(item.source_id, "default")
        if region == "default":
            result.append(item)
            continue

        current = region_counts.get(region, 0)
        if current < max_per_region:
            result.append(item)
            region_counts[region] = current + 1
        else:
            overflow.append(item)

    capped = {r: c for r, c in region_counts.items() if c >= max_per_region}
    if capped:
        logger.info(
            f"  Geographic cap applied: {capped} (max {max_per_region} per region, "
            f"{len(overflow)} items moved to overflow)"
        )

    return result + overflow


def _log_source_distribution(items: list[SourceItem]) -> None:
    """Loga distribuição de sources no output filtrado."""
    dist: dict[str, int] = {}
    for item in items:
        dist[item.source_id] = dist.get(item.source_id, 0) + 1
    parts = [f"{sid}: {count}" for sid, count in sorted(dist.items())]
    logger.info(f"  Source distribution: {' | '.join(parts)}")

    # v5: Log cross-source items
    cross = [it for it in items if it.cross_source_count > 1]
    if cross:
        logger.info(f"  Cross-source items in output: {len(cross)}")
