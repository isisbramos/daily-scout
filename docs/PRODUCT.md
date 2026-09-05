# AYA's Daily — Product Brief

> *Uma newsletter de curadoria de tech & AI, escrita por uma correspondente de IA com voz editorial própria.*

---

## O que é

O **AYA's Daily** é uma newsletter diária automatizada que resolve o problema de information overload no universo de tech & IA. Em vez de acompanhar dezenas de feeds, threads e newsletters, o leitor recebe um briefing editorial com o que realmente importa — curado com critério, escrito com clareza.

A "correspondente" é a **Aya** — uma persona de IA com voz, ponto de vista e consistência editorial. Ela monitora 10 fontes globais por dia, filtra ruído com critérios editoriais precisos, e entrega uma edição que parece escrita por uma colunista, não por um bot.

---

## O problema

O volume de conteúdo sobre tech & AI cresceu mais rápido do que a capacidade de qualquer pessoa de filtrar o que importa. O resultado é:

- **Tempo desperdiçado** lendo conteúdo que não gera insight
- **Viés de fonte** — a maioria das newsletters reflete uma perspectiva US/EU anglófona
- **Ruído mascarado de notícia** — alta tração ≠ alta relevância

O AYA's Daily existe pra resolver os três.

---

## A solução

Um pipeline automatizado end-to-end que roda diariamente sem intervenção manual:

```
10 fontes globais
    │
    ▼
Pre-filter estatístico (z-score, recency decay, wild card zone)
    │
    ▼
Aya — Gemini Flash com framework editorial de 5 steps
    │  AI Gate → Critérios → Anti-signal → Ranking → Teste final
    │
    ▼
Email (Jinja2 → Buttondown API) + Post social (LinkedIn)
```

O leitor recebe um **main find** (o achado editorial do dia), **quick finds** (3–4 itens relevantes) e uma seção **Radar** (early signals que merecem atenção).

---

## Diferencial

Três coisas que o AYA's Daily faz que a maioria das newsletters de tech/AI não faz:

**1. AI como lente editorial, não como tema**
Não é uma cobertura genérica de tech. Tudo passa pelo AI Gate: qual o ângulo AI dessa história? Se não tem, só entra se for excepcional. Isso cria foco, não filtro de bolha.

**2. Perspectiva global (não-ocidental)**
Das 10 fontes monitoradas, 3 são geográficas (SCMP Tech, Rest of World, TechNode) — cobrem Ásia, Global South e perspectivas fora do eixo US/EU que a maioria das newsletters ignora.

**3. Aya tem voz, não é um digest anônimo**
A Aya é uma persona consistente: factual, sem hype, com ângulo editorial definido. Ela explica o que algo *é* e por que *importa* — não amplifica o que já está sendo amplificado.

---

## Audience

**Quem é o leitor ideal:**
Pessoa que quer se manter informada sobre o que está evoluindo no mundo de AI — sem precisar gastar horas filtrando o ruído por conta própria. Não precisa ser técnico. Precisa ter curiosidade e interesse em usar AI como vantagem, não apenas como ferramenta.

**O que o leitor ganha:**
- 5 minutos por dia em vez de 45
- Contexto, não só notícia — entende o que o acontecimento *significa*
- Perspectiva global que a maioria das fontes não oferece

---

## Princípios editoriais

A Aya opera por um conjunto fixo de princípios que define o que entra e o que fica de fora:

| Princípio | O que significa na prática |
|-----------|---------------------------|
| **AI Gate** | Todo item precisa ter ângulo AI. Sem isso, não entra. |
| **So what test** | "Sabia que agora dá pra..." — se não passa, não é acionável. |
| **Tração ≠ relevância** | Score alto no HN não garante entrada. É sinal, não critério. |
| **Factual over hype** | A Aya explica, não dramatiza. Nunca converte incerteza em fato. |
| **Anti-signal** | Preço consumer, funding genérico, crypto sem AI = descarte imediato. |

---

## Métricas de sucesso

O produto é saudável quando três coisas estão crescendo juntas:

| Métrica | O que mede | Onde monitorar |
|---------|-----------|----------------|
| **Subscribers** | Reach e crescimento da audiência | Buttondown dashboard |
| **Feedback ratio** (🔥 vs 😐) | Qualidade percebida da curadoria | Google Sheet "Daily Scout Feedback" |
| **Publishing consistency** | Confiabilidade do pipeline | GitHub Actions — daily-scout.yml |

---

## Visão

O AYA's Daily é um projeto com potencial de escala. Começou como um experimento pessoal — uma PM testando quanto de um produto de mídia dá pra automatizar com AI — e evoluiu pra um pipeline editorial com arquitetura própria, framework de curadoria versionado e feedback loop funcional.

A direção de longo prazo é expandir audiência e explorar modelos de monetização, mantendo a qualidade editorial como constraint inegociável.

---

## Stack técnica (visão de produto)

| Componente | Tecnologia | Papel |
|-----------|-----------|-------|
| Coleta | Reddit API, HN API, RSS (10 fontes) | Fetch de conteúdo diário |
| Pre-filter | Python (z-score, exponential decay) | Reduz ~300 → 40 itens candidatos |
| Curadoria | Gemini 2.5 Flash + framework editorial v5.3 | Seleciona + escreve a edição |
| Validação | `validate_tone()` — hype detector com retry | Garante tom factual |
| Entrega | Jinja2 (HTML) → Buttondown API | Email para subscribers |
| Social | LinkedIn API | Post de distribuição diário |
| Feedback | Google Sheet + Apps Script + feedback.html | Signal de qualidade por edição |
| Automação | GitHub Actions (cron diário) | Zero intervenção manual |

Para arquitetura técnica detalhada → [`CURRENT_STATE.md`](CURRENT_STATE.md)
Para histórico de evolução → [`DOC_PROCESSO_DAILY_SCOUT.md`](DOC_PROCESSO_DAILY_SCOUT.md)
Para evolução editorial → [`EDITORIAL_RETROSPECTIVE.md`](EDITORIAL_RETROSPECTIVE.md)

---

*Documento criado em 19/04/2026. Mantenha atualizado a cada mudança significativa de direção de produto.*
