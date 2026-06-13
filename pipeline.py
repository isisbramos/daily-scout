"""
Daily Scout — Pipeline v5.3 (Multi-Source Architecture + Observability)
Correspondente: AYA (AI-powered field correspondent)
Stack: 10 Sources (Reddit, HN, TechCrunch, Lobsters, RSS/blogs) → Pre-Filter → Gemini 2.5 Flash → Jinja2 → Buttondown API

Arquitetura:
  sources/ (pluggable modules) → pre_filter.py → Gemini curadoria → Jinja2 render → Buttondown delivery
  Config-driven: sources_config.json controla tudo sem mudar código.
"""

from __future__ import annotations

import os
import random
import re
import sys
import json
import time
import logging
from collections import Counter
from datetime import datetime, timezone, timedelta
from jinja2 import Environment, FileSystemLoader

from sources.base import SourceRegistry, SourceItem
# Importar sources registra elas automaticamente no registry
import sources.reddit
import sources.hackernews
import sources.techcrunch
import sources.lobsters
import sources.rss_generic  # v5: AI lab blogs + geographic diversity sources
from pre_filter import run_pre_filter
from schemas import Reasoning, MainFind, QuickFind, RadarItem, Meta, CurationOutput
from delivery import send_via_buttondown, send_fallback
from exceptions import FetchError, CurationError, DeliveryError

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("daily-scout")

# ── Config ───────────────────────────────────────────────────────────
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
BUTTONDOWN_API_KEY = os.environ.get("BUTTONDOWN_API_KEY")
EDITION_NUMBER = os.environ.get("EDITION_NUMBER", "001")
FEEDBACK_BASE_URL = os.environ.get(
    "FEEDBACK_BASE_URL",
    "https://isisbramos.github.io/daily-scout/feedback.html",
)
AYA_AVATAR_URL = os.environ.get(
    "AYA_AVATAR_URL",
    "https://raw.githubusercontent.com/isisbramos/daily-scout/main/aya-avatar.png",
)
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
SOCIAL_ENABLED = os.environ.get("SOCIAL_ENABLED", "false").lower() == "true"
# DEBUG_SAVE=true → salva curation output + pre-filter items em debug/ para o audit agent
DEBUG_SAVE = os.environ.get("DEBUG_SAVE", "false").lower() == "true"


def load_config() -> dict:
    """Carrega sources_config.json. Fallback pra defaults se não existir."""
    config_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "sources_config.json"),
        "sources_config.json",
    ]
    for path in config_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
            logger.info(f"Config loaded: {path}")
            return config

    logger.warning("sources_config.json not found — using defaults")
    return {
        "sources": {
            "reddit": {"enabled": True, "weight": 1.0},
            "hackernews": {"enabled": True, "weight": 1.2},
        },
        "pre_filter": {"max_items_to_llm": 40},
        "scoring": {},
    }


# ── Fetch: all sources (config-driven) ──────────────────────────────
def fetch_all_sources(config: dict) -> list[SourceItem]:
    """Instancia sources do config e faz fetch com graceful degradation."""
    logger.info("=" * 50)
    logger.info("PHASE 1: FETCH — collecting from all sources")
    logger.info("=" * 50)

    sources = SourceRegistry.create_sources(config)
    logger.info(f"Active sources: {[s.source_id for s in sources]}")

    all_items: list[SourceItem] = []
    source_stats: dict[str, int] = {}

    for source in sources:
        items = source.safe_fetch()
        source_stats[source.source_id] = len(items)
        all_items.extend(items)

    logger.info(f"Total raw items: {len(all_items)}")
    for sid, count in source_stats.items():
        logger.info(f"  {sid}: {count}")

    return all_items


# ── Pre-Filter ──────────────────────────────────────────────────────
def filter_items(items: list[SourceItem], config: dict) -> list[SourceItem]:
    """Aplica pre-filter layer: dedup, recency, scoring, token budget."""
    logger.info("=" * 50)
    logger.info("PHASE 2: PRE-FILTER — dedup, score, trim")
    logger.info("=" * 50)

    return run_pre_filter(items, config)


# ── Curate & Write: Gemini (structured output + anti-hallucination) ──
# Schemas importados de schemas.py

