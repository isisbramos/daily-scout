# Daily Scout — Documentação de Processo

## Como uma PM construiu uma newsletter com IA (e o que aprendeu domando o modelo)

---

## 1. O que é o Daily Scout

Uma newsletter diária automatizada sobre tecnologia e IA. A "correspondente" é a **Aya**, uma persona de IA que:

- Coleta posts de 10 fontes (4 community + 3 AI labs + 3 geographic)
- Filtra ruído com pre-filter estatístico (z-score, decay, wild card zone)
- Escreve a curadoria do dia com tom editorial próprio (AI Gate + 5-step pipeline)
- Entrega via email automaticamente

O pipeline inteiro roda sozinho via GitHub Actions, sem intervenção manual.

```
Community ──────┐  Reddit, HN, TechCrunch, Lobsters
AI Labs ────────┤  Anthropic, OpenAI, DeepMind blogs
Geographic ─────┘  SCMP, Rest of World, TechNode
        │
        ▼
   Pré-Filtro (z-score, exponential decay, wild card zone)
        │
        ▼
   Gemini Flash (AI Gate → 5-step editorial pipeline → Radar)
        │
        ▼
   HTML (template Jinja2) → Buttondown API → Email
```

---

## 2. O problema: a Aya estava mentindo e exagerando

Na edição #003, a newsletter saiu com dois problemas graves:

**Hallucination** — a IA inventou informações que não existiam nas fontes.

O título original dizia: *"Report: OpenAI may shut down Sora after backlash"* (pode = rumor)

A Aya escreveu: *"A OpenAI encerra o Sora. O Sora havia sido anunciado com grande alarde, prometendo revolucionar a criação de conteúdo visual, mas também gerou preocupações sobre deepfakes e o impacto na indústria cinematográfica. O encerramento repentino é um choque."*

Nada disso — deepfakes, indústria cinematográfica, choque — estava na fonte. A IA preencheu as lacunas com o que "sabia" do treinamento.

**Sensacionalismo** — a IA escrevia como tabloid, não como analista.

- "reviravolta no mundo da inteligência artificial"
- "ganhos massivos de velocidade"
- "entrando pesado no mercado corporativo"
- "multa pesada para a Meta"

O leitor recebia hype em vez de informação.

---

## 3. O que já tinha sido tentado (e falhou)

### Versão 1.5 — Lista de palavras proibidas

A ideia: listar 20+ palavras que a IA não deveria usar ("revolução", "choque", "bombástico"...).

Por que falhou: funciona como dizer "não pense num elefante rosa". A IA lê as palavras proibidas e elas ficam ativas na "memória de trabalho" dela. Resultado: ela usava mais, não menos.

### Versão 2 — Instruções positivas + exemplos

A ideia: em vez de dizer o que não fazer, mostrar o que fazer. Incluímos 3 exemplos de input/output correto, persona unificada ("colunista experiente"), e regras de formato.

Por que falhou: a edição #003 mostrou que a IA ignorou tudo — inclusive um exemplo exato sobre o Sora que mostrava a resposta correta. O modelo leu as instruções, gerou o JSON, e no meio do caminho "esqueceu" as regras de tom.

---

## 4. O que funcionou: parar de pedir e começar a construir cercas

### 4.1 — A separação constitucional

> **Pergunta da Isis:** "Como foi essa separação? Separei as regras em um lugar onde a IA dá mais atenção?"

**O que é:** Modelos como o Gemini têm dois "espaços" para receber instruções:

- **System instruction** — é como a constituição. Define quem a IA é, suas regras fundamentais, o que pode e não pode fazer. O modelo dá mais peso a essa parte porque ela funciona como a identidade dele. É processada separadamente e fica "ativa" durante toda a geração do texto.

- **User prompt** — é como um pedido específico. "Faça isso com esses dados." O modelo trata como uma tarefa, não como uma regra.

**Na prática:**

Antes (v2), tudo ficava num único bloco de texto gigante — persona, regras de tom, exemplos, dados. A IA lia tudo como "um pedido longo". As regras de acurácia ficavam no meio, perdidas entre exemplos e formato.

Depois (v3), separamos em dois:

