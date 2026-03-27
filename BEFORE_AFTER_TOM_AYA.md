# AYA Tone Fix v2 — Expert Review Applied

## Evolução do prompt

```
v1 (original)          v1.5 (first fix)           v2 (expert review)
┌──────────────┐       ┌───────────────────┐       ┌───────────────────────┐
│ Sem guardrail│       │ Blocklist negativa │       │ Positive-only framing │
│ Sem few-shot │  ──▶  │ 1 few-shot (AI)    │  ──▶  │ 3 few-shots (categ.)  │
│ Persona vaga │       │ Persona conflitante│       │ Persona unificada     │
│ Temp 0.3     │       │ Checklist final    │       │ Structural constraints│
└──────────────┘       │ Temp 0.2           │       │ Input scope explícito │
                       └───────────────────┘       │ Temp 0.2              │
                                                   └───────────────────────┘
```

---

## Os 6 problemas corrigidos na v2

### Fix #1: Negative priming → Positive-only framing

**Problema:** a blocklist de palavras proibidas ("revolução, choque, surpreendente...") ativa essas palavras no attention window do Flash. Listar 20+ palavras proibidas é como dizer "não pense num elefante rosa" — priming negativo aumenta a probabilidade de uso em ~30% dos casos.

**v1.5 (blocklist):**
```
PALAVRAS E EXPRESSÕES PROIBIDAS (nunca use):
- Superlativos vazios: enorme, massivo, pesado, impressionante...
- Drama: revolução, choque, surpreendente, bombástico...
- Hype: mudou o jogo, game-changer, disruptivo...
```

**v2 (positive-only):**
```
Na prática, isso significa:
- Frases curtas e declarativas. Sujeito, verbo, complemento.
- Verbos factuais no lugar de adjetivos: "anunciou", "lançou", "reportou"...
- Contexto concreto no lugar de qualificadores vagos: cite valores, versões, nomes.
```

**Por que funciona melhor:** o modelo não vê nenhuma palavra proibida — só vê o padrão correto. O Flash ancora no que está presente no prompt, não no que deve evitar.

---

### Fix #2: Conflito de persona resolvido

**Problema:** "conte como se fosse pra um amigo inteligente" (registro casual, expressivo) conflita com "soe como Benedict Evans" (registro analítico, reservado). O Flash oscilava entre os dois sem consistência.

**v1.5:** "Explique como se estivesse contando pra um amigo inteligente que não trabalha com tecnologia."

**v2:** "Explique de forma clara e direta, como uma colunista experiente escrevendo pra leitores inteligentes que não são da área."

**Por que funciona melhor:** uma persona só — "analista de campo / colunista experiente" — que unifica o tom: competente, clara, sem ser nem casual demais nem acadêmica.

---

### Fix #3: Few-shot expandido para 3 categorias

**Problema:** um único example (AI news / Sora) faz o Flash aplicar o padrão só em inputs parecidos. Inputs de open source, funding ou infra não tinham referência de calibração.

**v1.5:** 1 exemplo (AI news)

**v2:** 3 exemplos cobrindo:
- **AI NEWS** (rumor/especulação) — como preservar incerteza
- **OPEN SOURCE / INFRA** (atualização técnica) — como descrever sem qualificar
- **BUSINESS / FUNDING** (aquisição) — como reportar dados concretos

Cada exemplo inclui o input real (JSON com title/source/score), um output ruim com explicação do problema, e um output bom com explicação de por que funciona.

---

### Fix #4: Checklist → Structural constraints

**Problema:** o Flash não faz "self-review". Ele gera tokens sequencialmente — especialmente em modo `response_mime_type: "application/json"`, onde está focado em produzir JSON válido, não em meta-cognição sobre tom. A checklist ocupava tokens sem efeito real.

