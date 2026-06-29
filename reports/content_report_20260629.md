# AYA — Relatório de Conteúdo

**Gerado:** 2026-06-29 11:43 BRT  
**Janela:** 7 edições (2026-06-23 → 2026-06-29)

> Avaliação editorial da AYA *através das edições*: o que cobre, com qual diversidade, como o feedback responde e como a qualidade evolui.

---

## 1. Tendências de Conteúdo

### Temas recorrentes

| Tema | Edições | |
|---|---|---|
| modelos de vídeo e código aberto | 1 | `████████████████` |
| agentes de IA e mercado de trabalho | 1 | `████████████████` |
| geopolítica da IA (EUA vs China) | 1 | `████████████████` |
| custo e eficiência de IA | 1 | `████████████████` |
| agentes de IA | 1 | `████████████████` |
| China e infraestrutura de AI | 1 | `████████████████` |
| interface cérebro-computador | 1 | `████████████████` |
| padrões de segurança para AI avançada | 1 | `████████████████` |
| regulação de IA | 1 | `████████████████` |
| infraestrutura de IA | 1 | `████████████████` |

### Entidades mais citadas

`OpenAI (7)` · `TechCrunch (4)` · `DeepSeek (3)` · `Anthropic (3)` · `Alibaba (2)` · `MIT Tech Review Brasil (2)` · `Claude (2)` · `Zhipu AI (2)` · `governo dos EUA (2)` · `China (2)` · `Ford (2)` · `HappyHorse 1.1 (1)`

### Distribuição de fontes

| Fonte | Usos | |
|---|---|---|
| techcrunch | 6 | `████████████████` |
| scmp_tech | 5 | `█████████████···` |
| hackernews | 4 | `███████████·····` |
| openai_blog | 2 | `█████···········` |
| mit_tech_review_brasil | 1 | `███·············` |
| reddit | 1 | `███·············` |

**Fontes habilitadas nunca selecionadas (16/22):** `agencia_brasil`, `anthropic_blog`, `arxiv_ai`, `deepmind_blog`, `ethan_mollick`, `huggingface_blog`, `huggingface_papers`, `lobsters`, `meta_ai_blog`, `mistral_releases`, `mit_tech_review`, `qwen_blog`, `rest_of_world`, `simon_willison`, `stratechery`, `technode`

### Mix epistêmico (claim_status)

**confirmado** 67% · **especulativo** 33%

### Feedback coletado

🔥 5 · 👍 1  (5 edições com rating)


_Média de feedback por tema:_

- modelos de vídeo e código aberto: **2.0**
- agentes de IA e mercado de trabalho: **2.0**
- geopolítica da IA (EUA vs China): **2.0**
- custo e eficiência de IA: **2.0**
- regulação de IA: **2.0**
- infraestrutura de IA: **2.0**
- modelos de código: **2.0**
- segurança de IA: **2.0**
- modelos de código aberto: **1.0**
- segurança em IA: **1.0**
- competição China-EUA: **1.0**
- aplicações de IA em saúde: **1.0**

### Repetição entre edições

8 par(es) com sobreposição ≥2 entidades:

- ed.093 (2026-06-23) ↔ ed.095 (2026-06-25) — compartilham: alibaba, openai
- ed.094 (2026-06-24) ↔ ed.095 (2026-06-25) — compartilham: openai, techcrunch
- ed.093 (2026-06-23) ↔ ed.096 (2026-06-26) — compartilham: deepseek, openai
- ed.095 (2026-06-25) ↔ ed.097 (2026-06-27) — compartilham: anthropic, openai
- ed.095 (2026-06-25) ↔ ed.099 (2026-06-29) — compartilham: anthropic, claude, openai
- ed.096 (2026-06-26) ↔ ed.099 (2026-06-29) — compartilham: openai, zhipu ai
- ed.097 (2026-06-27) ↔ ed.099 (2026-06-29) — compartilham: anthropic, china, openai
- ed.098 (2026-06-28) ↔ ed.099 (2026-06-29) — compartilham: ford, openai

---

## 2. Scorecard de Qualidade

_Nenhum audit encontrado em `debug/`._ Rode o audit_agent primeiro para popular esta seção:

```bash
python audit_agent.py --all      # precisa de DEBUG_SAVE=true no pipeline
```

---

