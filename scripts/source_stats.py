"""Conta as fontes reais em sources_config.json.

Existe porque o README já teve uma contagem de fontes hardcoded em prosa que
ficou errada silenciosamente: dizia "31 fontes, 22 habilitadas" quando na
config real são 22 fontes, todas habilitadas — o 31 vinha de contar por engano
as chaves `_comment_*` (documentação inline do JSON) como se fossem fontes.

Uso: `python scripts/source_stats.py` imprime a contagem real. `real_sources()`
e `count_enabled()` são reaproveitados por tests/test_docs_sync.py pra travar
o README.md sincronizado com a config.
"""

from __future__ import annotations

import json
import os

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources_config.json"
)


def load_sources_config(path: str | None = None) -> dict:
    with open(path or CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def real_sources(config: dict) -> dict[str, dict]:
    """Filtra as chaves `_comment*` do bloco "sources" — são documentação
    inline no JSON, não fontes configuradas."""
    return {k: v for k, v in config.get("sources", {}).items() if isinstance(v, dict)}


def count_enabled(config: dict) -> int:
    return sum(1 for v in real_sources(config).values() if v.get("enabled", True))


def main() -> None:
    config = load_sources_config()
    sources = real_sources(config)
    enabled = sorted(k for k, v in sources.items() if v.get("enabled", True))
    disabled = sorted(k for k in sources if k not in enabled)

    print(f"Total de fontes configuradas: {len(sources)}")
    print(f"Habilitadas ({len(enabled)}): {', '.join(enabled)}")
    print(f"Desabilitadas ({len(disabled)}): {', '.join(disabled) if disabled else 'nenhuma'}")


if __name__ == "__main__":
    main()
