import { useState } from "react";

const SEVERITY = { P0: "#EF4444", P1: "#F59E0B", P2: "#3B82F6", OK: "#22C55E" };
const LENS_COLORS = {
  "Prompt Engineering": "#8B5CF6",
  "Jornalismo & Curadoria": "#EC4899",
  "Sociologia & Estatística": "#06B6D4",
};

const findings = [
  // ── PROMPT ENGINEERING ──
  {
    id: "PE-01",
    lens: "Prompt Engineering",
    severity: "OK",
    title: "System ↔ User separation",
    summary: "Divisão limpa: persona + regras de acurácia no system, pipeline + few-shots no user. Sem overlap semântico (problema corrigido na v4).",
    detail: "A system instruction define o 'quem' (AYA) e os guardrails de acurácia (PODE/NÃO PODE). O user prompt define o 'como' (pipeline de 5 steps) e 'o quê' (few-shots + formato). Isso é textbook — facilita iteração independente em cada parte.",
    recommendation: null,
  },
  {
    id: "PE-02",
    lens: "Prompt Engineering",
    severity: "OK",
    title: "Structured output + Pydantic schema",
    summary: "response_schema com CurationOutput força JSON válido. Reasoning schema adiciona observability sem poluir o output final.",
    detail: "Gemini 2.5 Flash com response_mime_type='application/json' + Pydantic schema é o approach mais confiável pra structured output. O campo 'reasoning' dentro do schema (não como chain-of-thought separado) é elegante — fica no JSON mas não vai pro template.",
    recommendation: null,
  },
  {
    id: "PE-03",
    lens: "Prompt Engineering",
    severity: "P1",
    title: "Prompt token budget vs. informação útil",
    summary: "O user prompt (pipeline + 8 few-shots + regras de formato) consome ~3.5K tokens antes de qualquer item. Com 30 items, o input total pode bater 6-7K tokens. O ratio instrução/dados está alto.",
    detail: "Few-shots são o mecanismo mais eficaz de alignment, mas 8 exemplos completos (com input E output) podem estar competindo por atenção com os dados reais. O Gemini Flash tem context window grande, mas attention allocation em prompts longos favorece início e fim (primacy/recency effect no próprio prompt).",
    recommendation: "Considerar: (1) Mover 3-4 few-shots menos críticos pra um 'calibration document' no system instruction, mantendo no user prompt apenas os 4 mais impactantes (ex: seleção correta, descarte correto, tom rumor, regulação). (2) Medir empiricamente: rodar A/B com 4 vs 8 few-shots e comparar quality do output.",
  },
  {
    id: "PE-04",
    lens: "Prompt Engineering",
    severity: "P2",
    title: "Anti-signal: princípio vago + lista fechada = zona cinza",
    summary: "A instrução 'Use o princípio, não apenas a lista' é correta conceitualmente, mas LLMs performam melhor com heurísticas concretas do que com princípios abstratos.",
    detail: "O STEP 3 dá 6 exemplos de anti-signal e depois diz 'se não se enquadra nesses exemplos mas foge do escopo, DESCARTE também'. Isso força o modelo a fazer raciocínio analógico sem few-shot de suporte — é o tipo de instrução que funciona 80% das vezes mas falha nos edge cases ambíguos.",
    recommendation: "Adicionar 2-3 few-shots de edge cases ambíguos no anti-signal. Ex: 'Chip shortage affects gaming GPU prices' (anti-signal: gaming news, NÃO infra AI) vs 'NVIDIA H200 shortage delays AI training at scale' (sinal: infra AI). O princípio fica, mas com calibração.",
  },
  {
    id: "PE-05",
    lens: "Prompt Engineering",
    severity: "P2",
    title: "Reasoning schema com cap artificial",
    summary: "ai_gate_passed: list[str] com 'max 15' limita a observability quando há muitos items passando.",
    detail: "Se 25 dos 30 items passam no AI Gate, você só vê 15 — perde visibilidade sobre a outra metade. O campo ai_gate_rejected_sample (3-5 exemplos) é bom, mas o passed deveria ser ilimitado ou ter cap mais alto.",
    recommendation: "Remover o cap do ai_gate_passed ou subir pra 25. O custo em tokens é marginal (são apenas títulos) e a observability é valiosa pra debugging.",
  },
  {
    id: "PE-06",
    lens: "Prompt Engineering",
    severity: "OK",
    title: "Shuffle anti-bias",
    summary: "random.shuffle() antes de enviar ao LLM remove position bias. Combinado com sort do pre-filter, a ordem no prompt é decorrelacionada do score.",
    detail: "Primacy effect em LLMs é bem documentado — items no início da lista recebem mais atenção. O shuffle resolve isso. O pre-filter já fez o trabalho de quality, então a ordem no prompt pode ser aleatória sem perda de sinal.",
    recommendation: null,
  },
  {
    id: "PE-07",
    lens: "Prompt Engineering",
    severity: "P1",
    title: "STEP 5 — Teste Final usa completion task, mas sem enforcement estrutural",
    summary: "O teste pede pra AYA 'completar UMA das frases'. Mas não há campo no schema que force essa completude — é instrução textual sem validação.",
    detail: "Ao contrário do reasoning (que tem schema), o teste final é puramente honor-system. O modelo pode dizer que fez o teste sem realmente fazer. Não há como verificar no post-processing se o teste foi aplicado.",
    recommendation: "Adicionar um campo 'step5_test: str' no MainFind e QuickFind schemas, obrigando AYA a preencher a frase completada. Isso cria enforcement estrutural + audit trail.",
  },
  // ── JORNALISMO & CURADORIA ──
  {
    id: "JC-01",
    lens: "Jornalismo & Curadoria",
    severity: "OK",
    title: "AI Gate como filtro editorial primário",
    summary: "Excelente decisão editorial. Define a lente da newsletter de forma inequívoca e resolve o problema da edição #001 (prediction markets sem ângulo AI).",
    detail: "Em jornalismo de nicho, a lente editorial é o ativo mais valioso. O AI Gate funciona como um editorial policy document automatizado — qualquer editor humano faria a mesma pergunta antes de incluir uma pauta.",
    recommendation: null,
  },
  {
    id: "JC-02",
    lens: "Jornalismo & Curadoria",
    severity: "OK",
    title: "Preservação de certeza (certainty rule)",
    summary: "A regra 'may → poderia, reportedly → segundo relatos' é jornalismo 101 bem implementado. Resolve o problema mais comum de LLMs: converter especulação em fato.",
    detail: "Esta é provavelmente a regra de acurácia mais impactante do prompt. Combinada com os few-shots 4 e 5 (rumor e business), cria um pattern matching forte pro modelo.",
    recommendation: null,
  },
  {
    id: "JC-03",
    lens: "Jornalismo & Curadoria",
    severity: "P0",
    title: "Monocultura de fontes: 100% anglófona, tech-insider",
    summary: "Reddit, HN, TechCrunch e Lobsters compartilham a mesma bolha: profissionais de tech anglófonos, majoritariamente americanos. Zero cobertura internacional direta.",
    detail: "Para uma newsletter lida por profissionais brasileiros, há gaps enormes: regulação da UE (AI Act), movimentos na Ásia (Baidu, DeepSeek, ministério japonês de AI), LatAm (Mercado Livre AI, startups locais), e África (AI policy do AU). O TechCrunch cobre parte disso, mas com lente americana. A curadoria herda os vieses de seleção das fontes.",
    recommendation: "Adicionar pelo menos 2 fontes com perspectiva não-americana: (1) The Verge ou Ars Technica (mais editorial, menos echo-chamber que HN), (2) RSS de um veículo europeu (The Register, Sifted) ou asiático. Também considerar: arXiv RSS pra research papers com tag cs.AI — dá cobertura acadêmica que nenhuma fonte atual tem. A arquitetura plugável (SourceRegistry) já suporta isso.",
  },
  {
    id: "JC-04",
    lens: "Jornalismo & Curadoria",
    severity: "P0",
    title: "Zero memória editorial: AYA não sabe o que já foi publicado",
    summary: "Sem contexto de edições anteriores, a mesma história pode ser main_find em edições consecutivas. E não há follow-up tracking.",
    detail: "Bom jornalismo é cumulativo — 'ontem reportamos X, hoje há atualização Y'. AYA opera como se cada edição fosse a primeira. Isso causa: (1) repetição de temas quando algo trending fica vários dias no HN, (2) perda de arcos narrativos, (3) zero senso de 'já cobrimos isso'.",
    recommendation: "Injetar no context_block um resumo das últimas 3 edições (titles + main_find de cada). Pode ser um JSON mínimo: [{edition: '004', main_find: 'título', quick_finds: ['t1','t2','t3']}]. Adicionar instrução: 'Se um item já foi coberto, só inclua se houver update significativo — e mencione o follow-up.' Custo: ~200-300 tokens extras.",
  },
  {
    id: "JC-05",
    lens: "Jornalismo & Curadoria",
    severity: "P1",
    title: "Ausência de 'negative signal' — o que NÃO está sendo discutido",
    summary: "Bons curadores notam silêncios. Se toda semana tem news sobre OpenAI e numa edição não tem, isso é informação. AYA não tem essa capacidade.",
    detail: "Na prática jornalística, 'the dog that didn't bark' é um sinal editorial forte. Se regulação de AI sumiu do feed depois de semanas de cobertura, pode indicar que algo mudou. Isso requer memória editorial (JC-04) como pré-requisito.",
    recommendation: "Após implementar JC-04, adicionar no editorial_note do Meta schema: 'Se algum tema frequente das últimas edições DESAPARECEU do feed hoje, mencione.' Isso dá à AYA capacidade de curadoria por ausência — diferencial raro em newsletters automatizadas.",
  },
  {
    id: "JC-06",
    lens: "Jornalismo & Curadoria",
    severity: "P1",
    title: "STEP 1.5 (Source Bias Check) cobre só blogs de AI companies",
    summary: "A regra anti press-release é boa, mas só olha pra blog.anthropic.com, openai.com/blog etc. Press releases de big tech não-AI (Apple, Microsoft, Amazon) passam sem checagem.",
    detail: "Uma Amazon publicando no blog que 'está usando AI pra melhorar entregas' é marketing do mesmo tipo. A heurística deveria ser: 'qualquer blog corporativo oficial que não traz feature/produto testável = descarte potencial.'",
    recommendation: "Generalizar STEP 1.5 para 'blogs oficiais de qualquer empresa'. Manter os exemplos atuais e adicionar: 'Aplica a mesma lógica a blogs corporativos de qualquer empresa — se não há novidade concreta que o leitor possa usar, DESCARTE.'",
  },
  {
    id: "JC-07",
    lens: "Jornalismo & Curadoria",
    severity: "P2",
    title: "primary_audience como campo mas sem uso no pipeline",
    summary: "O schema pede primary_audience ('developers', 'PMs e founders', etc.) mas o pipeline de seleção não usa essa informação. É instrumentação sem ação.",
    detail: "Se o objetivo é futuro (personalização, segmentação), ok. Mas sem instrução de como usar, AYA pode defaultar pra 'todos' na maioria dos items.",
    recommendation: "Adicionar no STEP 4: 'Diversidade de AUDIÊNCIA: se todos os quick_finds são para developers, priorize pelo menos 1 item com primary_audience diferente.' Isso ativa o campo dentro do pipeline.",
  },
  // ── SOCIOLOGIA & ESTATÍSTICA ──
  {
    id: "SE-01",
    lens: "Sociologia & Estatística",
    severity: "P0",
    title: "Popularity bias sistêmico: engagement_weight=0.4 domina o pre-filter",
    summary: "Upvotes e comments medem popularidade, não relevância editorial. Com peso 0.4, o pre-filter sistema ativamente seleciona contra conteúdo niche-but-important.",
    detail: "Pesquisa em information retrieval mostra que engagement metrics correlacionam com: controversialidade > qualidade, clickbait > nuance, US-centric > internacional, consumer > infraestrutura. Um paper acadêmico sobre segurança de AI com 15 upvotes no r/MachineLearning é editorialmente mais relevante que um meme com 2000 upvotes. O scoring atual descarta o paper antes que AYA sequer veja.",
    recommendation: "Reduzir engagement_weight pra 0.25 e redistribuir pra category_weight (atualmente 0.1 com valor neutro 0.5). Implementar category_weight real: items com category='AI/ML' ou 'research' ganham boost. Isso corrige parcialmente o popularity bias sem eliminar engagement como sinal.",
  },
  {
    id: "SE-02",
    lens: "Sociologia & Estatística",
    severity: "P1",
    title: "Echo chamber cross-source: HN + Reddit + Lobsters compartilham audiência",
    summary: "Uma história que viraliza no HN aparece no Reddit e Lobsters horas depois. O pipeline trata como 'multi-source validation' quando na verdade é a mesma bolha ecoando.",
    detail: "A dedup por URL pega links idênticos, e a dedup por título similar pega reposts. Mas discussões SOBRE o mesmo tema com títulos diferentes passam — ex: 'OpenAI launches X' (TechCrunch), 'Thoughts on OpenAI X' (HN), 'Why OpenAI X matters' (Reddit). São 3 items no feed, todos sobre o mesmo evento, inflando artificialmente sua representação. O diversity_score no scoring penaliza source concentration mas não penaliza topic concentration.",
    recommendation: "Adicionar topic clustering no pre-filter: agrupar items por tema (embeddings ou keyword overlap) e cap por cluster. Versão simples: extrair entities (nomes de empresas/produtos) dos títulos e aplicar diversity cap por entity, similar ao max_per_source_pct. Versão sofisticada: embedding similarity com threshold.",
  },
  {
    id: "SE-03",
    lens: "Sociologia & Estatística",
    severity: "P1",
    title: "Survivorship bias: only socially-posted content enters the funnel",
    summary: "O pipeline só vê o que foi postado em Reddit/HN/Lobsters/TechCrunch. Research papers, government reports, corporate filings — todo um universo de informação relevante fica invisível.",
    detail: "Para uma newsletter com lente AI, ArXiv (cs.AI, cs.CL, cs.LG) é provavelmente a fonte primária mais importante que está ausente. Policy documents (EU AI Act updates, NIST guidelines), SEC filings (que revelam investimentos reais em AI), e patent databases (que mostram direção técnica de empresas) são todos blind spots.",
    recommendation: "Priorizar ArXiv RSS como próxima source — é gratuito, estruturado, e cobre o gap de research. A arquitetura plugável já suporta. Criar sources/arxiv.py com feed de cs.AI + cs.CL. Scoring: engagement_score neutro (0.5, como RSS-only — já implementado!), recency alto (papers são publicados por data).",
  },
  {
    id: "SE-04",
    lens: "Sociologia & Estatística",
    severity: "P2",
    title: "Sem baseline de qualidade: impossível medir se AYA cura melhor que random",
    summary: "Não há mecanismo pra comparar a curadoria da AYA com uma seleção aleatória dos mesmos items que passaram no AI Gate.",
    detail: "Sem baseline, não dá pra saber se o pipeline de 5 steps realmente melhora a seleção ou se é theater. Um A/B simples: random selection de 6 items AI-Gate-passing vs. curadoria AYA → enviar ambas pras mesmas métricas de feedback loop.",
    recommendation: "Implementar 'shadow curation': gerar uma edição alternativa com seleção aleatória, salvar como artifact (sem enviar), e comparar com a edição real nas métricas do feedback loop ao longo de 10-20 edições. Isso dá evidência estatística de que o pipeline agrega valor.",
  },
  {
    id: "SE-05",
    lens: "Sociologia & Estatística",
    severity: "P2",
    title: "Recency bias penaliza slow-burn stories",
    summary: "recency_decay_hours=12 com peso 0.3 significa que um paper publicado há 20h já perdeu ~60% do recency score. Policy changes e research são sistematicamente penalizados.",
    detail: "Notícias de produto viralizam em horas; papers de research acumulam tração em dias; mudanças de regulação levam semanas. O decay uniforme de 12h trata todos como breaking news.",
    recommendation: "Implementar decay variável por category: 'product/launch' → 12h, 'research/paper' → 48h, 'policy/regulation' → 72h. Requer que as sources classifiquem category (já existe no SourceItem). Alternativa simples: subir recency_decay_hours pra 24h uniformemente.",
  },
];

