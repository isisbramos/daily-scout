## Insight — 26 março 2026

**O que eu estava tentando fazer**
A edição #001 do Daily Scout saiu e o julgamento da AYA não batia com o meu. O main find era prediction markets (539 pontos no HN, zero ângulo AI) e Netflix subindo preço entrou como quick find. Eu sabia que tava errado mas não sabia explicar exatamente por quê — nem qual seria o critério certo.

**O que mudou**
Descobri minha visão editorial respondendo perguntas, não tentando escrever direto. O processo de ser entrevistada sobre o próprio produto revelou coisas que eu não tinha articulado: que o Daily Scout é AI-first (não tech & AI equilibrado), que tração alta não deveria salvar notícia irrelevante, que "genérico demais" é o anti-signal mais forte, e que o teste real de uma boa notícia é se o leitor consegue dizer "sabia que agora dá pra..." pra alguém.

Depois, tratar o prompt como um produto — com audit técnico, scorecard, P0/P1/P2 — mostrou que intuição editorial boa + prompt ruim = resultado ruim. O draft que eu aprovei na teoria tinha regressões que só apareceram na avaliação: few-shots desalinhados, conflito system↔user, overlap de critérios. Sem o audit, teria deployado um prompt que parecia melhor mas ia falhar nos edge cases.

**Como isso muda meu processo**
Três coisas:
1. Quando eu não souber articular um critério, pedir pra ser entrevistada sobre ele em vez de tentar definir do zero
2. Tratar prompt como feature: discovery → spec → audit → test → deploy. Nunca reescrever e deployar direto.
3. Usar exemplos de DESCARTE nos prompts, não só de acerto. O modelo precisa aprender o que NÃO fazer tanto quanto o que fazer.

**O que ainda está aberto**
Como vou saber se o v4 está funcionando ao longo do tempo? Preciso de um mecanismo de avaliação contínua — talvez comparar minha reação com o output da AYA a cada edição e registrar drift. O feedback loop de 1-clique (🔥/👍/😐) captura satisfação geral mas não captura "o main find deveria ter sido outro".

**Semente de post**
Eu não sabia o que era uma boa notícia pro meu próprio produto. Precisei ser entrevistada pela IA pra descobrir.

---

## Documentação Completa — Editorial Framework v4

### Contexto

O Daily Scout é uma newsletter diária automatizada sobre tech & AI. A AYA (correspondente virtual) coleta posts de 4 fontes (Reddit, HackerNews, TechCrunch, Lobsters), filtra, e usa Gemini Flash pra selecionar e escrever os achados do dia. O prompt que controla a curadoria da AYA passou por 4 versões desde o lançamento.

### O Problema

Na edição #001 (26/03/2026), a AYA selecionou como achado do dia um post sobre prediction markets com 539 pontos no HackerNews — tema sem qualquer conexão com AI. Netflix subindo preço entrou como quick find. Enquanto isso, "Gemini permite importar chats de outros chatbots" (acionável, AI-first, sinal de mercado) ficou relegado a quick find.

O critério editorial vigente era genérico demais: "2 de 3 entre Tração, Impacto, Novidade". Tração alta (score) sozinha garantia entrada. Não havia filtro de relevância temática nem exemplos de descarte.

### O Processo

#### Fase 1 — Discovery editorial (entrevista estruturada)

Em vez de reescrever o prompt direto, rodamos um discovery em 3 rodadas de perguntas:

**Rodada 1 — O que é bom vs ruim:**
- Main find preferido: Gemini importando chats (não prediction markets)
- Signal: afeta uso de AI hoje + mostra direção do mercado + é acionável
- Anti-signal: genérico demais (Netflix, série B sem ângulo AI)

**Rodada 2 — Posicionamento:**
- Escopo: "AI como lente" (qualquer tech news, mas sempre pelo ângulo AI)
- Persona: curious professionals (não só tech workers)
- Tração: sinal, não filtro (indica tema quente, não garante entrada)

**Rodada 3 — Testes de edge case:**
- So what test: "sabia que agora dá pra..." (leitor sai com algo prático)
- Off-topic: sem ângulo AI, só entra se for impactante demais pra ignorar
- Netflix como quick find: incomodou — não deveria entrar de jeito nenhum

#### Fase 2 — Prompt audit (avaliação técnica)

O draft v4 foi avaliado em 8 critérios de prompt engineering. Score geral: 5.6/10 (vs 5.6 do v3). Melhor intenção, mas regressões técnicas:

