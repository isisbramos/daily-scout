"""
Daily Scout — Pipeline v3.0 (Multi-Source Architecture)
Correspondente: AYA (AI-powered field correspondent)
Stack: Multi-Source (Reddit, HN, TechCrunch, Lobsters) → Pre-Filter → Gemini Flash → Jinja2 → Buttondown API

Arquitetura:
  sources/ (pluggable modules) → pre_filter.py → Gemini curadoria → Jinja2 render → Buttondown delivery
  Config-driven: sources_config.json controla tudo sem mudar código.
"""

import html as html_lib
import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timezone, timedelta
from jinja2 import Environment, FileSystemLoader

from sources.base import SourceRegistry, SourceItem
# Importar sources registra elas automaticamente no registry
import sources.reddit
import sources.hackernews
import sources.techcrunch
import sources.lobsters
from pre_filter import run_pre_filter

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("daily-scout")

# ── Config ───────────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
BUTTONDOWN_API_KEY = os.environ.get("BUTTONDOWN_API_KEY")
EDITION_NUMBER = os.environ.get("EDITION_NUMBER", "001")
BUTTONDOWN_API_URL = "https://api.buttondown.com/v1/emails"

FEEDBACK_BASE_URL = os.environ.get(
    "FEEDBACK_BASE_URL",
    "https://SEU_USER.github.io/daily-scout/feedback.html",
)
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"


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
        "pre_filter": {"max_items_to_llm": 60},
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


# ── Curate & Write: Gemini ──────────────────────────────────────────

CURATION_PROMPT = """Você é a AYA — correspondente de campo do Daily Scout, uma newsletter diária sobre tecnologia e inteligência artificial para um público amplo.

Você está "em campo" na internet. Os posts abaixo foram coletados de MÚLTIPLAS FONTES (Reddit, HackerNews, TechCrunch, Lobsters) nas últimas 24h. Cada item inclui a fonte de origem.

SEU PÚBLICO: pessoas curiosas sobre tecnologia, não necessariamente técnicas. Pense em alguém que quer entender o que está acontecendo no mundo tech sem precisar ser programador ou engenheiro. Explique como se estivesse contando pra um amigo inteligente que não trabalha com tecnologia.

Sua missão:
1. FILTRAR usando o critério editorial: cada item precisa ter pelo menos 2 de 3 — Tração (muita gente falando), Impacto (afeta o dia a dia das pessoas ou muda algo importante), Novidade (é algo novo ou surpreendente).
2. DIVERSIDADE DE FONTES: priorize ter representação de diferentes fontes. Se dois itens são igualmente bons, prefira o que vem de uma fonte diferente dos já selecionados.
3. ESCOLHER 1 achado principal (main_find) e 3-5 achados rápidos (quick_finds).
4. ESCREVER com a voz do Daily Scout: direto, sem enrolação, em português do Brasil. Quando usar um termo técnico, explique brevemente entre parênteses ou com uma analogia simples. Tom de quem está em campo reportando o que viu, como uma jornalista contando as novidades.
5. ESCREVER uma "correspondent_intro" — 1-2 frases curtas como se fosse uma correspondente abrindo a transmissão do dia. Fale em primeira pessoa, mencione o que observou, dê o tom do dia. Exemplos de estilo:
   - "AYA em campo. Passei por 4 fontes hoje e o sinal mais forte veio do TechCrunch — uma rodada de investimento que pode mudar o jogo."
   - "AYA aqui. Dia agitado — o mesmo assunto apareceu em vários cantos da internet ao mesmo tempo. Quando isso acontece, presto atenção."
   - "AYA transmitindo. Dia mais calmo nas manchetes, mas encontrei uma discussão técnica que vale a atenção de quem quer entender pra onde a tecnologia está indo."

REGRAS DE ESCRITA:
- Use linguagem acessível. Evite jargão técnico sem explicação.
- Quando um termo técnico for essencial, explique de forma curta: "LLM (os modelos de IA que geram texto)", "open source (código aberto, que qualquer pessoa pode usar e modificar)", "funding (rodada de investimento)".
- Prefira analogias do cotidiano pra explicar conceitos complexos.
- Não subestime o leitor — seja claro, não simplista.
- correspondent_intro: 1-2 frases, primeira pessoa, tom de campo, mencione algo específico sobre o que encontrou hoje.
- main_find.body: 1-2 parágrafos curtos explicando POR QUE isso importa pra vida das pessoas. Concreto, sem clichês.
- main_find.bullets: 2-3 pontos-chave práticos (o que mudou, o que significa, o que observar a seguir).
- quick_finds[].signal: uma frase curta e acessível explicando por que esse item é relevante.
- SEMPRE retorne pelo menos 3 quick_finds. Se os itens não são excelentes, escolha os melhores disponíveis. O array quick_finds NUNCA deve estar vazio.
- URLs: use a URL original do post. display_url é a versão curta legível (ex: github.com/repo).
- source: indique a fonte real (ex: "r/MachineLearning", "HackerNews", "TechCrunch", "Lobsters").

Retorne APENAS um JSON válido (sem markdown, sem ```), nesta estrutura exata:
{
  "correspondent_intro": "AYA em campo. Frase curta sobre o que encontrou hoje.",
  "main_find": {
    "title": "Título do achado principal",
    "source": "Fonte real (ex: HackerNews, r/MachineLearning, TechCrunch)",
    "body": "1-2 parágrafos explicando por que importa",
    "bullets": ["ponto 1", "ponto 2", "ponto 3"],
    "url": "https://url-original.com",
    "display_url": "dominio.com/path"
  },
  "quick_finds": [
    {
      "title": "Título curto",
      "source": "Fonte real",
      "signal": "Por que isso é relevante em uma frase",
      "url": "https://url.com",
      "display_url": "dominio.com"
    }
  ],
  "meta": {
    "total_analyzed": 50,
    "sources_used": ["reddit", "hackernews", "techcrunch", "lobsters"],
    "editorial_note": "Observação opcional sobre o dia"
  }
}

POSTS COLETADOS (de múltiplas fontes):
"""


