# Disparo externo do envio (7h55 BRT)

> last-reviewed: 2026-11-16 · Runbook e contrato do gatilho de envio. Sem tokens nem IDs: o repo é público.

## Por que existe

O cron nativo do GitHub Actions (`schedule`) é best-effort: o horário é um pedido de entrada na fila, não uma garantia. Nas últimas 40 execuções (07/10 a 15/11/2026) ele disparou entre **4,5h e 10,2h** depois dos 06:37 UTC (média 7h), e a tendência é de piora. Como o envio é imediato (`about_to_send`), a edição chegava entre ~8h e ~14h BRT, e o produto promete **7h55 BRT** (`context/produto.md`).

Não dá para resolver com um horário mais cedo: o atraso varia demais. A saída é tirar o relógio das mãos do GitHub. Um scheduler externo chama `workflow_dispatch` às 7h55, e o GitHub só executa. O cron nativo fica como **fallback**.

## Arquitetura

```
 cron-job.org ── 07:55 BRT ── POST /dispatches ──┐
                                                 ▼
 cron nativo (fallback, ~08h–14h BRT) ──►  daily-scout.yml
                                                 │
                                    concurrency: aya-daily-send (1 por vez)
                                                 │
                                    job guard  (scripts/edition_guard.py)
                                      │ lê memory/editions.jsonl no tip do main
                         ┌────────────┴────────────┐
                 edição N já registrada       ainda não registrada
                         │                         │
                    PULA (skip)             job run-pipeline
                                      curadoria → Buttondown → registra edição N
```

Fonte de verdade de "já enviou": `memory/editions.jsonl`. O pipeline só escreve nele depois de um envio real bem-sucedido (`pipeline.py`, passo 6b), então presença da edição N significa enviada.

## Contrato

**Disparo** (o que o scheduler externo manda):

