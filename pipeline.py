import os
import json
import logging
import requests
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(level=logging.INFO)

# Configuração da API do Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def curate_and_write(raw_items):
    print("DEBUG: Chamando o Gemini...")
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    
    prompt = f"""Analise estes posts e retorne APENAS um JSON (sem markdown). 
    Estrutura: {{"main_find": {{"title": "exemplo", "source": "exemplo", "body": "exemplo", "bullets": [], "url": "http://exemplo.com", "display_url": "exemplo.com"}}, "quick_finds": [], "meta": {{"total_analyzed": 0}}}} 
    POSTS: {str(raw_items[:30])}"""
    
    response = model.generate_content(prompt)
    print(f"DEBUG: Resposta do Gemini recebida: {response.text[:100]}...") # Mostra o começo da resposta
    
    text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def send_via_beehiiv(subject, html_content):
    print("DEBUG: Tentando enviar para o Beehiiv...")
    pub_id = os.environ.get("BEEHIIV_PUBLICATION_ID")
    url = f"https://api.beehiiv.com/v2/publications/{pub_id}/posts"
    headers = {
        "Authorization": f"Bearer {os.environ.get('BEEHIIV_API_KEY')}", 
        "Content-Type": "application/json"
    }
    payload = {"title": subject, "status": "draft", "content_html": html_content}
    
    resp = requests.post(url, headers=headers, json=payload)
    print(f"DEBUG: Resposta do Beehiiv (Código {resp.status_code}): {resp.text}")
    
    if resp.status_code == 201:
        print("Sucesso! Post criado no Beehiiv.")
    else:
        print(f"ERRO AO ENVIAR PARA BEEHIIV: {resp.status_code} - {resp.text}")

def run_pipeline():
    print("DEBUG: Pipeline Iniciou")
    items = [{"title": "Exemplo de Tech", "source": "Reddit", "score": 100}]
    
    try:
        content = curate_and_write(items)
        print("DEBUG: JSON do Gemini processado com sucesso.")
        
        env = Environment(loader=FileSystemLoader("templates"))
        template = env.get_template("email.html")
        
        html = template.render(
            main_find=content["main_find"], 
            quick_finds=content.get("quick_finds", []), 
            edition_number="001", 
            date="Hoje",
            sources_count=1,
            finds_count=len(content.get("quick_finds", [])),
            sources_detail="RSS",
            posts_analyzed=1,
            signal_ratio="high",
            runtime="1s"
        )
        print("DEBUG: Template HTML renderizado.")
        
        send_via_beehiiv("Daily Scout Teste", html)
        
    except Exception as e:
        print(f"ERRO FATAL NO PIPELINE: {e}")

if __name__ == "__main__":
    run_pipeline()
