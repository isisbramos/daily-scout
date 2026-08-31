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


def _covered_entities(records: list[dict]) -> list[tuple[str, set]]:
    """Entidades de todos os achados (main_find + quick_finds) das edições recentes,
    rotuladas pra debug. Base compartilhada por check_repetition e find_clean_quick_find."""
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
    return covered


def _overlap(entities: set, covered: list[tuple[str, set]], min_shared: int) -> tuple[list, str] | None:
    if len(entities) < min_shared:
        return None
    for label, cset in covered:
        shared = entities & cset
        if len(shared) >= min_shared:
            return sorted(shared), label
    return None


def check_repetition(content: dict, records: list[dict], min_shared: int = 2) -> list[dict]:
    """Guard determinístico de deduplicação (não depende do LLM seguir instrução).

    Compara as entidades dos achados selecionados hoje com as das edições recentes.
    Sobreposição de >= min_shared entidades sinaliza provável repetição. min_shared=2
    evita falso-positivo de uma entidade onipresente (ex: 'OpenAI' aparece todo dia).

    Retorna lista de hits estruturados (vazia se nada repetido):
      {where: 'main_find'|'quick_find', index: int|None, title, shared: [..], matched: label}
    O pipeline decide a ação (logar; dropar quick_finds repetidos; substituir main_find
    repetido — ver find_clean_quick_find).
    """
    covered = _covered_entities(records)

    def _match(item: dict) -> tuple[list, str] | None:
        return _overlap({e.lower() for e in item.get("entities", [])}, covered, min_shared)

    hits: list[dict] = []

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


def find_clean_quick_find(quick_finds: list[dict], records: list[dict], min_shared: int = 2) -> int | None:
    """Acha o índice do primeiro quick_find sem sobreposição de entidades com as
    edições recentes — candidato seguro pra promover a main_find quando o main_find
    original repete um achado já publicado. Retorna None se todos também repetirem."""
    covered = _covered_entities(records)
    for i, qf in enumerate(quick_finds):
        if _overlap({e.lower() for e in qf.get("entities", [])}, covered, min_shared) is None:
            return i
    return None


def promote_quick_find_to_main(qf: dict) -> dict:
    """Reconstrói um quick_find no formato de main_find, de forma determinística
    (sem chamada de LLM) — usado quando o main_find original precisa ser substituído
    por repetir uma edição recente. O `signal` do quick_find já segue a mesma lógica
    de conteúdo (o que aconteceu + por que importa + linha "→" de implicação prática),
    só falta o formato de main_find (body + bullets em vez de signal único)."""
    signal = (qf.get("signal") or "").strip()
    source = qf.get("source", "")
    # A fonte já aparece como sujeito da frase? (ex: signal "A Mistral lançou..." com
    # source "Mistral") — evita duplicar o nome ("Segundo Mistral, a Mistral lançou...").
    source_first_word = source.split(" ", 1)[0].lower() if source else ""
    subject_is_source = bool(source_first_word) and source_first_word in signal[:40].lower()

    if signal and source and not subject_is_source and not signal.lower().startswith(("segundo", "de acordo com")):
        # Só reescreve pra minúscula quando a frase abre com artigo (ex: "A Tencent
        # lançou..." → "a Tencent lançou..."); se abre com nome próprio (ex: "Sony
        # Music processa...") mantém a maiúscula pra não quebrar o nome.
        first_word = signal.split(" ", 1)[0].rstrip(",")
        if first_word.lower() in {"a", "o", "as", "os", "uma", "um"}:
            body = f"Segundo {source}, {signal[0].lower()}{signal[1:]}"
        else:
            body = f"Segundo {source}, {signal}"
    else:
        body = signal

    if "→" in signal:
        context, implication = signal.split("→", 1)
        bullets = [s.strip() for s in context.strip().split(". ") if s.strip()]
        bullets.append("→ " + implication.strip())
    else:
        bullets = [signal] if signal else []

    return {
        "title": qf.get("title", ""),
        "source": source,
        "body": body,
        "bullets": bullets[:3],
        "url": qf.get("url", ""),
        "display_url": qf.get("display_url", ""),
        "primary_audience": qf.get("primary_audience", "todos"),
        "step5_phrase": qf.get("step5_phrase", ""),
        "claim_status": qf.get("claim_status", ""),
        "entities": qf.get("entities", []),
    }


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
