"""
Daily Scout — Pipeline Principal
Roda todo dia via GitHub Actions.
"""
import os
import json
import time
import hashlib
import logging
import requests
import feedparser
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timedelta, timezone

# Config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("daily-scout")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
BEEHIIV_API_KEY = os.environ.get("BEEHIIV_API_KEY", "")
BEEHIIV_PUBLICATION_ID = os.environ.get("BEEHIIV_PUBLICATION_ID", "")

# ... [MANTENHA AQUI SUAS FUNÇÕES fetch_reddit_rss, fetch_hackernews_top E fetch_all_sources] ...
# (Cole aqui suas funções de fetch que você já tinha, elas estão corretas)

# ============================================================
# STEP 2: CURATE & WRITE (LLM)
# ============================================================

def curate_and_write(raw_items: list[dict]) -> dict:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    items_text = "\n".join([f"[{i+1}] {item['title']} (Score: {item.get('score', 0)})" for i, item in enumerate(raw_items)])
    
    prompt = f"""
    Voce e a Isis IA. Analise os posts abaixo e crie a newsletter.
    Responda APENAS com um JSON puro (sem markdown, sem nada extra).
    Estrutura: {{"main_find": {{"title": "", "source": "", "body": "", "bullets": [], "url": "", "display_url": ""}}, "quick_finds": [{"title": "", "signal": "", "url": "", "display_url": ""}], "meta": {{"total_analyzed": 0, "signal_ratio": ""}}}}
    
    POSTS:
    {items_text}
    """

    response = model.generate_content(prompt)
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)

# ============================================================
# STEP 3 & 4: RENDER & SEND
# ============================================================

# ... [MANTENHA AQUI SUA FUNÇÃO render_email] ...

def send_via_beehiiv(subject: str, html_content: str) -> bool:
    if not BEEHIIV_API_KEY or not BEEHIIV_PUBLICATION_ID:
        return False

    url = f"https://api.beehiiv.com/v2/publications/{BEEHIIV_PUBLICATION_ID}/posts"
    headers = {
        "Authorization": f"Bearer {BEEHIIV_API_KEY}",
        "Content-Type": "application/json",
    }
    # Payload v2 padrão
    payload = {
        "title": subject,
        "status": "draft",
        "content_html": html_content
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        logger.info(f"Sucesso! Beehiiv: {resp.status_code}")
        return True
    except Exception as e:
        logger.error(f"Erro Beehiiv: {e}")
        return False

# ... [MANTENHA AQUI A FUNÇÃO run_pipeline E O RESTANTE] ...