# ── Prompts: carregados de arquivos em prompts/ ──────────────────────
def _load_prompts() -> tuple[str, str]:
    """Carrega system instruction e curation template de arquivos de texto.
    Facilita iteração no prompt sem risco de quebrar sintaxe Python."""
    base = os.path.dirname(os.path.abspath(__file__))
    prompts_dir = os.path.join(base, "prompts")

    with open(os.path.join(prompts_dir, "system_instruction.txt"), encoding="utf-8") as f:
        system = f.read().rstrip("\n")

    with open(os.path.join(prompts_dir, "curation_template.txt"), encoding="utf-8") as f:
        template = f.read()

    return system, template


# Nota: {context_block} é injetado em runtime por curate_and_write()
# O template termina com "POSTS COLETADOS:\n" — o JSON é anexado em curate_and_write()
SYSTEM_INSTRUCTION, CURATION_PROMPT_TEMPLATE = _load_prompts()


# ── Startup: validação de env vars ───────────────────────────────────
def _validate_env() -> None:
    """Valida env vars obrigatórias antes de iniciar qualquer fase. Fail fast."""
    missing = []
    if not DEEPSEEK_API_KEY:
        missing.append("DEEPSEEK_API_KEY")
    if not DRY_RUN and not BUTTONDOWN_API_KEY:
        missing.append("BUTTONDOWN_API_KEY")
    if missing:
        logger.error(f"ABORT: env vars obrigatórias ausentes: {', '.join(missing)}")
        sys.exit(1)
    logger.info(f"Env vars OK (DRY_RUN={DRY_RUN})")


# ── Heurísticas anti-hallucination (pós-processamento) ───────────────
HYPE_PATTERNS = re.compile(
    r"(revolucion|bombástic|game.?changer|disruptiv|choque|chocou|impressionant[e]|"
    r"massiv[oa]|enorme[s]?|pesad[oa]|ousad[oa]|incrível|surpreendent[e]|"
    r"grande alarde|aposta pesada|mudou o jogo|pegou .+ de surpresa|"
    r"reviravolta|prometendo revolucionar|muito mais atraente|"
    r"pode mudar o cenário|entrand[oa] pesado)",
    re.IGNORECASE,
)


def validate_tone(content: dict) -> list[str]:
    """Checa heurísticas de sensacionalismo no output. Retorna lista de warnings."""
    warnings = []

    def _check_text(text: str, field_name: str):
        matches = HYPE_PATTERNS.findall(text)
        for match in matches:
            warnings.append(f"[HYPE] '{match}' encontrado em {field_name}")

    # Checa main_find
    mf = content.get("main_find", {})
    _check_text(mf.get("title", ""), "main_find.title")
    _check_text(mf.get("body", ""), "main_find.body")
    for i, bullet in enumerate(mf.get("bullets", [])):
        _check_text(bullet, f"main_find.bullets[{i}]")

    # Checa quick_finds
    for i, qf in enumerate(content.get("quick_finds", [])):
        _check_text(qf.get("title", ""), f"quick_finds[{i}].title")
        _check_text(qf.get("signal", ""), f"quick_finds[{i}].signal")

    # Checa correspondent_intro
    _check_text(content.get("correspondent_intro", ""), "correspondent_intro")

    return warnings


