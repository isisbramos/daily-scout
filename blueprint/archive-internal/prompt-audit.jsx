import { useState } from "react";

const PromptAudit = () => {
  const [activeSection, setActiveSection] = useState("score");

  const sections = [
    { id: "score", label: "Scorecard" },
    { id: "issues", label: "Problemas" },
    { id: "fix", label: "Prompt Corrigido" },
  ];

  const criteria = [
    {
      name: "Specificity over Ambiguity",
      before: 4,
      after: 7,
      afterFix: 9,
      issue:
        'Os 3 novos critérios (uso prático, direção mercado, acionável) são melhores que os antigos MAS ainda têm overlap semântico. "Afeta uso de AI hoje" e "Acionável" frequentemente descrevem a mesma notícia. O modelo vai ter dificuldade de distinguir.',
    },
    {
      name: "Decisiveness (binary output)",
      before: 3,
      after: 6,
      afterFix: 9,
      issue:
        'O so what test é ótimo como conceito, mas como escrito ("imagine o leitor contando pro colega") é uma instrução de simulação cognitiva — modelos são ruins nisso. Precisa virar checklist binário.',
    },
    {
      name: "Few-shot Alignment",
      before: 8,
      after: 5,
      afterFix: 9,
      issue:
        "REGRESSÃO CRÍTICA: os 3 few-shot examples existentes (rumor, update técnico, business) não foram atualizados pra refletir os novos critérios. O Exemplo 2 (Wine/DirectX) passaria no filtro antigo mas FALHARIA no novo — zero ângulo AI. O modelo vai receber sinais contraditórios.",
    },
    {
      name: "Instruction Hierarchy",
      before: 6,
      after: 5,
      afterFix: 8,
      issue:
        'SYSTEM_INSTRUCTION diz "newsletter de tech & AI" (equilibrado). CURATION_PROMPT diz "AI como lente" (AI-first). O modelo vai sofrer de conflito entre system e user prompt. A lente editorial precisa estar no system instruction.',
    },
    {
      name: "Negative Examples",
      before: 7,
      after: 7,
      afterFix: 9,
      issue:
        'Os exemplos negativos são bons pra tom (anti-hype), mas não existe nenhum exemplo negativo de SELEÇÃO. Falta um "este post NÃO deveria ter sido selecionado porque..." — que é exatamente o problema que você quer resolver.',
    },
    {
      name: "Measurability",
      before: 3,
      after: 5,
      afterFix: 9,
      issue:
        '"Impactante demais pra ignorar" é subjetivo. "Genérico demais" é subjetivo. Pro modelo, tudo é potencialmente impactante. Precisa de heurísticas concretas: número de fontes, presença de keywords AI, etc.',
    },
    {
      name: "Token Efficiency",
      before: 7,
      after: 5,
      afterFix: 8,
      issue:
        "O prompt proposto é ~40% mais longo que o atual. Com Gemini Flash + response_schema, cada token extra no prompt compete com tokens de output. Algumas seções podem ser compactadas sem perda de signal.",
    },
    {
      name: "Structural Coherence",
      before: 7,
      after: 6,
      afterFix: 9,
      issue:
        "Existem agora 3 camadas de filtragem (lente AI → critérios 2-de-3 → so what test → anti-signal) mas a ordem de aplicação não é explícita. O modelo pode aplicar em qualquer ordem, gerando inconsistência.",
    },
  ];

  const avgBefore = (criteria.reduce((s, c) => s + c.before, 0) / criteria.length).toFixed(1);
  const avgAfter = (criteria.reduce((s, c) => s + c.after, 0) / criteria.length).toFixed(1);
  const avgFix = (criteria.reduce((s, c) => s + c.afterFix, 0) / criteria.length).toFixed(1);

  const ScoreBar = ({ score, max = 10, color }) => (
    <div className="flex items-center gap-2">
      <div className="w-24 h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${color}`}
          style={{ width: `${(score / max) * 100}%` }}
        />
      </div>
      <span className="text-xs font-mono text-gray-400 w-6">{score}</span>
    </div>
  );

  const severityColor = (issue) => {
    if (issue.includes("REGRESSÃO") || issue.includes("CRÍTICA")) return "border-red-500 bg-red-950";
    if (issue.includes("conflito") || issue.includes("overlap")) return "border-amber-500 bg-amber-950";
    return "border-blue-500 bg-blue-950";
  };

  const severityLabel = (issue) => {
    if (issue.includes("REGRESSÃO") || issue.includes("CRÍTICA")) return { text: "P0 — Breaking", color: "bg-red-500" };
    if (issue.includes("conflito") || issue.includes("overlap")) return { text: "P1 — High", color: "bg-amber-500" };
    return { text: "P2 — Medium", color: "bg-blue-500" };
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 font-sans">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
            <span className="text-violet-400 text-xs font-mono uppercase tracking-widest">
              Prompt Engineering Audit
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            Avaliação do CURATION_PROMPT v4
          </h1>
          <p className="text-gray-400 mt-1 text-sm">
            8 critérios de prompt engineering aplicados ao prompt proposto
          </p>
        </div>

        {/* Score Summary */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800 text-center">
            <div className="text-3xl font-bold text-red-400">{avgBefore}</div>
            <div className="text-gray-500 text-xs mt-1">Prompt Atual (v3)</div>
          </div>
          <div className="bg-gray-900 rounded-xl p-5 border border-amber-800 text-center">
            <div className="text-3xl font-bold text-amber-400">{avgAfter}</div>
            <div className="text-gray-500 text-xs mt-1">Proposto (v4 draft)</div>
            <div className="text-amber-600 text-xs mt-1">+{(avgAfter - avgBefore).toFixed(1)} mas com regressões</div>
          </div>
          <div className="bg-gray-900 rounded-xl p-5 border border-emerald-800 text-center">
            <div className="text-3xl font-bold text-emerald-400">{avgFix}</div>
            <div className="text-gray-500 text-xs mt-1">v4 Corrigido</div>
            <div className="text-emerald-600 text-xs mt-1">com fixes aplicados</div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-900 rounded-lg p-1 w-fit">
          {sections.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSection(s.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeSection === s.id
                  ? "bg-violet-500 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>

        {/* Scorecard */}
        {activeSection === "score" && (
          <div className="space-y-3">
            {criteria.map((c, i) => (
              <div key={i} className="bg-gray-900 rounded-lg p-4 border border-gray-800">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-white font-medium text-sm">{c.name}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded ${severityLabel(c.issue).color} text-white`}
                  >
                    {severityLabel(c.issue).text}
                  </span>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500 w-16">Atual</span>
                    <ScoreBar score={c.before} color="bg-red-400" />
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500 w-16">Draft</span>
                    <ScoreBar score={c.after} color="bg-amber-400" />
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500 w-16">Fix</span>
                    <ScoreBar score={c.afterFix} color="bg-emerald-400" />
                  </div>
                </div>
                <div className="mt-3 text-gray-400 text-xs leading-relaxed">
                  {c.issue}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Issues Detail */}
        {activeSection === "issues" && (
          <div className="space-y-6">
            {/* P0 */}
            <div>
              <h3 className="text-red-400 font-semibold text-sm mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-500" />
                P0 — Regressão (quebra o comportamento)
              </h3>
              <div className="bg-gray-900 rounded-xl p-5 border border-red-900">
                <h4 className="text-white font-medium mb-2">
                  Few-shots desalinhados com novos critérios
                </h4>
                <p className="text-gray-400 text-sm mb-4">
                  Os 3 exemplos de calibração no prompt atual foram escritos pra ensinar TOM (anti-hype).
                  Nenhum deles ensina SELEÇÃO. Com os novos critérios, isso é um problema grave porque:
                </p>
                <div className="space-y-3">
                  <div className="bg-gray-800 rounded-lg p-3">
                    <div className="text-amber-400 text-xs font-mono mb-1">Exemplo 2 — Wine/DirectX</div>
                    <div className="text-gray-300 text-sm">
                      Wine 10.0 com DirectX 12. Pelo novo framework: zero ângulo AI, não é acionável pro público
                      (curious professionals), não mostra direção de mercado. Pela regra nova, NÃO deveria entrar.
                      Mas está como exemplo de output correto.
                    </div>
                    <div className="text-red-400 text-xs mt-2">
                      Conflito: modelo aprende que Wine/DirectX é seleção válida, mas os critérios dizem que não é.
                    </div>
                  </div>
                  <div className="bg-gray-800 rounded-lg p-3">
                    <div className="text-amber-400 text-xs font-mono mb-1">Exemplo 3 — Stripe/PayAI</div>
                    <div className="text-gray-300 text-sm">
                      Stripe compra startup de AI payments. Isso TEM ângulo AI, mas o output correto não destaca
                      o ângulo AI — foca no business deal. Pelo novo framework, o output deveria enfatizar
                      "o que isso significa na era AI".
                    </div>
                    <div className="text-amber-400 text-xs mt-2">
                      Parcialmente desalinhado: seleção ok, mas framing errado.
                    </div>
                  </div>
                </div>
                <div className="mt-4 bg-emerald-950 border border-emerald-800 rounded-lg p-3">
                  <div className="text-emerald-400 text-xs font-bold mb-1">FIX:</div>
                  <div className="text-gray-300 text-sm">
                    Adicionar 2 novos tipos de exemplo: (1) exemplo de SELEÇÃO correta vs incorreta —
                    "este post parece relevante mas NÃO passa nos critérios porque..." e
                    (2) exemplo de ranking — dado 3 posts, qual vira main_find e por quê.
                  </div>
                </div>
              </div>
            </div>

            {/* P1 */}
            <div>
              <h3 className="text-amber-400 font-semibold text-sm mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                P1 — Alto risco (comportamento imprevisível)
              </h3>
              <div className="space-y-4">
                <div className="bg-gray-900 rounded-xl p-5 border border-amber-900">
                  <h4 className="text-white font-medium mb-2">
                    Conflito System ↔ User prompt
                  </h4>
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="bg-gray-800 rounded-lg p-3">
                      <div className="text-xs text-gray-500 mb-1">SYSTEM_INSTRUCTION</div>
                      <div className="text-gray-300 text-sm font-mono">
                        "newsletter diária de tech & AI"
                      </div>
                      <div className="text-gray-500 text-xs mt-1">→ Implica peso igual</div>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-3">
                      <div className="text-xs text-gray-500 mb-1">CURATION_PROMPT (novo)</div>
                      <div className="text-gray-300 text-sm font-mono">
                        "AI como lente. Sem AI só entra se impactante demais"
                      </div>
                      <div className="text-gray-500 text-xs mt-1">→ AI-first</div>
                    </div>
                  </div>
                  <p className="text-gray-400 text-sm">
                    Em modelos com separação system/user (como Gemini), o system prompt tem precedência
                    implícita. Se o system diz "tech & AI" e o user diz "AI como lente", o modelo pode
                    ignorar a lente AI nos edge cases — exatamente onde você mais precisa dela.
                  </p>
                  <div className="mt-3 bg-emerald-950 border border-emerald-800 rounded-lg p-3">
                    <div className="text-emerald-400 text-xs font-bold mb-1">FIX:</div>
                    <div className="text-gray-300 text-sm">
                      Mover a lente editorial pra SYSTEM_INSTRUCTION: "newsletter diária que cobre
                      tech através da lente de AI". Redundância controlada entre system e user é ok.
                    </div>
                  </div>
                </div>

                <div className="bg-gray-900 rounded-xl p-5 border border-amber-900">
                  <h4 className="text-white font-medium mb-2">
                    Overlap semântico nos critérios
                  </h4>
                  <p className="text-gray-400 text-sm mb-3">
                    "Afeta uso de AI hoje" e "Acionável" têm ~70% de overlap. Se o leitor pode FAZER
                    algo com a notícia, quase sempre é porque ela afeta o uso de AI no dia a dia.
                    O modelo vai contar como 2 critérios o que na prática é 1 — inflando o score.
                  </p>
                  <div className="bg-gray-800 rounded-lg p-3 mb-3">
                    <div className="text-xs text-gray-500 mb-2">Teste mental:</div>
                    <div className="text-gray-300 text-sm">
                      "Gemini importa chats de outros chatbots"<br/>
                      → Afeta uso de AI hoje? SIM (posso migrar)<br/>
                      → Acionável? SIM (posso migrar agora)<br/>
                      → São dois critérios diferentes? ...não realmente.
                    </div>
                  </div>
                  <div className="mt-3 bg-emerald-950 border border-emerald-800 rounded-lg p-3">
                    <div className="text-emerald-400 text-xs font-bold mb-1">FIX:</div>
                    <div className="text-gray-300 text-sm">
                      Fundir em 3 critérios ortogonais: (1) Ângulo AI — tem conexão clara com AI/ML,
                      (2) Acionável — o leitor pode fazer algo concreto HOJE, (3) Sinal de mercado —
                      revela movimento estratégico, shift de poder ou nova categoria. Critério 1 é
                      obrigatório (gate), critérios 2 e 3 são differentiators.
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* P2 */}
            <div>
              <h3 className="text-blue-400 font-semibold text-sm mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500" />
                P2 — Médio (otimização)
              </h3>
              <div className="space-y-4">
                <div className="bg-gray-900 rounded-xl p-5 border border-blue-900">
                  <h4 className="text-white font-medium mb-2">
                    So What Test: simulação cognitiva → checklist binário
                  </h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-red-950 rounded-lg p-3">
                      <div className="text-red-400 text-xs font-bold mb-1">COMO ESTÁ</div>
                      <div className="text-gray-300 text-sm">
                        "Imagine o leitor contando pro colega no café. Se ele não consegue dizer
                        'sabia que agora dá pra...' ou 'isso muda X porque...', o item não passou."
                      </div>
                      <div className="text-red-400 text-xs mt-2">
                        Problema: pede ao modelo pra simular uma persona simulando outra persona.
                        Dois níveis de abstração. Gemini Flash vai simplificar.
                      </div>
                    </div>
                    <div className="bg-emerald-950 rounded-lg p-3">
                      <div className="text-emerald-400 text-xs font-bold mb-1">COMO DEVERIA SER</div>
                      <div className="text-gray-300 text-sm">
                        "TESTE FINAL: para cada item selecionado, complete UMA das frases abaixo.
                        Se não conseguir completar nenhuma com informação do título, descarte o item:<br/><br/>
                        → 'Agora é possível [ação concreta]'<br/>
                        → '[Player] está [movendo pra / saindo de / apostando em] [categoria]'"
                      </div>
                      <div className="text-emerald-400 text-xs mt-2">
                        Virou completion task — modelos são excelentes nisso.
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-900 rounded-xl p-5 border border-blue-900">
                  <h4 className="text-white font-medium mb-2">
                    Anti-signal precisa de heurísticas concretas
                  </h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-red-950 rounded-lg p-3">
                      <div className="text-red-400 text-xs font-bold mb-1">COMO ESTÁ</div>
                      <div className="text-gray-300 text-sm">
                        "Genérico demais: 'Netflix sobe preço', 'empresa levanta série B'"
                      </div>
                      <div className="text-red-400 text-xs mt-2">
                        Só 2 exemplos. "Genérico" é subjetivo. O modelo não sabe onde traçar a linha.
                      </div>
                    </div>
                    <div className="bg-emerald-950 rounded-lg p-3">
                      <div className="text-emerald-400 text-xs font-bold mb-1">COMO DEVERIA SER</div>
                      <div className="text-gray-300 text-sm">
                        "DESCARTE se o título se enquadra em:<br/>
                        → Preço/assinatura de serviço consumer (Netflix, Spotify, Disney+)<br/>
                        → Funding round sem ângulo AI/tech específico<br/>
                        → Atualização de produto sem impacto em workflows (ex: UI redesign)<br/>
                        → Política/regulação sem conexão direta com AI<br/>
                        → Mercado financeiro/crypto sem aplicação de AI"
                      </div>
                      <div className="text-emerald-400 text-xs mt-2">
                        Pattern matching &gt; julgamento subjetivo.
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-gray-900 rounded-xl p-5 border border-blue-900">
                  <h4 className="text-white font-medium mb-2">
                    Ordem de operações não explícita
                  </h4>
                  <div className="bg-emerald-950 rounded-lg p-3">
                    <div className="text-emerald-400 text-xs font-bold mb-1">FIX: Pipeline de decisão explícito</div>
                    <div className="text-gray-300 text-sm font-mono leading-relaxed">
                      {`STEP 1 — GATE: Tem ângulo AI?
  SIM → continua
  NÃO → só entra se magnitude
        excepcional (aquisição >$1B,
        regulação governamental)

STEP 2 — SCORE: 2 de 3 critérios?
  (acionável, sinal de mercado,
   afeta workflows)
  SIM → candidato
  NÃO → descarta

STEP 3 — ANTI-SIGNAL: matches
  algum padrão de descarte?
  SIM → descarta
  NÃO → mantém

STEP 4 — RANK: entre candidatos,
  main_find = mais acionável ou
  maior sinal de mercado.
  Tração = tiebreaker.`}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Fixed Prompt */}
        {activeSection === "fix" && (
          <div className="space-y-6">
            <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
              <div className="bg-violet-950 px-4 py-3 border-b border-violet-800">
                <span className="text-violet-300 font-mono text-sm font-bold">
                  CURATION_PROMPT v4 — CORRIGIDO
                </span>
                <span className="text-violet-600 text-xs ml-3">
                  todos os P0/P1/P2 aplicados
                </span>
              </div>
              <div className="p-5">
                <pre className="text-sm text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">
{`Selecione e escreva os achados do dia a partir
dos posts abaixo.

PÚBLICO: profissionais curiosos sobre tech & AI.
Não necessariamente técnicos, mas inteligentes e
ocupados. Explique termos técnicos brevemente
entre parênteses.

═══ PIPELINE DE SELEÇÃO ═══

STEP 1 — AI GATE (obrigatório):
O post tem conexão com AI/ML, modelos de
linguagem, automação inteligente, ou decisões de
empresas de AI?
→ SIM: continua pro Step 2.
→ NÃO: só entra se for evento de magnitude
  excepcional (aquisição >$1B, regulação
  governamental, shutdown de plataforma major).
  Caso contrário, DESCARTE.

STEP 2 — CRITÉRIOS (precisa de pelo menos 2):
1. Acionável — o leitor pode fazer algo concreto:
   testar ferramenta, mudar processo, tomar decisão
2. Sinal de mercado — revela movimento estratégico:
   player entrando/saindo de categoria, shift de
   política de dados, nova aliança/aquisição
3. Afeta workflows — muda como pessoas trabalham
   com tech/AI no dia a dia

STEP 3 — ANTI-SIGNAL (descarte imediato):
Descarte se o título se enquadra em:
→ Preço/assinatura de serviço consumer
  (Netflix, Spotify, Disney+)
→ Funding round sem ângulo AI/tech específico
→ Mercado financeiro/crypto/apostas sem
  aplicação de AI
→ Atualização de produto sem impacto em
  workflows (ex: UI redesign cosmético)
→ Confirmação do óbvio ("X vai continuar Y")

STEP 4 — RANKING:
→ main_find = item mais acionável OU com maior
  sinal de mercado. Tração (score) é tiebreaker,
  NUNCA critério principal.
→ quick_finds = 3-5 itens restantes que passaram.
→ Diversidade de fontes: prefira representação
  variada.

STEP 5 — TESTE FINAL:
Para cada item selecionado, complete UMA frase:
→ "Agora é possível [ação concreta]"
→ "[Player] está [movendo pra / investindo em /
   saindo de] [categoria]"
Se não conseguir completar com informação do
título, DESCARTE o item.

═══ EXEMPLOS DE CALIBRAÇÃO ═══

Exemplo 1 — SELEÇÃO CORRETA (acionável + AI):
Input: { "title": "Gemini now lets you import
  chat history from ChatGPT and other chatbots",
  "source": "TechCrunch", "score": 89 }
→ AI gate: SIM (chatbots de AI)
→ Critérios: Acionável (posso migrar agora) +
  Sinal de mercado (Google competindo por lock-in)
→ Teste: "Agora é possível importar conversas de
  outros chatbots pro Gemini"
→ SELECIONADO como main_find

Exemplo 2 — DESCARTE CORRETO (alta tração, sem AI):
Input: { "title": "We haven't satisfactorily
  dealt with the worst of what prediction markets
  will do", "source": "HackerNews", "score": 539 }
→ AI gate: NÃO (mercados de previsão/apostas)
→ Magnitude excepcional? NÃO (é post de opinião)
→ DESCARTADO — 539 pontos não salva post sem
  ângulo AI

Exemplo 3 — DESCARTE CORRETO (genérico):
Input: { "title": "Netflix confirms another price
  increase", "source": "TechCrunch", "score": 205 }
→ AI gate: NÃO
→ Anti-signal: preço de serviço consumer
→ DESCARTADO

Exemplo 4 — RUMOR/ESPECULAÇÃO (tom):
Input: { "title": "Report: OpenAI may shut down
  Sora after backlash", "source": "HackerNews",
  "score": 847 }
Output ERRADO: "A OpenAI encerra o Sora, gerando
  choque no mercado de vídeo por IA."
→ Converteu "may" em fato, inventou "choque".
Output CORRETO: "Segundo post com alta tração no
  HackerNews (847 pontos), a OpenAI estaria
  considerando descontinuar o Sora — sua
  ferramenta de geração de vídeo por IA — após
  reações negativas."

Exemplo 5 — BUSINESS com ângulo AI:
Input: { "title": "Stripe acquires AI payments
  startup PayAI for $1.2B", "source": "TechCrunch",
  "score": 0 }
→ AI gate: SIM (startup de AI payments)
→ Critérios: Sinal de mercado (Stripe apostando
  em AI pra pagamentos)
→ Teste: "Stripe está investindo em AI aplicada
  a pagamentos com aquisição de $1.2B"
→ SELECIONADO como quick_find
Output: "De acordo com o TechCrunch, a Stripe
  adquiriu a PayAI — startup de pagamentos com
  inteligência artificial — por US$ 1,2 bilhão.
  A aquisição sinaliza que AI está chegando ao
  core da infraestrutura de pagamentos online."

═══ REGRAS DE FORMATO ═══
(sem alterações — mantém regras atuais)

═══ REGRAS DE TOM ═══
(sem alterações — mantém regras atuais)

POSTS COLETADOS:`}
                </pre>
              </div>
            </div>

            {/* Also fix system instruction */}
            <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
              <div className="bg-amber-950 px-4 py-3 border-b border-amber-800">
                <span className="text-amber-300 font-mono text-sm font-bold">
                  SYSTEM_INSTRUCTION — AJUSTE (linha 143)
                </span>
              </div>
              <div className="p-5">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-red-400 text-xs font-bold mb-2">ANTES</div>
                    <div className="bg-gray-800 rounded-lg p-3 text-sm text-gray-300 font-mono">
                      "Você é a AYA — analista de campo do Daily Scout, newsletter diária de <span className="text-red-400">tech & AI</span>."
                    </div>
                  </div>
                  <div>
                    <div className="text-emerald-400 text-xs font-bold mb-2">DEPOIS</div>
                    <div className="bg-gray-800 rounded-lg p-3 text-sm text-gray-300 font-mono">
                      "Você é a AYA — analista de campo do Daily Scout, newsletter diária que cobre <span className="text-emerald-400">o mundo tech através da lente de AI</span>. Seu público são profissionais curiosos que querem entender como AI está mudando tecnologia, negócios e trabalho."
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Summary */}
            <div className="bg-gray-900 rounded-xl p-5 border border-violet-800">
              <h3 className="text-violet-300 font-semibold mb-3">TL;DR das mudanças</h3>
              <div className="space-y-2 text-sm text-gray-400">
                <div className="flex gap-2">
                  <span className="text-red-400 font-bold w-6">P0</span>
                  <span>Few-shots reescritos com exemplos de SELEÇÃO (não só tom). Adicionados exemplos de DESCARTE.</span>
                </div>
                <div className="flex gap-2">
                  <span className="text-amber-400 font-bold w-6">P1</span>
                  <span>Lente "AI-first" movida pro SYSTEM_INSTRUCTION. Critérios reestruturados pra ser ortogonais (sem overlap).</span>
                </div>
                <div className="flex gap-2">
                  <span className="text-blue-400 font-bold w-6">P2</span>
                  <span>So what test virou completion task. Anti-signal virou pattern list. Pipeline de decisão explícito em steps.</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PromptAudit;
