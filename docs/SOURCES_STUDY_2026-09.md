# Estudo de Fontes — Atualização 2026-09

> Complementa `SOURCES_STUDY.md` (19/abr/2026). Não repete o que já foi decidido — mapeia os gaps que continuam abertos com pesquisa online validada em 2026-09-08. Base: `sources_config.json` (22 fontes habilitadas), framework de avaliação da seção 2 do estudo original (5 critérios de entrada, 4 anti-critérios — reaplicado sem alteração).
>
> **Metodologia:** cada candidata foi checada com `curl` contra o feed real (status HTTP, content-type, itens recentes, densidade de IA nos títulos). "Validado" abaixo significa que a URL respondeu 200 com XML/Atom real e itens datados de setembro/2026 — não é uma citação de blog post sobre a fonte.

---

## 0. Antes de pesquisar fontes novas: as 5 fontes ociosas

Investigação paralela (leitura de `pre_filter.py`, `sources_config.json`, `dashboard.py` e `debug/edition_*_items.json`) mostrou que **não é um problema único** — são 3 causas distintas, e importa saber qual é qual antes de adicionar mais fontes que podem cair na mesma armadilha:

| Fonte | Causa raiz | Evidência |
|---|---|---|
| `anthropic_blog` | **Feed morto.** `anthropic.com/feed` → 404. Sem link `rel=alternate` de RSS na página atual — a Anthropic parece ter descontinuado o RSS público. `_fetch_rss` engole a exceção e retorna `[]` silenciosamente; zero itens chegam ao pré-filtro, sempre. | Confirmado agora via curl: 404 em `/feed`, `/rss.xml`, `/news/rss.xml`; sem autodiscovery no HTML. |
| `qwen_blog` | **Feed abandonado.** Responde 200, mas o post mais recente é de 23/set/**2025** — quase 1 ano parado. Com `recency_hours=24` (corte duro) + `recency_decay_constant=8`, um item de 300+ dias tem `recency_score ≈ 0` sempre. | Confirmado agora via curl: `pubDate` mais recente no feed atual é 2025-09-23. |
| `ethan_mollick` | **Cadência baixa + filtro de recência rígido.** Feed vivo (post mais recente 31/ago/2026), mas publica ~1x a cada 2-4 semanas. `recency_hours=24` é corte duro; mesmo dentro da janela, `decay_constant=8` já penaliza pesado (`exp(-20/8)=0.08`). A fonte quase nunca chega "fresca" ao pool. | Amostra de 8 edições em `debug/edition_0{93-99}_items.json`. |
| `simon_willison`, `stratechery` | **Não é bug de pré-filtro — é viés de curadoria.** Ambos chegam ao pool de 40 itens regularmente (Simon: 7/8 edições amostradas; Stratechery: 6/8), com peso alto (1.1 e 0.9). Mas em 76 edições registradas, cada um foi *selecionado* como item final só 1 vez. | Mesma amostra + `memory/editions.jsonl`. Para `stratechery` isso é parcialmente intencional (`_comment` em `sources_config.json:130` já instrui a Aya a tratar como signal-only); para `simon_willison` não há razão documentada — vale revisar o prompt de curadoria da Aya. |

**Implicação prática para a pesquisa abaixo:** ao aprovar uma candidata nova de baixo volume/cadência esporádica (blogs de lab, analistas individuais), validar não só se o feed existe, mas se ele *ainda está vivo* (post recente) — um feed morto ou parado é indistinguível de "fonte fraca" no dashboard depois de 30 edições, mas o fix é trivial (trocar URL) enquanto o outro exige repensar peso/critério.

**Atualização 2026-09-08 — implementado:** investiguei as duas URLs a fundo (ver `sources_config.json`, comentários em `anthropic_blog` e `qwen_blog`). Nenhuma tem RSS oficial vivo hoje — Anthropic não publica feed público (só sitemap.xml sem estrutura de item), e o blog do Qwen migrou pra uma SPA em `qwen.ai/research` sem RSS, com GitHub Releases também não usado pelos repos principais. Decisão: **ambas desabilitadas** (`enabled: false`) em vez de depender de feed não-oficial de terceiro. Reavaliar se algum dos dois expuser RSS oficial no futuro.

**Recomendação restante (não implementada, fora do escopo desta pesquisa):**
2. Adicionar um alerta simples de "fonte com 0 itens fetched em N dias" — teria pego os 2 feeds mortos sem esperar 30 edições de dashboard.
3. `ethan_mollick`: considerar `recency_hours` maior ou piso mínimo de score por fonte de baixa cadência, em vez de decay geométrico puro.
4. `simon_willison`: revisar se o prompt/critério de curadoria da Aya tem viés implícito contra posts de análise/opinião — está fora do escopo de fontes, é comportamento de seleção.

---

## 1. Gap 3 — AI Labs de segunda camada

Faltam: Cohere, Stability, xAI, Nvidia Research, Microsoft Research, Apple ML.

| Candidata | Feed | Status validado | Densidade IA | Peso sugerido | Risco/caveat |
|---|---|---|---|---|---|
| **NVIDIA Developer Blog** | `https://developer.nvidia.com/blog/feed` | ✅ 200, Atom, item de hoje (08/09/2026) | Alta agora — 7/8 títulos recentes são IA/agentes/LLM (CUDA Rust, agentic cybersecurity, speculative decoding). Pode variar por período — é blog técnico geral, não 100% IA. | 0.7 (mesma faixa dos outros labs oficiais; marketing-heavy, aplicar STEP 1.5) | É devblog técnico (tutoriais), não research puro — sinal de infraestrutura/deploy de IA, complementa em vez de duplicar Meta/Mistral/Qwen. |
| **Apple Machine Learning Research** ✅ implementado 2026-09-08 | `https://machinelearning.apple.com/rss.xml` | ✅ 200, RSS 2.0, item de 02/09/2026 | ~100% (é feed de research puro) | 0.8 | Cadência real observada no feed: rajadas na mesma semana com gaps de até ~6 dias. Aplicado `recency_hours: 168` + `recency_decay_constant: 48` (ver `sources_config.json` + `pre_filter.py` v5.4) pra não cair no mesmo padrão de `ethan_mollick`. Fetch testado ao vivo (10 itens, timestamps válidos, categoria "ai" inferida corretamente). |
| **Microsoft Research Blog** | `https://www.microsoft.com/en-us/research/feed/` | ⚠️ 200 só com User-Agent de browser real — retorna 403 com UA padrão de bot/curl simples | Alta (blog é dedicado a research, inclui AI) | 0.7 | **Risco técnico real**: se o fetcher do pipeline não seta um `User-Agent` de navegador, essa fonte vai falhar silenciosamente como `anthropic_blog` fez. Testar isso antes de habilitar. |
| Cohere Blog | — | ❌ Sem RSS público. `cohere.com/blog/rss`, `/feed`, `/feed.xml` → 404 ou HTML; sem `rel=alternate` na página. | — | — | **Rejeitar** — anti-critério "sem RSS público" (site é JS-rendered sem feed exposto). |
| Stability AI News | `https://stability.ai/news-updates?format=rss` | ✅ 200, RSS válido (achado via autodiscovery — a URL do estudo de abril, `/news?format=rss`, mudou de path) | Não verificada em detalhe, mas Stability publica quase só sobre modelos de imagem/vídeo — provavelmente alta | 0.7 | **Confirma o alerta do brief**: a URL mudou desde abril/2026. Se algum dia isso foi implementado com a URL antiga, estaria morto. |
| xAI Blog | — | ❌ 403 bloqueado (proteção anti-bot), sem padrão de feed encontrado. xAI comunica majoritariamente via X/Twitter, não blog. | — | — | **Rejeitar por ora** — incompatível com critério 5 (compatibilidade com pipeline); não há como buscar sem depender de scraping frágil ou da API do X. |

**Recomendação Gap 3:** próxima onda pequena = **NVIDIA Developer Blog + Apple ML Research**. Microsoft Research entra só depois de confirmar que o fetcher consegue passar um UA de navegador (teste de 5 min antes de codar). Cohere e xAI ficam fora — não têm RSS público hoje.

---

## 2. Gap 4 — Developer tooling / lançamento de ferramentas

Faltam: GitHub Trending, Product Hunt (sinal de *adoção*, não pesquisa).

| Candidata | Feed | Status validado | Densidade IA | Peso sugerido | Risco/caveat |
|---|---|---|---|---|---|
| **GitHub Blog** ✅ implementado 2026-09-08 | `https://github.blog/feed/` | ✅ 200, RSS, item de 04/09/2026 | Alta agora — 6/8 títulos recentes são sobre Copilot/agentes de código/IA de desenvolvimento | 0.8 | Cadência real observada: quase diária, gaps ocasionais de até ~6 dias — aplicado `recency_hours: 168` + `recency_decay_constant: 48` (mesma calibração do apple_ml_research). Fetch testado ao vivo (10 itens, todos categorizados "ai"). Isto **não é GitHub Trending** (que não tem API/RSS oficial estável — exigiria scraping frágil, falha no critério 5). É o blog oficial do produto GitHub, com foco forte em IA aplicada a dev tooling agora — bom proxy do gap, mas é conteúdo institucional, não "pulso de adoção OSS" como o estudo original pedia. |
| Product Hunt (feed geral) | `https://www.producthunt.com/feed` | ✅ 200, Atom, itens de hoje | Baixa/indeterminada pelos títulos — nomes de produto sem contexto (ex: "Widgo", "Coherence X6"), a maioria não parece ser IA | 0.6 | Confirma o caveat já previsto no estudo original: "muito launch marketing", precisa de STEP 1.5 + filtro de categoria/tag para não inundar. Sem tag AI-específica exposta no feed geral — filtrar por keyword no pre-filter. |
| GitHub Trending (AI topics) | — | ❌ Sem RSS/API pública estável — página é renderizada dinamicamente, terceiros oferecem scrapers não-oficiais | — | — | **Rejeitar** — viola critério 5 (compatibilidade, "sem scraping frágil"). Se quiser esse sinal, GitHub tem API REST (`/search/repositories?sort=stars`) que poderia ser uma fonte customizada, mas é trabalho de engenharia, não um RSS pronto — fora do escopo "PR de config". |

**Recomendação Gap 4:** **GitHub Blog** é a candidata mais sólida — feed estável, alta densidade IA agora. Product Hunt entra só se aceitar o custo de ruído e escrever um filtro de keyword dedicado; não é quick win.

---

## 3. Gap 6 — Enterprise / mercado

Zero fonte dedicada a decisão corporativa/M&A.

| Candidata | Feed | Status validado | Densidade IA | Peso sugerido | Risco/caveat |
|---|---|---|---|---|---|
| **Sifted** (startups/tech Europa) | `https://sifted.eu/feed` | ✅ 200, RSS, item de hoje (08/09/2026) — primeiro item é "Mistral confirms €3bn Series D" | Moderada-alta quando envolve AI labs europeus (Mistral, etc.) — geral é cobertura de venture/funding europeu | 0.9 | Bônus: fecha parte do Gap 1 (Europa) que o estudo original também apontava como fraco — é sinal de mercado *e* geografia ao mesmo tempo. Sem paywall no RSS. |
| WSJ — WSJD (tech) | `https://feeds.a.dj.com/rss/RSSWSJD.xml` | ✅ 200, RSS válido, headlines atuais incluindo cobertura de IA (ex: "What to Know About China's DeepSeek AI") | Moderada — feed misto de tech geral | 0.8, tratar como **signal-only** (mesmo tratamento já dado a `stratechery`) | Paywall no full-text, RSS só dá headline/resumo — não pode ser main_find sem fallback, igual ao caveat já resolvido para Stratechery no `sources_config.json`. |
| The Information | — | ❌ `theinformation.com/feed` → 403 (bloqueado, não é mais só paywall — parece bot-blocked mesmo pra headlines) | — | — | **Rejeitar por ora** — a recomendação de abril não é mais válida; o feed público de headlines não responde. Reavaliar só se a Aya achar um endpoint alternativo (ex: newsletter parceira que resyndica). |
| Bloomberg Technology | — | ❌ `bloomberg.com/technology/rss` → 403 | — | — | **Rejeitar** — mesmo padrão, sem RSS público acessível hoje. |
| Reuters Technology | — | ❌ `reuters.com/technology/rss` → 401; `feeds.reuters.com/...` → conexão falha (feed descontinuado) | — | — | **Rejeitar** — Reuters descontinuou feeds RSS públicos há alguns anos; confirma que essa recomendação de abril está obsoleta. |

**Recomendação Gap 6:** **Sifted** é a melhor candidata nova — feed limpo, sem paywall, sinal de mercado real (funding, M&A) com bônus de cobertura europeia. WSJD pode entrar como signal-only se aceitar o mesmo tratamento do Stratechery. As três recomendações "óbvias" do estudo original (Information, Bloomberg, Reuters) estão **todas inacessíveis hoje** — isso é a validação mais importante desta rodada: não dava pra saber sem checar de novo.

---

## 4. Gap 7-ES — LatAm em espanhol

Português já coberto (Agência Brasil + MIT TR Brasil); espanhol (México, Argentina, Espanha) continua sem fonte.

| Candidata | Feed | Status validado | Densidade IA | Peso sugerido | Risco/caveat |
|---|---|---|---|---|---|
| **Xataka — tag IA** | `https://www.xataka.com/tag/inteligencia-artificial/rss2.xml` | ✅ 200, RSS, itens de hoje (08/09/2026) | ~100% — feed dedicado exclusivamente a IA, não a Xataka geral | **0.8** (revisado — ver nota abaixo; não é equivalente institucional ao MIT Tech Review) | É Espanha (não LatAm stricto sensu), mas é a referência de maior alcance em espanhol para tech/IA. Confirma achado do brief: feed geral (`feedburner.xml`) tem densidade baixa (~12%) — **usar o feed de tag, não o geral**. **Ver nota de credibilidade abaixo antes de aprovar.** |
| **Infobae — Tecno** | `https://www.infobae.com/arc/outboundfeeds/rss/category/tecno/` | ✅ 200, RSS, itens de hoje, alta frequência | Moderada (~40-50% nos títulos observados — mistura IA com tech geral/cripto) | 0.8 | Sede Argentina, maior alcance editorial da América Latina hispanofalante (México, Argentina, Colômbia). Volume alto (`limit` menor recomendado, ~15) — vai precisar de filtro de keyword como `agencia_brasil` já usa. |
| Hipertextual | `https://hipertextual.com/feed` | ✅ 200, RSS, itens de hoje | Baixa (~20-25% nos títulos — muita cultura pop/gadgets) | — | **Não recomendar nesta onda** — densidade abaixo do critério de 30%, mistura forte com entretenimento (cinema, celulares). Fica como backup se Xataka/Infobae não performarem bem em produção. |
| El Economista (ES) | `https://www.eleconomista.es/rss/rss-tecnologia.xml` | ❌ 403 bloqueado | — | — | Rejeitar — bloqueio de bot, sem alternativa fácil testada. |

**Recomendação Gap 7-ES:** **Xataka (tag IA)** é quick win de densidade — feed 100% IA, vivo, alto alcance em espanhol. **Infobae Tecno** fecha o ângulo LatAm-hispânico de verdade (Argentina/México) mas precisa de filtro de keyword por causa do volume misto. Mesma ressalva do estudo original permanece: itens em espanhol entram no pipeline com título em ES — testar como a Aya trata isso na curadoria (ela já lida com PT via Agência Brasil, então o padrão de tratamento deve ser similar).

### Nota de credibilidade — Xataka (checado 2026-09-08)

Pedido explícito de validação antes de aprovar. Resumo do que a pesquisa achou, o mais próximo possível da fonte:

- **Propriedade:** Xataka pertence à Webedia (grupo francês de mídia digital), que comprou a Weblogs SL (editora original, fundada por Julio Alonso e Antonio Ortíz) em 2018 por ~€10M. Não é veículo independente — é ativo de um grupo comercial de mídia com dezenas de outras verticais (Genbeta, Motorpasión, Trendencias etc.).
- **Alcance:** fundado em 2004, se autodescreve como líder de tráfego em tech em espanhol (~40M usuários únicos/mês, número autorreportado — não verificado por terceiro independente).
- **Modelo de negócio:** misto — assinatura premium (XTRA), publicidade, **links de afiliado** em comparativos de produtos ("Xataka Selección"), e parcerias de marca patrocinadas (ex.: vertical "Innovación Volvo"). Existe política pública declarada de "relación com empresas" e "como fazemos as reviews", mas não achei declaração explícita de wall entre editorial e comercial nem menção a conflitos de interesse.
- **Reputação — dividida:** no setor de tech em espanhol é tratado como referência de volume e rapidez ("não há nada que se compare em rigor", segundo fãs). Mas há crítica recorrente de menor profundidade analítica e viés a manchete/clique — e no Trustpilot o site tem nota **1,7/5 ("muito ruim")**, com reclamações específicas de reviews com dados errados e insinuação de que "vendem-se ao maior comprador" (amostra do Trustpilot não é necessariamente representativa nem focada em jornalismo — mistura reclamação de e-commerce/afiliados, mas é o único dado quantitativo de terceiro que achei).
- **Tipo de viés relevante aqui:** não é viés político/editorial no sentido do framework original (US/EU anglófono) — é viés **comercial** (afiliados, parcerias de marca) mais forte no conteúdo de reviews/comparativos. O feed de tag IA recomendado é predominantemente *notícia*, não review — expõe menos a esse risco especificamente, mas a cultura editorial do veículo como um todo é mais tabloide/consumer do que institucional.
- **Comparação justa:** não é equivalente ao MIT Technology Review (veículo ligado ao MIT, sem modelo de afiliados, tier institucional distinto) nem ao Simon Willison (voz individual sem incentivo comercial de review). É mais próximo, em natureza comercial, do TechCrunch já presente no portfólio — grande site comercial de tech, útil por volume/velocidade/densidade, não por profundidade analítica.

**Ajuste de recomendação:** manter Xataka como candidata (densidade e vivacidade do feed continuam reais e validadas), mas com **peso revisado para 0.8** (faixa de AI Lab oficial/TechCrunch, não de editorial independente 0.9-1.1) e tratamento equivalente a TechCrunch no framework de curadoria — não tratar como "voz analítica premium" equivalente a MIT TR ou Simon Willison. Reavaliar peso depois de medir 7 dias de amostra real, como já recomendado para as demais candidatas.

---

## 5. Gap 8 — Sinal de prática/produção

Nenhum engineering blog cobrindo "IA em produção real".

| Candidata | Feed | Status validado | Densidade IA | Peso sugerido | Risco/caveat |
|---|---|---|---|---|---|
| **GitHub Blog** | (mesma do Gap 4) | ✅ | Alta agora | 0.8 | Ver Gap 4 — mesma fonte fecha os dois gaps parcialmente (dev tooling + produção de IA em código). |
| **Netflix Tech Blog** | `https://netflixtechblog.com/feed` | ✅ 200, RSS, item de 28/08/2026 | Baixa geral (~10-20% esperado, confirma caveat do estudo original) — é engineering blog amplo, não IA-específico | 0.6 | Precisa de filtro de keyword agressivo no pre-filter para não inundar com posts de infra genérica. Cadência ~1 post/1-2 semanas. |
| **Shopify Engineering** | `https://shopify.engineering/blog.atom` | ✅ 200, Atom, item de 02/09/2026 | Baixa-moderada | 0.6 | Mesmo caveat de densidade do Netflix. |
| **Stripe Blog** | `https://stripe.com/blog/feed.rss` | ✅ 200, RSS, item de 20/08/2026 | Baixa (blog é misto produto+engineering+policy) | 0.6 | Considerar usar só a seção de engineering se o pipeline suportar sub-feeds; o feed geral testado é o blog todo. |
| Figma Blog | — | ❌ Sem RSS encontrado (`/blog/rss.xml`, `/blog/feed.xml`, `?format=rss` → todos 404) | — | — | **Rejeitar** — não achei feed público funcional; Figma parece ter descontinuado ou nunca exposto RSS no blog atual. |

**Recomendação Gap 8:** confirma a recomendação original do estudo — agrupar em um único source `engineering_blogs` (bundle de Netflix + Shopify + Stripe, todos validados e vivos) em vez de 3 fontes separadas, com peso baixo (0.6-0.7) e filtro de keyword dedicado no pre-filter para não inundar com conteúdo não-IA. Este é o gap de **maior risco de ruído** dos cinco — condiz com o estudo original ter colocado como "baixa prioridade/experimental".

---

## 6. Resumo — candidatas prontas pra próxima onda

Ordenado por confiança/baixo risco primeiro, seguindo a lógica de rollout em ondas do estudo original (não adicionar tudo de uma vez):

| Prioridade | Fonte | Gap | Peso | Por quê primeiro |
|---|---|---|---|---|
| **Alta** | Xataka (tag IA) | 7-ES | 0.8 | Densidade ~100%, feed vivo, fecha gap de idioma real — peso revisado após checagem de credibilidade (Webedia, comercial, viés de afiliados — ver nota) |
| **Alta** | GitHub Blog | 4 + 8 | 0.8 | ✅ Implementado 2026-09-08 — densidade alta, fecha 2 gaps de uma vez |
| **Alta** | NVIDIA Developer Blog | 3 | 0.7 | Densidade alta agora, feed estável |
| **Média** | Sifted | 6 | 0.9 | Único candidato de enterprise/mercado com feed público limpo (Information/Bloomberg/Reuters todos inacessíveis) |
| **Média** | Apple ML Research | 3 | 0.8 | ✅ Implementado 2026-09-08 — com `recency_hours`/`recency_decay_constant` próprios pra não repetir o padrão `ethan_mollick` |
| **Média** | Infobae Tecno | 7-ES | 0.8 | Fecha ângulo LatAm-hispânico real, mas exige filtro de keyword (volume misto) |
| **Baixa/experimental** | `engineering_blogs` bundle (Netflix + Shopify + Stripe) | 8 | 0.6-0.7 | Maior risco de ruído do lote — monitorar 2-3 edições antes de manter, como o estudo original já recomendava |
| **Baixa/experimental** | WSJD (signal-only) | 6 | 0.8 | Paywall — mesmo tratamento do Stratechery |
| **Baixa/experimental** | Microsoft Research Blog | 3 | 0.7 | Só depois de confirmar que o fetcher aceita passar UA de browser (403 com UA padrão) |
| **Baixa/experimental** | Product Hunt | 4 | 0.6 | Densidade indeterminada, precisa de filtro de tag/keyword específico |

**Rejeitadas nesta rodada (sem RSS público viável hoje):** Cohere, xAI, The Information, Bloomberg Technology, Reuters Technology, GitHub Trending, Figma Blog, El Economista (ES), Hipertextual (densidade baixa).

**Antes de codar qualquer onda:**
1. Resolver os 2 feeds mortos das fontes ociosas (`anthropic_blog`, `qwen_blog`) — é fix separado e mais urgente que adicionar fontes novas.
2. Testar o `User-Agent` do fetcher contra Microsoft Research antes de habilitar (403 com UA padrão).
3. Medir densidade real em 7 dias de amostra para as fontes de densidade "indeterminada/mista" (Product Hunt, Infobae, engineering_blogs) antes de fixar peso definitivo — mesma prática recomendada no estudo original.
4. Considerar se `recency_hours`/`decay_constant` precisam de ajuste por fonte (piso mínimo de score, ou grace window) antes de adicionar mais fontes de cadência baixa (Apple ML Research entra nessa categoria) — senão repete o padrão de `ethan_mollick`.

---

*Pesquisa online realizada em 2026-09-08. Todas as URLs de feed foram validadas via HTTP request direto no momento da escrita — não são citações de terceiros sobre a existência das fontes. Complementa, não substitui, `SOURCES_STUDY.md`.*
