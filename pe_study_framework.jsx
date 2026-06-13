
// PE Study Framework — AYA Curation Prompt v5.3
// Visual methodology + preliminary audit findings
import { useState } from "react";

const PHASES = [
  {
    id: 0,
    label: "Phase 0",
    title: "Define 'Good'",
    icon: "🎯",
    color: "#6366f1",
    bg: "#eef2ff",
    duration: "1–2h",
    description: "Antes de qualquer mudança, defina o que 'bom' significa em termos mensuráveis. Sem isso, você não sabe se melhorou ou piorou.",
    steps: [
      "Definir 4–5 dimensões de qualidade (ver abaixo)",
      "Criar rubrica de scoring (1–5) para cada dimensão",
      "Alinhar rubrica com 2–3 edições que você considera 'referência'",
      "Documentar anti-patterns já conhecidos (ex: genérico, hype, rehashed)",
    ],
    dimensions: [
      { name: "Editorial Alignment", desc: "O item selecionado passa no AI Gate + 2-of-3 critérios?" },
      { name: "Tone Accuracy", desc: "Zero hype, zero invenção, certeza preservada?" },
      { name: "Diversity", desc: "Fonte, audiência, geografia variados?" },
      { name: "Freshness", desc: "Nenhum rehashed news passou?" },
      { name: "Correspondent Intro", desc: "Específico (cita tema real) vs genérico?" },
    ],
  },
  {
    id: 1,
    label: "Phase 1",
    title: "Static Audit",
    icon: "🔬",
    color: "#0891b2",
    bg: "#ecfeff",
    duration: "2–3h",
    description: "Analise o prompt como documento — sem rodar o modelo. Objetivo: encontrar structural smells que causam comportamento inconsistente.",
    steps: [
      "Mapear todos os conflitos instruction↔schema",
      "Identificar ambiguidades (onde 2 leituras diferentes são válidas)",
      "Auditar distribuição dos few-shots (quais failure modes não têm exemplo?)",
      "Medir overlap semântico entre critérios",
      "Checar 'instrução enterrada' — regras no meio do prompt que o modelo ignora",
    ],
    findings: "Ver aba Preliminary Findings ↓",
  },
  {
    id: 2,
    label: "Phase 2",
    title: "Test Set Construction",
    icon: "🧪",
    color: "#059669",
    bg: "#ecfdf5",
    duration: "2–4h",
    description: "Crie um conjunto de testes com ground truth. É o que separa intuição de evidência. Baseie nos inputs reais das edições passadas.",
    steps: [
      "Pegar raw items de 3–5 edições reais (o que entrou no LLM)",
      "Para cada edição: marcar manualmente o que DEVERIA ser selecionado (expected output)",
      "Criar casos de borda: itens ambíguos, rehashed, high-traction-no-AI",
      "Documentar edge cases que já causaram problema (prediction markets, Netflix)",
      "Resultado: test set de ~50 inputs com expected outputs anotados",
    ],
  },
  {
    id: 3,
    label: "Phase 3",
    title: "Behavioral Baseline",
    icon: "📊",
    color: "#d97706",
    bg: "#fffbeb",
    duration: "1–2h por run",
    description: "Rode o prompt atual contra o test set. Meça onde ele acerta e onde falha. Esse baseline é o ponto de partida de toda iteração futura.",
    steps: [
      "Rodar o prompt v5.3 contra o test set (3x para checar variance)",
      "Calcular scores por dimensão (rubrica da Phase 0)",
      "Catalogar failure modes: quais tipos de erro aparecem mais?",
      "Identificar os 3 maiores gap areas entre expected e actual",
      "NUNCA mudar o prompt antes de ter esse baseline documentado",
    ],
    failureModes: [
      "False positive no AI Gate (item sem ângulo AI que entrou)",
      "False negative no AI Gate (item relevante descartado)",
      "Critério mal aplicado (passou com só 1 de 3)",
      "correspondent_intro genérico mesmo com achado específico",
      "main_find escolhido por tração, não por valor editorial",
      "Radar forçado quando não havia early signals reais",
    ],
  },
  {
    id: 4,
    label: "Phase 4",
    title: "Hypothesis Testing",
    icon: "⚗️",
    color: "#7c3aed",
    bg: "#f5f3ff",
    duration: "iterativo",
    description: "Cada mudança no prompt é uma hipótese. Teste uma variável por vez. Compare delta de score no test set antes de deployar.",
    steps: [
      "Listar hipóteses priorizadas por impact × confidence",
      "Para cada hipótese: criar versão A (atual) e versão B (mudança isolada)",
      "Rodar ambas contra o test set",
      "Aceitar mudança apenas se delta for positivo em 2+ dimensões sem regressão",
      "Documentar resultado em ADR (Architectural Decision Record) no projeto",
    ],
    principle: "Regra de ouro: se você não pode medir a melhoria, você não sabe se melhorou. Isso vem do paper 'When Better Prompts Hurt' (arXiv 2601.22025).",
  },
];

