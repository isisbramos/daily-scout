"""
AYA — Rótulo de decisão por item (P / T / C).

Mede o que o Content Report ainda não mede: quantos itens de cada edição entregam uma
DECISÃO a quem usa IA no trabalho (o TESTE DE DECISÃO do STEP 2 do prompt de curadoria).

  P (decisão)  — dá para tomar, rever ou adiar uma decisão de ferramenta, fluxo,
                 fornecedor, custo, risco ou compliance.
  T (técnico)  — como modelos/sistemas funcionam por dentro (arquitetura, treino,
                 quantização, benchmark, método de pesquisa, infra de desenvolvedor).
  C (contexto) — mercado, empresa, geopolítica ou cultura sem decisão direta.

Por que um módulo separado do audit_agent: o prompt do juiz do audit é a régua da série
histórica de notas (Scorecard de Qualidade). Mexer nele muda a série. Aqui é uma chamada
própria, com prompt próprio, que NÃO altera a edição nem o audit.

Uso:
  python decision_labels.py --edition 247             # precisa de debug/edition_247_curation.json
  python decision_labels.py --all --skip-existing     # idempotente (CI)
  python decision_labels.py --from-memory 234-247     # backfill só com títulos (memory/editions.jsonl)
  python decision_labels.py --calibrate               # concordância com a leitura humana

Saída: debug/edition_XXX_labels.json (persiste no repo, como o audit).
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Literal

from pydantic import BaseModel, ValidationError

from llm_config import AUDIT_BASE_URL, AUDIT_EXTRA_BODY, AUDIT_MODEL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("decision-labels")

ROOT = os.path.dirname(os.path.abspath(__file__))
DEBUG_DIR = os.path.join(ROOT, "debug")
EDITIONS_PATH = os.path.join(ROOT, "memory", "editions.jsonl")
HUMAN_LABELS_PATH = os.path.join(ROOT, "tests", "fixtures", "decision_labels_human.json")

API_KEY = os.environ.get("AUDIT_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
LABELS = ("P", "T", "C")
_BRT = timezone(timedelta(hours=-3))
_TEXT_LIMIT = 400  # caracteres do corpo/signal que o juiz vê por item

# Exemplos do prompt. Ficam FORA da conta de calibração (senão a concordância infla).
FEWSHOT: dict[str, str] = {
    "ChatPRD encerra free trials após onda de fraude de tokens": "P",
    "Apps feitos no Lovable expõem passaportes e mais de 200 mil mensagens privadas": "P",
    "Clover-35B-A3B-Preview: modelo de difusão com resultado de 73,6 no SWE-bench Verified": "T",
    "Pesquisa escala supervisão de provas matemáticas a partir de livros didáticos estruturados": "T",
    "Lucro da Tencent cai com gasto em infraestrutura de IA seis vezes maior": "C",
    "Nvidia diz que não pretende reconduzir Jensen Huang como CEO": "C",
}


# ── Schema ─────────────────────────────────────────────────────────────
class ItemLabel(BaseModel):
    idx: int
    label: Literal["P", "T", "C"]
    decision: str = ""  # 1 frase: que decisão e de quem (P); por que não há decisão (T/C)


class LabelBatch(BaseModel):
    items: list[ItemLabel]


# ── Prompt ─────────────────────────────────────────────────────────────
SYSTEM = """Você classifica itens de uma newsletter diária de IA para quem USA IA no trabalho (product managers, fundadores, líderes de negócio), não para quem constrói IA.

Para cada item, escolha UM rótulo:

P — DECISÃO. Um profissional que usa IA no dia a dia consegue tomar, rever ou adiar uma decisão por causa do item: escolha de ferramenta, fluxo de trabalho, fornecedor, custo, risco ou compliance. Inclui lançamento de produto ou modelo de fornecedor, mudança de preço ou de termos, incidente de segurança em fornecedor, regra com efeito de compliance.
T — TÉCNICO. O item trata de como modelos ou sistemas funcionam por dentro: arquitetura, treino, quantização, benchmark, método de pesquisa, protocolo ou infraestrutura de desenvolvedor. Sem decisão acionável para quem usa IA no negócio.
C — CONTEXTO. Notícia de mercado, empresa, geopolítica ou cultura sem decisão direta: resultado financeiro, nomeação, investimento, disputa política, parceria genérica, curiosidade.

Regras de desempate:
1. Se T e P parecem possíveis, use P só se você consegue escrever, em uma frase, QUE decisão e QUEM a toma. Se não, use T.
2. Regulação ou crítica sem efeito direto numa decisão é C.
3. Julgue pelo título e pelo texto dado. Não use conhecimento externo para inventar uma decisão.