## 3. Insights — Como Melhorar a AYA

### Diagnóstico determinístico

- **Fontes ociosas:** 16 de 22 fontes habilitadas nunca foram selecionadas na janela (agencia_brasil, anthropic_blog, arxiv_ai, deepmind_blog, ethan_mollick, huggingface_blog, huggingface_papers, lobsters…). Avalie se geram ruído no pre-filter ou se o peso precisa de ajuste.
- **Repetição entre edições:** 8 par(es) de edições com sobreposição ≥2 entidades. A memória editorial barra quick_finds, mas main_finds repetidos só são logados — vale revisar se a regra precisa endurecer.
- **Feedback × tema:** «modelos de vídeo e código aberto» tem a melhor média (2.0) e «modelos de código aberto» a pior (1.0). Sinal pra dobrar no que engaja e revisar o que não pega.

### Síntese editorial (DeepSeek)

## Diagnóstico

A newsletter está excessivamente dependente de **TechCrunch (6/7 edições) e SCMP (5/7)**, ignorando 16 fontes relevantes (incluindo blogs oficiais da Anthropic, DeepMind, Meta AI, ArXiv e Stratechery). O conteúdo é **100% especulativo ou confirmado** (67% confirmado, 33% especulativo), sem fontes primárias ou papers. O feedback é **artificialmente uniforme** (todos os temas com nota 2.0), sugerindo que a métrica não discrimina — e o baixo número de reações (5 fire, 1 solid) indica baixo engajamento real. A diversidade temática é alta (8 temas em 7 edições), mas a profundidade é sacrificada: nenhum tema se repete, o que impede a construção de autoridade em nichos.

---

## Recomendações

### P0 – Diversificar fontes para reduzir viés e aumentar profundidade
**Alavanca:** Adicionar **3 fontes nunca usadas** como obrigatórias no prompt: `anthropic_blog`, `arxiv_ai`, `stratechery`.  
**Por quê:** TechCrunch e SCMP são jornalismo generalista; ArXiv e blogs oficiais trazem dados primários e análises de ponta. Stratechery oferece contexto estratégico (geopolítica, negócios) que falta nas edições atuais. Isso quebra a uniformidade temática e aumenta a credibilidade.

### P0 – Corrigir o sistema de feedback para gerar dados acionáveis
**Alavanca:** Substituir a escala atual (fire/solid) por **3 dimensões numéricas (1-5)** no prompt: `profundidade`, `relevância prática`, `novidade`.  
**Por quê:** O feedback atual é inútil — todos os temas recebem nota 2.0, indicando que a métrica não discrimina. Sem dados reais, não é possível priorizar temas ou ajustar tom. A nova escala permitirá identificar padrões (ex.: temas com alta novidade mas baixa profundidade).

### P1 – Reduzir especulação e aumentar fontes primárias
**Alavanca:** No prompt, exigir que **pelo menos 1 fonte primária** (paper, blog oficial, release técnico) seja citada por edição, com link direto.  
**Por quê:** 33% do conteúdo é especulativo, e 0% vem de fontes como ArXiv ou blogs de pesquisa. Isso enfraquece a autoridade da newsletter. Exigir uma fonte primária força a curadoria de conteúdo mais denso e verificável.

### P1 – Criar séries temáticas recorrentes para construir autoridade
**Alavanca:** No prompt, incluir regra: **"A cada 3 edições, retorne a um dos 3 temas com maior feedback médio"** (usando a nova métrica do P0).  
**Por quê:** Atualmente, 8 temas em 7 edições — nenhum se repete. Isso impede que a newsletter se torne referência em algo. Repetir temas permite aprofundamento, comparação temporal e fidelização de leitores interessados.

### P2 – Aumentar o uso de fontes brasileiras para diferenciação regional
**Alavanca:** Adicionar `agencia_brasil` e `mit_tech_review_brasil` como fontes obrigatórias **a cada 2 edições**.  
**Por quê:** A newsletter é em português, mas 0% das fontes são brasileiras. Isso é um diferencial competitivo inexplorado. A Agência Brasil cobre regulação e políticas públicas nacionais; MIT Tech Review Brasil traz curadoria local. Isso pode aumentar o engajamento do público brasileiro.

---

*Gerado por `content_report.py` — Daily Scout Content Report v1.0*