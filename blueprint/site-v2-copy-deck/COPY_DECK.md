# Daily Scout — Copy Deck & Narrative Blueprint

> Documento de referência pra análise estrutural e mudanças pontuais do site.
> Organizado como **narrative arc** → **section-by-section copy map** → **análise crítica**.

---

## 📝 Changelog

**2026-04-19 · UX writing pass (v2)**
- Hero headline: `Uma correspondente de IA reportando da linha de frente do tech.` → `A AYA lê ~300 histórias de tech toda manhã. Você lê só as que importam.` (D1 benefit-driven)
- Hero sub: reescrita afirmativa, sem triplete de negações — `10 fontes globais, 5 filtros editoriais, 1 email por dia às 8h BRT. Factual, curado, com perspectiva além do eixo US-EU.`
- Proof strip: removido `Grátis` (rumo a paid tier), substituído por linha de formato (`Deep dive + 3 quick finds`)
- Meet AYA título: `Ela não é humana. Ela tem uma linha editorial.` → `Ela não é humana. Mas tem critério.` (remove jargão editorial + soa menos autoritário)
- **Palavra `signal`** removida do user-facing copy (mantida apenas em labels técnicos como `FUNDING SIGNAL`, `TRACTION SIGNAL`, `Anti-signal`, `HIGH SIGNAL-TO-NOISE`, `OSS SIGNAL`)
  - `o signal que importa` → `o que vale a pena ler`
  - `só o signal` → `só o que muda algo`
  - `O que sobra é o signal` → `O que sobra, vale seu tempo`
  - `early signals` → `tendências em formação`
  - `market signal` → `indicador de mercado`
  - `é signal, não é critério` → `é tração, não é critério`
  - `signal silencioso` → `indício silencioso`
  - `ruído` → substituto único de `noise` em prose quando traduzido
- Meta tags (description, og, twitter): atualizadas pro novo hero

---

## 🎯 Premissa narrativa (one-liner)

> **"A AYA é uma correspondente de IA que lê ~300 histórias de tech toda manhã pra você ler só as que importam — e aqui está como e por que."**

O site vende **3 coisas em ordem**: (1) a persona AYA, (2) o editorial framework como diferencial defensível, (3) a assinatura como ato de baixo custo.

---

## 🗺️ Arquitetura das 3 páginas

| Página | Função narrativa | Objetivo de conversão |
|---|---|---|
| `/` (landing) | **Hook + prova + CTA** — gerar interesse em <30s | Email capture |
| `/archive/` | **Evidência de produto** — "isso de fato existe e é consistente" | Email capture (repeat) |
| `/about/` | **Defensibilidade** — "por que isso é diferente, por que confiar" | Email capture (conversion do skeptic) |

**Fluxo ideal do leitor:**
```
Landing (hook) → scroll → captura no hero OU no final CTA
       ↓
   (se não converter)
       ↓
Archive (prova de consistência) → captura no inline sub
       ↓
   (se ainda não converter)
       ↓
About (defensibilidade profunda) → captura no final CTA
```

---

# 1. Landing (`/`)

**Narrative arc da página:** `Hook → Identidade (AYA) → Produto (preview) → Método (framework) → Diferenciação → Prova (archive) → Humano (creator) → CTA`

## 1.1 Nav (sticky)

| Slot | Copy |
|---|---|
| Logo | `● AYA · Daily Scout` |
| Link 1 | `Edições` |
| Link 2 | `Sobre` |
| CTA | `Assinar` |

**Função:** navegação mínima + 1 ação. Dot verde pulsante reforça "live/active".

---

## 1.2 Hero

**Função narrativa:** 1 frase de hook, 1 parágrafo de prova, 1 ação.

| Slot | Copy |
|---|---|
| Eyebrow (badge) | `● TRANSMITINDO · 8H BRT` |
| Headline (serif, italic em "~300 histórias") | `A AYA lê ~300 histórias de tech toda manhã. Você lê só as que importam.` |
| Sub (body) | `10 fontes globais, 5 filtros editoriais, 1 email por dia às 8h BRT. Factual, curado, com perspectiva além do eixo US-EU.` |
| Input placeholder | `voce@empresa.com` |
| CTA button | `Assinar grátis` |
| Note (mono) | `// sem spam · unsubscribe em 1 clique · curadoria por IA, verificação por PM` |
| Portrait badge | `● AYA v0.1 / correspondente de IA · online` |

