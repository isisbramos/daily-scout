"""
Daily Scout — Pipeline v5.0 (Multi-Source Architecture + Observability)
Correspondente: AYA (AI-powered field correspondent)
Stack: Multi-Source (Reddit, HN, TechCrunch, Lobsters) → Pre-Filter → Gemini Flash → Jinja2 → Buttondown API

Arquitetura:
  sources/ (pluggable modules) → pre_filter.py → Gemini curadoria → Jinja2 render → Buttondown delivery
  Config-driven: sources_config.json controla tudo sem mudar código.

v5 changes:
  - Reasoning schema: observability do julgamento editorial da AYA
  - Shuffle anti-bias: remove position bias na lista enviada ao LLM
  - Context injection: AYA sabe quantos items existiam antes do pre-filter
  - Few-shots expandidos: cobertura de infra, regulação, open source
  - STEP 5 expandido: 4 templates em vez de 2
  - Anti-signal generativo: princípio + exemplos em vez de lista fechada
  - Diversidade de perspectiva no STEP 4
  - primary_audience no schema (instrumentação para futuro)
"""

import html as html_lib
import os
import random
import re
import sys
import json
import time
import logging
import requests
from collections import Counter
from datetime import datetime, timezone, timedelta
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field

from sources.base import SourceRegistry, SourceItem
# Importar sources registra elas automaticamente no registry
import sources.reddit
import sources.hackernews
import sources.techcrunch
import sources.lobsters
import sources.rss_generic  # v5: AI lab blogs + geographic diversity sources
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

# ── Pydantic schemas para structured output (v5.1 — com observability + enforcement) ──

class Reasoning(BaseModel):
    """Observability: registra o raciocínio editorial da AYA para debugging."""
    ai_gate_passed: list[str] = Field(
        # [PE-05] cap de 10 pra evitar token overflow — lista os mais relevantes
        description="Até 10 títulos que passaram no AI Gate (priorize os que avançaram pra seleção final)"
    )
    ai_gate_rejected_sample: list[str] = Field(
        description="3-5 exemplos de títulos rejeitados no AI Gate com motivo curto entre parênteses"
    )
    main_find_rationale: str = Field(
        description="1-2 frases: por que este item foi escolhido como main_find e não os outros"
    )
    perspective_check: str = Field(
        description="1 frase: observação sobre diversidade de fontes/perspectivas nos itens selecionados"
    )

class MainFind(BaseModel):
    title: str = Field(description="Título factual e descritivo, max 15 palavras")
    source: str = Field(
        # [SYNC-01] sem lista hardcoded — pipeline tem 10 fontes
        description="Fonte real do item — use exatamente o valor do campo 'source' no input"
    )
    body: str = Field(description="3-5 frases. Comece com atribuição à fonte. Explique o que é e por que importa pro leitor.")
    bullets: list[str] = Field(description="2-3 pontos-chave: o que aconteceu, o que significa, o que observar")
    url: str = Field(description="URL original do post")
    display_url: str = Field(description="Versão curta legível da URL")
    primary_audience: str = Field(
        description="Para quem este achado é mais relevante: 'developers', 'PMs e founders', 'business/executivos', ou 'todos'"
    )
    step5_phrase: str = Field(
        # [PE-03] enforcement estrutural do STEP 5 + audit trail
        description="Frase completada do STEP 5 que justifica a seleção deste item (ex: 'Agora é possível [ação]' ou '[Player] está [movendo pra] [categoria]')"
    )

class QuickFind(BaseModel):
    title: str = Field(description="Título curto e descritivo, max 10 palavras")
    source: str = Field(
        # [SYNC-01] sem lista hardcoded
        description="Fonte real do item — use exatamente o valor do campo 'source' no input"
    )
    signal: str = Field(description="1-2 frases curtas: [o que aconteceu] + [por que importa pro leitor]")
    url: str = Field(description="URL original")
    display_url: str = Field(description="Versão curta da URL")
    primary_audience: str = Field(
        description="Para quem este achado é mais relevante: 'developers', 'PMs e founders', 'business/executivos', ou 'todos'"
    )
    step5_phrase: str = Field(
        # [PE-03] enforcement estrutural do STEP 5
        description="Frase completada do STEP 5 que justifica a seleção deste item"
    )

