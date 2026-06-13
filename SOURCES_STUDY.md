# Estudo de Fontes — AYA's Daily

> Análise do portfólio atual + proposta de expansão.
> Data: 2026-04-19 · Base: `sources_config.json` v5.3 · Framework editorial v5.3

---

## 1. Diagnóstico do portfólio atual

### 1.1 Fontes ativas hoje (11 habilitadas, 1 validada)

| Categoria | Fonte | Weight | Região | Tipo de sinal |
|-----------|-------|--------|--------|---------------|
| Community | HackerNews | 1.2 | US | Engagement dev/founder |
| Community | TechCrunch | 1.1 | US | Tech/startup journalism |
| Community | Reddit (13 subs) | 1.0 | Global | Engagement de nicho |
| Community | Lobsters | 0.9 | US | Curadoria dev |
| Research T1 | arXiv (AI/LG/CL) | 1.3 | Global | Paper primário |
| Research T1 | HuggingFace Papers | 1.3 | Global | Paper com tração ML |
| AI Lab | Anthropic Blog | 0.8 | US | Releases + research |
| AI Lab | OpenAI Blog | 0.8 | US | Releases + research |
| AI Lab | DeepMind Blog | 0.7 | US | Releases + research |
| Geographic | SCMP Tech | 0.9 | Ásia | Tech journalism China/HK |
| Geographic | Rest of World | 0.9 | Global South | Tech journalism periferia |
| Geographic | TechNode | 0.8 | Ásia | Tech journalism China |

**Volume estimado:** ~300 itens/dia → pre-filter reduz para 40 → Aya seleciona ~5–7.

### 1.2 Mapa de cobertura — o que está forte

- **Pesquisa primária (T1):** arXiv + HF Papers dão excelente cobertura de papers com filtro de comunidade. Peso 1.3 (maior do sistema) está calibrado.
- **Community engagement anglófono:** HN + Reddit + Lobsters capturam praticamente todo ruído/sinal dev em inglês.
- **Três big labs dos EUA:** OpenAI, Anthropic, DeepMind — cobertura redundante do eixo US/UK.
- **Ásia-China:** SCMP + TechNode dão duas lentes distintas (HK vs mainland China).

### 1.3 Gaps identificados

Olhando o portfólio como um mapa, as lacunas são:

**Gap 1 — Europa praticamente ausente**
Não há fonte europeia. Sem Mistral/Aleph Alpha/Stability via canal primário, sem cobertura do AI Act e regulação europeia em primeira mão, sem perspectiva editorial UK/Alemã/Francesa. O eixo "US/EU anglófono" que a PRODUCT.md declara combater é, na prática, US-only.

**Gap 2 — China tech fora do mainstream jornalístico**
SCMP e TechNode são cobertura em inglês *sobre* China. Falta sinal direto de labs/comunidades chinesas: papers do Baidu/Alibaba/ByteDance, releases do Qwen/DeepSeek/Kimi, discussões no ecossistema WeChat/Zhihu (via proxy em inglês).

**Gap 3 — AI Labs de segunda camada**
Só as 3 maiores americanas. Faltam Meta AI (FAIR), Mistral, Cohere, Stability, xAI, Nvidia Research, Microsoft Research, Apple ML — todos com peso real em pesquisa ou produto.

**Gap 4 — Developer tooling e aplicação**
GitHub Trending, Product Hunt, Hugging Face model releases (não só papers). O pipeline capta *discussão* sobre ferramentas (HN, Lobsters) mas não o *lançamento* delas.

**Gap 5 — Regulação e policy**
Zero fonte dedicada. Depende de pegar por reverberação em TechCrunch/HN. Anti-signal do framework diz "regulation" é categoria válida, mas o intake é fraco. AI Act, executive orders, FTC, EU AI Office, UK AISI — tudo por tabela.

**Gap 6 — Enterprise/mercado**
The Information, Bloomberg Tech, Reuters Technology — cobertura de decisão corporativa e M&A. Hoje o Daily Scout só pega isso quando vira trending no HN, ou seja, tarde e enviesado para ângulo dev.

**Gap 7 — Latam (!)**
A newsletter é escrita por uma correspondente em português, para um público que inclui brasileiros, mas não há fonte Latam. Nem Rest of World é suficiente — sua cobertura Latam é esparsa. Isso é um buraco editorial e estratégico.

**Gap 8 — Signal de prática (não de especulação)**
Papers + community + blogs cobrem "o que foi feito / o que pode ser feito". Falta fonte de "o que está efetivamente sendo usado" em produção — engineering blogs de empresas (Netflix Tech, Stripe, Shopify, Figma), changelogs, status pages de modelos.

**Gap 9 — Voz editorial independente**
Hoje a curadoria depende de agregadores (HN, Reddit) ou veículos (TechCrunch). Faltam analistas individuais fortes — Simon Willison, Ethan Mollick, Benedict Evans, Stratechery, Gergely Orosz. Essa é a camada que *contextualiza*, e é exatamente o que a Aya produz — mas ela está trabalhando sem input de pares.