| Problema | Severidade | Descrição |
|----------|-----------|-----------|
| Few-shots desalinhados | P0 | Exemplos ensinavam TOM mas não SELEÇÃO. Wine/DirectX passaria no prompt antigo mas falharia no novo (zero AI). |
| Conflito system ↔ user | P1 | SYSTEM diz "tech & AI" (equilibrado), CURATION diz "AI como lente" (AI-first). Modelo sofre conflito nos edge cases. |
| Overlap de critérios | P1 | "Afeta uso de AI" e "Acionável" têm ~70% de overlap. Modelo conta 2 quando é 1. |
| So what como simulação | P2 | "Imagine o leitor contando pro colega" pede ao modelo simular 2 personas. Modelos são ruins nisso. |
| Anti-signal subjetivo | P2 | "Genérico demais" sem heurísticas concretas. Modelo não sabe onde traçar a linha. |
| Pipeline sem ordem | P2 | 4 camadas de filtragem sem ordem explícita. Modelo pode aplicar em qualquer sequência. |

Score pós-fix: 8.8/10.

#### Fase 3 — Implementação

Mudanças aplicadas no `pipeline.py`:

**SYSTEM_INSTRUCTION (1 mudança):**
```
ANTES: "newsletter diária de tech & AI"
DEPOIS: "newsletter diária que cobre o mundo tech através da lente de AI"
```

**CURATION_PROMPT (reescrita completa):**

O prompt flat virou pipeline sequencial em 5 steps:

```
STEP 1 — AI GATE (obrigatório)
  Tem conexão com AI? SIM → continua. NÃO → só se excepcional.

STEP 2 — CRITÉRIOS (2 de 3)
  Acionável / Sinal de mercado / Afeta workflows

STEP 3 — ANTI-SIGNAL (descarte imediato)
  Preço consumer / Funding genérico / Crypto sem AI / UI cosmético

STEP 4 — RANKING
  main_find = mais acionável. Tração = tiebreaker.

STEP 5 — TESTE FINAL (completion task)
  "Agora é possível [X]" ou "[Player] está [movendo pra] [Y]"
```

Few-shot examples: de 3 (só tom) para 5 (seleção + descarte + tom).

### Resultado — Before vs After

#### ANTES (Edição #001 — prompt v3)

```
ACHADO DO DIA:
  Prediction Markets — impacto negativo (539pts HN)
  → Sem ângulo AI, genérico, entrou por tração

QUICK FINDS:
  Wikipedia restringe IA ✓
  Gemini importa chats ← deveria ser main find
  GitHub Copilot usa dados ✓
  Netflix sobe preço ✗ noise
  Anthropic vs Pentágono ✓
```

#### DEPOIS (Dry run — prompt v4)

```
ACHADO DO DIA:
  Gemini permite importar histórico de chat de outros chatbots
  → Acionável + sinal de mercado + AI-first ✓

QUICK FINDS:
  GitHub Copilot usará dados para treinar modelos ✓
  Anthropic obtém liminar contra Pentágono ✓
  Wikipedia restringe uso de IA ✓
  Resposta a ataque de malware LiteLLM ✓ (novo — não estava no v3)
  Google Translate expande tradução em tempo real ✓ (novo — AI angle)

REMOVIDOS:
  Prediction markets ✗ (AI gate: falhou)
  Netflix sobe preço ✗ (anti-signal: serviço consumer)
```

### Aprendizados-chave

1. **Intuição editorial ≠ prompt bom.** Saber o que é certo e conseguir traduzir isso em instrução pra modelo são habilidades diferentes. O audit revelou regressões que a leitura intuitiva não pegou.

2. **Discovery por entrevista > definição direta.** Responder perguntas estruturadas extraiu critérios que eu não conseguia articular tentando escrever do zero. O processo de ser questionada gerou mais clareza que o processo de definir.

3. **Exemplos de descarte são tão importantes quanto exemplos de acerto.** O modelo precisa aprender onde está a fronteira. Sem exemplos de "isso NÃO entra", a fronteira fica vaga.

4. **Pipeline sequencial > lista flat.** Modelos seguem steps numerados com muito mais consistência do que julgamento aberto. AI Gate como primeiro filtro elimina o problema na raiz.

5. **Tração é context, não criteria.** Esse shift conceitual mudou todo o framework. Score alto indica tema quente, mas não garante relevância pro público.

### Status técnico

- Branch: `feat/editorial-v4`
- Commit: `a20450b` — "feat(curation): v4 editorial framework"
- Dry run: validado com sucesso em 26/03/2026
- Próximo passo: merge na main → edição #002 roda com framework v4