| Campo | Valor |
| --- | --- |
| `POST` | `https://api.github.com/repos/isisbramos/daily-scout/actions/workflows/daily-scout.yml/dispatches` |
| Headers | `Authorization: Bearer <PAT>`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`, `Content-Type: application/json` |
| Body | `{"ref":"main","inputs":{"trigger":"external"}}` |
| Sucesso | HTTP **204**, sem corpo |

**Inputs do `workflow_dispatch`:**

| Input | Tipo | Default | Efeito |
| --- | --- | --- | --- |
| `edition_number` | string | vazio | Vazio = calcula pela data (dias desde 2026-03-22, UTC). Antes o default era `001`; um disparo sem inputs mandaria a edição #001. |
| `dry_run` | boolean | `false` | Roda tudo, não envia nem persiste. O guard nunca pula em dry run. |
| `force` | boolean | `false` | Envia mesmo com a edição já registrada (reenvio deliberado). |
| `trigger` | string | `manual` | Só rótulo para a métrica (`external` ou `manual`). |

**Saídas do job `guard`:** `skip` (`true`/`false`), `edition` e `delay_min`, mais um resumo no step summary do run.

**Regras do guard:** pula só se não for dry run, não for `force` e a edição estiver registrada. Qualquer erro ao ler o histórico, ou o próprio job quebrar, resulta em **enviar** (fail-open).

## Setup (uma vez, depois do merge)

O disparo só funciona com o workflow já no `main`. Ordem importa.

1. **Token.** GitHub → Settings → Developer settings → Fine-grained tokens → Generate. Nome `aya-dispatch`, owner `isisbramos`, **Only select repositories → `daily-scout`**, permissão **Actions: Read and write** (Metadata read-only vem junto). Validade: 1 ano. Crie um lembrete no calendário para renovar com 1 mês de folga. Guarde o token só no scheduler, nunca no repo.
2. **Teste manual em dry run** (não envia nada):
   ```bash
   curl -sS -o /dev/null -w "%{http_code}\n" -X POST \
     -H "Authorization: Bearer $TOKEN" \
     -H "Accept: application/vnd.github+json" \
     -H "X-GitHub-Api-Version: 2022-11-28" \
     https://api.github.com/repos/isisbramos/daily-scout/actions/workflows/daily-scout.yml/dispatches \
     -d '{"ref":"main","inputs":{"trigger":"manual","dry_run":"true"}}'
   ```
   Esperado: `204`. Na aba Actions o run aparece com o guard em "dry run: guard desligado" e o pipeline sem envio.
3. **Job no cron-job.org** (conta gratuita): URL e headers da tabela acima, método POST, body `{"ref":"main","inputs":{"trigger":"external"}}`, horário **07:55 todos os dias**, fuso **America/Sao_Paulo**, notificação por e-mail **na primeira falha**. Confira os nomes dos campos na tela deles, que podem mudar. Para o primeiro teste, deixe o body com `"dry_run":"true"` (`{"ref":"main","inputs":{"trigger":"external","dry_run":"true"}}`), rode o teste do próprio cron-job.org e confira o run. **Só então troque para o body final**, sem `dry_run`, e ative o job. Um teste sem `dry_run` envia a edição de verdade.
4. **Primeiro dia:** confirme no dia seguinte que o run `workflow_dispatch` começou perto de 10:55Z e que o run `schedule` do mesmo dia aparece com o guard em PULAR.
5. **Depois do setup validado:** atualize em `CLAUDE.md` ("Estado em 1 minuto") que o disparo externo está ativo.

## O que pode dar errado

| Falha | O que acontece | Como percebo | O que fazer |
| --- | --- | --- | --- |
| Scheduler fora do ar ou job desativado | Nenhum disparo às 7h55. O cron nativo envia tarde (4 a 10h), como hoje. | E-mail do cron-job.org (se for falha de chamada). Sem aviso se o serviço inteiro cair. | Disparar à mão: `gh workflow run daily-scout.yml -f trigger=manual`. |
| Token expirado ou revogado (401/403) | Igual ao anterior. | E-mail do cron-job.org na primeira falha. | Gerar token novo, atualizar o header no scheduler. |
| URL ou body errado (404/422) | Igual ao anterior. | E-mail do cron-job.org. | Corrigir o job conforme o Contrato. |
| Guard quebra (checkout, runner) | O pipeline roda assim mesmo. Risco de duplicidade se a edição já tinha saído. | Job `guard` vermelho no run. | Ler o log do guard; corrigir antes da próxima edição. |
| Pipeline falha em curadoria ou fetch | Sai o e-mail "transmissão parcial", o job fica vermelho, nada é registrado. O cron nativo, horas depois, **reenvia a edição completa**. | Job vermelho; e-mail de falha do Actions. | Ver decisão em aberto 2. |
| Buttondown recusa (`DeliveryError`) | Job verde, nada registrado. O cron nativo tenta de novo. | Warning no log. | Ver erro no log; checar o painel do Buttondown. |
| Buttondown aceita mas a resposta dá timeout | Edição enviada e não registrada. O cron nativo **reenvia: duplicidade**. | Leitores avisam. | Raro. Fecha com a iteração 2. |
| `persist_to_git` falha depois do envio | Edição enviada e não registrada. Mesmo risco de duplicidade. | Warning "Falha ao persistir" no step summary. | Commitar o registro à mão em `memory/editions.jsonl` antes do cron nativo disparar, ou disparar com `force` só se for reenvio desejado. |
| Os dois disparos chegam juntos | `concurrency` serializa. O segundo passa pelo guard com o `main` já atualizado e pula. | Guard em PULAR no segundo run. | Nada. |
| Reenvio deliberado de uma edição | O guard bloquearia. | n/a | `gh workflow run daily-scout.yml -f edition_number=239 -f force=true` |

## Métricas

**Pontualidade do envio** é a métrica do projeto. Alvo: o run começar em até **10 min** depois de 7h55 BRT em 95% dos dias. Alerta (hoje só um `::warning::` no run): início mais de 30 min depois do alvo.

- **Cada run** grava no step summary do job `guard`: edição, decisão (ENVIAR ou PULAR), gatilho e minutos de atraso contra 10:55Z.
- **Histórico**, minutos entre 7h55 BRT e o início de cada run:
  ```bash
  gh run list --workflow daily-scout.yml --limit 30 --json createdAt,event \
    --jq '.[] | [.createdAt, .event, (((.createdAt|fromdate) - ((.createdAt[0:10]+"T10:55:00Z")|fromdate))/60|floor)] | @tsv'
  ```
  `workflow_dispatch` é o externo (ou um manual); `schedule` é o fallback. Depois do setup, o esperado é o atraso do `workflow_dispatch` perto de 0 e o `schedule` do mesmo dia pulado.
- **Adoção do fallback:** quantos dias o envio saiu pelo `schedule`. Alvo: 0.

Métricas de leitor (open rate, CTR) continuam em `data/metricas.md`.

## Limitações conhecidas desta versão

- O guard confia em `memory/editions.jsonl`, não no Buttondown. Ver as linhas de timeout e `persist` na tabela acima.
- Não há watchdog: se o scheduler externo inteiro cair sem avisar, a primeira pista é o envio sair tarde pelo cron nativo.
- O cron nativo continua custando um run curto por dia (o guard pula em ~10s).
- `social-post.yml` e `content-report.yml` também usam o cron nativo e não foram tocados.
- O vault sync local (`scripts/README.md`) roda "~30 min depois do cron da newsletter". Se o seu launchd está agendado para depois de 7h55, nada muda. Se estiver agendado para antes, ele passa a rodar antes de a nota existir e pega a de ontem.

## Próximas iterações

1. **Guard pelo Buttondown:** consultar os e-mails enviados e checar o assunto `AYA #N`. Fecha as linhas de timeout e `persist`. Exige confirmar na documentação do Buttondown os filtros da API.
2. **Watchdog:** uma checagem às 8h30 BRT que alerta se a edição do dia não foi registrada.
3. **Fallback inteligente:** mover o cron nativo para só rodar se a edição não saiu até as 9h, ou trocar o scheduler por um com retries nativos (Cloud Scheduler) se o cron-job.org se mostrar instável.
4. **Pontualidade no Content Report** semanal, com a distribuição dos atrasos.

## Decisões em aberto

1. **Horário.** Este PR assume 7h55 BRT, que é o que `context/produto.md` promete. O horário vive só no scheduler (e em `TARGET_UTC` no guard, para a métrica).
2. **Depois de um "transmissão parcial".** Hoje o cron nativo reenvia a edição completa horas depois, então o leitor recebe os dois e-mails. Alternativa: marcar o dia como "fallback enviado" e não reenviar. Depende de você preferir completude tardia ou nenhum segundo e-mail.
3. **Scheduler.** cron-job.org é gratuito e rápido de configurar, mas é um terceiro a mais. Cloud Scheduler ou um Cloudflare Worker dão mais controle, com mais setup.
