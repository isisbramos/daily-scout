"""
Daily Scout — Prompt v5.1 SUGGESTION
=====================================
Este arquivo NÃO é pra ser executado. É uma sugestão de melhoria do prompt
baseada no audit do pipeline v5.0 completo (10 sources + pre-filter v5).

Cada mudança está marcada com:
  # [SYNC-XX] ou [PE-XX] ou [JC-XX] ou [SE-XX] → finding do audit
  # CHANGED: descrição da mudança
  # WHY: razão da mudança

Para aplicar: copie os blocos relevantes pro pipeline.py.
"""

from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════════════
# PYDANTIC SCHEMAS (mudanças no schema)
# ════════════════════════════════════════════════════════════════════

class Reasoning(BaseModel):
    """Observability: registra o raciocínio editorial da AYA para debugging."""

    ai_gate_passed: list[str] = Field(
        # [PE-05] CHANGED: cap removido (antes era "max 15")
        # WHY: com 40 items no input e fontes AI-first (blogs), >15 passam no AI Gate.
        # Cap artificial perde observability. Custo em tokens é marginal (são títulos).
        description="Títulos que passaram no AI Gate"
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
        # [SYNC-01] CHANGED: removida lista hardcoded de 4 fontes
        # WHY: pipeline agora tem 10 fontes. Lista fixa no schema funciona como constraint
        # pro Gemini — ele pode forçar output pra um dos 4 nomes listados mesmo quando
        # o item veio do SCMP Tech ou Rest of World.
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
        # [PE-03] CHANGED: campo novo
        # WHY: STEP 5 (teste final) era honor-system — AYA podia dizer que fez o teste
        # sem realmente fazer. Este campo força enforcement estrutural + cria audit trail.
        # Custo: ~15-20 tokens por item. Benefício: verificabilidade.
        description="Frase completada do STEP 5 que justifica a seleção deste item (ex: 'Agora é possível [ação]' ou '[Player] está [movendo pra] [categoria]')"
    )


class QuickFind(BaseModel):
    title: str = Field(description="Título curto e descritivo, max 10 palavras")

    source: str = Field(
        # [SYNC-01] CHANGED: mesma correção do MainFind
        description="Fonte real do item — use exatamente o valor do campo 'source' no input"
    )

    signal: str = Field(description="1-2 frases curtas: [o que aconteceu] + [por que importa pro leitor]")
    url: str = Field(description="URL original")
    display_url: str = Field(description="Versão curta da URL")
    primary_audience: str = Field(
        description="Para quem este achado é mais relevante: 'developers', 'PMs e founders', 'business/executivos', ou 'todos'"
    )

    step5_phrase: str = Field(
        # [PE-03] CHANGED: campo novo (mesmo do MainFind)
        description="Frase completada do STEP 5 que justifica a seleção deste item"
    )


class Meta(BaseModel):
    total_analyzed: int = Field(description="Número total de posts analisados (use o valor informado no contexto do dia)")
    sources_used: list[str] = Field(description="Lista de fontes usadas")
    editorial_note: str = Field(default="", description="Observação opcional sobre o dia")


class CurationOutput(BaseModel):
    reasoning: Reasoning = Field(description="Raciocínio editorial — explique suas decisões de seleção")
    correspondent_intro: str = Field(description="1-2 frases em primeira pessoa. Cite dados concretos.")
    main_find: MainFind
    quick_finds: list[QuickFind] = Field(description="3-5 achados rápidos")
    meta: Meta


# ════════════════════════════════════════════════════════════════════
# SYSTEM INSTRUCTION (mudanças mínimas — a system instruction estava boa)
# ════════════════════════════════════════════════════════════════════

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

# Nota: system instruction sem mudanças substanciais. As melhorias são todas no user prompt.


# ════════════════════════════════════════════════════════════════════
# USER PROMPT (aqui estão as mudanças principais)
# ════════════════════════════════════════════════════════════════════