```
┌─────────────────────────────────┐
│ SYSTEM INSTRUCTION              │  ← "Constituição" da Aya
│                                 │
│ - Quem ela é                    │  O modelo dá MAIS peso
│ - Regra PODE / NÃO PODE        │  a essa parte
│ - Voz editorial                 │
│ - Regras de acurácia            │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ USER PROMPT                     │  ← "Tarefa do dia"
│                                 │
│ - Critérios de seleção          │  O modelo trata como
│ - Exemplos de calibração        │  pedido específico
│ - Regras de formato             │
│ - Dados (os posts coletados)    │
└─────────────────────────────────┘
```

**Por que funciona:** quando a IA está gerando texto e "decide" se vai escrever "choque" ou "segundo relatos", ela consulta a system instruction com mais peso. É como um juiz consultando a constituição antes de decidir — se a regra está lá, ela pesa mais do que um argumento no meio do processo.

**Como fazer no código:**

```python
# Antes (v2) — tudo junto
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt_gigante_com_tudo,  # regras + dados misturados
)

# Depois (v3) — separado
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=user_prompt,              # só a tarefa + dados
    config=GenerateContentConfig(
        system_instruction=REGRAS,     # "constituição" separada
    ),
)
```

---

### 4.2 — O formulário tipado (structured output)

> **Pergunta da Isis:** "Qual o método pra isso? Defini um formato rígido com campos tipados?"

**O que é:** Em vez de pedir "me devolva um JSON", definimos um formulário exato com campos tipados, cada um com descrição e limites. A IA preenche o formulário em vez de escrever livremente.

**Analogia:** Imagine a diferença entre pedir pra alguém "me escreve um relatório" versus dar um formulário com campos específicos:

```
Antes: "Escreva um JSON com main_find, quick_finds..."
→ A IA tem liberdade total. Escreve quanto quiser, inventa campos, muda o formato.

Depois: Formulário com campos definidos:
┌─────────────────────────────────────────────────────┐
│ Título: [max 15 palavras, factual e descritivo]     │
│ Fonte:  [HackerNews, TechCrunch, Reddit, Lobsters]  │
│ Body:   [3-5 frases. Comece com atribuição à fonte.  │
│          Explique o que é e por que importa.]        │
│ Bullets: [2-3 pontos: o que aconteceu, o que         │
│           significa, o que observar]                  │
└─────────────────────────────────────────────────────┘
→ A IA preenche dentro das restrições. Menos espaço pra inventar.
```

**Na prática, usamos Pydantic** — uma biblioteca Python que define modelos de dados:

```python
class MainFind(BaseModel):
    title: str = Field(description="Título factual e descritivo, max 15 palavras")
    body: str = Field(description="3-5 frases. Comece com atribuição à fonte.")
    bullets: list[str] = Field(description="2-3 pontos-chave")
```

E passamos esse modelo pro Gemini como `response_schema`. O modelo valida o output contra o schema **durante** a geração — não depois. Se um campo não bate com a descrição, o modelo ajusta em tempo real.

**Por que funciona:** campos curtos com descrições explícitas limitam o espaço de invenção. Se o body tem "3-5 frases", a IA não pode escrever 3 parágrafos de contexto inventado. A descrição "comece com atribuição à fonte" força a IA a citar a fonte antes de qualquer coisa.

---

### 4.3 — O limitador de velocidade (pós-processamento)

Mesmo com constituição e formulário, a IA às vezes escapa. A terceira camada é um filtro automático que lê o texto depois de gerado e procura padrões de sensacionalismo:

```python
# Lista de padrões de hype
HYPE_PATTERNS = [
    "revolucion", "bombástic", "choque", "impressionant",
    "massiv", "enorme", "pesad", "ousad", "incrível",
    "grande alarde", "aposta pesada", "reviravolta",
    "prometendo revolucionar", "pode mudar o cenário"...
]
```

Se encontrar qualquer um desses padrões, **rejeita o output e pede pra IA reescrever**. Até 5 tentativas. Só aceita com warnings na última.

**Analogia:** É literalmente um limitador de velocidade. A IA pode querer "acelerar" (dramatizar), mas o sistema trava e diz "refaça".

---

### 4.4 — Temperatura zero

A "temperatura" controla o grau de criatividade/aleatoriedade da IA:

- **Temperatura 0.3 (antes):** a IA escolhe entre várias opções de palavras, com alguma aleatoriedade. Às vezes escolhe a palavra neutra, às vezes a dramática.
- **Temperatura 0.0 (agora):** a IA sempre escolhe a opção mais provável. Sem improvisos.

É como a diferença entre um jazz musician (que improvisa) e um músico clássico (que segue a partitura). Pra uma newsletter factual, queremos a partitura.

