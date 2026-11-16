"""
Testes do guard de envio (scripts/edition_guard.py) e do contrato com o workflow.

O guard existe porque o envio tem dois gatilhos (disparo externo + cron nativo de
fallback). Os testes travam as três coisas que, se quebrarem, mandam a edição em
duplicidade ou fazem ela não sair:
  1. a conta do número da edição bate com a do workflow;
  2. a decisão pular/enviar (incluindo dry run, force e fail-open);
  3. a fiação do workflow (needs, concurrency, default do edition_number).
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
import yaml

from scripts import edition_guard as guard

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "daily-scout.yml"


def _write_editions(path: Path, editions: list[str], *, junk: bool = False) -> Path:
    lines = [json.dumps({"edition": e, "date": "2026-01-01"}) for e in editions]
    if junk:
        lines = ["", "{linha quebrada", *lines, "   "]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ── 1. Número da edição ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "day, expected",
    [
        (date(2026, 3, 23), "001"),
        (date(2026, 6, 23), "093"),  # confere com memory/editions.jsonl
        (date(2026, 11, 15), "238"),
        (date(2026, 11, 16), "239"),
    ],
)
def test_edition_number_known_dates(day, expected):
    assert guard.edition_number(day) == expected


@pytest.mark.skipif(
    platform.system() != "Linux" or not shutil.which("date"),
    reason="o workflow usa `date -d` (GNU); só dá pra cruzar no Linux",
)
def test_edition_number_matches_workflow_shell_formula():
    """Mesma conta do passo 'Calculate edition number' do workflow (GNU date, UTC)."""
    for day in (date(2026, 3, 23), date(2026, 9, 1), date(2026, 11, 16), date(2027, 1, 1)):
        shell = subprocess.run(
            ["bash", "-c", f'echo $(( ($(date -u -d {day} +%s) - $(date -u -d 2026-03-22 +%s)) / 86400 ))'],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        assert guard.edition_number(day) == f"{int(shell):03d}"


# ── 2. already_sent / decide ─────────────────────────────────────────────────


def test_already_sent_true_when_recorded(tmp_path):
    path = _write_editions(tmp_path / "e.jsonl", ["237", "238"])
    assert guard.already_sent("238", path) is True


def test_already_sent_false_when_not_recorded(tmp_path):
    path = _write_editions(tmp_path / "e.jsonl", ["237", "238"])
    assert guard.already_sent("239", path) is False


def test_already_sent_false_when_file_missing(tmp_path):
    assert guard.already_sent("239", tmp_path / "nao-existe.jsonl") is False


def test_already_sent_ignores_blank_and_corrupt_lines(tmp_path):
    path = _write_editions(tmp_path / "e.jsonl", ["239"], junk=True)
    assert guard.already_sent("239", path) is True
    assert guard.already_sent("240", path) is False


def test_already_sent_matches_edition_as_string(tmp_path):
    # A memória guarda "093" como string; um int sem zero à esquerda NÃO pode casar por engano.
    path = tmp_path / "e.jsonl"
    path.write_text(json.dumps({"edition": 93}) + "\n", encoding="utf-8")
    assert guard.already_sent("093", path) is False


def test_decide_skips_when_already_sent(tmp_path):
    path = _write_editions(tmp_path / "e.jsonl", ["239"])
    skip, reason = guard.decide("239", dry_run=False, force=False, path=path)
    assert skip is True
    assert "239" in reason


def test_decide_sends_when_not_sent(tmp_path):
    path = _write_editions(tmp_path / "e.jsonl", ["238"])
    skip, _ = guard.decide("239", dry_run=False, force=False, path=path)
    assert skip is False


def test_decide_dry_run_never_skips(tmp_path):
    path = _write_editions(tmp_path / "e.jsonl", ["239"])
    skip, _ = guard.decide("239", dry_run=True, force=False, path=path)
    assert skip is False


def test_decide_force_never_skips(tmp_path):
    path = _write_editions(tmp_path / "e.jsonl", ["239"])
    skip, _ = guard.decide("239", dry_run=False, force=True, path=path)
    assert skip is False


def test_decide_fails_open_on_read_error(tmp_path, monkeypatch, capsys):
    def boom(*_a, **_k):
        raise OSError("disco quebrou")

    monkeypatch.setattr(guard, "already_sent", boom)
    skip, reason = guard.decide("239", dry_run=False, force=False, path=tmp_path / "x")
    assert skip is False
    assert "OSError" in reason
    assert "::warning::" in capsys.readouterr().out


# ── 3. Pontualidade ──────────────────────────────────────────────────────────


def test_delay_minutes_on_target_is_zero():
    assert guard.delay_minutes(datetime(2026, 11, 16, 10, 55, tzinfo=timezone.utc)) == 0


def test_delay_minutes_late_and_early():
    assert guard.delay_minutes(datetime(2026, 11, 16, 11, 25, tzinfo=timezone.utc)) == 30
    # Cron nativo típico de hoje (13:43Z): ~2h48 depois do alvo.
    assert guard.delay_minutes(datetime(2026, 11, 16, 13, 43, tzinfo=timezone.utc)) == 168
    assert guard.delay_minutes(datetime(2026, 11, 16, 6, 37, tzinfo=timezone.utc)) < 0


# ── 4. main(): saídas para o GitHub Actions ──────────────────────────────────


def _run_main(monkeypatch, tmp_path, *, env: dict[str, str], editions: list[str], now: datetime):
    out, summary = tmp_path / "out", tmp_path / "summary"
    monkeypatch.setattr(guard, "EDITIONS_PATH", _write_editions(tmp_path / "e.jsonl", editions))
    # decide() usa o default de path definido na assinatura; reaponta o default via wrapper.
    original = guard.decide
    monkeypatch.setattr(guard, "decide", lambda ed, **kw: original(ed, path=guard.EDITIONS_PATH, **kw))
    for key in ("EDITION_NUMBER", "DRY_RUN", "FORCE", "TRIGGER", "EVENT_NAME"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    assert guard.main(now) == 0
    outputs = dict(line.split("=", 1) for line in out.read_text().splitlines())
    return outputs, summary.read_text()


def test_main_external_trigger_on_time_sends(monkeypatch, tmp_path):
    now = datetime(2026, 11, 16, 10, 55, 4, tzinfo=timezone.utc)
    outputs, summary = _run_main(
        monkeypatch, tmp_path, env={"TRIGGER": "external", "EVENT_NAME": "workflow_dispatch"},
        editions=["238"], now=now,
    )
    assert outputs["skip"] == "false"
    assert outputs["edition"] == "239"
    assert "ENVIAR" in summary and "`external`" in summary


def test_main_late_native_cron_skips_when_external_already_sent(monkeypatch, tmp_path):
    now = datetime(2026, 11, 16, 13, 43, tzinfo=timezone.utc)
    outputs, summary = _run_main(
        monkeypatch, tmp_path, env={"EVENT_NAME": "schedule"}, editions=["238", "239"], now=now,
    )
    assert outputs["skip"] == "true"
    assert outputs["edition"] == "239"
    assert "PULAR" in summary and "`schedule`" in summary


def test_main_trigger_falls_back_to_event_name(monkeypatch, tmp_path):
    now = datetime(2026, 11, 16, 13, 43, tzinfo=timezone.utc)
    _, summary = _run_main(monkeypatch, tmp_path, env={"TRIGGER": "", "EVENT_NAME": "schedule"}, editions=[], now=now)
    assert "`schedule`" in summary


def test_main_explicit_edition_number_wins(monkeypatch, tmp_path):
    now = datetime(2026, 11, 16, 10, 55, tzinfo=timezone.utc)
    outputs, _ = _run_main(
        monkeypatch, tmp_path, env={"EDITION_NUMBER": "200", "EVENT_NAME": "workflow_dispatch"},
        editions=["239"], now=now,
    )
    assert outputs["edition"] == "200"
    assert outputs["skip"] == "false"


def test_main_late_start_emits_warning(monkeypatch, tmp_path, capsys):
    now = datetime(2026, 11, 16, 13, 43, tzinfo=timezone.utc)
    _run_main(monkeypatch, tmp_path, env={"EVENT_NAME": "schedule"}, editions=["238"], now=now)
    assert "::warning::Envio atrasado" in capsys.readouterr().out


# ── 5. Contrato com o workflow ───────────────────────────────────────────────


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _triggers(wf: dict) -> dict:
    # PyYAML (YAML 1.1) lê a chave `on` como o booleano True.
    return wf.get("on", wf.get(True))


def test_workflow_edition_number_input_defaults_to_empty(workflow):
    """Default '001' fazia o disparo externo (sem inputs) mandar a edição #001."""
    inputs = _triggers(workflow)["workflow_dispatch"]["inputs"]
    assert inputs["edition_number"]["default"] == ""


def test_workflow_has_force_and_trigger_inputs(workflow):
    inputs = _triggers(workflow)["workflow_dispatch"]["inputs"]
    assert inputs["force"]["default"] is False
    assert inputs["trigger"]["default"] == "manual"


def test_workflow_serializes_runs_without_cancelling_the_running_one(workflow):
    assert workflow["concurrency"]["group"] == "aya-daily-send"
    assert workflow["concurrency"]["cancel-in-progress"] is False


def test_workflow_pipeline_waits_on_guard_and_fails_open(workflow):
    job = workflow["jobs"]["run-pipeline"]
    assert job["needs"] == "guard"
    condition = job["if"]
    assert "needs.guard.outputs.skip != 'true'" in condition
    assert "!cancelled()" in condition  # guard quebrado não pode impedir o envio


def test_workflow_guard_checks_out_branch_tip(workflow):
    steps = workflow["jobs"]["guard"]["steps"]
    checkout = next(s for s in steps if str(s.get("uses", "")).startswith("actions/checkout"))
    assert checkout["with"]["ref"] == "${{ github.ref_name }}"


def test_workflow_native_cron_is_still_there_as_fallback(workflow):
    assert _triggers(workflow)["schedule"] == [{"cron": "37 6 * * *"}]
