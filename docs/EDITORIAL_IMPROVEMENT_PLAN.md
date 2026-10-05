# Plano de melhoria editorial — out/2026

> Origem: Content Report de 05/10/2026 (30 edições, #167–#196) + conferência manual dos dados.
> Status geral: **em execução** — Rec. 4 implementada; as demais aguardam, uma por vez.

## Diagnóstico em uma frase

A AYA não sofre de falta de regras — o prompt já proíbe funding, panorama e opinião. O problema é que
**ela conhece as regras e não as cumpre**: o reasoning diz uma coisa e a edição publicada faz outra.

```
O que a AYA DIZ (reasoning)                 O que a AYA FAZ (edição publicada)
"Anthropic + líderes religiosos passa ✅" → ❌ não aparece na edição (#196)
"Saída de safety da OpenAI passa ✅"      → ❌ não aparece na edição (#196)
"Roundups são descartados"                → ✅ publica 2 panoramas (#195, #196)
(nada sobre o post do Reddit)             → ⭐ main_find = post anônimo, score 0 (#196)
```

Números: nota média 2.23/5. Pontos mais fracos: **Editorial 2.17** e **Reasoning 2.27**.
Mais fortes: Diversidade 3.33, Tom 3.17, Intro 3.60.

## Recomendações

| # | Recomendação | Status | Esforço | Risco |
|---|---|---|---|---|
| 4 | Registrar a fonte de cada item e validar o "juiz" contra o feedback do leitor | ✅ Implementada (branch `claude/editorial-improvement-plan`) | Baixo | Baixo |
| 5 | Investigar por que 4 fontes nunca entram | ⏳ Próxima | Baixo | Baixo |
| 2 | Barra mínima para o destaque principal (main_find) | ⏳ Planejada | Baixo | Baixo |
| 3 | Barrar funding/panorama por código (pre_filter) | ⏳ Planejada | Baixo | Médio (excluir funding relevante) |
| 1 | "Revisor final": comparar o que a AYA disse com o que publicou | ⏳ Planejada | Médio | Médio (custo extra) |

Ordem: uma mudança por vez, medindo no Content Report semanal seguinte.

### Rec. 4 — Registrar fonte por item + validar o juiz  ✅
- **O que é:** (a) gravar a fonte de cada item publicado (hoje só existe a lista de fontes da edição);
  (b) comparar a nota do audit (juiz LLM) com o feedback real dos leitores.
- **Por quê:** sem (a), qualquer regra de "teto de itens por fonte" é palpite — não dá para saber se
  uma fonte domina uma edição. Sem (b), corremos o risco de otimizar uma nota que o leitor não sente.
- **Impacto:** decisões sobre diversidade de fontes passam a ser baseadas em número; e sabemos quanto
  confiar na nota do audit antes de reescrever prompts para melhorá-la.
- **Como foi feito:** `memory_store.py` grava `source` em `main_find` e em cada `quick_find`
  (a partir da ed.197); `content_report.py` ganhou "Concentração de fonte por edição" e
  "Juiz × leitor". Testes em `tests/`.
- **Primeira leitura de Juiz × leitor** (10 edições, 14 votos, ed. ≥169): edições nota 2/5 → feedback
  médio 0.8; nota 3/5 → 1.17; correlação 0.28. Ou seja, **há uma relação fraca a moderada** — o juiz
  tem algum sinal, mas amostra é minúscula. *(Corrige uma leitura anterior, mais pessimista, que
  incluía edições antigas com votos contaminados por scanners de email.)* Reavaliar quando houver ~30 pares.
- **Como acompanhar:** seção "Concentração de fonte" só fica populada após algumas edições novas.

### Rec. 5 — Investigar as 4 fontes que nunca entram
- **O que é:** descobrir onde `anthropic_blog`, `qwen_blog`, `ethan_mollick` e `agencia_brasil`
  morrem no funil (coleta, pre-filter, STEP 1.5, ranking), antes de "ativar" qualquer coisa.
- **Por quê:** a Anthropic é a 2ª entidade mais citada (11×) mas o blog dela nunca é a fonte.
  Hipótese (não verificada): o STEP 1.5, que desconfia de blogs corporativos, os descarta.
- **Impacto:** se for excesso de rigor, a AYA passa a cobrir a Anthropic na fonte primária; se for
  proposital, evitamos mexer à toa.

### Rec. 2 — Barra mínima para o main_find
- **O que é:** o destaque não pode ser post de Reddit/fórum sem fonte primária ou corroboração.
- **Por quê:** é a manchete; na #196 foi um post anônimo com score 0, na #195 uma alegação de um
  lado só. Um erro aqui pesa muito mais que num quick_find.
- **Impacto:** protege a credibilidade; sem candidato forte, escolhe-se o melhor item verificável.

### Rec. 3 — Barrar funding/panorama por código
- **O que é:** o `pre_filter.py` rebaixa títulos óbvios ("levanta US$ X", "Série B", "valuation").
- **Por quê:** regra mecânica é mais confiável em código que em texto de prompt. Falsos positivos
  recorrentes: Nscale, XDOF, Anthropic S-1.
- **Impacto:** zero funding por descuido e menos conflito no reasoning. **Rebaixar, não excluir**,
  porque alguns rounds são relevantes. Pendência: checar o que o pre_filter já faz hoje.

### Rec. 1 — "Revisor final" (maior alavanca)
- **O que é:** após montar a edição, um passo extra confere se cada item "aprovado" entrou e se
  cada item publicado passa nas regras; se não bater, corrige antes de enviar.
- **Por quê:** é a causa raiz de Editorial e Reasoning, os eixos mais fracos (#195: 10+ itens
  aprovados sumiram sem explicação).
- **Impacto:** esperado nos dois eixos mais fracos; custo: uma chamada extra de LLM por edição.

## O que NÃO vamos fazer (por ora)

- **Recalibrar o ranking pelo feedback por tema:** ~22 ratings em 12 edições — temas com média 2.0
  provavelmente têm 1–2 votos. Além disso, favorecer só o que já engaja cria bolha e mata descoberta.
  Reavaliar com mais dados.
- **"Reescrever o AI Gate" como P0:** a regra já existe no prompt; o problema é cumprimento
  (coberto pelas Recs. 1–3), não ausência de regra.
- **Aceitar sem checar a síntese do DeepSeek:** ela citou "60 hipóteses recorrentes", mas esse 60 é a
  contagem de pares de edições repetidas; no scorecard só 2 hipóteses se repetem (2×).

## Como medir sucesso

Content Report semanal (seg. 9:00 BRT): Editorial e Reasoning ↑ (meta inicial: ≥ 2.6), falsos
negativos de TechCrunch/HN/SCMP ↓, zero funding/panorama nos quick_finds auditados, e a correlação
Juiz × leitor estável ou crescente.
