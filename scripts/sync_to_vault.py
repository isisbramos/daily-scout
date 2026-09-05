#!/usr/bin/env python3
"""
Daily Scout — Vault Bridge (Stage B)

Roda LOCALMENTE (no seu Mac, nunca no GitHub Actions): puxa o repo, pega as
notas novas que o CI deixou em vault-outbox/ (ver vault_bridge.py) e copia
cada uma pro caminho correspondente dentro do vault isis-brain de verdade.

Por que isso não roda no CI: o vault sincroniza via Obsidian Sync/iCloud —
o runner do GitHub Actions não tem acesso a esse filesystem. Esse script é a
metade da ponte que só faz sentido rodando onde o vault está montado.

Uso:
    export VAULT_PATH="/Users/<seu-usuario>/Documents/isis-brain"   # raiz do vault
    python3 scripts/sync_to_vault.py

Idempotente: mantém um estado local (.vault_sync_state.json, git-ignored) com
os arquivos já copiados, então rodar de novo não duplica nem sobrescreve nada.
Se o destino já existir no vault (ex: você editou a nota manualmente), o
arquivo é PULADO — nunca sobrescreve conteúdo seu.

Pensado pra rodar sozinho via cron/launchd (ver scripts/README.md) — não
depende de LLM, é cópia de arquivo determinística.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTBOX_DIR = os.path.join(REPO_ROOT, "vault-outbox")
STATE_PATH = os.path.join(REPO_ROOT, ".vault_sync_state.json")


def _log(msg: str) -> None:
    print(f"[sync_to_vault] {msg}", flush=True)


def _git_pull() -> bool:
    """Atualiza o clone local antes de sincronizar. Não é fatal se falhar
    (ex: sem internet) — só significa que não há nada novo pra pegar agora."""
    try:
        subprocess.run(
            ["git", "pull", "--rebase", "--autostash", "origin", "main"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        _log(f"git pull falhou (seguindo com o que já está local): {e.stderr.strip()}")
        return False


def _load_state() -> set[str]:
    if not os.path.exists(STATE_PATH):
        return set()
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return set(json.load(f))
    except (json.JSONDecodeError, OSError):
        return set()


def _save_state(synced: set[str]) -> None:
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(synced), f, ensure_ascii=False, indent=2)


def _iter_outbox_files() -> list[str]:
    """Paths relativos (a partir de vault-outbox/) de todas as notas .md."""
    if not os.path.isdir(OUTBOX_DIR):
        return []
    found = []
    for dirpath, _dirnames, filenames in os.walk(OUTBOX_DIR):
        for name in filenames:
            if name.endswith(".md"):
                abs_path = os.path.join(dirpath, name)
                found.append(os.path.relpath(abs_path, OUTBOX_DIR))
    return sorted(found)


def sync(vault_path: str) -> int:
    """Copia notas novas do outbox pro vault. Retorna o nº de notas copiadas."""
    if not os.path.isdir(vault_path):
        _log(f"ERRO: VAULT_PATH não existe ou não está montado: {vault_path}")
        _log("Se o vault sincroniza via iCloud/Obsidian Sync, confirme que a pasta "
             "já baixou localmente antes de rodar este script.")
        return 0

    _git_pull()

    synced = _load_state()
    copied = 0
    for rel_path in _iter_outbox_files():
        if rel_path in synced:
            continue

        src = os.path.join(OUTBOX_DIR, rel_path)
        dest = os.path.join(vault_path, rel_path)

        if os.path.exists(dest):
            _log(f"PULADO (já existe no vault, não sobrescrevo): {rel_path}")
            synced.add(rel_path)  # não tenta de novo a cada run
            continue

        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
        synced.add(rel_path)
        copied += 1
        _log(f"copiado -> {dest}")

    _save_state(synced)
    _log(f"concluído: {copied} nota(s) nova(s) sincronizada(s) com o vault.")
    return copied


def main() -> None:
    vault_path = os.environ.get("VAULT_PATH")
    if not vault_path:
        _log("ERRO: defina VAULT_PATH com o caminho absoluto da raiz do isis-brain.")
        sys.exit(1)
    sync(os.path.expanduser(vault_path))


if __name__ == "__main__":
    main()
