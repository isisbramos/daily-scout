"""
Teste dos 3 patches do framework v5.4.
Roda curate_and_write() com 3 itens sintéticos e valida os vereditos.

Itens de teste (conforme ADR em Endurecer curadoria AYA v5.4):
  1. Koshy John — blog pessoal, manifesto puro        → DEVE ser descartado (v5.4 Patch 1)
  2. Mollick (AI + dado concreto) — ensaio com estudo → DEVE ser selecionado (exceção Patch 1)
  3. Claude.ai anúncio de feature — blog Anthropic    → DEVE ser selecionado (STEP 1.5 existente)

Saída: reasoning do LLM + veredito de cada item + diagnóstico pass/fail.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from pipeline import curate_and_write
from sources.base import SourceItem

TEST_ITEMS = [
    SourceItem(
        title="AI Should Elevate Your Thinking, Not Replace It",
        url="https://www.koshyjohn.com/blog/ai-should-elevate-your-thinking-not-replace-it/",
        source_id="personal_blog",
        source_label="koshyjohn.com",
        timestamp=time.time(),
        raw_score=0,
        num_comments=0,
        category="ai",
    ),
    SourceItem(
        title="Ethan Mollick: My study of 758 workers found AI boosts productivity 14% — but only when used as thought partner, not replacement",
        url="https://www.oneusefulthing.org/p/ai-productivity-study-758-workers",
        source_id="substack",
        source_label="One Useful Thing (Mollick)",
        timestamp=time.time(),
        raw_score=312,
        num_comments=47,
        category="ai",
    ),
    SourceItem(
        title="Claude.ai now supports Projects: persistent memory and files across conversations",
        url="https://www.anthropic.com/news/projects",
        source_id="anthropic_blog",
        source_label="Anthropic Blog",
        timestamp=time.time(),
        raw_score=0,
        num_comments=0,
        category="ai",
    ),
]

EXPECTED = {
    "koshyjohn.com": "DESCARTADO",
    "One Useful Thing (Mollick)": "SELECIONADO",
    "Anthropic Blog": "SELECIONADO",
}


def run_test():
    print("\n" + "=" * 60)
    print("TESTE v5.4 — FILTRO ESTRUTURAL ANTI-OPINION")
    print("=" * 60)
    print(f"\n{len(TEST_ITEMS)} itens de teste enviados ao LLM:\n")
    for i, item in enumerate(TEST_ITEMS, 1):
        print(f"  [{i}] {item.source_label}")
        print(f"      {item.title[:80]}")
    print()

    result = curate_and_write(TEST_ITEMS, raw_count=3)

    print("\n" + "=" * 60)
    print("REASONING DO LLM")
    print("=" * 60)
    reasoning = result.get("reasoning", {})
    if isinstance(reasoning, str):
        try:
            reasoning = json.loads(reasoning)
        except Exception:
            reasoning = {"_raw": reasoning}
    print("\nPassaram no AI Gate:")
    for t in reasoning.get("ai_gate_passed", []):
        print(f"  ✓ {t}")
    print("\nRejeitados (amostra):")
    for t in reasoning.get("ai_gate_rejected_sample", []):
        print(f"  ✗ {t}")
    print(f"\nRationale main_find: {reasoning.get('main_find_rationale', '—')}")
    print(f"Perspectiva: {reasoning.get('perspective_check', '—')}")
    if "_raw" in reasoning:
        print(f"\nReasoning (raw string):\n{reasoning['_raw']}")

    # Coletar itens selecionados — cruzar por URL (source pode vir vazio do LLM)
    url_to_label = {item.url: item.source_label for item in TEST_ITEMS}
    selected_labels = set()

    mf = result.get("main_find", {})
    if mf:
        mf_label = url_to_label.get(mf.get("url", ""), mf.get("source", mf.get("url", "—")))
        selected_labels.add(mf_label)
        print(f"\nmain_find: {mf_label} — {mf.get('title')}")
        print(f"  step5_phrase: {mf.get('step5_phrase')}")

    for qf in result.get("quick_finds", []):
        qf_label = url_to_label.get(qf.get("url", ""), qf.get("source", qf.get("url", "—")))
        selected_labels.add(qf_label)
        print(f"quick_find: {qf_label} — {qf.get('title')}")
        print(f"  step5_phrase: {qf.get('step5_phrase')}")

    for r in result.get("radar", []):
        r_label = url_to_label.get(r.get("url", ""), r.get("source", r.get("url", "—")))
        print(f"radar:      {r_label} — {r.get('title')}")
        print(f"  why_watch: {r.get('why_watch')}")

    print("\n" + "=" * 60)
    print("DIAGNÓSTICO v5.4")
    print("=" * 60)

    all_passed = True
    for item in TEST_ITEMS:
        label = item.source_label
        expected = EXPECTED[label]
        actual = "SELECIONADO" if label in selected_labels else "DESCARTADO"
        ok = actual == expected
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        print(f"\n  [{status}] {label}")
        print(f"        Esperado: {expected} | Obtido: {actual}")

    print()
    if all_passed:
        print("  RESULTADO FINAL: TODOS OS CASOS CORRETOS — v5.4 funcionando")
    else:
        print("  RESULTADO FINAL: FALHA em pelo menos 1 caso — revisar patches")
    print()

    # Salvar JSON completo do resultado para debug
    os.makedirs("debug", exist_ok=True)
    with open("debug/edition_TEST_v54.json", "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("  JSON completo salvo em debug/edition_TEST_v54.json")


if __name__ == "__main__":
    run_test()
