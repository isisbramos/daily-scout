import { useState } from "react";

const SEVERITY = { P0: "#EF4444", P1: "#F59E0B", P2: "#3B82F6", OK: "#22C55E", FIXED: "#6B7280" };
const LENS_COLORS = {
  "Prompt ↔ Pipeline Sync": "#EF4444",
  "Prompt Engineering": "#8B5CF6",
  "Jornalismo & Curadoria": "#EC4899",
  "Sociologia & Estatística": "#06B6D4",
};

const findings = [
  // ── PROMPT ↔ PIPELINE SYNC (nova lente — gaps entre o que o prompt diz e o que o código faz) ──
  {
    id: "SYNC-01",
    lens: "Prompt ↔ Pipeline Sync",
    severity: "P0",
    title: "MainFind.source field só lista 4 fontes — pipeline tem 10",
    summary: "O schema diz 'Fonte real: HackerNews, r/MachineLearning, TechCrunch, Lobsters'. Mas agora existem Anthropic Blog, OpenAI Blog, DeepMind Blog, SCMP Tech, Rest of World e TechNode. AYA não sabe que pode citar essas fontes.",
    detail: "O campo source do MainFind tem uma description fixa que lista apenas as 4 fontes originais. Com o Gemini usando response_schema, essa description funciona como constraint — o modelo pode forçar o output pra um dos 4 nomes listados mesmo quando o item veio do SCMP ou Rest of World. Isso é um bug silencioso: a fonte real é descartada no schema.",
    recommendation: "Atualizar MainFind.source e QuickFind.source descriptions para: 'Fonte real do item — use o valor exato do campo source no input.' Remover a lista hardcoded. Mesma correção no few-shot que diz 'Fonte real: HackerNews, r/MachineLearning, TechCrunch, Lobsters'.",
    code: `# ANTES\nsource: str = Field(description="Fonte real: HackerNews, r/MachineLearning, TechCrunch, Lobsters")\n\n# DEPOIS\nsource: str = Field(description="Fonte real do item — use exatamente o valor do campo 'source' no input")`,
  },
  {
    id: "SYNC-02",
    lens: "Prompt ↔ Pipeline Sync",
    severity: "P0",
    title: "Zero few-shots das novas fontes — AYA nunca viu output de SCMP, Rest of World ou TechNode",
    summary: "Os 8 few-shots usam exclusivamente HackerNews, TechCrunch e r/MachineLearning. AYA não tem calibração pra escrever sobre fontes asiáticas ou Global South.",
    detail: "Few-shots são o mecanismo mais forte de alignment em prompts. Se AYA nunca viu um exemplo de 'Segundo o South China Morning Post Tech...' ou 'De acordo com o Rest of World...', ela vai: (1) não priorizar esses items por falta de pattern matching, (2) possivelmente reformular a atribuição de forma inconsistente, (3) perder nuances de perspectiva geográfica. O STEP 4 pede 'diversidade de perspectiva' mas os exemplos não demonstram como fazer.",
    recommendation: "Adicionar 2 few-shots: um de fonte geográfica (SCMP ou Rest of World com ângulo AI na Ásia/LatAm) e um de AI lab blog (demonstrando o STEP 1.5 na prática). Manter os 8 atuais e usar os 10 como pool, ou substituir os exemplos 3 e 6 que são mais previsíveis.",
    code: `# Exemplo novo sugerido — Geographic source + AI angle:\nExemplo 9 — SELEÇÃO CORRETA (perspectiva geográfica + AI):\nInput: {{ "title": "Baidu open-sources Ernie 4.5 to compete with Llama in China market", "source": "SCMP Tech", "score": 0 }}\n→ AI gate: SIM (open source model release)\n→ Critérios: Sinal de mercado (competição China vs Meta em open source) + Acionável (devs podem testar)\n→ Teste: "Agora é possível usar Ernie 4.5 open source como alternativa ao Llama na Ásia"\n→ SELECIONADO como quick_find — perspectiva geográfica diferente\nOutput CORRETO: "Segundo o SCMP Tech, a Baidu liberou o Ernie 4.5 — seu modelo de linguagem — como open source para competir com o Llama da Meta no mercado chinês. A China é o segundo maior mercado de AI do mundo e a competição em modelos abertos pode acelerar o acesso fora do ecossistema americano."`,
  },
  {
    id: "SYNC-03",
    lens: "Prompt ↔ Pipeline Sync",
    severity: "P1",
    title: "also_trending_on é injetado no input mas o prompt não instrui AYA sobre o que fazer com ele",
    summary: "O pipeline injeta 'also_trending_on' quando um item aparece em múltiplas fontes. Mas a CURATION_PROMPT não menciona esse campo. AYA pode ignorá-lo.",
    detail: "O cross-source signal é uma feature poderosa do pre-filter v5 — transforma dedup em informação editorial. Mas sem instrução no prompt, o modelo não sabe que 'also_trending_on: [\"reddit\"]' significa 'este tema está gerando tração cross-platform'. É metadata sem semântica no prompt.",
    recommendation: "Adicionar no STEP 4 — RANKING: 'Items com campo also_trending_on indicam que o tema apareceu em múltiplas fontes independentes — trate isso como sinal de relevância editorial.' E no formato: 'Se o item tem also_trending_on, mencione na atribuição: \"notícia que apareceu tanto no [source] quanto no [other source]\".'",
  },
  {
    id: "SYNC-04",
    lens: "Prompt ↔ Pipeline Sync",
    severity: "P1",
    title: "STEP 1.5 agora é testável — blogs oficiais estão no feed, mas exemplos são teóricos",
    summary: "Com Anthropic/OpenAI/DeepMind blogs como sources reais, o STEP 1.5 vai ser executado de verdade agora. Mas não há few-shot mostrando descarte de marketing de AI lab.",
    detail: "Antes, o STEP 1.5 era preventivo — 'se aparecer um blog oficial'. Agora é operacional: todo dia vai chegar conteúdo do blog da Anthropic, OpenAI e DeepMind. Sem um few-shot de descarte ('thought leadership sem novidade concreta → DESCARTE'), AYA vai tender a manter tudo de AI labs porque passa no AI Gate automaticamente.",
    recommendation: "Adicionar 1 few-shot de descarte de blog oficial: Input: {{ \"title\": \"Our approach to responsible AI development\", \"source\": \"Anthropic Blog\", \"score\": 0 }} → STEP 1.5: blog oficial, thought leadership sem feature concreta → DESCARTADO.",
  },
  {
    id: "SYNC-05",
    lens: "Prompt ↔ Pipeline Sync",
    severity: "P2",
    title: "Banner do pipeline diz v3.0 mas o código é v5.0",
    summary: "run_pipeline() loga 'PIPELINE v3.0 (Multi-Source)' no banner. O docstring e todo o resto diz v5. Cosmético mas confunde no debugging.",
    detail: "Quem olhar os logs vai ver v3.0 no banner e v5 features (cross-source, wild cards, z-score) nos detalhes.",
    recommendation: "Atualizar o banner: 'PIPELINE v5.0 (Multi-Source + Observability)'.",
  },

  // ── PROMPT ENGINEERING ──
  {
    id: "PE-01",
    lens: "Prompt Engineering",
    severity: "OK",
    title: "System ↔ User separation continua limpa",
    summary: "Persona + acurácia no system, pipeline + few-shots no user. Sem overlap. Isso está sólido desde a v4.",
    detail: null,
    recommendation: null,
  },
  {
    id: "PE-02",
    lens: "Prompt Engineering",
    severity: "OK",
    title: "Structured output + Pydantic + Reasoning schema",
    summary: "CurationOutput com Reasoning embutido é elegante — observability sem poluir template. temperature=0.0 correto pra curadoria determinística.",
    detail: null,
    recommendation: null,
  },
  {
    id: "PE-03",
    lens: "Prompt Engineering",
    severity: "P1",
    title: "STEP 5 (Teste Final) é honor-system — sem enforcement no schema",
    summary: "O teste pede pra AYA 'completar UMA das 4 frases'. Mas não há campo no schema que force isso — AYA pode dizer que fez sem realmente fazer.",
    detail: "Comparado com o reasoning (que TEM schema obrigando preenchimento), o teste final é instrução textual sem validação. O Gemini pode skippá-lo silenciosamente, especialmente quando o prompt fica longo com muitos items.",
    recommendation: "Adicionar step5_phrase: str no MainFind e QuickFind, com description 'Frase do STEP 5 completada para este item'. Isso cria enforcement + audit trail. Custo: ~20 tokens extras por item, audit trail valioso.",
  },
  {
    id: "PE-04",
    lens: "Prompt Engineering",
    severity: "P1",
    title: "Prompt token budget cresceu — 8 few-shots + 40 items + reasoning",
    summary: "Com max_items=40 (antes 30) e reasoning schema, o input total pode chegar a 8-9K tokens. Os 8 few-shots consomem ~3.5K tokens fixos. Ratio instrução/dados está comprimindo.",
    detail: "Gemini Flash tem context window grande, mas attention allocation em prompts longos favorece início e fim. Com 40 items no meio do prompt, items no centro podem receber menos atenção — ironicamente re-introduzindo position bias que o shuffle tentou resolver.",
    recommendation: "Duas opções: (1) Consolidar few-shots — mover 3 exemplos mais previsíveis (2, 3, 6) para um 'calibration block' no system instruction, mantendo 5 no user prompt. (2) Testar empiricamente: rodar com 5 vs 8 few-shots e comparar quality via feedback loop.",
  },
  {
    id: "PE-05",
    lens: "Prompt Engineering",
    severity: "P2",
    title: "ai_gate_passed cap de 15 limita observability",
    summary: "Com 40 items no input (antes 30), é provável que 20+ passem no AI Gate. O cap de 15 perde metade da visibilidade.",
    detail: "O campo é description='Títulos que passaram no AI Gate (max 15)'. Com mais items e fontes AI-first (blogs da Anthropic, OpenAI, DeepMind), a taxa de passagem no AI Gate tende a ser alta.",
    recommendation: "Subir o cap pra 30 ou remover. O custo é marginal — são títulos curtos — e a observability completa permite análises como 'qual % de items de cada source passa no AI Gate'.",
  },
  {
    id: "PE-06",
    lens: "Prompt Engineering",
    severity: "P2",
    title: "Tone validation retry é O(n) no budget de retries",
    summary: "Se o Gemini falha no tone check, o pipeline retenta com o MESMO prompt. Sem feedback do que deu errado, tende a gerar o mesmo hype na próxima tentativa.",
    detail: "O retry loop faz time.sleep(2**attempt) e tenta de novo. Mas o prompt é idêntico — não injeta os warnings de tone como feedback. Em LLMs com temperature=0.0, a resposta tende a ser determinística, então o retry pode gastar 5 tentativas pra obter o mesmo resultado.",
    recommendation: "Se tone check falhar, injetar os warnings no prompt do retry: 'AVISO: sua resposta anterior usou [hype_word] em [field]. Reescreva SEM esses termos.' Isso transforma retry burro em retry informado.",
  },

  // ── JORNALISMO & CURADORIA ──
  {
    id: "JC-01",
    lens: "Jornalismo & Curadoria",
    severity: "OK",
    title: "Diversidade geográfica de fontes: de 4 pra 10",
    summary: "SCMP Tech (China/Ásia), Rest of World (Global South), TechNode (China tech). Isso é uma evolução significativa — quebra a bolha US-only.",
    detail: "O config atribuiu weight 1.1 pro SCMP (acima do Reddit!) e 1.0 pro Rest of World. O DeepMind tem 0.7 (o mais baixo). Essa calibração mostra intenção editorial: fontes geográficas diversas têm mais peso que blogs corporativos.",
    recommendation: null,
  },
  {
    id: "JC-02",
    lens: "Jornalismo & Curadoria",
    severity: "OK",
    title: "AI Lab Blogs com weight baixo (0.7-0.8) + STEP 1.5",
    summary: "Combinação inteligente: blogs oficiais entram no pipeline mas com peso menor E passam pelo source bias check. Double-gate contra marketing content.",
    detail: null,
    recommendation: null,
  },
  {
    id: "JC-03",
    lens: "Jornalismo & Curadoria",
    severity: "P0",
    title: "Zero memória editorial — AYA ainda não sabe o que já foi publicado",
    summary: "Sem contexto de edições anteriores, a mesma história pode ser main_find em edições consecutivas. Não existe conceito de follow-up.",
    detail: "Um paper trending no HN segunda, que aparece no SCMP terça com ângulo asiático, e no Rest of World quarta — AYA vai tratar cada um como notícia nova. Bom jornalismo acumula: 'como reportamos ontem... hoje há atualização'. Com 10 fontes, a chance de re-cobertura AUMENTA, tornando a memória editorial mais urgente que antes.",
    recommendation: "Injetar no context_block um JSON com as últimas 3 edições: [{edition: '004', date: '26/03', main_find: 'título', quick_find_titles: ['t1','t2','t3']}]. Adicionar instrução: 'Se um item foi main_find ou quick_find nas últimas 3 edições, só inclua se houver UPDATE significativo. Mencione o follow-up.' Custo: ~300 tokens, impacto editorial alto.",
  },
  {
    id: "JC-04",
    lens: "Jornalismo & Curadoria",
    severity: "P1",
    title: "Fontes geográficas vão gerar items que NÃO passam no AI Gate — e está ok",
    summary: "SCMP e Rest of World cobrem tech broadly, não só AI. Muitos items vão ser descartados no AI Gate. O pipeline precisa tolerar alta taxa de rejeição sem penalizar essas fontes.",
    detail: "Se SCMP manda 15 items e só 3 passam no AI Gate, isso é esperado — é uma fonte generalista. Mas o scoring do pre-filter usa engagement=0.5 (RSS neutral) pra RSS sources. Combinado com diversity bonus e weight 1.1, os items SCMP que passarem no AI Gate terão scoring competitivo. O design é correto.",
    recommendation: "Monitorar via observability: logar taxa de AI Gate pass por source. Se SCMP/RoW/TechNode consistentemente passam <10%, considerar adicionar keyword pre-filter nas sources RSS antes de entrar no pipeline geral. Isso economiza slots no token budget pra items mais relevantes.",
  },
  {
    id: "JC-05",
    lens: "Jornalismo & Curadoria",
    severity: "P1",
    title: "STEP 1.5 não cobre press releases de big tech não-AI",
    summary: "O source bias check só menciona 'blogs oficiais de empresas de AI'. Mas com fontes diversas, items de blogs da Apple, Microsoft, Amazon sobre AI também podem aparecer.",
    detail: "Um post do SCMP citando o blog da Alibaba Cloud sobre AI, ou um item do TechCrunch linkando pro blog da Microsoft — esses passam pelo STEP 1.5? A instrução atual é ambígua porque foca em 'empresas de AI', não em 'blogs corporativos com AI angle'.",
    recommendation: "Generalizar: 'Se a fonte ORIGINAL (não a que indexou) é um blog corporativo oficial...' + adicionar exemplos: 'Aplica a mesma lógica se o SCMP está reportando um anúncio do blog da Alibaba Cloud ou se o TechCrunch está linkando um post do blog da Microsoft AI.'",
  },
  {
    id: "JC-06",
    lens: "Jornalismo & Curadoria",
    severity: "P2",
    title: "Research papers ainda ausentes — ArXiv não está no pipeline",
    summary: "AI lab blogs são secondary sources dos papers deles. ArXiv seria a primary source de research. Continua sendo um blind spot.",
    detail: "Quando a Anthropic publica um paper, o blog deles vai ter um post marketing. ArXiv teria o paper real. O pipeline hoje captura o marketing, não o paper.",
    recommendation: "Adicionar ArXiv RSS (cs.AI + cs.CL + cs.LG) como source. A infra RSS genérica já suporta. Baixa prioridade porque os blogs já cobrem indiretamente, mas seria um diferencial editorial.",
  },

  // ── SOCIOLOGIA & ESTATÍSTICA ──
  {
    id: "SE-01",
    lens: "Sociologia & Estatística",
    severity: "OK",
    title: "Z-score normalization resolve comparabilidade cross-source",
    summary: "Sigmoid de z-score para engagement é estatisticamente correto. Reddit (0-5000 upvotes) e HN (0-800 points) agora são comparáveis numa escala [0,1].",
    detail: "A mediana real das sources com engagement é usada como RSS neutral — muito melhor que o 0.5 fixo anterior. Se a mediana de engagement é alta, RSS sources competem em pé de igualdade.",
    recommendation: null,
  },
  {
    id: "SE-02",
    lens: "Sociologia & Estatística",
    severity: "OK",
    title: "Cross-source signal: dedup inteligente que preserva informação",
    summary: "Em vez de deletar duplicatas, marca cross_source_count e injeta also_trending_on no prompt. Item que aparece em 3 fontes ganha +30% de boost (0.15 * 2).",
    detail: "O cross_bonus = 1.0 + (0.15 * (cross_source_count - 1)) é um multiplicador no composite score. Um item aparecendo em HN + Reddit + TechCrunch tem 1.3x boost. Esse é um proxy válido de relevância — se 3 comunidades diferentes estão discutindo, tem sinal real.",
    recommendation: null,
  },
  {
    id: "SE-03",
    lens: "Sociologia & Estatística",
    severity: "OK",
    title: "Wild card zone: exploration vs exploitation",
    summary: "5 slots aleatórios do pool descartado é um mecanismo de serendipity estatisticamente fundamentado. Dá ao LLM chance de encontrar gems que o scoring perdeu.",
    detail: "Em sistemas de recomendação, 10-15% de exploration é best practice. 5/40 = 12.5% — dentro do range ideal. Os wild cards podem surfar items de fontes geográficas que teriam scoring baixo mas relevância editorial alta.",
    recommendation: null,
  },
  {
    id: "SE-04",
    lens: "Sociologia & Estatística",
    severity: "P1",
    title: "engagement_weight=0.4 ainda é o fator dominante — agora com mais impacto",
    summary: "Com 10 fontes onde 6 são RSS-only (score=0), o engagement weight de 0.4 cria uma bifurcação: sources com engagement real (Reddit, HN) dominam o top do ranking, RSS sources competem por diversidade/recency.",
    detail: "O z-score + sigmoid normaliza DENTRO das sources com engagement. Mas sources RSS-only recebem mediana como score — que é por definição o meio da distribuição. Items com engagement acima da mediana (que são metade dos items de Reddit/HN) sempre ganham do RSS neutral. O diversity bonus (0.2) e recency (0.3) compensam parcialmente, mas 0.4 > 0.3 > 0.2.",
    recommendation: "Reduzir engagement_weight para 0.3 e subir category_weight de 0.1 para 0.2 (implementando categorias reais em vez do placeholder 0.5). Isso equilibra: engagement 0.3, recency 0.3, diversity 0.2, category 0.2. A categorização por título já existe no rss_generic.py — basta usar o campo category no scoring.",
  },
  {
    id: "SE-05",
    lens: "Sociologia & Estatística",
    severity: "P1",
    title: "max_per_source_pct=0.25 com 10 fontes pode over-constrain",
    summary: "25% de 40 items = 10 items max por source. Com 10 fontes, o cap total é 100 — nunca ativa em sources com poucos items. Mas Reddit (13 subs × 10 = até 130 items) vai bater o cap todo dia.",
    detail: "O 0.25 fazia sentido com 4 fontes (25% = fair share). Com 10 fontes, fair share seria 10%. O cap de 25% ainda permite que Reddit domine 1/4 do input pro LLM. Ao mesmo tempo, TechNode/SCMP/RoW com limit=15 cada nunca batem o cap — o constraint é assimétrico.",
    recommendation: "Considerar baixar pra 0.20 (20%) ou implementar cap absoluto (max 8 items por source) em vez de percentual. Isso garante que Reddit não monopolize mais que ~20% dos slots mesmo produzindo 130 items. As fontes geográficas menores não são afetadas.",
  },
  {
    id: "SE-06",
    lens: "Sociologia & Estatística",
    severity: "P2",
    title: "Recency decay exponencial com constant=8 ainda penaliza slow-burn",
    summary: "e^(-age/8) = items com 16h têm 13.5% do score de recency. Research papers e policy changes que levam 2-3 dias pra ganhar tração perdem quase todo o recency score.",
    detail: "O exponential decay é melhor que o linear anterior, mas a constante 8 é agressiva. Um item de 24h tem e^(-3) = 5% de recency. Fontes geográficas em timezones diferentes (Ásia: +12h de delay na cobertura ocidental) são sistematicamente penalizadas.",
    recommendation: "Opção 1: subir decay_constant pra 12 (24h = 13.5% em vez de 5%). Opção 2: decay variável por category — 'ai' usa 8, 'regulation' usa 16, 'tech' usa 12. O campo category já existe e está sendo populado pelo _categorize_by_title.",
  },
  {
    id: "SE-07",
    lens: "Sociologia & Estatística",
    severity: "P2",
    title: "category_weight=0.1 com valor fixo 0.5 é dead weight",
    summary: "O scoring tem category_weight=0.1 mas usa category_score=0.5 pra TODOS os items. É um placeholder que ocupa 10% do composite score sem adicionar informação.",
    detail: "O rss_generic.py já implementa _categorize_by_title que retorna 'ai', 'startup', 'opensource', 'regulation', 'dev', ou 'tech'. Essa categorização existe mas não é usada no scoring.",
    recommendation: "Implementar scoring real por category: 'ai' → 0.9, 'regulation' → 0.8, 'opensource' → 0.7, 'startup' → 0.6, 'dev' → 0.5, 'tech' → 0.3. Isso dá ao pre-filter consciência editorial — items categorized como 'ai' ganham boost antes de chegar na AYA. Combine com subir category_weight pra 0.2.",
  },
];