const scorecard = {
  "Prompt Engineering": { score: "B+", label: "Sólido, com refinamentos pontuais" },
  "Jornalismo & Curadoria": { score: "B-", label: "Bom pipeline, fontes limitadas" },
  "Sociologia & Estatística": { score: "C+", label: "Biases sistêmicos não endereçados" },
};

const priorityMap = [
  { id: "JC-03", title: "Adicionar fontes não-anglófonas", effort: "Medium", impact: "Alto" },
  { id: "JC-04", title: "Memória editorial (últimas 3 edições)", effort: "Low", impact: "Alto" },
  { id: "SE-01", title: "Rebalancear engagement_weight no scoring", effort: "Low", impact: "Alto" },
  { id: "PE-07", title: "Enforcement estrutural do STEP 5 (schema)", effort: "Low", impact: "Médio" },
  { id: "PE-03", title: "Otimizar ratio few-shots no prompt", effort: "Medium", impact: "Médio" },
  { id: "SE-02", title: "Topic clustering no pre-filter", effort: "High", impact: "Alto" },
  { id: "SE-03", title: "ArXiv como source (research papers)", effort: "Medium", impact: "Alto" },
];

function Badge({ severity }) {
  return (
    <span
      style={{
        background: SEVERITY[severity],
        color: severity === "P2" ? "#fff" : severity === "OK" ? "#fff" : "#000",
        padding: "2px 8px",
        borderRadius: "4px",
        fontSize: "11px",
        fontWeight: 700,
        letterSpacing: "0.5px",
      }}
    >
      {severity}
    </span>
  );
}

