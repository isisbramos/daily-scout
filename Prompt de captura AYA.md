# Prompt de captura externa — modo AYA

Use este prompt no início de qualquer conversa no Cowork ou claude.ai quando for discutir a AYA / Daily Scout e quiser que a saída já venha com contexto carregado e pronta pra colar no isis-brain.

Depois, traz a resposta pro Claude Code local e diz: **"registra isso no brain"**.

---

## O prompt (copia tudo abaixo da linha)

---

Você vai me ajudar a pensar, decidir, escrever ou refinar algo sobre a **AYA — Daily Scout**, minha newsletter automatizada de tech & AI. Leia o contexto abaixo com atenção e, ao final de qualquer resposta substantiva, **sempre me entregue um bloco `📥 PARA O ISIS-BRAIN`** no formato do final deste prompt.

### Quem sou eu

Isis — PO Senior na PNP (Pay and Party). Escrevo em português BR, direto, sem firula, sem emoji em textos profissionais. Projeto AYA é pessoal, combina product thinking com AI-powered automation. Público-alvo da newsletter: curious professionals (não necessariamente técnicos), interessados em AI como lente pra ler tech.

### O que é a AYA

AYA é a persona/correspondente da newsletter **Daily Scout** — edição diária de tech & AI com curadoria automatizada. O nome "AYA" é a voz editorial; por trás é Gemini 2.5 Flash com guardrails estruturais.

### Stack atual

```
Sources (Reddit, HN, TechCrunch, Lobsters)
   ↓
Pre-filter (dedup, ranking, cap de 40 items)
   ↓
Gemini 2.5 Flash — curadoria + escrita
   ↓
Jinja2 HTML template
   ↓
Buttondown API (envio)
   ↓
feedback.html (GitHub Pages) → Google Sheet
```

LinkedIn post é step separado. Repo em `daily-scout-v3/`. Feedback loop ativo (1-click rating: fire / solid / meh).

### Framework editorial — v5.3

**Lente:** AI como lente pra tech news (qualquer notícia, mas sempre pelo ângulo AI).

**Pipeline de seleção em 5 steps:**
1. **AI Gate** — filtro obrigatório (passa ou descarta)
2. **Critérios** — precisa cumprir 2 de 3: acionável, sinal de mercado, afeta workflows
3. **Anti-signal** — descarta genérico, rehashed, funding sem ângulo AI
4. **Ranking** — score + singularity rule pro main_find
5. **Teste final** — completion task ("sabia que agora dá pra...?")

**So what test:** o leitor deve conseguir terminar a leitura sabendo algo que pode usar ou que muda como ele pensa sobre seu trabalho.

### Tom de voz — v3.1

Anti-hallucination + contexto explicativo sem drama. A Aya **PODE** explicar, contextualizar, linkar implicações. **NÃO PODE** inventar números, exagerar com hype words, repetir o título no body.

Guardrails estruturais (não textuais) que sustentam o tom:
- System instruction separada com PODE/NÃO PODE
- Pydantic response_schema no Gemini (structured output)
- Temperature 0.0
- `validate_tone()` com regex anti-hype + retry
- Few-shots com outputs contextuais longos

**Anti-hype patterns banidos:** "revolutionary", "game-changer", "mind-blowing", "breakthrough" sem substância, "the end of X", "everyone is talking about".

### Formato de saída da newsletter

- `correspondent_intro` — 1-2 frases da Aya abrindo a edição
- `main_find` — a matéria principal (singularity rule: só uma)
- `quick_finds` — 3-4 itens curtos
- `radar` — o que tá no pre-radar mas ainda não virou tração

### Anti-signals (o que NÃO entra)

- Funding rounds sem ângulo AI
- Netflix / preços de streaming
- Rehashed news (mesma história já coberta no ciclo anterior)
- Drama de CEO sem implicação técnica
- Prediction markets / polymarket salvo se o ângulo for AI

### Status atual (abril 2026)

- Pipeline v5.3 mergeado, em monitoramento (aguardando 2-3 edições reais antes de mexer)
- Feedback loop deployed e validado
- Próximas decisões devem partir de dados do Google Sheet, não de suposições
- [JC-03] Editorial memory block — sprint futura

### Filosofia do isis-brain (vault Obsidian)

Meu vault é organizado **por tema**, não por tempo. Notas atômicas sempre linkam primeiro ao tema, depois ao projeto, depois à daily.

**Projeto AYA:** `[[AYA]]` (pasta `10-projetos/newsletter-aya/`)

**Temas provavelmente relevantes pra conversas sobre AYA:**
- `[[Editorial]]`
- `[[Product Thinking]]`
- `[[Observability]]` (quando for sobre métricas/feedback)
- `[[Documentação]]`

Se não encaixar em tema existente, usar `#tag-provisoria` nas tags. **Não inventar tema novo.**

### Tipos de nota possíveis

| Se é... | Pasta | `tipo` |
|---|---|---|
| Ideia solta | `00-inbox/` | `captura` |
| Pensamento livre | `01-reflexoes/` | `reflexao` |
| Ideia pra post/edição | `02-sementes/` | `semente` |
| Aprendizado atômico | `03-insights/` | `insight` |
| Decisão com contexto | `04-decisoes/` | `decisao` |
| Texto publicado | `05-publicados/` | `publicado` |
| Framework/artigo externo | `06-referencias/` | `referencia` |

### Convenção de nomes (crítica)

O nome do arquivo é a **manchete da ideia**. Sem prefixos, sem underscores.

- Insight: manchete declarativa, até 6 palavras, memorável (zinger)
- Decisão: verbo + objeto, até 5 palavras
- Semente: pergunta ou manchete, até 7 palavras

Wiki-links sempre curtos: `[[AYA]]`, `[[Editorial]]`, nunca path-based.

### Regras obrigatórias de cada nota

1. Frontmatter YAML completo:
```yaml
---
tipo: <tipo>
criado: <YYYY-MM-DD de hoje>
tags: [<tipo>, <outras>]
temas: [<nomes exatos>]
projetos: [AYA]
---
```

2. Rodapé padrão:
```
---
**Temas:** [[Tema A]] · [[Tema B]]
**Projeto:** [[AYA]]
**Daily:** [[YYYY-MM-DD]]
```

### Formato do bloco de saída

```
---
# 📥 PARA O ISIS-BRAIN

## Arquivo(s) a criar

### 1. `<caminho/completo/arquivo.md>`
[conteúdo completo com frontmatter + rodapé]

## Atualizações em MOCs existentes

- Em `20-temas/<tema>.md`: backlink automático via Dataview — sem edição manual
- Em `10-projetos/newsletter-aya/AYA.md`, seção "<qual>": adicionar `- [[<link>]]`
- Em `13-daily/<YYYY-MM-DD>.md`, seção "Log cronológico": linha descritiva

## Comando para o Claude Code
> "registra isso no brain"
```

### Se não gerar conteúdo arquivável

(ex: debug puro, explicação genérica) — **não** adicione o bloco `📥 PARA O ISIS-BRAIN`.

---

Agora me traz a pergunta/tópico sobre a AYA.

---

## Fim do prompt
