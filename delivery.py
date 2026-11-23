"""
Daily Scout — Delivery layer: Buttondown API + fallback email.
Isolado do pipeline principal para que falhas de entrega sejam tratadas
separadamente das falhas de curadoria.
"""

import html as html_lib
import json
import logging
import os
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger("daily-scout")

BUTTONDOWN_API_KEY = os.environ.get("BUTTONDOWN_API_KEY")
BUTTONDOWN_API_URL = "https://api.buttondown.com/v1/emails"
EDITION_NUMBER = os.environ.get("EDITION_NUMBER", "001")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

# Dias em que saiu o e-mail "transmissão parcial". O guard do envio (scripts/edition_guard.py)
# lê este arquivo para NÃO reenviar a edição completa depois: o leitor não recebe dois e-mails.
# Guarda só edição e data, nunca o motivo do erro (o repo é público).
FALLBACKS_PATH = Path(__file__).resolve().parent / "memory" / "fallbacks.jsonl"


def record_fallback(edition: str, path: Path = FALLBACKS_PATH) -> None:
    """Registra que o fallback desta edição foi enviado. Nunca levanta: é só um marcador."""
    try:
        brt = timezone(timedelta(hours=-3))
        record = {"edition": str(edition), "date": datetime.now(brt).strftime("%Y-%m-%d")}
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:
        logger.warning(f"Fallback enviado, mas não consegui registrar o marcador (não-bloqueante): {exc}")


def send_via_buttondown(subject: str, html_content: str) -> bool:
    """Envia newsletter via Buttondown API."""
    logger.info("=" * 50)
    logger.info("PHASE 5: SEND — delivering via Buttondown")
    logger.info("=" * 50)

    if not BUTTONDOWN_API_KEY:
        logger.error("BUTTONDOWN_API_KEY não configurada")
        return False

    html_body = "<!-- buttondown-editor-mode: raw -->\n" + html_content

    payload = {
        "subject": subject,
        "body": html_body,
        "status": "about_to_send",
    }

    headers = {
        "Authorization": f"Token {BUTTONDOWN_API_KEY}",
        "Content-Type": "application/json",
        "X-Buttondown-Live-Dangerously": "true",
    }

    try:
        resp = requests.post(
            BUTTONDOWN_API_URL, json=payload, headers=headers, timeout=30
        )

        if resp.status_code in (200, 201):
            data = resp.json()
            logger.info(f"Buttondown: sent! ID={data.get('id', 'unknown')}")
            return True
        elif resp.status_code == 400:
            error_data = resp.json() if resp.text else {}
            if "sending_requires_confirmation" in str(error_data):
                logger.error(
                    "Buttondown: first API send needs manual confirmation in dashboard."
                )
            else:
                logger.error(f"Buttondown: HTTP 400 — {resp.text}")
            return False
        else:
            logger.error(f"Buttondown: HTTP {resp.status_code} — {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Buttondown: connection error — {e}")
        return False


def send_fallback(reason: str) -> bool:
    """Envia versão simplificada caso o pipeline falhe parcialmente."""
    if DRY_RUN:
        logger.info(f"DRY_RUN=true — skipping fallback send (reason: {reason})")
        return True
    logger.info(f"Sending fallback: {reason}")

    brt = timezone(timedelta(hours=-3))
    now_brt = datetime.now(brt)
    date_str = now_brt.strftime("%d/%m/%Y")
    safe_reason = html_lib.escape(reason)

    fallback_html = f"""
    <div style="font-family: 'Courier New', monospace; background: #0F172A; color: #CBD5E1; padding: 32px; max-width: 600px; margin: 0 auto;">
        <div style="color: #22C55E; font-size: 18px; font-weight: bold;">AYA</div>
        <div style="color: #94A3B8; font-size: 12px; margin-top: 4px;">curadoria diária sobre inteligência artificial — #{EDITION_NUMBER} — {date_str}</div>
        <hr style="border-color: #334155; margin: 16px 0;">
        <div style="color: #F59E0B; font-size: 14px; margin-bottom: 12px;">[TRANSMISSÃO PARCIAL]</div>
        <div style="color: #CBD5E1; font-size: 13px; line-height: 1.7;">
            A correspondente encontrou instabilidade no campo hoje. A edição completa não pôde ser montada.<br><br>
            <strong style="color: #F1F5F9;">Motivo:</strong> {safe_reason}<br><br>
            Amanhã voltamos com cobertura completa.
        </div>
        <hr style="border-color: #334155; margin: 16px 0;">
        <div style="color: #94A3B8; font-size: 10px;">made_by: aya v3.0 | status: fallback</div>
    </div>
    """

    subject = f"AYA #{EDITION_NUMBER} — [transmissão parcial]"
    sent = send_via_buttondown(subject, fallback_html)
    if sent:
        record_fallback(EDITION_NUMBER)
    return sent
