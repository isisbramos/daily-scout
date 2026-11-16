#!/usr/bin/env python3
"""Guard de envio da AYA: decide se a edição de hoje ainda precisa ser enviada.

Roda como primeiro job do `daily-scout.yml`, só com a stdlib (sem pip install).
O envio passa a ter dois gatilhos: o disparo externo às 7h55 BRT (principal) e o
cron nativo do Actions (fallback, atrasa horas). Sem este guard os dois mandariam
a mesma edição. Contrato completo e runbook: `ops/disparo-externo.md`.

Regras:
  - Já existe a edição N em `memory/editions.jsonl` -> skip=true (não envia de novo).
  - Já saiu o "transmissão parcial" da edição N (`memory/fallbacks.jsonl`) -> skip=true:
    decisão de produto, o leitor não recebe um segundo e-mail com a edição completa.
  - DRY_RUN=true -> nunca pula: dry run tem que exercitar o pipeline inteiro.
  - FORCE=true -> nunca pula: reenvio deliberado (ex.: corrigir uma edição).
  - Qualquer erro ao ler o histórico -> skip=false + warning (fail-open: melhor um
    risco de duplicidade do que uma edição que não sai).

Também registra a pontualidade (início do run x alvo 7h55 BRT) no step summary.
É a métrica de entrega do projeto; ver `data/metricas.md`.

Saídas: `skip`, `edition` e `delay_min` em $GITHUB_OUTPUT; resumo em $GITHUB_STEP_SUMMARY.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EDITIONS_PATH = REPO_ROOT / "memory" / "editions.jsonl"
# Mesmo caminho de delivery.FALLBACKS_PATH (um teste trava a igualdade).
FALLBACKS_PATH = REPO_ROOT / "memory" / "fallbacks.jsonl"

# Edição #001 = 2026-03-23 (ver passo "Calculate edition number" do workflow).
EDITION_EPOCH = date(2026, 3, 22)

# Alvo de entrega: 7h55 BRT = 10h55 UTC. Mudou o horário no scheduler? Mude aqui também.
TARGET_UTC = time(10, 55)
LATE_WARNING_MIN = 30


def edition_number(today_utc: date) -> str:
    """Mesma conta do workflow: dias desde 2026-03-22 (UTC), com 3 dígitos."""
    return f"{(today_utc - EDITION_EPOCH).days:03d}"


def already_sent(edition: str, path: Path = EDITIONS_PATH) -> bool:
    """True se `edition` já está registrada na memória editorial.

    A memória só é escrita depois de um envio real bem-sucedido (pipeline.py,
    passo 6b), então presença = enviada. Linhas ilegíveis são ignoradas.
    """
    return _recorded(edition, path)


def fallback_sent(edition: str, path: Path = FALLBACKS_PATH) -> bool:
    """True se o e-mail "transmissão parcial" da `edition` já saiu (delivery.send_fallback)."""
    return _recorded(edition, path)


def _recorded(edition: str, path: Path) -> bool:
    if not path.exists():
        return False
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict) and str(record.get("edition")) == edition:
                return True
    return False


def delay_minutes(now_utc: datetime) -> float:
    """Minutos entre o alvo de hoje (7h55 BRT) e `now_utc`. Negativo = adiantado."""
    target = datetime.combine(now_utc.date(), TARGET_UTC, tzinfo=timezone.utc)
    return round((now_utc - target) / timedelta(minutes=1), 1)


def _flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() == "true"


def decide(
    edition: str,
    *,
    dry_run: bool,
    force: bool,
    path: Path = EDITIONS_PATH,
    fallbacks_path: Path = FALLBACKS_PATH,
) -> tuple[bool, str]:
    """Retorna (skip, motivo)."""
    if dry_run:
        return False, "dry run: guard desligado"
    if force:
        return False, "force=true: reenvio deliberado"
    try:
        sent = already_sent(edition, path)
        partial = fallback_sent(edition, fallbacks_path)
    except Exception as exc:  # fail-open
        print(f"::warning::Guard não conseguiu ler o histórico ({exc}); seguindo sem checagem.")
        return False, f"erro ao ler histórico ({type(exc).__name__}): seguindo"
    if sent:
        return True, f"edição {edition} já registrada: nada a enviar"
    if partial:
        return True, f"'transmissão parcial' da edição {edition} já enviada: sem segundo e-mail"
    return False, f"edição {edition} ainda não registrada: enviar"


def _append(env_var: str, text: str) -> None:
    target = os.environ.get(env_var)
    if target:
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(text)


def main(now_utc: datetime | None = None) -> int:
    now = now_utc or datetime.now(timezone.utc)
    edition = os.environ.get("EDITION_NUMBER", "").strip() or edition_number(now.date())
    trigger = os.environ.get("TRIGGER", "").strip() or os.environ.get("EVENT_NAME", "").strip() or "desconhecido"
    delay = delay_minutes(now)

    skip, reason = decide(edition, dry_run=_flag("DRY_RUN"), force=_flag("FORCE"))

    if delay > LATE_WARNING_MIN and not skip:
        print(f"::warning::Envio atrasado: início {delay:.0f} min depois do alvo (7h55 BRT). trigger={trigger}")

    _append("GITHUB_OUTPUT", f"skip={'true' if skip else 'false'}\nedition={edition}\ndelay_min={delay}\n")
    _append(
        "GITHUB_STEP_SUMMARY",
        "### Guard de envio\n"
        f"- Edição: **#{edition}**\n"
        f"- Decisão: **{'PULAR' if skip else 'ENVIAR'}** ({reason})\n"
        f"- Gatilho: `{trigger}`\n"
        f"- Início do run: {now:%H:%M:%S}Z · alvo 10:55Z (7h55 BRT) · "
        f"**{'+' if delay >= 0 else ''}{delay} min**\n",
    )
    print(f"guard: edition={edition} skip={skip} trigger={trigger} delay_min={delay} ({reason})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