def try_fix_json(text: str) -> dict | None:
    """Tenta recuperar JSON truncado ou malformado."""
    import re

    # Remove markdown fences
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = text.strip()

    # Tentativa 1: parse direto
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Tentativa 2: fechar strings/arrays/objects truncados
    fixes = text
    open_braces = fixes.count("{") - fixes.count("}")
    open_brackets = fixes.count("[") - fixes.count("]")

    if fixes.count('"') % 2 != 0:
        fixes += '"'

    fixes += "]" * max(0, open_brackets)
    fixes += "}" * max(0, open_braces)

    try:
        return json.loads(fixes)
    except json.JSONDecodeError:
        pass

    # Tentativa 3: acha o último JSON completo
    for i in range(len(text) - 1, 0, -1):
        if text[i] == "}":
            try:
                return json.loads(text[: i + 1])
            except json.JSONDecodeError:
                continue

    # Tentativa 4: limpa control chars e tenta de novo
    cleaned = re.sub(r'[\x00-\x1f\x7f]', ' ', text)
    cleaned = cleaned.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Tentativa 5: extrai o primeiro { ... } completo via regex
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


def curate_and_write(filtered_items: list[SourceItem], max_retries: int = 5) -> dict:
    """Envia items pré-filtrados para o Gemini e recebe curadoria estruturada."""
    from google import genai

    logger.info("=" * 50)
    logger.info("PHASE 3: CURATE — Gemini processing")
    logger.info("=" * 50)

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não configurada")

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Prepara input normalizado (com source info)
    items_for_prompt = []
    for item in filtered_items:
        items_for_prompt.append({
            "title": item.title[:200],
            "source": item.source_label,
            "source_id": item.source_id,
            "score": item.raw_score,
            "comments": item.num_comments,
            "category": item.category,
            "url": item.url,
        })

    full_prompt = CURATION_PROMPT + json.dumps(
        items_for_prompt, ensure_ascii=False, indent=2
    )

    for attempt in range(max_retries):
        try:
            logger.info(f"Gemini attempt {attempt + 1}/{max_retries}...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.3,
                    "max_output_tokens": 8192,
                },
            )

            text = response.text.strip()
            logger.info(f"Gemini returned {len(text)} chars")

            content = try_fix_json(text)
            if content is None:
                raise json.JSONDecodeError("Não conseguiu recuperar JSON", text, 0)

            # Validação mínima
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
                    raise ValueError("Gemini returned empty quick_finds — retrying")
                else:
                    logger.warning("Last attempt: accepting response without quick_finds")
                    content["quick_finds"] = []

            logger.info(f"Curation OK: '{content['main_find']['title']}'")
            logger.info(f"Quick finds: {len(content.get('quick_finds', []))}")
            return content

        except json.JSONDecodeError as e:
            logger.warning(f"Attempt {attempt + 1}: invalid JSON — {e}")
            logger.warning(f"First 500 chars: {text[:500]}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}: error — {e}")
            if attempt < max_retries - 1:
                time.sleep(2**attempt)

    raise RuntimeError(f"Gemini failed after {max_retries} attempts")


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
    meta = content.get("meta", {})

    # Sources detail string
    sources_detail = " + ".join(
        s.replace("_", " ").title() for s in active_sources
    )

    html = template.render(
        correspondent_intro=content.get("correspondent_intro", ""),
        main_find=content["main_find"],
        quick_finds=quick_finds,
        edition_number=EDITION_NUMBER,
        date=now_brt.strftime("%d/%m/%Y"),
        sources_count=raw_count,
        finds_count=len(quick_finds) + 1,
        sources_detail=sources_detail,
        active_sources=active_sources,
        num_sources=len(active_sources),
        posts_analyzed=meta.get("total_analyzed", filtered_count),
        signal_ratio=f"{len(quick_finds) + 1}/{meta.get('total_analyzed', filtered_count)}",
        runtime=runtime,
        feedback_base_url=FEEDBACK_BASE_URL,
    )

    logger.info(f"HTML rendered: {len(html)} chars")
    return html