### 1.4 Vieses estruturais do portfólio

- **Linguagem:** 100% das fontes publicam em inglês. Nenhum feed em português, espanhol, francês, alemão ou chinês.
- **Modo de sinal:** ~70% do peso vem de *engagement* (HN/Reddit/Lobsters/TechCrunch) + 30% primário (arXiv/HF/blogs). Risco de echo chamber americano se engagement dominar empate.
- **Geographic cap (30%) protege contra ova-representação**, mas só depois de coletar. O problema está no intake — não há do que capar fora do eixo anglófono.
- **Blogs de lab oficiais** têm bias de marketing (mitigado pelo STEP 1.5, mas peso 0.7–0.8 mostra que o sistema já reconhece isso).

---

## 2. Framework de avaliação para novas fontes

Antes de listar candidatas, critério para entrar/ficar de fora. Uma fonte merece entrar no Daily Scout se passa em **pelo menos 3 de 5**:

1. **Sinal diferenciado** — cobre algo que as 11 fontes atuais não cobrem (geografia, nicho, camada de stack, tipo de ator).
2. **Latência aceitável** — feed RSS ou API pública, atualização ≥ diária, sem paywall hard que quebre link-out.
3. **Densidade AI** — ≥ 30% dos itens têm ângulo AI, ou é fonte geográfica/regulatória onde o gap justifica peso menor.
4. **Autoridade editorial** — autor/publicação tem credibilidade verificável (não aggregator farm, não content marketing).
5. **Compatibilidade com o pipeline** — tem timestamp, tem link direto, não requer scraping frágil, tolera fetch diário.

**Anti-critérios (descartar mesmo se passa em 3):**
- Newsletter gatekeeped (Substack-only, sem RSS público)
- Conteúdo majoritariamente de opinião/hot-take sem reporting
- Overlap > 80% com fonte já existente (seria só amplificar o mesmo sinal)
- Paywall que impede o leitor de clicar no link-out da edição

---

## 3. Candidatas recomendadas — priorizadas

### 3.1 Alta prioridade (fecham gaps críticos)

#### **The Information** (enterprise/mercado) — Gap 6
- **Por quê:** cobertura de decisão corporativa de AI labs e big tech, ângulo mercado.
- **Acesso:** RSS público de headlines; paywall no full-text.
- **Risco:** paywall quebra experiência de clique — usar só como *signal de tema* no pre-filter, não como link primário.
- **Peso sugerido:** 1.0

#### **Simon Willison's Weblog** (voz editorial independente) — Gap 9
- **Por quê:** o melhor curador individual de AI em inglês. Densidade AI ~95%. Cita primary sources, testa hands-on.
- **Acesso:** RSS público em simonwillison.net.
- **Peso sugerido:** 1.1 (alto — é signal pré-filtrado por editor que a Aya respeitaria).

#### **Hugging Face Blog + Model Releases** (developer tooling/release) — Gap 4
- **Por quê:** HF Papers já está. Falta o lado de *release* (novos modelos, datasets, spaces). É o canal onde release acontece antes de virar paper.
- **Acesso:** `huggingface.co/blog/feed.xml`.
- **Peso sugerido:** 1.0

#### **Meta AI Research / AI.meta.com** (AI Lab tier-2) — Gap 3
- **Por quê:** FAIR + Llama são top-tier. A ausência é notável.
- **Acesso:** RSS em `ai.meta.com/blog/rss` (verificar).
- **Peso sugerido:** 0.8 (mesmo nível dos outros labs).

#### **MIT Technology Review — AI section** (regulação/policy/ética) — Gap 5
- **Por quê:** jornalismo com profundidade em AI, inclui regulação e implicação social.
- **Acesso:** RSS `technologyreview.com/feed`.
- **Peso sugerido:** 1.0

### 3.2 Média prioridade (enriquecimento temático)

#### **Stratechery (free posts) + Ben Thompson** (análise mercado) — Gap 9
- **Por quê:** análise de estratégia de big tech. Densidade AI menor, mas quando entra é peso-pesado.
- **Acesso:** RSS parcial (só free posts) via `stratechery.com/feed`.
- **Peso sugerido:** 0.9 — aplicar anti-signal contra posts pagos truncados.

#### **Ethan Mollick — One Useful Thing** (voz editorial — uso prático AI) — Gap 9
- **Por quê:** uso aplicado de AI em trabalho e educação. Público exato da Aya.
- **Acesso:** Substack com RSS público.
- **Peso sugerido:** 0.9

#### **Qwen / DeepSeek / Moonshot blogs ou GitHub releases** (China primary) — Gap 2
- **Por quê:** os labs chineses relevantes não aparecem via SCMP/TechNode no dia do release. É necessário feed direto.
- **Acesso:** GitHub Releases RSS dos repos oficiais (Qwen, DeepSeek-V3, Kimi). Alternativa: blog da Alibaba Cloud.
- **Peso sugerido:** 0.9
- **Caveat:** alto volume de ruído técnico — pode exigir filtro de category dedicado.

