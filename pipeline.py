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

# Monitoramento
SUBREDDITS = ["LocalLLaMA", "MachineLearning", "artificial", "singularity", "ChatGPT", "ClaudeAI", "OpenAI", "StableDiffusion", "comfyui", "SelfHosted", "programming", "technology", "ProductHunt"]
BRT = timezone(timedelta(hours=-3))

def fetch_reddit_rss(subreddit: str, limit: int = 25) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/hot.rss?limit={limit}"
    headers = {"User-Agent": "DailyScout/1.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        feed = feedparser.parse(resp.text)
        return [{"title": e.title, "url": e.link, "source": f"r/{subreddit}", "score": 0, "platform": "reddit"} for e in feed.entries]
    except: return []

def fetch_hackernews_top(limit: int = 30) -> list[dict]:
    try:
        resp = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
        story_ids = resp.json()[:limit]
        items = []
        for sid in story_ids:
            story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=5).json()
            if story and story.get("type") == "story":
                items.append({"title": story.get("title", ""), "url": story.get("url", ""), "source": "HackerNews", "score": story.get("score", 0), "platform": "hackernews"})
        return items
    except: return []

def fetch_all_sources() -> list[dict]:
    all_items = []
    for sub in SUBREDDITS:
        all_items.extend(fetch_reddit_rss(sub))
    all_items.extend(fetch_hackernews_top())
    return all_items

def curate_and_write(raw_items: list[dict]) -> dict:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    items_text = "\n".join([f"[{i+1}] {item['title']} ({item['source']})" for i, item in enumerate(raw_items[:50])])
    prompt = f"Voce e Isis IA. Analise estes posts e retorne APENAS um JSON (sem markdown). Estrutura: {{\"main_find\": {{\"title\": \"\", \"source\": \"\", \"body\": \"\", \"bullets\": [], \"url\": \"\", \"display_url\": \"\"}}, \"quick_finds\": [], \"meta\": {{\"total_analyzed\": 0, \"signal_ratio\": \"\"}}}} POSTS: {items_text}"
    
    response = model.generate_content(prompt)
    return json.loads(response.text.replace("```json", "").replace("```", "").strip())

def render_email(content: dict, raw_count: int, runtime: float) -> str:
    env = Environment(loader=FileSystemLoader("templates"))
    return env.get_template("email.html").render(
        edition_number=os.environ.get("EDITION_NUMBER", "001"),
        date=datetime.now(BRT).strftime("%d %b %Y"),
        sources_count=raw_count,
        finds_count=1 + len(content.get("quick_finds", [])),
        main_find=content["main_find"],
        quick_finds=content.get("quick_finds", []),
        sources_detail="Reddit + HN",
        posts_analyzed=raw_count,
        signal_ratio="1.0%",
        runtime="0s"
    )

def send_via_beehiiv(subject: str, html_content: str) -> bool:
    url = f"https://api.beehiiv.com/v2/publications/{BEEHIIV_PUBLICATION_ID}/posts"
    headers = {"Authorization": f"Bearer {BEEHIIV_API_KEY}", "Content-Type": "application/json"}
    payload = {"title": subject, "status": "draft", "content_html": html_content}
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 201: return True
    logger.error(f"Erro Beehiiv {resp.status_code}: {resp.text}")
    return False

def run_pipeline():
    print("DEBUG: Pipeline Iniciou")
    logger.info("Starting Daily Scout Pipeline...")
    raw_items = fetch_all_sources()
    content = curate_and_write(raw_items)
    html = render_email(content, len(raw_items), 0)
    send_via_beehiiv(f"📡 Daily Scout — {content['main_find']['title']}", html)
    logger.info("Pipeline Finalizado.")

if __name__ == "__main__":
    run_pipeline()