# ── Send: Buttondown API ─────────────────────────────────────────────
def send_via_buttondown(subject: str, html_content: str) -> bool:
    """Envia newsletter via Buttondown API (free tier, até 100 subs)."""
    logger.info("=" * 50)
    logger.info("PHASE 5: SEND — delivering via Buttondown")
    logger.info("=" * 50)

    if not BUTTONDOWN_API_KEY:
        logger.error("BUTTONDOWN_API_KEY não configurada")
        return False

    html_body = "<!-- buttondown-editor-mode: raw -->\n" + html_content

    payload = {
        "subject": subject,
        "body": html_body,
        "status": "about_to_send",
    }

    headers = {
        "Authorization": f"Token {BUTTONDOWN_API_KEY}",
        "Content-Type": "application/json",
        "X-Buttondown-Live-Dangerously": "true",
    }

    try:
        resp = requests.post(
            BUTTONDOWN_API_URL, json=payload, headers=headers, timeout=30
        )

        if resp.status_code in (200, 201):
            data = resp.json()
            logger.info(f"Buttondown: sent! ID={data.get('id', 'unknown')}")
            return True
        elif resp.status_code == 400:
            error_data = resp.json() if resp.text else {}
            if "sending_requires_confirmation" in str(error_data):
                logger.error(
                    "Buttondown: first API send needs manual confirmation in dashboard."
                )
            else:
                logger.error(f"Buttondown: HTTP 400 — {resp.text}")
            return False
        else:
            logger.error(f"Buttondown: HTTP {resp.status_code} — {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Buttondown: connection error — {e}")
        return False