Exemplos:
- "ChatPRD encerra free trials após onda de fraude de tokens" → P (quem opera produto de IA com teste gratuito revisa o custo de inferência por trial)
- "Apps feitos no Lovable expõem passaportes e mais de 200 mil mensagens privadas" → P (quem usa a ferramenta revisa o risco de dados dos apps gerados)
- "Clover-35B-A3B-Preview: modelo de difusão com resultado de 73,6 no SWE-bench Verified" → T (benchmark de modelo, sem decisão para quem usa IA no negócio)
- "Pesquisa escala supervisão de provas matemáticas a partir de livros didáticos estruturados" → T (método de pesquisa)
- "Lucro da Tencent cai com gasto em infraestrutura de IA seis vezes maior" → C (resultado financeiro)
- "Nvidia diz que não pretende reconduzir Jensen Huang como CEO" → C (nomeação)

Responda SÓ com um objeto JSON: {"items": [{"idx": 0, "label": "P", "decision": "uma frase"}, ...]} com um objeto para cada item, na mesma numeração da entrada."""


def build_prompt(items: list[dict]) -> str:
    blocks = []
    for i, it in enumerate(items):
        text = (it.get("text") or "").strip().replace("\n", " ")[:_TEXT_LIMIT]
        block = f"[{i}] ({it['field']}) {it['title']}"
        if text:
            block += f"\n    Texto: {text}"
        blocks.append(block)
    return "Rotule os itens abaixo.\n\n" + "\n".join(blocks)


# ── Itens de uma edição ────────────────────────────────────────────────
def collect_items(curation: dict) -> list[dict]:
    """Achado do dia, quick finds e radar de um curation output, como lista plana."""
    items: list[dict] = []
    mf = curation.get("main_find")
    if isinstance(mf, dict) and mf.get("title"):
        items.append({"field": "main_find", "title": mf["title"], "text": mf.get("body", "")})
    for i, qf in enumerate(curation.get("quick_finds") or []):
        if isinstance(qf, dict) and qf.get("title"):
            items.append({"field": f"quick_finds[{i}]", "title": qf["title"], "text": qf.get("signal", "")})
    for i, rd in enumerate(curation.get("radar") or []):
        if isinstance(rd, dict) and rd.get("title"):
            items.append({"field": f"radar[{i}]", "title": rd["title"], "text": rd.get("why_watch", "")})
    return items


def items_from_memory(record: dict) -> list[dict]:
    """Backfill: o editions.jsonl só guarda título (achado do dia + quick finds)."""
    items: list[dict] = []
    mf = record.get("main_find") or {}
    if mf.get("title"):
        items.append({"field": "main_find", "title": mf["title"], "text": ""})
    for i, qf in enumerate(record.get("quick_finds") or []):
        if qf.get("title"):
            items.append({"field": f"quick_finds[{i}]", "title": qf["title"], "text": ""})
    return items


# ── Chamada ao juiz ────────────────────────────────────────────────────
def _make_client():
    from openai import OpenAI

    if not API_KEY:
        raise ValueError("DEEPSEEK_API_KEY (ou AUDIT_API_KEY) não configurada")
    return OpenAI(api_key=API_KEY, base_url=AUDIT_BASE_URL)


def label_items(items: list[dict], client=None, max_attempts: int = 3) -> list[dict]:
    """Devolve os itens com `label` e `decision`. Repete a chamada se o JSON não validar
    ou se faltar algum idx (o modelo não pode pular item)."""
    if not items:
        return []
    client = client or _make_client()
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": build_prompt(items)},
    ]
    last_err: Exception | None = None
    for attempt in range(max_attempts):
        response = client.chat.completions.create(
            model=AUDIT_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=4096,
            extra_body=AUDIT_EXTRA_BODY,
        )
        text = (response.choices[0].message.content or "").strip()
        try:
            batch = LabelBatch(**json.loads(text))
            by_idx = {x.idx: x for x in batch.items}
            missing = [i for i in range(len(items)) if i not in by_idx]
            if missing:
                raise ValueError(f"faltam idx {missing}")
            return [
                {**it, "label": by_idx[i].label, "decision": by_idx[i].decision.strip()}
                for i, it in enumerate(items)
            ]
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            last_err = e
            logger.warning("Tentativa %d: rótulos inválidos (%s) — pedindo correção.", attempt + 1, type(e).__name__)
            messages.append({"role": "assistant", "content": text})
            messages.append({"role": "user", "content": (
                f"O JSON não validou: {str(e)[:600]}. Devolva o objeto completo, com um item para cada idx "
                f"de 0 a {len(items) - 1} e label em P, T ou C."
            )})
    raise ValueError(f"rotulagem falhou após {max_attempts} tentativas: {last_err}")


# ── Persistência ───────────────────────────────────────────────────────
def labels_path(edition: str) -> str:
    return os.path.join(DEBUG_DIR, f"edition_{edition}_labels.json")


def save_labels(edition: str, labeled: list[dict], source: str) -> str:
    """Grava debug/edition_XXX_labels.json. Sem nome de modelo: o repo é público."""
    os.makedirs(DEBUG_DIR, exist_ok=True)
    payload = {
        "edition": edition,
        "labeled_at": datetime.now(_BRT).isoformat(),
        "source": source,  # "curation" (título + texto) ou "memory" (só título)
        "items": [
            {"field": it["field"], "title": it["title"], "label": it["label"], "decision": it["decision"]}
            for it in labeled
        ],
    }
    path = labels_path(edition)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


# ── Calibração contra a leitura humana ─────────────────────────────────
def calibrate(human: dict[str, list[dict]], labels: dict[str, dict]) -> dict:
    """Concordância entre o juiz e a leitura humana, por título, sem os exemplos do prompt."""
    pairs: list[tuple[str, str, str]] = []  # (title, humano, juiz)
    for edition, rows in human.items():
        judge = {it["title"]: it["label"] for it in (labels.get(edition) or {}).get("items", [])}
        for row in rows:
            if row["title"] in FEWSHOT or row["title"] not in judge:
                continue
            pairs.append((row["title"], row["label"], judge[row["title"]]))
    confusion = {h: {j: 0 for j in LABELS} for h in LABELS}
    for _, h, j in pairs:
        confusion[h][j] += 1
    agree = sum(1 for _, h, j in pairs if h == j)
    return {
        "n": len(pairs),
        "agree": agree,
        "agreement": round(agree / len(pairs), 3) if pairs else None,
        "confusion": confusion,  # linhas = humano, colunas = juiz
        "disagreements": [(t, h, j) for t, h, j in pairs if h != j],
    }


def load_labels_dir() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for f in sorted(glob.glob(os.path.join(DEBUG_DIR, "edition_*_labels.json"))):
        edition = os.path.basename(f).split("_")[1]
        try:
            with open(f, encoding="utf-8") as fh:
                out[edition] = json.load(fh)
        except (json.JSONDecodeError, OSError):
            logger.warning("labels inválido ignorado: %s", f)
    return out


# ── CLI ────────────────────────────────────────────────────────────────
def _curation_editions() -> list[str]:
    return sorted(
        os.path.basename(f).split("_")[1]
        for f in glob.glob(os.path.join(DEBUG_DIR, "edition_*_curation.json"))
    )


def _parse_range(spec: str) -> list[str]:
    a, _, b = spec.partition("-")
    lo, hi = int(a), int(b or a)
    return [f"{n:03d}" for n in range(lo, hi + 1)]


def main():
    p = argparse.ArgumentParser(description="AYA — rótulo de decisão (P/T/C) por item.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--edition", help="Edição a rotular (ex: 247); usa debug/edition_N_curation.json")
    g.add_argument("--all", action="store_true", help="Todas as edições com curation em debug/")
    g.add_argument("--from-memory", metavar="A-B", help="Backfill só com títulos, ex: 234-247")
    g.add_argument("--calibrate", action="store_true", help="Concordância com tests/fixtures/decision_labels_human.json")
    p.add_argument("--skip-existing", action="store_true", help="Pula edições que já têm labels (idempotente)")
    args = p.parse_args()

    if args.calibrate:
        with open(HUMAN_LABELS_PATH, encoding="utf-8") as f:
            human = json.load(f)["labels"]
        r = calibrate(human, load_labels_dir())
        print(f"Itens comparados: {r['n']} (sem os {len(FEWSHOT)} exemplos do prompt)")
        if r["n"]:
            print(f"Concordância: {r['agree']}/{r['n']} = {r['agreement']:.0%}")
            print("Confusão (linhas = humano, colunas = juiz):")
            for h in LABELS:
                print(f"  {h}: " + "  ".join(f"{j}={r['confusion'][h][j]}" for j in LABELS))
            for t, h, j in r["disagreements"]:
                print(f"  ≠ humano={h} juiz={j} | {t}")
        return

    jobs: list[tuple[str, list[dict], str]] = []
    if args.from_memory:
        wanted = set(_parse_range(args.from_memory))
        with open(EDITIONS_PATH, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("edition") in wanted:
                    jobs.append((rec["edition"], items_from_memory(rec), "memory"))
    else:
        editions = [args.edition.zfill(3)] if args.edition else _curation_editions()
        for ed in editions:
            path = os.path.join(DEBUG_DIR, f"edition_{ed}_curation.json")
            if not os.path.exists(path):
                logger.error("curation de #%s não encontrado em debug/ (rode com DEBUG_SAVE=true)", ed)
                continue
            with open(path, encoding="utf-8") as f:
                jobs.append((ed, collect_items(json.load(f)), "curation"))

    client = None
    for ed, items, source in jobs:
        if args.skip_existing and os.path.exists(labels_path(ed)):
            logger.info("#%s já tem labels — pulando", ed)
            continue
        client = client or _make_client()
        try:
            labeled = label_items(items, client=client)
        except Exception as e:  # não-fatal: uma edição ruim não derruba as outras
            logger.error("#%s falhou: %s", ed, e)
            continue
        save_labels(ed, labeled, source)
        counts = {k: sum(1 for x in labeled if x["label"] == k) for k in LABELS}
        logger.info("#%s rotulada (%s): %s", ed, source, counts)


if __name__ == "__main__":
    main()
