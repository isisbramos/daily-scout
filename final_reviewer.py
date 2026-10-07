"""
Daily Scout — Revisor final (Rec. 1 do plano de melhoria editorial).

Problema: a curadoria "diz" uma coisa e "faz" outra — o reasoning aprova itens que somem da
edição, rejeita panoramas e publica dois, escolhe um post anônimo como manchete. Este módulo
é um passo extra, DEPOIS da curadoria: uma segunda chamada de LLM (curta, só títulos) confere
cada item publicado contra as regras editoriais e aponta candidatos fortes que ficaram de fora.

Dois modos (config `final_review.mode` em sources_config.json):
  - "off"     : não faz nada (default do código).
  - "shadow"  : roda o revisor e REGISTRA o veredito (debug/edition_N_review.json), sem alterar
                a edição. Serve para medir a concordância com o audit_agent antes de confiar.
  - "enforce" : além de registrar, remove os itens reprovados, com guardrails (mantém o mínimo
                de quick_finds, limita remoções, nunca bloqueia o envio).

Princípios: falha aberta (qualquer erro vira warning e a edição segue como a curadoria entregou);
sem regeneração de texto (só remove ou promove quick_find, reaproveitando o que já existe).
"""

from __future__ import annotations

import json
import logging
import os
import traceback
from difflib import SequenceMatcher

from coherence import note_main_swap
from llm_config import DEEPSEEK_BASE_URL, DEEPSEEK_EXTRA_BODY, DEEPSEEK_MODEL
from memory_store import find_eligible_quick_find, promote_quick_find_to_main

logger = logging.getLogger("daily-scout")

ROOT = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(ROOT, "prompts", "final_review_prompt.txt")

VALID_RULES = {"funding", "panorama", "opinion", "unverified", "rehash", "offtopic", "other", "none"}
DEFAULT_MIN_QUICK_FINDS = 3
DEFAULT_MAX_REMOVALS = 2


def _reasoning(content: dict) -> dict:
    """`content["reasoning"]` como dict; qualquer outro formato vira {} (nunca quebra)."""
    r = content.get("reasoning")
    return r if isinstance(r, dict) else {}


# ── Checagem determinística: reasoning × edição ───────────────────────
def find_contradictions(content: dict, threshold: float = 0.85) -> list[dict]:
    """Itens publicados que o próprio reasoning da curadoria listou como REJEITADOS no AI Gate.

    Sem LLM. `ai_gate_rejected_sample` é uma amostra de títulos descartados; se um deles
    reaparece como main_find/quick_find, a curadoria se contradisse.
    """
    rejected = [r for r in (_reasoning(content).get("ai_gate_rejected_sample") or [])
                if isinstance(r, str)]
    if not rejected:
        return []
    published = [("main_find", content.get("main_find", {}))] + [
        ("quick_find", qf) for qf in content.get("quick_finds", [])
    ]
    out = []
    for where, item in published:
        title = (item or {}).get("title", "").lower().strip()
        if not title:
            continue
        for r in rejected:
            rl = r.lower().strip()
            if title in rl or SequenceMatcher(None, title, rl[: len(title) + 20]).ratio() >= threshold:
                out.append({"where": where, "title": item.get("title", ""), "rejected_as": r[:120]})
                break
    return out


# ── Entrada e saída do LLM ────────────────────────────────────────────
def _build_prompt(content: dict, candidates: list) -> str:
    with open(PROMPT_PATH, encoding="utf-8") as f:
        template = f.read()

    cand_lines = [f"C{i}: [{c.source_label}] {c.title[:160]}" for i, c in enumerate(candidates, 1)]

    items = [("main_find", content.get("main_find", {}))] + [
        ("quick_find", qf) for qf in content.get("quick_finds", [])
    ]
    pub_lines = []
    for idx, (kind, it) in enumerate(items):
        detail = (it.get("body") or it.get("signal") or "")[:260].replace("\n", " ")
        pub_lines.append(
            f"idx {idx} ({kind}) [{it.get('source', '?')}] {it.get('title', '')}\n"
            f"   claim_status: {it.get('claim_status', '')} | step5: {it.get('step5_phrase', '')}\n"
            f"   resumo: {detail}\n   url: {it.get('url', '')}"
        )

    rationale = str(_reasoning(content).get("main_find_rationale") or "")[:500]
    return (
        template.replace("{{CANDIDATES}}", "\n".join(cand_lines))
        .replace("{{PUBLISHED}}", "\n".join(pub_lines))
        .replace("{{RATIONALE}}", rationale or "(vazia)")
    )