**Visual:** portrait da AYA à direita, gradient mesh ao fundo, parallax sutil no scroll.

---

## 1.3 Proof Strip (tira horizontal)

**Função narrativa:** números rápidos que legitimam antes do leitor scrollar.

| # | Copy |
|---|---|
| 1 | `+ 3 min de leitura` |
| 2 | `+ 8h BRT, toda manhã` |
| 3 | `+ 10 fontes globais · 3 fora da bolha US` |
| 4 | `+ 100% PT-BR` |
| 5 | `+ Deep dive + 3 quick finds` |

---

## 1.4 Meet AYA (2 colunas: portrait + texto)

**Função narrativa:** humanizar a persona. Transformar a AYA de feature em personagem.

| Slot | Copy |
|---|---|
| Eyebrow | `// Conheça sua correspondente` |
| Título (serif) | `Ela não é humana. Mas tem critério.` |
| Blockquote | `"Eu não amplifico o que já está alto. Eu filtro pelo que você realmente vai querer saber amanhã."` |
| Body 1 | `A AYA é uma persona de IA rodando no Gemini 2.5 Flash. Toda manhã ela escaneia 10 fontes globais — Reddit, HackerNews, SCMP Tech, Rest of World, TechNode, Lobsters, arXiv, e mais — e aplica um editorial framework de 5 steps pra encontrar o que vale a pena ler.` |
| Body 2 | `Ela usa IA como lente, não como tópico. Ela se importa com o "so what?" — a coisa que você não podia fazer ontem e agora pode. Ela filtra sem dó contra hype, notícia reciclada e anúncio genérico de funding.` |
| Stat 1 | `10` / `Fontes globais / dia` |
| Stat 2 | `3` / `Veículos não-ocidentais` |
| Stat 3 | `5` / `Filtros editoriais` |
| Portrait caption | `> FIELD REPORT #042 / transmitindo das fontes: HN · Reddit · SCMP · Rest of World · TechNode · Lobsters · arXiv` |
| Portrait live badge | `● LIVE` |

---

## 1.5 Live Preview (email mockup)

**Função narrativa:** "mostre, não conte". O leitor vê literalmente como a edição chega.

| Slot | Copy |
|---|---|
| Eyebrow | `// Por dentro do daily scout` |
| Título (serif) | `É assim que ela chega na sua inbox.` |
| Sub | `Um deep dive. Três quick finds. Uma seção radar. Toda manhã às 8h BRT. Sem scroll-bait — só o que muda algo.` |
| Preview chrome | `inbox · aya@daily-scout` |
| Preview meta line | `> FIELD REPORT #001 · 11 fontes · 282 posts → 8 achados` |
| Preview subject | `Copilot insere anúncios em pull requests de desenvolvedores` |
| Preview byline | `AYA · 30/03/2026 · 3 min de leitura` |
| Section label 1 | `🎯 ACHADO DO DIA` |
| Body deep dive | `Um PR bot patrocinado começou a postar sugestões pagas dentro de pull requests no GitHub — monetizando o fluxo do desenvolvedor sem consentimento explícito. Não é um experimento isolado: a monetização do espaço cognitivo do dev está saindo do IDE e entrando no próprio workflow de code review. Se você mantém repos open source, vale conferir policies antes do próximo PR.` |
| Section label 2 | `⚡ QUICK FINDS` |
| Quick find 1 | `Anthropic expande Claude pra enterprise coding. Pricing agressivo contra Copilot — sinal de que o segmento vai ter guerra de margem.` |
| Quick find 2 | `SCMP: Alibaba fecha parceria com state labs em modelo multimodal. Sinal pra quem monitora o eixo China-tech soberano.` |
| Quick find 3 | `Rust no kernel Linux 6.x — merge de drivers GPU em Rust aprovado. Validação estrutural, não hype.` |
| Edition footer | `Field report #001 · publicado em 30/03/2026` |
| Read link | `Ler edição completa →` |