const overallScore = {
  before: "B-",
  after: "B+",
  delta: "Evolução real: fontes diversas + pre-filter estatístico + observability. Gaps restantes são prompt↔pipeline sync e memória editorial.",
};

const scorecard = {
  "Prompt ↔ Pipeline Sync": { score: "D", label: "2 P0s — prompt desatualizado pro pipeline v5" },
  "Prompt Engineering": { score: "B+", label: "Sólido com refinamentos pontuais" },
  "Jornalismo & Curadoria": { score: "B", label: "Fontes diversas, falta memória editorial" },
  "Sociologia & Estatística": { score: "A-", label: "Z-score, cross-source, wild cards — bem fundamentado" },
};

const priorityMap = [
  { id: "SYNC-01", title: "Atualizar schema source pras 10 fontes", effort: "Trivial", impact: "Crítico", sprint: "Agora" },
  { id: "SYNC-02", title: "Adicionar 2 few-shots de fontes novas", effort: "Low", impact: "Alto", sprint: "Agora" },
  { id: "JC-03", title: "Memória editorial (últimas 3 edições)", effort: "Medium", impact: "Alto", sprint: "Next" },
  { id: "SYNC-03", title: "Instrução pra also_trending_on no prompt", effort: "Trivial", impact: "Médio", sprint: "Agora" },
  { id: "SYNC-04", title: "Few-shot de descarte de AI lab blog", effort: "Low", impact: "Médio", sprint: "Agora" },
  { id: "SE-04", title: "Rebalancear weights (engagement 0.3, category 0.2)", effort: "Low", impact: "Médio", sprint: "Next" },
  { id: "SE-07", title: "Implementar category scoring real", effort: "Low", impact: "Médio", sprint: "Next" },
  { id: "PE-03", title: "Enforcement estrutural do STEP 5 (schema)", effort: "Low", impact: "Médio", sprint: "Next" },
  { id: "PE-06", title: "Retry informado no tone check (injetar warnings)", effort: "Medium", impact: "Low", sprint: "Later" },
];

