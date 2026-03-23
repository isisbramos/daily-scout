"""
Daily Scout — Pipeline Principal
=================================
Correspondente digital de Tech & AI.
Roda todo dia as 7:55 BRT via GitHub Actions.
Flow: Fetch Sources -> Curate (LLM) -> Write (LLM) -> Render HTML -> Send via Beehiiv
"""

import os
import json
import time
import hashlib
import logging
from datetime import datetime, timedelta, timezone

import requests
import feedparser
from google import genai
from jinja2 import Environment, FileSystemLoader

# ============================================================
# CONFIG
# ============================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("daily-scout")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
BEEHIIV_API_KEY = os.environ.get("BEEHIIV_API_KEY", "")
BEEHIIV_PUBLICATION_ID = os.environ.get("BEEHIIV_PUBLICATION_ID", "")

# Reddit subreddits to monitor (RSS feeds)
SUBREDDITS = [
    "LocalLLaMA",
    "MachineLearning",
    "artificial",
    "singularity",
    "ChatGPT",
    "ClaudeAI",
    "OpenAI",
    "StableDiffusion",
    "comfyui",
    "SelfHosted",
    "programming",
    "technology",
    "ProductHunt",
]

# Hours to look back
LOOKBACK_HOURS = 24

# Max items to send to LLM for curation
MAX_RAW_ITEMS = 150

# Timezone: BRT (UTC-3)
BRT = timezone(timedelta(hours=-3))

# ============================================================
# STEP 1: FETCH SOURCES
# ============================================================

def fetch_reddit_rss(subreddit: str, limit: int = 25) -> list[dict]:
    """Fetch top posts from a subreddit via RSS."""
    url = f"https://www.reddit.com/r/{subreddit}/hot.rss?limit={limit}"
    headers = {"User-Agent": "DailyScout/1.0 (newsletter bot)"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        items = []
        for entry in feed.entries:
            # Extract score from content if available
            score = 0
            if hasattr(entry, "content"):
                content_text = entry.content[0].value if entry.content else ""
                # Reddit RSS includes vote info in content
                if "points" in content_text.lower():
                    try:
                        import re
                        score_match = re.search(r'(\d+)\s*points?', content_text.lower())
                        if score_match:
                            score = int(score_match.group(1))
                    except (ValueError, AttributeError):
                        pass
            items.append({
                "title": entry.title,
                "url": entry.link,
                "source": f"r/{subreddit}",
                "score": score,
                "published": entry.get("published", ""),
                "content_snippet": entry.get("summary", "")[:500],
                "platform": "reddit",
            })
        return items
    except Exception as e:
        logger.warning(f"Failed to fetch r/{subreddit}: {e}")
        return []


def fetch_hackernews_top(limit: int = 30) -> list[dict]:
    """Fetch top stories from HackerNews API as supplementary source."""
    try:
        resp = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
        resp.raise_for_status()
        story_ids = resp.json()[:limit]
        items = []
        for sid in story_ids:
            try:
                story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=5).json()
                if story and story.get("type") == "story":
                    items.append({
                        "title": story.get("title", ""),
                        "url": story.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                        "source": "HackerNews",
                        "score": story.get("score", 0),
                        "comments": story.get("descendants", 0),
                        "published": "",
                        "content_snippet": "",
                        "platform": "hackernews",
                    })
            except Exception:
                continue
        return items
    except Exception as e:
        logger.warning(f"Failed to fetch HackerNews: {e}")
        return []


def fetch_all_sources() -> list[dict]:
    """Fetch from all configured sources."""
    all_items = []

    # Reddit
    for sub in SUBREDDITS:
        items = fetch_reddit_rss(sub)
        all_items.extend(items)
        time.sleep(0.5)  # Rate limiting

    # HackerNews (bonus source, free)
    hn_items = fetch_hackernews_top()
    all_items.extend(hn_items)

    # Deduplicate by URL
    seen_urls = set()
    unique_items = []
    for item in all_items:
        url_hash = hashlib.md5(item["url"].encode()).hexdigest()
        if url_hash not in seen_urls:
            seen_urls.add(url_hash)
            unique_items.append(item)

    # Sort by score (descending) and limit
    unique_items.sort(key=lambda x: x.get("score", 0), reverse=True)
    unique_items = unique_items[:MAX_RAW_ITEMS]

    logger.info(f"Fetched {len(all_items)} total items, {len(unique_items)} unique after dedup")
    return unique_items

# ============================================================
# STEP 2: CURATE & WRITE (LLM)
# ============================================================

