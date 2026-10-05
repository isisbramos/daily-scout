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
| 5 | Investigar por que 4 fontes nunca entram | ✅ Investigada; visibilidade corrigida (PR empilhado). Falta decidir fix de cada fonte | Baixo | Baixo |
| 2 | Barra mínima para o destaque principal (main_find) | ✅ No `main` (PR #38) | Baixo | Baixo |
| 3 | Rebaixar funding/valuation/IPO por código (pre_filter) | ✅ Implementada (PR aberto). Panorama/roundup fica para a Rec. 1 | Baixo | Baixo (rebaixa, não exclui) |
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

### Rec. 5 — Investigar as 4 fontes que nunca entram  ✅ (investigação)
- **Método:** log do pipeline de 05/10 (edição #197, run #238) + leitura do código de coleta e do
  pre-filter + teste direto do feed da Anthropic.
- **Resultado — cada fonte morre num ponto diferente do funil:**

| Fonte | Onde morre | Evidência | Natureza |
|---|---|---|---|
| `anthropic_blog` | **Coleta**: 0 itens | `anthropic.com/feed` responde **404** (testado). O log dizia "OK — 0 items" porque `_fetch_rss` engolia o erro em nível DEBUG | **Bug**: fonte morta desde sempre, sem alarme |
| `agencia_brasil` | **Filtro de keywords da própria fonte**: 30 → 0 | Log: "OK — 0 items". Pega as 30 últimas notícias gerais e só mantém as que citam termos de IA; em geral nenhuma cita | Provável excesso de rigor (cobertura é "eventual" por desenho) |
| `qwen_blog` | **Ranking/critério**, com **uma única chance** (janela de 24h) | Coleta 15 itens. Com o pipeline diário, cada post é elegível em exatamente 1 execução; se perder o ranking naquele dia (RSS não tem engajamento) ou cair no STEP 1.5, não volta | Esperado pelo desenho; janela ajustada (abaixo) |
| `ethan_mollick` | Idem | Cadência semanal; ensaio/opinião tende a cair no descarte de "blog pessoal" do STEP 1.5 | Esperado pelo desenho; janela ajustada (abaixo) |

- **Confirmado vs. hipótese:** o 404 da Anthropic e os "0 items" de Anthropic/Agência Brasil estão
  confirmados no log. Para Qwen e Mollick, falta ver o histórico: os arquivos `debug/edition_N_items.json`
  não são commitados (só ficam 30 dias como artifact do Actions).
- **Corrigido (PR empilhado):** falhas de feed agora geram `WARNING` ("fetch error — 404…",
  "feed respondeu mas sem posts"), e a Agência Brasil loga "N raw → M após filtro". Não muda a seleção.
- **Aplicado (PR de ajuste):** (2) Agência Brasil: palavras-chave ampliadas (IA, IA generativa, big techs,
  data center, deepfake, marco legal da IA…) com casamento por palavra inteira ("ia" não casa em
  "polícia") e limite 30→60. (3) Qwen e Mollick: `recency_hours: 72` por fonte (novo campo opcional no
  `sources_config.json`); demais fontes seguem em 24h. Risco: um post aceito pode reaparecer em até 3
  edições; a guarda de repetição da memória editorial (entidades em comum) deve barrar, mas vale
  observar. Medir: quantas vezes Qwen/Mollick/Agência Brasil entram nas próximas 4 semanas.
- **Pendente de decisão:**
  1. **Anthropic (✅ aplicado: feed da comunidade):** não há RSS oficial na URL atual. Opções: feed da comunidade, scraping de
     `anthropic.com/news`, ou desligar a fonte e cobrir via secundárias. Ganho: a Anthropic é a 2ª
     entidade mais citada (11×) e hoje só aparece por reportagem de terceiros.
     **Recomendação:** adotar o feed da comunidade `Olshansk/rss-feeds` (`feed_anthropic_news.xml`).
     Testado em 05/10: responde 200, 265 posts, último de 02/10. Prós: custo mínimo, só trocar a URL.
     Contras: depende de um repositório de terceiros (se parar de atualizar, volta a ficar mudo, mas o
     WARNING novo avisa) e seus títulos entram no prompt da curadoria, então é um canal externo não
     controlado (risco baixo, mas real). Alternativa mais robusta, mais trabalhosa: ler `anthropic.com/news`.
- **Próximo passo de dados:** gravar no `editions.jsonl` (ou num artifact permanente) quantos itens cada
  fonte teve em cada etapa do funil, para parar de depender de logs de 30 dias.

### Rec. 2 — Barra mínima para o main_find  ✅
- **O que é:** o destaque não pode ser um item do Reddit sem corroboração de outra fonte. Se for, a
  edição troca automaticamente pelo primeiro quick_find elegível (que também não repita edição recente).
- **Por quê:** o main_find é a manchete; em 6 dos 105 audits (#111, #113, #140, #190, #195, #196) o destaque
  foi um post do Reddit sem fonte primária. O link do item é sempre o próprio Reddit e o RSS não traz
  score, então "tração" não é verificável: a única barra objetiva é "outra fonte também cobriu".
- **Como funciona:** guard determinístico no pipeline (`pipeline.py`, depois do guard de repetição), sem
  nova chamada de LLM. Funções em `memory_store.py` (`main_find_below_bar`, `find_eligible_quick_find`).
  Fontes cobertas: lista `LOW_TRUST_MAIN_SOURCES` (hoje só `reddit`). Item desconhecido nunca é
  bloqueado; sem candidato à troca, mantém e avisa no log ("Main-find bar: … revisar manualmente").
- **Impacto esperado:** protege a credibilidade da manchete. Não resolve quick_finds do Reddit nem
  panoramas (Recs. 3 e 1).
- **Limites:** o prompt não foi alterado (a regra é só de código); o item rebaixado é descartado, não
  vira quick_find. Se o log mostrar o guard disparando muito, vale pôr a regra também no prompt.
- **Como acompanhar:** `grep "Main-find bar"` nos logs do pipeline.

### Rec. 3 — Rebaixar funding/valuation/IPO por código  ✅
- **O que é:** o `pre_filter.py` multiplica o score de títulos de rodada, valuation ou IPO por 0.5
  (`scoring.funding_penalty` no `sources_config.json`; 1.0 desliga). O item **não é excluído**: só desce no
  ranking, então chega ao LLM apenas se sobrar espaço nos 40 melhores ou for muito forte.
- **Por quê:** o prompt (STEP 3) já manda descartar "empresa X levanta $Y" sem novidade de produto, mas o
  modelo não cumpre de forma confiável. Nos dados: **14 dos 140 falsos positivos dos audits (10%)** e
  **19 dos 478 itens publicados (4%)** são desse tipo (Nscale, XDOF, Mistral €3 bi, Anthropic S-1…).
  Regra mecânica funciona melhor em código do que em texto de prompt.
- **O que conta como funding:** "Série A–F", "seed round", "rodada de investimento", pré-IPO/IPO, S-1,
  valuation, "avaliada em", ou "levanta/raises" + valor em dinheiro.
- **O que NÃO é rebaixado:** título com lançamento/produto ("OpenAI lança X e levanta $Y") ou M&A
  ("Nvidia compra Hugging Face por US$ 12,9B"), e "raises concerns" sem dinheiro. Validei o padrão contra
  os 478 títulos publicados: todos os 19 pegos são funding/IPO/valuation de fato.
- **Impacto esperado:** menos funding ocupando vaga de quick_find e menos conflito no reasoning (o modelo
  nem chega a ver boa parte desses itens). Não toca panoramas/roundups (isso é a Rec. 1).
- **Risco:** um round realmente relevante pode ser rebaixado. Mitigação: ele ainda pode entrar se for muito
  forte (ex.: cross-source), e basta pôr `funding_penalty` em 1.0 para desligar.
- **Como acompanhar:** `grep "Funding demotion"` nos logs do pipeline (lista os títulos rebaixados), e a
  taxa de falsos positivos de funding nos próximos Content Reports.

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
