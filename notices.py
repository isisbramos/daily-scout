"""
Daily Scout — Avisos ao leitor (one-shot, auto-limpante)

Sistema pra anunciar mudanças no email (ex: "ajustamos a curadoria") sem
precisar lembrar de desligar depois. Fluxo:

  1. Isis pede um aviso no chat, a gente combina o texto.
  2. Claude escreve notices/pending.json e commita.
  3. Na próxima edição REAL enviada (não dry run), pipeline.py lê o pending,
     usa o texto no email, registra em notices/sent_log.jsonl (histórico
     append-only, igual memory/editions.jsonl) e apaga o pending.
  4. O workflow persiste isso de volta pro repo (mesmo padrão de
     scripts/persist_to_git.sh usado pra memória editorial).

Resultado: nunca aparece duas vezes, nunca precisa lembrar de tirar nada,
e fica um log de todo aviso que já foi ao ar.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("daily-scout")

ROOT = os.path.dirname(os.path.abspath(__file__))
NOTICES_DIR = os.path.join(ROOT, "notices")
PENDING_PATH = os.path.join(NOTICES_DIR, "pending.json")
SENT_LOG_PATH = os.path.join(NOTICES_DIR, "sent_log.jsonl")

_BRT = timezone(timedelta(hours=-3))


def load_pending_notice() -> str:
    """Texto do aviso pendente, ou "" se não houver nenhum. Nunca levanta —
    um pending.json corrompido não pode derrubar o envio da newsletter."""
    if not os.path.exists(PENDING_PATH):
        return ""
    try:
        with open(PENDING_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return (data.get("text") or "").strip()
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"notices: pending.json inválido, ignorando ({e})")
        return ""


def mark_notice_sent(edition: str) -> None:
    """Chamar só depois de um envio real bem-sucedido. Move o pending pro
    log append-only e apaga o pending — próxima edição já sai limpa.
    Não-bloqueante: falha aqui nunca derruba o pipeline (newsletter já saiu)."""
    if not os.path.exists(PENDING_PATH):
        return
    try:
        with open(PENDING_PATH, encoding="utf-8") as f:
            data = json.load(f)
        record = {
            "text": data.get("text", ""),
            "edition": edition,
            "sent_at": datetime.now(_BRT).isoformat(),
        }
        os.makedirs(NOTICES_DIR, exist_ok=True)
        with open(SENT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        os.remove(PENDING_PATH)
        logger.info(f"notices: aviso da edição #{edition} registrado e pending limpo")
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"notices: falha ao registrar/limpar aviso (não-bloqueante): {e}")