def curate_and_write(
    filtered_items: list[SourceItem],
    raw_count: int = 0,
    source_breakdown: dict[str, int] | None = None,
    max_retries: int = 5,
) -> dict:
    """Envia items pré-filtrados para o Gemini e recebe curadoria estruturada (v5).

    v5 changes:
    - Shuffle dos items para remover position bias
    - Context injection: AYA sabe quantos items existiam originalmente
    - Reasoning schema para observability
    """
    from openai import OpenAI

    logger.info("=" * 50)
    logger.info("PHASE 3: CURATE — DeepSeek processing (v5)")
    logger.info("=" * 50)

    if not DEEPSEEK_API_KEY:
        raise ValueError("DEEPSEEK_API_KEY não configurada")

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

    # ── v5: Shuffle para remover position bias ──
    # O pre-filter já selecionou os top N; a ordem interna não carrega
    # informação útil mas carrega viés (primacy effect no LLM).
    shuffled_items = list(filtered_items)
    random.shuffle(shuffled_items)
    logger.info(f"Shuffled {len(shuffled_items)} items to remove position bias")

    # Prepara input normalizado (com source info + v5: cross-source signal)
    items_for_prompt = []
    for item in shuffled_items:
        entry = {
            "title": item.title[:200],
            "source": item.source_label,
            "score": item.raw_score,
            "comments": item.num_comments,
            "url": item.url,
        }
        # v5: inclui cross-source signal quando item apareceu em múltiplas fontes
        if item.cross_source_count > 1:
            entry["also_trending_on"] = [
                sid for sid in item.cross_source_ids if sid != item.source_id
            ]
        items_for_prompt.append(entry)

    # ── v5: Context injection — AYA sabe o que existia antes do pre-filter ──
    source_counts = Counter(item.source_id for item in shuffled_items)
    sources_in_input = ", ".join(f"{sid} ({cnt})" for sid, cnt in source_counts.items())

    if raw_count and source_breakdown:
        breakdown_str = ", ".join(f"{sid}: {cnt}" for sid, cnt in source_breakdown.items())
        context_block = (
            f"CONTEXTO DO DIA: O pipeline coletou {raw_count} posts de "
            f"{len(source_breakdown)} fontes ({breakdown_str}). "
            f"Após pré-filtragem automática, você está recebendo os {len(shuffled_items)} "
            f"mais relevantes: {sources_in_input}. "
            f"Use o valor {raw_count} como total_analyzed no meta."
        )
    else:
        context_block = (
            f"CONTEXTO DO DIA: Você está recebendo {len(shuffled_items)} posts "
            f"pré-filtrados de: {sources_in_input}."
        )

    user_prompt = CURATION_PROMPT_TEMPLATE.format(
        context_block=context_block
    ) + json.dumps(items_for_prompt, ensure_ascii=False, indent=2)

    for attempt in range(max_retries):
        try:
            logger.info(f"DeepSeek attempt {attempt + 1}/{max_retries}...")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION + "\n\nRetorne sempre um JSON válido."},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=16384,
            )

            # ── v5.2: Detecta truncação antes de tentar parse ──
            finish_reason = response.choices[0].finish_reason if response.choices else None

            text = (response.choices[0].message.content or "").strip()
            logger.info(f"DeepSeek returned {len(text)} chars (finish_reason={finish_reason})")

            if finish_reason and finish_reason not in ("stop", None):
                raise ValueError(
                    f"DeepSeek output truncated (finish_reason={finish_reason}, "
                    f"{len(text)} chars) — likely hit max_tokens"
                )

            content = json.loads(text)
            if isinstance(content, str):
                content = json.loads(content)

            # Validação mínima de estrutura
            if "main_find" not in content:
                raise ValueError("JSON sem 'main_find'")
            if "title" not in content["main_find"]:
                raise ValueError("main_find sem 'title'")

            # Garante campos obrigatórios com defaults
            mf = content["main_find"]
            mf.setdefault("body", "")
            mf.setdefault("bullets", [])
            mf.setdefault("url", "")
            mf.setdefault("display_url", "")
            mf.setdefault("source", "")

            for qf in content.get("quick_finds", []):
                qf.setdefault("signal", "")
                qf.setdefault("url", "")
                qf.setdefault("display_url", "")
                qf.setdefault("source", "")

            # Validação: quick_finds não pode estar vazio (mas aceita na última tentativa)
            if not content.get("quick_finds"):
                if attempt < max_retries - 1:
                    raise ValueError("DeepSeek returned empty quick_finds — retrying")
                else:
                    logger.warning("Last attempt: accepting response without quick_finds")
                    content["quick_finds"] = []

            # ── Tone validation (post-processing) ──
            tone_warnings = validate_tone(content)
            if tone_warnings:
                for w in tone_warnings:
                    logger.warning(w)
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Tone check failed with {len(tone_warnings)} issues — retrying "
                        f"(attempt {attempt + 1})"
                    )
                    time.sleep(2**attempt)
                    continue
                else:
                    logger.warning(
                        f"Last attempt: accepting with {len(tone_warnings)} tone warnings"
                    )

            # ── v5: Log reasoning para observability ──
            reasoning = content.get("reasoning", {})
            if isinstance(reasoning, str):
                try:
                    reasoning = json.loads(reasoning)
                except Exception:
                    reasoning = {}
            if reasoning and isinstance(reasoning, dict):
                passed = reasoning.get("ai_gate_passed", [])
                rejected = reasoning.get("ai_gate_rejected_sample", [])
                rationale = reasoning.get("main_find_rationale", "")
                perspective = reasoning.get("perspective_check", "")
                logger.info(f"[REASONING] AI Gate passed: {len(passed)} items")
                for r in rejected[:3]:
                    logger.info(f"  [REJECTED] {r}")
                logger.info(f"  [RATIONALE] {rationale}")
                logger.info(f"  [PERSPECTIVE] {perspective}")

            # ── v5.2: Ensure radar field exists ──
            if "radar" not in content:
                content["radar"] = []

            logger.info(f"Curation OK: '{content['main_find']['title']}'")
            logger.info(f"Quick finds: {len(content.get('quick_finds', []))}")
            logger.info(f"Radar items: {len(content.get('radar', []))}")
            for ri in content.get("radar", []):
                logger.info(f"  [RADAR] {ri.get('title', 'N/A')}: {ri.get('why_watch', '')}")
            return content

        except json.JSONDecodeError as e:
            logger.warning(f"Attempt {attempt + 1}: invalid JSON — {e}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt + random.uniform(0, 1))
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = any(
                k in err_str for k in ("429", "resource exhausted", "quota", "rate limit", "insufficient_quota")
            )
            if is_rate_limit:
                sleep_secs = 60 + random.uniform(0, 15)
                logger.warning(
                    f"Attempt {attempt + 1}: rate limit — sleeping {sleep_secs:.0f}s before retry"
                )
            else:
                sleep_secs = 2**attempt + random.uniform(0, 1)
                logger.warning(f"Attempt {attempt + 1}: error — {e}")
            if attempt < max_retries - 1:
                time.sleep(sleep_secs)

    raise CurationError(f"DeepSeek failed after {max_retries} attempts")


# ── Render: Jinja2 HTML ──────────────────────────────────────────────
def render_email(
    content: dict,
    raw_count: int,
    filtered_count: int,
    active_sources: list[str],
    runtime: str,
) -> str:
    """Renderiza o template HTML com o conteúdo curado."""
    logger.info("=" * 50)
    logger.info("PHASE 4: RENDER — building email HTML")
    logger.info("=" * 50)

    template_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "templates"
    )
    if not os.path.exists(template_dir):
        template_dir = "templates"

    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True,
    )
    template = env.get_template("email.html")

    brt = timezone(timedelta(hours=-3))
    now_brt = datetime.now(brt)

    quick_finds = content.get("quick_finds", [])
    radar = content.get("radar", [])
    meta = content.get("meta", {})

    # Sources detail string
    sources_detail = " + ".join(
        s.replace("_", " ").title() for s in active_sources
    )

    # Total finds includes radar
    total_finds = len(quick_finds) + 1 + len(radar)

    html = template.render(
        correspondent_intro=content.get("correspondent_intro", ""),
        main_find=content["main_find"],
        quick_finds=quick_finds,
        radar=radar,
        edition_number=EDITION_NUMBER,
        date=now_brt.strftime("%d/%m/%Y"),
        sources_count=raw_count,
        finds_count=total_finds,
        sources_detail=sources_detail,
        active_sources=active_sources,
        num_sources=len(active_sources),
        posts_analyzed=meta.get("total_analyzed", filtered_count),
        signal_ratio=f"{total_finds}/{meta.get('total_analyzed', filtered_count)}",
        runtime=runtime,
        feedback_base_url=FEEDBACK_BASE_URL,
        aya_avatar_url=AYA_AVATAR_URL,
    )

    logger.info(f"HTML rendered: {len(html)} chars")
    return html


