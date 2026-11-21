# AYA — router

Leia este arquivo antes de qualquer outro. Ele diz o que existe no repo, onde está a verdade de cada assunto e quando ler cada coisa. Não varra o repo inteiro: abra só o que o assunto pede.

## O que é a AYA

Newsletter diária de tech & IA, curada e escrita por uma persona de IA. O pipeline roda sozinho todo dia às 7h55 BRT (GitHub Actions), cura com LLM e envia pelo Buttondown. Site: assineaya.com.br (GitHub Pages).

**Naming:** a marca é só **AYA**. "Daily Scout", "AYA's Daily" e "AYA's Daily Scout" são nomes legados (nome do repo, arquivos antigos). Nunca use em texto novo.

## Estado em 1 minuto

> last-reviewed: 2026-11-19. Atualize esta seção sempre que algo aqui mudar.

- **Disparo do envio:** o cron nativo do Actions (06:37 UTC) atrasa 4,5–10h (média 7h nas 40 execuções de out-nov/2026), então a edição não chega às 7h55. Solução mergeada (PR #59): disparo externo (cron-job.org → `workflow_dispatch`) às 7h55 BRT, com o cron nativo só como fallback e um job `guard` contra envio duplicado e contra segundo e-mail depois de um "transmissão parcial". **Setup feito em 16/11** (job no cron-job.org, 7h55 BRT; teste em dry run OK). **Validado em 18/11:** o disparo externo rodou às 7h55 BRT (ed. 241) e o cron nativo do mesmo dia foi pulado pelo `guard`. Detalhes e falhas em `ops/disparo-externo.md`. Token `aya-dispatch` vence em 15/11/2027: renovar até meados de out/2027.
- **Modelo:** `deepseek-v4-flash`. Fonte da verdade: `llm_config.py`.
- **Editorial:** framework v5.5 (calibração de 17/11, PR #66) com ajustes v5.5.1 (RADAR, #67), v5.5.2 (papers com resumo no input, #68) e v5.5.3 (follow-up controlado no guard de repetição, #69), todos mergeados em 17/11; v5.5.3 em `prompts/curation_template.txt` desde a ed. 241 (18/11); resumo de 650 caracteres e guard do radar (#71, sem mudar prompt) desde a ed. 242 (19/11). **Input do LLM desde a ed. 243 (20/11):** summary do feed em todas as fontes, com herança no dedup (#76); `excerpt` (início do artigo) dos 10 primeiros itens do pre-filter (#79, `article_fetch.py`, liga/desliga em `sources_config.json` → `article_fetch`); warning `[META]` no `validate_tone` contra texto que comenta o input ("o título não diz…", #79). **Redundância entre camadas (21/11, ed. 245+):** assunto lista os protagonistas, Transmissão não reconta o achado, 1ª frase do corpo não reconta o título; guard `[REPEAT]` em `validate_tone` (detalhe em `data/fila-editorial.md`). O freeze de 17/11 foi quebrado em 19/11 por decisão da Isis (ed. 242 escrevia a partir do título); a contagem de 5 edições recomeçou na 243 e, com a mudança de 21/11, recomeça na 245. Revisor final em modo `shadow` (`sources_config.json` → `final_review.mode`).
- **Fontes:** 23 habilitadas. Confira com `python scripts/source_stats.py`.
- **Prioridade editorial:** plano de out/2026 — as 6 recomendações estão concluídas. Estado atual e próximos passos em `data/roadmap.md`.
- **Posicionamento decidido (15/11):** recorte para PMs dentro do Tech Operator, com critério "muda uma decisão de produto", linha "→ No seu trabalho:" (revisada em 17/11, passo 1.1) e pilar 5 (IA, consciência e cultura). Passo 1 (a linha) está em produção desde 15/11 e foi revisada em 17/11 (a medição reinicia), em medição até ~13/12; o passo 2 (critério de curadoria, TESTE DE DECISÃO) entrou na calibração v5.5 de 17/11; o passo 3 (pilar 5) ainda não está no prompt. Ordem e medição em `context/produto.md`.
- **Migração de contexto em andamento:** Fase 2. `context/produto.md`, `context/marca.md`, `context/editorial.md` e `data/` (estado-atual, roadmap, fila editorial, métricas) já migrados; falta mover o resto de `docs/` pra `ops/`. Este mapa é atualizado a cada passo.

## Onde está a verdade

Quando o código e um doc discordarem, o código vence.

| Assunto | Fonte da verdade | Atenção |
| --- | --- | --- |
| Arquitetura, como rodar, CI | `README.md` | |
| Produto, público, métricas | `context/produto.md` | inclui a direção para PMs e as perguntas em aberto |
| Estado do pipeline | código (`llm_config.py`, `sources_config.json`); resumo em `data/estado-atual.md` | `docs/historico/CURRENT_STATE.md` é de maio, só histórico |
| Roadmap | `data/roadmap.md` | junta `docs/historico/ROADMAP.md` + `docs/historico/EDITORIAL_IMPROVEMENT_PLAN.md` |
| Regras editoriais (runtime) | `prompts/` | só muda com dry run (ver regras); o porquê de cada regra está em `context/editorial.md` |
| Fila de ajustes editoriais | `data/fila-editorial.md` | |
| Onde medir cada métrica | `data/metricas.md` | sem números reais |
| Histórico editorial e técnico | `docs/EDITORIAL_RETROSPECTIVE.md`, `docs/DOC_PROCESSO_DAILY_SCOUT.md`, `docs/SOURCES_STUDY.md`, `docs/historico/` | só leitura |
| Marca e visual | `context/marca.md` (resumo) → `~/Documents/isis-brain/10-projetos/newsletter-aya/brand-system/SYSTEM.md` (detalhe); arquivos em `brand-assets/` | a persona anime foi descartada |
| Vault sync | `scripts/README.md` | notícias vão para `07-sinais/` |
| Memória editorial | `memory/README.md` | |
| Qualidade | `reports/` (content report semanal), `debug/` (audit por edição) | |

**Ignore:** `.claude/worktrees/` (cópias antigas do repo), `blueprint/archive-internal/` (histórico de março e abril).

## Quando ler o quê

- **Ajuste editorial** (o que entra, o que sai, tom): `data/fila-editorial.md` → `data/roadmap.md` → `context/editorial.md` (o porquê) → o prompt em `prompts/` (a execução).
- **Fonte nova ou quebrada:** `sources_config.json` + `sources/`.
- **Edição não saiu, saiu tarde ou saiu duplicada:** `ops/disparo-externo.md` (falhas, métricas, reenvio) + `README.md` (seção CI) + `.github/workflows/daily-scout.yml` + `debug/`.
- **Produto, público, posicionamento:** `context/produto.md`.
- **Marca, visual, persona:** `context/marca.md` → `SYSTEM.md` no vault pro detalhe.

## Regras de produção

- Mudança em `prompts/` ou no pipeline só com dry run (`python scripts/manual_dry_run.py`) e `pytest tests/` passando.
- Uma mudança editorial por vez, medida no Content Report seguinte.
- [2026-11-17] Mudança em `prompts/` só entra comparada com a base no replay (`scripts/prompt_replay.py`, ver `scripts/README.md`); uma única edição de teste não é evidência. Editorial congelado até 5 edições reais medidas (exceto bug ou parâmetro).
- Nunca exponha qual modelo de LLM a AYA usa em texto público (site, e-mail, social).
- O repo é público: nada de dados internos (IDs de planilha, métricas de assinantes, notas pessoais) em arquivos versionados.
- Push só quando a Isis pedir. Mudanças entram por PR, que ela aprova.

## Write-back

- Quando a Isis corrigir algo ou vocês tomarem uma decisão, atualize o arquivo certo e diga em 1 linha o que mudou:
  - correção de tom ou critério editorial → `data/fila-editorial.md`
  - decisão com alternativas (stack, marca, posicionamento) → ADR no vault (`04-decisoes/`) + 1 linha em "Estado em 1 minuto" se mudar o estado
  - algo quebrou e foi resolvido → seção de troubleshooting do doc da área (`README.md` ou `scripts/README.md`)
  - mudou estado, modelo, fontes ou prioridade → "Estado em 1 minuto" acima
- Antes de adicionar uma regra, procure uma parecida: edite, não duplique. Regras novas entram com data: `- [2026-11-15] ...`.
- Write-back nunca altera `prompts/` ou o pipeline: isso é mudança de produção e segue as regras acima.

## Manutenção

- Este arquivo tem no máximo 150 linhas. Passou disso, consolide antes de escrever.
- Se `last-reviewed` passar de 30 dias, avise a Isis no início da sessão.
