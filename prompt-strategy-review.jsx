import { useState } from "react";

const TABS = [
  { id: "overview", label: "Visao Geral" },
  { id: "prompt", label: "Prompt Architecture" },
  { id: "sociology", label: "Sociologia" },
  { id: "statistics", label: "Estatistica" },
  { id: "interaction", label: "Pre-filter x Prompt" },
  { id: "recommendations", label: "Recomendacoes" },
];

const SeverityBadge = ({ level }) => {
  const colors = {
    critical: "bg-red-100 text-red-800 border-red-300",
    high: "bg-orange-100 text-orange-800 border-orange-300",
    medium: "bg-yellow-100 text-yellow-800 border-yellow-300",
    low: "bg-blue-100 text-blue-800 border-blue-300",
    ok: "bg-green-100 text-green-800 border-green-300",
  };
  return (
    <span className={`text-xs font-bold px-2 py-0.5 rounded border ${colors[level]}`}>
      {level.toUpperCase()}
    </span>
  );
};

const ScoreBar = ({ label, score, max = 10 }) => {
  const pct = (score / max) * 100;
  const color = score >= 8 ? "bg-green-500" : score >= 6 ? "bg-yellow-500" : score >= 4 ? "bg-orange-500" : "bg-red-500";
  return (
    <div className="mb-2">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700">{label}</span>
        <span className="font-bold">{score}/{max}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
};

const Finding = ({ severity, title, description, impact, recommendation }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="border rounded-lg p-3 mb-3 bg-white">
      <div className="flex items-start gap-2 cursor-pointer" onClick={() => setOpen(!open)}>
        <SeverityBadge level={severity} />
        <div className="flex-1">
          <span className="font-semibold text-sm text-gray-900">{title}</span>
          <span className="text-gray-400 ml-2 text-xs">{open ? "[-]" : "[+]"}</span>
        </div>
      </div>
      {open && (
        <div className="mt-2 ml-16 text-sm space-y-2">
          <p className="text-gray-700">{description}</p>
          {impact && <p className="text-gray-600"><span className="font-semibold">Impacto:</span> {impact}</p>}
          {recommendation && (
            <div className="bg-gray-50 border-l-4 border-blue-400 p-2 rounded">
              <span className="font-semibold text-blue-700">Recomendacao:</span>{" "}
              <span className="text-gray-700">{recommendation}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const FlowDiagram = () => (
  <div className="bg-gray-50 rounded-lg p-4 mb-4">
    <p className="text-xs font-bold text-gray-500 mb-3 uppercase tracking-wide">Pipeline Decision Flow</p>
    <div className="flex items-center gap-1 text-xs flex-wrap">
      {[
        { label: "4 Sources", sub: "~130 items", color: "bg-blue-100 border-blue-300" },
        { label: "URL Dedup", sub: "-15%", color: "bg-gray-100 border-gray-300" },
        { label: "Title Dedup", sub: "-10%", color: "bg-gray-100 border-gray-300" },
        { label: "Recency 24h", sub: "fallback 10", color: "bg-gray-100 border-gray-300" },
        { label: "Scoring", sub: "E×0.4+R×0.3+D×0.2+C×0.1", color: "bg-purple-100 border-purple-300" },
        { label: "Diversity Cap", sub: "max 40%/source", color: "bg-purple-100 border-purple-300" },
        { label: "Token Trim", sub: "top 30", color: "bg-orange-100 border-orange-300" },
        { label: "GEMINI", sub: "5-step pipeline", color: "bg-green-100 border-green-400" },
        { label: "validate_tone", sub: "regex hype", color: "bg-red-100 border-red-300" },
      ].map((step, i) => (
        <div key={i} className="flex items-center gap-1">
          <div className={`${step.color} border rounded px-2 py-1.5 text-center min-w-16`}>
            <div className="font-bold">{step.label}</div>
            <div className="text-gray-500 text-[10px]">{step.sub}</div>
          </div>
          {i < 8 && <span className="text-gray-400 font-bold">→</span>}
        </div>
      ))}
    </div>
    <div className="mt-3 flex gap-4 text-[10px] text-gray-500">
      <span className="flex items-center gap-1"><span className="w-3 h-3 bg-gray-100 border border-gray-300 rounded inline-block" /> Deterministic filter</span>
      <span className="flex items-center gap-1"><span className="w-3 h-3 bg-purple-100 border border-purple-300 rounded inline-block" /> Statistical ranking</span>
      <span className="flex items-center gap-1"><span className="w-3 h-3 bg-green-100 border border-green-400 rounded inline-block" /> LLM judgment</span>
      <span className="flex items-center gap-1"><span className="w-3 h-3 bg-red-100 border border-red-300 rounded inline-block" /> Post-processing</span>
    </div>
  </div>
);

const OverviewTab = () => (
  <div>
    <h3 className="text-lg font-bold text-gray-900 mb-1">Diagnostic Summary</h3>
    <p className="text-sm text-gray-600 mb-4">Revisao completa da estrategia de prompt do Daily Scout v4, com lentes de prompt engineering, sociologia e estatistica.</p>

    <FlowDiagram />

    <div className="grid grid-cols-2 gap-4 mb-4">
      <div className="bg-white border rounded-lg p-4">
        <h4 className="font-bold text-sm mb-3 text-gray-800">Scorecard Geral</h4>
        <ScoreBar label="Prompt Clarity" score={8.5} />
        <ScoreBar label="Selection Logic" score={7} />
        <ScoreBar label="Tone Control" score={9} />
        <ScoreBar label="Bias Mitigation" score={4} />
        <ScoreBar label="Statistical Rigor" score={5} />
        <ScoreBar label="Observability" score={3} />
        <ScoreBar label="Scalability" score={6} />
      </div>
      <div className="bg-white border rounded-lg p-4">
        <h4 className="font-bold text-sm mb-3 text-gray-800">Risk Heat Map</h4>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between items-center">
            <span className="text-gray-700">Confirmation bias no scoring</span>
            <SeverityBadge level="critical" />
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-700">Zero observability do LLM reasoning</span>
            <SeverityBadge level="critical" />
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-700">Engagement proxy invalido pra RSS</span>
            <SeverityBadge level="high" />
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-700">Few-shot anchoring effect</span>
            <SeverityBadge level="high" />
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-700">Monocultura geografica</span>
            <SeverityBadge level="high" />
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-700">STEP 5 teste final ambiguo</span>
            <SeverityBadge level="medium" />
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-700">Category weight nao implementado</span>
            <SeverityBadge level="medium" />
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-700">Tone control (HYPE_PATTERNS)</span>
            <SeverityBadge level="ok" />
          </div>
        </div>
      </div>
    </div>

    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
      <span className="font-bold">TL;DR</span> — O prompt v4 resolveu o problema #001 (julgamento editorial). A AYA agora filtra por relevancia AI. Mas o sistema tem um gap estrutural: <span className="font-bold">o pre-filter decide o que o LLM ve, e o LLM decide o que o leitor ve — mas ninguem audita nenhuma dessas decisoes</span>. Alem disso, o scoring carrega vieses estatisticos que o prompt nao consegue compensar.
    </div>
  </div>
);

const PromptTab = () => (
  <div>
    <h3 className="text-lg font-bold text-gray-900 mb-1">Prompt Architecture Diagnostic</h3>
    <p className="text-sm text-gray-600 mb-4">Analise da estrutura SYSTEM_INSTRUCTION + CURATION_PROMPT + validate_tone.</p>

    <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4 text-sm">
      <span className="font-bold text-green-800">O que esta funcionando bem:</span>
      <p className="text-green-700 mt-1">Pipeline de 5 steps cria chain-of-thought implicito — o LLM segue uma sequencia logica em vez de avaliar criterios flat. Few-shots cobrem tanto selecao quanto tom. SYSTEM_INSTRUCTION define persona + restricoes de acuracia separadamente do user prompt. Temperature 0.0 + response_schema reduz variancia.</p>
    </div>

    <Finding
      severity="critical"
      title="F1 — Zero observability: voce nao sabe POR QUE a AYA escolheu algo"
      description="O prompt pede que a AYA execute 5 steps internamente, mas o response_schema so captura o OUTPUT final (main_find, quick_finds, meta). Voce nao ve: quais items passaram no AI Gate, quais falharam no Step 2, qual foi o ranking antes do Step 4. E como se voce pedisse pra alguem fazer uma prova mas so entregasse a nota final sem mostrar o rascunho."
      impact="Impossivel diagnosticar quando a AYA erra. Se ela escolhe um item ruim como main_find, voce nao sabe se o problema foi no AI Gate (deixou passar), no Step 2 (criterios mal aplicados), ou no Step 4 (ranking errado). Debugging vira guesswork."
      recommendation="Adicionar campo 'reasoning' no schema — um objeto com: ai_gate_passed (lista de titulos que passaram), ai_gate_rejected (lista com motivo), ranking_rationale (por que o main_find ganhou). Custo: ~200 tokens extras no output (~$0.0005/dia). Valor: observability total."
    />

    <Finding
      severity="high"
      title="F2 — Few-shot anchoring: os exemplos enviesam o que 'parece certo'"
      description="Psicologia cognitiva: few-shots nao sao apenas 'exemplos' — sao ancoras. O Gemini vai gravitar pra items que SE PARECEM com os exemplos. O Exemplo 1 (Gemini chat import) ancora em 'feature de chatbot'. O Exemplo 5 (Stripe/PayAI) ancora em 'aquisicao B2B'. Nenhum exemplo mostra: infraestrutura (chips, datacenters), open source release, regulacao governamental, research paper impactante."
      impact="A AYA vai sub-representar categorias que nao tem exemplos. Papers do tipo 'DeepSeek R2 technical report' ou 'EU AI Act enforcement begins' nao tem ancora nos few-shots, entao o modelo tem menos confianca pra selecioná-los como main_find."
      recommendation="Adicionar 2-3 few-shots que cubram categorias ausentes: (1) infra/chips — 'TSMC announces 1.4nm process for AI chips'; (2) regulacao — 'EU begins enforcing AI Act transparency requirements'; (3) open source — 'Meta releases Llama 4 with Apache 2.0 license'. Manter total em 6-7 exemplos (mais que isso dilui a atencao do modelo)."
    />

    <Finding
      severity="medium"
      title="F3 — STEP 5 Teste Final: completion task muito rigida"
      description="O teste pede que TODO item selecionado complete uma de duas frases: 'Agora e possivel [X]' ou '[Player] esta [movendo pra / investindo em] [Y]'. Isso funciona pra features e M&A, mas elimina categorias validas: research breakthroughs ('paper mostra que X supera Y em benchmark Z'), regulatory actions ('governo proibiu X'), community movements ('devs migrando de X pra Y')."
      impact="Filtragem excessiva. Items relevantes mas que nao encaixam nessas duas templates sao descartados. Isso cria um editorial com vies de 'product announcements' — exatamente o tipo de newsletter que ja existe (The Verge, TechCrunch)."
      recommendation="Expandir pra 4 templates: (1) 'Agora e possivel [X]' — feature/tool. (2) '[Player] esta [acao] em [categoria]' — M&A/estrategia. (3) '[Resultado] muda o que sabiamos sobre [area]' — research/benchmark. (4) '[Autoridade] decidiu [acao] sobre [tema]' — regulacao/policy."
    />

    <Finding
      severity="medium"
      title="F4 — SYSTEM vs USER instruction overlap cria ambiguidade"
      description="A SYSTEM_INSTRUCTION define regras de tom ('frases curtas e declarativas', 'verbos factuais') E a CURATION_PROMPT tambem define formato ('SEMPRE comece com atribuicao'). Quando ha overlap, o Gemini precisa resolver conflitos implicitamente. Nao ha conflito direto hoje, mas a redundancia dilui a atencao — attention budget e finito."
      impact="Baixo hoje, mas cresce com complexidade. Se voce adicionar STEP 1.5 Source Bias Check e mais few-shots, o prompt fica mais longo e a redundancia custa mais attention."
      recommendation="Separacao clara: SYSTEM = persona + restricoes de acuracia + tom. USER = missao + selecao + formato + exemplos. Remover duplicatas de formato do SYSTEM (ja estao no USER) e mover restricoes de acuracia que aparecem no USER pro SYSTEM."
    />

    <Finding
      severity="low"
      title="F5 — Anti-signal list no prompt e closed set"
      description="O STEP 3 lista 5 anti-signals especificos (Netflix pricing, funding rounds, crypto, UI redesign, obvio). Mas o mundo gera anti-signals que nao estao na lista: hardware reviews, gaming news sem AI, celebrity tech takes, etc."
      impact="Anti-signals nao listados passam pelo filtro. A AYA pode selecionar items como 'Apple releases new MacBook Pro with M5 chip' que nao tem angulo AI mas nao cai em nenhuma das 5 categorias listadas."
      recommendation="Trocar closed set por principio + exemplos: 'Descarte posts que NAO passam no AI Gate E nao sao magnitude excepcional. Exemplos de anti-signal frequentes: [lista atual]'. Isso da ao modelo um principio gerativo em vez de uma checklist finita."
    />
  </div>
);

const SociologyTab = () => (
  <div>
    <h3 className="text-lg font-bold text-gray-900 mb-1">Analise Sociologica</h3>
    <p className="text-sm text-gray-600 mb-4">Vieses de audiencia, representacao cultural, framing effects e echo chambers.</p>

    <Finding
      severity="critical"
      title="S1 — Confirmation Bias Estrutural: o pipeline auto-reforça o que ja acredita"
      description='O scoring do pre-filter usa engagement (upvotes) como 40% do composite score. Engagement no Reddit/HN reflete o que uma audiencia especifica (devs americanos, 25-40 anos, male-dominated) considera importante. O prompt entao recebe esses items JA rankeados por esse vies e faz selecao. E um loop: "a audiencia do HN acha importante → pre-filter rankeia alto → AYA seleciona → leitor ve → confirma que era importante".'
      impact='O Daily Scout herda o vies editorial do HackerNews/Reddit sem saber. Temas como AI ethics, impacto em trabalhadoras de gig economy, AI no Global South, regulacao europeia — que tem ALTO impacto mas BAIXO engagement nessas plataformas — sao sistematicamente sub-representados.'
      recommendation='Implementar "contra-sample": reservar 2-3 slots nos 30 items enviados ao LLM para items de baixo engagement mas alta recencia de fontes sub-representadas. O pre-filter ja tem diversity cap — extender pra incluir um "minority voice floor" (minimo 3 items de fontes nao-US).'
    />

    <Finding
      severity="high"
      title="S2 — Framing Effect: a lingua do prompt molda o output"
      description="O prompt inteiro e em portugues, os few-shots mostram output em portugues, mas 95%+ do input (titulos) esta em ingles. Isso cria um framing onde a AYA TRADUZ e ADAPTA em vez de REPORTAR. Estudos de sociolinguistica mostram que traducao implica interpretacao — a AYA nao so muda o idioma, muda o frame cognitivo. 'May shut down' vira 'estaria considerando descontinuar' — o hedge linguistico muda."
      impact="Risco moderado de shift semantico. A conversao ingles→portugues, especialmente com temperature 0.0, pode fazer o modelo ser mais assertivo ou mais hedge do que o original, dependendo da construcao em portugues."
      recommendation="Adicionar instrucao explicita: 'Ao traduzir, preserve o nivel de certeza do titulo original. Se o titulo diz may/might/could, use condicional (estaria, poderia). Se diz reportedly/sources say, use atribuicao (segundo relatos). NUNCA aumente nem diminua a certeza do original.' Ja esta parcialmente la, mas vale reforcar como regra nomeada."
    />

    <Finding
      severity="high"
      title="S3 — Echo Chamber Risk: monocultura de fontes cria blind spots"
      description="4 fontes, todas anglófonas, 3 com audiencia predominantemente americana (Reddit, HN, TechCrunch). Lobsters e nicho (devs seniores). Ja mapeamos isso na analise geografica. Do ponto de vista sociologico, o problema nao e so geografico — e epistemico. Essas fontes compartilham premissas: AI e progresso, VC funding valida, escala e metrica de sucesso. Fontes como Rest of World, SCMP, Nikkei Asia trazem premissas diferentes."
      impact="A newsletter reproduz a visao de mundo de Silicon Valley. Temas como: soberania de dados na India, AI regulation na China, uso de AI em saude publica na Africa, impacto em mercado de trabalho informal — ficam invisiveis."
      recommendation="Alem da expansao geografica ja planejada, adicionar no STEP 4 uma instrucao de diversidade de PERSPECTIVA (nao so de fonte): 'Se todos os quick_finds vem da mesma premissa (ex: todos sao product launches), priorize pelo menos um item que traga perspectiva regulatoria, critica, ou de mercado emergente.'"
    />

    <Finding
      severity="medium"
      title="S4 — Audience Mismatch: 'profissionais curiosos' e vago demais"
      description="O prompt define a audiencia como 'profissionais curiosos que querem entender como AI esta mudando tecnologia, negocios e trabalho'. Isso cobre: PM, dev, designer, executivo, jornalista, estudante. Cada um tem necessidade informacional diferente. Um PM quer saber de product launches; um dev quer saber de open source tools; um executivo quer sinais de mercado."
      impact="A AYA nao tem como otimizar pra todos. O resultado e um editorial 'middle-of-the-road' que nao e excepcional pra ninguem. Nao e critico hoje porque o produto esta early-stage, mas vai importar quando voce tiver dados de engagement dos leitores."
      recommendation="Por agora: manter generico, mas adicionar ao meta schema um campo 'primary_audience' onde a AYA indica PRA QUEM aquele main_find e mais relevante (ex: 'PMs e founders', 'developers', 'business'). Isso nao muda o output mas gera dados pra voce calibrar depois."
    />

    <Finding
      severity="medium"
      title="S5 — Survivorship Bias no HackerNews scoring"
      description="HN tem weight 1.2 (o mais alto). O algoritmo do HN penaliza posts com muitos flags/controversia — eles caem do ranking rapido. Isso significa que posts polemicos-mas-relevantes (ex: 'AI replacing junior devs at Google — internal memo') podem ter 50 pontos mas ter sido flagged to death. O pre-filter ve 50 pontos, rankeia baixo, e a AYA nunca ve."
      impact="Controversias reais sobre AI (layoffs, bias em modelos, surveillance) sao sub-representadas porque o HN as suprime. O Daily Scout herda esse filtro invisivel."
      recommendation="Considerar usar a API do HN pra capturar 'new' stories (nao so 'top') e incluir num_comments como signal de importancia independente de score. Um post com 50 pontos e 200 comentarios e provavelmente mais relevante que um com 200 pontos e 10 comentarios."
    />
  </div>
);

const StatisticsTab = () => {
  const [showFormula, setShowFormula] = useState(false);

  return (
    <div>
      <h3 className="text-lg font-bold text-gray-900 mb-1">Analise Estatistica</h3>
      <p className="text-sm text-gray-600 mb-4">Validade da formula de scoring, distribuicao de sources, sample size, e mensurabilidade.</p>

      <div className="bg-white border rounded-lg p-4 mb-4">
        <div className="flex justify-between items-center mb-2">
          <h4 className="font-bold text-sm">Formula de Scoring Atual</h4>
          <button onClick={() => setShowFormula(!showFormula)} className="text-xs text-blue-600 hover:underline">
            {showFormula ? "Esconder" : "Ver detalhes"}
          </button>
        </div>
        <code className="text-xs bg-gray-100 p-2 rounded block">
          composite = (engagement × 0.4 + recency × 0.3 + diversity × 0.2 + category × 0.1) × source_weight
        </code>
        {showFormula && (
          <div className="mt-3 text-sm space-y-2 text-gray-700">
            <p><span className="font-bold">engagement [0,1]:</span> raw_score / max_score_da_source. RSS-only = 0.5 fixo.</p>
            <p><span className="font-bold">recency [0,1]:</span> 1 - (age_hours / 24). Linear decay.</p>
            <p><span className="font-bold">diversity [0,1]:</span> 1 - (items_da_source / total_items).</p>
            <p><span className="font-bold">category:</span> 0.5 fixo (nao implementado).</p>
            <p><span className="font-bold">source_weight:</span> HN 1.2, TC 1.1, Reddit 1.0, Lobsters 0.9.</p>
          </div>
        )}
      </div>

      <Finding
        severity="critical"
        title="E1 — Engagement normalization cria comparacao invalida cross-source"
        description="O engagement e normalizado DENTRO de cada source (score / max_da_source). Um post no Reddit com 50 upvotes num dia calmo onde o max e 80 ganha engagement_score = 0.625. Um post no HN com 100 pontos num dia quente onde o max e 800 ganha engagement_score = 0.125. O post do HN e objetivamente mais relevante (mais eyes), mas o scoring o penaliza por ter 'concorrencia interna' mais forte."
        impact="A normalizacao por source distorce a comparacao. Em dias onde uma source tem um outlier (post viral com 2000+ pontos), TODOS os outros posts dessa source ficam com engagement_score baixo, mesmo que tenham engagement absoluto alto."
        recommendation="Usar normalizacao cross-source: z-score ou percentil ranking. Calcular mean e stdev do engagement de TODAS as sources juntas, e normalizar com (score - mean) / stdev. Isso torna os scores comparaveis entre sources sem depender do max de cada uma."
      />

      <Finding
        severity="high"
        title="E2 — RSS-only engagement = 0.5 e um 'magic number' sem justificativa"
        description="Sources sem engagement data (RSS feeds como TechCrunch, futuros blogs de AI labs) recebem engagement_score = 0.5 fixo. Por que 0.5 e nao 0.3 ou 0.7? Nao ha justificativa estatistica. 0.5 foi escolhido como 'neutro', mas com engagement_weight = 0.4, isso da a esses items um bonus de 0.20 no composite — acima da mediana real de engagement das outras sources."
        impact="Na pratica, isso significa que posts do TechCrunch (RSS, engagement fixo 0.5) tem vantagem sobre posts medianos do Reddit/HN (que tem engagement real abaixo de 0.5). E um subsidio invisivel."
        recommendation="Duas opcoes: (A) Calcular a mediana real de engagement_score das sources com dados e usar ESSE valor pro RSS. (B) Usar o num_comments do RSS como proxy de engagement quando disponivel (TechCrunch RSS inclui comment count). Opcao B e mais robusta."
      />

      <Finding
        severity="high"
        title="E3 — Pesos foram definidos por intuicao, nao por dados"
        description="engagement 0.4, recency 0.3, diversity 0.2, category 0.1 — somam 1.0, o que e correto. Mas a distribuicao foi arbitraria. Por que engagement pesa 4x mais que category? Por que recency pesa 1.5x mais que diversity? Nao ha A/B test, ground truth, ou modelo de regressao validando esses pesos."
        impact="Os pesos podem estar amplificando vieses (engagement = 40% = vies de popularidade) e sub-valorando sinais que a Isis acha importantes (category = 10% = quase irrelevante, e nem esta implementado)."
        recommendation="Short-term: implementar category scoring (esta hardcoded 0.5) com as categorias que o pipeline ja captura. Medium-term: coletar feedback da Isis por 2-4 semanas (qual main_find ela achou bom/ruim) e rodar uma logistic regression simples pra encontrar os pesos otimos. O feedback loop via Google Sheet que ja existe e perfeito pra isso."
      />

      <Finding
        severity="medium"
        title="E4 — Sample size de 30 items pro LLM e arbitrario"
        description="max_items_to_llm = 30. O pipeline coleta ~130 items, filtra pra ~80 apos dedup, e corta nos top 30. Isso significa que o LLM ve ~23% do input original. Se um item relevante tem baixo engagement mas alta recencia, ele pode ficar na posicao 35 e nunca ser visto pela AYA."
        impact="O pre-filter faz uma pre-selecao que o prompt nao pode corrigir. Se o filtro errar (e vai, porque os pesos sao arbitrarios), o LLM nao tem como compensar."
        recommendation="Aumentar pra 40-50 items (ja proposto: 30→40). Mas o fix real e adicionar uma 'wild card zone': reservar 5 dos 40 slots pra items aleatorios do pool descartado. Isso da ao LLM a chance de encontrar gems que o scoring perdeu — o equivalente estatistico de exploration vs exploitation."
      />

      <Finding
        severity="medium"
        title="E5 — Recency decay linear nao modela o ciclo real de noticias"
        description="O decay e linear: 1 - (age_hours / 24). Um post de 6h atras tem score 0.75; um de 12h tem 0.50; um de 18h tem 0.25. Mas o ciclo de noticias tech nao e linear — um post de 2h e MUITO mais fresco que um de 6h, enquanto a diferenca entre 18h e 20h e irrelevante."
        impact="Posts publicados logo antes do pipeline rodar tem vantagem desproporcional. Se o pipeline roda as 6am UTC, noticias publicadas as 4am (2h) dominam vs noticias de 6pm do dia anterior (12h), mesmo que as de 6pm tenham tido o dia inteiro pra acumular engagement."
        recommendation="Trocar por decay exponencial: score = e^(-age_hours / decay_constant). Com decay_constant = 8, um post de 2h tem 0.78, de 6h tem 0.47, de 12h tem 0.22. Isso modela melhor a curva de atencao real."
      />

      <div className="bg-white border rounded-lg p-4 mt-4">
        <h4 className="font-bold text-sm mb-2">Simulacao: Impacto dos Vieses</h4>
        <p className="text-xs text-gray-600 mb-3">Cenario hipotetico: dia com 1 outlier no HN (2000pts) + 1 post importante do TechCrunch RSS + 1 item de baixo engagement mas alta relevancia.</p>
        <div className="overflow-x-auto">
          <table className="text-xs w-full">
            <thead>
              <tr className="border-b text-left text-gray-600">
                <th className="py-1 pr-2">Item</th>
                <th className="py-1 px-2">Source</th>
                <th className="py-1 px-2">Raw Score</th>
                <th className="py-1 px-2">Eng. Norm.</th>
                <th className="py-1 px-2">Recency</th>
                <th className="py-1 px-2">Composite</th>
                <th className="py-1 px-2">Rank</th>
              </tr>
            </thead>
            <tbody className="text-gray-700">
              <tr className="border-b">
                <td className="py-1 pr-2">HN outlier (meme viral)</td>
                <td className="py-1 px-2">HN</td>
                <td className="py-1 px-2">2000</td>
                <td className="py-1 px-2">1.00</td>
                <td className="py-1 px-2">0.75</td>
                <td className="py-1 px-2 font-bold">0.80 × 1.2 = 0.96</td>
                <td className="py-1 px-2 font-bold text-green-600">#1</td>
              </tr>
              <tr className="border-b bg-yellow-50">
                <td className="py-1 pr-2">HN post relevante AI (mesmo dia)</td>
                <td className="py-1 px-2">HN</td>
                <td className="py-1 px-2">300</td>
                <td className="py-1 px-2 text-red-600">0.15</td>
                <td className="py-1 px-2">0.85</td>
                <td className="py-1 px-2 font-bold">0.47 × 1.2 = 0.56</td>
                <td className="py-1 px-2 font-bold text-orange-600">#4</td>
              </tr>
              <tr className="border-b">
                <td className="py-1 pr-2">TechCrunch — Anthropic launch</td>
                <td className="py-1 px-2">TC</td>
                <td className="py-1 px-2">0 (RSS)</td>
                <td className="py-1 px-2 text-blue-600">0.50 (fixo)</td>
                <td className="py-1 px-2">0.90</td>
                <td className="py-1 px-2 font-bold">0.58 × 1.1 = 0.64</td>
                <td className="py-1 px-2 font-bold text-yellow-600">#2</td>
              </tr>
              <tr className="bg-red-50">
                <td className="py-1 pr-2">Reddit — EU AI Act enforcement</td>
                <td className="py-1 px-2">Reddit</td>
                <td className="py-1 px-2">45</td>
                <td className="py-1 px-2">0.08</td>
                <td className="py-1 px-2">0.70</td>
                <td className="py-1 px-2 font-bold">0.36 × 1.0 = 0.36</td>
                <td className="py-1 px-2 font-bold text-red-600">#8</td>
              </tr>
            </tbody>
          </table>
        </div>
        <p className="text-xs text-gray-500 mt-2">O post sobre EU AI Act (#8) e altamente relevante pro editorial mas fica enterrado. O meme viral do HN (#1) vai pro topo. O prompt da AYA pode compensar — mas so se o item chegar ate ela nos top 30.</p>
      </div>
    </div>
  );
};

const InteractionTab = () => (
  <div>
    <h3 className="text-lg font-bold text-gray-900 mb-1">Interacao Pre-filter ↔ Prompt</h3>
    <p className="text-sm text-gray-600 mb-4">O gap entre o que o pre-filter decide e o que o prompt pode corrigir.</p>

    <div className="bg-white border rounded-lg p-4 mb-4">
      <h4 className="font-bold text-sm mb-2">Decisoes Irreversiveis vs Reversiveis</h4>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="bg-red-50 rounded p-3">
          <p className="font-bold text-red-800 mb-2">Pre-filter decide (IRREVERSIVEL)</p>
          <ul className="text-red-700 space-y-1 text-xs">
            <li>• Quais items o LLM VE (top 30 de ~130)</li>
            <li>• Ordem dos items (scoring influencia position bias)</li>
            <li>• Diversidade de sources no input</li>
            <li>• Dedup: qual versao de um item duplicado sobrevive</li>
            <li>• Recency cutoff: items velhos eliminados</li>
          </ul>
        </div>
        <div className="bg-green-50 rounded p-3">
          <p className="font-bold text-green-800 mb-2">Prompt decide (REVERSIVEL)</p>
          <ul className="text-green-700 space-y-1 text-xs">
            <li>• Qual item e main_find vs quick_find</li>
            <li>• Quais items passam no AI Gate</li>
            <li>• Tom e framing do texto</li>
            <li>• Nivel de detalhe e contexto</li>
            <li>• Rejeicao de items via anti-signal</li>
          </ul>
        </div>
      </div>
    </div>

    <Finding
      severity="critical"
      title="I1 — Position Bias: os primeiros items da lista tem vantagem no LLM"
      description="O pre-filter ordena items por composite score. O Gemini recebe uma lista JSON ordenada. Pesquisa em LLMs mostra que items no inicio e fim de listas longas recebem mais atencao (primacy + recency effect). Com 30 items, os primeiros 5-7 tem vantagem significativa na selecao, independente do prompt."
      impact="O ranking do pre-filter 'contamina' o julgamento editorial da AYA. Ela acha que esta escolhendo pelo AI Gate + criterios, mas inconscientemente favorece os items que apareceram primeiro — que sao os de maior engagement, nao necessariamente os mais relevantes editorialmente."
      recommendation="Shuffle aleatorio dos items antes de enviar ao LLM. Isso forca a AYA a avaliar cada item por merito, nao por posicao. O pre-filter fez seu trabalho (selecionar os 30 melhores) — a ordem dentro dos 30 nao deveria importar."
    />

    <Finding
      severity="high"
      title="I2 — Information loss: o LLM nao sabe o que NAO esta vendo"
      description="O LLM recebe 30 items e acha que e 'o mundo'. Ele nao sabe que havia 130 originais, que 100 foram cortados, nem quais fontes contribuiram mais ou menos. O campo meta.total_analyzed e preenchido pelo LLM com base no que ele ve (30), nao no total real."
      impact="O editorial_note e o correspondent_intro da AYA nao podem refletir a realidade ('analisei 130 posts de 4 fontes') porque ela literalmente nao tem essa informacao. Se o Reddit falhou no fetch, a AYA nao sabe — ela so ve menos items."
      recommendation="Adicionar no prompt: 'CONTEXTO DO DIA: Analisei {total_fetched} posts de {sources_count} fontes ({source_breakdown}). Voce esta recebendo os {filtered_count} mais relevantes apos pre-filtragem automatica.' Isso da ao LLM context awareness sem mudar o pipeline."
    />

    <Finding
      severity="medium"
      title="I3 — Dedup por titulo pode matar o 'cross-source signal'"
      description="O dedup fuzzy (threshold 0.7) remove items com titulos similares, mantendo o de maior engagement. Mas quando o MESMO tema aparece em multiplas sources (Reddit, HN, TechCrunch), isso e um SIGNAL forte de relevancia — nao duplicacao. O dedup destroi esse signal."
      impact="Um anuncio da OpenAI que aparece simultaneamente no HN (500pts), Reddit (200 upvotes), e TechCrunch (RSS) — deveria ser boost signal. Em vez disso, o dedup mantém só a versão HN e descarta as outras. A AYA ve 1 item em vez de 3, perdendo o signal de cross-source traction."
      recommendation="Adicionar campo 'cross_source_count' no SourceItem: quantas sources mencionaram o mesmo tema (usando o fuzzy match que JA existe). Passar esse campo pro LLM como signal. Nao remover duplicatas — apenas marcar e manter a melhor versao com metadata 'also trending on: Reddit, TechCrunch'."
    />

    <div className="bg-gray-50 border rounded-lg p-4 mt-4">
      <h4 className="font-bold text-sm mb-2">Mapa de Responsabilidade: Quem Decide O Que</h4>
      <div className="text-xs space-y-1.5">
        {[
          { decision: "Este item existe no input?", owner: "Source fetch", risk: "Low", note: "Graceful degradation OK" },
          { decision: "Este item e unico?", owner: "Pre-filter dedup", risk: "Medium", note: "Pode matar cross-source signal" },
          { decision: "Este item e recente?", owner: "Pre-filter recency", risk: "Low", note: "Fallback min_items protege" },
          { decision: "Este item e relevante (engagement)?", owner: "Pre-filter scoring", risk: "High", note: "Pesos arbitrarios, cross-source invalido" },
          { decision: "Este item chega ao LLM?", owner: "Pre-filter trim", risk: "Critical", note: "Decisao irreversivel, 77% cortado" },
          { decision: "Este item tem angulo AI?", owner: "Prompt (AI Gate)", risk: "Low", note: "Bem definido, few-shots ajudam" },
          { decision: "Este item e acionavel/sinal?", owner: "Prompt (Step 2)", risk: "Medium", note: "Subjetivo, sem calibracao" },
          { decision: "Este item vira main_find?", owner: "Prompt (Step 4)", risk: "Medium", note: "Anchoring effect dos few-shots" },
          { decision: "O texto ta hype?", owner: "validate_tone", risk: "Low", note: "Regex funciona, pode ter false positives" },
        ].map((row, i) => (
          <div key={i} className="flex items-center gap-2 py-1 border-b border-gray-200 last:border-0">
            <span className="w-52 text-gray-700">{row.decision}</span>
            <span className="w-28 font-bold text-gray-800">{row.owner}</span>
            <SeverityBadge level={row.risk.toLowerCase()} />
            <span className="text-gray-500 flex-1">{row.note}</span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

const RecommendationsTab = () => (
  <div>
    <h3 className="text-lg font-bold text-gray-900 mb-1">Recomendacoes Priorizadas</h3>
    <p className="text-sm text-gray-600 mb-4">Ordenadas por impacto × esforco. Cada uma com justificativa cross-disciplinar.</p>

    <div className="space-y-4">
      <div className="bg-white border-2 border-red-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="bg-red-600 text-white text-xs font-bold px-2 py-0.5 rounded">P0</span>
          <span className="font-bold text-sm">Adicionar reasoning no schema + context do dia no prompt</span>
          <span className="text-xs text-gray-500 ml-auto">~2h dev | impacto: transformacional</span>
        </div>
        <p className="text-sm text-gray-700 mb-2">Combina F1 (observability) + I2 (information loss). Adicionar ao Pydantic schema um campo 'reasoning' com ai_gate_results e ranking_rationale. Injetar no prompt o contexto do dia (total_fetched, source_breakdown). Isso transforma o pipeline de caixa preta em caixa translucida.</p>
        <div className="bg-gray-50 rounded p-2 text-xs font-mono text-gray-600">
          <p>class Reasoning(BaseModel):</p>
          <p>    ai_gate_passed: list[str]  # titulos que passaram</p>
          <p>    ai_gate_rejected_sample: list[str]  # 3-5 exemplos de rejeicao + motivo</p>
          <p>    main_find_rationale: str  # por que esse e o main_find</p>
          <p>    diversity_note: str  # observacao sobre representacao de sources</p>
        </div>
        <p className="text-xs text-gray-500 mt-2">Custo estimado: +200-300 tokens output = +$0.0007/dia. Payoff: debugging de edicoes futuras leva minutos em vez de horas.</p>
      </div>

      <div className="bg-white border-2 border-red-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="bg-red-600 text-white text-xs font-bold px-2 py-0.5 rounded">P0</span>
          <span className="font-bold text-sm">Shuffle dos items antes do LLM</span>
          <span className="text-xs text-gray-500 ml-auto">~15min dev | impacto: alto</span>
        </div>
        <p className="text-sm text-gray-700">Corrige I1 (position bias). Uma linha de codigo: random.shuffle(filtered_items) antes de montar o prompt. O pre-filter ja selecionou os top 30 — a ordem dentro deles nao carrega informacao util, mas carrega vies. Remover o vies e free lunch.</p>
      </div>

      <div className="bg-white border-2 border-orange-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="bg-orange-500 text-white text-xs font-bold px-2 py-0.5 rounded">P1</span>
          <span className="font-bold text-sm">Expandir few-shots + generalizar anti-signal</span>
          <span className="text-xs text-gray-500 ml-auto">~1h dev | impacto: medio-alto</span>
        </div>
        <p className="text-sm text-gray-700">Combina F2 (anchoring) + F5 (closed set). Adicionar 2-3 few-shots de categorias ausentes (infra, regulacao, open source). Trocar anti-signal de lista fechada pra principio + exemplos. Expandir STEP 5 pra 4 templates.</p>
      </div>

      <div className="bg-white border-2 border-orange-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="bg-orange-500 text-white text-xs font-bold px-2 py-0.5 rounded">P1</span>
          <span className="font-bold text-sm">Cross-source signal em vez de dedup destrutivo</span>
          <span className="text-xs text-gray-500 ml-auto">~3h dev | impacto: medio-alto</span>
        </div>
        <p className="text-sm text-gray-700">Corrige I3 + S1 parcialmente. O dedup fuzzy deve marcar duplicatas com cross_source_count em vez de deletar. Passar ao LLM: "also trending on: [sources]". Isso transforma duplicacao de BUG em FEATURE — cross-source traction e um dos signals mais fortes de relevancia real.</p>
      </div>

      <div className="bg-white border-2 border-yellow-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="bg-yellow-500 text-white text-xs font-bold px-2 py-0.5 rounded">P2</span>
          <span className="font-bold text-sm">Fix engagement normalization + wild card zone</span>
          <span className="text-xs text-gray-500 ml-auto">~4h dev | impacto: medio</span>
        </div>
        <p className="text-sm text-gray-700 mb-2">Corrige E1 + E2 + E4. Trocar normalizacao por z-score cross-source. RSS engagement usa mediana real. Reservar 5 slots dos 40 items pra random sample do pool descartado (exploration vs exploitation).</p>
      </div>

      <div className="bg-white border-2 border-yellow-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="bg-yellow-500 text-white text-xs font-bold px-2 py-0.5 rounded">P2</span>
          <span className="font-bold text-sm">Calibracao de pesos via feedback loop</span>
          <span className="text-xs text-gray-500 ml-auto">~2 semanas coleta + 2h analise | impacto: fundamental</span>
        </div>
        <p className="text-sm text-gray-700">Corrige E3. Coletar ratings da Isis ("esse main_find foi bom?") via feedback loop ja deployado. Apos 2-4 semanas, rodar logistic regression simples: quais features (engagement, recency, source, category) predizem "Isis gostou"? Ajustar pesos empiricamente.</p>
      </div>

      <div className="bg-white border-2 border-blue-200 rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="bg-blue-500 text-white text-xs font-bold px-2 py-0.5 rounded">P3</span>
          <span className="font-bold text-sm">Adicionar primary_audience no schema + diversidade de perspectiva no Step 4</span>
          <span className="text-xs text-gray-500 ml-auto">~1h dev | impacto: baixo agora, alto futuro</span>
        </div>
        <p className="text-sm text-gray-700">Corrige S3 + S4. Instrumentacao pra futuro: a AYA indica pra quem cada item e relevante e tenta diversificar perspectivas nos quick_finds. Gera dados sem mudar o output drasticamente.</p>
      </div>
    </div>

    <div className="bg-gray-50 border rounded-lg p-4 mt-4">
      <h4 className="font-bold text-sm mb-2">Roadmap de Implementacao Sugerido</h4>
      <div className="text-sm space-y-2">
        <div className="flex items-center gap-3">
          <span className="font-bold text-gray-600 w-20">Sprint 1</span>
          <span className="text-gray-700">P0s: reasoning schema + shuffle + context injection (~3h)</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-bold text-gray-600 w-20">Sprint 2</span>
          <span className="text-gray-700">P1s: few-shots + cross-source signal + source expansion (~5h)</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-bold text-gray-600 w-20">Sprint 3</span>
          <span className="text-gray-700">P2s: scoring fix + wild cards + iniciar coleta de feedback (~4h)</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="font-bold text-gray-600 w-20">Sprint 4</span>
          <span className="text-gray-700">P2-P3: calibracao de pesos com dados reais + audience tagging (~3h)</span>
        </div>
      </div>
    </div>
  </div>
);

export default function PromptStrategyReview() {
  const [activeTab, setActiveTab] = useState("overview");

  const renderTab = () => {
    switch (activeTab) {
      case "overview": return <OverviewTab />;
      case "prompt": return <PromptTab />;
      case "sociology": return <SociologyTab />;
      case "statistics": return <StatisticsTab />;
      case "interaction": return <InteractionTab />;
      case "recommendations": return <RecommendationsTab />;
      default: return <OverviewTab />;
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 bg-gray-50 min-h-screen">
      <div className="mb-4">
        <h1 className="text-xl font-bold text-gray-900">Daily Scout — Prompt Strategy Review</h1>
        <p className="text-sm text-gray-500">Senior Prompt Engineer + Sociologia + Estatistica | Pipeline v4 Diagnostic</p>
      </div>

      <div className="flex gap-1 mb-4 flex-wrap">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-1.5 text-sm rounded-lg font-medium transition-colors ${
              activeTab === tab.id
                ? "bg-gray-900 text-white"
                : "bg-white text-gray-600 hover:bg-gray-100 border"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow-sm border p-5">
        {renderTab()}
      </div>

      <div className="mt-4 text-center text-xs text-gray-400">
        15 findings | 7 recomendacoes priorizadas | 3 lentes de analise
      </div>
    </div>
  );
}
