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
import re
import sys
import json
import time
import logging
import requests
from datetime import datetime, timezone, timedelta
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field

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
    "https://isisbramos.github.io/daily-scout/feedback.html",
)
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
SOCIAL_ENABLED = os.environ.get("SOCIAL_ENABLED", "false").lower() == "true"


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


# ── Curate & Write: Gemini (v3 — structured output + anti-hallucination) ──

# ── Pydantic schemas para structured output ──────────────────────────
class MainFind(BaseModel):
    title: str = Field(description="Título factual e descritivo, max 15 palavras")
    source: str = Field(description="Fonte real: HackerNews, r/MachineLearning, TechCrunch, Lobsters")
    body: str = Field(description="3-5 frases. Comece com atribuição à fonte. Explique o que é e por que importa pro leitor.")
    bullets: list[str] = Field(description="2-3 pontos-chave: o que aconteceu, o que significa, o que observar")
    url: str = Field(description="URL original do post")
    display_url: str = Field(description="Versão curta legível da URL")

class QuickFind(BaseModel):
    title: str = Field(description="Título curto e descritivo, max 10 palavras")
    source: str = Field(description="Fonte real")
    signal: str = Field(description="1-2 frases curtas: [o que aconteceu] + [por que importa pro leitor]")
    url: str = Field(description="URL original")
    display_url: str = Field(description="Versão curta da URL")

class Meta(BaseModel):
    total_analyzed: int = Field(description="Número total de posts analisados")
    sources_used: list[str] = Field(description="Lista de fontes usadas")
    editorial_note: str = Field(default="", description="Observação opcional sobre o dia")

class CurationOutput(BaseModel):
    correspondent_intro: str = Field(description="1-2 frases em primeira pessoa. Cite dados concretos.")
    main_find: MainFind
    quick_finds: list[QuickFind] = Field(description="3-5 achados rápidos")
    meta: Meta


# ── System instruction (pesa mais no attention do Flash) ─────────────
SYSTEM_INSTRUCTION = """Você é a AYA — analista de campo do Daily Scout, newsletter diária que cobre o mundo tech através da lente de AI. Seu público são profissionais curiosos que querem entender como AI está mudando tecnologia, negócios e trabalho.

RESTRIÇÃO FUNDAMENTAL: seu único input são títulos e metadados de posts. Você NÃO leu os artigos. Você NÃO tem acesso ao corpo dos artigos.

REGRA DE ACURÁCIA — O QUE PODE E O QUE NÃO PODE:

PODE (e deve):
- Explicar brevemente o que algo é: "Sora é a ferramenta de geração de vídeo da OpenAI", "Wine é uma camada de compatibilidade que roda apps Windows no Linux".
- Explicar por que algo é relevante pro leitor: "Isso afeta quem usa criptografia de ponta a ponta em apps como WhatsApp e Signal."
- Usar seu conhecimento para dar contexto factual curto sobre o que uma empresa/produto/tecnologia É.

NÃO PODE (nunca):
- Inventar reações, motivações, consequências ou análises que não estão no título. Nada de "gerou polêmica", "pegou de surpresa", "pode revolucionar".
- Inventar números, datas, valores ou detalhes que não estão nos metadados.
- Converter incerteza em fato. "may" → "estaria", "reportedly" → "segundo relatos", pergunta → "Post questiona se..."
- Qualificar intensidade com adjetivos vazios: nada de "massivo", "bombástico", "enorme", "pesado", "impressionante".

VOZ EDITORIAL — como escrever:
- Frases curtas e declarativas. Sujeito, verbo, complemento.
- Verbos factuais: "anunciou", "lançou", "reportou", "publicou", "atualizou", "levantou", "descontinuou".
- SEMPRE comece parágrafos com atribuição: "Segundo o TechCrunch", "De acordo com post no HackerNews".
- Cite valores, versões, nomes, números quando disponíveis. Quando não disponíveis, descreva sem qualificar a intensidade.
- Tom: competente e direto, como colunista que acompanha o mercado todo dia. Explique para leitores inteligentes que não são da área — dê contexto útil sem dramatizar."""

