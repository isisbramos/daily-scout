"""
Daily Scout — Pydantic schemas para structured output do Gemini.
Separado do pipeline principal para facilitar testes e iteração.
"""

from pydantic import BaseModel, Field


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
    body: str = Field(description="3-5 frases. Comece com atribuição à fonte. NÃO reformule o título com as mesmas palavras/números — aprofunde só com contexto factual do que as coisas SÃO e consequência prática; nunca com mecanismo, comparação ou número que o título não traz. Termine com a linha '→ No seu trabalho: ...' — o que a notícia muda no trabalho de quem usa IA no dia a dia (decisão de ferramenta, workflow, fornecedor, custo ou risco). Não invente contexto que o título não sustenta.")
    bullets: list[str] = Field(description="Lista de 2-3 strings simples (texto corrido, NUNCA objeto/dicionário com label) que ACRESCENTAM ao título, não o repetem: um detalhe específico que o título NÃO cobre — não uma paráfrase dele —, o que isso significa, o que observar")
    url: str = Field(description="URL original do post")
    display_url: str = Field(description="Versão curta legível da URL")
    primary_audience: str = Field(
        description="Para quem este achado é mais relevante: 'desenvolvedores', 'product managers e fundadores', 'executivos de negócio', ou 'todos'"
    )
    step5_phrase: str = Field(
        # [PE-03] enforcement estrutural do STEP 5 + audit trail
        description="Frase completada do STEP 5 que justifica a seleção deste item (ex: 'Agora é possível [ação]' ou '[Empresa] está [movendo pra] [categoria]')"
    )
    claim_status: str = Field(
        description="Status factual do item: 'confirmado' (anúncio oficial, fonte primária), 'especulativo' (report, rumor, 'may', 'could'), ou 'em_andamento' (negociação, investigação, processo regulatório em curso)"
    )
    entities: list[str] = Field(
        default_factory=list,
        description="Entidades-chave citadas (empresas, modelos, pessoas, produtos). Usado pela memória editorial entre edições."
    )


class QuickFind(BaseModel):
    title: str = Field(description="Título curto e descritivo, max 10 palavras")
    source: str = Field(
        # [SYNC-01] sem lista hardcoded
        description="Fonte real do item — use exatamente o valor do campo 'source' no input"
    )
    signal: str = Field(description="2-3 frases: [o que aconteceu, com informação além do título] + [por que importa pro leitor] + [linha iniciada com '→ No seu trabalho:': o que a notícia muda no trabalho de quem usa IA no dia a dia — uma decisão que ele pode tomar, revisar ou acompanhar, sem inventar contexto que o título não sustenta]. NÃO reformule o título com as mesmas palavras/números. Baseado só em título/metadados — não invente mecanismo ou número que o título não sustenta; aprofunde conectando a um padrão do setor ou nomeando concretamente quem é afetado e como.")
    url: str = Field(description="URL original")
    display_url: str = Field(description="Versão curta da URL")
    follow_up: str = Field(
        default="",
        description="SÓ quando o item coincide com tema/entidades de edição recente mas traz fato novo: 1 frase dizendo o que é novo (ex: 'prometeu manter pesos abertos e lançou só como API'). Vazio quando não é follow-up. O sistema aceita no máximo 1 por edição e descarta repetição sem este campo."
    )
    primary_audience: str = Field(
        description="Para quem este achado é mais relevante: 'desenvolvedores', 'product managers e fundadores', 'executivos de negócio', ou 'todos'"
    )
    step5_phrase: str = Field(
        # [PE-03] enforcement estrutural do STEP 5
        description="Frase completada do STEP 5 que justifica a seleção deste item"
    )
    claim_status: str = Field(
        description="Status factual do item: 'confirmado' (anúncio oficial, fonte primária), 'especulativo' (report, rumor, 'may', 'could'), ou 'em_andamento' (negociação, investigação, processo regulatório em curso)"
    )
    entities: list[str] = Field(
        default_factory=list,
        description="Entidades-chave citadas (empresas, modelos, pessoas, produtos). Usado pela memória editorial entre edições."
    )


class RadarItem(BaseModel):
    title: str = Field(description="Título curto e descritivo, max 10 palavras")
    source: str = Field(
        description="Fonte real do item — use exatamente o valor do campo 'source' no input"
    )
    why_watch: str = Field(description="1 frase: por que vale acompanhar nos próximos dias (tom de 'cedo demais pra conclusão, mas...')")
    url: str = Field(description="URL original")
    display_url: str = Field(description="Versão curta da URL")


class EpistemicDistribution(BaseModel):
    produto: str = Field(default="", description="Título do item que cobre produto/lançamento, ou 'ausente — [motivo]'")
    pesquisa: str = Field(default="", description="Título do item que cobre pesquisa/dado/benchmark, ou 'ausente — [motivo]'")
    regulacao: str = Field(default="", description="Título do item que cobre regulação/crítica/análise de impacto, ou 'ausente — [motivo]'")


class Meta(BaseModel):
    total_analyzed: int = Field(description="Número total de posts analisados (use o valor informado no contexto do dia)")
    sources_used: list[str] = Field(description="Lista de fontes usadas")
    editorial_note: str = Field(default="", description="Observação opcional sobre o dia")
    epistemic_distribution: EpistemicDistribution = Field(
        default_factory=EpistemicDistribution,
        description="Categorias epistêmicas cobertas na curadoria. Para cada campo: título do item selecionado, ou 'ausente — [motivo]' se nenhum item cobriu aquela categoria."
    )


class CurationOutput(BaseModel):
    reasoning: Reasoning = Field(description="Raciocínio editorial — explique suas decisões de seleção")
    correspondent_intro: str = Field(description="1-2 frases em primeira pessoa. Dá o recorte do dia (o que liga os achados) SEM recontar o achado do dia, cujo título aparece logo abaixo; a segunda pode citar volume (X posts de Y fontes).")
    main_find: MainFind
    quick_finds: list[QuickFind] = Field(description="3-5 achados rápidos")
    radar: list[RadarItem] = Field(default_factory=list, description="1-2 itens de early signal — temas emergentes que ainda não são achados mas valem acompanhar")
    themes: list[str] = Field(default_factory=list, description="2-4 temas macro da edição (ex: 'agentes de código', 'regulação UE'). Usado pela memória editorial entre edições.")
    edition_headline: str = Field(default="", description="Assunto do e-mail: até 70 caracteres que encapsulam a edição inteira (o fio entre os achados). Não repete o main_find.title, não lista nomes, não cita fonte.")
    meta: Meta
