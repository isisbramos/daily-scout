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
    print("--- INICIANDO DIAGNÓSTICO DE MODELOS ---")
    try:
        # Lista todos os modelos disponíveis para esta chave
        models = list(genai.list_models())
        for m in models:
            print(f"DEBUG: Modelo disponível: {m.name}")
        
        # Escolhe um modelo baseado no que foi listado (priorizando o flash)
        target_model = "gemini-2.0-flash"
        
        print(f"DEBUG: Tentando instanciar: {target_model}")
        model = genai.GenerativeModel(target_model)
        
        prompt = f"""Analise estes posts e retorne APENAS um JSON (sem markdown). 
        Estrutura: {{"main_find": {{"title": "exemplo", "source": "exemplo", "body": "exemplo", "bullets": [], "url": "http://exemplo.com", "display_url": "exemplo.com"}}, "quick_finds": [], "meta": {{"total_analyzed": 0}}}} 
        POSTS: {str(raw_items[:30])}"""
        
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
        
    except Exception as e:
        print(f"DEBUG: ERRO CRÍTICO NA CONEXÃO COM O GEMINI: {str(e)}")
        raise e

def send_via_beehiiv(subject, html_content):
    pub_id = os.environ.get("BEEHIIV_PUBLICATION_ID")
    url = f"https://api.beehiiv.com/v2/publications/{pub_id}/posts"
    headers = {
        "Authorization": f"Bearer {os.environ.get('BEEHIIV_API_KEY')}", 
        "Content-Type": "application/json"
    }
    payload = {"title": subject, "status": "draft", "content_html": html_content}
    
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 201:
        print("Sucesso! Post criado no Beehiiv.")
    else:
        print(f"ERRO BEEHIIV: {resp.status_code} - {resp.text}")

def run_pipeline():
    print("DEBUG: Pipeline Iniciou")
    items = [{"title": "Exemplo de Tech", "source": "Reddit", "score": 100}]
    
    try:
        content = curate_and_write(items)
        
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
        
        send_via_beehiiv("Daily Scout Teste", html)
        
    except Exception as e:
        print(f"ERRO FINAL: {e}")

if __name__ == "__main__":
    run_pipeline()
