import os
import json
import logging
import requests
import feedparser
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("daily-scout")

# Configuração pegando os Segredos do GitHub
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def curate_and_write(raw_items):
    # Usando o modelo direto e simples
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = "Analise estes posts e retorne APENAS um JSON (sem markdown). Estrutura: {'main_find': {'title': '', 'source': '', 'body': '', 'bullets': [], 'url': '', 'display_url': ''}, 'quick_finds': [], 'meta': {'total_analyzed': 0}} POSTS: " + str(raw_items[:30])
    
    response = model.generate_content(prompt)
    return json.loads(response.text.replace("```json", "").replace("```", "").strip())

def send_via_beehiiv(subject, html_content):
    url = f"https://api.beehiiv.com/v2/publications/{os.environ.get('BEEHIIV_PUBLICATION_ID')}/posts"
    headers = {"Authorization": f"Bearer {os.environ.get('BEEHIIV_API_KEY')}", "Content-Type": "application/json"}
    payload = {"title": subject, "status": "draft", "content_html": html_content}
    
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 201:
        print("Sucesso! Post criado no Beehiiv.")
    else:
        print(f"Erro Beehiiv {resp.status_code}: {resp.text}")

def run_pipeline():
    print("DEBUG: Pipeline Iniciou")
    # Pega itens de teste rápidos para não falhar
    items = [{"title": "Exemplo de Tech", "source": "Reddit", "score": 100}]
    content = curate_and_write(items)
    
    # Renderiza (exige a pasta templates/email.html)
    env = Environment(loader=FileSystemLoader("templates"))
    html = env.get_template("email.html").render(main_find=content["main_find"], quick_finds=[], edition_number="001", date="Hoje")
    
    send_via_beehiiv("Daily Scout Teste", html)

if __name__ == "__main__":
    run_pipeline()