function LensBadge({ lens }) {
  return (
    <span
      style={{
        background: LENS_COLORS[lens] + "22",
        color: LENS_COLORS[lens],
        padding: "2px 8px",
        borderRadius: "4px",
        fontSize: "10px",
        fontWeight: 600,
        border: `1px solid ${LENS_COLORS[lens]}44`,
      }}
    >
      {lens}
    </span>
  );
}

function FindingCard({ finding, isExpanded, onToggle }) {
  return (
    <div
      style={{
        background: "#1E293B",
        border: `1px solid ${SEVERITY[finding.severity]}33`,
        borderLeft: `3px solid ${SEVERITY[finding.severity]}`,
        borderRadius: "8px",
        padding: "16px",
        marginBottom: "8px",
        cursor: "pointer",
      }}
      onClick={onToggle}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
        <Badge severity={finding.severity} />
        <LensBadge lens={finding.lens} />
        <span style={{ color: "#94A3B8", fontSize: "11px", fontFamily: "monospace" }}>{finding.id}</span>
      </div>
      <div style={{ color: "#F1F5F9", fontSize: "14px", fontWeight: 600, marginBottom: "6px" }}>
        {finding.title}
      </div>
      <div style={{ color: "#CBD5E1", fontSize: "13px", lineHeight: "1.5" }}>
        {finding.summary}
      </div>
      {isExpanded && (
        <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid #334155" }}>
          <div style={{ color: "#94A3B8", fontSize: "12px", lineHeight: "1.6", marginBottom: "12px" }}>
            {finding.detail}
          </div>
          {finding.recommendation && (
            <div
              style={{
                background: "#0F172A",
                borderRadius: "6px",
                padding: "12px",
                borderLeft: `2px solid ${SEVERITY[finding.severity]}`,
              }}
            >
              <div style={{ color: "#F59E0B", fontSize: "11px", fontWeight: 700, marginBottom: "6px", letterSpacing: "0.5px" }}>
                RECOMENDAÇÃO
              </div>
              <div style={{ color: "#E2E8F0", fontSize: "12px", lineHeight: "1.6" }}>
                {finding.recommendation}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function PromptAudit() {
  const [expandedId, setExpandedId] = useState(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const [showPriority, setShowPriority] = useState(false);

  const lenses = ["all", ...Object.keys(LENS_COLORS)];
  const filtered = activeFilter === "all" ? findings : findings.filter((f) => f.lens === activeFilter);

  const stats = {
    P0: findings.filter((f) => f.severity === "P0").length,
    P1: findings.filter((f) => f.severity === "P1").length,
    P2: findings.filter((f) => f.severity === "P2").length,
    OK: findings.filter((f) => f.severity === "OK").length,
  };

  return (
    <div style={{ background: "#0F172A", minHeight: "100vh", color: "#E2E8F0", fontFamily: "'Inter', system-ui, sans-serif" }}>
      {/* Header */}
      <div style={{ padding: "24px 24px 0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "4px" }}>
          <span style={{ color: "#22C55E", fontSize: "13px", fontFamily: "monospace", fontWeight: 700 }}>DAILY SCOUT</span>
          <span style={{ color: "#334155" }}>|</span>
          <span style={{ color: "#94A3B8", fontSize: "13px" }}>Prompt Audit v5.0</span>
        </div>
        <h1 style={{ fontSize: "22px", fontWeight: 700, color: "#F1F5F9", margin: "8px 0 4px" }}>
          Audit: Pipeline Editorial da AYA
        </h1>
        <p style={{ color: "#94A3B8", fontSize: "13px", margin: 0 }}>
          3 lentes: Prompt Engineering + Jornalismo & Curadoria + Sociologia & Estatística
        </p>
      </div>

      {/* Scorecard */}
      <div style={{ padding: "16px 24px", display: "flex", gap: "12px", flexWrap: "wrap" }}>
        {Object.entries(scorecard).map(([lens, data]) => (
          <div
            key={lens}
            style={{
              background: "#1E293B",
              borderRadius: "8px",
              padding: "12px 16px",
              flex: "1 1 180px",
              borderTop: `2px solid ${LENS_COLORS[lens]}`,
            }}
          >
            <div style={{ fontSize: "11px", color: LENS_COLORS[lens], fontWeight: 600, marginBottom: "4px" }}>{lens}</div>
            <div style={{ fontSize: "24px", fontWeight: 800, color: "#F1F5F9" }}>{data.score}</div>
            <div style={{ fontSize: "11px", color: "#94A3B8" }}>{data.label}</div>
          </div>
        ))}
      </div>

      {/* Stats bar */}
      <div style={{ padding: "0 24px 12px", display: "flex", gap: "16px", alignItems: "center" }}>
        {Object.entries(stats).map(([sev, count]) => (
          <div key={sev} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: SEVERITY[sev] }} />
            <span style={{ fontSize: "12px", color: "#94A3B8" }}>{sev}: {count}</span>
          </div>
        ))}
        <div style={{ flex: 1 }} />
        <button
          onClick={() => setShowPriority(!showPriority)}
          style={{
            background: showPriority ? "#F59E0B" : "#334155",
            color: showPriority ? "#000" : "#CBD5E1",
            border: "none",
            borderRadius: "6px",
            padding: "6px 12px",
            fontSize: "12px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          {showPriority ? "Ver Findings" : "Ver Priority Map"}
        </button>
      </div>

      {/* Priority Map */}
      {showPriority && (
        <div style={{ padding: "0 24px 16px" }}>
          <div style={{ background: "#1E293B", borderRadius: "8px", padding: "16px" }}>
            <div style={{ color: "#F59E0B", fontSize: "12px", fontWeight: 700, marginBottom: "12px", letterSpacing: "0.5px" }}>
              PRIORITY ROADMAP (esforço → impacto)
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {priorityMap.map((item, i) => (
                <div
                  key={item.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    padding: "8px 12px",
                    background: i < 3 ? "#22C55E11" : "#0F172A",
                    borderRadius: "6px",
                    borderLeft: i < 3 ? "2px solid #22C55E" : "2px solid #334155",
                  }}
                >
                  <span style={{ color: "#94A3B8", fontSize: "11px", fontFamily: "monospace", minWidth: "42px" }}>{item.id}</span>
                  <span style={{ color: "#F1F5F9", fontSize: "13px", flex: 1 }}>{item.title}</span>
                  <span
                    style={{
                      fontSize: "10px",
                      padding: "2px 6px",
                      borderRadius: "3px",
                      background: item.effort === "Low" ? "#22C55E22" : item.effort === "Medium" ? "#F59E0B22" : "#EF444422",
                      color: item.effort === "Low" ? "#22C55E" : item.effort === "Medium" ? "#F59E0B" : "#EF4444",
                    }}
                  >
                    {item.effort}
                  </span>
                  <span
                    style={{
                      fontSize: "10px",
                      padding: "2px 6px",
                      borderRadius: "3px",
                      background: item.impact === "Alto" ? "#8B5CF622" : "#3B82F622",
                      color: item.impact === "Alto" ? "#8B5CF6" : "#3B82F6",
                    }}
                  >
                    Impact: {item.impact}
                  </span>
                </div>
              ))}
            </div>
            <div style={{ marginTop: "12px", padding: "10px", background: "#0F172A", borderRadius: "6px", fontSize: "12px", color: "#94A3B8", lineHeight: "1.6" }}>
              Os 3 primeiros items (highlighted) formam o <strong style={{ color: "#22C55E" }}>Quick Win Pack</strong>: alto impacto com esforço low-to-medium. Podem ser implementados em 1-2 sprints sem mudança na arquitetura.
            </div>
          </div>
        </div>
      )}

      {/* Filter tabs */}
      {!showPriority && (
        <>
          <div style={{ padding: "0 24px 12px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {lenses.map((lens) => (
              <button
                key={lens}
                onClick={() => setActiveFilter(lens)}
                style={{
                  background: activeFilter === lens ? (lens === "all" ? "#475569" : LENS_COLORS[lens] + "33") : "#1E293B",
                  color: activeFilter === lens ? (lens === "all" ? "#F1F5F9" : LENS_COLORS[lens]) : "#94A3B8",
                  border: `1px solid ${activeFilter === lens ? (lens === "all" ? "#475569" : LENS_COLORS[lens] + "66") : "#334155"}`,
                  borderRadius: "6px",
                  padding: "6px 12px",
                  fontSize: "12px",
                  fontWeight: 500,
                  cursor: "pointer",
                }}
              >
                {lens === "all" ? `Todos (${findings.length})` : lens}
              </button>
            ))}
          </div>

          {/* Findings */}
          <div style={{ padding: "0 24px 24px" }}>
            {filtered.map((f) => (
              <FindingCard
                key={f.id}
                finding={f}
                isExpanded={expandedId === f.id}
                onToggle={() => setExpandedId(expandedId === f.id ? null : f.id)}
              />
            ))}
          </div>
        </>
      )}

      {/* Footer */}
      <div style={{ padding: "0 24px 24px", borderTop: "1px solid #1E293B", paddingTop: "16px" }}>
        <div style={{ color: "#475569", fontSize: "11px", fontFamily: "monospace" }}>
          audit_by: prompt_engineer_senior | lenses: journalism, sociology, statistics | target: daily-scout v5.0
        </div>
      </div>
    </div>
  );
}
