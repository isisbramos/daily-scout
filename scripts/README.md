# Vault bridge — setup do Stage B (local)

Contexto completo da arquitetura: ver o artifact "Vault Bridge" gerado na
sessão que criou isso, ou o resumo abaixo.

O Stage A (geração da nota + commit em `vault-outbox/`) já roda sozinho no CI,
sem nada a fazer. Isso aqui é só o Stage B — a ponte final até o vault de
verdade, que só pode rodar na sua máquina porque é onde o vault (Obsidian
Sync/iCloud) está montado.

## Clone dedicado (obrigatório)

O job faz `git pull` todo dia antes de sincronizar. Rode-o num **clone só dele**, nunca no clone onde você desenvolve. Em 06/10/2026 o pull com `--autostash` no clone de desenvolvimento prendeu trabalho não commitado num conflito: o sync ficou parado 6 semanas e o trabalho só voltou no PR #46. Hoje o script usa `--ff-only` e falha de forma visível se o clone divergir, mas o clone dedicado é o que evita o problema.

Padrão usado: `~/code/aya-vault-sync`.

## Setup (uma vez)

1. Confirme o caminho absoluto da raiz do seu vault, ex:
   `/Users/<seu-usuario>/Library/Mobile Documents/iCloud~md~obsidian/Documents/<seu-vault>`
   (ou o path do Obsidian Sync, o que for).

2. Teste manual primeiro, antes de automatizar:
   ```bash
   cd ~/code/aya-vault-sync   # clone dedicado, não o de desenvolvimento
   git pull origin main
   export VAULT_PATH="/caminho/completo/do/seu/vault"
   python3 scripts/sync_to_vault.py
   ```
   Confira no Obsidian se a nota apareceu em `03-insights/`.

3. Automatize com launchd (equivalente ao cron, mas nativo do macOS e
   sobrevive a reboot):
   ```bash
   cp scripts/com.aya.vaultsync.plist.example ~/Library/LaunchAgents/com.aya.vaultsync.plist
   ```
   Edite o arquivo copiado e troque os 3 placeholders:
   - `/ABSOLUTE/PATH/TO/daily-scout` (2 ocorrências) → seu clone local
   - `/ABSOLUTE/PATH/TO/vault` → raiz do vault
   - `/usr/bin/python3` → rode `which python3` e confirme (importa se você usa
     pyenv/venv — o launchd não herda seu shell)

   Depois:
   ```bash
   launchctl load -w ~/Library/LaunchAgents/com.aya.vaultsync.plist
   ```

4. Validar que o job está agendado:
   ```bash
   launchctl list | grep aya.vaultsync
   ```

## Operação

- Roda 1x/dia, ~30min depois do cron da newsletter (dá tempo do CI commitar a
  nota no outbox antes do pull local). Ajuste o horário no plist se quiser.
- Log de cada run: `/tmp/aya-vaultsync.log`.
- Idempotente: nunca duplica nem sobrescreve nota que já existe no vault
  (se o destino já existe, pula e loga — nunca vai atropelar uma edição sua).
- Estado de "já sincronizado" fica em `.vault_sync_state.json` na raiz do repo
  local (git-ignored, não é compartilhado nem versionado).

## Desativar

```bash
launchctl unload ~/Library/LaunchAgents/com.aya.vaultsync.plist
```

## Rodar manualmente a qualquer momento

```bash
VAULT_PATH="/caminho/do/vault" python3 scripts/sync_to_vault.py
```

## Troubleshooting

- **"VAULT_PATH não existe ou não está montado"** → confira se o Obsidian
  Sync/iCloud já baixou a pasta localmente (às vezes fica só "on-demand" no
  Finder, não baixada de fato).
- **Nada aparece pra sincronizar** → confirme que o CI rodou hoje e que
  `vault-outbox/` tem arquivo novo no repo remoto (`git log --oneline -- vault-outbox/`).
- **launchd não disparou** → `launchctl list | grep aya.vaultsync` deve
  mostrar o job; se não aparecer, o `load` falhou — rode de novo e olhe o
  output do comando.

## Avaliar mudança de prompt (replay + lint)

Mudança em `prompts/` não se julga por uma edição de teste: ela mistura o efeito da mudança, a aleatoriedade do LLM e a entrada do dia. Use entradas fixas e várias execuções.

```bash
# 1. base, antes de mexer no prompt (chama o LLM; precisa de DEEPSEEK_API_KEY)
python scripts/prompt_replay.py --label base
# 2. muda o prompt
# 3. mesma entrada, comparando com a base
python scripts/prompt_replay.py --label novo --compare debug/replay/base.json
```

- Entradas: `tests/fixtures/replay/*_items.json` (títulos públicos de notícias). Para adicionar uma, copie o `debug/edition_N_items.json` de um dry run com `DEBUG_SAVE=true`.
- Sem memória editorial por padrão (`--with-memory` liga), para o resultado não depender das últimas edições. Não envia nada nem grava memória.
- `⚠` na comparação = métrica "mais alto é pior" (radar sem link, meta-linguagem vazada, ineditismo, número fora do input…) que subiu. Mudança que acende `⚠` precisa de explicação antes de entrar.
- As saídas completas ficam em `debug/replay/<label>/` para leitura humana: o lint conta violações de regras que o prompt já tem, mas não julga qualidade editorial.
- Lint avulso sobre um dry run: `python scripts/prompt_lint.py curation.json items.json`.

Limite conhecido: as 3 entradas atuais são do mesmo dia (17/11) e as mais antigas não carregam o `summary` de papers. Acrescente entradas de outros dias aos poucos.

## Lista de edições do site (`build_archive.py`)

- [2026-11-18] `scripts/build_archive.py` gera `archive/editions.json` a partir do arquivo público do Buttondown (sem API key, sem LLM). O site lê esse JSON: `archive/index.html` lista todas as edições com busca, e `index.html` mostra as 3 mais recentes.
- Roda sozinho pelo workflow `.github/workflows/site-archive.yml`: depois de cada execução do pipeline diário e às 15h BRT. Incremental (~3 s); `--full` reabre todas (~8 min).
- Edições que não estão no arquivo público do Buttondown (hoje #002 e #065) não aparecem na lista.
