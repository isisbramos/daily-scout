"""
Daily Scout — Pipeline automatizado de newsletter Tech & AI
Correspondente: Isis IA (AI-powered field correspondent)
Stack: Reddit RSS + HackerNews API → Gemini Flash → Jinja2 → Pipedream webhook
"""

import os
import sys
import json
import time
import logging
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from jinja2 import Environment, FileSystemLoader

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("daily-scout")

# ── Config ───────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PIPEDREAM_WEBHOOK_URL = os.environ.get("PIPEDREAM_WEBHOOK_URL")
EDITION_NUMBER = os.environ.get("EDITION_NUMBER", "001")

REDDIT_SUBS = [
    "artificial", "MachineLearning", "ChatGPT", "LocalLLaMA",
    "technology", "programming", "opensource", "singularity",
    "techNews", "ArtificialIntelligence", "compsci",
    "startups", "SideProject",
]

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0"


# ── Fetch: Reddit JSON ───────────────────────────────────────────────
def fetch_reddit() -> list[dict]:
    """Busca top posts de cada subreddit via JSON API (sem auth)."""
    items = []
    for sub in REDDIT_SUBS:
        url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
        headers = {"User-Agent": "DailyScout/1.0 (newsletter bot)"}
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                posts = data.get("data", {}).get("children", [])
                for post in posts:
                    d = post["data"]
                    items.append({
                        "title": d.get("title", ""),
                        "url": d.get("url", ""),
                        "score": d.get("score", 0),
                        "num_comments": d.get("num_comments", 0),
                        "subreddit": d.get("subreddit", sub),
                        "source": f"r/{sub}",
                        "created_utc": d.get("created_utc", 0),
                    })
                logger.info(f"  r/{sub}: {len(posts)} posts")
            elif resp.status_code == 429:
                logger.warning(f"  r/{sub}: rate limited, pulando")
            else:
                logger.warning(f"  r/{sub}: HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"  r/{sub}: erro — {e}")
        time.sleep(1)  # rate limit courtesy
    logger.info(f"Reddit total: {len(items)} posts coletados")
    return items


# ── Fetch: HackerNews API ────────────────────────────────────────────
def fetch_hackernews(limit: int = 30) -> list[dict]:
    """Busca top stories do HackerNews via Firebase API."""
    items = []
    try:
        resp = requests.get(f"{HN_TOP_URL}/topstories.json", timeout=15)
        if resp.status_code != 200:
            logger.warning(f"HN topstories: HTTP {resp.status_code}")
            return items
        story_ids = resp.json()[:limit]
        for sid in story_ids:
            try:
                sr = requests.get(f"{HN_TOP_URL}/item/{sid}.json", timeout=10)
                if sr.status_code == 200:
                    story = sr.json()
                    if story and story.get("title"):
                        items.append({
                            "title": story.get("title", ""),
                            "url": story.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                            "score": story.get("score", 0),
                            "num_comments": story.get("descendants", 0),
                            "source": "HackerNews",
                            "created_utc": story.get("time", 0),
                        })
            except Exception:
                continue
        logger.info(f"HackerNews: {len(items)} stories coletadas")
    except Exception as e:
        logger.warning(f"HackerNews fetch falhou: {e}")
    return items


# ── Fetch: all sources ───────────────────────────────────────────────
def fetch_all_sources() -> list[dict]:
    """Agrega todas as fontes e filtra últimas 24h."""
    logger.info("=" * 50)
    logger.info("FASE 1: FETCH — coletando fontes")
    logger.info("=" * 50)

    reddit = fetch_reddit()
    hn = fetch_hackernews()
    all_items = reddit + hn

    # Filtra últimas 24h
    cutoff = time.time() - 86400
    recent = [i for i in all_items if i.get("created_utc", 0) > cutoff]

    # Se filtro ficou muito restritivo, usa tudo
    if len(recent) < 10:
        logger.info(f"Filtro 24h retornou só {len(recent)}, usando todos os {len(all_items)}")
        recent = all_items

    # Ordena por score (proxy de relevância)
    recent.sort(key=lambda x: x.get("score", 0), reverse=True)

    logger.info(f"Total após filtro: {len(recent)} itens")
    return recent


# ── Curate & Write: Gemini ───────────────────────────────────────────

CURATION_PROMPT = """Você é a Isis IA — correspondente de campo do Daily Scout, uma newsletter diária de Tech & AI.

Você está "em campo" na internet. Os posts abaixo são os fatos brutos que você coletou. Sua missão:
1. FILTRAR usando o critério editorial: cada item precisa ter pelo menos 2 de 3 — Traction (engajamento alto), Impact (afeta muita gente ou muda algo relevante), Novelty (é novo ou surpreendente).
2. ESCOLHER 1 achado principal (main_find) e 3-5 achados rápidos (quick_finds).
3. ESCREVER com a voz do Daily Scout: direto, sem enrolação, PT-BR com termos técnicos em inglês quando natural. Tom de quem está em campo reportando o que viu, não de quem está opinando de longe.

REGRAS:
- main_find.body: 1-2 parágrafos curtos explicando POR QUE isso importa. Concreto, sem clichês.
- main_find.bullets: 2-3 pontos-chave práticos (o que mudou, o que significa, o que observar).
- quick_finds[].signal: uma frase curta explicando por que esse item é relevante.
- Se não houver nada realmente bom, diga — não force conteúdo fraco.
- URLs: use a URL original do post. display_url é a versão curta legível (ex: github.com/repo).

Retorne APENAS um JSON válido (sem markdown, sem ```), nesta estrutura exata:
{
  "main_find": {
    "title": "Título do achado principal",
    "source": "r/subreddit ou HackerNews",
    "body": "1-2 parágrafos explicando por que importa",
    "bullets": ["ponto 1", "ponto 2", "ponto 3"],
    "url": "https://url-original.com",
    "display_url": "dominio.com/path"
  },
  "quick_finds": [
    {
      "title": "Título curto",
      "signal": "Por que isso é relevante em uma frase",
      "url": "https://url.com",
      "display_url": "dominio.com"
    }
  ],
  "meta": {
    "total_analyzed": 50,
    "editorial_note": "Observação opcional sobre o dia"
  }
}

POSTS COLETADOS:
"""


def curate_and_write(raw_items: list[dict], max_retries: int = 3) -> dict:
    """Envia posts para o Gemini e recebe curadoria estruturada."""
    import google.generativeai as genai

    logger.info("=" * 50)
    logger.info("FASE 2: CURATE — Gemini processando")
    logger.info("=" * 50)

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não configurada")

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    # Prepara input (limita pra não estourar context window)
    items_for_prompt = []
    for item in raw_items[:50]:
        items_for_prompt.append({
            "title": item.get("title", "")[:200],
            "source": item.get("source", ""),
            "score": item.get("score", 0),
            "comments": item.get("num_comments", 0),
            "url": item.get("url", ""),
        })

    full_prompt = CURATION_PROMPT + json.dumps(items_for_prompt, ensure_ascii=False, indent=2)

    for attempt in range(max_retries):
        try:
            logger.info(f"Gemini attempt {attempt + 1}/{max_retries}...")
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "temperature": 0.7,
                    "max_output_tokens": 4096,
                },
            )

            text = response.text.strip()
            # Limpeza defensiva caso venha com markdown
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()

            content = json.loads(text)

            # Validação mínima
            if "main_find" not in content:
                raise ValueError("JSON sem 'main_find'")
            if "title" not in content["main_find"]:
                raise ValueError("main_find sem 'title'")

            logger.info(f"Curadoria OK: '{content['main_find']['title']}'")
            logger.info(f"Quick finds: {len(content.get('quick_finds', []))}")
            return content

        except json.JSONDecodeError as e:
            logger.warning(f"Attempt {attempt + 1}: JSON inválido — {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}: erro — {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    raise RuntimeError(f"Gemini falhou após {max_retries} tentativas")


# ── Render: Jinja2 HTML ──────────────────────────────────────────────
def render_email(content: dict, sources_count: int, runtime: str) -> str:
    """Renderiza o template HTML com o conteúdo curado."""
    logger.info("=" * 50)
    logger.info("FASE 3: RENDER — montando email HTML")
    logger.info("=" * 50)

    # Detecta path do template (funciona local e no GitHub Actions)
    template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    if not os.path.exists(template_dir):
        template_dir = "templates"

    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("email.html")

    brt = timezone(timedelta(hours=-3))
    now_brt = datetime.now(brt)

    quick_finds = content.get("quick_finds", [])
    meta = content.get("meta", {})

    html = template.render(
        main_find=content["main_find"],
        quick_finds=quick_finds,
        edition_number=EDITION_NUMBER,
        date=now_brt.strftime("%d/%m/%Y"),
        sources_count=sources_count,
        finds_count=len(quick_finds) + 1,
        sources_detail=f"Reddit ({len(REDDIT_SUBS)} subs) + HackerNews",
        posts_analyzed=meta.get("total_analyzed", sources_count),
        signal_ratio=f"{len(quick_finds) + 1}/{meta.get('total_analyzed', sources_count)}",
        runtime=runtime,
    )

    logger.info(f"HTML renderizado: {len(html)} chars")
    return html


# ── Send: Pipedream Webhook ──────────────────────────────────────────
def send_to_pipedream(subject: str, html_content: str) -> bool:
    """Envia email via Pipedream webhook."""
    logger.info("=" * 50)
    logger.info("FASE 4: SEND — enviando para Pipedream")
    logger.info("=" * 50)

    if not PIPEDREAM_WEBHOOK_URL:
        logger.error("PIPEDREAM_WEBHOOK_URL não configurada")
        return False

    payload = {
        "subject": subject,
        "html_content": html_content,
    }

    try:
        resp = requests.post(PIPEDREAM_WEBHOOK_URL, json=payload, timeout=30)
        if resp.status_code == 200:
            logger.info("Pipedream: enviado com sucesso!")
            return True
        else:
            logger.error(f"Pipedream: HTTP {resp.status_code} — {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Pipedream: erro de conexão — {e}")
        return False


# ── Send: Fallback (email simplificado) ──────────────────────────────
def send_fallback(reason: str) -> bool:
    """Envia versão simplificada caso o pipeline falhe parcialmente."""
    logger.info(f"Enviando fallback: {reason}")

    brt = timezone(timedelta(hours=-3))
    now_brt = datetime.now(brt)
    date_str = now_brt.strftime("%d/%m/%Y")

    fallback_html = f"""
    <div style="font-family: 'Courier New', monospace; background: #0F172A; color: #CBD5E1; padding: 32px; max-width: 600px; margin: 0 auto;">
        <div style="color: #22C55E; font-size: 18px; font-weight: bold;">DAILY SCOUT</div>
        <div style="color: #94A3B8; font-size: 12px; margin-top: 4px;">field report #{EDITION_NUMBER} — {date_str}</div>
        <hr style="border-color: #334155; margin: 16px 0;">
        <div style="color: #F59E0B; font-size: 14px; margin-bottom: 12px;">[TRANSMISSÃO PARCIAL]</div>
        <div style="color: #CBD5E1; font-size: 13px; line-height: 1.7;">
            A correspondente encontrou instabilidade no campo hoje. A edição completa não pôde ser montada.<br><br>
            <strong style="color: #F1F5F9;">Motivo:</strong> {reason}<br><br>
            Amanhã voltamos com cobertura completa.
        </div>
        <hr style="border-color: #334155; margin: 16px 0;">
        <div style="color: #94A3B8; font-size: 10px;">made_by: isis-ia v0.1 | status: fallback</div>
    </div>
    """

    subject = f"Daily Scout #{EDITION_NUMBER} — [transmissão parcial]"
    return send_to_pipedream(subject, fallback_html)


# ── Pipeline principal ───────────────────────────────────────────────
def run_pipeline():
    """Executa o pipeline completo: Fetch → Curate → Render → Send."""
    start_time = time.time()

    logger.info("╔══════════════════════════════════════════╗")
    logger.info("║     DAILY SCOUT — PIPELINE v2.0         ║")
    logger.info("║     Correspondente: Isis IA              ║")
    logger.info("╚══════════════════════════════════════════╝")

    try:
        # ── Step 1: Fetch ──
        raw_items = fetch_all_sources()

        if not raw_items:
            logger.warning("Nenhum item coletado — enviando fallback")
            send_fallback("Nenhuma fonte respondeu. Possível rate limit ou instabilidade.")
            return

        # ── Step 2: Curate ──
        content = curate_and_write(raw_items)

        # ── Step 3: Render ──
        elapsed = f"{time.time() - start_time:.1f}s"
        html = render_email(content, len(raw_items), elapsed)

        # ── Step 4: Save local (artifact) ──
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"edition_{EDITION_NUMBER}.html")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        logger.info(f"HTML salvo: {output_path}")

        # ── Step 5: Send ──
        subject = f"Daily Scout #{EDITION_NUMBER} — {content['main_find']['title']}"
        success = send_to_pipedream(subject, html)

        # ── Report ──
        total_time = f"{time.time() - start_time:.1f}s"
        logger.info("=" * 50)
        logger.info("PIPELINE COMPLETO")
        logger.info(f"  Sources: {len(raw_items)} posts coletados")
        logger.info(f"  Main find: {content['main_find']['title']}")
        logger.info(f"  Quick finds: {len(content.get('quick_finds', []))}")
        logger.info(f"  Delivery: {'OK' if success else 'FALHOU'}")
        logger.info(f"  Runtime: {total_time}")
        logger.info("=" * 50)

        if not success:
            logger.warning("Delivery falhou mas HTML foi salvo como artifact")

    except Exception as e:
        logger.error(f"PIPELINE FALHOU: {e}", exc_info=True)
        try:
            send_fallback(str(e))
        except Exception as fallback_err:
            logger.error(f"Fallback também falhou: {fallback_err}")
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