# send_via_buttondown e send_fallback importados de delivery.py

# ── Pipeline principal ───────────────────────────────────────────────
def run_pipeline():
    """Executa o pipeline completo: Config → Fetch → Pre-Filter → Curate → Render → Send."""
    start_time = time.time()

    logger.info("╔══════════════════════════════════════════════════╗")
    logger.info("║     DAILY SCOUT — PIPELINE v3.0 (Multi-Source)  ║")
    logger.info("║     Correspondente: AYA                          ║")
    logger.info("╚══════════════════════════════════════════════════╝")

    # ── Fail fast: valida env vars antes de qualquer I/O ──
    _validate_env()

    try:
        # ── Step 0: Load config ──
        config = load_config()
        active_sources = [
            sid
            for sid, conf in config.get("sources", {}).items()
            if isinstance(conf, dict) and conf.get("enabled", True)
        ]
        logger.info(f"Config: {len(active_sources)} sources enabled: {active_sources}")

        # ── Step 1: Fetch ──
        raw_items = fetch_all_sources(config)
        if not raw_items:
            raise FetchError("Nenhuma fonte respondeu. Possível rate limit ou instabilidade.")

        # ── Step 2: Pre-Filter ──
        filtered_items = filter_items(raw_items, config)
        if not filtered_items:
            raise FetchError("Pré-filtro descartou todos os items. Revisando thresholds.")

        # ── Step 3: Curate (v5: com context injection) ──
        source_breakdown = {}
        for item in raw_items:
            source_breakdown[item.source_id] = source_breakdown.get(item.source_id, 0) + 1

        content = curate_and_write(
            filtered_items,
            raw_count=len(raw_items),
            source_breakdown=source_breakdown,
        )

        # ── Step 3b: Save debug artifacts (para audit agent / PE study) ──
        if DEBUG_SAVE:
            debug_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "debug"
            )
            os.makedirs(debug_dir, exist_ok=True)

            curation_path = os.path.join(debug_dir, f"edition_{EDITION_NUMBER}_curation.json")
            with open(curation_path, "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            logger.info(f"[DEBUG] Curation output saved: {curation_path}")

            items_data = [
                {
                    "title": item.title,
                    "source": item.source_label,
                    "source_id": item.source_id,
                    "score": item.raw_score,
                    "comments": item.num_comments,
                    "url": item.url,
                    "cross_source_count": item.cross_source_count,
                    "cross_source_ids": item.cross_source_ids,
                }
                for item in filtered_items
            ]
            items_path = os.path.join(debug_dir, f"edition_{EDITION_NUMBER}_items.json")
            with open(items_path, "w", encoding="utf-8") as f:
                json.dump(items_data, f, ensure_ascii=False, indent=2)
            logger.info(f"[DEBUG] Pre-filter items saved: {items_path}")

        # ── Step 4: Render ──
        elapsed = f"{time.time() - start_time:.1f}s"
        html = render_email(
            content,
            raw_count=len(raw_items),
            filtered_count=len(filtered_items),
            active_sources=active_sources,
            runtime=elapsed,
        )

        # ── Step 5: Save local (artifact) ──
        output_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "output"
        )
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"edition_{EDITION_NUMBER}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"HTML saved: {output_path}")

        # ── Step 6: Send newsletter ──
        subject = f"AYA #{EDITION_NUMBER} — {content['main_find']['title']}"
        if DRY_RUN:
            logger.info("DRY_RUN=true — skipping Buttondown send")
            success = True
        else:
            success = send_via_buttondown(subject, html)
            if not success:
                raise DeliveryError("Buttondown delivery failed — HTML saved as artifact")

        # ── Step 7: Generate social content (isolated — failures don't affect newsletter) ──
        social_success = False
        if SOCIAL_ENABLED:
            try:
                from social.content_adapter import adapt_for_linkedin, save_social_artifacts

                logger.info("=" * 50)
                logger.info("PHASE 7: SOCIAL — generating adapted content")
                logger.info("=" * 50)

                linkedin_data = adapt_for_linkedin(content)
                artifact_path = save_social_artifacts(linkedin_data, EDITION_NUMBER)
                social_success = artifact_path is not None

                if social_success:
                    logger.info(f"Social content ready for delayed posting: {artifact_path}")
                else:
                    logger.warning("Social adaptation failed — newsletter unaffected")

            except Exception as social_err:
                logger.warning(f"Social generation failed (non-blocking): {social_err}")
        else:
            logger.info("SOCIAL_ENABLED=false — skipping social content generation")

        # ── Report ──
        total_time = f"{time.time() - start_time:.1f}s"
        logger.info("=" * 50)
        logger.info("PIPELINE COMPLETE")
        logger.info(f"  Sources: {len(active_sources)} active ({', '.join(active_sources)})")
        logger.info(f"  Raw items: {len(raw_items)} → Filtered: {len(filtered_items)}")
        logger.info(f"  Main find: {content['main_find']['title']}")
        logger.info(f"  Quick finds: {len(content.get('quick_finds', []))}")
        logger.info(f"  Social: {'OK' if social_success else 'SKIPPED' if not SOCIAL_ENABLED else 'FAILED'}")
        logger.info(f"  Runtime: {total_time}")
        logger.info("=" * 50)

    except (FetchError, CurationError) as e:
        # Falha na coleta ou curadoria — envia fallback e falha o job
        logger.error(f"{type(e).__name__}: {e}")
        try:
            send_fallback(str(e))
        except Exception as fallback_err:
            logger.error(f"Fallback also failed: {fallback_err}")
        sys.exit(1)

    except DeliveryError as e:
        # Falha só na entrega — HTML foi salvo, não envia fallback, não mata o job
        logger.warning(f"DeliveryError: {e}")

    except Exception as e:
        # Erro inesperado — trata igual a FetchError/CurationError
        logger.error(f"PIPELINE FAILED (unexpected): {e}", exc_info=True)
        try:
            send_fallback(str(e))
        except Exception as fallback_err:
            logger.error(f"Fallback also failed: {fallback_err}")
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