#### **Nvidia Research Blog** (AI Lab — hardware/infra) — Gap 3
- **Por quê:** camada infra-AI que os outros labs não cobrem. Releases de CUDA, inference frameworks, chips.
- **Acesso:** `blogs.nvidia.com/feed`.
- **Peso sugerido:** 0.7 (marketing-heavy, aplicar STEP 1.5).

#### **Product Hunt — AI tag** (release de ferramentas aplicadas) — Gap 4
- **Por quê:** feed de produtos AI novos, enviesado consumer/SaaS.
- **Acesso:** RSS por tag.
- **Peso sugerido:** 0.7
- **Caveat:** muito launch marketing — depender de STEP 1.5 e anti-signal "genérico".

#### **Folha Mercado / Valor Tech / The Brief Latam** (Latam) — Gap 7
- **Por quê:** fechar o gap Latam. Cobertura em português/espanhol de AI no Brasil, México, Argentina.
- **Acesso:** variável — Folha tem RSS, Valor é paywall. Alternativa: Núcleo Jornalismo (nucleo.jor.br), Rest of World Latam tag.
- **Peso sugerido:** 0.9
- **Caveat:** item em PT entra no pipeline com título em português — requer teste de como a Aya trata na curadoria.

### 3.3 Baixa prioridade / experimental

#### **GitHub Trending (daily, filtered by AI topics)** — Gap 4
- **Por quê:** pulso de o que está sendo adotado em OSS.
- **Acesso:** scraping ou API do GitHub com filtro por topic `ai`, `llm`, `machine-learning`.
- **Peso sugerido:** 0.6 — sinal raso (stars ≠ relevância).

#### **Bloomberg Technology** — Gap 6
- **Por quê:** overlap com Information + TechCrunch. Só se Information for paywall-bloqueada.

#### **Gergely Orosz — The Pragmatic Engineer** — Gap 9
- **Por quê:** engineering práticas, perspectiva europeia. Densidade AI ~40%.
- **Acesso:** Substack, RSS parcial.
- **Peso sugerido:** 0.8

#### **Engineering blogs (Stripe, Figma, Shopify, Netflix)** — Gap 8
- **Por quê:** cobre "AI em produção real". Densidade AI baixa (10–20%), mas quando entra é ouro.
- **Formato:** agrupar num único source `engineering_blogs` com RSS composto.
- **Peso sugerido:** 0.7
- **Caveat:** exige classificação no pre-filter pra não inundar com posts não-AI.

---

## 4. Recomendação de próximo passo

Não adicionar tudo de uma vez — expansão tem custo (ruído, pre-filter precisa de re-tuning, `geographic_max_pct` e `max_per_source_pct` podem precisar revisão).

**Sugestão de rollout em 3 ondas:**

| Onda | Fontes | Ganho esperado | Custo |
|------|--------|----------------|-------|
| **1ª — Quick wins** | Simon Willison · HF Blog · Meta AI · MIT Tech Review | Fecha Gap 9 e reforça Gap 3 e 5. Baixo risco técnico (todos RSS estáveis). | 4 novas fontes, ~60–80 itens/dia extra |
| **2ª — Geografia e análise** | Mistral blog · Qwen/DeepSeek releases · Ethan Mollick · Stratechery | Ataca Gap 1 (Europa) e Gap 2 (China primary). Exige revisitar `geographic_max_pct`. | 4 novas fontes, refatoração leve do pre-filter |
| **3ª — Experimentais** | Folha/Núcleo Latam · Product Hunt AI · Engineering blogs bundle | Fecha Gap 7 e 4/8. Alto risco de ruído — requer monitoramento de 2–3 edições antes de manter. | 3 fontes, testar e podar |

**Antes de qualquer onda:**
1. Validar feed URL de cada candidata (usar `feedparser` no REPL).
2. Medir densidade AI em 7 dias de amostra antes de decidir peso definitivo.
3. Definir se `geographic_max_pct` precisa segmentar por região específica (Europa vs Ásia vs Latam) em vez de um teto único.

**Questões em aberto para discussão editorial:**
- Qual é o limite aceitável de itens em PT/ES entrando na coleta? A Aya hoje cura material EN e escreve em PT-BR. Fontes Latam em PT mudam essa premissa.
- `The Information` e `Stratechery` têm paywall parcial — aceitar como *signal-only* (entram no pre-filter mas Aya precisa de instrução específica pra não selecionar como main_find sem fallback)?
- Worth abrir slot fixo "voice lane" no output (1 item/dia de analyst independente) ou deixar competir no pool geral?

---

*Documento de estudo — não implementa mudanças. Próximo artefato seria PR de config quando houver decisão sobre onda 1.*
