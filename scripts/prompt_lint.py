#!/usr/bin/env python3
"""Lint determinístico da saída da curadoria (sem LLM, sem chave de API).

Serve para comparar versões do prompt com os MESMOS checks, em vez de olhar uma edição
de teste e decidir pelo olho. Cada check conta violações de uma regra que o prompt já tem;
nenhum deles julga qualidade editorial (isso continua sendo leitura humana).

Uso:
    python scripts/prompt_lint.py curation.json items.json [curation2.json items2.json ...]

`curation.json` e `items.json` são os arquivos que `DEBUG_SAVE=true python pipeline.py`
grava em `debug/` (edition_N_curation.json e edition_N_items.json).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Nomes de fonte que não são "entidade" (poluem o guard de repetição, que compara entidades).
SOURCE_NAMES = {
    "techcrunch", "technode", "huggingface papers", "huggingface", "arxiv", "reddit",
    "hackernews", "hacker news", "scmp", "scmp tech", "mit technology review",
    "mit tech review brasil", "the github blog", "openai blog", "simon willison",
    "lobsters", "stratechery", "rest of world", "agência brasil",
}
META_RE = re.compile(
    r"\b(o t[ií]tulo|no t[ií]tulo|edi[cç][aã]o anterior|o an[uú]ncio s[oó] diz|a mem[oó]ria editorial)\b", re.I)
SPECULATION_RE = re.compile(r"pode antecipar|sinaliza|pode indicar|deve (levar|mudar)", re.I)
INEDITISM_RE = re.compile(r"um dos primeiros|pela primeira vez|historicamente|in[eé]dito", re.I)
ARROW_RE = re.compile(r"→ No seu trabalho:\s*(\w+)")
NUM_RE = re.compile(r"\d[\d.,]*")
RESEARCH_HOSTS = ("arxiv.org", "huggingface.co/papers")

# Rótulos legíveis, na ordem em que aparecem no relatório.
METRICS = [
    ("itens", "itens (main+quick+radar)"),
    ("radar_sem_url", "radar sem url"),
    ("meta_linguagem", "meta-linguagem vazada"),
    ("radar_especula", "especulação no radar"),
    ("ineditismo", "ineditismo inventado"),
    ("sem_linha_trabalho", "sem linha '→ No seu trabalho'"),
    ("linha_abre_com_se", "linha '→' abre com 'se'"),
    ("entidade_e_fonte", "entities com nome de fonte"),
    ("audiencia_dev", "audiência 'desenvolvedores'"),
    ("so_reddit", "itens só do Reddit"),
    ("papers", "papers (arXiv/HF)"),
    ("follow_ups", "follow-ups marcados"),
    ("numero_fora_do_input", "itens c/ número fora do input"),
]
# Para estes, MAIS é pior; os demais são só informativos (contagem, mix).
HIGHER_IS_WORSE = {"radar_sem_url", "meta_linguagem", "radar_especula", "ineditismo",
                   "sem_linha_trabalho", "entidade_e_fonte", "numero_fora_do_input"}


def _numbers(text: str) -> set[str]:
    return set(NUM_RE.findall(text or ""))


def lint_curation(curation: dict, items: list[dict]) -> dict:
    """Devolve {métrica: valor} para uma curadoria e o input que a gerou."""
    by_url = {i.get("url", ""): i for i in items}
    main = curation.get("main_find") or {}
    quick = curation.get("quick_finds") or []
    radar = curation.get("radar") or []
    # (item, texto principal) de main + quick
    found = [(main, main.get("body", ""))] + [(q, q.get("signal", "")) for q in quick]

    arrows = [ARROW_RE.search(text) for _, text in found]
    suspect_numbers = 0
    for item, text in found:
        src = by_url.get(item.get("url", ""), {})
        known = _numbers(src.get("title", "")) | _numbers(src.get("summary", ""))
        written = _numbers(" ".join([item.get("body", ""), item.get("signal", ""),
                                     " ".join(item.get("bullets", []) or [])]))
        extra = {n for n in written - known if n.strip(".,") not in {"1", "2", "3"}
                 and not re.fullmatch(r"20\d\d", n.strip(".,"))}
        suspect_numbers += 1 if extra else 0

    return {
        "itens": (1 if main else 0) + len(quick) + len(radar),
        "radar_sem_url": sum(1 for r in radar if not (r.get("url") or "").strip()),
        "meta_linguagem": sum(1 for _, t in found if META_RE.search(t or ""))
                          + sum(1 for r in radar if META_RE.search(r.get("why_watch", "") or "")),
        "radar_especula": sum(1 for r in radar if SPECULATION_RE.search(r.get("why_watch", "") or "")),
        "ineditismo": sum(1 for _, t in found if INEDITISM_RE.search(t or "")),
        "sem_linha_trabalho": sum(1 for a in arrows if not a),
        "linha_abre_com_se": sum(1 for a in arrows if a and a.group(1).lower() == "se"),
        "entidade_e_fonte": sum(1 for i, _ in found
                                if any(str(e).lower() in SOURCE_NAMES for e in i.get("entities", []) or [])),
        "audiencia_dev": sum(1 for i, _ in found if i.get("primary_audience") == "desenvolvedores"),
        "so_reddit": sum(1 for i, _ in found if "reddit.com" in (i.get("url") or "")),
        "papers": sum(1 for i, _ in found if any(h in (i.get("url") or "") for h in RESEARCH_HOSTS)),
        "follow_ups": sum(1 for i, _ in found if (i.get("follow_up") or "").strip()),
        "numero_fora_do_input": suspect_numbers,
    }


def format_table(columns: dict[str, dict]) -> str:
    """Tabela de texto: uma linha por métrica, uma coluna por rodada."""
    names = list(columns)
    width = max(len(label) for _, label in METRICS) + 2
    head = " " * width + "".join(f"{n[:14]:>16}" for n in names)
    lines = [head]
    for key, label in METRICS:
        row = "".join(f"{columns[n].get(key, '-'):>16}" for n in names)
        lines.append(f"{label:<{width}}{row}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) < 2 or len(argv) % 2:
        print(__doc__)
        return 2
    columns: dict[str, dict] = {}
    for curation_path, items_path in zip(argv[0::2], argv[1::2]):
        curation = json.loads(Path(curation_path).read_text(encoding="utf-8"))
        items = json.loads(Path(items_path).read_text(encoding="utf-8"))
        columns[Path(curation_path).stem[:14]] = lint_curation(curation, items)
    print(format_table(columns))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
