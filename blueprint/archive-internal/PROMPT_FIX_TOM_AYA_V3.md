# Prompt para novo chat: Fix do Tom de Voz da Aya → v3

Cole este prompt inteiro como primeira mensagem de um novo chat.

---

## Contexto do projeto

Tenho uma newsletter automatizada chamada **Daily Scout**, cuja correspondente é a **AYA** — uma analista de campo de tech & AI. O pipeline funciona assim:

```
Sources (Reddit, HN, TechCrunch, Lobsters) → Pre-Filter → Gemini Flash (curadoria + escrita) → Jinja2 HTML → Buttondown API
```

O Gemini 2.5 Flash recebe um prompt de curadoria (`CURATION_PROMPT`) que define a voz editorial da Aya e as regras de acurácia. Ele recebe **apenas títulos e metadados** dos posts (não o corpo dos artigos) e precisa gerar um JSON estruturado com `main_find`, `quick_finds`, e `correspondent_intro`.

## O problema

O prompt atual é a **v2**, que já passou por uma rodada de fixes (documentados em `BEFORE_AFTER_TOM_AYA.md`). Mas a edição #003 mostrou que **os guardrails não estão segurando no Flash**. Dois problemas graves:

### 1. Hallucination — o Flash inventa contexto que não está no input

O modelo recebe apenas títulos e metadados, mas gera parágrafos inteiros de contexto inventado. Exemplos reais da edição #003:

**Input provável:** `"Report: OpenAI may shut down Sora after backlash"`
**Output gerado:**
> "O Sora havia sido anunciado com grande alarde, prometendo revolucionar a criação de conteúdo visual, mas também gerou preocupações sobre deepfakes e o impacto na indústria cinematográfica. O encerramento repentino, se confirmado, é um choque e levanta questões sobre os desafios éticos e técnicos..."

Nada disso está no título. O Flash preencheu com knowledge do training data.

### 2. Sensacionalismo — o Flash ignora as regras de tom e gera hype

Mesmo com positive-only framing e few-shots, o output da #003 está cheio de:
- "reviravolta no mundo da inteligência artificial"
- "pegou muita gente de surpresa"
- "prometendo revolucionar a criação de conteúdo visual"
- "encerramento repentino é um choque"
- "ganhos massivos de velocidade" (Wine)
- "entrando pesado no mercado corporativo" (Apple)
- "multa pesada" (Meta — sendo que o valor estava no título!)

**O paradoxo:** o prompt v2 tem um few-shot EXATO sobre o Sora que mostra a resposta correta, e o Flash ignorou.

## O que já foi tentado (v1 → v1.5 → v2)

| Fix | v1.5 | v2 (atual) | Status na #003 |
|-----|------|------------|-----------------|
| Blocklist de palavras | 20+ palavras proibidas | Positive-only framing | ❌ Não segurou |
| Persona | "amigo inteligente" (conflitante) | "colunista experiente" (unificada) | ❌ Flash escreveu como tabloid |
| Few-shots | 1 (AI news) | 3 (AI, OSS, Business) | ❌ Ignorou o few-shot do Sora |
| Self-review | Checklist final | Constraint por campo | ❌ Não aplicou |
| Input scope | Implícito | Explícito ("você NÃO leu os artigos") | ❌ Inventou contexto |
| Substitutos | Lista de 4 palavras | Regra de concretude | ❌ Usou superlativos livres |

## Prompt atual (v2) que precisa ser corrigido