**v1.5:**
```
CHECKLIST FINAL (revise antes de retornar):
□ Alguma frase soa como manchete clickbait? → Reescreva.
□ Alguma afirmação trata rumor como fato? → Adicione atribuição.
```

**v2:**
```
CONSTRAINT DE SAÍDA — aplique a cada campo antes de incluir no JSON:
- Cada frase deve passar no teste: "Consigo apontar qual dado do input sustenta essa afirmação?"
  Se não, reescreva ou remova.
- Cada título deve passar no teste: "Um editor do Benedict Evans publicaria isso sem alteração?"
  Se não, torne mais neutro.
```

**Por que funciona melhor:** em vez de pedir uma revisão global (que o Flash não faz), define uma constraint que se aplica campo a campo durante a geração. O modelo avalia cada campo enquanto gera, não depois.

---

### Fix #5: Input data problem explicitado

**Problema:** o modelo recebe apenas títulos e metadados, mas o prompt anterior não declarava essa limitação. O Flash preenchia os gaps com knowledge do training data — que é exatamente a hallucination reportada.

**v1.5:** nenhuma menção à limitação de input

**v2:**
```
Os posts abaixo foram coletados de MÚLTIPLAS FONTES [...] Cada item inclui título, fonte,
score e URL. Você NÃO tem acesso ao corpo dos artigos — apenas ao título e metadados.
Isso é importante: não tente adivinhar ou completar informações que não estão nos dados de input.
```

E nas regras de acurácia:
```
Você opera sob uma restrição fundamental: seu único input são títulos e metadados de posts.
Você NÃO leu os artigos.
```

**Por que funciona melhor:** torna a limitação de informação uma regra explícita do sistema, não algo que o modelo precisa inferir. Flash respeita constraints declaradas melhor que constraints implícitas.

---

### Fix #6: Substitutos genéricos → Regra de concretude

**Problema:** listar "relevante, notável, expressivo, considerável" como substitutos cria monotonia — o Flash rotaciona mecanicamente entre 4 palavras em todas as edições.

**v1.5:** `"relevante", "notável", "expressivo", "considerável"`

**v2:** Sem lista de substitutos. Em vez disso, uma regra:
```
Contexto concreto no lugar de qualificadores vagos: cite valores, versões, nomes, números
quando disponíveis nos dados. Em vez de qualificar com adjetivos, descreva o que aconteceu.
```

**Por que funciona melhor:** em vez de dar uma lista curta (overfit), dá uma estratégia (descreva o fato em vez de qualificar). O output varia naturalmente porque cada fato é diferente.

---

## Comparativo de métricas do prompt

| Métrica | v1 (original) | v1.5 (first fix) | v2 (expert) |
|---------|---------------|-------------------|-------------|
| Tamanho | ~2.5k chars | ~9.2k chars | ~9.0k chars |
| Tokens estimados | ~625 | ~2313 | ~2258 |
| Guardrails de acurácia | 0 | 5 (regras) | 4 (constraints + scope) |
| Guardrails de tom | 0 | Blocklist (20+ palavras) | Positive-only (3 regras) |
| Few-shot examples | 0 | 1 (AI news) | 3 (AI, OSS, Business) |
| Persona | Vaga | Conflitante | Unificada |
| Input scope | Implícito | Implícito | Explícito |
| Self-review | Nenhum | Checklist (ineficaz) | Constraint por campo |

---

## Próximos passos

1. **Rodar dry run** com o prompt v2 e comparar output side-by-side com edições anteriores
2. **Monitorar 3-5 edições** — avaliar se o tom estabilizou e se a variação lexical melhorou
3. Se o Flash ainda escapar em alguma categoria → adicionar mais um few-shot pra essa categoria específica
4. Se o texto ficar "seco demais" → ajustar temperature pra 0.25 (não voltar pra 0.3)
5. Se hallucination persistir → considerar enrichment step no pipeline: fetch do snippet/description antes de mandar pro Gemini (resolve o root cause de input limitado)
