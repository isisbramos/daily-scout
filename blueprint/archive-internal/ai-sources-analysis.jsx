import { useState } from "react";

const AISourcesAnalysis = () => {
  const [view, setView] = useState("matrix");

  const sources = [
    {
      name: "Anthropic",
      blog: "anthropic.com/news",
      rss: "Community (GitHub)",
      rssUrl: "Olshansk/rss-feeds → feed_anthropic_news.xml",
      official: false,
      frequency: "2-4x/semana",
      signalRatio: "Alto",
      signalColor: "emerald",
      examples: "Lançamento de modelos, research papers, safety updates, product updates",
      effort: "Baixo",
      recommendation: "add",
      notes: "Feed comunitário confiável (Olshansk project). Separa news, engineering, research. Pode usar só o news feed.",
    },
    {
      name: "OpenAI",
      blog: "openai.com/blog",
      rss: "Community (GitHub)",
      rssUrl: "Olshansk/rss-feeds → feed_openai_research.xml",
      official: false,
      frequency: "3-5x/semana",
      signalRatio: "Alto",
      signalColor: "emerald",
      examples: "GPT updates, API changes, pricing, DALL-E, Sora, safety reports",
      effort: "Baixo",
      recommendation: "add",
      notes: "Maior volume entre os labs. Feed comunitário. Postam frequentemente sobre updates de API que são super acionáveis.",
    },
    {
      name: "Google DeepMind",
      blog: "deepmind.google/blog",
      rss: "Oficial",
      rssUrl: "deepmind.com/blog/feed/basic/",
      official: true,
      frequency: "2-3x/semana",
      signalRatio: "Médio",
      signalColor: "amber",
      examples: "Research papers, Gemini updates, AlphaFold, safety research",
      effort: "Baixo",
      recommendation: "add",
      notes: "Mais research-heavy que os outros. Precisa de filtro: só pegar posts que passam no AI Gate + acionabilidade.",
    },
    {
      name: "Meta AI",
      blog: "ai.meta.com/blog",
      rss: "Não encontrado",
      rssUrl: "Sem feed oficial. RSSHub tem request aberto (issue #16938).",
      official: false,
      frequency: "1-3x/semana",
      signalRatio: "Alto",
      signalColor: "emerald",
      examples: "Llama releases, open-source models, research, PyTorch updates",
      effort: "Médio",
      recommendation: "add",
      notes: "Sem RSS nativo. Opções: scraper custom ou usar RSSHub community. Llama updates são altamente acionáveis pro público.",
    },
    {
      name: "Mistral",
      blog: "mistral.ai/news",
      rss: "Não encontrado",
      rssUrl: "Sem feed oficial. Releasebot tem tracking via API.",
      official: false,
      frequency: "1-2x/semana",
      signalRatio: "Alto",
      signalColor: "emerald",
      examples: "Novos modelos (Small, Medium, Large), API updates, pricing",
      effort: "Alto",
      recommendation: "watch",
      notes: "Player importante mas sem RSS. Precisaria de scraper. Volume baixo não justifica o esforço agora.",
    },
    {
      name: "xAI (Grok)",
      blog: "x.ai/news",
      rss: "Community (GitHub)",
      rssUrl: "Olshansk/rss-feeds → feed_xainews.xml",
      official: false,
      frequency: "1-2x/mês",
      signalRatio: "Médio",
      signalColor: "amber",
      examples: "Grok model updates, API launches, company announcements",
      effort: "Baixo",
      recommendation: "watch",
      notes: "Volume muito baixo. Feed existe mas raramente tem conteúdo novo. Melhor pegar via HN/TechCrunch quando virar notícia.",
    },
    {
      name: "DeepSeek",
      blog: "deepseek.ai/blog",
      rss: "Não encontrado",
      rssUrl: "Sem feed. Sem projeto comunitário dedicado.",
      official: false,
      frequency: "1-3x/mês",
      signalRatio: "Alto quando posta",
      signalColor: "amber",
      examples: "Model releases (V3, V4, R1, R2), benchmark results, técnicas novas",
      effort: "Alto",
      recommendation: "watch",
      notes: "Quando posta é bomba (DeepSeek V4 foi top news). Mas frequência é imprevisível. HN/Reddit já captam bem.",
    },
    {
      name: "Perplexity",
      blog: "perplexity.ai/hub",
      rss: "Não encontrado",
      rssUrl: "Sem feed blog. Podcast Discover Daily tem RSS.",
      official: false,
      frequency: "2-3x/semana",
      signalRatio: "Médio",
      signalColor: "amber",
      examples: "Product updates, enterprise features, Sonar API, Discover features",
      effort: "Alto",
      recommendation: "later",
      notes: "Mais product updates que research. Sem RSS nativo. TechCrunch geralmente cobre os anúncios relevantes.",
    },
  ];

  const recMap = {
    add: { label: "Adicionar", bg: "bg-emerald-500", border: "border-emerald-800" },
    watch: { label: "Monitorar", bg: "bg-amber-500", border: "border-amber-800" },
    later: { label: "Depois", bg: "bg-gray-500", border: "border-gray-700" },
  };

  const addSources = sources.filter((s) => s.recommendation === "add");
  const watchSources = sources.filter((s) => s.recommendation !== "add");

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 font-sans">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-cyan-400 text-xs font-mono uppercase tracking-widest">
              Daily Scout — Source Expansion
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            Blogs oficiais de AI companies como source
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Pesquisa de RSS feeds, frequência, e recomendação de inclusão
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-900 rounded-lg p-1 w-fit">
          {[
            { id: "matrix", label: "Matriz" },
            { id: "plan", label: "Plano de Ação" },
            { id: "arch", label: "Arquitetura" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setView(tab.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                view === tab.id
                  ? "bg-cyan-500 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Matrix View */}
        {view === "matrix" && (
          <div className="space-y-4">
            {sources.map((s, i) => (
              <div
                key={i}
                className={`bg-gray-900 rounded-xl p-5 border ${recMap[s.recommendation].border}`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <h3 className="text-white font-semibold">{s.name}</h3>
                    <span
                      className={`text-xs px-2 py-0.5 rounded text-white ${recMap[s.recommendation].bg}`}
                    >
                      {recMap[s.recommendation].label}
                    </span>
                  </div>
                  <span className="text-gray-500 text-xs font-mono">{s.blog}</span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                  <div>
                    <div className="text-xs text-gray-500 mb-1">RSS</div>
                    <div className={`text-sm ${s.official ? "text-emerald-400" : "text-amber-400"}`}>
                      {s.rss}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Frequência</div>
                    <div className="text-sm text-gray-300">{s.frequency}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Signal/Noise</div>
                    <div className={`text-sm text-${s.signalColor}-400`}>{s.signalRatio}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Esforço</div>
                    <div className="text-sm text-gray-300">{s.effort}</div>
                  </div>
                </div>

                <div className="text-gray-400 text-xs mb-2">
                  <span className="text-gray-500">Tipo de conteúdo:</span> {s.examples}
                </div>
                <div className="text-gray-500 text-xs">
                  {s.notes}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Plan View */}
        {view === "plan" && (
          <div className="space-y-6">
            {/* Phase 1 */}
            <div className="bg-gray-900 rounded-xl p-6 border border-emerald-800">
              <div className="flex items-center gap-2 mb-4">
                <span className="bg-emerald-500 text-white text-xs font-bold px-2 py-1 rounded">FASE 1</span>
                <span className="text-white font-semibold">Adicionar agora (esforço baixo)</span>
              </div>

              <div className="space-y-4">
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-emerald-400 font-medium mb-2">Anthropic + OpenAI + Google DeepMind</div>
                  <div className="text-gray-400 text-sm mb-3">
                    Esses 3 têm feeds RSS disponíveis (oficial ou community) e postam com frequência
                    relevante. Podem ser adicionados com zero código novo — a arquitetura de sources
                    do Daily Scout já suporta feeds RSS via feedparser (mesmo padrão do TechCrunch).
                  </div>
                  <div className="text-gray-300 text-sm font-mono bg-gray-900 rounded p-3">
                    <div className="text-gray-500 text-xs mb-2">sources_config.json</div>
{`"anthropic": {
  "enabled": true,
  "weight": 1.3,
  "limit": 10,
  "feeds": {
    "news": "[community-feed-url]"
  }
},
"openai_blog": {
  "enabled": true,
  "weight": 1.3,
  "limit": 10,
  "feeds": {
    "research": "[community-feed-url]"
  }
},
"deepmind": {
  "enabled": true,
  "weight": 1.0,
  "limit": 10,
  "feeds": {
    "blog": "deepmind.com/blog/feed/basic/"
  }
}`}
                  </div>
                </div>

                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-white font-medium mb-2">Decisão: peso dos blogs oficiais</div>
                  <div className="text-gray-400 text-sm">
                    Recomendo weight 1.3 (acima do TechCrunch 1.1) porque são fontes primárias.
                    Mas com um cuidado: blogs oficiais são marketing. O AI Gate + anti-signal do
                    prompt v4 já filtram hype, mas vale monitorar se a AYA começa a priorizar
                    press releases como se fossem notícia.
                  </div>
                </div>

                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-white font-medium mb-2">Implementação</div>
                  <div className="text-gray-400 text-sm">
                    A forma mais simples: criar 1 novo source genérico tipo RSSBlogSource que
                    aceita qualquer URL de feed, reutilizando a lógica do TechCrunch. Registra
                    no sources_config.json e pronto — sem tocar no pipeline.
                  </div>
                </div>
              </div>
            </div>

            {/* Phase 2 */}
            <div className="bg-gray-900 rounded-xl p-6 border border-amber-800">
              <div className="flex items-center gap-2 mb-4">
                <span className="bg-amber-500 text-white text-xs font-bold px-2 py-1 rounded">FASE 2</span>
                <span className="text-white font-semibold">Monitorar (decidir depois)</span>
              </div>

              <div className="bg-gray-800 rounded-lg p-4">
                <div className="text-amber-400 font-medium mb-2">Meta AI + Mistral + DeepSeek + xAI</div>
                <div className="text-gray-400 text-sm">
                  Sem RSS nativo. Opções pra Fase 2: scraper custom com Beautiful Soup, ou usar
                  RSSHub (projeto open-source que gera feeds pra sites sem RSS).
                  Recomendação: esperar. Quando esses labs postam algo big, já aparece no
                  HackerNews e TechCrunch em minutos. O custo de manutenção de scrapers
                  não se justifica agora.
                </div>
                <div className="text-gray-500 text-xs mt-3">
                  Exceção: se Meta lançar Llama 5 e você quiser a notícia na fonte,
                  aí vale criar um scraper pontual pra ai.meta.com/blog.
                </div>
              </div>
            </div>

            {/* Impact */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <div className="text-white font-semibold mb-4">Impacto esperado</div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-800 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-cyan-400">4 → 7</div>
                  <div className="text-gray-500 text-xs mt-1">sources ativas</div>
                </div>
                <div className="bg-gray-800 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-cyan-400">+30</div>
                  <div className="text-gray-500 text-xs mt-1">posts/dia adicionais (estimativa)</div>
                </div>
                <div className="bg-gray-800 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-cyan-400">1ª mão</div>
                  <div className="text-gray-500 text-xs mt-1">anúncios na fonte, não via cobertura</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Architecture View */}
        {view === "arch" && (
          <div className="space-y-6">
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <div className="text-white font-semibold mb-4">Arquitetura atual vs proposta</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div className="text-gray-500 text-xs uppercase tracking-wider mb-3">Hoje (4 sources)</div>
                  <div className="space-y-2">
                    {["Reddit (13 subs)", "HackerNews (top 30)", "TechCrunch (RSS)", "Lobsters (RSS)"].map((s, i) => (
                      <div key={i} className="bg-gray-800 rounded-lg px-3 py-2 text-sm text-gray-300 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-gray-500" />
                        {s}
                      </div>
                    ))}
                    <div className="text-center text-gray-600 text-xs my-2">↓</div>
                    <div className="bg-gray-800 rounded-lg px-3 py-2 text-sm text-gray-400 text-center">
                      pre_filter → Gemini → newsletter
                    </div>
                  </div>
                </div>
                <div>
                  <div className="text-cyan-400 text-xs uppercase tracking-wider mb-3">Proposta (7 sources)</div>
                  <div className="space-y-2">
                    {[
                      { name: "Reddit (13 subs)", type: "community" },
                      { name: "HackerNews (top 30)", type: "community" },
                      { name: "TechCrunch (RSS)", type: "media" },
                      { name: "Lobsters (RSS)", type: "community" },
                      { name: "Anthropic Blog", type: "primary", isNew: true },
                      { name: "OpenAI Blog", type: "primary", isNew: true },
                      { name: "Google DeepMind Blog", type: "primary", isNew: true },
                    ].map((s, i) => (
                      <div
                        key={i}
                        className={`rounded-lg px-3 py-2 text-sm flex items-center gap-2 ${
                          s.isNew
                            ? "bg-cyan-950 border border-cyan-800 text-cyan-300"
                            : "bg-gray-800 text-gray-300"
                        }`}
                      >
                        <span
                          className={`w-2 h-2 rounded-full ${
                            s.type === "primary"
                              ? "bg-cyan-400"
                              : s.type === "media"
                              ? "bg-amber-400"
                              : "bg-gray-500"
                          }`}
                        />
                        {s.name}
                        {s.isNew && (
                          <span className="text-xs bg-cyan-800 text-cyan-200 px-1.5 py-0.5 rounded ml-auto">
                            NEW
                          </span>
                        )}
                      </div>
                    ))}
                    <div className="text-center text-gray-600 text-xs my-2">↓</div>
                    <div className="bg-gray-800 rounded-lg px-3 py-2 text-sm text-gray-400 text-center">
                      pre_filter → Gemini (com AI Gate v4) → newsletter
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <div className="text-white font-semibold mb-4">Vantagem: AI Gate fica mais poderoso</div>
              <div className="text-gray-400 text-sm">
                Com blogs oficiais de AI labs, a maioria dos posts já passa no AI Gate
                automaticamente. Isso aumenta a densidade de conteúdo AI-first que chega
                pro Gemini, melhorando a qualidade da seleção. O pre_filter já tem
                max_per_source_pct: 0.4 (nenhuma source domina mais de 40%), então
                as novas fontes não vão canibalizar as existentes.
              </div>
              <div className="mt-4 bg-gray-800 rounded-lg p-3">
                <div className="text-gray-500 text-xs mb-2">Simulação de distribuição com 7 sources:</div>
                <div className="space-y-1.5">
                  {[
                    { name: "Reddit", pct: 25, color: "bg-orange-400" },
                    { name: "HackerNews", pct: 20, color: "bg-amber-400" },
                    { name: "TechCrunch", pct: 15, color: "bg-green-400" },
                    { name: "Lobsters", pct: 10, color: "bg-blue-400" },
                    { name: "Anthropic", pct: 10, color: "bg-cyan-400" },
                    { name: "OpenAI", pct: 10, color: "bg-violet-400" },
                    { name: "DeepMind", pct: 10, color: "bg-pink-400" },
                  ].map((s, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-xs text-gray-400 w-20">{s.name}</span>
                      <div className="flex-1 h-3 bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${s.color}`}
                          style={{ width: `${s.pct}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 w-8">{s.pct}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AISourcesAnalysis;