**Visual:** card com rotateX 4° (se endireita no hover).

---

## 1.6 Editorial Framework (pipeline horizontal)

**Função narrativa:** apresentar o método como moat — "não é só uma newsletter, é um processo".

| Slot | Copy |
|---|---|
| Eyebrow | `// O filtro de 5 steps` |
| Título | `Não é mais um digest de notícias de IA. É um editorial framework de verdade.` |
| Sub | `A maioria das newsletters de IA amplifica o que viralizou. A AYA roda cada candidata por um pipeline de 5 steps antes de qualquer coisa chegar na sua inbox. Se não passa, não sobe.` |

### Pipeline steps

| # | Nome | Descrição |
|---|---|---|
| 01 | `AI Gate` | `A matéria tem ângulo de IA? Se não tem, está fora — sem exceção.` |
| 02 | `Critérios` | `Precisa passar em 2 de 3: acionável, market signal, ou afeta workflows.` |
| 03 | `Anti-Signal` | `Funding genérico, notícia requentada, crypto-sem-IA → corte duro.` |
| 04 | `Ranking` | `Z-score de tração + recency decay + peso editorial.` |
| 05 | `Teste Final` | `"Sabia que agora dá pra...?" Se o complemento não fecha, sai.` |

---

## 1.7 Differentiators (3 cards)

**Função narrativa:** resposta direta à pergunta "por que eu assinaria isso e não outra?"

| Slot | Copy |
|---|---|
| Eyebrow | `// Por que o Daily Scout é diferente` |
| Título | `Três coisas que a maioria das newsletters de IA não faz.` |

### Card 1 — IA como lente
- **Ícone:** ◆
- **Título:** `IA como lente, não como tópico.`
- **Body:** `A maioria cobre "notícia de IA". A AYA cobre tech inteiro através do AI angle. Security, hardware, infra, policy — se tem ângulo de IA relevante, você vê. Se não tem, não passa no corte.`

### Card 2 — Perspectiva global
- **Ícone:** ⟡
- **Título:** `Perspectiva global.`
- **Body:** `Das 10 fontes monitoradas, 3 são geográficas — SCMP Tech, Rest of World, TechNode. Você enxerga a IA na Ásia e no Global South que os feeds US-centric ignoram.`

### Card 3 — Voz
- **Ícone:** ◈
- **Título:** `A Aya tem voz.`
- **Body:** `Não é um digest anônimo. A AYA escreve com persona editorial consistente — factual, sem hype, contexto primeiro. Ela explica o que algo é e por que importa. Ela não amplifica noise.`

---

## 1.8 Archive Teaser (3 cards)

**Função narrativa:** prova de que existe e tem backlog.

| Slot | Copy |
|---|---|
| Eyebrow | `// Field reports` |
| Título | `Uma amostra do que leitores anteriores receberam.` |

### Card #001
- `FIELD REPORT #001` / `Ataque de supply-chain atinge 23 mil+ repos no GitHub.` / `Um commit malicioso em tj-actions/changed-files expôs secrets de CI/CD. Por que isso importa além do CVE.` / `30/03/2026 · 3 min de leitura →`

### Card #003
- `FIELD REPORT #003` / `Copilot coloca anúncios dentro de pull requests.` / `Monetização sai do IDE e entra no code review. O que isso significa pra maintainers e pra policy de open source.` / `02/04/2026 · 3 min de leitura →`

### Card #007
- `FIELD REPORT #007` / `Modelo multimodal da Alibaba aparece.` / `Cobertura via SCMP sobre a parceria com state labs que a maior parte dos feeds ocidentais deixou passar. Por que o eixo China-tech ainda importa.` / `08/04/2026 · 3 min de leitura →`

| CTA | `Ver o arquivo completo →` |

---

## 1.9 Creator Strip

**Função narrativa:** humanizar a operadora por trás. Gera confiança e diferenciação (PM real, não content farm).

| Slot | Copy |
|---|---|
| Label | `// sobre a operadora` |
| Quote (serif italic) | `"Sou uma Product Manager que queria um tech briefing que eu realmente lesse. Então construí uma correspondente de IA pra escrever por mim. A AYA é o que acontece quando instinto de PM encontra LLM tooling."` |
| Sign | `— Isis Ramos · operadora · stack open-source` |

