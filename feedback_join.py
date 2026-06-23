"""
Daily Scout — Feedback Joiner v1.0

Junta os ratings coletados no Google Sheet (loop de feedback 🔥/👍/😐) de volta
ao `memory/editions.jsonl`, preenchendo o campo `feedback_score` que nasce `None`
no envio. Sem isso, a correlação feedback × conteúdo do content_report.py fica sem
combustível.

Fluxo do feedback (contexto):
  footer do email → Apps Script (apps-script/Code.gs) → linha no Sheet
  colunas: [timestamp ISO, edition (int), rating, referrer]
  ratings válidos: fire / solid / meh

Este script agrega os ratings por edição e grava em cada registro do editions.jsonl:
  "feedback_score": {"fire": 3, "solid": 1, "meh": 0, "n": 4, "avg": 1.75}
  (avg na escala fire=2 / solid=1 / meh=0 — quanto maior, melhor recepção)

Fontes de dado (escolha uma):
  --csv-url URL     CSV export da planilha (precisa de "qualquer um com link pode ver")
  --csv-file PATH   CSV baixado manualmente
  env FEEDBACK_CSV_URL  usado como default se nenhum for passado

Uso:
  python feedback_join.py --csv-file feedback.csv
  python feedback_join.py --csv-url "https://docs.google.com/.../export?format=csv"
  python feedback_join.py --csv-file feedback.csv --dry-run   # mostra sem gravar

O SHEET_ID está em apps-script/Code.gs. A URL de export pública tem a forma:
  https://docs.google.com/spreadsheets/d/<SHEET_ID>/gviz/tq?tqx=out:csv&sheet=feedback
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import os
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("feedback-join")

ROOT = os.path.dirname(os.path.abspath(__file__))
EDITIONS_PATH = os.path.join(ROOT, "memory", "editions.jsonl")

# Planilha do loop de feedback (mesma de apps-script/Code.gs). A URL gviz exporta a
# aba por nome como CSV — requer a planilha em "qualquer um com o link pode ver".
SHEET_ID = "1ToD2eW-owhGsdE0cswVHNGiX8yHJH87Mdtviz-l6kuM"
SHEET_NAME = "feedback"
DEFAULT_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
)

# Mesma escala usada pelo content_report. fire melhor, meh pior.
RATING_VALUE = {"fire": 2, "solid": 1, "meh": 0}
# Cabeçalhos possíveis (a planilha pode ou não ter header; o Apps Script só dá appendRow).
HEADER_HINTS = {"timestamp", "edition", "rating", "referrer", "date"}


# ── Leitura do CSV ─────────────────────────────────────────────────────
def fetch_csv(csv_url: str | None, csv_file: str | None) -> str:
    """Retorna o conteúdo CSV cru (string), de URL ou arquivo local."""
    if csv_file:
        with open(csv_file, encoding="utf-8") as f:
            return f.read()
    if csv_url:
        import urllib.error
        import urllib.request

        logger.info("Baixando CSV da planilha…")
        try:
            with urllib.request.urlopen(csv_url, timeout=30) as resp:  # noqa: S310 — URL controlada pela usuária
                body = resp.read().decode("utf-8")
            # Planilha privada às vezes responde 200 com a página de login (HTML), não CSV.
            if body.lstrip().lower().startswith(("<!doctype", "<html")):
                raise SystemExit(
                    "A planilha respondeu com HTML (página de login), não CSV — ou seja, não está pública.\n"
                    "→ No Google Sheets: Compartilhar → 'Qualquer pessoa com o link' → Leitor.\n"
                    "  Alternativa sem liberar o link: baixe a aba como CSV e use --csv-file."
                )
            return body
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise SystemExit(
                    "Planilha não está acessível por link (HTTP %d).\n"
                    "→ No Google Sheets: Compartilhar → 'Qualquer pessoa com o link' → Leitor.\n"
                    "  (Os dados são ratings anônimos: timestamp, edição, nota, referrer.)\n"
                    "  Alternativa sem liberar o link: baixe a aba como CSV e use --csv-file." % e.code
                )
            raise SystemExit(f"Falha ao baixar a planilha (HTTP {e.code}: {e.reason}).")
        except urllib.error.URLError as e:
            raise SystemExit(f"Falha de rede ao baixar a planilha: {e.reason}.")
    raise ValueError("Forneça --csv-file, --csv-url, ou a env FEEDBACK_CSV_URL.")


def parse_rows(raw: str) -> list[dict]:
    """Parseia o CSV em [{edition:int, rating:str}], tolerante a header/sem header
    e à ordem das colunas. Ignora linhas sem edição ou rating inválido."""
    reader = csv.reader(io.StringIO(raw))
    rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return []

    # Detecta header: primeira linha tem palavras conhecidas e nenhuma edição numérica?
    first = [c.strip().lower() for c in rows[0]]
    has_header = any(h in HEADER_HINTS for h in first)
    col = {"edition": None, "rating": None}
    if has_header:
        for i, name in enumerate(first):
            if name == "edition":
                col["edition"] = i
            elif name == "rating":
                col["rating"] = i
        data_rows = rows[1:]
    else:
        data_rows = rows

    out: list[dict] = []
    for r in data_rows:
        # Sem header confiável: assume layout do Apps Script [ts, edition, rating, referrer].
        try:
            if col["edition"] is not None and col["rating"] is not None:
                ed_raw, rating = r[col["edition"]], r[col["rating"]]
            else:
                ed_raw, rating = r[1], r[2]
        except IndexError:
            continue
        rating = rating.strip().lower()
        if rating not in RATING_VALUE:
            continue
        digits = "".join(ch for ch in str(ed_raw) if ch.isdigit())
        if not digits:
            continue
        out.append({"edition": int(digits), "rating": rating})
    return out


# ── Agregação por edição ───────────────────────────────────────────────
def aggregate(rows: list[dict]) -> dict[int, dict]:
    """edição(int) → {fire, solid, meh, n, avg}."""
    buckets: dict[int, list[str]] = defaultdict(list)
    for r in rows:
        buckets[r["edition"]].append(r["rating"])

    scores: dict[int, dict] = {}
    for ed, ratings in buckets.items():
        counts = {k: ratings.count(k) for k in RATING_VALUE}
        n = len(ratings)
        avg = round(sum(RATING_VALUE[r] for r in ratings) / n, 2) if n else None
        scores[ed] = {**counts, "n": n, "avg": avg}
    return scores


# ── Patch do editions.jsonl ────────────────────────────────────────────
def load_editions(path: str) -> list[dict]:
    records: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("linha inválida ignorada em %s", path)
    return records


def write_editions(path: str, records: list[dict]) -> None:
    """Reescreve o jsonl de forma atômica (temp + rename) — nunca deixa o arquivo
    pela metade se algo falhar no meio."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def join(records: list[dict], scores: dict[int, dict]) -> tuple[int, int]:
    """Aplica os scores nos registros (match por edição como int). Retorna
    (n_atualizados, n_sem_match_no_sheet)."""
    updated = 0
    for r in records:
        ed_raw = str(r.get("edition", ""))
        digits = "".join(ch for ch in ed_raw if ch.isdigit())
        if not digits:
            continue
        ed = int(digits)
        if ed in scores:
            new = scores[ed]
            if r.get("feedback_score") != new:
                r["feedback_score"] = new
                updated += 1
    # ratings no Sheet sem edição correspondente no jsonl (edições antigas/fora da memória)
    jsonl_eds = {
        int("".join(ch for ch in str(r.get("edition", "")) if ch.isdigit()) or -1)
        for r in records
    }
    orphans = sum(1 for ed in scores if ed not in jsonl_eds)
    return updated, orphans