def _as_dict_items(value) -> list[dict]:
    """Normaliza o que o modelo devolveu para uma lista de dicts.

    O LLM nem sempre respeita o formato: pode mandar a lista como dict indexado
    ({"0": {...}, "1": {...}}), ou itens como texto solto. Entradas que não dão
    para interpretar são descartadas (nunca levantam exceção).
    """
    if isinstance(value, dict):
        out = []
        for k, v in value.items():
            if isinstance(v, dict):
                out.append({"idx": int(k) if str(k).isdigit() else None, **v})
        return out
    return [v for v in (value or []) if isinstance(v, dict)] if isinstance(value, list) else []


def _parse_review(raw: str, n_items: int, candidates: list) -> dict:
    """Valida o JSON do revisor. Descarta vereditos malformados em vez de falhar."""
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"resposta do revisor não é um objeto JSON ({type(data).__name__})")
    verdicts = []
    for v in _as_dict_items(data.get("verdicts")):
        idx = v.get("idx")
        if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < n_items:
            continue
        verdict = str(v.get("verdict", "")).upper()
        if verdict not in ("PASS", "FAIL"):
            continue
        rule = str(v.get("rule", "none")).lower()
        verdicts.append({"idx": idx, "verdict": verdict,
                         "rule": rule if rule in VALID_RULES else "other",
                         "why": str(v.get("why", ""))[:300]})
    missed = []
    raw_missed = data.get("missed")
    raw_missed = raw_missed if isinstance(raw_missed, list) else []
    for m in raw_missed[:2]:
        # aceita {"candidate": "C7", "why": "..."} ou texto solto "C7" / "C7: motivo"
        cand = m.get("candidate", "") if isinstance(m, dict) else str(m).split(":", 1)[0]
        why = m.get("why", "") if isinstance(m, dict) else (str(m).split(":", 1)[1] if ":" in str(m) else "")
        cid = str(cand).strip().upper().lstrip("C")
        if cid.isdigit() and 1 <= int(cid) <= len(candidates):
            c = candidates[int(cid) - 1]
            missed.append({"candidate": f"C{cid}", "title": c.title, "source": c.source_label,
                           "url": c.url, "why": str(why)[:300]})
    return {"verdicts": verdicts, "missed": missed}


def _call_llm(prompt: str, client=None) -> str:
    if client is None:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=DEEPSEEK_BASE_URL)
    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "Você é um revisor editorial rigoroso. Retorne sempre um JSON válido."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=4096,
        extra_body=DEEPSEEK_EXTRA_BODY,
    )
    return resp.choices[0].message.content