---

## 1.10 Final CTA

**Função narrativa:** última chance de capturar email antes do footer.

| Slot | Copy |
|---|---|
| Título (serif) | `Fique à frente em IA amanhã de manhã.` |
| Sub | `Um email por dia. Zero scroll-bait. Construído por uma PM, escrito por IA.` |
| Input placeholder | `voce@empresa.com` |
| CTA | `Assinar grátis` |
| Note | `// sem spam · unsubscribe em 1 clique` |

---

## 1.11 Footer

| Coluna | Conteúdo |
|---|---|
| Brand | Logo + `Briefing de tech & IA com curadoria por IA, entregue toda manhã às 8h BRT.` |
| Produto | `Edições` · `Sobre a AYA` · `Arquivo Buttondown` |
| Operadora | `LinkedIn` · `GitHub (open source)` |
| Stack | `Gemini 2.5 Flash` · `Buttondown` · `GitHub Actions` |
| Bottom line | `© 2026 AYA · Daily Scout` · `correspondente: aya v0.1 · pipeline: editorial v5.3` |

---

# 2. Archive (`/archive/`)

**Narrative arc:** `Contexto (arquivo) → Filtro → Lista → CTA de arquivo completo → CTA de assinatura`

## 2.1 Nav
Mesma da landing, mas com "Edições" marcado como active.

## 2.2 Page Header

| Slot | Copy |
|---|---|
| Eyebrow | `// Arquivo de field reports` |
| Título | `Toda edição, desde o início.` |
| Sub | `Toda manhã desde março de 2026, a AYA filtra ~300 histórias de tech & IA até chegar em 5. Abaixo está o field log — o deep dive de cada edição, com link pra ler o relatório completo.` |

## 2.3 Filter Bar

| Slot | Copy |
|---|---|
| Label | `Filtrar por ângulo:` |
| Chips | `Todas` · `AI infra` · `Security` · `Dev tools` · `Global` · `Product` |

> ⚠️ **Nota:** filtros atualmente são visuais apenas (sem JS de filtragem).

## 2.4 Edições (lista)

Estrutura de cada card: `#NUM + data` / `título` / `excerpt` / `tag de categoria + 3 min de leitura + fontes`

| # | Data | Título | Tag |
|---|---|---|---|
| #001 | 30 MAR 2026 | Ataque de supply-chain atinge 23 mil+ repos no GitHub. | SECURITY |
| #003 | 02 ABR 2026 | Copilot coloca anúncios dentro de pull requests. | DEV TOOLS |
| #005 | 05 ABR 2026 | Anthropic parte pra cima do enterprise coding. | AI INFRA |
| #007 | 08 ABR 2026 | Modelo multimodal da Alibaba aparece. | GLOBAL |
| #010 | 12 ABR 2026 | Rust entra nos drivers de GPU do kernel Linux. | AI INFRA |
| #014 | 16 ABR 2026 | Voice agents comem o papel do SDR sem fazer barulho. | PRODUCT |

## 2.5 Buttondown CTA (mid-page)

| Slot | Copy |
|---|---|
| Título | `Quer mais?` |
| Sub | `O arquivo completo vive no Buttondown — todo field report que a AYA já publicou.` |
| CTA | `Ver arquivo completo no Buttondown →` |

## 2.6 Inline Subscribe (final)

| Slot | Copy |
|---|---|
| Título | `Não leia o arquivo. Receba a próxima.` |
| Sub | `Edição nova toda manhã às 8h BRT. Grátis, 3 min, sem spam.` |
| CTA | `Assinar grátis` |
| Note | `// unsubscribe em 1 clique` |

## 2.7 Footer
`© 2026 AYA · Daily Scout · correspondente v0.1` + links: `Home · Sobre · GitHub · Operadora`

---

# 3. About (`/about/`)

**Narrative arc:** `Identidade (AYA) → Princípios → Pipeline detalhado → Fontes (defensibilidade) → Operadora humana → Stack técnico → CTA`

## 3.1 Nav
Com "Sobre" active.

## 3.2 Page Header

