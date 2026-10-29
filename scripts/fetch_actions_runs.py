"""Grava um snapshot do histórico do GitHub Actions em ci/actions_runs.json.

O dashboard roda offline e não chama a API — ele lê este snapshot. Separar as
duas coisas é de propósito: gerar o painel não deve depender de rede nem de
token, e o histórico de runs muda devagar o bastante pra um snapshot servir.

Precisa do `gh` autenticado (`gh auth login`), ou de GITHUB_TOKEN no ambiente.

Uso:
  python scripts/fetch_actions_runs.py
  python scripts/fetch_actions_runs.py --repo owner/repo --pages 12
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "ci", "actions_runs.json")
DEFAULT_REPO = "isisbramos/daily-scout"

# Só o que o painel usa. O payload cru da API tem ~100 campos por run e passaria
# de 3 MB — guardar isso no git pra ler 8 campos não se paga.
KEEP = ("id", "name", "path", "conclusion", "status", "event", "created_at",
        "updated_at", "run_started_at", "run_attempt", "head_branch",
        "display_title", "head_sha")


def _duration_s(run: dict) -> float | None:
    start, end = run.get("run_started_at"), run.get("updated_at")
    if not (start and end):
        return None
    try:
        a = datetime.fromisoformat(start.replace("Z", "+00:00"))
        b = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except ValueError:
        return None
    return round((b - a).total_seconds(), 1)


def fetch_page(repo: str, page: int) -> list[dict]:
    """Uma página de 100 runs. Usa caminho repos/{owner}/{repo} explícito —
    `gh run list` pagina por repositories/{id}, que alguns proxies recusam."""
    cmd = ["gh", "api", f"repos/{repo}/actions/runs?per_page=100&page={page}"]
    try:
        raw = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
    except FileNotFoundError:
        print("gh não encontrado — instale o GitHub CLI ou exporte GITHUB_TOKEN.",
              file=sys.stderr)
        raise SystemExit(1)
    except subprocess.CalledProcessError as exc:
        print(f"gh api falhou na página {page}: {(exc.stderr or '').strip()[:300]}",
              file=sys.stderr)
        return []
    except subprocess.TimeoutExpired:
        print(f"gh api expirou na página {page}.", file=sys.stderr)
        return []
    try:
        return json.loads(raw.stdout).get("workflow_runs") or []
    except json.JSONDecodeError:
        return []


def main() -> None:
    p = argparse.ArgumentParser(description="Snapshot dos runs do GitHub Actions.")
    p.add_argument("--repo", default=DEFAULT_REPO, help=f"owner/repo (default: {DEFAULT_REPO})")
    p.add_argument("--pages", type=int, default=12, help="Máximo de páginas de 100 (default: 12)")
    p.add_argument("--out", default=OUT_PATH, help="Caminho de saída")
    args = p.parse_args()

    seen: dict[int, dict] = {}
    for page in range(1, args.pages + 1):
        batch = fetch_page(args.repo, page)
        if not batch:
            break
        for run in batch:
            slim = {k: run.get(k) for k in KEEP}
            slim["duration_s"] = _duration_s(run)
            seen[run["id"]] = slim
        print(f"página {page}: {len(batch)} runs")
        if len(batch) < 100:
            break

    if not seen:
        print("Nenhum run obtido — nada escrito.", file=sys.stderr)
        raise SystemExit(1)

    runs = sorted(seen.values(), key=lambda r: r.get("created_at") or "")
    payload = {
        "repo": args.repo,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_runs": len(runs),
        "runs": runs,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    print(f"{len(runs)} runs → {args.out} "
          f"({runs[0]['created_at'][:10]} → {runs[-1]['created_at'][:10]})")


if __name__ == "__main__":
    main()