class RadarItem(BaseModel):
    title: str = Field(description="Título curto e descritivo, max 10 palavras")
    source: str = Field(
        description="Fonte real do item — use exatamente o valor do campo 'source' no input"
    )
    why_watch: str = Field(description="1 frase: por que vale acompanhar nos próximos dias (tom de 'cedo demais pra conclusão, mas...')")
    url: str = Field(description="URL original")
    display_url: str = Field(description="Versão curta da URL")

class Meta(BaseModel):
    total_analyzed: int = Field(description="Número total de posts analisados (use o valor informado no contexto do dia)")
    sources_used: list[str] = Field(description="Lista de fontes usadas")
    editorial_note: str = Field(default="", description="Observação opcional sobre o dia")

class CurationOutput(BaseModel):
    reasoning: Reasoning = Field(description="Raciocínio editorial — explique suas decisões de seleção")
    correspondent_intro: str = Field(description="1-2 frases em primeira pessoa. Cite dados concretos.")
    main_find: MainFind
    quick_finds: list[QuickFind] = Field(description="3-5 achados rápidos")
    radar: list[RadarItem] = Field(default_factory=list, description="1-2 itens de early signal — temas emergentes que ainda não são achados mas valem acompanhar")
    meta: Meta


# ── System instruction (v5 — persona + acurácia + tom; SEM overlap com user prompt) ──
SYSTEM_INSTRUCTION = """Você é a AYA — analista de campo do Daily Scout, newsletter diária que cobre o mundo tech através da lente de AI. Seu público são profissionais curiosos que querem entender como AI está mudando tecnologia, negócios e trabalho.

═══ RESTRIÇÃO FUNDAMENTAL ═══
Seu único input são títulos e metadados de posts. Você NÃO leu os artigos. Você NÃO tem acesso ao corpo dos artigos.

═══ REGRAS DE ACURÁCIA ═══

PODE (e deve):
- Explicar brevemente o que algo é: "Sora é a ferramenta de geração de vídeo da OpenAI".
- Explicar por que algo é relevante pro leitor: "Isso afeta quem usa criptografia de ponta a ponta."
- Usar seu conhecimento para dar contexto factual curto sobre o que uma empresa/produto/tecnologia É.

NÃO PODE (nunca):
- Inventar reações, motivações, consequências ou análises que não estão no título.
- Inventar números, datas, valores ou detalhes que não estão nos metadados.
- Qualificar intensidade com adjetivos vazios: nada de "massivo", "bombástico", "enorme", "pesado", "impressionante".

REGRA DE CERTEZA — ao traduzir/reformular, preserve o nível de certeza do título original:
- "may/might/could" → condicional: "estaria", "poderia"
- "reportedly/sources say" → atribuição: "segundo relatos"
- Pergunta no título → "Post questiona se..."
- NUNCA aumente nem diminua a certeza do original.

═══ VOZ EDITORIAL ═══
- Frases curtas e declarativas. Sujeito, verbo, complemento.
- Verbos factuais: "anunciou", "lançou", "reportou", "publicou", "atualizou", "levantou", "descontinuou".
- Tom: competente e direto, como colunista que acompanha o mercado todo dia. Dê contexto útil sem dramatizar.
- Explique para leitores inteligentes que não são da área — termos técnicos ganham explicação breve entre parênteses."""

