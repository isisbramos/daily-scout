"""
Daily Scout — Editorial Memory Store

Persistência append-only das edições publicadas, para dar memória à curadoria.
Resolve o gap stateless: antes, cada execução do pipeline rodava sem saber o que
a AYA já publicou — podia repetir o mesmo tema em dias consecutivos e não conseguia
conectar desdobramentos. Agora a curadoria recebe um resumo das últimas edições.

Camada 1 do plano de memória editorial:
  - append_edition()    → ao fim de cada edição enviada, registra um snapshot leve.
  - load_recent_editions() + format_memory_block() → injeta histórico no prompt.

Persistência: o arquivo é commitado de volta ao repo pelo workflow (CI é efêmero).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("daily-scout")

MEMORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory")
EDITIONS_PATH = os.path.join(MEMORY_DIR, "editions.jsonl")

# Brasília (UTC-3) — mesma referência de fuso usada no render do email.
_BRT = timezone(timedelta(hours=-3))


def load_recent_editions(n: int = 7) -> list[dict]:
    """Lê os últimos n registros do editions.jsonl (ordem de gravação: mais antigo
    primeiro no arquivo, mais recente por último). Retorna [] se não há histórico.

    Tolerante a linhas corrompidas: ignora e segue, nunca quebra o pipeline.
    """
    if not os.path.exists(EDITIONS_PATH):
        return []

    records: list[dict] = []
    with open(EDITIONS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("memory: linha inválida ignorada em editions.jsonl")
    return records[-n:]


def _resolve_sources_used(content: dict, source_index: dict | None) -> list:
    """Fontes realmente usadas na edição, como source_id canônico (= chave do
    sources_config), derivadas dos itens SELECIONADOS — não do meta.sources_used,
    que o LLM preenche de forma não confiável (vem vazio ou como contagem).

    Estratégia: mapear a URL de cada achado (main_find + quick_finds) → source_id,
    via `source_index` {url: source_id} passado pelo pipeline a partir dos
    filtered_items. Determinístico e independente do LLM. Mantém a ordem de seleção
    e deduplica. Fallback pro meta.sources_used (só se for lista) quando não há índice
    ou nenhuma URL casou — nunca quebra.
    """
    if source_index:
        used: list[str] = []
        seen: set[str] = set()
        items = [content.get("main_find", {})] + content.get("quick_finds", [])
        for item in items:
            sid = source_index.get((item or {}).get("url", ""))
            if sid and sid not in seen:
                seen.add(sid)
                used.append(sid)
        if used:
            return used

    meta_sources = content.get("meta", {}).get("sources_used", [])
    return meta_sources if isinstance(meta_sources, list) else []


def build_memory_record(edition: str, content: dict, source_index: dict | None = None) -> dict:
    """Monta o registro leve de uma edição a partir do output de curadoria.

    Mantém só o necessário para detectar repetição e conectar follow-ups —
    títulos, entidades, temas e fontes. Usa .get() em tudo: campos novos
    (entities/themes) podem faltar se o LLM não os emitir, e isso não pode quebrar.

    `source_index` ({url: source_id}) vem do pipeline (filtered_items) e permite
    registrar as fontes reais de forma determinística — ver _resolve_sources_used.
    """
    mf = content.get("main_find", {})

    sources = _resolve_sources_used(content, source_index)

    def _entities(d: dict) -> list:
        ents = d.get("entities") or []
        return ents if isinstance(ents, list) else []

    return {
        "edition": edition,
        "date": datetime.now(_BRT).strftime("%Y-%m-%d"),
        "main_find": {
            "title": mf.get("title", ""),
            "entities": _entities(mf),
            # claim_status pode vir None/ausente — normaliza pra string.
            "claim_status": mf.get("claim_status") or "",
        },
        "quick_finds": [
            {
                "title": qf.get("title", ""),
                "entities": _entities(qf),
            }
            for qf in content.get("quick_finds", [])
        ],
        "themes": content.get("themes", []) or [],
        "sources_used": sources,
        # Preenchido depois pelo loop de feedback (🔥/👍/😐) — gancho de calibração.
        "feedback_score": None,
    }


def append_edition(record: dict) -> None:
    """Adiciona um registro ao editions.jsonl (cria memory/ e o arquivo se preciso)."""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(EDITIONS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info(f"memory: edição {record.get('edition')} registrada em {EDITIONS_PATH}")


def check_repetition(content: dict, records: list[dict], min_shared: int = 2) -> list[dict]:
    """Guard determinístico de deduplicação (não depende do LLM seguir instrução).

    Compara as entidades dos achados selecionados hoje com as das edições recentes.
    Sobreposição de >= min_shared entidades sinaliza provável repetição. min_shared=2
    evita falso-positivo de uma entidade onipresente (ex: 'OpenAI' aparece todo dia).

    Retorna lista de hits estruturados (vazia se nada repetido):
      {where: 'main_find'|'quick_find', index: int|None, title, shared: [..], matched: label}
    O pipeline decide a ação (logar; dropar quick_finds repetidos).
    """
    covered: list[tuple[str, set]] = []
    for r in records:
        mf = r.get("main_find", {})
        covered.append(
            (f"ed.{r.get('edition', '?')} «{mf.get('title', '')[:40]}»",
             {e.lower() for e in mf.get("entities", [])})
        )
        for qf in r.get("quick_finds", []):
            covered.append(
                (f"ed.{r.get('edition', '?')} «{qf.get('title', '')[:40]}»",
                 {e.lower() for e in qf.get("entities", [])})
            )

    hits: list[dict] = []

    def _match(item: dict) -> tuple[list, str] | None:
        ents = {e.lower() for e in item.get("entities", [])}
        if len(ents) < min_shared:
            return None
        for label, cset in covered:
            shared = ents & cset
            if len(shared) >= min_shared:
                return sorted(shared), label
        return None

    mf_match = _match(content.get("main_find", {}))
    if mf_match:
        hits.append({"where": "main_find", "index": None,
                     "title": content.get("main_find", {}).get("title", ""),
                     "shared": mf_match[0], "matched": mf_match[1]})

    for i, qf in enumerate(content.get("quick_finds", [])):
        m = _match(qf)
        if m:
            hits.append({"where": "quick_find", "index": i,
                         "title": qf.get("title", ""),
                         "shared": m[0], "matched": m[1]})
    return hits


def format_memory_block(records: list[dict]) -> str:
    """Formata as edições recentes como bloco de texto para o prompt de curadoria.

    Retorna string vazia quando não há histórico (primeiras edições) — nesse caso
    o placeholder some do prompt e nenhuma instrução órfã sobre memória aparece.
    """
    if not records:
        return ""

    lines = [
        "═══ MEMÓRIA EDITORIAL — JÁ PUBLICADO (filtro obrigatório, aplique ANTES do AI Gate) ═══",
        "As edições abaixo JÁ SAÍRAM. Regra dura, antes de qualquer outra avaliação:",
        "→ Qualquer item de hoje cujo tema/entidades coincidam com um achado abaixo está PROIBIDO "
        "de virar main_find ou quick_find — A MENOS que o título traga informação comprovadamente "
        "NOVA (novo número, nova decisão, nova consequência) ausente da cobertura anterior.",
        "→ Na dúvida sobre se há informação nova: DESCARTE. Repetir um achado é o pior erro de curadoria.",
        "",
    ]
    for r in records:
        mf = r.get("main_find", {})
        ents = ", ".join(mf.get("entities", []))
        line = f"[{r.get('date', '?')} · ed.{r.get('edition', '?')}] PRINCIPAL: {mf.get('title', '')}"
        if ents:
            line += f"  (entidades: {ents})"
        lines.append(line)
        qf_titles = [qf.get("title", "") for qf in r.get("quick_finds", []) if qf.get("title")]
        if qf_titles:
            lines.append("    também cobriu: " + " | ".join(qf_titles))
    lines.append("")
    return "\n".join(lines)