CURATION_PROMPT = """Voce e a Isis IA, correspondente digital do Daily Scout. Sua missao e analisar os posts abaixo e criar a edicao de hoje da newsletter.

## QUEM VOCE E

- Uma AI correspondente que vive embedded na internet
- Abertamente AI, self-aware, transparente sobre seu processo
- Tom: direto, factual, contextualizado. Correspondente em campo. Sem sensacionalismo.
- Idioma: PT-BR com jargao tecnico em EN (LLM, fine-tuning, open source, etc)

## SEU FILTRO EDITORIAL

Cada item precisa bater pelo menos 2 de 3 criterios:

1. Traction: Upvotes, stars, comments altos. O crowd esta validando.
2. Impact: Pode mudar algo significativo. Muda como pessoas trabalham/pensam/constroem.
3. Novelty: Genuinamente novo. Nao e requentado, nao e obvio, nao e PR disfarçado.

## OUTPUT ESPERADO

Retorne um JSON valido com esta estrutura exata:

\`\`\`json
{
  "main_find": {
    "title": "titulo do achado principal (PT-BR, impactante, sem clickbait)",
    "source": "r/SubredditName | 3.2k upvotes em 8h",
    "body": "1-2 paragrafos explicando o que e e por que importa (PT-BR, tom correspondente)",
    "bullets": [
      "Por que importa: ...",
      "Caveat: ...",
      "Signal: ..."
    ],
    "url": "url original do post/link",
    "display_url": "dominio.com/path-curto"
  },
  "quick_finds": [
    {
      "title": "titulo curto (PT-BR)",
      "signal": "uma frase de por que importa",
      "url": "url original",
      "display_url": "dominio.com/path"
    }
  ],
  "meta": {
    "total_analyzed": <numero de items que voce recebeu>,
    "signal_ratio": "<porcentagem que passou no filtro>"
  }
}
\`\`\`

## REGRAS

- O main_find e OBRIGATORIO. Escolha o melhor achado do dia.
- quick_finds: 0 a 5 items. So inclua se realmente merece. Zero filler.
- Se nenhum item merece ser main_find, retorne um JSON com main_find sobre "dia fraco na internet" e quick_finds vazio.
- NAO invente informacoes. Use apenas o que esta nos posts abaixo.
- Bullets do main_find: sempre 2-3 bullets. "Por que importa", "Caveat" (se houver), "Signal".
- display_url: so o dominio + path curto, sem https://

## POSTS PARA ANALISAR (ultimas 24h):

"""


def curate_and_write(raw_items: list[dict]) -> dict:
    """Send items to Gemini Flash for curation and writing."""
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Format items for the prompt
    items_text = ""
    for i, item in enumerate(raw_items):
        items_text += f"\n---\n[{i+1}] {item['title']}\n"
        items_text += f"    source: {item['source']} | score: {item.get('score', 'n/a')} | comments: {item.get('comments', 'n/a')}\n"
        items_text += f"    url: {item['url']}\n"
        if item.get("content_snippet"):
            items_text += f"    snippet: {item['content_snippet'][:200]}\n"

    full_prompt = CURATION_PROMPT + items_text

    logger.info(f"Sending {len(raw_items)} items to Gemini Flash for curation...")

    # Retry up to 3 times
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=full_prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.7,
                    "max_output_tokens": 4096,
                },
            )
            result = json.loads(response.text)

            # Validate structure
            if "main_find" not in result:
                raise ValueError("Missing 'main_find' in response")

            logger.info("Curation complete!")
            return result

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

    raise RuntimeError("All 3 attempts failed")

# ============================================================
# STEP 3: RENDER HTML
# ============================================================

def render_email(content: dict, raw_count: int, runtime_seconds: float) -> str:
    """Render the email HTML from template + content."""
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("email.html")

    now = datetime.now(BRT)

    # Calculate edition number (days since launch — placeholder)
    edition_number = os.environ.get("EDITION_NUMBER", "001")

    meta = content.get("meta", {})
    finds_count = 1 + len(content.get("quick_finds", []))
    sources_count = meta.get("total_analyzed", raw_count)
    signal_ratio = meta.get("signal_ratio", f"{(finds_count / max(sources_count, 1)) * 100:.1f}%")

    html = template.render(
        edition_number=edition_number,
        date=now.strftime("%d %b %Y"),
        sources_count=sources_count,
        finds_count=finds_count,
        main_find=content["main_find"],
        quick_finds=content.get("quick_finds", []),
        sources_detail=f"Reddit ({len(SUBREDDITS)} subs) + HackerNews",
        posts_analyzed=f"{raw_count:,}",
        signal_ratio=signal_ratio,
        runtime=f"{runtime_seconds:.0f}s",
    )

    logger.info(f"Email rendered: {len(html)} chars")
    return html

# ============================================================
# STEP 4: SEND VIA BEEHIIV
# ============================================================