# ── Main ───────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="Junta ratings do Google Sheet no editions.jsonl.")
    p.add_argument("--csv-url", default=os.environ.get("FEEDBACK_CSV_URL") or DEFAULT_CSV_URL,
                   help="URL de export CSV da planilha (default: env FEEDBACK_CSV_URL ou a URL gviz do SHEET_ID)")
    p.add_argument("--csv-file", help="Caminho de um CSV baixado manualmente")
    p.add_argument("--editions-file", default=EDITIONS_PATH,
                   help="Caminho do editions.jsonl (default: memory/editions.jsonl)")
    p.add_argument("--dry-run", action="store_true", help="Mostra o que mudaria sem gravar")
    args = p.parse_args()

    raw = fetch_csv(args.csv_url, args.csv_file)
    rows = parse_rows(raw)
    if not rows:
        logger.error("Nenhum rating válido encontrado no CSV.")
        raise SystemExit(1)
    scores = aggregate(rows)
    logger.info("%d ratings em %d edições no Sheet.", len(rows), len(scores))

    if not os.path.exists(args.editions_file):
        logger.error("editions.jsonl não encontrado: %s", args.editions_file)
        logger.error("Ele só existe depois que o pipeline roda em prod (ou use um fixture).")
        raise SystemExit(1)

    records = load_editions(args.editions_file)
    updated, orphans = join(records, scores)

    # Resumo legível
    print(f"\n{'='*52}")
    print("FEEDBACK JOIN")
    print(f"{'='*52}")
    for ed in sorted(scores):
        s = scores[ed]
        mark = "✓" if any(
            int("".join(c for c in str(r.get('edition','')) if c.isdigit()) or -1) == ed
            for r in records
        ) else "· (sem match no jsonl)"
        print(f"  ed.{ed:>3}  🔥{s['fire']} 👍{s['solid']} 😐{s['meh']}  "
              f"avg={s['avg']}  n={s['n']}  {mark}")
    print(f"\n{updated} edição(ões) atualizada(s); {orphans} sem match no jsonl.")
    print(f"{'='*52}\n")

    if args.dry_run:
        logger.info("[dry-run] nada gravado.")
        return
    if updated:
        write_editions(args.editions_file, records)
        logger.info("editions.jsonl atualizado: %s", args.editions_file)
    else:
        logger.info("Nada a atualizar (já estava em dia).")


if __name__ == "__main__":
    main()