| Slot | Copy |
|---|---|
| Eyebrow | `// A correspondente` |
| Título | `Ela é a AYA. Uma correspondente que não é humana.` |
| Sub | `A AYA é uma persona de IA com linha editorial, voz e ponto de vista. Toda manhã ela roda um framework de 5 steps em 10 fontes globais e publica um relatório. Aqui está como funciona — e quem construiu ela.` |

## 3.3 AYA Bio (2 colunas: portrait sticky + texto rolando)

### 3.3.1 Identity card (portrait + specs)
```
// identity.json
name: AYA
version: v0.1
role: correspondente de IA
model: Gemini 2.5 Flash
temperature: 0.0
framework: editorial v5.3
frequency: diária · 8h BRT
language: PT-BR
voice: factual, no hype
status: transmitindo
```

### 3.3.2 Bio H1 — "Ela não amplifica. Ela filtra."
- **Body 1:** `A maioria das newsletters de IA são amplificadores. Pegam o que deu trending no HN ou no Twitter e reembalam com adjetivos mais pesados. Não é isso que a AYA faz.`
- **Body 2:** `Toda manhã ela puxa ~300 histórias candidatas de 10 fontes e roda cada uma por um pipeline editorial. Quando você abre o email, ela já disse "não" pra cerca de 295 coisas. O que sobra, vale seu tempo — um deep dive, três quick finds e uma seção radar de tendências em formação que valem acompanhar.`
- **Quote:** `"Não me importa se foi trending. Me importa se mudou o que você pode fazer amanhã."`

### 3.3.3 Bio H2 — "Os princípios editoriais"
- **Intro:** `A AYA opera por um conjunto fixo de princípios. Eles definem o que entra na edição e o que fica de fora. Não são preferências fracas — são guardrails estruturais embutidos no pipeline.`

#### Tabela de princípios

| Princípio | Descrição |
|---|---|
| `AI Gate` | Todo item precisa ter ângulo de IA. Sem ângulo, sem entrada. Sem exceção — nem pra matérias com tração alta. |
| `So-what test` | "Sabia que agora dá pra...?" — se o complemento não fecha, a história não é acionável e sai. |
| `Tração ≠ relevância` | Score alto no HN é tração, não é critério. Só tração não garante slot na edição. |
| `Factual over hype` | A AYA explica o que algo é e por que importa. Ela nunca converte incerteza em fato. Um regex de hype-pattern + auto-retry valida cada output. |
| `Anti-signal` | Rodadas genéricas de funding, notícia reciclada, pricing de consumer sem ângulo de IA, crypto-sem-IA → corte duro, sem review. |

### 3.3.4 Bio H3 — "O pipeline de 5 steps"
- **Intro:** `Toda história que a AYA considera passa pela mesma sequência de 5 steps. Se falha em qualquer step, sai — sem override, sem "interessante o suficiente pra incluir mesmo assim". Essa é a parte que a maioria das newsletters não tem, e é por isso que a edição fica enxuta.`
- **Step 1 — AI Gate:** `A história precisa ter ângulo de IA substantivo. Não é "tem AI no título". É ângulo de verdade.`
- **Step 2 — Critérios:** `Precisa passar em 2 de 3 testes: acionável pro leitor, indicador de mercado relevante, ou afeta workflows diretamente.`
- **Step 3 — Anti-signal scan:** `Sinaliza e corta conteúdo reciclado, genérico ou anti-pattern (funding sem implicação de produto, etc.).`
- **Step 4 — Ranking:** `Z-score de tração + recency decay + peso editorial. Aqui é onde a tração finalmente entra — como tiebreaker, não como gate.`
- **Step 5 — Teste de completude:** `"Sabia que agora dá pra...?" Se a AYA não consegue terminar essa frase com uma capability específica e afiada, a história não pertence.`

## 3.4 Sources (grid 2 colunas)

| Slot | Copy |
|---|---|
| Eyebrow | `// fontes monitoradas` |
| Título | `10 fontes globais. 3 intencionalmente fora da bolha US/EU.` |
| Sub | `A maioria das newsletters de IA bebe do mesmo lago — US-centric, Valley-first. O mix de fontes da AYA é deliberadamente diferente. Perspectiva global não é feature. É o default.` |

### Cards das 10 fontes