def send_via_beehiiv(subject: str, html_content: str) -> bool:
    """Send the email via Beehiiv API."""
    if not BEEHIIV_API_KEY or not BEEHIIV_PUBLICATION_ID:
        logger.warning("Beehiiv credentials not set. Saving HTML locally instead.")
        with open("output/latest_edition.html", "w") as f:
            f.write(html_content)
        logger.info("Saved to output/latest_edition.html")
        return False

    url = f"https://api.beehiiv.com/v2/publications/{BEEHIIV_PUBLICATION_ID}/posts"
    headers = {
        "Authorization": f"Bearer {BEEHIIV_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "title": subject,
        "subtitle": "Todo dia, os melhores achados de Tech & AI",
        "status": "confirmed",
        "send_to": "all",
        "content_html": html_content,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        post_data = resp.json()
        logger.info(f"Published to Beehiiv! Post ID: {post_data.get('data', {}).get('id', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send via Beehiiv: {e}")
        return False


def send_fallback_via_beehiiv() -> bool:
    """Send a simplified 'technical difficulties' edition."""
    if not BEEHIIV_API_KEY or not BEEHIIV_PUBLICATION_ID:
        return False

    now = datetime.now(BRT)
    edition_number = os.environ.get("EDITION_NUMBER", "001")

    fallback_html = f"""
    <div style="background-color: #0F172A; padding: 40px 24px; font-family: 'Courier New', monospace; color: #CBD5E1; text-align: center;">
        <div style="color: #22C55E; font-size: 18px; font-weight: bold;">DAILY SCOUT</div>
        <div style="color: #94A3B8; font-size: 12px; margin-top: 8px;">field report #{edition_number} // {now.strftime('%d %b %Y')}</div>
        <div style="margin-top: 24px; padding: 20px; border: 1px solid #334155; border-radius: 8px;">
            <div style="color: #F59E0B; font-size: 14px; font-weight: bold;">
                &gt; DIFICULDADES TECNICAS
            </div>
            <div style="color: #94A3B8; font-size: 13px; margin-top: 12px; line-height: 1.6;">
                A Isis IA encontrou problemas no pipeline hoje.<br>
                Voltamos amanha com os melhores achados de Tech & AI.
            </div>
        </div>
        <div style="color: #475569; font-size: 11px; margin-top: 24px;">
            made_by: isis-ia v0.1 | status: pipeline_error
        </div>
    </div>
    """

    subject = f"\ud83d\udce1 Daily Scout #{edition_number} \u2014 De volta amanha"
    return send_via_beehiiv(subject, fallback_html)

# ============================================================
# MAIN PIPELINE
# ============================================================

def run_pipeline():
    """Execute the full Daily Scout pipeline."""
    logger.info("=" * 50)
    logger.info("DAILY SCOUT \u2014 Pipeline Starting")
    logger.info("=" * 50)

    start_time = time.time()
    edition_number = os.environ.get("EDITION_NUMBER", "001")

    try:
        # Step 1: Fetch sources
        logger.info("[1/4] Fetching sources...")
        raw_items = fetch_all_sources()

        if not raw_items:
            logger.error("No items fetched from any source!")
            send_fallback_via_beehiiv()
            return

        # Step 2: Curate & Write
        logger.info("[2/4] Curating & writing with Gemini Flash...")
        content = curate_and_write(raw_items)

        # Step 3: Render HTML
        runtime = time.time() - start_time
        logger.info("[3/4] Rendering email template...")
        html = render_email(content, len(raw_items), runtime)

        # Step 4: Send
        subject = f"\ud83d\udce1 Daily Scout #{edition_number} \u2014 {content['main_find']['title']}"
        logger.info(f"[4/4] Sending: {subject}")

        # Save locally regardless
        os.makedirs("output", exist_ok=True)
        with open("output/latest_edition.html", "w") as f:
            f.write(html)
        with open("output/latest_edition.json", "w") as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

        success = send_via_beehiiv(subject, html)

        total_time = time.time() - start_time
        logger.info("=" * 50)
        logger.info(f"Pipeline complete in {total_time:.1f}s")
        logger.info(f"Items fetched: {len(raw_items)}")
        logger.info(f"Finds: 1 main + {len(content.get('quick_finds', []))} quick")
        logger.info(f"Beehiiv: {'sent' if success else 'saved locally'}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        logger.info("Sending fallback edition...")
        send_fallback_via_beehiiv()

        # Save error log
        os.makedirs("output", exist_ok=True)
        with open("output/error_log.txt", "a") as f:
            f.write(f"{datetime.now(BRT).isoformat()} | ERROR: {e}\n")
        raise


if __name__ == "__main__":
    run_pipeline()
