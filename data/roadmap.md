# Roadmap

> last-reviewed: 2026-11-15 · Junta `docs/ROADMAP.md` e `docs/EDITORIAL_IMPROVEMENT_PLAN.md` no que ainda vale; os originais foram para `docs/historico/` como registro. Para o histórico completo de como cada coisa foi construída → `docs/historico/ROADMAP.md`, `docs/historico/EDITORIAL_IMPROVEMENT_PLAN.md`, `docs/EDITORIAL_RETROSPECTIVE.md`, `docs/DOC_PROCESSO_DAILY_SCOUT.md`.

## Shipped — o que já está rodando

- **Pipeline v5.4** em produção (AI Gate + anti-hype + anti-opinion + revisor final em shadow) — detalhe completo em `data/estado-atual.md`.
- **23 fontes ativas**, em 3 ondas de expansão + ajustes pontuais (Apple ML Research e GitHub Blog entraram, Qwen Blog saiu — ver abaixo).
- **Migração DeepSeek** (de Gemini, abr/2026) — concluída, sem plano de reavaliar sem degradação documentada.
- **Memória editorial** (`memory_store.py`, jun/2026) — pipeline deixou de ser stateless; evita repetição de quick_finds e temas saturados.
- **Plano de melhoria editorial de out/2026** — as 6 recomendações (fonte por item, barra do main_find, funding penalty, revisor final em shadow, coerência na troca de destaque, investigação de fontes ociosas) estão **todas implementadas**. Detalhe de cada uma, incluindo o que ficou pendente de decisão, em `docs/historico/EDITORIAL_IMPROVEMENT_PLAN.md`.
- **Rebrand AYA como entidade autônoma** (decidido 20/05) — concluído: avatar e paleta (verde neon `#22C55E` + charcoal `#0F172A`) estão em `templates/email.html`; naming consolidado em "AYA" só.
- **Nunca expor o modelo de LLM em comunicação pública** — regra aplicada em todo o texto voltado ao leitor.
- **Vault sync para `07-sinais/`** (PR #46) — notícias da edição passam a seguir a taxonomia do vault.

### Correção: Qwen Blog não é mais "fonte que nunca entra"

O `docs/historico/EDITORIAL_IMPROVEMENT_PLAN.md` (Rec. 5) lista `qwen_blog` como fonte que raramente entra por causa da janela de ranking de 24h, com `recency_hours: 72` como ajuste. Isso ficou obsoleto: desde o PR #46, `qwen_blog` está **desabilitado** em `sources_config.json` — o feed parou de existir (o blog migrou para um site sem RSS em set/2025). Não é mais uma questão de critério, é fonte morta.

## Now — frente editorial PM (recorte decidido em 15/11)

Uma mudança por vez, medida no Content Report seguinte (regra de produção em `CLAUDE.md`). Detalhe da decisão, critério e tensão do pilar 5 em `context/produto.md`.

| Data | Passo | Status |
| --- | --- | --- |
| 15/11/2026 | **Passo 1** — linha "→ No seu produto:" em cada achado (PR #51) | ✅ Em produção, em medição |
| 17/11/2026 | **Passo 1.1** — linha "→ No seu produto:" vira "→ No seu trabalho:" + proibição de inventar contexto (ver `context/produto.md`). **Reinicia a medição do passo 1** | ✅ Em produção (PR #63), em medição desde 18/11 |
| ~13/12/2026 | Fim da medição dos passos 1.1 + 2 + 2.1 + 2.2 (contada da 1ª edição com a v5.5.3, 18/11) | 🔜 Agendado |
| 17/11/2026 | **Passo 2** — TESTE DE DECISÃO no STEP 2 + calibração v5.5 do prompt (ver `context/editorial.md`) | ✅ Em produção (PR #66; ajuste do RADAR v5.5.1 no PR #67), em medição desde 18/11 |
| 17/11/2026 | **Passo 2.1 (v5.5.2)** — papers com resumo no input e regra por capacidade concreta (ver `context/editorial.md`) | ✅ Em produção (PR #68), em medição desde 18/11 |
| 17/11/2026 | **Passo 2.2 (v5.5.3)** — follow-up controlado no guard de repetição (ver `context/editorial.md`) | ✅ Em produção (PR #69), em medição desde 18/11 |
| 17/11/2026 | **Passo 2.3** — replay e lint de prompt (`scripts/prompt_replay.py`, `scripts/prompt_lint.py`), guard do radar sem link e resumo de ~650 caracteres. Sem texto de prompt alterado | ✅ Em produção (PR #71), desde 19/11 (ed. 242); a ed. 241 saiu com resumo de 320 caracteres e sem o guard do radar |
| após 5 edições reais | **Passo 2.4** — limpeza do prompt (voltar ao tamanho de antes de 17/11, 4,5 mil palavras no `curation_template`), validada no replay contra a base. **Editorial congelado até lá** | ⏸ Planejado |
| jan/2027 | **Passo 3** — pilar 5 (IA, consciência e cultura), com exceção de evento âncora e máximo 1 item por edição | ⏸ Planejado |

### Diagnóstico de concentração por fonte

**23/11/2026** — diagnóstico agendado sobre concentração de itens por fonte (segue a Rec. 4 do plano de melhoria editorial: `memory_store.py` já grava a fonte de cada item publicado desde a ed.197; falta a leitura dedicada desse dado).

## Next — backlog não verificável só pelo código

Estes itens vêm do `docs/historico/ROADMAP.md` (maio/2026) e dependem de configuração fora do repo (Buttondown, secrets do GitHub) — o código não confirma se já foram feitos. Confirmar com a Isis antes de assumir o status:

- Sequência de welcome email no Buttondown (copy já escrito, segundo o roadmap antigo).
- Ativar analytics do Buttondown (open rate / CTR) — pré-requisito para medir as métricas em `data/metricas.md`.
- Reativar social posting: verificar secrets `LINKEDIN_ACCESS_TOKEN`/`LINKEDIN_PERSON_URN` e trocar `SOCIAL_ENABLED` para `true` em `daily-scout.yml` (hoje é `false` — confirmado no código).

### Achado da revisão dos PRs #17/#18 (Dependabot)

`social-post.yml` usa `actions/download-artifact` sem `run-id`, então só procura artifacts do próprio run — nunca vai encontrar o artifact `edition-N` que o `daily-scout.yml` subiu num run diferente. Isso já falha hoje (confirmado no log do run de 14/11: "Artifact not found for name: edition-237") e é independente da versão da action — não é um risco introduzido pelo bump, mas o motivo real de o social posting nunca ter saído do papel mesmo com `SOCIAL_ENABLED=true` em algum teste futuro. Precisa de `run-id` + `github-token` (ou outra estratégia) para funcionar entre workflows.

## Later — apostas de médio/longo prazo

Sem mudança desde o `docs/historico/ROADMAP.md`: monetização (500+ subs ativos, open rate > 40%), weekly digest para leitores inativos, personalização por persona (dev vs. PM — parcialmente endereçada pelo recorte de 15/11), API/dados abertos, edição multi-idioma. Nenhuma tem trabalho iniciado.

## O que não está no roadmap (e por quê)

| Item | Decisão |
| --- | --- |
| App mobile | Distribuição via email é suficiente na fase atual. |
| Curadoria humana em cima da AYA | Negaria o pressuposto do produto. |
| Mudar de DeepSeek agora | Stack atual funciona; reavaliar só com degradação documentada. |
| Aumentar frequência (> 1x/dia) | Mais frequência sem mais subscribers = mais custo sem mais impacto. |
| Substack/social como canal primário | AYA tem domínio próprio; canais externos são distribuição, não sede. |