| Badge | Nome | Tipo | Descrição |
|---|---|---|---|
| HN | HackerNews | TECH HUB · TRACTION SIGNAL | Front page + "Show HN" — pulso forte de tech, mas enviesado por tração pra tópicos ocidentais. |
| R | Reddit | COMMUNITIES · r/MachineLearning, r/programming, r/LocalLLaMA | Sentimento de practitioner — o que engenheiros realmente estão penando, não só o que estão lançando. |
| TC | TechCrunch | STARTUP · FUNDING SIGNAL | Indicador de mercado sobre onde o funding de IA está fluindo — usado com cuidado, a maioria não passa no AI Gate. |
| L | Lobsters | TECH · HIGH SIGNAL-TO-NOISE | Alternativa menor e mais curada ao HN. Mais forte pra systems, infra e histórias de nicho dev. |
| **SCMP** ⚡ | SCMP Tech | GEOGRAPHIC · HONG KONG / CHINA | Cobertura de China-tech que os feeds ocidentais perdem. Fonte de referência pra movimentos de IA da Alibaba, DeepSeek e Baidu. |
| **RoW** ⚡ | Rest of World | GEOGRAPHIC · GLOBAL SOUTH | Jornalismo de tech fora do eixo US-EU. Excelente pra aplicações de IA em emerging markets. |
| **TN** ⚡ | TechNode | GEOGRAPHIC · CHINA STARTUPS | Cobertura de startups chinesas em ground-level — onde os experimentos de produto acontecem antes de aparecer no radar ocidental. |
| aX | arXiv | RESEARCH · CS.AI, CS.LG, CS.CL | Preprint server de pesquisa em AI/ML. Filtrado por papers com implicação prática ou estratégica. |
| GH | GitHub Trending | OSS SIGNAL · BUILDING TODAY | O que está ganhando estrelas essa semana. Frequentemente traz tools antes delas chegarem nas newsletters. |
| PH | Product Hunt | PRODUCT · DAILY LAUNCHES | Lançamentos diários filtrados por produtos de IA com diferenciação real, não só wrappers. |

> ⚡ = badge roxo (geographic/geo-tagged) — diferenciador visual das fontes não-ocidentais.

## 3.5 Creator (2 colunas: card + texto)

### 3.5.1 Operator profile card
```
// operator.profile
Isis Ramos
PRODUCT MANAGER · BUILDER

Foco:        Produtos AI-powered, sistemas editoriais, automação
Construindo: Pay and Party (tech-powered events) · AYA
Links:       LinkedIn · GitHub
Escreve:     Substack — PM encontra AI tooling
```

### 3.5.2 Bio da operadora

| Slot | Copy |
|---|---|
| Eyebrow | `// A operadora` |
| Título | `Construído por uma PM, escrito por IA.` |
| Body 1 | `Eu queria um tech briefing que eu realmente lesse — algo com julgamento editorial, não só uma lista de links. A maioria das newsletters de IA falha nesse bar porque otimiza pra engagement, não pra relevância. Então construí a minha.` |
| Body 2 | `A AYA é o resultado. Ela é um experimento de até onde dá pra empurrar AI tooling quando é embrulhado em product thinking — linha editorial clara, framework versionado, feedback loop real, retrospectives estruturadas. O stack é todo open source. A parte interessante não é a tech — é o processo de tratar um output de IA como produto e iterar em cima.` |
| Body 3 | `Se você se importa com IA como ferramenta pra ganhar leverage (não só como tópico pra ler sobre), provavelmente é pra você.` |

## 3.6 Stack (diagrama vertical, 8 stages)

| Slot | Copy |
|---|---|
| Eyebrow | `// O stack` |
| Título | `Open source. Zero human in the loop.` |
| Sub | `Toda edição é produzida end-to-end sem intervenção manual. A única decisão humana está no framework em si — que é versionado, testado e publicado.` |

### Linhas do stack

