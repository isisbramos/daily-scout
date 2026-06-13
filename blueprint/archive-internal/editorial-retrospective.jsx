import { useState } from "react";

const PHASES = [
  { id: "timeline", label: "Timeline" },
  { id: "v4", label: "v4 Editorial" },
  { id: "v5", label: "v5.0 Scale" },
  { id: "v52", label: "v5.2 Balance" },
  { id: "evolution", label: "Evolution Table" },
  { id: "learnings", label: "Learnings" },
];

const Badge = ({ children, color = "gray" }) => {
  const colors = {
    amber: "bg-amber-900 text-amber-300 border-amber-700",
    emerald: "bg-emerald-900 text-emerald-300 border-emerald-700",
    red: "bg-red-900 text-red-300 border-red-700",
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

const SectionNum = ({ n }) => (
  <span className="text-amber-400 font-mono font-bold mr-2">{String(n).padStart(2, "0")}</span>
);

const EditorialRetrospective = () => {
  const [tab, setTab] = useState("timeline");

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 font-sans">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-amber-400 text-xs font-mono uppercase tracking-widest">
              Daily Scout — Editorial Retrospective
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            Journey v4 → v5.2: De prompt genérico a pipeline editorial completo
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            48h de evolução — 26-27 março 2026
          </p>
        </div>

        {/* Tabs */}
        <div className="flex flex-wrap gap-1 mb-6 bg-gray-900 rounded-lg p-1 w-fit">
          {PHASES.map((p) => (
            <button
              key={p.id}
              onClick={() => setTab(p.id)}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-all ${
                tab === p.id
                  ? "bg-amber-400 text-gray-950"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* ═══ TIMELINE ═══ */}
        {tab === "timeline" && (
          <div className="space-y-4">
            <Card>
              <h2 className="text-lg font-semibold text-white mb-6">
                48h de evolução editorial
              </h2>
              <div className="relative">
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-800" />
                {[
                  {
                    time: "26/03 manhã",
                    label: "Edição #001",
                    desc: "Prediction markets como main find. Netflix como quick find. AYA selecionou por tração, não por relevância.",
                    color: "red",
                    version: null,
                  },
                  {
                    time: "26/03 tarde",
                    label: "Discovery editorial",
                    desc: "3 rodadas de entrevista estruturada revelam: AI como lente, tração é context não criteria, so what test.",
                    color: "amber",
                    version: "v4",
                  },
                  {
                    time: "26/03 noite",
                    label: "Prompt audit",
                    desc: "Score 5.6/10 — P0: few-shots desalinhados, P1: conflito system↔user. Fix aplicado → 8.8/10.",
                    color: "amber",
                    version: "v4",
                  },
                  {
                    time: "27/03 manhã",
                    label: "Source expansion",
                    desc: "4→10 sources. rss_generic.py, z-score normalization, exponential decay, wild card zone, 10 few-shots.",
                    color: "blue",
                    version: "v5.0",
                  },
                  {
                    time: "27/03 tarde",
                    label: "Dry run #38",
                    desc: "266 items, 10 sources OK. Feedback: muito China, Reddit morno.",
                    color: "blue",
                    version: "v5.0",
                  },
                  {
                    time: "27/03 noite",
                    label: "Balance & Radar",
                    desc: "Weight rebalance, geographic cap, STEP 4.5 Radar section com early signals.",
                    color: "emerald",
                    version: "v5.2",
                  },
                ].map((evt, i) => (
                  <div key={i} className="relative pl-12 pb-8 last:pb-0">
                    <div className={`absolute left-2.5 w-3 h-3 rounded-full border-2 ${
                      evt.color === "red" ? "bg-red-500 border-red-400" :
                      evt.color === "amber" ? "bg-amber-500 border-amber-400" :
                      evt.color === "blue" ? "bg-blue-500 border-blue-400" :
                      "bg-emerald-500 border-emerald-400"
                    }`} />
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-gray-500 text-xs font-mono">{evt.time}</span>
                      {evt.version && <Badge color={
                        evt.color === "amber" ? "amber" : evt.color === "blue" ? "blue" : "emerald"
                      }>{evt.version}</Badge>}
                    </div>
                    <div className="text-white font-medium text-sm">{evt.label}</div>
                    <div className="text-gray-400 text-sm mt-1">{evt.desc}</div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Key metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Sources", before: "4", after: "10", color: "text-blue-400" },
                { label: "Few-shots", before: "3", after: "10", color: "text-purple-400" },
                { label: "Prompt Score", before: "5.6", after: "8.8", color: "text-emerald-400" },
                { label: "New Sections", before: "0", after: "2", color: "text-amber-400" },
              ].map((m, i) => (
                <Card key={i} className="text-center">
                  <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">{m.label}</div>
                  <div className="flex items-center justify-center gap-2">
                    <span className="text-gray-600 text-lg">{m.before}</span>
                    <span className="text-gray-600">→</span>
                    <span className={`text-2xl font-bold ${m.color}`}>{m.after}</span>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* ═══ V4 EDITORIAL ═══ */}
        {tab === "v4" && (
          <div className="space-y-6">
            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                <SectionNum n={1} />O Problema — Edição #001
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-red-950 border border-red-900 rounded-lg p-4">
                  <div className="text-red-400 text-xs uppercase tracking-wider mb-2">Main find (errado)</div>
                  <div className="text-white font-medium">Prediction Markets — impacto negativo</div>
                  <div className="text-gray-400 text-sm mt-1">539pts HN. Zero ângulo AI. Entrou por tração pura.</div>
                </div>
                <div className="bg-emerald-950 border border-emerald-800 rounded-lg p-4">
                  <div className="text-emerald-400 text-xs uppercase tracking-wider mb-2">Main find (certo)</div>
                  <div className="text-white font-medium">Gemini importa chats de outros chatbots</div>
                  <div className="text-gray-400 text-sm mt-1">Acionável + sinal de mercado + AI-first. Relegado a quick find.</div>
                </div>
              </div>
              <div className="mt-4 bg-gray-800 rounded-lg p-4">
                <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">Root cause</div>
                <div className="text-gray-300 text-sm">
                  Critério "2 de 3: Tração, Impacto, Novidade" — tração alta sozinha garantia entrada. Sem filtro de relevância temática, sem exemplos de descarte.
                </div>
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                <SectionNum n={2} />Discovery Editorial — Entrevista Estruturada
              </h2>
              <div className="space-y-3">
                {[
                  { round: "Rodada 1", topic: "Bom vs Ruim", findings: ["Gemini > Prediction Markets", "Signal: afeta uso + direção mercado + acionável", "Anti-signal: genérico demais"] },
                  { round: "Rodada 2", topic: "Posicionamento", findings: ["Escopo: AI como lente", "Persona: curious professionals", "Tração: sinal, não filtro"] },
                  { round: "Rodada 3", topic: "Edge Cases", findings: ["So what test: 'sabia que agora dá pra...'", "Sem ângulo AI = só se excepcional", "Netflix em QF = incomodou, não deveria entrar"] },
                ].map((r, i) => (
                  <div key={i} className="bg-gray-800 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge color="amber">{r.round}</Badge>
                      <span className="text-white text-sm font-medium">{r.topic}</span>
                    </div>
                    <div className="text-gray-400 text-sm space-y-1">
                      {r.findings.map((f, j) => (
                        <div key={j}>→ {f}</div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                <SectionNum n={3} />Pipeline v4 — 5 Steps
              </h2>
              <div className="space-y-2">
                {[
                  { step: "STEP 1", name: "AI GATE", desc: "Tem conexão com AI? Sim → continua. Não → só se excepcional.", color: "red" },
                  { step: "STEP 2", name: "CRITÉRIOS", desc: "2 de 3: Acionável / Sinal de mercado / Afeta workflows", color: "emerald" },
                  { step: "STEP 3", name: "ANTI-SIGNAL", desc: "Preço consumer / Funding genérico / Crypto sem AI / UI cosmético", color: "red" },
                  { step: "STEP 4", name: "RANKING", desc: "main_find = mais acionável. Tração = tiebreaker, nunca critério.", color: "amber" },
                  { step: "STEP 5", name: "TESTE FINAL", desc: "'Agora é possível [X]' ou '[Player] está [movendo pra] [Y]'", color: "blue" },
                ].map((s, i) => (
                  <div key={i} className="flex items-start gap-3 bg-gray-800 rounded-lg p-3">
                    <Badge color={s.color}>{s.step}</Badge>
                    <div>
                      <span className="text-white text-sm font-medium">{s.name}</span>
                      <div className="text-gray-400 text-sm">{s.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                <SectionNum n={4} />Prompt Audit — De 5.6 pra 8.8
              </h2>
              <div className="space-y-2">
                {[
                  { id: "P0", title: "Few-shots desalinhados", desc: "Ensinavam TOM mas não SELEÇÃO. Wine/DirectX passaria no antigo mas falharia no novo.", color: "red" },
                  { id: "P1", title: "Conflito system ↔ user", desc: "SYSTEM: 'tech & AI'. CURATION: 'AI como lente'. Modelo sofre conflito nos edge cases.", color: "amber" },
                  { id: "P1", title: "Overlap de critérios", desc: "'Afeta uso de AI' e 'Acionável' têm ~70% overlap. Modelo conta 2 quando é 1.", color: "amber" },
                ].map((bug, i) => (
                  <div key={i} className="flex items-start gap-3 bg-gray-800 rounded-lg p-3">
                    <Badge color={bug.color}>{bug.id}</Badge>
                    <div>
                      <span className="text-white text-sm font-medium">{bug.title}</span>
                      <div className="text-gray-400 text-sm">{bug.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex items-center gap-4">
                <div className="bg-red-950 border border-red-900 rounded-lg px-4 py-2 text-center">
                  <div className="text-red-400 text-xs">Antes</div>
                  <div className="text-white text-xl font-bold">5.6</div>
                </div>
                <div className="text-gray-600 text-2xl">→</div>
                <div className="bg-emerald-950 border border-emerald-800 rounded-lg px-4 py-2 text-center">
                  <div className="text-emerald-400 text-xs">Depois</div>
                  <div className="text-white text-xl font-bold">8.8</div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* ═══ V5.0 SCALE ═══ */}
        {tab === "v5" && (
          <div className="space-y-6">
            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                <SectionNum n={1} />Source Expansion: 4 → 10
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-gray-500 text-xs uppercase tracking-wider mb-3">Community (original)</div>
                  {["Reddit", "HackerNews", "TechCrunch", "Lobsters"].map((s) => (
                    <div key={s} className="text-gray-300 text-sm py-1 flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-gray-600" />
                      {s}
                    </div>
                  ))}
                </div>
                <div className="bg-blue-950 border border-blue-900 rounded-lg p-4">
                  <div className="text-blue-400 text-xs uppercase tracking-wider mb-3">AI Lab Blogs (v5 new)</div>
                  {[
                    { name: "Anthropic Blog", w: 0.8 },
                    { name: "OpenAI Blog", w: 0.8 },
                    { name: "DeepMind Blog", w: 0.7 },
                  ].map((s) => (
                    <div key={s.name} className="text-gray-300 text-sm py-1 flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                        {s.name}
                      </span>
                      <span className="text-blue-400 text-xs font-mono">w:{s.w}</span>
                    </div>
                  ))}
                  <div className="mt-2 text-blue-400 text-xs">
                    Mitigação: STEP 1.5 Source Bias Check
                  </div>
                </div>
                <div className="bg-cyan-950 border border-cyan-900 rounded-lg p-4">
                  <div className="text-cyan-400 text-xs uppercase tracking-wider mb-3">Geographic (v5 new)</div>
                  {[
                    { name: "SCMP Tech", w: 0.9, region: "asia" },
                    { name: "Rest of World", w: 0.9, region: "global_south" },
                    { name: "TechNode", w: 0.8, region: "asia" },
                  ].map((s) => (
                    <div key={s.name} className="text-gray-300 text-sm py-1 flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
                        {s.name}
                      </span>
                      <span className="text-cyan-400 text-xs font-mono">{s.region}</span>
                    </div>
                  ))}
                </div>
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                <SectionNum n={2} />Pre-Filter Rewrite
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  {
                    title: "Z-Score Normalization",
                    desc: "HN scores ~500, RSS blogs = 0. Sigmoid normaliza engagement pra [0,1] comparável entre sources.",
                    icon: "📊",
                  },
                  {
                    title: "Exponential Recency Decay",
                    desc: "e^(-age/8) — half-life ~5.5h. Modela ciclo real de notícias vs cutoff hard de 24h.",
                    icon: "⏱",
                  },
                  {
                    title: "Cross-Source Signal",
                    desc: "Dedup marca duplicatas com cross_source_count em vez de deletar. AYA sabe quando tema é multi-source.",
                    icon: "🔗",
                  },
                  {
                    title: "Wild Card Zone",
                    desc: "5 dos 40 slots são aleatórios do pool descartado. Exploration vs exploitation pra encontrar gems.",
                    icon: "🎲",
                  },
                ].map((f, i) => (
                  <div key={i} className="bg-gray-800 rounded-lg p-4">
                    <div className="text-lg mb-2">{f.icon}</div>
                    <div className="text-white text-sm font-medium mb-1">{f.title}</div>
                    <div className="text-gray-400 text-sm">{f.desc}</div>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                <SectionNum n={3} />Prompt Engineering v5
              </h2>
              <div className="space-y-2">
                {[
                  { tag: "Few-shots", desc: "3 → 10 exemplos (seleção + descarte + tom + geographic + cross-source)", color: "purple" },
                  { tag: "STEP 1.5", desc: "Source Bias Check generalizado pra qualquer blog corporativo", color: "blue" },
                  { tag: "STEP 5", desc: "4 templates de completion task (vs 2)", color: "blue" },
                  { tag: "Reasoning", desc: "Schema com ai_gate_passed, rejected_sample, rationale, perspective_check", color: "amber" },
                  { tag: "Shuffle", desc: "Items enviados em ordem aleatória — remove position bias", color: "gray" },
                  { tag: "Context", desc: "AYA recebe total items + source breakdown antes de decidir", color: "gray" },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3 bg-gray-800 rounded-lg p-3">
                    <Badge color={item.color}>{item.tag}</Badge>
                    <span className="text-gray-300 text-sm">{item.desc}</span>
                  </div>
                ))}
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                <SectionNum n={4} />Dry Run #38 — Resultado
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: "Sources", value: "10", sub: "todas operacionais" },
                  { label: "Items coletados", value: "266", sub: "multi-source" },
                  { label: "Após pre-filter", value: "40", sub: "enviados ao Gemini" },
                  { label: "Status", value: "OK", sub: "pipeline sem erros" },
                ].map((m, i) => (
                  <div key={i} className="bg-gray-800 rounded-lg p-4 text-center">
                    <div className="text-gray-500 text-xs uppercase tracking-wider mb-1">{m.label}</div>
                    <div className="text-white text-xl font-bold">{m.value}</div>
                    <div className="text-gray-500 text-xs">{m.sub}</div>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* ═══ V5.2 BALANCE ═══ */}
        {tab === "v52" && (
          <div className="space-y-6">
            <Card>
              <h2 className="text-lg font-semibold text-white mb-2">
                Feedback-driven iteration
              </h2>
              <p className="text-gray-400 text-sm mb-6">
                Dois feedbacks do dry run #38 geraram v5.2 em horas.
              </p>

              <div className="space-y-6">
                {/* Feedback 1 */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Badge color="red">Feedback 1</Badge>
                    <span className="text-white text-sm font-medium">"Muito conteúdo sobre China"</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-gray-800 rounded-lg p-4">
                      <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">Fix: Weight Rebalance</div>
                      <div className="space-y-2 text-sm">
                        {[
                          { source: "SCMP", before: "1.1", after: "0.9" },
                          { source: "Rest of World", before: "1.0", after: "0.9" },
                          { source: "TechNode", before: "0.9", after: "0.8" },
                        ].map((w) => (
                          <div key={w.source} className="flex items-center justify-between">
                            <span className="text-gray-300">{w.source}</span>
                            <span>
                              <span className="text-red-400 font-mono">{w.before}</span>
                              <span className="text-gray-600 mx-1">→</span>
                              <span className="text-emerald-400 font-mono">{w.after}</span>
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <div className="text-gray-500 text-xs uppercase tracking-wider mb-2">Fix: Geographic Cap (STEP 4)</div>
                      <div className="text-gray-300 text-sm space-y-2">
                        <div>→ Campo <code className="text-amber-400">region</code> no sources_config.json</div>
                        <div>→ Max 2 items da mesma região geográfica</div>
                        <div>→ 3+ items asiáticos fortes? Escolhe os 2 melhores.</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Feedback 2 */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Badge color="amber">Feedback 2</Badge>
                    <span className="text-white text-sm font-medium">"Reddit com conteúdo morno em 24h"</span>
                  </div>
                  <div className="bg-amber-950 border border-amber-800 rounded-lg p-4">
                    <div className="text-amber-300 font-medium mb-2">Fix: STEP 4.5 — RADAR (early signals)</div>
                    <div className="text-gray-300 text-sm space-y-2">
                      <div>→ Após main_find + quick_finds, AYA olha items que passaram no AI Gate mas ficaram de fora</div>
                      <div>→ Seleciona 1-2 items com tom "keep an eye": temas emergentes, sinais fracos</div>
                      <div>→ <code className="text-amber-400">RadarItem</code> schema: title, source, why_watch, url</div>
                      <div>→ Template HTML: seção RADAR com accent color <span className="text-amber-400 font-mono">#FBBF24</span></div>
                      <div>→ Se nenhum item justifica radar, lista vazia — NÃO força items fracos</div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            <Card>
              <h2 className="text-lg font-semibold text-white mb-4">
                v5.2 na prática — o que o leitor vê
              </h2>
              <div className="bg-gray-800 rounded-lg p-6 font-mono text-sm">
                <div className="text-emerald-400 mb-4">
                  <div className="text-xs text-gray-500 mb-1">▸ ACHADO DO DIA</div>
                  <div className="text-white">Gemini lança modelo Imagen 4...</div>
                  <div className="text-gray-400 text-xs mt-1">fonte: Anthropic Blog · primary_audience: developers</div>
                </div>
                <div className="text-blue-400 mb-4">
                  <div className="text-xs text-gray-500 mb-1">▸ QUICK FINDS (3-5 items)</div>
                  <div className="text-gray-300 space-y-1">
                    <div>• Item acionável de HackerNews</div>
                    <div>• Item sinal de mercado de TechCrunch</div>
                    <div>• Item perspectiva SCMP <span className="text-cyan-400">[max 2 da mesma região]</span></div>
                  </div>
                </div>
                <div className="text-amber-400">
                  <div className="text-xs text-gray-500 mb-1">▸ RADAR <span className="text-amber-400">(new in v5.2)</span></div>
                  <div className="text-gray-300 space-y-1">
                    <div>• "Discussão sobre X ganhando tração no Reddit — vale acompanhar"</div>
                    <div>• "Sinal fraco: Y pode virar notícia nos próximos dias"</div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* ═══ EVOLUTION TABLE ═══ */}
        {tab === "evolution" && (
          <Card>
            <h2 className="text-lg font-semibold text-white mb-6">
              Evolução técnica comparada
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left text-gray-500 font-medium py-3 pr-4">Aspecto</th>
                    <th className="text-center text-gray-500 font-medium py-3 px-2">
                      <span className="text-red-400">v3</span>
                      <div className="text-xs font-normal">pré-intervenção</div>
                    </th>
                    <th className="text-center text-gray-500 font-medium py-3 px-2">
                      <span className="text-amber-400">v4</span>
                      <div className="text-xs font-normal">editorial</div>
                    </th>
                    <th className="text-center text-gray-500 font-medium py-3 px-2">
                      <span className="text-blue-400">v5.0</span>
                      <div className="text-xs font-normal">scale</div>
                    </th>
                    <th className="text-center text-gray-500 font-medium py-3 px-2">
                      <span className="text-emerald-400">v5.2</span>
                      <div className="text-xs font-normal">balance</div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { aspect: "Sources", v3: "4", v4: "4", v5: "10", v52: "10" },
                    { aspect: "Critério", v3: "Tração/Impacto/Novidade", v4: "AI Gate + 5 steps", v5: "+ bias check", v52: "+ geo cap" },
                    { aspect: "Few-shots", v3: "3 (tom)", v4: "5 (seleção+descarte)", v5: "10 (+geo+cross)", v52: "10" },
                    { aspect: "Pre-filter", v3: "Dedup + recency", v4: "=", v5: "Z-score + decay + wild card", v52: "=" },
                    { aspect: "Observability", v3: "—", v4: "—", v5: "Reasoning schema", v52: "+ Radar" },
                    { aspect: "Geographic", v3: "—", v4: "—", v5: "3 fontes", v52: "+ region cap" },
                    { aspect: "Score", v3: "~5.6", v4: "8.8", v5: "8.8 (+sync)", v52: "=" },
                  ].map((row, i) => (
                    <tr key={i} className="border-b border-gray-800/50">
                      <td className="py-3 pr-4 text-gray-300 font-medium">{row.aspect}</td>
                      <td className="py-3 px-2 text-center text-gray-500">{row.v3}</td>
                      <td className="py-3 px-2 text-center text-amber-400">{row.v4}</td>
                      <td className="py-3 px-2 text-center text-blue-400">{row.v5}</td>
                      <td className="py-3 px-2 text-center text-emerald-400">{row.v52}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* ═══ LEARNINGS ═══ */}
        {tab === "learnings" && (
          <div className="space-y-6">
            {[
              {
                category: "De Produto",
                color: "amber",
                items: [
                  { title: "Discovery por entrevista > definição direta", desc: "Responder perguntas estruturadas extraiu critérios que não saíam escrevendo do zero." },
                  { title: "Prompt é feature", desc: "discovery → spec → audit → test → deploy. Nunca reescrever e deployar direto." },
                  { title: "Feedback loop rápido muda tudo", desc: "Dry run #38 → 2 feedbacks → v5.2 em horas. O ciclo curto é o que importa." },
                  { title: "Scale revela novos problemas", desc: "4→10 sources não é 2.5x mais do mesmo — é complexidade diferente (bias, normalization, geographic balance)." },
                ],
              },
              {
                category: "De Prompt Engineering",
                color: "blue",
                items: [
                  { title: "Exemplos de descarte = exemplos de acerto", desc: "O modelo precisa aprender a fronteira. Sem exemplos de 'isso NÃO entra', a fronteira fica vaga." },
                  { title: "Pipeline sequencial > lista flat", desc: "Steps numerados geram consistência. AI Gate como step 1 elimina noise na raiz." },
                  { title: "Tração é context, não criteria", desc: "Shift conceitual que mudou todo o framework." },
                  { title: "Sync prompt ↔ pipeline é P0", desc: "Schema listava 4 sources enquanto pipeline tinha 10 — bug silencioso." },
                  { title: "Reasoning schema = observability", desc: "Ver o quê E por quê a AYA decidiu mudou a qualidade do debug." },
                ],
              },
              {
                category: "De Operação",
                color: "emerald",
                items: [
                  { title: "Config-driven > hardcoded", desc: "sources_config.json — liga/desliga sources sem deploy." },
                  { title: "Wild card zone = exploration", desc: "5 slots aleatórios do pool descartado — gems que o scoring perdeu." },
                  { title: "Geographic cap no prompt > cap no pre-filter", desc: "AYA tem contexto editorial que scoring heurístico não tem." },
                ],
              },
            ].map((section, i) => (
              <Card key={i}>
                <h2 className="text-lg font-semibold text-white mb-4">
                  <Badge color={section.color}>{section.category}</Badge>
                </h2>
                <div className="space-y-3">
                  {section.items.map((item, j) => (
                    <div key={j} className="flex gap-3 items-start">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5 ${
                        section.color === "amber" ? "bg-amber-400 text-gray-950" :
                        section.color === "blue" ? "bg-blue-400 text-gray-950" :
                        "bg-emerald-400 text-gray-950"
                      }`}>
                        {j + 1}
                      </div>
                      <div>
                        <div className="text-white font-medium text-sm">{item.title}</div>
                        <div className="text-gray-400 text-sm">{item.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-gray-600 text-xs">
          Daily Scout Editorial Retrospective — 27/03/2026
        </div>
      </div>
    </div>
  );
};

export default EditorialRetrospective;