CURATION_PROMPT_TEMPLATE = """Selecione e escreva os achados do dia a partir dos posts abaixo.

{context_block}

{editorial_memory_block}

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
→ Items com campo "also_trending_on" indicam que o tema apareceu em múltiplas fontes independentes. Trate isso como sinal de relevância editorial e, ao escrever, mencione: "notícia reportada tanto no [source] quanto no [other_source]".

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
- Termos técnicos: explique brevemente — "LLM (modelos de IA que geram texto)", "open source (código aberto)".

LEMBRETE FINAL: Você PODE explicar o que algo é (contexto factual) e por que importa pro leitor. Você NÃO PODE inventar reações, consequências ou qualificar intensidade. Na dúvida: descreva, não qualifique.

POSTS COLETADOS:
"""


# ════════════════════════════════════════════════════════════════════
# CONTEXT BLOCK + EDITORIAL MEMORY (mudança no runtime)
# ════════════════════════════════════════════════════════════════════

# O context_block já existe e não muda. A novidade é o editorial_memory_block.

# [JC-03] CHANGED: novo bloco de memória editorial injetado no prompt
# WHY: sem contexto de edições anteriores, AYA trata cada edição como a primeira.
# Mesma história pode ser main_find em edições consecutivas. Com 10 fontes,
# re-cobertura é mais provável — memória é mais urgente que antes.

EDITORIAL_MEMORY_TEMPLATE = """═══ MEMÓRIA EDITORIAL (últimas edições) ═══
Abaixo estão os achados das últimas edições. Use para:
- NÃO repetir a mesma história como main_find, a menos que haja UPDATE significativo.
- Se incluir um item que atualiza algo já coberto, mencione o follow-up: "como reportamos na edição #X..."
- Se um tema frequente das últimas edições DESAPARECEU do feed hoje, considere mencionar na editorial_note.

{recent_editions_json}
"""

# Exemplo de como gerar o recent_editions_json:
#
# recent_editions = [
#     {
#         "edition": "006",
#         "date": "26/03/2026",
#         "main_find": "Google DeepMind lança Gemma 3 com pesos abertos",
#         "quick_finds": [
#             "EU começa a aplicar AI Act para sistemas de alto risco",
#             "Anthropic lança Claude com acesso a ferramentas externas",
#             "Baidu abre código do ERNIE 4.5 para competir com Llama"
#         ]
#     },
#     # ... últimas 2-3 edições
# ]
# editorial_memory_block = EDITORIAL_MEMORY_TEMPLATE.format(
#     recent_editions_json=json.dumps(recent_editions, ensure_ascii=False, indent=2)
# )
#
# Se não houver edições anteriores (primeira edição), usar string vazia:
# editorial_memory_block = ""


# ════════════════════════════════════════════════════════════════════
# SUMÁRIO DE MUDANÇAS (prompt v5.0 → v5.1)
# ════════════════════════════════════════════════════════════════════