# ── User prompt (v5.1 — missão + pipeline + few-shots + formato) ──────
# Nota: {context_block} é injetado em runtime por curate_and_write()
CURATION_PROMPT_TEMPLATE = """Selecione e escreva os achados do dia a partir dos posts abaixo.

{context_block}

═══ PIPELINE DE SELEÇÃO (execute na ordem) ═══

STEP 1 — AI GATE (obrigatório):
O post tem conexão com AI/ML, modelos de linguagem, automação inteligente, ou decisões de empresas de AI?
→ SIM: continua pro Step 2.
→ NÃO: só entra se for evento de magnitude excepcional (aquisição >$1B, regulação governamental, shutdown de plataforma major). Caso contrário, DESCARTE.

STEP 1.5 — SOURCE BIAS CHECK (para blogs oficiais de QUALQUER empresa):
Se a fonte original é um blog corporativo oficial (ex: blog.anthropic.com, openai.com/blog, deepmind.google, blog.google, developer.apple.com, aws.amazon.com/blogs):
→ O post anuncia algo que USUÁRIOS podem usar/testar agora? → Tratar normalmente.
→ O post é marketing/thought-leadership/branding sem novidade concreta? → DESCARTE.
→ A informação já foi coberta por outra fonte na lista? → Preferir a cobertura independente.
Aplica a mesma lógica quando uma fonte jornalística (SCMP, TechCrunch, Rest of World) está reportando um anúncio de blog corporativo — avalie o conteúdo original, não a cobertura.

STEP 2 — CRITÉRIOS (precisa de pelo menos 2 de 3):
1. Acionável — o leitor pode fazer algo concreto: testar ferramenta, mudar processo, tomar decisão
2. Sinal de mercado — revela movimento estratégico: player entrando/saindo de categoria, shift de política de dados, nova aliança/aquisição
3. Afeta workflows — muda como pessoas trabalham com tech/AI no dia a dia

STEP 3 — ANTI-SIGNAL:
Descarte posts que NÃO passaram no AI Gate E não são magnitude excepcional. Exemplos frequentes de anti-signal:
→ Preço/assinatura de serviço consumer (Netflix, Spotify, Disney+)
→ Funding round sem ângulo AI/tech específico
→ Mercado financeiro/crypto/apostas sem aplicação de AI
→ Atualização de produto sem impacto em workflows (ex: UI redesign cosmético)
→ Confirmação do óbvio ("X vai continuar fazendo Y")
→ Hardware reviews, gaming news, celebrity tech takes sem ângulo AI
Se um post não se enquadra nesses exemplos mas claramente foge do escopo AI/tech relevante, DESCARTE também. Use o princípio, não apenas a lista.

STEP 4 — RANKING:
→ main_find = item mais acionável OU com maior sinal de mercado. Tração (score) é tiebreaker, NUNCA critério principal.
→ quick_finds = 3-5 itens restantes que passaram nos steps anteriores.
→ Diversidade de fontes: prefira representação variada de sources.
→ Diversidade de PERSPECTIVA: se todos os quick_finds são product launches, priorize pelo menos 1 item que traga perspectiva diferente (regulação, open source, research, mercado emergente, crítica fundamentada).
→ Diversidade de AUDIÊNCIA: se todos os quick_finds têm primary_audience='developers', priorize pelo menos 1 item para audiência diferente.
→ Diversidade GEOGRÁFICA: no máximo 2 itens (entre main_find + quick_finds) podem ser da mesma região geográfica (ex: China/Asia). Se houver 3+ itens asiáticos fortes, escolha os 2 melhores e descarte o resto em favor de diversidade.
→ Items com campo "also_trending_on" indicam que o tema apareceu em múltiplas fontes independentes. Trate isso como sinal de relevância editorial e, ao escrever, mencione: "notícia reportada tanto no [source] quanto no [other_source]".

STEP 4.5 — RADAR (early signals):
→ Após selecionar main_find e quick_finds, olhe para os itens restantes que passaram no AI Gate mas ficaram de fora.
→ Selecione 1-2 itens que são "cedo demais pra ser achado" mas vale acompanhar: temas emergentes, discussões ganhando tração, sinais fracos de mercado.
→ Esses itens entram no campo "radar" com tom diferente: "vale acompanhar", "ainda cedo, mas...", "pode virar notícia nos próximos dias".
→ Se nenhum item justifica radar, deixe a lista vazia. NÃO force itens fracos aqui.

STEP 5 — TESTE FINAL:
Para cada item selecionado, complete UMA das frases abaixo no campo step5_phrase. Se não conseguir completar com informação do título, DESCARTE o item:
→ "Agora é possível [ação concreta]" — para features e ferramentas
→ "[Player] está [movendo pra / investindo em / saindo de] [categoria]" — para M&A e estratégia
→ "[Resultado/dado] muda o que sabíamos sobre [área]" — para research e benchmarks
→ "[Autoridade] decidiu [ação] sobre [tema de AI/tech]" — para regulação e policy

═══ EXEMPLOS DE CALIBRAÇÃO ═══

Exemplo 1 — SELEÇÃO CORRETA (acionável + AI):
Input: {{ "title": "Gemini now lets you import chat history from ChatGPT and other chatbots", "source": "TechCrunch", "score": 89 }}
→ AI gate: SIM (chatbots de AI)
→ Critérios: Acionável (posso migrar agora) + Sinal de mercado (Google competindo por lock-in)
→ step5_phrase: "Agora é possível importar conversas de outros chatbots pro Gemini"
→ SELECIONADO como main_find
Output CORRETO: "Segundo o TechCrunch, o Gemini — chatbot de IA do Google — agora permite transferir conversas e informações pessoais de outros chatbots diretamente para ele. Isso facilita a migração de usuários entre plataformas de IA e centraliza o histórico de interações."

Exemplo 2 — DESCARTE CORRETO (alta tração, sem ângulo AI):
Input: {{ "title": "We haven't satisfactorily dealt with the worst of what prediction markets will do", "source": "HackerNews", "score": 539 }}
→ AI gate: NÃO (mercados de previsão/apostas, sem conexão com AI)
→ Magnitude excepcional? NÃO (post de opinião, não evento)
→ DESCARTADO — 539 pontos de tração não salva post sem ângulo AI

Exemplo 3 — TOM: RUMOR/ESPECULAÇÃO:
Input: {{ "title": "Report: OpenAI may shut down Sora after backlash", "source": "HackerNews", "score": 847 }}
Output ERRADO (NÃO faça isso): "A OpenAI encerra o Sora, sua ferramenta de vídeo por IA. O Sora havia sido anunciado com grande alarde, prometendo revolucionar a criação de conteúdo visual."
→ Por que está errado: converteu "may" em fato, inventou "grande alarde", "revolucionar" — NADA disso está no título.
Output CORRETO: "Segundo post com alta tração no HackerNews (847 pontos), a OpenAI estaria considerando descontinuar o Sora — sua ferramenta de geração de vídeo por IA — após reações negativas. O Sora permite criar vídeos a partir de descrições em texto."

Exemplo 4 — TOM: BUSINESS com ângulo AI:
Input: {{ "title": "Stripe acquires AI payments startup PayAI for $1.2B", "source": "TechCrunch", "score": 0 }}
→ AI gate: SIM (startup de AI payments)
→ Critérios: Sinal de mercado (Stripe apostando em AI pra pagamentos)
→ step5_phrase: "Stripe está investindo em AI aplicada a pagamentos com aquisição de $1.2B"
→ SELECIONADO como quick_find
Output CORRETO: "De acordo com o TechCrunch, a Stripe adquiriu a PayAI — startup de pagamentos com inteligência artificial — por US$ 1,2 bilhão. A aquisição sinaliza que AI está chegando ao core da infraestrutura de pagamentos online."

Exemplo 5 — SELEÇÃO CORRETA (regulação + AI):
Input: {{ "title": "EU begins enforcing AI Act transparency requirements for high-risk systems", "source": "TechCrunch", "score": 45 }}
→ AI gate: SIM (regulação de AI)
→ Critérios: Sinal de mercado (Europa impondo regras) + Afeta workflows (empresas precisam se adequar)
→ step5_phrase: "UE decidiu começar a aplicar requisitos de transparência do AI Act"
→ SELECIONADO como quick_find — score baixo (45) mas relevância editorial alta
Output CORRETO: "De acordo com o TechCrunch, a União Europeia começou a aplicar os requisitos de transparência do AI Act para sistemas classificados como alto risco. Empresas que operam na Europa precisam documentar como seus modelos de AI tomam decisões."

Exemplo 6 — SELEÇÃO CORRETA (open source release):
Input: {{ "title": "Meta releases Llama 4 Scout and Maverick with Apache 2.0 license", "source": "r/MachineLearning", "score": 1200 }}
→ AI gate: SIM (release de modelo de AI open source)
→ Critérios: Acionável (desenvolvedores podem baixar e usar agora) + Sinal de mercado (Meta mantendo estratégia open source)
→ step5_phrase: "Agora é possível usar Llama 4 com licença Apache 2.0"
→ SELECIONADO como main_find
Output CORRETO: "Segundo post no r/MachineLearning, a Meta lançou o Llama 4 em duas versões — Scout e Maverick — com licença Apache 2.0 (código aberto). A licença permite uso comercial sem restrições, o que amplia o acesso a modelos de grande porte fora das APIs pagas."

Exemplo 7 — SELEÇÃO CORRETA (perspectiva geográfica + AI):
Input: {{ "title": "Baidu open-sources ERNIE 4.5 to compete with Llama in Chinese market", "source": "SCMP Tech", "score": 0 }}
→ AI gate: SIM (open source AI model)
→ Critérios: Sinal de mercado (competição China vs Meta em open source) + Acionável (devs podem testar)
→ step5_phrase: "Agora é possível usar ERNIE 4.5 open source como alternativa ao Llama"
→ SELECIONADO como quick_find — perspectiva geográfica diferenciada
Output CORRETO: "Segundo o SCMP Tech, a Baidu — maior empresa de buscas da China — liberou o ERNIE 4.5 como open source para competir com o Llama da Meta no mercado chinês. A China é o segundo maior ecossistema de AI do mundo e a competição de modelos abertos pode acelerar o acesso fora do eixo americano."

Exemplo 8 — DESCARTE CORRETO (blog oficial, thought-leadership sem novidade):
Input: {{ "title": "Our approach to building safe and beneficial AI systems", "source": "Anthropic Blog", "score": 0 }}
→ AI gate: SIM (empresa de AI falando sobre AI)
→ STEP 1.5: blog oficial da Anthropic. Anuncia feature testável? NÃO. É thought-leadership/branding. Coberto por outra fonte? N/A.
→ DESCARTADO — blog oficial sem novidade concreta para o leitor

Exemplo 9 — SELEÇÃO CORRETA (cross-source signal):
Input: {{ "title": "Google DeepMind releases Gemma 3 with open weights", "source": "TechCrunch", "score": 67, "also_trending_on": ["hackernews", "reddit"] }}
→ AI gate: SIM (release de modelo AI)
→ Cross-source signal: apareceu em 3 fontes independentes — alta relevância
→ Critérios: Acionável (devs podem usar) + Sinal de mercado (Google apostando em open weights)
→ step5_phrase: "Agora é possível usar Gemma 3 com pesos abertos do DeepMind"
→ SELECIONADO como main_find — cross-source signal reforça relevância
Output CORRETO: "De acordo com o TechCrunch — notícia também em destaque no HackerNews e Reddit — o Google DeepMind lançou o Gemma 3 com pesos abertos (open weights). Isso permite que desenvolvedores rodem o modelo localmente sem depender de APIs pagas."

Exemplo 10 — SELEÇÃO CORRETA (Global South + AI impact):
Input: {{ "title": "Brazil's Serpro deploys AI to automate 40% of federal tax audits", "source": "Rest of World", "score": 0 }}
→ AI gate: SIM (AI em governo)
→ Critérios: Afeta workflows (automação de auditoria fiscal) + Sinal de mercado (governo brasileiro apostando em AI)
→ step5_phrase: "Serpro está investindo em AI para automatizar auditorias fiscais federais"
→ SELECIONADO como quick_find — perspectiva LatAm relevante pro público brasileiro
Output CORRETO: "Segundo o Rest of World, o Serpro — empresa de tecnologia do governo federal brasileiro — implementou inteligência artificial para automatizar 40% das auditorias fiscais. É um sinal concreto de que AI está entrando na operação pública no Brasil."

═══ REGRAS DE FORMATO ═══
- reasoning: preencha ANTES de escrever os achados. Liste quais títulos passaram/falharam no AI Gate e explique a escolha do main_find.
- correspondent_intro: 1-2 frases curtas em primeira pessoa. Cite dado concreto do contexto do dia (total de fontes, quantos posts analisados, qual tema dominou).
- main_find.title: factual, max 15 palavras. Reformule se o original for sensacionalista.
- main_find.body: 3-5 frases. SEMPRE comece com atribuição ("Segundo [fonte]", "De acordo com [fonte]"). Depois, explique o que é e por que importa pro leitor.
- main_find.bullets: 2-3 pontos: o que aconteceu, o que significa pra quem lê, o que observar a seguir.
- main_find.step5_phrase: a frase do STEP 5 completada que justificou a seleção.
- quick_finds[].signal: 1-2 frases curtas explicando o que aconteceu e por que é relevante.
- quick_finds[].step5_phrase: a frase do STEP 5 completada.
- primary_audience: indique para quem cada achado é mais relevante ('developers', 'PMs e founders', 'business/executivos', ou 'todos').
- radar[].why_watch: 1 frase com tom de "cedo demais pra conclusão, mas vale ficar de olho". NÃO use o mesmo formato de quick_finds.
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


def curate_and_write(
    filtered_items: list[SourceItem],
    raw_count: int = 0,
    source_breakdown: dict[str, int] | None = None,
    max_retries: int = 5,
) -> dict:
    """Envia items pré-filtrados para o Gemini e recebe curadoria estruturada (v5).

    v5 changes:
    - Shuffle dos items para remover position bias
    - Context injection: AYA sabe quantos items existiam originalmente
    - Reasoning schema para observability
    """
    from google import genai
    from google.genai import types

    logger.info("=" * 50)
    logger.info("PHASE 3: CURATE — Gemini processing (v5)")
    logger.info("=" * 50)

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY não configurada")

    client = genai.Client(api_key=GEMINI_API_KEY)

    # ── v5: Shuffle para remover position bias ──
    # O pre-filter já selecionou os top N; a ordem interna não carrega
    # informação útil mas carrega viés (primacy effect no LLM).
    shuffled_items = list(filtered_items)
    random.shuffle(shuffled_items)
    logger.info(f"Shuffled {len(shuffled_items)} items to remove position bias")

    # Prepara input normalizado (com source info + v5: cross-source signal)
    items_for_prompt = []
    for item in shuffled_items:
        entry = {
            "title": item.title[:200],
            "source": item.source_label,
            "source_id": item.source_id,
            "score": item.raw_score,
            "comments": item.num_comments,
            "category": item.category,
            "url": item.url,
        }
        # v5: inclui cross-source signal quando item apareceu em múltiplas fontes
        if item.cross_source_count > 1:
            entry["also_trending_on"] = [
                sid for sid in item.cross_source_ids if sid != item.source_id
            ]
        items_for_prompt.append(entry)

    # ── v5: Context injection — AYA sabe o que existia antes do pre-filter ──
    source_counts = Counter(item.source_id for item in shuffled_items)
    sources_in_input = ", ".join(f"{sid} ({cnt})" for sid, cnt in source_counts.items())

    if raw_count and source_breakdown:
        breakdown_str = ", ".join(f"{sid}: {cnt}" for sid, cnt in source_breakdown.items())
        context_block = (
            f"CONTEXTO DO DIA: O pipeline coletou {raw_count} posts de "
            f"{len(source_breakdown)} fontes ({breakdown_str}). "
            f"Após pré-filtragem automática, você está recebendo os {len(shuffled_items)} "
            f"mais relevantes: {sources_in_input}. "
            f"Use o valor {raw_count} como total_analyzed no meta."
        )
    else:
        context_block = (
            f"CONTEXTO DO DIA: Você está recebendo {len(shuffled_items)} posts "
            f"pré-filtrados de: {sources_in_input}."
        )

    user_prompt = CURATION_PROMPT_TEMPLATE.format(
        context_block=context_block
    ) + json.dumps(items_for_prompt, ensure_ascii=False, indent=2)

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
                    max_output_tokens=16384,
                ),
            )

            # ── v5.2: Detecta truncação antes de tentar parse ──
            finish_reason = None
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = response.candidates[0].finish_reason

            text = response.text.strip()
            logger.info(f"Gemini returned {len(text)} chars (finish_reason={finish_reason})")

            if finish_reason and str(finish_reason) not in ("STOP", "FinishReason.STOP", "1"):
                raise ValueError(
                    f"Gemini output truncated (finish_reason={finish_reason}, "
                    f"{len(text)} chars) — likely hit max_output_tokens"
                )

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

            # ── v5: Log reasoning para observability ──
            reasoning = content.get("reasoning", {})
            if reasoning:
                passed = reasoning.get("ai_gate_passed", [])
                rejected = reasoning.get("ai_gate_rejected_sample", [])
                rationale = reasoning.get("main_find_rationale", "")
                perspective = reasoning.get("perspective_check", "")
                logger.info(f"[REASONING] AI Gate passed: {len(passed)} items")
                for r in rejected[:3]:
                    logger.info(f"  [REJECTED] {r}")
                logger.info(f"  [RATIONALE] {rationale}")
                logger.info(f"  [PERSPECTIVE] {perspective}")

            # ── v5.2: Ensure radar field exists ──
            if "radar" not in content:
                content["radar"] = []

            logger.info(f"Curation OK: '{content['main_find']['title']}'")
            logger.info(f"Quick finds: {len(content.get('quick_finds', []))}")
            logger.info(f"Radar items: {len(content.get('radar', []))}")
            for ri in content.get("radar", []):
                logger.info(f"  [RADAR] {ri.get('title', 'N/A')}: {ri.get('why_watch', '')}")
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
    radar = content.get("radar", [])
    meta = content.get("meta", {})

    # Sources detail string
    sources_detail = " + ".join(
        s.replace("_", " ").title() for s in active_sources
    )

    # Total finds includes radar
    total_finds = len(quick_finds) + 1 + len(radar)

    html = template.render(
        correspondent_intro=content.get("correspondent_intro", ""),
        main_find=content["main_find"],
        quick_finds=quick_finds,
        radar=radar,
        edition_number=EDITION_NUMBER,
        date=now_brt.strftime("%d/%m/%Y"),
        sources_count=raw_count,
        finds_count=total_finds,
        sources_detail=sources_detail,
        active_sources=active_sources,
        num_sources=len(active_sources),
        posts_analyzed=meta.get("total_analyzed", filtered_count),
        signal_ratio=f"{total_finds}/{meta.get('total_analyzed', filtered_count)}",
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
            if isinstance(conf, dict) and conf.get("enabled", True)
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

        # ── Step 3: Curate (v5: com context injection) ──
        source_breakdown = {}
        for item in raw_items:
            source_breakdown[item.source_id] = source_breakdown.get(item.source_id, 0) + 1

        content = curate_and_write(
            filtered_items,
            raw_count=len(raw_items),
            source_breakdown=source_breakdown,
        )

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
