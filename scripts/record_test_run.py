"""Converte o relatório JUnit XML de uma run de pytest num registro JSON e
acrescenta a ci/test_runs.jsonl — histórico de saúde de CI ao longo do tempo,
consumido por dashboard.py.

Só faz a leitura/gravação do arquivo local; quem commita de volta pro repo é
scripts/persist_to_git.sh, chamado como passo separado em tests.yml.

Uso (chamado pelo workflow, mas roda igual local):
  pytest tests/ --junitxml=pytest-results.xml
  python scripts/record_test_run.py pytest-results.xml \
      --commit-sha "$GITHUB_SHA" --trigger "$GITHUB_EVENT_NAME"
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(ROOT, "ci", "test_runs.jsonl")


def _pytest_version() -> str:
    try:
        import pytest

        return pytest.__version__
    except Exception:
        return "?"


def parse_junit(xml_path: str) -> dict:
    """JUnit XML do pytest tem uma <testsuite> raiz (ou <testsuites> com uma
    <testsuite> filha, dependendo da versão) com os totais já agregados nos
    atributos — não precisa contar <testcase> um a um."""
    root = ET.parse(xml_path).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        raise ValueError(f"formato de JUnit XML inesperado em {xml_path}")

    total = int(suite.get("tests", 0))
    failed = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    passed = total - failed - skipped

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "duration_s": round(float(suite.get("time", 0)), 2),
    }


def build_record(xml_path: str, commit_sha: str, trigger: str) -> dict:
    counts = parse_junit(xml_path)
    return {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit_sha": commit_sha[:7] if commit_sha else "",
        "trigger": trigger or "",
        "python_version": platform.python_version(),
        "pytest_version": _pytest_version(),
        **counts,
        "conclusion": "passed" if counts["failed"] == 0 else "failed",
    }


def append_record(record: dict) -> None:
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("junit_xml", help="Caminho do relatório JUnit XML gerado pelo pytest")
    p.add_argument("--commit-sha", default=os.environ.get("GITHUB_SHA", ""))
    p.add_argument("--trigger", default=os.environ.get("GITHUB_EVENT_NAME", ""))
    args = p.parse_args()

    if not os.path.exists(args.junit_xml):
        print(f"[record_test_run] ERRO: {args.junit_xml} não existe.", file=sys.stderr)
        sys.exit(1)

    record = build_record(args.junit_xml, args.commit_sha, args.trigger)
    append_record(record)
    print(f"[record_test_run] registrado: {record}")


if __name__ == "__main__":
    main()
