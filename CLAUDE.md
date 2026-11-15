# AYA — router

Leia este arquivo antes de qualquer outro. Ele diz o que existe no repo, onde está a verdade de cada assunto e quando ler cada coisa. Não varra o repo inteiro: abra só o que o assunto pede.

## O que é a AYA

Newsletter diária de tech & IA, curada e escrita por uma persona de IA. O pipeline roda sozinho todo dia às 7h55 BRT (GitHub Actions), cura com LLM e envia pelo Buttondown. Site: assineaya.com.br (GitHub Pages).

**Naming:** a marca é só **AYA**. "Daily Scout", "AYA's Daily" e "AYA's Daily Scout" são nomes legados (nome do repo, arquivos antigos). Nunca use em texto novo.

## Estado em 1 minuto

> last-reviewed: 2026-11-15. Atualize esta seção sempre que algo aqui mudar.

- **Modelo:** `deepseek-v4-flash`. Fonte da verdade: `llm_config.py`.
- **Editorial:** framework v5.4 em `prompts/curation_template.txt`. Revisor final em modo `shadow` (`sources_config.json` → `final_review.mode`).
- **Fontes:** 23 habilitadas. Confira com `python scripts/source_stats.py`.
- **Prioridade editorial:** plano de out/2026 em `docs/EDITORIAL_IMPROVEMENT_PLAN.md`.
- **Posicionamento decidido (15/11):** recorte para PMs dentro do Tech Operator, com critério "muda uma decisão de produto", linha "→ No seu produto:" e pilar 5 (IA, consciência e cultura). Passo 1 (a linha) está em produção desde 15/11, em medição até ~13/12; passos 2 (critério de curadoria) e 3 (pilar 5) ainda não estão no prompt. Ordem e medição em `context/produto.md`.
- **Migração de contexto em andamento:** Fase 2. `context/produto.md` já migrado; o resto de `docs/` vai para `context/`, `ops/` e `data/`, e este mapa é atualizado a cada passo.

## Onde está a verdade

Quando o código e um doc discordarem, o código vence.

| Assunto | Fonte da verdade | Atenção |
| --- | --- | --- |
| Arquitetura, como rodar, CI | `README.md` | |
| Produto, público, métricas | `context/produto.md` | inclui a direção para PMs e as perguntas em aberto |
| Estado do pipeline | código (`llm_config.py`, `sources_config.json`) | `docs/CURRENT_STATE.md` é de maio |
| Roadmap | `docs/ROADMAP.md` + `docs/EDITORIAL_IMPROVEMENT_PLAN.md` | |
| Regras editoriais (runtime) | `prompts/` | só muda com dry run (ver regras); o porquê de cada regra está em `context/editorial.md` |
| Fila de ajustes editoriais | `docs/EDITOR_NOTES.md` | |
| Histórico editorial e técnico | `docs/EDITORIAL_RETROSPECTIVE.md`, `docs/DOC_PROCESSO_DAILY_SCOUT.md`, `docs/SOURCES_STUDY.md`, `docs/historico/` | só leitura |
| Marca e visual | `~/Documents/isis-brain/10-projetos/newsletter-aya/brand-system/SYSTEM.md`; arquivos em `brand-assets/` | a persona anime foi descartada |
| Vault sync | `scripts/README.md` | notícias vão para `07-sinais/` |
| Memória editorial | `memory/README.md` | |
| Qualidade | `reports/` (content report semanal), `debug/` (audit por edição) | |

**Ignore:** `.claude/worktrees/` (cópias antigas do repo), `blueprint/archive-internal/` (histórico de março e abril).

## Quando ler o quê

- **Ajuste editorial** (o que entra, o que sai, tom): `docs/EDITOR_NOTES.md` → `docs/EDITORIAL_IMPROVEMENT_PLAN.md` → `context/editorial.md` (o porquê) → o prompt em `prompts/` (a execução).
- **Fonte nova ou quebrada:** `sources_config.json` + `sources/`.
- **Edição não saiu ou saiu errada:** `README.md` (seção CI) + `.github/workflows/daily-scout.yml` + `debug/`.
- **Produto, público, posicionamento:** `context/produto.md`.
- **Marca, visual, persona:** `SYSTEM.md` no vault.

## Regras de produção

- Mudança em `prompts/` ou no pipeline só com dry run (`python scripts/manual_dry_run.py`) e `pytest tests/` passando.
- Uma mudança editorial por vez, medida no Content Report seguinte.
- Nunca exponha qual modelo de LLM a AYA usa em texto público (site, e-mail, social).
- O repo é público: nada de dados internos (IDs de planilha, métricas de assinantes, notas pessoais) em arquivos versionados.
- Push só quando a Isis pedir. Mudanças entram por PR, que ela aprova.

## Write-back

- Quando a Isis corrigir algo ou vocês tomarem uma decisão, atualize o arquivo certo e diga em 1 linha o que mudou:
  - correção de tom ou critério editorial → `docs/EDITOR_NOTES.md`
  - decisão com alternativas (stack, marca, posicionamento) → ADR no vault (`04-decisoes/`) + 1 linha em "Estado em 1 minuto" se mudar o estado
  - algo quebrou e foi resolvido → seção de troubleshooting do doc da área (`README.md` ou `scripts/README.md`)
  - mudou estado, modelo, fontes ou prioridade → "Estado em 1 minuto" acima
- Antes de adicionar uma regra, procure uma parecida: edite, não duplique. Regras novas entram com data: `- [2026-11-15] ...`.
- Write-back nunca altera `prompts/` ou o pipeline: isso é mudança de produção e segue as regras acima.

## Manutenção

- Este arquivo tem no máximo 150 linhas. Passou disso, consolide antes de escrever.
- Se `last-reviewed` passar de 30 dias, avise a Isis no início da sessão.
