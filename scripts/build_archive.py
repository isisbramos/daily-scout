"""Gera archive/editions.json com todas as edições publicadas da AYA.

Fonte: arquivo público do Buttondown (https://buttondown.com/ramosdisis/archive/),
sem API key. Lê as páginas de listagem para descobrir as edições e abre a página
de cada edição só quando ela ainda não está no JSON (incremental).

Uso:
    python scripts/build_archive.py            # incremental
    python scripts/build_archive.py --full     # reabre todas as edições

O site (index.html e archive/index.html) lê o JSON gerado.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://buttondown.com/ramosdisis/archive/"
OUT = Path(__file__).resolve().parent.parent / "archive" / "editions.json"
UA = "Mozilla/5.0 (AYA archive builder; +https://assineaya.com.br)"
MONTHS = {
    "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4, "maio": 5,
    "junho": 6, "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10,
    "novembro": 11, "dezembro": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
}
EXCERPT_MAX = 240


def fetch(url: str, retries: int = 3) -> str:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001 — rede instável, tenta de novo
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"falha ao buscar {url}: {last}")


def to_text(raw: str) -> str:
    t = re.sub(r"<(script|style)\b.*?</\1>", "", raw, flags=re.S | re.I)
    t = re.sub(r"<br\s*/?>|</p>|</div>|</h\d>|</li>|</tr>|</td>", "\n", t, flags=re.I)
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    t = re.sub(r"[ \t ]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t)


def split_title(full: str) -> tuple[int | None, str]:
    full = html.unescape(full).strip()
    m = re.match(r"^(?:AYA|Daily Scout)\s*#(\d+)\s*[—–-]\s*(.+)$", full)
    if m:
        return int(m.group(1)), m.group(2).strip()
    m = re.search(r"#(\d+)", full)
    return (int(m.group(1)) if m else None), full


def list_page(page: int) -> list[dict]:
    raw = fetch(f"{BASE}?page={page}")
    out = []
    for block in re.findall(r'<a href="([^"]+)" class="email-link">(.*?)</a>', raw, flags=re.S):
        url, body = block
        title_m = re.search(r'class="email-title">(.*?)</div>', body, flags=re.S)
        date_m = re.search(r'class="email-metadata">(.*?)</div>', body, flags=re.S)
        if not title_m:
            continue
        num, title = split_title(title_m.group(1))
        out.append({
            "num": num,
            "title": title,
            "url": url,
            "date": parse_list_date(to_text(date_m.group(1)) if date_m else ""),
        })
    return out


def parse_list_date(s: str) -> str | None:
    m = re.search(r"([A-Za-zçÇ]+)\s+(\d{1,2}),\s*(\d{4})", s)
    if not m:
        return None
    month = MONTHS.get(m.group(1).lower())
    if not month:
        return None
    return f"{int(m.group(3)):04d}-{month:02d}-{int(m.group(2)):02d}"


def first_sentences(text: str, limit: int = EXCERPT_MAX) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    if end > 80:
        return cut[: end + 1]
    return cut[: cut.rfind(" ")].rstrip(",;:") + "…"


def edition_details(url: str) -> dict:
    text = to_text(fetch(url))
    det: dict = {}
    m = re.search(r"field report #\d+\s*\n\s*(\d{2})/(\d{2})/(\d{4})", text)
    if m:
        det["date"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    m = re.search(r"> ACHADO DO DIA\s*\n(.*?)\n\s*src:\s*(.*?)\n(.*?)(?:\n\s*->|\n\s*- - -|\n\s*> )", text, flags=re.S)
    if m:
        det["main_title"] = m.group(1).strip()
        det["source"] = m.group(2).strip()
        body = re.sub(r"\s+", " ", m.group(3)).strip()
        work = re.search(r"→ No seu (?:trabalho|produto):\s*(.+)$", body)
        if work:
            det["work_line"] = first_sentences(work.group(1), 200)
            body = body[: work.start()].strip()
        det["excerpt"] = first_sentences(body)
    return det


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="reabre todas as edições")
    ap.add_argument("--max-pages", type=int, default=60)
    args = ap.parse_args()

    existing = {}
    if OUT.exists() and not args.full:
        for e in json.loads(OUT.read_text(encoding="utf-8")).get("editions", []):
            existing[e["url"]] = e

    found: list[dict] = []
    seen: set[str] = set()
    for page in range(1, args.max_pages + 1):
        items = [i for i in list_page(page) if i["url"] not in seen]
        if not items:
            break
        for i in items:
            seen.add(i["url"])
        found.extend(items)
        # incremental: para quando a página inteira já estava no JSON
        if existing and all(i["url"] in existing for i in items):
            break

    merged = dict(existing)
    new = 0
    for item in found:
        if item["url"] in merged and merged[item["url"]].get("excerpt"):
            continue
        try:
            det = edition_details(item["url"])
        except RuntimeError as exc:
            print(f"aviso: {exc}", file=sys.stderr)
            det = {}
        entry = {**item, **{k: v for k, v in det.items() if v}}
        entry.setdefault("excerpt", "")
        merged[item["url"]] = entry
        new += 1
        time.sleep(0.3)

    editions = sorted(
        merged.values(),
        key=lambda e: (e.get("num") or 0, e.get("date") or ""),
        reverse=True,
    )
    payload = {"source": BASE, "count": len(editions), "editions": editions}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(editions)} edições ({new} novas/atualizadas) → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