| Stage | Nome | Descrição | Tech |
|---|---|---|---|
| 01 · Collect | Ingestão de fontes | 10 fontes · Reddit, HN, RSS, APIs | Python |
| 02 · Filter | Pipeline de pre-filter | z-score + recency decay · 300 → 40 candidatos | Python / numpy |
| 03 · Curate | Editorial framework v5.3 | AI Gate · Critérios · Anti-signal · Ranking · Teste de completude | Gemini 2.5 Flash |
| 04 · Validate | Tone validator | regex de hype-pattern + auto-retry | Python |
| 05 · Render | Template de email | HTML responsivo, dark theme, preflight-tested | Jinja2 |
| 06 · Deliver | Envio da newsletter | + post de distribuição no LinkedIn | Buttondown API |
| 07 · Feedback | Signal de 1 clique | 🔥 / 👍 / 😐 — loop de qualidade pra retrospectives | Apps Script + Sheets |
| 08 · Schedule | Cron diário | 8h BRT · deploys sem intervenção | GitHub Actions |

## 3.7 Final CTA

| Slot | Copy |
|---|---|
| Título | `Agora que você conheceu a AYA.` |
| Sub | `Comece a ler os field reports dela toda manhã às 8h BRT.` |
| CTA | `Assinar grátis` |
| Note | `// sem spam · unsubscribe em 1 clique` |

## 3.8 Footer
`© 2026 AYA · Daily Scout · correspondente v0.1 · pipeline editorial v5.3` + links.

---

# 🔍 Análise crítica da estrutura narrativa

## O que funciona bem

1. **Persona como espinha dorsal.** A AYA não é um gimmick — ela aparece em 3 camadas: hook (hero), humanização (Meet AYA), e defensibilidade (About). Isso é raro em newsletters B2C de tech.
2. **Show, don't tell, no lugar certo.** Live preview na landing (sec 1.5) entrega o produto antes de vender ele. Corta a resistência do "é mais uma newsletter".
3. **Editorial framework como moat.** O framework aparece 3 vezes com profundidade crescente: 5 steps visuais (landing) → tabela de princípios (about) → descrição passo-a-passo (about). Isso escala bem pra leitores mais/menos técnicos.
4. **Prova de consistência.** Archive com 6 edições reais com tags por ângulo legitima "isso de fato existe e tem curadoria".
5. **Human-in-the-loop ambíguo de propósito.** "Curadoria por IA, verificação por PM" no hero e "zero human in the loop" no about são aparentemente contraditórios — mas funcionam como signaling: a IA faz, a PM decide o framework. Isso é um ponto sutil.

## Riscos e pontos de atenção

### 🟡 Risco 1: Hero headline competindo com subtítulo
A headline `Uma correspondente de IA reportando da linha de frente do tech.` é elegante mas **não diz o benefício**. O benefício aparece só no sub ("signal, não noise, sem viés US-only"). Leitor de 3s não chega no sub.

**Blueprint de teste:** A/B entre a atual e uma variação mais benefit-driven tipo `O tech briefing que filtra hype e te dá só o que muda seu trabalho amanhã.` (perde poesia, ganha clareza).

### 🟡 Risco 2: Proof strip genérica
`300 → 5 itens/dia` e `pipeline 100% automatizado` são métricas de produto, não de benefício pro leitor. Funcionam pra tech audience, mas o ICP híbrido (broad + tech) pode não ressoar com a metade broad.

**Blueprint de teste:** substituir 1-2 itens por signals de leitura (`3 min de leitura`, `leitores em 4+ países`, `100% PT-BR`) ou outcomes (`usado por PMs de produtos de IA`, se der).

### 🟡 Risco 3: Creator strip muito enxuto na landing
A Isis aparece como quote curta. Pra um PM com background interessante, isso é subutilizado — a legitimidade do criador pode ser decisivo pra o skeptic. A página About resolve, mas exige ir pra outra página.

**Blueprint de teste:** expandir o creator strip da landing com 1 foto + 1 linha de credenciais (ex: "Product Manager em [empresa/produto], building Pay and Party").

### 🟡 Risco 4: Filter chips do archive são decorativos
Promessa implícita de filtragem que não cumpre. Pra PM, isso é dissonância cognitiva.

**Blueprint de decisão:** OU implementa o filtro (client-side, `data-tag` + show/hide), OU remove os chips e substitui por uma linha de contexto ("6 campos de ângulo: AI infra, security, dev tools, global, product, research").

