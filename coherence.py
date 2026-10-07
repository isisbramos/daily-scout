"""
Daily Scout — Coerência após troca do destaque (Rec. 6).

Problema: o modelo escreve o main_find, o reasoning e a correspondent_intro JUNTOS. Depois,
guards determinísticos podem TROCAR o main_find (repetição de edição recente, barra do Reddit,
revisor final em enforce). O destaque muda, mas a introdução — que o leitor vê no e-mail — e o
reasoning continuam falando do destaque antigo. O audit da ed.197 apontou exatamente isso.

Este módulo:
  1. registra cada troca em `content["main_swaps"]` e anota o reasoning (determinístico);
  2. reescreve a introdução UMA vez, com uma chamada curta de LLM, validada e com fallback
     determinístico — qualquer falha deixa a edição coerente do mesmo jeito, nunca bloqueia.
"""

from __future__ import annotations

import json
import logging
import os
import re

from llm_config import DEEPSEEK_BASE_URL, DEEPSEEK_EXTRA_BODY, DEEPSEEK_MODEL

logger = logging.getLogger("daily-scout")

ROOT = os.path.dirname(os.path.abspath(__file__))
PROMPT_PATH = os.path.join(ROOT, "prompts", "intro_rewrite_prompt.txt")
MAX_INTRO_CHARS = 420
MIN_INTRO_CHARS = 20


# ── 1. Registro da troca + reasoning ──────────────────────────────────
def note_main_swap(content: dict, old_main: dict, reason: str) -> None:
    """Registra que o main_find foi trocado e anota a justificativa da curadoria.

    Deve ser chamada logo APÓS `content["main_find"]` receber o novo destaque. Idempotente
    o bastante: cada chamada empilha uma troca (o reasoning ganha uma nota por troca).
    """
    old_title = (old_main or {}).get("title", "")
    new_title = content.get("main_find", {}).get("title", "")
    content.setdefault("main_swaps", []).append(
        {"from": old_title, "to": new_title, "reason": reason, "intro_refreshed": False}
    )
    reasoning = content.get("reasoning")
    if isinstance(reasoning, dict):
        original = str(reasoning.get("main_find_rationale") or "").strip()
        reasoning["main_find_rationale"] = (
            f"[AJUSTE AUTOMÁTICO — {reason}] O destaque escolhido pelo modelo ('{old_title}') foi "
            f"substituído por '{new_title}'. Justificativa original, que se refere ao destaque "
            f"anterior: {original}"
        ).strip()


# ── 2. Reescrita da introdução ────────────────────────────────────────
def _tokens(title: str) -> set[str]:
    return {w for w in re.findall(r"\w+", title.lower()) if len(w) >= 5}


def _mentions_old(text: str, old_title: str) -> bool:
    """A frase compartilha 2+ palavras significativas com o título do destaque antigo?"""
    return len(_tokens(text) & _tokens(old_title)) >= 2


def _fallback_intro(content: dict, old_intro: str, old_title: str) -> str:
    """Introdução determinística: destaque novo + a última frase da antiga, se não falar do destaque antigo."""
    title = content.get("main_find", {}).get("title", "").strip().rstrip(".")
    first = f"O destaque de hoje: {title}."
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", (old_intro or "").strip()) if s]
    tail = sentences[-1] if len(sentences) > 1 and not _mentions_old(sentences[-1], old_title) else ""
    return f"{first} {tail}".strip()


def _build_prompt(content: dict, old_intro: str, old_title: str) -> str:
    with open(PROMPT_PATH, encoding="utf-8") as f:
        template = f.read()
    main = content.get("main_find", {})
    summary = (main.get("body") or main.get("signal") or "")[:400].replace("\n", " ")
    others = "\n".join(f"- {qf.get('title', '')}" for qf in content.get("quick_finds", [])) or "(nenhum)"
    return (
        template.replace("{{NEW_TITLE}}", main.get("title", ""))
        .replace("{{NEW_SUMMARY}}", summary or "(sem resumo)")
        .replace("{{OTHERS}}", others)
        .replace("{{OLD_INTRO}}", old_intro or "(vazia)")
        .replace("{{OLD_TITLE}}", old_title or "(desconhecido)")
    )


def _call_llm(prompt: str, client=None) -> str:
    if client is None:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=DEEPSEEK_BASE_URL)
    resp = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": "Você é a AYA. Retorne sempre um JSON válido."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=600,
        extra_body=DEEPSEEK_EXTRA_BODY,
    )
    return resp.choices[0].message.content


def _valid_intro(intro, old_intro: str, old_title: str, tone_check=None) -> str | None:
    """Devolve o texto limpo se a nova introdução passar nas validações, senão None."""
    if not isinstance(intro, str):
        return None
    intro = intro.strip()
    if not MIN_INTRO_CHARS <= len(intro) <= MAX_INTRO_CHARS:
        return None
    if intro == (old_intro or "").strip() or _mentions_old(intro, old_title):
        return None
    if tone_check is not None and tone_check(intro):
        return None
    return intro


def refresh_after_swaps(content: dict, tone_check=None, client=None) -> dict | None:
    """Reescreve a correspondent_intro se o destaque foi trocado. Retorna um resumo (ou None).

    `tone_check(texto) -> bool` (True = reprovado) é injetado pelo pipeline para reaproveitar o
    detector de sensacionalismo sem import circular. Nunca levanta exceção: se a chamada ao LLM
    falhar ou a resposta não passar na validação, usa a introdução determinística de fallback.
    """
    swaps = content.get("main_swaps") or []
    pending = [s for s in swaps if not s.get("intro_refreshed")]
    if not pending:
        return None

    old_intro = str(content.get("correspondent_intro") or "")
    old_title = pending[0].get("from", "")
    result = {"swaps": len(pending), "method": "fallback", "old_intro": old_intro}
    new_intro = None
    try:
        raw = _call_llm(_build_prompt(content, old_intro, old_title), client)
        data = json.loads(raw)
        new_intro = _valid_intro(data.get("correspondent_intro") if isinstance(data, dict) else None,
                                 old_intro, old_title, tone_check)
        if new_intro:
            result["method"] = "llm"
        else:
            result["note"] = "resposta do LLM reprovada na validação"
    except Exception as err:  # falha aberta
        result["note"] = f"LLM falhou: {str(err)[:200]}"
        logger.warning(f"Coerência: reescrita da introdução falhou, usando fallback: {err}")

    if not new_intro:
        new_intro = _fallback_intro(content, old_intro, old_title)
    content["correspondent_intro"] = new_intro
    for s in pending:
        s["intro_refreshed"] = True
    result["new_intro"] = new_intro
    logger.info(f"Coerência: introdução reescrita após troca do destaque ({result['method']}): {new_intro[:120]}")
    return result