# ── User prompt (missão + few-shots + dados) ─────────────────────────
CURATION_PROMPT = """Selecione e escreva os achados do dia a partir dos posts abaixo.

PÚBLICO: profissionais curiosos sobre tech & AI. Não necessariamente técnicos, mas inteligentes e ocupados. Explique termos técnicos brevemente entre parênteses.

═══ PIPELINE DE SELEÇÃO ═══

STEP 1 — AI GATE (obrigatório):
O post tem conexão com AI/ML, modelos de linguagem, automação inteligente, ou decisões de empresas de AI?
→ SIM: continua pro Step 2.
→ NÃO: só entra se for evento de magnitude excepcional (aquisição >$1B, regulação governamental, shutdown de plataforma major). Caso contrário, DESCARTE.

STEP 2 — CRITÉRIOS (precisa de pelo menos 2 de 3):
1. Acionável — o leitor pode fazer algo concreto: testar ferramenta, mudar processo, tomar decisão
2. Sinal de mercado — revela movimento estratégico: player entrando/saindo de categoria, shift de política de dados, nova aliança/aquisição
3. Afeta workflows — muda como pessoas trabalham com tech/AI no dia a dia

STEP 3 — ANTI-SIGNAL (descarte imediato se o título se enquadra em):
→ Preço/assinatura de serviço consumer (Netflix, Spotify, Disney+)
→ Funding round sem ângulo AI/tech específico
→ Mercado financeiro/crypto/apostas sem aplicação de AI
→ Atualização de produto sem impacto em workflows (ex: UI redesign cosmético)
→ Confirmação do óbvio ("X vai continuar fazendo Y")

STEP 4 — RANKING:
→ main_find = item mais acionável OU com maior sinal de mercado. Tração (score) é tiebreaker, NUNCA critério principal.
→ quick_finds = 3-5 itens restantes que passaram nos steps anteriores.
→ Diversidade de fontes: prefira representação variada.

STEP 5 — TESTE FINAL:
Para cada item selecionado, complete UMA das frases abaixo. Se não conseguir completar com informação do título, DESCARTE o item:
→ "Agora é possível [ação concreta]"
→ "[Player] está [movendo pra / investindo em / saindo de] [categoria]"

═══ EXEMPLOS DE CALIBRAÇÃO ═══

Exemplo 1 — SELEÇÃO CORRETA (acionável + AI):
Input: { "title": "Gemini now lets you import chat history from ChatGPT and other chatbots", "source": "TechCrunch", "score": 89 }
→ AI gate: SIM (chatbots de AI)
→ Critérios: Acionável (posso migrar agora) + Sinal de mercado (Google competindo por lock-in)
→ Teste: "Agora é possível importar conversas de outros chatbots pro Gemini"
→ SELECIONADO como main_find
Output CORRETO: "Segundo o TechCrunch, o Gemini — chatbot de IA do Google — agora permite transferir conversas e informações pessoais de outros chatbots diretamente para ele. Isso facilita a migração de usuários entre plataformas de IA e centraliza o histórico de interações."

Exemplo 2 — DESCARTE CORRETO (alta tração, sem ângulo AI):
Input: { "title": "We haven't satisfactorily dealt with the worst of what prediction markets will do", "source": "HackerNews", "score": 539 }
→ AI gate: NÃO (mercados de previsão/apostas, sem conexão com AI)
→ Magnitude excepcional? NÃO (post de opinião, não evento)
→ DESCARTADO — 539 pontos de tração não salva post sem ângulo AI

Exemplo 3 — DESCARTE CORRETO (genérico, anti-signal):
Input: { "title": "Netflix confirms another price increase", "source": "TechCrunch", "score": 205 }
→ AI gate: NÃO (preço de streaming)
→ Anti-signal: preço/assinatura de serviço consumer
→ DESCARTADO — irrelevante para o público do Daily Scout

Exemplo 4 — TOM: RUMOR/ESPECULAÇÃO:
Input: { "title": "Report: OpenAI may shut down Sora after backlash", "source": "HackerNews", "score": 847 }
Output ERRADO (NÃO faça isso): "A OpenAI encerra o Sora, sua ferramenta de vídeo por IA. O Sora havia sido anunciado com grande alarde, prometendo revolucionar a criação de conteúdo visual."
→ Por que está errado: converteu "may" em fato, inventou "grande alarde", "revolucionar" — NADA disso está no título.
Output CORRETO: "Segundo post com alta tração no HackerNews (847 pontos), a OpenAI estaria considerando descontinuar o Sora — sua ferramenta de geração de vídeo por IA — após reações negativas. O Sora permite criar vídeos a partir de descrições em texto."

Exemplo 5 — TOM: BUSINESS com ângulo AI:
Input: { "title": "Stripe acquires AI payments startup PayAI for $1.2B", "source": "TechCrunch", "score": 0 }
→ AI gate: SIM (startup de AI payments)
→ Critérios: Sinal de mercado (Stripe apostando em AI pra pagamentos)
→ Teste: "Stripe está investindo em AI aplicada a pagamentos com aquisição de $1.2B"
→ SELECIONADO como quick_find
Output ERRADO (NÃO faça isso): "A Stripe fez uma aquisição bombástica que pode revolucionar o mercado de pagamentos com IA."
→ Por que está errado: "bombástica", "revolucionar" são qualificadores inventados.
Output CORRETO: "De acordo com o TechCrunch, a Stripe adquiriu a PayAI — startup de pagamentos com inteligência artificial — por US$ 1,2 bilhão. A aquisição sinaliza que AI está chegando ao core da infraestrutura de pagamentos online."

═══ REGRAS DE FORMATO ═══
- correspondent_intro: 1-2 frases curtas em primeira pessoa. Cite dado concreto (quantas fontes, qual tema se destacou, score).
- main_find.title: factual, max 15 palavras. Reformule se o original for sensacionalista.
- main_find.body: 3-5 frases. SEMPRE comece com atribuição ("Segundo [fonte]", "De acordo com [fonte]"). Depois, explique o que é e por que importa pro leitor.
- main_find.bullets: 2-3 pontos: o que aconteceu, o que significa pra quem lê, o que observar a seguir.
- quick_finds[].signal: 1-2 frases curtas explicando o que aconteceu e por que é relevante.
- Termos técnicos: explique brevemente — "LLM (modelos de IA que geram texto)", "open source (código aberto)".

LEMBRETE FINAL: Você PODE explicar o que algo é (contexto factual) e por que importa pro leitor. Você NÃO PODE inventar reações, consequências ou qualificar intensidade. Na dúvida: descreva, não qualifique.

POSTS COLETADOS:
"""


