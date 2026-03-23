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
    print("--- INICIANDO CURADORIA GEMINI ---")
    try:
        # Usando o modelo confirmado na sua lista de disponíveis
        target_model = "gemini-2.0-flash"
        print(f"DEBUG: Usando modelo: {target_model}")
        
        model = genai.GenerativeModel(target_model)
        
        prompt = f"""Analise estes posts e retorne APENAS um JSON (sem markdown). 
        Estrutura exata: {{"main_find": {{"title": "Exemplo", "source": "Exemplo", "body": "Corpo", "bullets": ["item1", "item2"], "url": "http://exemplo.com", "display_url": "exemplo.com"}}, "quick_finds": [], "meta": {{"total_analyzed": 1}}}} 
        POSTS: {str(raw_items[:30])}"""
        
        response = model.generate_content(prompt)
        # Limpeza robusta
        text = response.text.replace("```json", "").replace("```", "").replace("\n", "").strip()
        return json.loads(text)
        
    except Exception as e:
        print(f"DEBUG: ERRO NO GEMINI: {str(e)}")
        raise e

def send_via_beehiiv(subject, html_content):
    print("--- TENTANDO ENVIO PARA BEEHIIV ---")
    pub_id = os.environ.get("BEEHIIV_PUBLICATION_ID")
    api_key = os.environ.get("BEEHIIV_API_KEY")
    
    url = f"https://api.beehiiv.com/v2/publications/{pub_id}/posts"
    headers = {
        "Authorization": f"Bearer {api_key}", 
        "Content-Type": "application/json"
    }
    payload = {"title": subject, "status": "draft", "content_html": html_content}
    
    print(f"DEBUG: URL de envio: {url}")
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    
    print(f"DEBUG: Beehiiv Status Code: {resp.status_code}")
    print(f"DEBUG: Beehiiv Resposta: {resp.text}")
    
    if resp.status_code == 201:
        print("Sucesso! Post criado no Beehiiv.")
    else:
        print(f"ERRO BEEHIIV: {resp.status_code} - Verifique a API Key e o Publication ID!")

def run_pipeline():
    print("DEBUG: Pipeline Iniciou")
    items = [{"title": "Exemplo de Tech", "source": "Reddit", "score": 100}]
    
    try:
        content = curate_and_write(items)
        print("DEBUG: JSON recebido do Gemini.")
        
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
        print("DEBUG: HTML renderizado.")
        
        send_via_beehiiv("Daily Scout Teste", html)
        
    except Exception as e:
        print(f"ERRO FATAL: {e}")

if __name__ == "__main__":
    run_pipeline()