CHANGELOG = """
═══ MUDANÇAS v5.0 → v5.1 ═══

PROMPT ↔ PIPELINE SYNC (fixes críticos):
─────────────────────────────────────────
[SYNC-01] MainFind.source / QuickFind.source
  ANTES: description="Fonte real: HackerNews, r/MachineLearning, TechCrunch, Lobsters"
  DEPOIS: description="Fonte real do item — use exatamente o valor do campo 'source' no input"
  WHY: Pipeline tem 10 fontes. Lista hardcoded fazia Gemini forçar output pra 4 nomes,
       "apagando" SCMP Tech, Rest of World, TechNode, blogs de AI labs.

[SYNC-02] 2 few-shots novos de fontes geográficas + 1 de AI lab blog
  ADICIONADO: Exemplo 7 (SCMP Tech — perspectiva China/AI)
  ADICIONADO: Exemplo 10 (Rest of World — perspectiva LatAm/governo)
  ADICIONADO: Exemplo 8 (Anthropic Blog — descarte de thought-leadership)
  WHY: Few-shots são o mecanismo mais forte de alignment. Sem calibração pra novas fontes,
       AYA sub-prioriza items de SCMP/RoW/TechNode por falta de pattern matching.

[SYNC-03] Instrução pra also_trending_on no STEP 4
  ADICIONADO: "Items com campo 'also_trending_on' indicam que o tema apareceu em múltiplas
               fontes independentes. Trate como sinal de relevância editorial."
  ADICIONADO: Exemplo 9 (cross-source signal com also_trending_on)
  WHY: Pipeline injeta also_trending_on mas prompt não instruía AYA sobre o que fazer.

[SYNC-04] STEP 1.5 generalizado
  ANTES: "para blogs oficiais de empresas de AI"
  DEPOIS: "para blogs oficiais de QUALQUER empresa" + instrução pra fontes jornalísticas
          reportando anúncios de blogs corporativos
  WHY: Com 10 fontes, items de blogs da Apple/Microsoft/Alibaba sobre AI também aparecem.
       A heurística precisa ser "blog corporativo" e não "blog de empresa de AI".

PROMPT ENGINEERING (refinamentos):
─────────────────────────────────────────
[PE-03] step5_phrase como campo obrigatório no schema
  ADICIONADO: MainFind.step5_phrase e QuickFind.step5_phrase
  CHANGED: STEP 5 agora diz "complete no campo step5_phrase" (enforcement estrutural)
  WHY: Antes era honor-system. Agora é verificável no post-processing e cria audit trail.

[PE-05] ai_gate_passed sem cap
  ANTES: "max 15"
  DEPOIS: sem limite
  WHY: Com 40 items no input e fontes AI-first, >15 passam. Cap perdia observability.

FEW-SHOTS (reorganização):
─────────────────────────────────────────
  REMOVIDOS: Exemplo 3 original (Netflix — descarte óbvio demais, não calibra)
             Exemplo 6 original (TSMC — substituído por geográfico mais impactante)
  MANTIDOS: Exemplos 1, 2, 4, 5 (agora renumerados como 1, 2, 4, 5)
            Exemplo 4 original → agora Exemplo 3 (rumor/especulação — calibração crítica)
            Exemplo 8 original → agora Exemplo 6 (open source — calibração importante)
  ADICIONADOS: Exemplo 7 (SCMP — geográfico), Exemplo 8 (Anthropic Blog — descarte),
               Exemplo 9 (cross-source), Exemplo 10 (Rest of World — LatAm)
  TOTAL: 10 few-shots (antes 8). +2 cobrindo gaps de diversidade geográfica e cross-source.
  TRADE-OFF: ~800 tokens extras. Aceitável dado max_items=40 e context window do Gemini Flash.

JORNALISMO & CURADORIA:
─────────────────────────────────────────
[JC-03] editorial_memory_block (memória editorial)
  ADICIONADO: template pra injetar últimas 3 edições no prompt
  REQUER: persistência de edições anteriores (JSON com title + quick_find_titles por edição)
  WHY: Evita repetição de main_find em edições consecutivas. Habilita conceito de follow-up.
  CUSTO: ~300 tokens extras. IMPACTO: alto — diferencial editorial raro em newsletters automatizadas.

[JC-07] primary_audience ativado no pipeline
  ANTES: campo existia mas sem instrução de uso
  DEPOIS: STEP 4 agora inclui "Diversidade de AUDIÊNCIA"
  WHY: Sem instrução, AYA defaultava pra 'todos'. Agora cria pressão editorial real.

═══ O QUE NÃO MUDOU (e por quê) ═══
- System instruction: estava limpa, sem overlap, sem necessidade de mudança.
- STEP 1 (AI Gate): funciona como designed, validado desde v4.
- STEP 2 (Critérios 2 de 3): equilibrado, não há evidência de falha.
- STEP 3 (Anti-signal): o princípio + exemplos é suficiente. Edge cases ambíguos
  são raros o bastante pra não justificar mais few-shots aqui.
- Regras de formato: estáveis.
- HYPE_PATTERNS regex: funciona como safety net, não precisa de mudança.

═══ MUDANÇAS QUE FICARAM FORA (backlog) ═══
- [SE-04] Rebalancear engagement_weight 0.4→0.3 → mudança no config, não no prompt
- [SE-07] Implementar category scoring real → mudança no pre_filter.py, não no prompt
- [SE-06] Recency decay variável por category → mudança no pre_filter.py
- [SE-05] max_per_source_pct 0.25→0.20 → mudança no config
- [PE-06] Retry informado no tone check → mudança no pipeline.py
- [JC-06] ArXiv como source → nova source, não afeta prompt
"""

# Para referência rápida, imprimir o changelog
if __name__ == "__main__":
    print(CHANGELOG)