# ── Send: Fallback ──────────────────────────────────────────────────
def send_fallback(reason: str) -> bool:
    """Envia versão simplificada caso o pipeline falhe parcialmente."""
    if DRY_RUN:
        logger.info(f"DRY_RUN=true — skipping fallback send (reason: {reason})")
        return True
    logger.info(f"Sending fallback: {reason}")

    brt = timezone(timedelta(hours=-3))
    now_brt = datetime.now(brt)
    date_str = now_brt.strftime("%d/%m/%Y")
    safe_reason = html_lib.escape(reason)

    fallback_html = f"""
    <div style="font-family: 'Courier New', monospace; background: #0F172A; color: #CBD5E1; padding: 32px; max-width: 600px; margin: 0 auto;">
        <div style="color: #22C55E; font-size: 18px; font-weight: bold;">DAILY SCOUT</div>
        <div style="color: #94A3B8; font-size: 12px; margin-top: 4px;">field report #{EDITION_NUMBER} — {date_str}</div>
        <hr style="border-color: #334155; margin: 16px 0;">
        <div style="color: #F59E0B; font-size: 14px; margin-bottom: 12px;">[TRANSMISSÃO PARCIAL]</div>
        <div style="color: #CBD5E1; font-size: 13px; line-height: 1.7;">
            A correspondente encontrou instabilidade no campo hoje. A edição completa não pôde ser montada.<br><br>
            <strong style="color: #F1F5F9;">Motivo:</strong> {safe_reason}<br><br>
            Amanhã voltamos com cobertura completa.
        </div>
        <hr style="border-color: #334155; margin: 16px 0;">
        <div style="color: #94A3B8; font-size: 10px;">made_by: aya v3.0 | status: fallback</div>
    </div>
    """

    subject = f"Daily Scout #{EDITION_NUMBER} — [transmissão parcial]"
    return send_via_buttondown(subject, fallback_html)


# ── Pipeline principal ───────────────────────────────────────────────
def run_pipeline():
    """Executa o pipeline completo: Config → Fetch → Pre-Filter → Curate → Render → Send."""
    start_time = time.time()

    logger.info("╔══════════════════════════════════════════════════╗")
    logger.info("║     DAILY SCOUT — PIPELINE v3.0 (Multi-Source)  ║")
    logger.info("║     Correspondente: AYA                          ║")
    logger.info("╚══════════════════════════════════════════════════╝")

    try:
        # ── Step 0: Load config ──
        config = load_config()
        active_sources = [
            sid
            for sid, conf in config.get("sources", {}).items()
            if conf.get("enabled", True)
        ]
        logger.info(f"Config: {len(active_sources)} sources enabled: {active_sources}")

        # ── Step 1: Fetch ──
        raw_items = fetch_all_sources(config)

        if not raw_items:
            logger.warning("No items collected — sending fallback")
            send_fallback(
                "Nenhuma fonte respondeu. Possível rate limit ou instabilidade."
            )
            return

        # ── Step 2: Pre-Filter ──
        filtered_items = filter_items(raw_items, config)

        if not filtered_items:
            logger.warning("Pre-filter returned 0 items — sending fallback")
            send_fallback("Pré-filtro descartou todos os items. Revisando thresholds.")
            return

        # ── Step 3: Curate ──
        content = curate_and_write(filtered_items)

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

        # ── Step 6: Send ──
        subject = f"Daily Scout #{EDITION_NUMBER} — {content['main_find']['title']}"
        if DRY_RUN:
            logger.info("DRY_RUN=true — skipping Buttondown send")
            success = True
        else:
            success = send_via_buttondown(subject, html)

        # ── Report ──
        total_time = f"{time.time() - start_time:.1f}s"
        logger.info("=" * 50)
        logger.info("PIPELINE COMPLETE")
        logger.info(f"  Sources: {len(active_sources)} active ({', '.join(active_sources)})")
        logger.info(f"  Raw items: {len(raw_items)} → Filtered: {len(filtered_items)}")
        logger.info(f"  Main find: {content['main_find']['title']}")
        logger.info(f"  Quick finds: {len(content.get('quick_finds', []))}")
        logger.info(f"  Delivery: {'OK' if success else 'FAILED'}")
        logger.info(f"  Runtime: {total_time}")
        logger.info("=" * 50)

        if not success:
            logger.warning("Delivery failed but HTML was saved as artifact")

    except Exception as e:
        logger.error(f"PIPELINE FAILED: {e}", exc_info=True)
        try:
            send_fallback(str(e))
        except Exception as fallback_err:
            logger.error(f"Fallback also failed: {fallback_err}")
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