---

## 5. A overcorreção (e como achamos o equilíbrio)

A v3 corrigiu a hallucination e o sensacionalismo. Mas matou o contexto. O output ficou:

> "Segundo post com alta tração no HackerNews (488 pontos), a União Europeia ainda busca escanear mensagens e fotos privadas. A proposta gerou 150 comentários na plataforma."

Seco demais. Repetia o título. Não explicava o que era "Chat Control" nem por que o leitor deveria se importar.

O fix (v3.1) foi criar uma régua explícita de **PODE vs NÃO PODE**:

```
PODE (e deve):
✓ Explicar o que algo É: "Sora é a ferramenta de geração de vídeo da OpenAI"
✓ Explicar por que importa: "Isso afeta quem usa criptografia de ponta a ponta"
✓ Dar contexto factual curto sobre empresas/produtos/tecnologias

NÃO PODE (nunca):
✗ Inventar reações: "gerou polêmica", "pegou de surpresa"
✗ Inventar números ou detalhes
✗ Converter incerteza em fato: "may" → "estaria", nunca "encerrou"
✗ Qualificar com adjetivos vazios: "massivo", "enorme", "bombástico"
```

O resultado final (v3.1):

> "Segundo post com 507 pontos no HackerNews, a União Europeia continua a propor a varredura de mensagens e fotos privadas. Esta medida, conhecida como 'Chat Control', visa combater o abuso infantil, mas levanta preocupações sobre a privacidade e a criptografia de ponta a ponta. Isso afeta diretamente a segurança da comunicação digital para milhões de usuários na Europa."

Contexto útil. Tom factual. Sem drama.

---

## 6. As 5 camadas de defesa (resumo visual)

```
Camada 1: System Instruction    → "Constituição" com regras PODE/NÃO PODE
Camada 2: Temperatura 0.0       → Elimina improvisação
Camada 3: Schema tipado          → Formulário com limites por campo
Camada 4: Lembrete final         → Constraint antes dos dados (recency bias)
Camada 5: validate_tone()        → Filtro automático rejeita + retry se hype
```

Nenhuma camada sozinha resolve. É a combinação que funciona.

---

## 7. Lições aprendidas

### Para quem trabalha com IA:

**IA não segue intenção, segue estrutura.** Dizer "não exagere" não funciona. Construir um sistema que detecta e rejeita exagero funciona. É a diferença entre pedir pra alguém dirigir devagar e instalar um limitador de velocidade.

**A calibração nunca é linear.** O caminho foi: v2 (exagero) → v3 (seco demais) → v3.1 (equilíbrio). A overcorreção é parte do processo. O ponto certo aparece quando você erra pros dois lados.

**Instruções no texto são sugestões. Estrutura é enforcement.** O modelo ignorou 3 versões de prompt com instruções detalhadas. O que segurou foram mudanças arquiteturais: system instruction, schema tipado, pós-processamento.

**A fronteira entre "explicar" e "inventar" precisa ser explícita.** Pra humanos é óbvio. Pra IA, não. A régua PODE/NÃO PODE desbloqueou o tom certo.

### Para PMs que usam IA como ferramenta:

**O prompt é um produto.** Tem versões, tem bugs, precisa de testes, tem trade-offs. A mesma mentalidade de product development se aplica.

**O output da IA é o MVP, não o produto final.** Pós-processamento, validação, retry — tudo isso é infraestrutura necessária. Confiar cegamente no output é como deployar sem testes.

**Documente o processo, não só o resultado.** O valor está em saber POR QUE algo funciona, não só QUE funciona. Quando a IA encontrar novas formas de escapar (e vai), o diagnóstico é mais rápido.

---

## 8. Da curadoria técnica à curadoria editorial (v4 → v5.2)

Com o tom de voz estabilizado, o próximo desafio foi a qualidade editorial da seleção. O registro completo dessa evolução está em `EDITORIAL_RETROSPECTIVE.md`. Aqui vai o resumo:

### v4 — Framework editorial (26/03)

A edição #001 mostrou que o prompt selecionava por tração, não por relevância. Prediction markets (539pts HN, zero ângulo AI) virou main find enquanto "Gemini importa chats de outros chatbots" ficou relegado.

**Solução:** Discovery por entrevista → framework de 5 steps:

