import { useState } from "react";

const Badge = ({ children, color = "gray" }) => {
  const colors = {
    red: "bg-red-900 text-red-300 border-red-700",
    amber: "bg-amber-900 text-amber-300 border-amber-700",
    emerald: "bg-emerald-900 text-emerald-300 border-emerald-700",
    blue: "bg-blue-900 text-blue-300 border-blue-700",
    purple: "bg-purple-900 text-purple-300 border-purple-700",
    gray: "bg-gray-800 text-gray-300 border-gray-700",
    cyan: "bg-cyan-900 text-cyan-300 border-cyan-700",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${colors[color]}`}>
      {children}
    </span>
  );
};

const Card = ({ children, className = "" }) => (
  <div className={`bg-gray-900 rounded-xl p-6 border border-gray-800 ${className}`}>
    {children}
  </div>
);

const TABS = [
  { id: "diagnosis", label: "Diagnóstico" },
  { id: "plan", label: "Plano de Fix" },
  { id: "order", label: "Ordem & Riscos" },
  { id: "validation", label: "Validação" },
];

const PromptFixPlan = () => {
  const [tab, setTab] = useState("diagnosis");
  const [expandedFix, setExpandedFix] = useState(null);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 font-sans">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-2 h-2 rounded-full bg-red-400 animate-pulse" />
            <span className="text-red-400 text-xs font-mono uppercase tracking-widest">
              Prompt Engineering — Fix Plan v5.3
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            4 fixes editoriais: diagnóstico, implementação e validação
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Baseado no output do dry run v5.2 — 27/03/2026
          </p>
        </div>

        {/* Tabs */}
        <div className="flex flex-wrap gap-1 mb-6 bg-gray-900 rounded-lg p-1 w-fit">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-all ${
                tab === t.id
                  ? "bg-red-500 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* ═══ DIAGNÓSTICO ═══ */}
        {tab === "diagnosis" && (
          <div className="space-y-6">
            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                Análise do output — o que falhou e por quê
              </h2>
              <p className="text-gray-400 text-sm mb-6">
                O dry run v5.2 rodou com sucesso técnico (fix de truncação OK), mas
                o output editorial tem 4 problemas identificados. Cada um tem uma
                root cause diferente no prompt.
              </p>

              <div className="space-y-4">
                {[
                  {
                    id: "P1",
                    severity: "P0",
                    title: "Main find é notícia velha requentada",
                    output: '"OpenAI descontinua Sora" — evento de dias/semanas atrás',
                    rootCause: "O pre-filter checa recência do POST (quando foi publicado), não do EVENTO. O prompt não tem instrução pra detectar rehashed news. O Gemini tem world knowledge pra saber que Sora foi descontinuado antes, mas ninguém pediu pra ele usar isso.",
                    promptGap: "Nenhum STEP filtra por freshness do EVENTO subjacente",
                    layer: "Prompt (STEP 3)",
                    color: "red",
                  },
                  {
                    id: "P2",
                    severity: "P0",
                    title: "Main find mistura 2 notícias não-relacionadas",
                    output: '"OpenAI descontinua Sora; Meta enfrenta problemas legais"',
                    rootCause: "TechCrunch publica vídeo-roundups com títulos compostos ('X; Y; Z'). O pre-filter não diferencia post singular de roundup. O prompt diz 'main_find = item mais acionável' mas não diz 'main_find = UM evento'.",
                    promptGap: "Sem regra de singularidade no main_find. Sem heurística de roundup no pre-filter.",
                    layer: "Prompt (STEP 4) + Pre-filter",
                    color: "red",
                  },
                  {
                    id: "P3",
                    severity: "P1",
                    title: "Correspondent intro genérico",
                    output: '"O dia trouxe novidades sobre a estratégia de grandes players..."',
                    rootCause: "A instrução diz 'cite dado concreto' mas a AYA interpreta como 'diga quantos posts analisou'. Falta instrução pra referenciar o main_find e falta exemplo negativo de intro genérico.",
                    promptGap: "Instrução de formato ambígua. Sem negative example.",
                    layer: "Prompt (REGRAS DE FORMATO)",
                    color: "amber",
                  },
                  {
                    id: "P4",
                    severity: "P2",
                    title: "Funding round passou no filtro",
                    output: '"Aetherflux busca Série B com valuation de US$ 2 bilhões"',
                    rootCause: "STEP 3 diz 'Funding round sem ângulo AI/tech específico' → AYA entende que se a empresa É de AI, tem ângulo. Mas funding round de empresa de AI não é automaticamente acionável pro leitor.",
                    promptGap: "Filtro de funding frouxo — 'ângulo AI' é interpretado como 'é empresa de AI'",
                    layer: "Prompt (STEP 3)",
                    color: "blue",
                  },
                ].map((p) => (
                  <div
                    key={p.id}
                    className="bg-gray-800 rounded-lg p-4 border-l-4"
                    style={{
                      borderColor:
                        p.color === "red"
                          ? "#EF4444"
                          : p.color === "amber"
                          ? "#F59E0B"
                          : "#3B82F6",
                    }}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <Badge color={p.color}>{p.severity}</Badge>
                      <Badge color="gray">{p.id}</Badge>
                      <span className="text-white text-sm font-medium">{p.title}</span>
                    </div>
                    <div className="text-gray-500 text-xs font-mono mb-3 bg-gray-900 rounded px-3 py-1.5">
                      Output: {p.output}
                    </div>
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-gray-500">Root cause: </span>
                        <span className="text-gray-300">{p.rootCause}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Gap no prompt: </span>
                        <span className="text-amber-400">{p.promptGap}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Camada: </span>
                        <span className="text-cyan-400">{p.layer}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Dependency map */}
            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                Mapa de dependência entre problemas
              </h2>
              <div className="bg-gray-800 rounded-lg p-4 font-mono text-sm">
                <div className="text-gray-400 mb-2">
                  P1 (old news) + P2 (compound) → causaram juntos o main_find ruim
                </div>
                <div className="text-gray-400 mb-2">
                  P3 (intro genérico) → consequência de P1/P2 (intro reflete main_find fraco)
                </div>
                <div className="text-gray-400">
                  P4 (funding filter) → independente, mas revela frouxidão do STEP 3
                </div>
                <div className="mt-4 text-amber-400">
                  Implicação: se P1+P2 fossem resolvidos, P3 provavelmente melhoraria
                  sozinho. Mas o fix de P3 é barato e previne recorrência.
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* ═══ PLANO DE FIX ═══ */}
        {tab === "plan" && (
          <div className="space-y-6">
            {[
              {
                id: "FIX-A",
                title: "Freshness Gate — filtrar notícia velha requentada",
                severity: "P0",
                color: "red",
                where: "STEP 3 — ANTI-SIGNAL (expandir)",
                rationale:
                  "Criar um STEP novo (1.75) seria overhead — o pipeline já tem 7 steps. Melhor expandir STEP 3 com um anti-signal específico para rehashed news. O Gemini 2.5 Flash tem world knowledge suficiente pra detectar 'isso já aconteceu'.",
                alternativeConsidered:
                  "STEP 1.75 FRESHNESS GATE como step separado. Descartado: adicionar mais steps aumenta complexity do prompt e risco de conflito entre steps. O STEP 3 já é onde anti-signals vivem.",
                change: {
                  type: "Prompt: adicionar anti-signal + few-shot",
                  prompt: `→ Rehashed news: se o título reporta evento que você sabe que já aconteceu dias ou semanas atrás (lançamento já anunciado, descontinuação já reportada, aquisição já fechada), DESCARTE — mesmo que o post seja de hoje. Exceção: se o título traz INFORMAÇÃO NOVA sobre o evento (dados, reação, consequência concreta), trate como story nova.`,
                  fewShot: `Exemplo 11 — DESCARTE CORRETO (rehashed news):
Input: {{ "title": "OpenAI shuts down Sora video generation tool", "source": "TechCrunch", "score": 0 }}
→ AI gate: SIM (ferramenta de AI)
→ Freshness check: a descontinuação do Sora já foi amplamente reportada dias atrás. Este post não traz informação nova.
→ DESCARTADO — rehashed news, evento já coberto anteriormente

Exemplo 11b — SELEÇÃO CORRETA (follow-up com info nova):
Input: {{ "title": "Sora users report losing paid credits after OpenAI shutdown — no refund policy", "source": "HackerNews", "score": 423 }}
→ AI gate: SIM
→ Freshness check: embora o shutdown do Sora seja velho, este post traz informação nova (perda de créditos, ausência de política de reembolso)
→ SELECIONADO — info nova + acionável (afeta quem pagou pelo Sora)`,
                },
                sideEffects: [
                  "Risco de false positive: modelo pode rejeitar follow-up legítimo. Mitigado pela exceção 'informação nova'.",
                  "Depende de world knowledge do Gemini — se o evento for muito recente (horas), o modelo pode não saber. Aceitável: o pre-filter de recência cobre esse caso.",
                ],
                tokenImpact: "+~120 tokens no prompt (anti-signal + 2 few-shots)",
              },
              {
                id: "FIX-B",
                title: "Singularidade do main_find — 1 evento, não roundup",
                severity: "P0",
                color: "red",
                where: "STEP 4 — RANKING (adicionar regra) + Pre-filter (heurística)",
                rationale:
                  "Duas camadas de defesa: (1) prompt rule no STEP 4 que main_find deve ser UM evento, (2) heurística no pre-filter que flagga títulos compostos com ';' ou padrão roundup.",
                alternativeConsidered:
                  "Só prompt rule sem pre-filter heurística. Descartado: se o título chega ao LLM como 'X; Y; Z', o modelo pode interpretar como um único evento. Melhor sinalizar antes.",
                change: {
                  type: "Prompt + Pre-filter code",
                  prompt: `→ main_find DEVE ser sobre UM evento específico. Se um post é roundup/compilação (título com múltiplas notícias separadas por ';' ou 'and' sem relação causal), NÃO use como main_find. Extraia o evento mais relevante individualmente ou prefira outro item.`,
                  code: `# pre_filter.py — flag compound titles
def _flag_compound_titles(items):
    """Marca títulos que parecem roundups (';' separator ou padrão 'X and Y')."""
    compound_pattern = re.compile(r';|\\band\\b.*\\band\\b', re.IGNORECASE)
    for item in items:
        if compound_pattern.search(item.title):
            item.metadata['is_compound'] = True
            logger.info(f"  [COMPOUND] '{item.title[:60]}...'")
    return items`,
                },
                sideEffects: [
                  "Títulos legítimos com ';' (ex: 'OpenAI launches GPT-5; sets new benchmark') podem ser flaggados. Mitigado: flag é informational, não bloqueante.",
                  "A regra no prompt diz 'não use como main_find' mas permite como quick_find — roundups podem ter items bons dentro.",
                ],
                tokenImpact: "+~40 tokens no prompt. Code change no pre_filter.py.",
              },
              {
                id: "FIX-C",
                title: "Correspondent intro deve referenciar o achado do dia",
                severity: "P1",
                color: "amber",
                where: "REGRAS DE FORMATO — reescrever instrução",
                rationale:
                  "A instrução atual é ambígua ('cite dado concreto'). O modelo interpreta como métricas (X posts, Y fontes). Precisa ser específica: referencie o main_find pelo nome.",
                alternativeConsidered:
                  "Adicionar few-shot de intro. Descartado: os 10 few-shots atuais não cobrem intro — e adicionar um 12o exemplo só pra intro é token waste. Melhor reescrever a instrução com positive + negative example inline.",
                change: {
                  type: "Prompt: reescrever instrução de formato",
                  prompt: `ANTES:
- correspondent_intro: 1-2 frases curtas em primeira pessoa. Cite dado concreto do contexto do dia (total de fontes, quantos posts analisados, qual tema dominou).

DEPOIS:
- correspondent_intro: 1-2 frases em primeira pessoa. A PRIMEIRA frase deve referenciar o achado do dia pelo tema (não pelo nome do campo). A segunda pode citar volume (X posts de Y fontes).
  BOM: "Hoje o destaque é a descontinuação do Sora pela OpenAI. Analisei 267 posts de 10 fontes."
  RUIM: "O dia trouxe novidades sobre a estratégia de grandes players de AI." (genérico, serve pra qualquer dia)`,
                },
                sideEffects: [
                  "Intro fica acoplado ao main_find — se o main_find mudar em retry, o intro precisa mudar junto. Risco baixo: são gerados na mesma chamada.",
                ],
                tokenImpact: "+~60 tokens (instrução expandida com positive/negative example)",
              },
              {
                id: "FIX-D",
                title: "Apertar filtro de funding rounds",
                severity: "P2",
                color: "blue",
                where: "STEP 3 — ANTI-SIGNAL (refinar item existente)",
                rationale:
                  "O filtro atual ('funding round sem ângulo AI/tech específico') é interpretado loose: 'a empresa É de AI' conta como ângulo. Precisa exigir acionabilidade — o que o leitor FAZ com a info de que Aetherflux levantou $2B?",
                alternativeConsidered:
                  "Remover funding rounds completamente do escopo. Descartado: funding round de magnitude excepcional ($10B+, OpenAI/Anthropic) ou que revela shift de estratégia tem valor editorial.",
                change: {
                  type: "Prompt: refinar anti-signal existente",
                  prompt: `ANTES:
→ Funding round sem ângulo AI/tech específico

DEPOIS:
→ Funding round (mesmo de empresa de AI): descarte a menos que o título revele informação acionável para o leitor — nova feature, novo produto, shift de estratégia. "Empresa X levanta $Y" sozinho é noise. Exceção: magnitude excepcional (>$5B) ou player de referência (OpenAI, Anthropic, Google DeepMind).`,
                },
                sideEffects: [
                  "Pode filtrar rounds que teriam ângulo editorial em mercados emergentes. Risco aceitável: se o título não comunica o ângulo, o leitor também não vai extrair valor.",
                ],
                tokenImpact: "+~30 tokens (refinamento de anti-signal existente)",
              },
            ].map((fix) => (
              <Card key={fix.id}>
                <div
                  className="cursor-pointer"
                  onClick={() =>
                    setExpandedFix(expandedFix === fix.id ? null : fix.id)
                  }
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Badge color={fix.color}>{fix.severity}</Badge>
                      <Badge color="gray">{fix.id}</Badge>
                      <span className="text-white font-medium">{fix.title}</span>
                    </div>
                    <span className="text-gray-500 text-sm">
                      {expandedFix === fix.id ? "▼" : "▶"}
                    </span>
                  </div>
                  <div className="flex gap-4 text-xs">
                    <span className="text-gray-500">
                      Onde: <span className="text-cyan-400">{fix.where}</span>
                    </span>
                    <span className="text-gray-500">
                      Token cost: <span className="text-amber-400">{fix.tokenImpact}</span>
                    </span>
                  </div>
                </div>

                {expandedFix === fix.id && (
                  <div className="mt-4 space-y-4 border-t border-gray-800 pt-4">
                    <div>
                      <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">
                        Rationale
                      </div>
                      <div className="text-gray-300 text-sm">{fix.rationale}</div>
                    </div>

                    <div>
                      <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">
                        Alternativa considerada e descartada
                      </div>
                      <div className="text-gray-400 text-sm italic">
                        {fix.alternativeConsidered}
                      </div>
                    </div>

                    <div>
                      <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">
                        Mudança no prompt
                      </div>
                      <pre className="bg-gray-800 rounded-lg p-4 text-sm text-emerald-300 whitespace-pre-wrap font-mono overflow-x-auto">
                        {fix.change.prompt}
                      </pre>
                    </div>

                    {fix.change.fewShot && (
                      <div>
                        <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">
                          Few-shot adicionado
                        </div>
                        <pre className="bg-gray-800 rounded-lg p-4 text-sm text-amber-300 whitespace-pre-wrap font-mono overflow-x-auto">
                          {fix.change.fewShot}
                        </pre>
                      </div>
                    )}

                    {fix.change.code && (
                      <div>
                        <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">
                          Mudança no código
                        </div>
                        <pre className="bg-gray-800 rounded-lg p-4 text-sm text-blue-300 whitespace-pre-wrap font-mono overflow-x-auto">
                          {fix.change.code}
                        </pre>
                      </div>
                    )}

                    <div>
                      <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">
                        Side effects & mitigações
                      </div>
                      <div className="space-y-1">
                        {fix.sideEffects.map((se, i) => (
                          <div key={i} className="text-gray-400 text-sm flex gap-2">
                            <span className="text-amber-400 flex-shrink-0">⚠</span>
                            {se}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}

        {/* ═══ ORDEM & RISCOS ═══ */}
        {tab === "order" && (
          <div className="space-y-6">
            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                Ordem de implementação
              </h2>
              <p className="text-gray-400 text-sm mb-6">
                Ordenado por: impacto editorial × risco de side effect.
                Implementar e validar em sequência — cada fix é um commit separado.
              </p>

              <div className="space-y-4">
                {[
                  {
                    order: 1,
                    fix: "FIX-B",
                    title: "Singularidade do main_find",
                    reason: "Menor risco de false positive. Regra clara e objetiva ('UM evento'). Resolve metade do P0.",
                    effort: "Baixo",
                    risk: "Baixo",
                  },
                  {
                    order: 2,
                    fix: "FIX-A",
                    title: "Freshness Gate",
                    reason: "Maior impacto editorial. Depende de world knowledge do modelo — mais subjetivo, mas a exceção 'informação nova' mitiga false positives.",
                    effort: "Médio",
                    risk: "Médio",
                  },
                  {
                    order: 3,
                    fix: "FIX-C",
                    title: "Correspondent intro",
                    reason: "Format-only, zero risco editorial. Implementar depois de A+B pra validar se o intro melhora naturalmente.",
                    effort: "Baixo",
                    risk: "Nenhum",
                  },
                  {
                    order: 4,
                    fix: "FIX-D",
                    title: "Funding filter",
                    reason: "P2, menor urgência. Refinamento de anti-signal existente. Pode esperar dry run pós A+B+C.",
                    effort: "Baixo",
                    risk: "Baixo",
                  },
                ].map((item) => (
                  <div
                    key={item.order}
                    className="flex items-start gap-4 bg-gray-800 rounded-lg p-4"
                  >
                    <div className="w-8 h-8 rounded-full bg-red-500 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
                      {item.order}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge color="gray">{item.fix}</Badge>
                        <span className="text-white text-sm font-medium">
                          {item.title}
                        </span>
                      </div>
                      <div className="text-gray-400 text-sm">{item.reason}</div>
                      <div className="flex gap-4 mt-2 text-xs">
                        <span className="text-gray-500">
                          Effort: <span className="text-emerald-400">{item.effort}</span>
                        </span>
                        <span className="text-gray-500">
                          Risco:{" "}
                          <span
                            className={
                              item.risk === "Nenhum"
                                ? "text-emerald-400"
                                : item.risk === "Baixo"
                                ? "text-blue-400"
                                : "text-amber-400"
                            }
                          >
                            {item.risk}
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                Token budget analysis
              </h2>
              <p className="text-gray-400 text-sm mb-4">
                Cada token adicionado ao prompt é custo recorrente em todas as
                edições. Precisa justificar.
              </p>
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">FIX-A (anti-signal + 2 few-shots)</span>
                    <span className="text-amber-400 font-mono">+~120 tokens</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">FIX-B (regra STEP 4)</span>
                    <span className="text-emerald-400 font-mono">+~40 tokens</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">FIX-C (instrução formato)</span>
                    <span className="text-emerald-400 font-mono">+~60 tokens</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">FIX-D (refinar anti-signal)</span>
                    <span className="text-emerald-400 font-mono">+~30 tokens</span>
                  </div>
                  <div className="border-t border-gray-700 pt-3 flex justify-between font-medium">
                    <span className="text-white">Total incremental</span>
                    <span className="text-amber-400 font-mono">+~250 tokens</span>
                  </div>
                  <div className="text-gray-500 text-xs mt-2">
                    Contexto: prompt atual ~2800 tokens + 40 items (~4000 tokens) = ~6800 input.
                    +250 = +3.7%. Dentro do budget.
                  </div>
                </div>
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                Risco estatístico: contração do pool
              </h2>
              <p className="text-gray-400 text-sm mb-4">
                Cada anti-signal adicionado reduz o pool de candidatos. Se formos
                muito agressivos, a AYA pode não ter items suficientes pra preencher
                a newsletter.
              </p>
              <div className="bg-gray-800 rounded-lg p-4 space-y-3 text-sm">
                <div className="text-gray-300">
                  <span className="text-white font-medium">Baseline:</span> 40 items
                  chegam ao LLM → ~20-25 passam no AI Gate → ~10-15 passam nos
                  critérios → 6-8 selecionados (1 main + 3-5 QF + 1-2 radar)
                </div>
                <div className="text-gray-300">
                  <span className="text-white font-medium">Com FIX-A:</span> rehashed
                  news remove ~2-5 items do pool (estimativa conservadora). Pool
                  pós-filtro: ~8-13. Ainda confortável.
                </div>
                <div className="text-gray-300">
                  <span className="text-white font-medium">Com FIX-D:</span> funding
                  rounds remove ~1-2 items. Impacto mínimo.
                </div>
                <div className="text-amber-400 mt-2">
                  Cenário worst case: dia fraco (poucas notícias novas) + filtros
                  agressivos = pool de ~6-7 items. Suficiente pro mínimo (1 main +
                  3 QF), mas sem margem pra radar. Risco aceitável — radar é
                  optional by design.
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* ═══ VALIDAÇÃO ═══ */}
        {tab === "validation" && (
          <div className="space-y-6">
            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                Plano de validação
              </h2>
              <p className="text-gray-400 text-sm mb-6">
                Cada fix precisa de validation criteria claros antes de declarar
                sucesso. O output do dry run é o test case.
              </p>

              <div className="space-y-4">
                {[
                  {
                    fix: "FIX-A",
                    criteria: [
                      "Main find NÃO deve ser sobre evento que a Isis já conhece de dias anteriores",
                      "Se aparecer 'Sora' no output, deve ser com informação nova (ex: refund policy)",
                      "Reasoning deve listar títulos rejeitados com '(rehashed)' como motivo",
                      "Follow-ups com info nova devem PASSAR (não filtrar legítimos)",
                    ],
                    testCase:
                      "Se o TechCrunch postar 'OpenAI shuts down Sora' hoje, deve ser descartado. Se postar 'Sora users lose credits after shutdown', deve passar.",
                  },
                  {
                    fix: "FIX-B",
                    criteria: [
                      "Main find deve ser sobre UM evento específico, nunca roundup",
                      "Título do main_find não deve conter ';' separando tópicos não-relacionados",
                      "Pre-filter log deve mostrar [COMPOUND] pra títulos flaggados",
                    ],
                    testCase:
                      "Se TechCrunch postar vídeo 'X; Y; Z', o item deve ser flaggado no pre-filter e a AYA não deve usá-lo como main_find.",
                  },
                  {
                    fix: "FIX-C",
                    criteria: [
                      "Primeira frase do intro deve mencionar o tema do main_find",
                      "Intro NÃO deve conter frases genéricas tipo 'o dia trouxe novidades'",
                      "Intro deve ser specific enough pra distinguir de qualquer outro dia",
                    ],
                    testCase:
                      'Se main_find é sobre Meta lançando Llama 4, intro deve começar com algo como "Hoje o destaque é o Llama 4..."',
                  },
                  {
                    fix: "FIX-D",
                    criteria: [
                      "Funding rounds genéricos ('X levanta $Y') devem ser descartados",
                      "Funding rounds com feature nova ou shift estratégico devem PASSAR",
                      "Reasoning deve listar funding rounds descartados com motivo",
                    ],
                    testCase:
                      '"Aetherflux raises $2B Series B" deve ser descartado. "OpenAI closes $10B round to fund AGI research lab" pode passar.',
                  },
                ].map((v, i) => (
                  <div key={i} className="bg-gray-800 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Badge color="purple">{v.fix}</Badge>
                      <span className="text-white text-sm font-medium">
                        Validation criteria
                      </span>
                    </div>
                    <div className="space-y-1 mb-3">
                      {v.criteria.map((c, j) => (
                        <div key={j} className="text-gray-300 text-sm flex gap-2">
                          <span className="text-emerald-400 flex-shrink-0">✓</span>
                          {c}
                        </div>
                      ))}
                    </div>
                    <div className="bg-gray-900 rounded px-3 py-2 text-sm">
                      <span className="text-gray-500">Test case: </span>
                      <span className="text-cyan-300">{v.testCase}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                Cadência de deploy
              </h2>
              <div className="space-y-3">
                {[
                  {
                    step: "1",
                    action: "Implementar FIX-B + FIX-A no prompt",
                    validation: "Dry run → checar main_find singularity + freshness",
                  },
                  {
                    step: "2",
                    action: "Implementar FIX-C (intro) + FIX-D (funding)",
                    validation: "Dry run → checar intro references main_find + funding filtered",
                  },
                  {
                    step: "3",
                    action: "Rodar 3 dry runs consecutivos",
                    validation:
                      "Consistência: os 4 critérios devem passar em 3/3 runs. Se falhar em 1, investigar edge case.",
                  },
                  {
                    step: "4",
                    action: "Deploy pra produção + monitor primeira edição real",
                    validation: "Isis faz review editorial da edição + registra feedback",
                  },
                ].map((s) => (
                  <div
                    key={s.step}
                    className="flex items-start gap-3 bg-gray-800 rounded-lg p-3"
                  >
                    <div className="w-6 h-6 rounded-full bg-red-500 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">
                      {s.step}
                    </div>
                    <div>
                      <div className="text-white text-sm font-medium">{s.action}</div>
                      <div className="text-gray-400 text-sm">{s.validation}</div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        <div className="mt-8 text-center text-gray-600 text-xs">
          Prompt Engineering Fix Plan — Daily Scout v5.3 — 27/03/2026
        </div>
      </div>
    </div>
  );
};

export default PromptFixPlan;
