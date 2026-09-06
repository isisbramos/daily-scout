"""
Guarda contra drift entre sources_config.json e a contagem de fontes citada em
README.md. Sem isso, o número em prosa fica desatualizado silenciosamente
sempre que uma fonte é ligada/desligada/adicionada — foi exatamente o que já
aconteceu: o README dizia "31 fontes config-driven, 22 habilitadas" quando a
config real tinha 22 fontes, todas habilitadas (o 31 vinha de contar por
engano as chaves `_comment_*` do JSON como se fossem fontes).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.source_stats import real_sources

REPO_ROOT = Path(__file__).resolve().parent.parent


def _enabled_source_count() -> int:
    config = json.loads((REPO_ROOT / "sources_config.json").read_text(encoding="utf-8"))
    sources = real_sources(config)
    return sum(1 for v in sources.values() if v.get("enabled", True))


def test_readme_source_count_matches_config():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(r"sources/ \((\d+) fontes", readme)
    assert match, (
        "README.md não tem mais a linha 'sources/ (N fontes ...)' — "
        "atualize o regex deste teste para o novo formato"
    )

    readme_count = int(match.group(1))
    real_count = _enabled_source_count()
    assert readme_count == real_count, (
        f"README.md diz {readme_count} fontes mas sources_config.json tem "
        f"{real_count} habilitadas — rode `python scripts/source_stats.py` "
        f"e atualize o número no README"
    )
