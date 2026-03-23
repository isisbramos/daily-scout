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
        # Modelo verificado na sua lista
        target_model = "gemini-2.5-flash"
        print(f"DEBUG: Usando modelo: {target_model}")
        
        model = genai.GenerativeModel(target_model)
        
        prompt = f"""Analise estes posts e retorne APENAS um JSON (sem markdown). 
        Estrutura exata: {{"main_find": {{"title": "Exemplo", "source": "Exemplo", "body": "Corpo", "bullets": ["item1", "item2"], "url": "http://exemplo.com", "display_url": "exemplo.com"}}, "quick_finds": [], "meta": {{"total_analyzed": 1}}}} 
        POSTS: {str(raw_items[:30])}"""
        
        response = model.generate_content(prompt)
        # Limpeza do JSON
        text = response.text.replace("```json", "").replace("```", "").replace("\n", "").strip()
        return json.loads(text)
        
    except Exception as e:
        print(f"DEBUG: ERRO NO GEMINI: {str(e)}")
        raise e

def send_to_pipedream(subject, html_content):
    print("--- ENVIANDO PARA O WEBHOOK DO PIPEDREAM ---")
    webhook_url = "https://eoijdv78et94xfs.m.pipedream.net"
    
    payload = {
        "subject": subject,
        "html_content": html_content
    }
    
    try:
        resp = requests.post(webhook_url, json=payload, timeout=30)
        if resp.status_code == 200:
            print("Sucesso! Conteúdo enviado para o Pipedream.")
        else:
            print(f"Erro ao enviar para Pipedream: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"ERRO AO CONECTAR COM PIPEDREAM: {e}")

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
        
        # Agora chama a função que envia para o Pipedream em vez do Beehiiv
        send_to_pipedream("Daily Scout Teste", html)
        
    except Exception as e:
        print(f"ERRO FATAL: {e}")

if __name__ == "__main__":
    run_pipeline()