# ── Heurísticas anti-hallucination (pós-processamento) ───────────────
HYPE_PATTERNS = re.compile(
    r"(revolucion|bombástic|game.?changer|disruptiv|choque|chocou|impressionant[e]|"
    r"massiv[oa]|enorme[s]?|pesad[oa]|ousad[oa]|incrível|surpreendent[e]|"
    r"grande alarde|aposta pesada|mudou o jogo|pegou .+ de surpresa|"
    r"reviravolta|prometendo revolucionar|muito mais atraente|"
    r"pode mudar o cenário|entrand[oa] pesado)",
    re.IGNORECASE,
)


def validate_tone(content: dict) -> list[str]:
    """Checa heurísticas de sensacionalismo no output. Retorna lista de warnings."""
    warnings = []

    def _check_text(text: str, field_name: str):
        matches = HYPE_PATTERNS.findall(text)
        for match in matches:
            warnings.append(f"[HYPE] '{match}' encontrado em {field_name}")

    # Checa main_find
    mf = content.get("main_find", {})
    _check_text(mf.get("title", ""), "main_find.title")
    _check_text(mf.get("body", ""), "main_find.body")
    for i, bullet in enumerate(mf.get("bullets", [])):
        _check_text(bullet, f"main_find.bullets[{i}]")

    # Checa quick_finds
    for i, qf in enumerate(content.get("quick_finds", [])):
        _check_text(qf.get("title", ""), f"quick_finds[{i}].title")
        _check_text(qf.get("signal", ""), f"quick_finds[{i}].signal")

    # Checa correspondent_intro
    _check_text(content.get("correspondent_intro", ""), "correspondent_intro")

    return warnings


