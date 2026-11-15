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

## O que fica em `debug/`

`debug/` guarda o audit por edição (`edition_N_audit.json`, `edition_N_review.json`) — isso é qualidade editorial (alinhamento, tom, diversidade, veredito do revisor final), não métrica de leitor. Entra no Content Report (`reports/`) como scorecard de qualidade, cruzado com o feedback real (ver linha "Feedback ratio" acima), mas não substitui nenhuma das 8 métricas de produto.

## O que não está instrumentado no repo

CTR, open rate, novos assinantes, unsubscribe e retenção dependem inteiramente do painel do Buttondown — não há coleta própria no código além da Camada 2 de tracking (desligada). Antes de cobrar essas métricas de alguém, confirme se o analytics do Buttondown já está ativo (item pendente em `data/roadmap.md`).
