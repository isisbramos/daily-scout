# Onde medir cada métrica

> last-reviewed: 2026-11-15 · Mapa de onde checar cada métrica da tabela em `context/produto.md`. Sem números reais e sem ID de planilha — isso fica fora do repo, que é público.

| Métrica (de `context/produto.md`) | Onde medir | Como |
| --- | --- | --- |
| CTR (North Star A) | Buttondown | Analytics nativo do Buttondown, por edição. Pré-requisito pendente: ativar analytics (ver `data/roadmap.md`). |
| Engaged subs (North Star B) | Buttondown | Segmento de quem abriu ou clicou nos últimos 14 dias — relatório do Buttondown. |
| Novos assinantes por semana (Growth) | Buttondown | Painel de assinantes do Buttondown. |
| Open rate (Surface health) | Buttondown | Analytics nativo, por edição. |
| Unsubscribe por edição (Quality signal) | Buttondown | Analytics nativo, por edição. |
| Feedback ratio (Editorial fit) | Sheet de feedback → `reports/` | Votos 🔥/👍/😐 coletados por `feedback.html`, armazenados na planilha (ID em `feedback_join.py` e `apps-script/Code.gs`, não repetido aqui). `feedback_join.py` junta isso em `memory/editions.jsonl` (campo `feedback_score`); o Content Report semanal (`content_report.py` → `reports/`) agrega a série e cruza com a nota do audit agent ("Juiz × leitor"). |
| Retenção de leitura em 30 dias (Retention) | Buttondown | Depende de analytics ativado; sem instrumentação própria no repo. |
| % de assinantes que clicam ≥ 1 link/semana (Click distribution) | Buttondown | Analytics nativo. Complemento possível: a Camada 2 de tracking de clique por achado (`pipeline.py`, filtro `track`), hoje desligada por falta de `TRACK_BASE_URL` — ver `data/estado-atual.md`. |

## Métrica operacional: pontualidade do envio

Não é métrica de produto, mas sustenta a promessa de "7h55 BRT" de `context/produto.md`. Mede o atraso entre 7h55 BRT e o início do run que enviou a edição. Alvo: início em até 10 min depois do horário em 95% dos dias. Onde medir: step summary do job `guard` em cada run, e o histórico com `gh run list` (comando em `ops/disparo-externo.md`, seção Métricas). Fica fora do Content Report até a iteração 4 daquele doc.

## Métrica operacional: qualidade do input e do texto

Desde a ed. 243 (#76, #79). Não é métrica de produto: diz se o LLM está escrevendo a partir da matéria ou só do título.

- **`[META]` por edição.** Alvo: zero. É o texto que comenta o input ("o título não diz…"). Onde medir: o log do run em `daily-scout.yml` (linhas `[META]`; cada uma gera um retry) e, depois do envio, a nota da edição em `vault-outbox/` (regex `META_INPUT_PATTERNS` em `pipeline.py`). Linha de base: 6 de 82 notas com o padrão até a ed. 242.
- **Taxa de excerpt.** Linha `Article excerpts: X/Y ok` no log do run. Se ficar abaixo de ~50%, revisar `SKIP_HOSTS` e o extractor em `article_fetch.py` pelos domínios que aparecem em `[EXCERPT] sem trecho`.

## O que fica em `debug/`

`debug/` guarda o audit por edição (`edition_N_audit.json`, `edition_N_review.json`) — isso é qualidade editorial (alinhamento, tom, diversidade, veredito do revisor final), não métrica de leitor. Entra no Content Report (`reports/`) como scorecard de qualidade, cruzado com o feedback real (ver linha "Feedback ratio" acima), mas não substitui nenhuma das 8 métricas de produto.

## O que não está instrumentado no repo

CTR, open rate, novos assinantes, unsubscribe e retenção dependem inteiramente do painel do Buttondown — não há coleta própria no código além da Camada 2 de tracking (desligada). Antes de cobrar essas métricas de alguém, confirme se o analytics do Buttondown já está ativo (item pendente em `data/roadmap.md`).
