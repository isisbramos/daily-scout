# AYA — Relatório de Conteúdo

**Gerado:** 2026-06-29 12:32 BRT  
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

A AYA está operando com diversidade temática excessiva (8 temas em 7 edições) e dependência excessiva de fontes mainstream (TechCrunch/SCMP dominam 11 de 19 citações), gerando cobertura rasa e sem aprofundamento. O feedback "fire" (5 de 6) sugere que o público valoriza a curadoria, mas a ausência de fontes técnicas (arxiv, blogs de labs) e a alta proporção especulativa (33%) indicam risco de viés para notícias quentes em detrimento de análises fundamentadas. A repetição de entidades (OpenAI em 7/7 edições) cria monotonia estrutural.

## Recomendações

### P0 – Diversificar fontes técnicas para reduzir especulação
- **O que**: Substituir 2 das 6 citações do TechCrunch por fontes da lista `never_used_sources` (prioridade: `arxiv_ai`, `huggingface_papers`, `anthropic_blog`).
- **Por que**: 33% especulativo vs 67% confirmado é alto para uma newsletter de IA. Fontes primárias (papers, blogs de labs) reduzem ruído e aumentam credibilidade. TechCrunch já cobre 31% das fontes usadas – saturação.
- **Alavanca**: No prompt, adicionar regra: "Para cada tema, inclua ao menos 1 fonte primária (arxiv, blog de lab, paper) antes de fontes jornalísticas."

### P1 – Reduzir cobertura da OpenAI para liberar espaço temático
- **O que**: Limitar menções à OpenAI a no máximo 3 por edição (atualmente 7/7 edições = 100%).
- **Por que**: A entidade domina 100% das edições, mas temas como "interface cérebro-computador" e "padrões de segurança" aparecem apenas 1 vez cada. Isso cria viés de cobertura e cansaço do leitor.
- **Alavanca**: No prompt, incluir: "Se OpenAI aparecer em mais de 3 parágrafos, substitua 1 parágrafo por cobertura de entidade não-OpenAI com relevância similar (ex: DeepSeek, Anthropic, Mistral)."

### P1 – Aumentar profundidade temática com séries de 2-3 edições
- **O que**: Agrupar temas correlatos em mini-séries (ex: "agentes de IA" em 2 edições consecutivas, com progressão de básico para avançado).
- **Por que**: 8 temas em 7 edições = 1.14 temas/edição, sem repetição. Isso impede aprofundamento. O feedback "solid" (1/6) pode indicar falta de valor agregado em temas superficiais.
- **Alavanca**: No prompt, adicionar: "Se um tema apareceu nos últimos 3 dias, priorize aprofundamento (dados, comparações, implicações) em vez de novo tema."

### P2 – Incorporar fontes brasileiras para diferenciação regional
- **O que**: Usar `agencia_brasil` e `mit_tech_review_brasil` em pelo menos 1 edição a cada 3.
- **Por que**: `mit_tech_review_brasil` foi usado apenas 1 vez, `agencia_brasil` nunca. A newsletter tem público brasileiro – ignorar fontes locais perde relevância contextual e diferenciação frente a agregadores globais.
- **Alavanca**: No prompt, incluir: "Para cada edição, verifique se há notícia relevante em `agencia_brasil` ou `mit_tech_review_brasil`; se sim, priorize como fonte principal."

### P2 – Reduzir especulação com regra de "confirmação dupla"
- **O que**: Para qualquer afirmação marcada como "especulativo", exigir 2 fontes independentes ou 1 fonte primária + 1 secundária.
- **Por que**: 33% especulativo é alto para uma newsletter que busca ser referência. Semântica de "especulativo" não está calibrada – pode estar sendo usado para notícias não confirmadas, o que erosiona confiança.
- **Alavanca**: No prompt, adicionar: "Se o conteúdo for especulativo, cite explicitamente 2 fontes ou justifique por que a especulação é relevante (ex: tendência identificada por múltiplos labs)."

---

*Gerado por `content_report.py` — Daily Scout Content Report v1.0*