const PRELIMINARY_FINDINGS = [
  {
    severity: "P0",
    color: "#dc2626",
    bg: "#fef2f2",
    area: "Instruction Burial",
    title: "Singularity rule do main_find está em STEP 4, não no início",
    detail: "A regra 'main_find DEVE ser sobre UM evento específico' está enterrada no meio do STEP 4. Se o modelo já decidiu o main_find nos STEP 1–3, pode não revisitar. Candidato a mover para uma regra FORMAT ou adicionar como critério explícito no STEP 2.",
    hypothesis: "Mover a singularity rule para antes da seleção final (STEP 2 ou STEP 3) pode reduzir roundup como main_find.",
  },
  {
    severity: "P1",
    color: "#d97706",
    bg: "#fffbeb",
    area: "Few-shot Coverage Gap",
    title: "Radar não tem nenhum exemplo de calibração",
    detail: "Há 11 exemplos para main_find, quick_finds, discard e tone. Nenhum para radar. A instrução diz 'cedo demais pra ser achado, mas...' — ambíguo sem exemplo. O modelo pode forçar radar quando não deveria, ou nunca usar.",
    hypothesis: "Adicionar 1–2 few-shots de radar (1 selecionado, 1 descartado por ser fraco) pode reduzir variância nessa seção.",
  },
  {
    severity: "P1",
    color: "#d97706",
    bg: "#fffbeb",
    area: "Criterion Overlap",
    title: "'Acionável' e 'Afeta workflows' têm sobreposição semântica alta",
    detail: "STEP 2 critério 1 (Acionável: 'testar ferramenta, mudar processo') e critério 3 (Afeta workflows: 'muda como pessoas trabalham com tech') descrevem a mesma coisa em ~60% dos casos. Isso pode inflar artificialmente o 2-of-3 score.",
    hypothesis: "Refactoring dos critérios para dimensões ortogonais: acionável (curto prazo), sinal estratégico (médio prazo), impacto estrutural (longo prazo).",
  },
  {
    severity: "P1",
    color: "#d97706",
    bg: "#fffbeb",
    area: "Step Numbering Smell",
    title: "Passos 1.5 e 4.5 são patches — podem causar confusão de sequência",
    detail: "STEP 1.5 e STEP 4.5 foram adicionados em iterações posteriores. O modelo pode não garantir a ordem correta de execução quando os passos não são inteiros. Especialmente STEP 1.5 (source bias) que opera em dimensão diferente do STEP 1 (AI gate).",
    hypothesis: "Renumerar steps para 1–7 com nomes claros. Testar se o modelo executa na ordem correta com logging do reasoning.",
  },
  {
    severity: "P2",
    color: "#2563eb",
    bg: "#eff6ff",
    area: "Missing Edge Case",
    title: "Sem instrução para 'slow news day' (poucos itens qualificados)",
    detail: "O schema exige 3–5 quick_finds. Não há instrução sobre o que fazer se apenas 1–2 itens passarem em todos os gates. O modelo pode forçar itens fracos nos quick_finds para satisfazer o constraint do schema.",
    hypothesis: "Adicionar fallback explícito: 'Se menos de 3 itens passarem nos STEPS 1–3, aceite 2 quick_finds excepcionalmente. NÃO force itens fracos.'",
  },
  {
    severity: "P2",
    color: "#2563eb",
    bg: "#eff6ff",
    area: "Redundancy",
    title: "LEMBRETE FINAL repete regras do system instruction",
    detail: "O bloco final 'PODE/NÃO PODE' replica o que já está no SYSTEM_INSTRUCTION. Pode ser intencional (reforço), mas adiciona ~100 tokens por chamada e pode diluir a atenção do modelo nos steps reais.",
    hypothesis: "Testar remoção do LEMBRETE FINAL e medir se hype/hallucination rate sobe. Se não sobe, remover para limpar o prompt.",
  },
  {
    severity: "P3",
    color: "#059669",
    bg: "#ecfdf5",
    area: "Token Efficiency",
    title: "Few-shots têm output completo — alto token count",
    detail: "Vários exemplos mostram o output completo ('Output CORRETO: ...') o que é bom para calibração de tom, mas custoso em tokens. Para exemplos de DISCARD, o output completo é desnecessário.",
    hypothesis: "Para exemplos de descarte (Ex 2, 8, 11), remover o 'Output CORRETO' — só o raciocínio de descarte importa. Potencial economia de ~200–400 tokens/request.",
  },
];