### 🟡 Risco 5: About é denso pra quem não é tech
A seção "pipeline de 5 steps" + "princípios editoriais" + "sources grid" + "stack diagram" é 4 blocos densos em sequência. Pro leitor broad do ICP híbrido, é muito.

**Blueprint de mudança:** tornar o stack diagram collapsable (accordion default-closed) ou mover pra página separada `/how-it-works/`. About vira mais "sobre a AYA + a operadora", técnico vai pra uma página dedicada.

### 🟢 Risco 6: CTA stacking — 3 forms na mesma página
Landing tem form no hero + form no final CTA. About tem só 1 no final. Archive tem 2. Não é risco crítico, mas vale validar métricas: se o hero form domina, os outros são redundantes.

**Blueprint de teste:** instrumentar cada form com `name="email"` + UTM ou hidden field de origem (`source=hero_landing`, `source=final_landing`, etc.) pra medir onde conversão acontece e podar o que não performar.

### 🟡 Risco 7: Ausência de social proof externa
Nenhum testimonial, nenhum número de assinantes, nenhuma menção de empresa/publicação que leu. Pra newsletter nova, é aceitável — mas se já existe tração, vale adicionar.

**Blueprint (quando fizer sentido):** slot discreto entre "Differentiators" e "Archive teaser" do tipo `Lidos por PMs, founders e engineers em [X países / Y empresas]`.

---

# 🛠️ Blueprint de mudanças pontuais — checklist

Slots prontos pra edição rápida (baixo custo, alto impacto potencial):

| # | Slot | Arquivo | Mudança candidata |
|---|---|---|---|
| 1 | Hero headline | `index.html` linha ~1297 | A/B test: poético vs benefit-driven |
| 2 | Hero sub | `index.html` linha ~1302 | Reduzir de 2 linhas pra 1 (mais scan-friendly) |
| 3 | Proof strip | `index.html` linhas ~1339-1343 | Trocar 1-2 métricas técnicas por signals de leitura |
| 4 | AYA quote (Meet AYA) | `index.html` linha ~1373 | Testar quote alternativa mais direta |
| 5 | Differentiator 3 (voz) | `index.html` linhas ~1509-1511 | "A Aya tem voz" pode ser "Ela assina o que escreve" ou similar mais visual |
| 6 | Creator strip | `index.html` linhas ~1558-1564 | Expandir com mini-bio + foto inline |
| 7 | Final CTA headline | `index.html` linha ~1572 | Testar ação ("Receba amanhã cedo") vs estado ("Fique à frente") |
| 8 | Filter chips | `archive/index.html` linhas ~557-562 | Implementar ou remover |
| 9 | Stack diagram | `about/index.html` seção `<section class="stack">` | Avaliar mover pra accordion ou página separada |
| 10 | About CTA | `about/index.html` linha ~1096 | Testar versão mais específica de ação |

---

# 📌 Anotações sobre anglicismos

O copy mantém deliberadamente termos em inglês que já fazem parte do vocabulário tech-PT-BR:

**Mantidos em EN (core vocabulary):** `AI`, `framework`, `pipeline`, `signal`, `noise`, `hype`, `inbox`, `stack`, `field report`, `deep dive`, `quick finds`, `radar`, `open source`, `AI Gate`, `Anti-Signal`, `Ranking`, `So-what test`, `market signal`, `actionable`, `workflows`, `dev tools`, `IDE`, `code review`, `supply-chain`, `maintainer`, `unit economics`, `outbound`, `wrapper`, `traction`, `leverage`, `PM`, `operator`, `takes`, `trending`, `z-score`, `recency decay`, `editorial weight`, `tiebreaker`, `gate`, `HN score`, `auto-retry`, `preflight`, `cron`.

**Traduzidos:** ações (subscribe → assinar), conectivos, descrições genéricas, referências temporais, papéis (correspondent → correspondente, operator → operadora em alguns contextos).

**Híbrido aceito:** "AI Gate" (nome próprio, fica EN) mas "ângulo de IA" (IA em PT porque é substantivo comum).

---

*Gerado a partir da versão atual de `/site-v2/` em `2026-04-19`. Atualize este doc quando fizer mudanças estruturais.*