function Badge({ severity }) {
  const colors = { P0: "#EF4444", P1: "#F59E0B", P2: "#3B82F6", OK: "#22C55E", FIXED: "#6B7280" };
  const textColors = { P0: "#fff", P1: "#000", P2: "#fff", OK: "#fff", FIXED: "#fff" };
  return (
    <span style={{ background: colors[severity], color: textColors[severity], padding: "2px 8px", borderRadius: "4px", fontSize: "11px", fontWeight: 700, letterSpacing: "0.5px" }}>
      {severity}
    </span>
  );
}

function LensBadge({ lens }) {
  return (
    <span style={{ background: LENS_COLORS[lens] + "22", color: LENS_COLORS[lens], padding: "2px 8px", borderRadius: "4px", fontSize: "10px", fontWeight: 600, border: `1px solid ${LENS_COLORS[lens]}44` }}>
      {lens}
    </span>
  );
}

function FindingCard({ finding, isExpanded, onToggle }) {
  return (
    <div
      style={{ background: "#1E293B", border: `1px solid ${SEVERITY[finding.severity]}33`, borderLeft: `3px solid ${SEVERITY[finding.severity]}`, borderRadius: "8px", padding: "16px", marginBottom: "8px", cursor: "pointer" }}
      onClick={onToggle}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px", flexWrap: "wrap" }}>
        <Badge severity={finding.severity} />
        <LensBadge lens={finding.lens} />
        <span style={{ color: "#94A3B8", fontSize: "11px", fontFamily: "monospace" }}>{finding.id}</span>
      </div>
      <div style={{ color: "#F1F5F9", fontSize: "14px", fontWeight: 600, marginBottom: "6px" }}>{finding.title}</div>
      <div style={{ color: "#CBD5E1", fontSize: "13px", lineHeight: "1.5" }}>{finding.summary}</div>
      {isExpanded && (
        <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid #334155" }}>
          {finding.detail && (
            <div style={{ color: "#94A3B8", fontSize: "12px", lineHeight: "1.6", marginBottom: "12px" }}>{finding.detail}</div>
          )}
          {finding.code && (
            <pre style={{ background: "#0F172A", padding: "12px", borderRadius: "6px", fontSize: "11px", color: "#A78BFA", overflow: "auto", marginBottom: "12px", whiteSpace: "pre-wrap", lineHeight: "1.5" }}>
              {finding.code}
            </pre>
          )}
          {finding.recommendation && (
            <div style={{ background: "#0F172A", borderRadius: "6px", padding: "12px", borderLeft: `2px solid ${SEVERITY[finding.severity]}` }}>
              <div style={{ color: "#F59E0B", fontSize: "11px", fontWeight: 700, marginBottom: "6px", letterSpacing: "0.5px" }}>RECOMENDAÇÃO</div>
              <div style={{ color: "#E2E8F0", fontSize: "12px", lineHeight: "1.6" }}>{finding.recommendation}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function PromptAuditV5() {
  const [expandedId, setExpandedId] = useState(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const [view, setView] = useState("findings");

  const lenses = ["all", ...Object.keys(LENS_COLORS)];
  const filtered = activeFilter === "all" ? findings : findings.filter((f) => f.lens === activeFilter);

  const stats = { P0: 0, P1: 0, P2: 0, OK: 0 };
  findings.forEach((f) => { if (stats[f.severity] !== undefined) stats[f.severity]++; });

  return (
    <div style={{ background: "#0F172A", minHeight: "100vh", color: "#E2E8F0", fontFamily: "'Inter', system-ui, sans-serif" }}>
      {/* Header */}
      <div style={{ padding: "24px 24px 0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "4px" }}>
          <span style={{ color: "#22C55E", fontSize: "13px", fontFamily: "monospace", fontWeight: 700 }}>DAILY SCOUT</span>
          <span style={{ color: "#334155" }}>|</span>
          <span style={{ color: "#94A3B8", fontSize: "13px" }}>Prompt Audit v5.0 — Revised</span>
        </div>
        <h1 style={{ fontSize: "22px", fontWeight: 700, color: "#F1F5F9", margin: "8px 0 4px" }}>
          Audit: Pipeline v5 Completo (10 sources + pre-filter v5 + prompt)
        </h1>
        <p style={{ color: "#94A3B8", fontSize: "13px", margin: "0 0 8px" }}>
          4 lentes: Prompt↔Pipeline Sync + Prompt Engineering + Jornalismo + Estatística
        </p>
        {/* Overall score */}
        <div style={{ display: "inline-flex", alignItems: "center", gap: "12px", background: "#1E293B", borderRadius: "8px", padding: "8px 16px" }}>
          <span style={{ color: "#94A3B8", fontSize: "12px" }}>Overall:</span>
          <span style={{ color: "#F59E0B", fontSize: "18px", fontWeight: 800, textDecoration: "line-through", opacity: 0.5 }}>{overallScore.before}</span>
          <span style={{ color: "#94A3B8", fontSize: "14px" }}>→</span>
          <span style={{ color: "#22C55E", fontSize: "18px", fontWeight: 800 }}>{overallScore.after}</span>
          <span style={{ color: "#64748B", fontSize: "11px", maxWidth: "300px" }}>{overallScore.delta}</span>
        </div>
      </div>

      {/* Scorecard */}
      <div style={{ padding: "16px 24px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
        {Object.entries(scorecard).map(([lens, data]) => (
          <div key={lens} style={{ background: "#1E293B", borderRadius: "8px", padding: "10px 14px", flex: "1 1 160px", borderTop: `2px solid ${LENS_COLORS[lens]}`, minWidth: "160px" }}>
            <div style={{ fontSize: "10px", color: LENS_COLORS[lens], fontWeight: 600, marginBottom: "2px" }}>{lens}</div>
            <div style={{ fontSize: "22px", fontWeight: 800, color: "#F1F5F9" }}>{data.score}</div>
            <div style={{ fontSize: "10px", color: "#94A3B8" }}>{data.label}</div>
          </div>
        ))}
      </div>

      {/* Stats + view toggle */}
      <div style={{ padding: "0 24px 12px", display: "flex", gap: "16px", alignItems: "center", flexWrap: "wrap" }}>
        {Object.entries(stats).map(([sev, count]) => (
          <div key={sev} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: SEVERITY[sev] }} />
            <span style={{ fontSize: "12px", color: "#94A3B8" }}>{sev}: {count}</span>
          </div>
        ))}
        <div style={{ flex: 1 }} />
        {["findings", "priority", "architecture"].map((v) => (
          <button key={v} onClick={() => setView(v)} style={{ background: view === v ? "#F59E0B" : "#334155", color: view === v ? "#000" : "#CBD5E1", border: "none", borderRadius: "6px", padding: "6px 12px", fontSize: "12px", fontWeight: 600, cursor: "pointer", textTransform: "capitalize" }}>
            {v === "findings" ? "Findings" : v === "priority" ? "Priority Map" : "Architecture"}
          </button>
        ))}
      </div>

      {/* Architecture view */}
      {view === "architecture" && (
        <div style={{ padding: "0 24px 24px" }}>
          <div style={{ background: "#1E293B", borderRadius: "8px", padding: "20px", fontFamily: "monospace", fontSize: "12px", lineHeight: "1.8" }}>
            <div style={{ color: "#22C55E", fontWeight: 700, marginBottom: "12px" }}>PIPELINE v5 — DATA FLOW (10 sources)</div>
            <div style={{ color: "#64748B", marginBottom: "8px" }}>── COMMUNITY (engagement data) ──</div>
            <div style={{ color: "#CBD5E1" }}>  Reddit (13 subs × 10)  ─┐  weight: 1.0</div>
            <div style={{ color: "#CBD5E1" }}>  HackerNews (top 30)    ─┤  weight: 1.2</div>
            <div style={{ color: "#CBD5E1" }}>  TechCrunch (RSS)       ─┤  weight: 1.1</div>
            <div style={{ color: "#CBD5E1" }}>  Lobsters (RSS)         ─┤  weight: 0.9</div>
            <div style={{ color: "#64748B", margin: "8px 0" }}>── AI LAB BLOGS (RSS, no engagement) ──</div>
            <div style={{ color: "#A78BFA" }}>  Anthropic Blog         ─┤  weight: 0.8</div>
            <div style={{ color: "#A78BFA" }}>  OpenAI Blog            ─┤  weight: 0.8</div>
            <div style={{ color: "#A78BFA" }}>  DeepMind Blog          ─┤  weight: 0.7</div>
            <div style={{ color: "#64748B", margin: "8px 0" }}>── GEOGRAPHIC DIVERSITY (RSS, no engagement) ──</div>
            <div style={{ color: "#06B6D4" }}>  SCMP Tech (China)      ─┤  weight: 1.1  ★ highest non-community</div>
            <div style={{ color: "#06B6D4" }}>  Rest of World (Global) ─┤  weight: 1.0</div>
            <div style={{ color: "#06B6D4" }}>  TechNode (China)       ─┘  weight: 0.9</div>
            <div style={{ color: "#94A3B8", margin: "12px 0" }}>          ↓ ~200-250 raw items</div>
            <div style={{ color: "#F59E0B", fontWeight: 700 }}>  PRE-FILTER v5</div>
            <div style={{ color: "#94A3B8" }}>  ├─ URL dedup</div>
            <div style={{ color: "#94A3B8" }}>  ├─ Title dedup (fuzzy) → cross_source_count signal</div>
            <div style={{ color: "#94A3B8" }}>  ├─ Recency (24h cutoff, 10 item fallback)</div>
            <div style={{ color: "#94A3B8" }}>  ├─ Z-score scoring (engagement sigmoid + exp decay + diversity)</div>
            <div style={{ color: "#94A3B8" }}>  ├─ Diversity cap (25% max per source)</div>
            <div style={{ color: "#94A3B8" }}>  └─ Token trim: 35 scored + 5 wild cards = 40 items</div>
            <div style={{ color: "#94A3B8", margin: "12px 0" }}>          ↓ 40 items (shuffled)</div>
            <div style={{ color: "#22C55E", fontWeight: 700 }}>  GEMINI 2.5 FLASH (temp=0.0)</div>
            <div style={{ color: "#94A3B8" }}>  ├─ System: persona AYA + accuracy rules + voice</div>
            <div style={{ color: "#94A3B8" }}>  ├─ User: pipeline 5 steps + 8 few-shots + items</div>
            <div style={{ color: "#EF4444" }}>  │  ⚠ schema lists 4 sources, pipeline sends 10</div>
            <div style={{ color: "#EF4444" }}>  │  ⚠ few-shots cover 3 sources, missing 7 new ones</div>
            <div style={{ color: "#EF4444" }}>  │  ⚠ also_trending_on injected but not instructed</div>
            <div style={{ color: "#94A3B8" }}>  ├─ Output: CurationOutput (structured JSON)</div>
            <div style={{ color: "#94A3B8" }}>  └─ Post-process: tone validation (hype regex)</div>
            <div style={{ color: "#94A3B8", margin: "12px 0" }}>          ↓ curated content</div>
            <div style={{ color: "#8B5CF6", fontWeight: 700 }}>  JINJA2 RENDER → BUTTONDOWN API → subscribers</div>
          </div>
        </div>
      )}

      {/* Priority Map */}
      {view === "priority" && (
        <div style={{ padding: "0 24px 24px" }}>
          <div style={{ background: "#1E293B", borderRadius: "8px", padding: "16px" }}>
            <div style={{ color: "#F59E0B", fontSize: "12px", fontWeight: 700, marginBottom: "4px", letterSpacing: "0.5px" }}>PRIORITY ROADMAP</div>
            <div style={{ color: "#64748B", fontSize: "11px", marginBottom: "16px" }}>Ordenado por impacto × facilidade. Sprint tags: Agora (pré-deploy), Next (próximo ciclo), Later.</div>
            {["Agora", "Next", "Later"].map((sprint) => {
              const items = priorityMap.filter((p) => p.sprint === sprint);
              if (!items.length) return null;
              return (
                <div key={sprint} style={{ marginBottom: "16px" }}>
                  <div style={{ color: sprint === "Agora" ? "#EF4444" : sprint === "Next" ? "#F59E0B" : "#64748B", fontSize: "11px", fontWeight: 700, marginBottom: "8px", letterSpacing: "1px" }}>
                    {sprint.toUpperCase()} {sprint === "Agora" ? "— antes do próximo deploy" : sprint === "Next" ? "— próximo ciclo" : "— backlog"}
                  </div>
                  {items.map((item) => (
                    <div key={item.id} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "8px 12px", background: "#0F172A", borderRadius: "6px", marginBottom: "4px", borderLeft: `2px solid ${sprint === "Agora" ? "#EF4444" : sprint === "Next" ? "#F59E0B" : "#334155"}` }}>
                      <span style={{ color: "#94A3B8", fontSize: "11px", fontFamily: "monospace", minWidth: "60px" }}>{item.id}</span>
                      <span style={{ color: "#F1F5F9", fontSize: "13px", flex: 1 }}>{item.title}</span>
                      <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "3px", background: item.effort === "Trivial" ? "#22C55E22" : item.effort === "Low" ? "#22C55E22" : "#F59E0B22", color: item.effort === "Trivial" ? "#22C55E" : item.effort === "Low" ? "#22C55E" : "#F59E0B" }}>
                        {item.effort}
                      </span>
                      <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "3px", background: item.impact === "Crítico" ? "#EF444422" : item.impact === "Alto" ? "#8B5CF622" : "#3B82F622", color: item.impact === "Crítico" ? "#EF4444" : item.impact === "Alto" ? "#8B5CF6" : "#3B82F6" }}>
                        {item.impact}
                      </span>
                    </div>
                  ))}
                </div>
              );
            })}
            <div style={{ marginTop: "12px", padding: "10px", background: "#0F172A", borderRadius: "6px", fontSize: "12px", color: "#94A3B8", lineHeight: "1.6" }}>
              Os 5 items <strong style={{ color: "#EF4444" }}>AGORA</strong> são prompt-only changes — zero mudança em código Python. Podem ser feitos em 30 minutos e resolvem os 2 P0s (schema desatualizado + few-shots missing).
            </div>
          </div>
        </div>
      )}

      {/* Findings */}
      {view === "findings" && (
        <>
          <div style={{ padding: "0 24px 12px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {lenses.map((lens) => {
              const count = lens === "all" ? findings.length : findings.filter((f) => f.lens === lens).length;
              return (
                <button key={lens} onClick={() => setActiveFilter(lens)} style={{ background: activeFilter === lens ? (lens === "all" ? "#475569" : LENS_COLORS[lens] + "33") : "#1E293B", color: activeFilter === lens ? (lens === "all" ? "#F1F5F9" : LENS_COLORS[lens]) : "#94A3B8", border: `1px solid ${activeFilter === lens ? (lens === "all" ? "#475569" : LENS_COLORS[lens] + "66") : "#334155"}`, borderRadius: "6px", padding: "6px 12px", fontSize: "12px", fontWeight: 500, cursor: "pointer" }}>
                  {lens === "all" ? `Todos (${count})` : `${lens} (${count})`}
                </button>
              );
            })}
          </div>
          <div style={{ padding: "0 24px 24px" }}>
            {filtered.map((f) => (
              <FindingCard key={f.id} finding={f} isExpanded={expandedId === f.id} onToggle={() => setExpandedId(expandedId === f.id ? null : f.id)} />
            ))}
          </div>
        </>
      )}

      {/* Footer */}
      <div style={{ padding: "0 24px 24px", borderTop: "1px solid #1E293B", paddingTop: "16px" }}>
        <div style={{ color: "#475569", fontSize: "11px", fontFamily: "monospace" }}>
          audit_by: prompt_engineer_senior | scope: full pipeline (10 sources, pre-filter v5, prompt v5) | date: 2026-03-27
        </div>
      </div>
    </div>
  );
}
