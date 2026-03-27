import { useState } from "react";

const GeographicDiversity = () => {
  const [view, setView] = useState("map");

  const currentSources = [
    { name: "Reddit", region: "US", type: "Community", hasAI: "mixed" },
    { name: "HackerNews", region: "US", type: "Community", hasAI: "mixed" },
    { name: "TechCrunch", region: "US", type: "Media", hasAI: "mixed" },
    { name: "Lobsters", region: "US", type: "Community", hasAI: "low" },
  ];

  const proposedSources = [
    // AI Labs (from previous analysis)
    {
      name: "Anthropic Blog",
      region: "US",
      type: "Primary",
      hasAI: "high",
      phase: 1,
      status: "approved",
    },
    {
      name: "OpenAI Blog",
      region: "US",
      type: "Primary",
      hasAI: "high",
      phase: 1,
      status: "approved",
    },
    {
      name: "Google DeepMind",
      region: "US/UK",
      type: "Primary",
      hasAI: "high",
      phase: 1,
      status: "approved",
    },
    // New geographic sources
    {
      name: "South China Morning Post (Tech)",
      region: "China/HK",
      type: "Media",
      hasAI: "high",
      rss: "scmp.com/rss/36/feed/",
      frequency: "5-10x/dia",
      effort: "Baixo",
      phase: 1,
      status: "new",
      why: "Melhor fonte em inglês sobre tech chinesa. Cobre DeepSeek, Baidu, Alibaba, Tencent, ByteDance. Feed RSS oficial. Alta frequência mas o pre_filter resolve.",
      signalExamples: "Llama downloads na China, AI price wars, semiconductor bans impact, DeepSeek updates",
    },
    {
      name: "TechNode",
      region: "China",
      type: "Media",
      hasAI: "high",
      rss: "technode.com/feed/",
      frequency: "3-5x/dia",
      effort: "Baixo",
      phase: 1,
      status: "new",
      why: "Media baseada em Beijing focada em startups e tech chinesa. Fundada em 2007. Cobre o que o SCMP não cobre: startups menores, funding rounds chineses, adoção de AI na China. Feed RSS nativo.",
      signalExamples: "Moonshot AI, Zhipu AI, chinese enterprise AI, regulatory moves MIIT",
    },
    {
      name: "Rest of World",
      region: "Global South",
      type: "Media",
      hasAI: "medium",
      rss: "restofworld.org/feed/",
      frequency: "3-5x/dia",
      effort: "Baixo",
      phase: 1,
      status: "new",
      why: "Cobre tech em mercados emergentes: África, SEA, Latam, Índia, Oriente Médio. Perspectiva única que nenhuma outra fonte dá. Feed RSS provável (padrão WordPress).",
      signalExamples: "AI adoption in India, Chinese tech expansion in Africa, gig economy + AI, regulation in Global South",
    },
    {
      name: "DIGITIMES Asia",
      region: "Taiwan",
      type: "Media",
      hasAI: "medium",
      rss: "digitimes.com/rss/",
      frequency: "10+/dia",
      effort: "Baixo",
      phase: 2,
      status: "new",
      why: "Supply chain de semicondutores, TSMC, hardware AI. Perspectiva Taiwan/manufacturing. Volume muito alto — precisa de filtro agressivo.",
      signalExamples: "TSMC capacity, AI chip demand, Nvidia supply chain, SEMICON events",
    },
    {
      name: "EU AI Act Newsletter",
      region: "Europa",
      type: "Specialist",
      hasAI: "high",
      rss: "artificialintelligenceact.substack.com/feed",
      frequency: "1-2x/semana",
      effort: "Baixo",
      phase: 2,
      status: "new",
      why: "Tracking especializado da regulação AI europeia. Relevante porque EU AI Act afeta toda empresa de AI global. Volume baixo e altamente focado.",
      signalExamples: "AI Act enforcement dates, compliance requirements, fines, prohibited practices",
    },
    {
      name: "Pandaily",
      region: "China",
      type: "Media",
      hasAI: "medium",
      rss: "pandaily.com/feed/",
      frequency: "2-3x/dia",
      effort: "Baixo",
      phase: 2,
      status: "new",
      why: "Beijing-based, cobre startups chinesas. Complementar ao TechNode. Menor mas mais focada em early-stage.",
      signalExamples: "Chinese AI startups, funding rounds, govt policy, tech ecosystem Beijing/Shenzhen",
    },
  ];

  const regions = [
    {
      name: "Estados Unidos",
      flag: "US",
      color: "blue",
      current: 4,
      proposed: 6,
      sources: ["Reddit", "HackerNews", "TechCrunch", "Lobsters", "Anthropic*", "OpenAI*"],
      blind: false,
    },
    {
      name: "China & Hong Kong",
      flag: "CN",
      color: "red",
      current: 0,
      proposed: 2,
      sources: ["SCMP Tech*", "TechNode*"],
      blind: true,
    },
    {
      name: "Reino Unido",
      flag: "UK",
      color: "blue",
      current: 0,
      proposed: 1,
      sources: ["Google DeepMind*"],
      blind: false,
      note: "DeepMind é UK-based",
    },
    {
      name: "Global South",
      flag: "GS",
      color: "emerald",
      current: 0,
      proposed: 1,
      sources: ["Rest of World*"],
      blind: true,
    },
    {
      name: "Taiwan",
      flag: "TW",
      color: "amber",
      current: 0,
      proposed: 1,
      sources: ["DIGITIMES Asia*"],
      blind: true,
      note: "Fase 2",
    },
    {
      name: "Europa (regulação)",
      flag: "EU",
      color: "violet",
      current: 0,
      proposed: 1,
      sources: ["EU AI Act Newsletter*"],
      blind: true,
      note: "Fase 2",
    },
  ];

  const colorMap = {
    blue: { bg: "bg-blue-950", border: "border-blue-800", text: "text-blue-400", dot: "bg-blue-400" },
    red: { bg: "bg-red-950", border: "border-red-800", text: "text-red-400", dot: "bg-red-400" },
    emerald: { bg: "bg-emerald-950", border: "border-emerald-800", text: "text-emerald-400", dot: "bg-emerald-400" },
    amber: { bg: "bg-amber-950", border: "border-amber-800", text: "text-amber-400", dot: "bg-amber-400" },
    violet: { bg: "bg-violet-950", border: "border-violet-800", text: "text-violet-400", dot: "bg-violet-400" },
  };

  const phase1New = proposedSources.filter((s) => s.phase === 1 && s.status === "new");
  const phase2New = proposedSources.filter((s) => s.phase === 2 && s.status === "new");

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 font-sans">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-cyan-400 text-xs font-mono uppercase tracking-widest">
              Daily Scout — Geographic Diversity Audit
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            De US-only para cobertura global
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Mapeamento de blind spots geográficos e recomendação de novas sources
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-900 rounded-lg p-1 w-fit">
          {[
            { id: "map", label: "Mapa" },
            { id: "sources", label: "Novas Sources" },
            { id: "plan", label: "Plano" },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setView(t.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                view === t.id ? "bg-cyan-500 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Map View */}
        {view === "map" && (
          <div className="space-y-6">
            {/* Blind spot alert */}
            <div className="bg-red-950 border border-red-800 rounded-xl p-5">
              <div className="text-red-400 font-semibold mb-2">Diagnóstico: 100% das sources são US-based</div>
              <div className="text-gray-400 text-sm">
                Hoje o Daily Scout enxerga AI pelo retrovisor americano. Reddit, HackerNews, TechCrunch, Lobsters
                — tudo é Silicon Valley perspective. A China representa ~15% do mercado global de AI generativa
                (700M+ downloads do Qwen no Hugging Face), a Europa está regulando AI com o AI Act mais agressivo
                do mundo, e o Global South está adotando AI de formas que o Vale não vê. Nenhuma dessas perspectivas
                chega no Daily Scout hoje.
              </div>
            </div>

            {/* Region cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {regions.map((r, i) => {
                const c = colorMap[r.color];
                return (
                  <div key={i} className={`${c.bg} border ${c.border} rounded-xl p-5`}>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className={`w-3 h-3 rounded-full ${c.dot}`} />
                        <span className="text-white font-semibold">{r.name}</span>
                      </div>
                      {r.blind && (
                        <span className="text-xs bg-red-900 text-red-300 px-2 py-0.5 rounded">
                          BLIND SPOT
                        </span>
                      )}
                    </div>
                    <div className="flex gap-4 mb-3">
                      <div>
                        <div className="text-xs text-gray-500">Hoje</div>
                        <div className={`text-2xl font-bold ${r.current === 0 ? "text-red-400" : c.text}`}>
                          {r.current}
                        </div>
                      </div>
                      <div className="text-gray-600 self-center">→</div>
                      <div>
                        <div className="text-xs text-gray-500">Proposto</div>
                        <div className={`text-2xl font-bold ${c.text}`}>{r.proposed}</div>
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {r.sources.map((s, j) => (
                        <span
                          key={j}
                          className={`text-xs px-2 py-0.5 rounded ${
                            s.includes("*")
                              ? `${c.bg} ${c.text} border ${c.border}`
                              : "bg-gray-800 text-gray-400"
                          }`}
                        >
                          {s.replace("*", "")}
                          {s.includes("*") && " ✦"}
                        </span>
                      ))}
                    </div>
                    {r.note && <div className="text-gray-600 text-xs mt-2">{r.note}</div>}
                  </div>
                );
              })}
            </div>

            {/* Summary bar */}
            <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
              <div className="text-gray-500 text-xs uppercase tracking-wider mb-3">
                Distribuição geográfica: antes vs depois
              </div>
              <div className="space-y-3">
                <div>
                  <div className="text-xs text-gray-500 mb-1">Hoje (4 sources)</div>
                  <div className="flex h-6 rounded-full overflow-hidden">
                    <div className="bg-blue-500 w-full flex items-center justify-center text-xs text-white font-bold">
                      US 100%
                    </div>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Proposta Fase 1 (10 sources)</div>
                  <div className="flex h-6 rounded-full overflow-hidden">
                    <div className="bg-blue-500 flex items-center justify-center text-xs text-white font-bold" style={{ width: "60%" }}>
                      US 60%
                    </div>
                    <div className="bg-red-500 flex items-center justify-center text-xs text-white font-bold" style={{ width: "20%" }}>
                      CN 20%
                    </div>
                    <div className="bg-emerald-500 flex items-center justify-center text-xs text-white font-bold" style={{ width: "10%" }}>
                      GS
                    </div>
                    <div className="bg-blue-400 flex items-center justify-center text-xs text-white font-bold" style={{ width: "10%" }}>
                      UK
                    </div>
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Proposta completa — Fase 1+2 (13 sources)</div>
                  <div className="flex h-6 rounded-full overflow-hidden">
                    <div className="bg-blue-500 flex items-center justify-center text-xs text-white font-bold" style={{ width: "46%" }}>
                      US 46%
                    </div>
                    <div className="bg-red-500 flex items-center justify-center text-xs text-white font-bold" style={{ width: "23%" }}>
                      CN 23%
                    </div>
                    <div className="bg-emerald-500 flex items-center justify-center text-xs text-white" style={{ width: "8%" }}>
                    </div>
                    <div className="bg-blue-400 flex items-center justify-center text-xs text-white" style={{ width: "8%" }}>
                    </div>
                    <div className="bg-amber-500 flex items-center justify-center text-xs text-white" style={{ width: "8%" }}>
                    </div>
                    <div className="bg-violet-500 flex items-center justify-center text-xs text-white" style={{ width: "7%" }}>
                    </div>
                  </div>
                  <div className="flex gap-3 mt-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" />Global South</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-400" />UK</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500" />Taiwan</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-violet-500" />EU</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Sources Detail */}
        {view === "sources" && (
          <div className="space-y-6">
            <div className="text-gray-400 text-sm mb-2">
              3 novas sources geográficas pra Fase 1 (RSS disponível, esforço baixo):
            </div>

            {phase1New.map((s, i) => (
              <div key={i} className="bg-gray-900 rounded-xl p-5 border border-cyan-800">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <h3 className="text-white font-semibold">{s.name}</h3>
                    <span className="text-xs bg-cyan-500 text-white px-2 py-0.5 rounded">
                      Fase 1
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      s.region.includes("China") ? "bg-red-900 text-red-300" :
                      s.region === "Global South" ? "bg-emerald-900 text-emerald-300" :
                      "bg-amber-900 text-amber-300"
                    }`}>
                      {s.region}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="bg-gray-800 rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">RSS Feed</div>
                    <div className="text-sm text-cyan-400 font-mono break-all">{s.rss}</div>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Frequência</div>
                    <div className="text-sm text-gray-300">{s.frequency}</div>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-3">
                    <div className="text-xs text-gray-500 mb-1">Esforço</div>
                    <div className="text-sm text-emerald-400">{s.effort}</div>
                  </div>
                </div>

                <div className="text-gray-400 text-sm mb-3">{s.why}</div>

                <div className="bg-gray-800 rounded-lg p-3">
                  <div className="text-xs text-gray-500 mb-1">Exemplos de signal</div>
                  <div className="text-gray-300 text-sm">{s.signalExamples}</div>
                </div>
              </div>
            ))}

            <div className="border-t border-gray-800 pt-6">
              <div className="text-gray-500 text-sm mb-4">
                3 sources adicionais pra Fase 2 (monitorar antes de incluir):
              </div>
              {phase2New.map((s, i) => (
                <div key={i} className="bg-gray-900 rounded-lg p-4 border border-gray-800 mb-3">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-white font-medium text-sm">{s.name}</span>
                    <span className="text-xs bg-gray-700 text-gray-300 px-2 py-0.5 rounded">Fase 2</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      s.region === "Taiwan" ? "bg-amber-900 text-amber-300" :
                      s.region === "Europa" ? "bg-violet-900 text-violet-300" :
                      "bg-red-900 text-red-300"
                    }`}>{s.region}</span>
                  </div>
                  <div className="text-gray-500 text-xs">{s.why}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Plan View */}
        {view === "plan" && (
          <div className="space-y-6">
            <div className="bg-gray-900 rounded-xl p-6 border border-emerald-800">
              <div className="flex items-center gap-2 mb-4">
                <span className="bg-emerald-500 text-white text-xs font-bold px-2 py-1 rounded">FASE 1</span>
                <span className="text-white font-semibold">6 novas sources (AI Labs + Geo)</span>
              </div>
              <div className="text-gray-400 text-sm mb-4">
                Todas usam RSS via feedparser. A implementação é criar 1 source genérica
                (RSSBlogSource) e configurar via sources_config.json.
              </div>

              <div className="bg-gray-800 rounded-lg p-4 mb-4">
                <div className="text-gray-500 text-xs font-mono mb-2">sources_config.json (novas entradas)</div>
                <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono">
{`// --- AI Labs (fontes primárias) ---
"anthropic_blog":  { weight: 1.3, limit: 10 }
"openai_blog":     { weight: 1.3, limit: 10 }
"deepmind_blog":   { weight: 1.0, limit: 10 }

// --- Geographic diversity ---
"scmp_tech":       { weight: 1.1, limit: 15 }
"technode":        { weight: 1.0, limit: 10 }
"rest_of_world":   { weight: 1.0, limit: 10 }`}
                </pre>
              </div>

              <div className="bg-gray-800 rounded-lg p-4 mb-4">
                <div className="text-gray-500 text-xs mb-2">Impacto no pipeline</div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-cyan-400">4 → 10</div>
                    <div className="text-gray-500 text-xs">sources</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-cyan-400">~60</div>
                    <div className="text-gray-500 text-xs">posts/dia extras</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-cyan-400">5</div>
                    <div className="text-gray-500 text-xs">regiões cobertas</div>
                  </div>
                </div>
              </div>

              <div className="bg-amber-950 border border-amber-800 rounded-lg p-4">
                <div className="text-amber-400 text-xs font-bold mb-2">ATENÇÃO: ajuste no pre_filter</div>
                <div className="text-gray-400 text-sm">
                  Com ~60 posts extras/dia, o max_items_to_llm (hoje 30) pode precisar subir pra 40-50.
                  Senão o pre_filter vai cortar posts relevantes antes deles chegarem no Gemini.
                  O max_per_source_pct (0.4) garante que nenhuma fonte domina, mas com 10 sources
                  o cap efetivo por source vira ~12 posts (40% de 30) — pode ser suficiente.
                  Monitorar no dry run.
                </div>
              </div>
            </div>

            <div className="bg-gray-900 rounded-xl p-6 border border-amber-800">
              <div className="flex items-center gap-2 mb-4">
                <span className="bg-amber-500 text-white text-xs font-bold px-2 py-1 rounded">FASE 2</span>
                <span className="text-white font-semibold">Após validar Fase 1 (~1 semana)</span>
              </div>
              <div className="text-gray-400 text-sm">
                Avaliar DIGITIMES Asia (Taiwan/semicondutores), EU AI Act Newsletter (regulação),
                e Pandaily (startups chinesas). Incluir se a Fase 1 mostrar que o pipeline aguenta
                mais volume sem perder qualidade.
              </div>
            </div>

            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <div className="text-white font-semibold mb-3">Por que essas 3 sources geográficas</div>
              <div className="space-y-3">
                <div className="flex gap-3 items-start">
                  <span className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center text-xs text-white font-bold flex-shrink-0">1</span>
                  <div>
                    <div className="text-white text-sm font-medium">SCMP Tech — a lente chinesa que falta</div>
                    <div className="text-gray-500 text-sm">
                      Cobre Alibaba, Baidu, ByteDance, Tencent, DeepSeek, Huawei diariamente em inglês.
                      É o equivalente a TechCrunch mas pro ecossistema chinês. Sem ela, o Daily Scout
                      só vê AI chinesa quando vira notícia no Ocidente — com dias de delay.
                    </div>
                  </div>
                </div>
                <div className="flex gap-3 items-start">
                  <span className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center text-xs text-white font-bold flex-shrink-0">2</span>
                  <div>
                    <div className="text-white text-sm font-medium">TechNode — startups e governo chinês</div>
                    <div className="text-gray-500 text-sm">
                      Complementa SCMP com cobertura mais profunda do ecossistema de startups e regulação
                      do MIIT (Ministério da Indústria e TI). Quando a China regula AI, TechNode cobre primeiro.
                    </div>
                  </div>
                </div>
                <div className="flex gap-3 items-start">
                  <span className="w-6 h-6 rounded-full bg-emerald-500 flex items-center justify-center text-xs text-white font-bold flex-shrink-0">3</span>
                  <div>
                    <div className="text-white text-sm font-medium">Rest of World — o que ninguém mais cobre</div>
                    <div className="text-gray-500 text-sm">
                      Como AI está sendo adotada na Índia, África, Sudeste Asiático, América Latina.
                      Gig economy + AI, infra chinesa na África, regulação indiana. Nenhuma outra fonte
                      do Daily Scout captura essa perspectiva.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GeographicDiversity;
