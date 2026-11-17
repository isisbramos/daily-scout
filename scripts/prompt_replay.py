#!/usr/bin/env python3
"""Replay de prompt: roda a MESMA entrada fixa N vezes e mede com os checks de prompt_lint.

Por quê: avaliar o prompt por uma única edição de teste mistura três coisas — o efeito da
mudança, a aleatoriedade do LLM e a entrada do dia (o feed muda). Aqui a entrada é fixa
(tests/fixtures/replay/*_items.json) e há N execuções por entrada, então a diferença entre
duas versões do prompt aparece como diferença de média, não de sorte.

Fluxo para mudar o prompt:
    1. python scripts/prompt_replay.py --label base            # antes da mudança
    2. (muda o prompt)
    3. python scripts/prompt_replay.py --label novo --compare debug/replay/base.json
Se alguma métrica "pior = mais alto" subir, a mudança não entra sem explicação.

Precisa de DEEPSEEK_API_KEY (chama o LLM de verdade, ~1 chamada por entrada x runs).
Não envia nada, não grava memória editorial. Por padrão roda SEM memória editorial, para o
resultado não depender de quais edições saíram nos últimos dias (--with-memory liga).

Entradas novas: copie o `debug/edition_N_items.json` de um dry run (DEBUG_SAVE=true) para
tests/fixtures/replay/ — são títulos públicos de notícias, sem dado interno.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.prompt_lint import HIGHER_IS_WORSE, METRICS, lint_curation  # noqa: E402

FIXTURES_DIR = ROOT / "tests" / "fixtures" / "replay"
OUT_DIR = ROOT / "debug" / "replay"


def load_fixture(path: Path) -> tuple[list[dict], list]:
    """Lê um *_items.json e devolve (dicts crus, lista de SourceItem)."""
    from sources.base import SourceItem

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    items = []
    for r in raw:
        extra = {"summary": r["summary"]} if r.get("summary") else {}
        items.append(SourceItem(
            title=r["title"], url=r["url"], source_id=r.get("source_id", ""),
            source_label=r.get("source", ""), timestamp=time.time(),
            raw_score=r.get("score", 0), num_comments=r.get("comments", 0),
            cross_source_count=r.get("cross_source_count", 1),
            cross_source_ids=r.get("cross_source_ids", []), extra=extra,
        ))
    return raw, items


def run_replay(fixtures_dir: Path, runs: int, curate_fn, save_dir: Path | None = None) -> dict:
    """Roda `curate_fn(items, raw_count=N)` `runs` vezes por fixture.

    Devolve {"fixtures": {nome: {"runs": [métricas...], "failures": n}}, "mean": {métrica: média}}.
    """
    result: dict = {"fixtures": {}, "mean": {}}
    for path in sorted(Path(fixtures_dir).glob("*_items.json")):
        raw, items = load_fixture(path)
        name = path.name.removesuffix("_items.json")
        entry = {"runs": [], "failures": 0}
        for k in range(1, runs + 1):
            try:
                curation = curate_fn(items, raw_count=len(items))
            except Exception as err:  # uma falha do LLM não derruba o replay inteiro
                entry["failures"] += 1
                print(f"  [{name} #{k}] falhou: {type(err).__name__}: {str(err)[:100]}", file=sys.stderr)
                continue
            entry["runs"].append(lint_curation(curation, raw))
            if save_dir:
                save_dir.mkdir(parents=True, exist_ok=True)
                (save_dir / f"{name}_run{k}.json").write_text(
                    json.dumps(curation, ensure_ascii=False, indent=2), encoding="utf-8")
        result["fixtures"][name] = entry

    all_runs = [m for e in result["fixtures"].values() for m in e["runs"]]
    if all_runs:
        result["mean"] = {key: round(sum(m[key] for m in all_runs) / len(all_runs), 2)
                          for key, _ in METRICS}
    return result


def format_report(result: dict, baseline: dict | None = None) -> str:
    lines = []
    width = max(len(label) for _, label in METRICS) + 2
    total_runs = sum(len(e["runs"]) for e in result["fixtures"].values())
    fails = sum(e["failures"] for e in result["fixtures"].values())
    lines.append(f"{len(result['fixtures'])} entradas, {total_runs} execuções ({fails} falhas)")
    lines.append(f"{'métrica (média por execução)':<{width}}{'agora':>9}" + (f"{'base':>9}{'delta':>9}" if baseline else ""))
    for key, label in METRICS:
        now = result["mean"].get(key, 0)
        row = f"{label:<{width}}{now:>9}"
        if baseline:
            base = baseline.get("mean", {}).get(key, 0)
            delta = round(now - base, 2)
            flag = " ⚠" if key in HIGHER_IS_WORSE and delta > 0 else ""
            row += f"{base:>9}{delta:>+9}{flag}"
        lines.append(row)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", required=True, help="nome desta rodada (grava debug/replay/<label>.json)")
    ap.add_argument("--runs", type=int, default=3, help="execuções por entrada (padrão 3)")
    ap.add_argument("--fixtures", type=Path, default=FIXTURES_DIR)
    ap.add_argument("--compare", type=Path, help="JSON de uma rodada anterior para comparar")
    ap.add_argument("--with-memory", action="store_true", help="liga a memória editorial (padrão: desligada)")
    args = ap.parse_args(argv)

    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("DEEPSEEK_API_KEY não configurada — o replay chama o LLM de verdade.", file=sys.stderr)
        return 2

    os.environ.setdefault("DRY_RUN", "true")
    import pipeline

    if not args.with_memory:
        pipeline.load_recent_editions = lambda n=7: []  # entrada fixa => memória fixa (vazia)

    result = run_replay(args.fixtures, args.runs, pipeline.curate_and_write, OUT_DIR / args.label)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{args.label}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    baseline = json.loads(args.compare.read_text(encoding="utf-8")) if args.compare else None
    print(format_report(result, baseline))
    print(f"\nSaídas para leitura humana: {OUT_DIR / args.label}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