1. **AI Gate** — tem conexão com AI? Se não, só entra se excepcional.
2. **Critérios** — 2 de 3: acionável / sinal de mercado / afeta workflows.
3. **Anti-signal** — descarte imediato: preço consumer, funding genérico, crypto sem AI.
4. **Ranking** — main_find = mais acionável. Tração = tiebreaker (não critério).
5. **Teste final** — completion task: "agora é possível [X]" ou "[player] está [movendo pra] [Y]".

Score do prompt: 5.6 → 8.8/10 após audit técnico.

### v5.0 — Scaling sources (27/03)

4 fontes = echo chamber ocidental. Expansão pra 10:

- **AI Labs (3):** Anthropic, OpenAI, DeepMind blogs — cobertura first-party
- **Geographic (3):** SCMP Tech, Rest of World, TechNode — perspectivas fora do eixo US/EU

Reescrita completa do pre-filter: z-score normalization (engagement comparável entre sources), exponential recency decay (`e^(-age/8)`), cross-source signal (dedup marca em vez de deletar), wild card zone (5 slots aleatórios = exploration).

### v5.2 — Balance + Radar (27/03)

Dois feedbacks do dry run #38:

1. **"Muito conteúdo sobre China"** → weight rebalance (SCMP 1.1→0.9) + geographic diversity cap (max 2 items da mesma região)
2. **"Reddit com conteúdo morno"** → seção RADAR: 1-2 early signals que passaram no AI Gate mas ficaram fora da seleção principal

---

## 9. Timeline do projeto

| Data | Marco |
|------|-------|
| 23/mar/2026 | v1 — Primeiro pipeline funcionando |
| 24/mar/2026 | v2 — Multi-source + primeiro fix de tom |
| 25/mar/2026 | Edição #003 expõe falha: hallucination + sensacionalismo |
| 25/mar/2026 | v3 — System instruction + schema + validate_tone |
| 25/mar/2026 | v3.1 — PODE/NÃO PODE + few-shots contextuais |
| 26/mar/2026 | v4 — Editorial framework (AI Gate + 5-step pipeline) |
| 27/mar/2026 | v5.0 — 10 sources + pre-filter rewrite |
| 27/mar/2026 | v5.2 — Radar section + geographic diversity cap |

---

## 10. Arquitetura de arquivos

```
daily-scout-v3/
├── pipeline.py              ← Pipeline principal (v5.3 — AI Gate + 5-step + Radar)
├── pre_filter.py            ← Pre-filter estatístico (z-score, decay, wild card)
├── requirements.txt         ← Dependências (pydantic, google-genai, jinja2)
├── sources_config.json      ← Config das 10 fontes (on/off, pesos, regions)
├── sources/                 ← Módulos plugáveis de coleta
│   ├── base.py              ← SourceRegistry + SourceItem
│   ├── reddit.py
│   ├── hackernews.py
│   ├── techcrunch.py
│   ├── lobsters.py
│   └── rss_generic.py       ← Módulo genérico RSS (AI labs + geographic)
├── templates/
│   └── email.html           ← Template Jinja2 (inclui seção Radar)
├── social/
│   ├── content_adapter.py   ← Adaptação pra LinkedIn (LINKEDIN_PROMPT)
│   └── linkedin.py          ← API do LinkedIn
├── apps-script/
│   └── Code.gs              ← Google Apps Script do feedback loop
├── .github/workflows/
│   ├── daily-scout.yml      ← Workflow principal (cron diário)
│   └── social-post.yml      ← Workflow de post social (delayed)
├── test_dry_run.py          ← Teste sem LLM (fetch→filter→render)
├── feedback.html            ← 1-click feedback collector (🔥/👍/😐)
├── index.html               ← Newsletter archive UI
├── mobile-preview.html      ← Preview mobile do template
├── aya-avatar.png           ← Avatar da Aya
│
├── DOC_PROCESSO_DAILY_SCOUT.md   ← Este documento (v1 → v5.2)
├── EDITORIAL_RETROSPECTIVE.md    ← Journey editorial v4 → v5.2
├── FEEDBACK_SETUP.md             ← Quick reference do feedback loop
│
└── archive/                 ← Documentos históricos e visualizações
    ├── INSIGHT_*.md          ← Insights de sessões anteriores
    ├── BEFORE_AFTER_*.md     ← Evolução v1 → v2
    ├── PROMPT_FIX_*.md       ← Templates de fix
    └── *.jsx                 ← Visualizações React de audits e análises
```
