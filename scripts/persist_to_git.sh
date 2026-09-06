#!/usr/bin/env bash
# Commita e envia um caminho para origin/main, com retry em caso de push
# concorrente e um aviso visível se todas as tentativas falharem.
#
# Usado pelos passos "Persist editorial memory" e "Persist vault note" do
# workflow .github/workflows/daily-scout.yml. Os dois rodam com
# continue-on-error: true de propósito — a newsletter já foi enviada nesse
# ponto do job, então uma falha de git (branch protection, conflito, etc.)
# nunca pode derrubar o job. Mas o script antigo engolia a falha com um
# `|| echo` que só aparecia se alguém fosse ler o log manualmente — perda de
# dado 100% silenciosa. Este script tenta de novo antes de desistir e, se
# mesmo assim falhar, escreve no GITHUB_STEP_SUMMARY (aparece na tela do run
# no GitHub, sem precisar abrir o log) e sai com código != 0, o que marca o
# step com aviso na UI mesmo com o job continuando verde.
#
# Uso: scripts/persist_to_git.sh <caminho-a-commitar> <mensagem-de-commit>
set -euo pipefail

PATH_TO_COMMIT="${1:?uso: persist_to_git.sh <caminho> <mensagem>}"
COMMIT_MSG="${2:?uso: persist_to_git.sh <caminho> <mensagem>}"
MAX_ATTEMPTS=3

if [ -z "$(git status --porcelain -- "$PATH_TO_COMMIT")" ]; then
  echo "Sem mudanças em $PATH_TO_COMMIT — nada a commitar."
  exit 0
fi

git config user.name "aya-bot"
git config user.email "actions@users.noreply.github.com"
git add "$PATH_TO_COMMIT"
git commit -m "$COMMIT_MSG" || { echo "nada a commitar"; exit 0; }

attempt=1
while [ "$attempt" -le "$MAX_ATTEMPTS" ]; do
  if git pull --rebase --autostash origin main && git push origin HEAD:main; then
    echo "Push OK (tentativa $attempt/$MAX_ATTEMPTS)."
    exit 0
  fi
  echo "Push falhou (tentativa $attempt/$MAX_ATTEMPTS)."
  sleep $((attempt * 5))
  attempt=$((attempt + 1))
done

WARNING="⚠️ **Falha ao persistir \`$PATH_TO_COMMIT\`** após $MAX_ATTEMPTS tentativas de push — a mudança ficou commitada só localmente no runner e será perdida quando ele for descartado (a newsletter já foi enviada, sem impacto no envio). Investigar branch protection ou conflito em \`main\` antes da próxima edição."
echo "$WARNING" >&2
if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  echo "$WARNING" >> "$GITHUB_STEP_SUMMARY"
fi
exit 1
