"""
Daily Scout — Vault Bridge (Stage A)

Gera, a partir de cada edição enviada, uma nota atômica no formato do isis-brain
(vault Obsidian) e grava em vault-outbox/<pasta-do-tipo>/<manchete>.md.

Por que um "outbox" em vez de escrever direto no vault: o vault sincroniza via
Obsidian Sync/iCloud, inacessível a partir do runner do GitHub Actions (roda na
nuvem, sem acesso ao filesystem do Mac). O outbox é o trecho da ponte que o CI
consegue fazer sozinho — commitar o arquivo de volta ao repo, no mesmo padrão
já usado por memory/editions.jsonl (ver memory_store.py). A ponte até o vault
de fato (Stage B) roda localmente — ver scripts/sync_to_vault.py.

Segue o formato descrito em "Prompt de captura AYA.md" > Regras obrigatórias
de cada nota: frontmatter YAML + corpo + rodapé com backlinks.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone, timedelta

OUTBOX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault-outbox")

_BRT = timezone(timedelta(hours=-3))

# Pasta de destino no vault + tipo de nota, por natureza do conteúdo. Por ora
# geramos só "insight" (achado atômico) a partir do main_find de cada edição —
# ver tabela "Tipos de nota possíveis" no prompt de captura para os demais tipos.
_FOLDER_BY_TIPO = {
    "insight": "03-insights",
}

# Temas fixos do vault (ver "Prompt de captura AYA.md" > Filosofia do isis-brain).
# Cada tema recebe algumas keywords pra casar com o campo livre `themes` da
# edição (ex: "métricas de feedback" -> Observability). Ajuste esta lista se a
# taxonomia real do vault mudar — nunca inventamos tema novo (regra do vault),
# o que não casa vira tag provisória.
_KNOWN_TEMAS = {
    "Observability": ("feedback", "métrica", "metrica", "metric", "observability", "rating"),
    "Product Thinking": ("produto", "product", "roadmap", "workflow"),
    "Documentação": ("documentação", "documentacao", "documentation", "doc"),
}
_DEFAULT_TEMA = "Editorial"


def _slugify_filename(title: str, max_words: int = 8) -> str:
    """Manchete -> nome de arquivo. Sem prefixos/underscores (convenção do vault:
    o nome do arquivo É a manchete da ideia)."""
    clean = re.sub(r'[\\/:*?"<>|]', "", title).strip()
    words = clean.split()
    return " ".join(words[:max_words]) or "Achado sem titulo"


def _provisional_tag(theme: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", theme.lower()).strip("-")
    return f"tema-provisorio/{slug}" if slug else "tema-provisorio"


def _pick_temas(themes: list[str]) -> tuple[list[str], list[str]]:
    """Casa os temas livres da edição (ex: 'agentes de código') contra a
    taxonomia fixa do vault via keyword match. O que não casa vira tag
    provisória — nunca inventa tema novo no frontmatter (regra do vault)."""
    matched: set[str] = set()
    provisional: list[str] = []
    for theme in themes:
        theme_lower = theme.lower()
        hit = next(
            (tema for tema, kws in _KNOWN_TEMAS.items() if any(kw in theme_lower for kw in kws)),
            None,
        )
        if hit:
            matched.add(hit)
        else:
            provisional.append(_provisional_tag(theme))
    matched.add(_DEFAULT_TEMA)
    return sorted(matched), provisional


def build_insight_note(edition: str, content: dict) -> dict | None:
    """Monta a nota da vault a partir do main_find da edição. Retorna None se
    não há achado publicável (edição vazia/erro) — nunca quebra o pipeline."""
    mf = content.get("main_find") or {}
    title = (mf.get("title") or "").strip()
    if not title:
        return None

    today = datetime.now(_BRT).strftime("%Y-%m-%d")
    temas, provisional_tags = _pick_temas(content.get("themes", []) or [])
    filename = _slugify_filename(title)

    tags = ", ".join(["insight", *provisional_tags])
    frontmatter = "\n".join(
        [
            "---",
            "tipo: insight",
            f"criado: {today}",
            f"tags: [{tags}]",
            f"temas: [{', '.join(temas)}]",
            "projetos: [AYA]",
            f"fonte_edicao: {edition}",
            "---",
        ]
    )

    body_lines = [(mf.get("body") or "").strip()]
    for bullet in mf.get("bullets") or []:
        body_lines.append(f"- {bullet}")
    url = mf.get("url")
    if url:
        body_lines.append(f"\nFonte: {url}")

    footer = "\n".join(
        [
            "---",
            "**Temas:** " + " · ".join(f"[[{t}]]" for t in temas),
            "**Projeto:** [[AYA]]",
            f"**Daily:** [[{today}]]",
        ]
    )

    text = "\n\n".join([frontmatter, f"# {title}", "\n".join(body_lines), footer]) + "\n"

    return {
        "relative_path": os.path.join(_FOLDER_BY_TIPO["insight"], f"{filename}.md"),
        "content": text,
    }


def write_to_outbox(note: dict) -> str:
    """Grava a nota no outbox do repo (é isso que o CI commita). Retorna o path
    absoluto do arquivo escrito."""
    dest = os.path.join(OUTBOX_DIR, note["relative_path"])
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(note["content"])
    return dest
