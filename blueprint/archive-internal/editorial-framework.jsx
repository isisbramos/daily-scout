import { useState } from "react";

const EditorialFramework = () => {
  const [activeTab, setActiveTab] = useState("framework");

  const tabs = [
    { id: "framework", label: "Framework Editorial" },
    { id: "before_after", label: "Before → After (Prompt)" },
    { id: "test", label: "Teste: Edição #001" },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 font-sans">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            <span className="text-amber-400 text-xs font-mono uppercase tracking-widest">
              Daily Scout — Editorial Calibration
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            Novo framework de curadoria da AYA
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            Extraído das respostas da Isis em 26/03/2026
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-900 rounded-lg p-1 w-fit">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? "bg-amber-400 text-gray-950"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab: Framework */}
        {activeTab === "framework" && (
          <div className="space-y-6">
            {/* Positioning */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-amber-400">01</span> Posicionamento
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Lente</div>
                  <div className="text-white font-medium">AI como lente</div>
                  <div className="text-gray-400 text-sm mt-1">
                    Qualquer notícia de tech, mas sempre pelo ângulo de "o que isso significa na era AI"
                  </div>
                </div>
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Persona</div>
                  <div className="text-white font-medium">Curious professionals</div>
                  <div className="text-gray-400 text-sm mt-1">
                    Profissionais de qualquer área que querem entender tech/AI sem ser técnico demais
                  </div>
                </div>
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">So What Test</div>
                  <div className="text-white font-medium">"Sabia que agora dá pra..."</div>
                  <div className="text-gray-400 text-sm mt-1">
                    O leitor sai com algo prático que pode experimentar ou aplicar
                  </div>
                </div>
              </div>
            </div>

            {/* Signal Framework */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-amber-400">02</span> O que é Signal (notícia entra)
              </h2>
              <p className="text-gray-400 text-sm mb-4">
                Precisa ter pelo menos 2 de 3 — mas os critérios mudaram:
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-emerald-950 border border-emerald-800 rounded-lg p-4">
                  <div className="text-emerald-400 font-medium mb-1">Afeta uso de AI hoje</div>
                  <div className="text-gray-400 text-sm">
                    Muda o comportamento prático de quem trabalha com tech/AI no dia a dia
                  </div>
                  <div className="mt-3 text-xs text-emerald-600">
                    Ex: "Gemini permite importar chats de outros chatbots" → afeta workflow direto
                  </div>
                </div>
                <div className="bg-emerald-950 border border-emerald-800 rounded-lg p-4">
                  <div className="text-emerald-400 font-medium mb-1">Direção do mercado</div>
                  <div className="text-gray-400 text-sm">
                    Sinais estratégicos — movimentos de players, shifts, novas categorias
                  </div>
                  <div className="mt-3 text-xs text-emerald-600">
                    Ex: "GitHub Copilot usará dados de usuários" → shift de política de dados em AI
                  </div>
                </div>
                <div className="bg-emerald-950 border border-emerald-800 rounded-lg p-4">
                  <div className="text-emerald-400 font-medium mb-1">Acionável</div>
                  <div className="text-gray-400 text-sm">
                    O leitor consegue fazer algo: testar, mudar processo, tomar decisão
                  </div>
                  <div className="mt-3 text-xs text-emerald-600">
                    Ex: "Wikipedia restringe AI em artigos" → editores precisam adaptar workflow
                  </div>
                </div>
              </div>
            </div>

            {/* Anti-signal */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-amber-400">03</span> O que é Noise (notícia NÃO entra)
              </h2>
              <div className="space-y-3">
                <div className="bg-red-950 border border-red-900 rounded-lg p-4 flex items-start gap-3">
                  <span className="text-red-400 text-lg mt-0.5">✕</span>
                  <div>
                    <div className="text-red-300 font-medium">Genérica demais</div>
                    <div className="text-gray-400 text-sm">
                      "Netflix sobe preço", "empresa X levanta série B" — não ensina nada novo sobre tech/AI.
                      Mesmo com tração alta, se não passa no filtro editorial, não entra nem como quick find.
                    </div>
                  </div>
                </div>
                <div className="bg-red-950 border border-red-900 rounded-lg p-4 flex items-start gap-3">
                  <span className="text-red-400 text-lg mt-0.5">✕</span>
                  <div>
                    <div className="text-red-300 font-medium">Sem conexão com AI</div>
                    <div className="text-gray-400 text-sm">
                      Notícia de tech pura sem ângulo AI só entra se for impactante demais
                      (nível "Google compra X"). Caso contrário, descarta.
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Traction Rule */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <span className="text-amber-400">04</span> Papel da Tração
              </h2>
              <div className="bg-amber-950 border border-amber-800 rounded-lg p-4">
                <div className="text-amber-300 font-medium mb-2">
                  Tração é sinal, não filtro
                </div>
                <div className="text-gray-400 text-sm">
                  Score alto indica que o tema está quente, mas NÃO garante entrada na newsletter.
                  Um post com 50 pontos que afeta uso de AI no dia a dia vale mais que um post
                  com 500 pontos sobre um tema genérico sem ângulo AI.
                </div>
                <div className="mt-3 text-xs text-amber-600">
                  Antes: "2 de 3: Tração, Impacto, Novidade" → Tração era critério de entrada.
                  Agora: Tração é context, não criteria.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab: Before/After */}
        {activeTab === "before_after" && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* BEFORE */}
              <div className="bg-gray-900 rounded-xl border border-red-900/50 overflow-hidden">
                <div className="bg-red-950 px-4 py-3 border-b border-red-900/50">
                  <span className="text-red-400 font-mono text-sm font-bold">ANTES — CURATION_PROMPT</span>
                </div>
                <div className="p-4">
                  <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">{`PÚBLICO: pessoas curiosas sobre
tecnologia, não necessariamente
técnicas.

CRITÉRIOS DE SELEÇÃO:
- Cada item precisa ter pelo menos
  2 de 3:
  Tração (score alto ou múltiplas
  fontes),
  Impacto (afeta o dia a dia),
  Novidade (algo novo no setor).
- Diversidade de fontes: prefira
  representação variada.
- Escolha 1 main_find e 3-5
  quick_finds.`}</pre>
                </div>
              </div>

              {/* AFTER */}
              <div className="bg-gray-900 rounded-xl border border-emerald-900/50 overflow-hidden">
                <div className="bg-emerald-950 px-4 py-3 border-b border-emerald-900/50">
                  <span className="text-emerald-400 font-mono text-sm font-bold">DEPOIS — CURATION_PROMPT</span>
                </div>
                <div className="p-4">
                  <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">{`PÚBLICO: profissionais curiosos
sobre tech & AI — não
necessariamente técnicos, mas
inteligentes e ocupados. Querem
sair sabendo algo que podem usar
ou contar pra alguém.

LENTE EDITORIAL: AI como lente.
Qualquer notícia de tech é
bem-vinda, mas SEMPRE analisada
pelo ângulo de "o que isso
significa na era AI". Notícia sem
conexão com AI só entra se for
impactante demais pra ignorar
(nível "Google compra X").

CRITÉRIOS DE SELEÇÃO — cada item
precisa ter pelo menos 2 de 3:
1. Afeta uso de AI hoje — muda
   comportamento prático de quem
   trabalha com tech/AI
2. Direção do mercado — sinal
   estratégico, movimento de
   players, shift de categoria
3. Acionável — o leitor consegue
   fazer algo: testar, mudar
   processo, tomar decisão

PAPEL DA TRAÇÃO: score alto é
SINAL (indica tema quente), não
FILTRO. Post com 50pts que afeta
uso de AI vale mais que post com
500pts genérico. Nunca escolha
main_find apenas por score.

TESTE DO "SO WHAT": imagine o
leitor contando pro colega no
café. Se ele não consegue dizer
"sabia que agora dá pra..." ou
"isso muda X porque...", o item
não passou.

ANTI-SIGNAL — NÃO selecione:
- Genérico demais: "Netflix sobe
  preço", "empresa levanta série
  B" — não ensina nada sobre
  tech/AI
- Sem ângulo AI + sem impacto
  excepcional: descarta
- Confirmação do óbvio: "X vai
  continuar fazendo Y" — zero
  novidade

COMPOSIÇÃO:
- 1 main_find + 3-5 quick_finds
- Diversidade de fontes
- Priorize: main_find deve ser o
  item mais acionável ou com maior
  sinal de direção de mercado`}</pre>
                </div>
              </div>
            </div>

            {/* Changelog */}
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h3 className="text-white font-semibold mb-4">O que mudou</h3>
              <div className="space-y-3">
                {[
                  {
                    change: "Tração saiu dos critérios de seleção",
                    why: "Antes era 1 de 3 critérios. Agora é context, não criteria. Prediction markets não teria sido main find.",
                  },
                  {
                    change: "Novos critérios: uso prático, direção de mercado, acionabilidade",
                    why: "Substituem o trio genérico Tração/Impacto/Novidade por critérios alinhados com o público.",
                  },
                  {
                    change: "Lente editorial explícita: AI-first",
                    why: "Notícia sem ângulo AI agora precisa passar por um bar muito alto pra entrar.",
                  },
                  {
                    change: "So What Test adicionado",
                    why: "'Sabia que agora dá pra...' como litmus test. Se o leitor não consegue formular, descarta.",
                  },
                  {
                    change: "Anti-signal explícito: genérico = noise",
                    why: "Netflix subindo preço não entra mais nem como quick find.",
                  },
                ].map((item, i) => (
                  <div key={i} className="flex gap-4 items-start">
                    <div className="w-6 h-6 rounded-full bg-amber-400 text-gray-950 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                      {i + 1}
                    </div>
                    <div>
                      <div className="text-white font-medium text-sm">{item.change}</div>
                      <div className="text-gray-500 text-sm">{item.why}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Tab: Test */}
        {activeTab === "test" && (
          <div className="space-y-6">
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h3 className="text-white font-semibold mb-2">
                Re-ranking da edição #001 com novo framework
              </h3>
              <p className="text-gray-400 text-sm mb-6">
                Se a AYA tivesse usado os novos critérios, como ficaria a edição de hoje?
              </p>

              <div className="space-y-4">
                {/* New Main Find */}
                <div className="bg-emerald-950 border border-emerald-800 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="bg-emerald-400 text-gray-950 text-xs font-bold px-2 py-0.5 rounded">
                      MAIN FIND
                    </span>
                    <span className="text-emerald-400 text-xs">com novo framework</span>
                  </div>
                  <div className="text-white font-medium">
                    Gemini Permite Transferência de Chats de Outros Chatbots
                  </div>
                  <div className="text-gray-400 text-sm mt-2">
                    Por quê? Afeta uso de AI hoje (portabilidade de dados), mostra direção do mercado
                    (Google competindo por lock-in), e é acionável (usuário pode migrar agora).
                    Passa no so what test: "sabia que agora dá pra importar tudo do ChatGPT pro Gemini?"
                  </div>
                  <div className="flex gap-2 mt-3">
                    <span className="bg-emerald-900 text-emerald-300 text-xs px-2 py-0.5 rounded">uso prático</span>
                    <span className="bg-emerald-900 text-emerald-300 text-xs px-2 py-0.5 rounded">direção mercado</span>
                    <span className="bg-emerald-900 text-emerald-300 text-xs px-2 py-0.5 rounded">acionável</span>
                  </div>
                </div>

                {/* Quick Finds */}
                {[
                  {
                    title: "Wikipedia Restringe Uso de IA na Escrita de Artigos",
                    tags: ["direção mercado", "acionável"],
                    reason: "Plataforma de conhecimento mudando regras por AI — editores precisam adaptar",
                  },
                  {
                    title: "GitHub Copilot Usará Dados de Usuários para Treinamento",
                    tags: ["uso prático", "direção mercado"],
                    reason: "Afeta todo dev que usa Copilot — questão de privacidade e IP",
                  },
                  {
                    title: "Juiz Bloqueia Rótulo de Risco do Pentágono para Anthropic",
                    tags: ["direção mercado"],
                    reason: "Relação governo + AI companies — regulação do setor",
                  },
                ].map((item, i) => (
                  <div key={i} className="bg-gray-800 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-gray-500 text-xs font-mono">QF{i + 1}</span>
                    </div>
                    <div className="text-white text-sm font-medium">{item.title}</div>
                    <div className="text-gray-500 text-xs mt-1">{item.reason}</div>
                    <div className="flex gap-2 mt-2">
                      {item.tags.map((tag, j) => (
                        <span
                          key={j}
                          className="bg-gray-700 text-gray-300 text-xs px-2 py-0.5 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}

                {/* Removed */}
                <div className="border-t border-gray-800 pt-4 mt-4">
                  <div className="text-gray-500 text-xs uppercase tracking-wider mb-3">
                    Removidos pelo novo framework
                  </div>
                  {[
                    {
                      title: "Prediction Markets — potencial impacto negativo",
                      reason: "Sem ângulo AI, genérico. 539pts no HN mas não passa no so what test pro público Daily Scout.",
                    },
                    {
                      title: "Netflix Confirma Novo Aumento de Preços",
                      reason: "Genérico demais. Não ensina nada sobre tech/AI. Noise puro.",
                    },
                  ].map((item, i) => (
                    <div
                      key={i}
                      className="bg-gray-900 border border-red-900/30 rounded-lg p-3 mb-2 opacity-60"
                    >
                      <div className="text-gray-400 text-sm line-through">{item.title}</div>
                      <div className="text-red-400 text-xs mt-1">{item.reason}</div>
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

export default EditorialFramework;