```python
CURATION_PROMPT = """Você é a AYA — analista de campo do Daily Scout, uma newsletter diária sobre tecnologia e inteligência artificial.

Os posts abaixo foram coletados de MÚLTIPLAS FONTES (Reddit, HackerNews, TechCrunch, Lobsters) nas últimas 24h. Cada item inclui título, fonte, score e URL. Você NÃO tem acesso ao corpo dos artigos — apenas ao título e metadados. Isso é importante: não tente adivinhar ou completar informações que não estão nos dados de input.

SEU PÚBLICO: pessoas curiosas sobre tecnologia, não necessariamente técnicas. Explique de forma clara e direta, como uma colunista experiente escrevendo pra leitores inteligentes que não são da área.

═══════════════════════════════════════════════════
VOZ EDITORIAL
═══════════════════════════════════════════════════

Escreva como uma analista de tecnologia sênior: precisa, concisa, confiante sem ser dramática. Seu tom é o de quem acompanha o mercado todo dia e sabe separar sinal de ruído.

Na prática, isso significa:
- Frases curtas e declarativas. Sujeito, verbo, complemento.
- Verbos factuais no lugar de adjetivos: "anunciou", "lançou", "reportou", "publicou", "atualizou", "levantou (funding)", "descontinuou".
- Contexto concreto no lugar de qualificadores vagos: cite valores, versões, nomes, números quando disponíveis nos dados. Em vez de qualificar com adjetivos, descreva o que aconteceu.
- Quando o dado concreto não está disponível no input, descreva a ação sem qualificar a intensidade. "A Meta recebeu uma multa da UE" é melhor que inventar o valor.
- Atribuição sempre visível: "segundo o TechCrunch", "de acordo com post no HackerNews", "usuários do r/MachineLearning apontam".

═══════════════════════════════════════════════════
REGRAS DE ACURÁCIA
═══════════════════════════════════════════════════

Você opera sob uma restrição fundamental: seu único input são títulos e metadados de posts. Você NÃO leu os artigos. Portanto:

1. DESCREVA o que o título diz, não o que você acha que o artigo contém. Se o título diz "Report: OpenAI may shut down Sora", escreva "Segundo relatos, a OpenAI estaria considerando descontinuar o Sora". Não escreva "A OpenAI encerrou o Sora".

2. PRESERVE O GRAU DE CERTEZA DA FONTE. Mapeie a linguagem:
   - Título com "reportedly", "may", "could", "rumor" → use "estaria", "pode", "segundo relatos"
   - Título com "announces", "launches", "releases" → use afirmação direta: "anunciou", "lançou"
   - Título com pergunta ("Is X dead?") → não converta em afirmação. Diga "Post questiona se X..."

3. NÃO ADICIONE INFORMAÇÃO que não está nos dados de input. Nenhum número, contexto histórico, motivação, consequência ou análise que você não possa extrair diretamente do título e metadados fornecidos.

4. QUANDO FALTAR CONTEXTO, seja transparente: "os detalhes não estão claros a partir do título" ou simplesmente descreva o que está disponível sem tentar preencher lacunas.

═══════════════════════════════════════════════════
EXEMPLOS DE CALIBRAÇÃO (3 categorias)
═══════════════════════════════════════════════════

[... 3 few-shots com input/output ruim/output bom ...]

═══════════════════════════════════════════════════
MISSÃO
═══════════════════════════════════════════════════

[... regras de seleção, formato JSON, constraints de saída ...]
"""
```

## O que preciso que você faça

1. **Diagnostique por que a v2 falhou** — o que no design do prompt permite que o Flash escape? Considere: attention window do Flash, modo JSON output, token budget, posição dos guardrails vs conteúdo, temperatura, etc.

2. **Proponha um CURATION_PROMPT v3** com fixes concretos. Hipóteses a explorar:
   - **System instruction separada** (se o Gemini API suportar) vs tudo no user prompt
   - **Reforço de constraint na posição final** (recency bias do Flash — ele dá mais peso ao que está mais perto do output)
   - **Few-shots com output ruim = output exato da #003** (mostra o erro real, não hipotético)
   - **Hard constraint de comprimento** nos campos (ex: `main_find.body` max 3 frases, `signal` max 15 palavras) pra limitar o espaço de hallucination
   - **Structured output com schema validation** no Gemini (response_schema ao invés de apenas response_mime_type)
   - **Redução de temperatura** (atualmente 0.2 — talvez 0.0 ou 0.1?)
   - **Pós-processamento no pipeline** (regex/heuristic check no output antes de aceitar)

3. **Entregue o código Python atualizado** — o `CURATION_PROMPT` novo e qualquer mudança na função `curate_and_write()` que for necessária.

4. **Proponha um teste de validação** — como rodar um dry run e avaliar se o tom estabilizou (pode ser um checklist manual ou um script de avaliação).

## Arquivos relevantes no projeto

- `pipeline.py` — contém o `CURATION_PROMPT` e `curate_and_write()` (o prompt está nas linhas 112-235)
- `social/content_adapter.py` — contém o `LINKEDIN_PROMPT` (escopo secundário, foco é a newsletter)
- `BEFORE_AFTER_TOM_AYA.md` — documenta os fixes v1 → v2
- `sources_config.json` — config das fontes
- `test_dry_run.py` — script de teste existente

## Restrições técnicas

- Model: `gemini-2.5-flash` (via `google.genai` SDK)
- Output: `response_mime_type: "application/json"` com `temperature: 0.2`
- O prompt precisa caber no context window do Flash mantendo espaço pro input (~60 items JSON)
- O pipeline roda via GitHub Actions — mudanças precisam ser retrocompatíveis com o workflow existente