# ── Aplicação (modo enforce) ──────────────────────────────────────────
def apply_review(content: dict, verdicts: list[dict], candidates_by_url: dict | None = None,
                 recent_editions: list[dict] | None = None,
                 min_quick_finds: int = DEFAULT_MIN_QUICK_FINDS,
                 max_removals: int = DEFAULT_MAX_REMOVALS) -> list[dict]:
    """Remove itens reprovados com guardrails. Retorna a lista de ações tomadas.

    - quick_find FAIL: removido, desde que sobrem >= min_quick_finds e dentro de max_removals.
    - main_find FAIL: substituído pelo primeiro quick_find PASS elegível (passa a barra do
      main_find e não repete edição recente); sem candidato, mantém e registra.
    """
    items = [content.get("main_find", {})] + list(content.get("quick_finds", []))
    # Vereditos FAIL por identidade do item: promover/remover não desloca nada.
    fails = {id(items[v["idx"]]): v for v in verdicts
             if v["verdict"] == "FAIL" and 0 <= v["idx"] < len(items)}
    actions: list[dict] = []
    quick = list(content.get("quick_finds", []))
    removals = 0

    main = content.get("main_find", {})
    if id(main) in fails and max_removals > 0:
        passing = [qf for qf in quick if id(qf) not in fails]
        pos = find_eligible_quick_find(passing, candidates_by_url or {}, recent_editions)
        if pos is not None:
            promoted = passing[pos]
            quick = [qf for qf in quick if qf is not promoted]
            content["main_find"] = promote_quick_find_to_main(promoted)
            note_main_swap(content, main, f"revisor final: {fails[id(main)]['rule']}")
            actions.append({"action": "main_replaced", "removed": main.get("title", ""),
                            "promoted": promoted.get("title", ""), "rule": fails[id(main)]["rule"]})
            removals += 1
        else:
            actions.append({"action": "main_kept_no_replacement", "title": main.get("title", ""),
                            "rule": fails[id(main)]["rule"]})

    for qf in list(quick):
        v = fails.get(id(qf))
        if not v:
            continue
        if removals >= max_removals or len(quick) - 1 < min_quick_finds:
            actions.append({"action": "kept_by_guardrail", "title": qf.get("title", ""), "rule": v["rule"]})
            continue
        quick = [x for x in quick if x is not qf]
        actions.append({"action": "quick_removed", "title": qf.get("title", ""), "rule": v["rule"]})
        removals += 1
    content["quick_finds"] = quick
    return actions


# ── Orquestração ──────────────────────────────────────────────────────
def run_final_review(content: dict, candidates: list, cfg: dict | None,
                     recent_editions: list[dict] | None = None, client=None) -> dict | None:
    """Roda o revisor conforme `cfg` ({"mode": "off|shadow|enforce", ...}).

    Retorna o relatório (para salvar em debug/) ou None se estiver off. Em enforce, MUTA
    `content`. Nunca levanta exceção: erro vira warning e a edição segue intacta.
    """
    cfg = cfg or {}
    mode = cfg.get("mode", "off")
    if mode == "off":
        return None
    review: dict = {"mode": mode, "model": DEEPSEEK_MODEL}
    try:
        review["contradictions"] = find_contradictions(content)
        n_items = 1 + len(content.get("quick_finds", []))
        raw = _call_llm(_build_prompt(content, candidates), client)
        review["raw_response"] = (raw or "")[:4000]   # para depurar se o parse falhar
        review.update(_parse_review(raw, n_items, candidates))

        fails = [v for v in review["verdicts"] if v["verdict"] == "FAIL"]
        logger.info(f"Revisor final [{mode}]: {len(fails)} FAIL de {n_items} itens; "
                    f"{len(review['missed'])} candidato(s) forte(s) omitido(s); "
                    f"{len(review['contradictions'])} contradição(ões) com o reasoning")
        for v in fails:
            logger.info(f"  [REVIEW FAIL idx {v['idx']}] {v['rule']}: {v['why'][:120]}")
        for m in review["missed"]:
            logger.info(f"  [REVIEW MISSED] {m['title'][:80]} — {m['why'][:100]}")

        if mode == "enforce":
            by_url = {c.url: c for c in candidates}
            review["actions"] = apply_review(
                content, review["verdicts"], by_url, recent_editions,
                min_quick_finds=cfg.get("min_quick_finds", DEFAULT_MIN_QUICK_FINDS),
                max_removals=cfg.get("max_removals", DEFAULT_MAX_REMOVALS),
            )
            for a in review["actions"]:
                logger.warning(f"Revisor final: {a}")
    except Exception as err:  # falha aberta: nunca bloqueia o envio
        frame = traceback.extract_tb(err.__traceback__)[-1]
        where = f"{os.path.basename(frame.filename)}:{frame.lineno} ({frame.name})"
        review["error"] = f"{type(err).__name__}: {str(err)[:250]} @ {where}"
        logger.warning(f"Revisor final falhou (não-bloqueante): {review['error']}")
    return review