def curate_and_write(filtered_items: list[SourceItem], max_retries: int = 5) -> dict:
    """Envia items pré-filtrados para o Gemini e recebe curadoria estruturada (v3)."""
    from google import genai
    from google.genai import types

    logger.info("=" * 50)
    logger.info("PHASE 3: CURATE — Gemini processing (v3)")
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

    user_prompt = CURATION_PROMPT + json.dumps(
        items_for_prompt, ensure_ascii=False, indent=2
    )

    for attempt in range(max_retries):
        try:
            logger.info(f"Gemini attempt {attempt + 1}/{max_retries}...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=CurationOutput,
                    temperature=0.0,
                    max_output_tokens=8192,
                ),
            )

            text = response.text.strip()
            logger.info(f"Gemini returned {len(text)} chars")

            # Com response_schema, o Gemini retorna JSON válido por design
            content = json.loads(text)

            # Validação mínima de estrutura
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

            # ── v3: Tone validation (post-processing) ──
            tone_warnings = validate_tone(content)
            if tone_warnings:
                for w in tone_warnings:
                    logger.warning(w)
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Tone check failed with {len(tone_warnings)} issues — retrying "
                        f"(attempt {attempt + 1})"
                    )
                    time.sleep(2**attempt)
                    continue
                else:
                    logger.warning(
                        f"Last attempt: accepting with {len(tone_warnings)} tone warnings"
                    )

            logger.info(f"Curation OK: '{content['main_find']['title']}'")
            logger.info(f"Quick finds: {len(content.get('quick_finds', []))}")
            return content

        except json.JSONDecodeError as e:
            logger.warning(f"Attempt {attempt + 1}: invalid JSON — {e}")
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

        # ── Step 6: Send newsletter ──
        subject = f"Daily Scout #{EDITION_NUMBER} — {content['main_find']['title']}"
        if DRY_RUN:
            logger.info("DRY_RUN=true — skipping Buttondown send")
            success = True
        else:
            success = send_via_buttondown(subject, html)

        # ── Step 7: Generate social content (isolated — failures don't affect newsletter) ──
        social_success = False
        if SOCIAL_ENABLED:
            try:
                from social.content_adapter import adapt_for_linkedin, save_social_artifacts

                logger.info("=" * 50)
                logger.info("PHASE 7: SOCIAL — generating adapted content")
                logger.info("=" * 50)

                linkedin_data = adapt_for_linkedin(content)
                artifact_path = save_social_artifacts(linkedin_data, EDITION_NUMBER)
                social_success = artifact_path is not None

                if social_success:
                    logger.info(f"Social content ready for delayed posting: {artifact_path}")
                else:
                    logger.warning("Social adaptation failed — newsletter unaffected")

            except Exception as social_err:
                logger.warning(f"Social generation failed (non-blocking): {social_err}")
        else:
            logger.info("SOCIAL_ENABLED=false — skipping social content generation")

        # ── Report ──
        total_time = f"{time.time() - start_time:.1f}s"
        logger.info("=" * 50)
        logger.info("PIPELINE COMPLETE")
        logger.info(f"  Sources: {len(active_sources)} active ({', '.join(active_sources)})")
        logger.info(f"  Raw items: {len(raw_items)} → Filtered: {len(filtered_items)}")
        logger.info(f"  Main find: {content['main_find']['title']}")
        logger.info(f"  Quick finds: {len(content.get('quick_finds', []))}")
        logger.info(f"  Newsletter: {'OK' if success else 'FAILED'}")
        logger.info(f"  Social: {'OK' if social_success else 'SKIPPED' if not SOCIAL_ENABLED else 'FAILED'}")
        logger.info(f"  Runtime: {total_time}")
        logger.info("=" * 50)

        if not success:
            logger.warning("Newsletter delivery failed but HTML was saved as artifact")

    except Exception as e:
        logger.error(f"PIPELINE FAILED: {e}", exc_info=True)
        try:
            send_fallback(str(e))
        except Exception as fallback_err:
            logger.error(f"Fallback also failed: {fallback_err}")
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
