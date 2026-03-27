import { useState } from "react";

const SourceExpansionTradeoffs = () => {
  const [view, setView] = useState("calibration");

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 font-sans">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-amber-400 text-xs font-mono uppercase tracking-widest">
              Daily Scout — Expansion Trade-offs
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            3 perguntas antes de expandir as sources
          </h1>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-900 rounded-lg p-1 w-fit">
          {[
            { id: "calibration", label: "1. Calibração" },
            { id: "weights", label: "2. Pesos" },
            { id: "cost", label: "3. Custo" },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setView(t.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                view === t.id ? "bg-amber-400 text-gray-950" : "text-gray-400 hover:text-white"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* === TAB 1: Calibration === */}
        {view === "calibration" && (
          <div className="space-y-6">
            <div className="bg-amber-950 border border-amber-800 rounded-xl p-5">
              <div className="text-amber-300 font-semibold mb-2">
                "Precisamos calibrar o prompt pra outros tipos de conteúdo?"
              </div>
              <div className="text-gray-300 text-sm">
                Sim. Blogs oficiais de AI labs e media chinesa têm um viés diferente das fontes
                atuais. Sem calibração, a AYA pode tratar press release como notícia factual.
              </div>
            </div>

            {/* Content type matrix */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h3 className="text-white font-semibold mb-4">Tipos de conteúdo por source</h3>
              <div className="space-y-3">
                {[
                  {
                    type: "Community-curated",
                    sources: "Reddit, HN, Lobsters",
                    bias: "Nenhum — já filtrado por upvotes da comunidade",
                    risk: "Baixo",
                    riskColor: "emerald",
                    action: "Sem mudança necessária",
                  },
                  {
                    type: "Jornalismo tech",
                    sources: "TechCrunch, SCMP, Rest of World",
                    bias: "Leve — clickbait em títulos, mas reportagem verificada",
                    risk: "Baixo",
                    riskColor: "emerald",
                    action: "Sem mudança — regras de tom anti-hype já cobrem",
                  },
                  {
                    type: "Blogs oficiais AI labs",
                    sources: "Anthropic, OpenAI, DeepMind",
                    bias: "Alto — é marketing. Linguagem otimista, benchmarks cherry-picked",
                    risk: "Médio",
                    riskColor: "amber",
                    action: "Precisa de calibração no prompt",
                  },
                  {
                    type: "Media chinesa em inglês",
                    sources: "TechNode",
                    bias: "Moderado — foco no ecossistema chinês, pode sobrerrepresentar",
                    risk: "Baixo-médio",
                    riskColor: "amber",
                    action: "Precisa de calibração de contexto",
                  },
                ].map((row, i) => (
                  <div key={i} className="bg-gray-800 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-medium text-sm">{row.type}</span>
                      <span className={`text-xs px-2 py-0.5 rounded bg-${row.riskColor}-900 text-${row.riskColor}-300`}>
                        Risco: {row.risk}
                      </span>
                    </div>
                    <div className="text-gray-500 text-xs mb-1">Sources: {row.sources}</div>
                    <div className="text-gray-400 text-xs mb-1">Viés: {row.bias}</div>
                    <div className={`text-xs mt-2 ${row.riskColor === "amber" ? "text-amber-400" : "text-gray-500"}`}>
                      → {row.action}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Proposed prompt addition */}
            <div className="bg-gray-900 rounded-xl p-6 border border-amber-800">
              <h3 className="text-white font-semibold mb-4">
                Adição proposta ao CURATION_PROMPT
              </h3>
              <div className="text-gray-400 text-sm mb-4">
                Adicionar entre o STEP 1 (AI Gate) e o STEP 2 (Critérios):
              </div>
              <div className="bg-gray-800 rounded-lg p-4">
                <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">
{`STEP 1.5 — SOURCE BIAS CHECK:
Se a fonte é blog oficial de empresa de AI
(OpenAI, Anthropic, Google, Meta, etc):
→ Trate como ANÚNCIO, não como notícia neutra
→ Use "A [empresa] anunciou..." em vez de
  linguagem que sugira validação independente
→ NÃO repita claims de performance sem
  qualificar: "segundo benchmarks internos"
→ Acionável? Só se o leitor pode TESTAR
  agora (API pública, feature disponível)

Se a fonte é media regional (SCMP, TechNode,
Rest of World):
→ Contextualize a região: "Na China...",
  "No Sudeste Asiático..."
→ Priorize se mostra algo que fontes
  ocidentais NÃO cobriram`}
                </pre>
              </div>

              <div className="mt-4 bg-gray-800 rounded-lg p-4">
                <div className="text-gray-500 text-xs mb-2">Exemplo de calibração (few-shot novo)</div>
                <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">
{`Exemplo 6 — BLOG OFICIAL (source bias):
Input: { "title": "Introducing Claude 4.5:
  Our most capable model yet",
  "source": "Anthropic Blog", "score": 0 }

Output ERRADO: "A Anthropic lançou o Claude
  4.5, seu modelo mais capaz até agora, que
  supera todos os concorrentes em benchmarks."
→ Erro: repetiu claim de marketing sem
  qualificar.

Output CORRETO: "A Anthropic anunciou o
  Claude 4.5 em seu blog oficial. Segundo
  benchmarks internos da empresa, o modelo
  apresenta melhorias em [X]. O modelo está
  disponível via API para testes."
→ Tratou como anúncio, qualificou benchmarks,
  destacou acionabilidade.

Exemplo 7 — SOURCE REGIONAL (contexto geo):
Input: { "title": "Alibaba's Qwen hits 1B
  downloads on Hugging Face",
  "source": "SCMP Tech", "score": 0 }

Output CORRETO: "Segundo o SCMP, o Qwen —
  família de modelos open-source da Alibaba
  Cloud — atingiu 1 bilhão de downloads no
  Hugging Face. Na China, o Qwen é o modelo
  open-source mais usado, competindo
  diretamente com o Llama da Meta no mercado
  global."
→ Contextualizou a região e o player.`}
                </pre>
              </div>
            </div>
          </div>
        )}

        {/* === TAB 2: Weights === */}
        {view === "weights" && (
          <div className="space-y-6">
            <div className="bg-amber-950 border border-amber-800 rounded-xl p-5">
              <div className="text-amber-300 font-semibold mb-2">
                "Preciso calibrar os pesos? Como não perder a essência?"
              </div>
              <div className="text-gray-300 text-sm">
                A essência do Daily Scout são as fontes de comunidade (HN, Reddit) — é o que dá
                o feeling de "o que a galera de tech tá discutindo". Os pesos precisam garantir
                que as novas fontes complementam, não substituem.
              </div>
            </div>

            {/* Current vs Proposed weights */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h3 className="text-white font-semibold mb-4">Pesos: atual vs proposta</h3>

              <div className="space-y-4">
                {[
                  { name: "HackerNews", current: 1.2, proposed: 1.2, role: "Community pulse", note: "Mantém — é o coração editorial" },
                  { name: "Reddit", current: 1.0, proposed: 1.0, role: "Community breadth", note: "Mantém — diversidade de subs" },
                  { name: "TechCrunch", current: 1.1, proposed: 1.1, role: "Jornalismo", note: "Mantém" },
                  { name: "Lobsters", current: 0.9, proposed: 0.9, role: "Dev community", note: "Mantém" },
                  { name: "SCMP Tech", current: null, proposed: 1.1, role: "China lens", note: "Mesmo peso que TC — jornalismo verificado", isNew: true },
                  { name: "TechNode", current: null, proposed: 0.9, role: "China startups", note: "Peso menor — mais nicho", isNew: true },
                  { name: "Rest of World", current: null, proposed: 1.0, role: "Global South", note: "Peso neutro — qualidade alta", isNew: true },
                  { name: "Anthropic Blog", current: null, proposed: 0.8, role: "AI Lab", note: "Peso MENOR que media — é marketing", isNew: true },
                  { name: "OpenAI Blog", current: null, proposed: 0.8, role: "AI Lab", note: "Peso MENOR — mesma razão", isNew: true },
                  { name: "DeepMind Blog", current: null, proposed: 0.7, role: "AI Lab", note: "Mais research, menos acionável", isNew: true },
                ].map((s, i) => (
                  <div key={i} className={`flex items-center gap-4 p-3 rounded-lg ${s.isNew ? "bg-cyan-950 border border-cyan-900" : "bg-gray-800"}`}>
                    <div className="w-32 flex-shrink-0">
                      <div className={`text-sm font-medium ${s.isNew ? "text-cyan-300" : "text-white"}`}>
                        {s.name}
                      </div>
                      <div className="text-xs text-gray-500">{s.role}</div>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        {s.current !== null && (
                          <span className="text-xs text-gray-500 w-8">{s.current}</span>
                        )}
                        {s.current !== null && <span className="text-gray-600">→</span>}
                        <span className={`text-sm font-mono font-bold ${
                          s.proposed >= 1.1 ? "text-emerald-400" :
                          s.proposed >= 0.9 ? "text-gray-300" :
                          "text-amber-400"
                        }`}>
                          {s.proposed}
                        </span>
                        <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              s.proposed >= 1.1 ? "bg-emerald-400" :
                              s.proposed >= 0.9 ? "bg-gray-400" :
                              "bg-amber-400"
                            }`}
                            style={{ width: `${(s.proposed / 1.3) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 w-48 flex-shrink-0">{s.note}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Key insight */}
            <div className="bg-gray-900 rounded-xl p-6 border border-emerald-800">
              <h3 className="text-emerald-400 font-semibold mb-3">Insight: blogs oficiais com peso MENOR, não maior</h3>
              <div className="text-gray-400 text-sm">
                Na análise anterior eu sugeri weight 1.3 pros AI labs. Olhando com mais cuidado: errado.
                Blogs oficiais são marketing — se derem peso alto, a AYA vai priorizar press release
                da Anthropic sobre discussão orgânica no HackerNews. O HN/Reddit é o que dá a "voz da
                comunidade" pro Daily Scout. Os blogs oficiais entram como complemento: garantem que
                anúncios grandes não passem despercebidos, mas nunca devem dominar.
              </div>
              <div className="mt-3 text-gray-500 text-xs">
                Weight 0.8 significa que um post de blog oficial precisa ser muito mais relevante que um
                post de HN (1.2) pra ganhar na pontuação. É exatamente o comportamento desejado: a
                comunidade lidera, os labs complementam.
              </div>
            </div>

            {/* Pre-filter adjustments */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h3 className="text-white font-semibold mb-4">Ajustes no pre_filter</h3>
              <div className="space-y-3">
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white text-sm font-medium">max_items_to_llm</span>
                    <span className="text-gray-500 text-xs">Quantos posts chegam no Gemini</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-red-400 font-mono">30</span>
                    <span className="text-gray-600">→</span>
                    <span className="text-emerald-400 font-mono font-bold">40</span>
                  </div>
                  <div className="text-gray-500 text-xs mt-2">
                    Com 10 sources, 30 posts é apertado. 40 dá espaço pra representar todas as
                    regiões sem cortar ninguém. O custo extra é mínimo (~10 títulos a mais).
                  </div>
                </div>

                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white text-sm font-medium">max_per_source_pct</span>
                    <span className="text-gray-500 text-xs">Cap por source</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-gray-400 font-mono">0.4 (40%)</span>
                    <span className="text-gray-600">→</span>
                    <span className="text-amber-400 font-mono font-bold">0.25 (25%)</span>
                  </div>
                  <div className="text-gray-500 text-xs mt-2">
                    Com 10 sources, 40% permite que 1 source domine com 16 posts de 40.
                    25% (= max 10 posts por source) garante diversidade geográfica forçada.
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* === TAB 3: Cost === */}
        {view === "cost" && (
          <div className="space-y-6">
            <div className="bg-amber-950 border border-amber-800 rounded-xl p-5">
              <div className="text-amber-300 font-semibold mb-2">
                "Mais posts = mais custo?"
              </div>
              <div className="text-gray-300 text-sm">
                Sim, mas o impacto é quase irrelevante. O Gemini Flash é absurdamente barato
                e o pre_filter controla o volume que chega no LLM.
              </div>
            </div>

            {/* Cost calculation */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h3 className="text-white font-semibold mb-4">Conta do guardanapo</h3>

              <div className="space-y-4">
                {/* Current */}
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-gray-500 text-xs uppercase tracking-wider mb-3">Hoje (4 sources, 30 posts pro LLM)</div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div>
                      <div className="text-xs text-gray-500">Prompt (system + user)</div>
                      <div className="text-white font-mono">~4.000 tokens</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">30 posts (títulos + meta)</div>
                      <div className="text-white font-mono">~1.500 tokens</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Output (JSON)</div>
                      <div className="text-white font-mono">~2.000 tokens</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Custo/dia</div>
                      <div className="text-emerald-400 font-mono font-bold">~$0.007</div>
                    </div>
                  </div>
                </div>

                {/* Proposed */}
                <div className="bg-cyan-950 border border-cyan-800 rounded-lg p-4">
                  <div className="text-cyan-400 text-xs uppercase tracking-wider mb-3">Proposta (10 sources, 40 posts pro LLM)</div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div>
                      <div className="text-xs text-gray-500">Prompt (system + user)</div>
                      <div className="text-white font-mono">~4.500 tokens</div>
                      <div className="text-amber-400 text-xs">+500 (source bias check)</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">40 posts (títulos + meta)</div>
                      <div className="text-white font-mono">~2.000 tokens</div>
                      <div className="text-amber-400 text-xs">+500 (10 posts extras)</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Output (JSON)</div>
                      <div className="text-white font-mono">~2.000 tokens</div>
                      <div className="text-gray-500 text-xs">sem mudança</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-500">Custo/dia</div>
                      <div className="text-emerald-400 font-mono font-bold">~$0.009</div>
                      <div className="text-emerald-400 text-xs">+$0.002/dia</div>
                    </div>
                  </div>
                </div>

                {/* Monthly */}
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-gray-500 text-xs uppercase tracking-wider mb-3">Custo mensal</div>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-gray-400">$0.21</div>
                      <div className="text-gray-500 text-xs">Hoje/mês</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-cyan-400">$0.27</div>
                      <div className="text-gray-500 text-xs">Proposta/mês</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-emerald-400">+$0.06</div>
                      <div className="text-gray-500 text-xs">Diferença/mês</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Explanation */}
            <div className="bg-gray-900 rounded-xl p-6 border border-emerald-800">
              <h3 className="text-emerald-400 font-semibold mb-3">Por que o custo é irrelevante</h3>
              <div className="text-gray-400 text-sm space-y-3">
                <p>
                  O Gemini 2.5 Flash cobra $0.30 por milhão de tokens de input e $2.50 por milhão
                  de output. O Daily Scout usa ~6.500 tokens de input e ~2.000 de output por edição.
                  Isso é menos de 1 centavo por dia.
                </p>
                <p>
                  Dobrar o número de sources não dobra o custo — o pre_filter controla quantos posts
                  chegam no Gemini (hoje 30, proposta 40). O aumento real é de ~1.000 tokens de input
                  por dia, que custa $0.0003. Literalmente frações de centavo.
                </p>
                <p>
                  O custo real é operacional, não financeiro: manter scrapers, lidar com feeds que
                  quebram, monitorar qualidade. Mas como todas as sources Fase 1 usam RSS padrão
                  via feedparser, o overhead é mínimo.
                </p>
              </div>
            </div>

            {/* Free tier reminder */}
            <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
              <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">Referência: free tier do Gemini API</div>
              <div className="text-gray-400 text-sm">
                O Gemini Flash tem free tier generoso (15 RPM, 1M tokens/dia). O Daily Scout usa
                1 request por dia com ~8.500 tokens. Você está usando menos de 1% da cota gratuita.
                Mesmo com 10 sources, continua no free tier sem problemas.
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SourceExpansionTradeoffs;