const severityOrder = { P0: 0, P1: 1, P2: 2, P3: 3 };

export default function PEStudyFramework() {
  const [activeTab, setActiveTab] = useState("methodology");
  const [activePhase, setActivePhase] = useState(0);

  const phase = PHASES[activePhase];

  return (
    <div style={{ fontFamily: "'Inter', sans-serif", maxWidth: 900, margin: "0 auto", padding: 24, background: "#f8fafc", minHeight: "100vh" }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 12, color: "#64748b", fontWeight: 600, letterSpacing: "0.05em", textTransform: "uppercase", marginBottom: 4 }}>
          Daily Scout · AYA Curation Prompt
        </div>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "#0f172a", margin: 0 }}>
          Prompt Engineering Study Framework
        </h1>
        <p style={{ color: "#64748b", marginTop: 6, fontSize: 14 }}>
          Metodologia para encontrar melhorias no CURATION_PROMPT v5.3 de forma sistemática e mensurável.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 24, borderBottom: "1px solid #e2e8f0", paddingBottom: 0 }}>
        {[
          { id: "methodology", label: "📋 Metodologia" },
          { id: "findings", label: "🔍 Preliminary Audit Findings" },
          { id: "principle", label: "📚 Por que este approach?" },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: "8px 16px",
              fontSize: 13,
              fontWeight: 600,
              border: "none",
              background: "none",
              cursor: "pointer",
              borderBottom: activeTab === tab.id ? "2px solid #6366f1" : "2px solid transparent",
              color: activeTab === tab.id ? "#6366f1" : "#64748b",
              transition: "all 0.15s",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── TAB: METHODOLOGY ── */}
      {activeTab === "methodology" && (
        <div>
          {/* Phase selector */}
          <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
            {PHASES.map((p, i) => (
              <button
                key={p.id}
                onClick={() => setActivePhase(i)}
                style={{
                  padding: "6px 14px",
                  fontSize: 12,
                  fontWeight: 700,
                  borderRadius: 20,
                  border: activePhase === i ? `2px solid ${p.color}` : "2px solid #e2e8f0",
                  background: activePhase === i ? p.bg : "white",
                  color: activePhase === i ? p.color : "#64748b",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                }}
              >
                {p.icon} {p.label}: {p.title}
              </button>
            ))}
          </div>

          {/* Active phase detail */}
          <div style={{ background: "white", borderRadius: 12, border: `2px solid ${phase.color}`, padding: 24, marginBottom: 20 }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 16, marginBottom: 16 }}>
              <div style={{ fontSize: 36 }}>{phase.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: phase.color, textTransform: "uppercase", letterSpacing: "0.05em", background: phase.bg, padding: "2px 8px", borderRadius: 10 }}>
                    {phase.label}
                  </span>
                  <span style={{ fontSize: 11, color: "#94a3b8", background: "#f1f5f9", padding: "2px 8px", borderRadius: 10 }}>
                    ⏱ {phase.duration}
                  </span>
                </div>
                <h2 style={{ fontSize: 20, fontWeight: 700, color: "#0f172a", margin: 0 }}>{phase.title}</h2>
              </div>
            </div>

            <p style={{ color: "#475569", fontSize: 14, lineHeight: 1.6, marginBottom: 20 }}>{phase.description}</p>

            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: phase.color, textTransform: "uppercase", marginBottom: 10, letterSpacing: "0.05em" }}>
                Checklist
              </div>
              {phase.steps.map((step, i) => (
                <div key={i} style={{ display: "flex", gap: 10, marginBottom: 8, alignItems: "flex-start" }}>
                  <div style={{ width: 20, height: 20, borderRadius: 4, border: `2px solid ${phase.color}`, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center", marginTop: 2 }}>
                    <div style={{ width: 8, height: 8, borderRadius: 2, background: phase.color, opacity: 0.3 }} />
                  </div>
                  <span style={{ fontSize: 13, color: "#374151", lineHeight: 1.5 }}>{step}</span>
                </div>
              ))}
            </div>

            {/* Phase-specific extras */}
            {phase.dimensions && (
              <div style={{ background: phase.bg, borderRadius: 8, padding: 16 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: phase.color, textTransform: "uppercase", marginBottom: 10, letterSpacing: "0.05em" }}>
                  Evaluation Dimensions (rubrica 1–5)
                </div>
                {phase.dimensions.map((d, i) => (
                  <div key={i} style={{ display: "flex", gap: 10, marginBottom: 6, alignItems: "flex-start" }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: phase.color, minWidth: 160 }}>{d.name}</span>
                    <span style={{ fontSize: 12, color: "#475569" }}>{d.desc}</span>
                  </div>
                ))}
              </div>
            )}

            {phase.failureModes && (
              <div style={{ background: phase.bg, borderRadius: 8, padding: 16 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: phase.color, textTransform: "uppercase", marginBottom: 10, letterSpacing: "0.05em" }}>
                  Failure Modes a Categorizar
                </div>
                {phase.failureModes.map((fm, i) => (
                  <div key={i} style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "flex-start" }}>
                    <span style={{ fontSize: 13, color: phase.color, fontWeight: 700, minWidth: 20 }}>✗</span>
                    <span style={{ fontSize: 13, color: "#374151" }}>{fm}</span>
                  </div>
                ))}
              </div>
            )}

            {phase.principle && (
              <div style={{ background: phase.bg, borderRadius: 8, padding: 16, borderLeft: `3px solid ${phase.color}` }}>
                <span style={{ fontSize: 13, color: "#374151", fontStyle: "italic", lineHeight: 1.6 }}>{phase.principle}</span>
              </div>
            )}
          </div>

          {/* Flow overview */}
          <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", padding: 16 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", marginBottom: 12, letterSpacing: "0.05em" }}>
              Study Flow
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 0, flexWrap: "wrap" }}>
              {PHASES.map((p, i) => (
                <div key={p.id} style={{ display: "flex", alignItems: "center" }}>
                  <div
                    onClick={() => setActivePhase(i)}
                    style={{ display: "flex", flexDirection: "column", alignItems: "center", cursor: "pointer", padding: "8px 12px" }}
                  >
                    <div style={{ width: 36, height: 36, borderRadius: "50%", background: i === activePhase ? p.color : p.bg, border: `2px solid ${p.color}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16 }}>
                      {p.icon}
                    </div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: p.color, marginTop: 4, textAlign: "center" }}>{p.label}</div>
                    <div style={{ fontSize: 10, color: "#94a3b8", textAlign: "center", maxWidth: 70 }}>{p.title}</div>
                  </div>
                  {i < PHASES.length - 1 && (
                    <div style={{ width: 20, height: 2, background: "#e2e8f0", flexShrink: 0 }} />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ── TAB: FINDINGS ── */}
      {activeTab === "findings" && (
        <div>
          <div style={{ background: "#fef9c3", borderRadius: 10, padding: 14, marginBottom: 20, border: "1px solid #fde047", display: "flex", gap: 10, alignItems: "flex-start" }}>
            <span style={{ fontSize: 18 }}>⚡</span>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: "#713f12", marginBottom: 2 }}>Preliminary Audit — Static Analysis do Prompt v5.3</div>
              <div style={{ fontSize: 12, color: "#713f12", lineHeight: 1.5 }}>
                Esses achados foram identificados por leitura direta do prompt (sem rodar o modelo). São hipóteses, não certezas — precisam ser validadas com behavioral testing (Phase 3).
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
            {["P0", "P1", "P2", "P3"].map(sev => {
              const counts = PRELIMINARY_FINDINGS.filter(f => f.severity === sev).length;
              const colors = { P0: "#dc2626", P1: "#d97706", P2: "#2563eb", P3: "#059669" };
              return (
                <div key={sev} style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 10px", borderRadius: 12, background: "white", border: `1px solid #e2e8f0`, fontSize: 12 }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: colors[sev] }} />
                  <span style={{ color: colors[sev], fontWeight: 700 }}>{sev}</span>
                  <span style={{ color: "#94a3b8" }}>{counts} finding{counts > 1 ? "s" : ""}</span>
                </div>
              );
            })}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {PRELIMINARY_FINDINGS.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]).map((finding, i) => (
              <div key={i} style={{ background: "white", borderRadius: 10, border: "1px solid #e2e8f0", borderLeft: `4px solid ${finding.color}`, padding: 18 }}>
                <div style={{ display: "flex", gap: 10, alignItems: "flex-start", marginBottom: 10 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: finding.color, background: finding.bg, padding: "2px 8px", borderRadius: 8, flexShrink: 0 }}>
                    {finding.severity}
                  </span>
                  <span style={{ fontSize: 11, color: "#94a3b8", background: "#f8fafc", padding: "2px 8px", borderRadius: 8, flexShrink: 0 }}>
                    {finding.area}
                  </span>
                </div>
                <div style={{ fontSize: 14, fontWeight: 700, color: "#0f172a", marginBottom: 8 }}>{finding.title}</div>
                <p style={{ fontSize: 13, color: "#475569", lineHeight: 1.6, marginBottom: 10 }}>{finding.detail}</p>
                <div style={{ background: finding.bg, borderRadius: 6, padding: 10 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: finding.color, textTransform: "uppercase", letterSpacing: "0.05em" }}>Hipótese de fix: </span>
                  <span style={{ fontSize: 12, color: "#374151" }}>{finding.hypothesis}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── TAB: PRINCIPLE ── */}
      {activeTab === "principle" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", padding: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: "#0f172a", marginBottom: 8 }}>Por que não editar o prompt diretamente?</h3>
            <p style={{ fontSize: 14, color: "#475569", lineHeight: 1.7, marginBottom: 12 }}>
              O risco central de prompt iteration sem evals é o chamado <strong>"prompt regression paradox"</strong>: você adiciona uma instrução para corrigir problema A, e ela silenciosamente piora o comportamento em B — que só vai aparecer numa edição futura.
            </p>
            <p style={{ fontSize: 14, color: "#475569", lineHeight: 1.7 }}>
              O paper <em>"When 'Better' Prompts Hurt"</em> (arXiv 2601.22025) documenta exatamente isso: mudanças que parecem melhorias em testes ad hoc frequentemente regridem métricas críticas quando testadas sistematicamente.
            </p>
          </div>

          <div style={{ background: "white", borderRadius: 12, border: "1px solid #e2e8f0", padding: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 700, color: "#0f172a", marginBottom: 16 }}>Frameworks relevantes da literatura</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {[
                {
                  paper: "Calibrate Before Use (Zhao et al., 2021 / arXiv 2102.09690)",
                  insight: "Few-shot examples não são neutros — eles calibram o output distribution do modelo. A ordem e seleção dos exemplos afeta tanto quanto o prompt principal. Implicação: auditar os 11 few-shots como se fossem training data.",
                  relevance: "Alta — a AYA tem 11 exemplos. Precisamos checar se eles calibram para os failure modes certos.",
                },
                {
                  paper: "When Better Prompts Hurt (arXiv 2601.22025)",
                  insight: "Introduz o MVES framework: Minimum Viable Evaluation Standard. Antes de qualquer iteração de prompt, você precisa de um test set com ground truth e métricas definidas.",
                  relevance: "Muito alta — é o núcleo da Phase 0 + Phase 2 desta metodologia.",
                },
                {
                  paper: "Chain-of-Thought Prompting (Wei et al., 2022)",
                  insight: "O campo reasoning no schema da AYA implementa implicitamente CoT. Mas CoT é mais efetivo quando o modelo raciocina ANTES de produzir o output, não em paralelo.",
                  relevance: "Média — hipótese: mover reasoning como step explícito ANTES dos campos de output pode melhorar coerência.",
                },
              ].map((item, i) => (
                <div key={i} style={{ background: "#f8fafc", borderRadius: 8, padding: 16, borderLeft: "3px solid #6366f1" }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: "#6366f1", marginBottom: 6 }}>📄 {item.paper}</div>
                  <p style={{ fontSize: 13, color: "#374151", lineHeight: 1.6, marginBottom: 6 }}>{item.insight}</p>
                  <div style={{ fontSize: 12, color: "#64748b" }}>
                    <span style={{ fontWeight: 700 }}>Relevância para a AYA: </span>{item.relevance}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: "#f0fdf4", borderRadius: 12, border: "1px solid #86efac", padding: 20 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#166534", marginBottom: 6 }}>💡 TL;DR — O que fazer primeiro</div>
            <ol style={{ fontSize: 13, color: "#166534", lineHeight: 1.8, paddingLeft: 18, margin: 0 }}>
              <li>Defina as 5 evaluation dimensions e uma rubrica de scoring</li>
              <li>Pegue os inputs reais de 3 edições e anote o expected output manualmente</li>
              <li>Rode o prompt v5.3 contra esse test set e documente os erros</li>
              <li>Só então priorize quais dos 7 findings preliminares vale testar</li>
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}
