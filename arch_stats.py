"""
Métricas de arquitetura do próprio repo — a camada que o dashboard não tinha.

O painel já respondia "a AYA está escrevendo bem?". Não respondia "o código que
escreve a AYA aguenta a próxima mudança?". Este módulo calcula as três coisas
que mudam essa decisão:

  ① dívida técnica e acoplamento — tamanho, complexidade, quem depende de quem,
    e cobertura de testes por módulo;
  ② saúde operacional — histórico de runs do GitHub Actions (opcional: lê um
    snapshot em ci/actions_runs.json, que scripts/fetch_actions_runs.py atualiza);
  ③ performance por fonte — quais das fontes habilitadas realmente entregam, e
    quais o judge aponta como cego recorrente.

Tudo em stdlib. A análise de módulos lê a AST, não importa nada do repo: medir
`pipeline.py` não pode disparar um fetch. A cobertura vem de um coverage.json
já gerado (`pytest --cov --cov-report=json`); sem ele, a coluna fica vazia em
vez de o painel quebrar — mesma tolerância de load_test_runs.

Uso direto:
  python arch_stats.py              # imprime o resumo por módulo
  python arch_stats.py --json       # despeja tudo em JSON
"""

from __future__ import annotations

import argparse
import ast
import json
import os
from collections import Counter, defaultdict

# `real_sources` filtra as chaves `_comment_*` do bloco "sources" — reaproveitado
# em vez de reimplementado porque essa contagem já errou uma vez no README, e
# duas implementações do mesmo filtro é como ela erra de novo.
from scripts.source_stats import load_sources_config, real_sources

ROOT = os.path.dirname(os.path.abspath(__file__))
COVERAGE_PATH = os.path.join(ROOT, "coverage.json")
ACTIONS_RUNS_PATH = os.path.join(ROOT, "ci", "actions_runs.json")

# Pastas que não são código de produção: medir dá número, mas não decisão.
SKIP_DIRS = {".git", "output", "__pycache__", "archive", "blueprint", "brand-assets",
             ".github", "node_modules", ".pytest_cache", ".venv", "venv"}

# ── Limiares ────────────────────────────────────────────────────────────
# Mesma regra que o resto do dashboard segue: um número só ganha cor se o
# limiar significar alguma coisa fora do visual. Cada um aqui tem motivo.

# Complexidade ciclomática de UMA função. 10 é o limite clássico de McCabe
# (acima disso o número de caminhos passa do que se testa à mão); 15 é onde a
# função costuma já precisar ser quebrada pra ser entendida.
FN_CC_WARN = 10
FN_CC_BAD = 15

# Cobertura por módulo. 0% é o caso binário — ninguém nunca executou aquele
# código num teste. 50% é o ponto onde metade dos caminhos é desconhecida.
COV_BAD = 0
COV_WARN = 50

# Instabilidade de Martin: fan_out / (fan_in + fan_out). Perto de 1 o módulo
# depende de muita coisa e quebra quando qualquer uma muda; perto de 0 muita
# coisa depende dele e mudá-lo é caro. O risco real é o canto onde ambos são
# altos — por isso o índice de risco abaixo usa fan_in, não a instabilidade.
INSTABILITY_FRAGILE = 0.8

# Taxa de sucesso de um workflow. Abaixo disso o vermelho deixa de ser evento e
# passa a ser estado — e um check que vive vermelho para de informar.
WORKFLOW_OK_PCT = 90

# Fonte habilitada que o judge aponta como false negative mais vezes do que
# entregou itens está sendo sistematicamente subestimada, não só azarada.
FN_PER_ITEM_BAD = 5.0


# ════════════════════════════════════════════════════════════════════════
# ① Dívida técnica e acoplamento
# ════════════════════════════════════════════════════════════════════════

def _iter_py_files(root: str) -> dict[str, str]:
    """Caminhos relativos → absolutos dos .py de produção e de teste."""
    found = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                full = os.path.join(dirpath, fn)
                found[os.path.relpath(full, root)] = full
    return found


def _module_name(rel_path: str) -> str:
    """sources/base.py → sources.base; sources/__init__.py → sources."""
    name = rel_path[:-3].replace(os.sep, ".")
    return name[: -len(".__init__")] if name.endswith(".__init__") else name


def _cyclomatic(node: ast.AST) -> int:
    """CC aproximada: 1 + um ponto por cada desvio de fluxo.

    Não é a métrica de McCabe ao pé da letra (que conta arestas do grafo de
    fluxo), mas ordena funções do mesmo jeito e não precisa de dependência.
    """
    cc = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While,
                              ast.ExceptHandler, ast.IfExp, ast.Assert,
                              ast.comprehension)):
            cc += 1
        elif isinstance(child, ast.BoolOp):
            cc += len(child.values) - 1
    return cc


def _nesting_depth(node: ast.AST, depth: int = 0) -> int:
    deepest = depth
    for child in ast.iter_child_nodes(node):
        step = 1 if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While,
                                       ast.Try, ast.With, ast.AsyncWith)) else 0
        deepest = max(deepest, _nesting_depth(child, depth + step))
    return deepest


def _imports(tree: ast.AST, own_name: str, local_tops: set[str]) -> tuple[set[str], set[str]]:
    """Separa imports locais (módulos do repo) dos externos."""
    local, external = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                (local if top in local_tops else external).add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # import relativo: resolve contra o pacote do próprio módulo
                base = own_name.rsplit(".", 1)[0] if "." in own_name else own_name
                local.add(f"{base}.{node.module}" if node.module else base)
            elif node.module:
                top = node.module.split(".")[0]
                (local if top in local_tops else external).add(node.module)
    return local, external


def analyze_modules(root: str = ROOT) -> dict[str, dict]:
    """Uma entrada por módulo: tamanho, complexidade, acoplamento, hotspots."""
    files = _iter_py_files(root)
    names = {_module_name(rel) for rel in files}
    local_tops = {n.split(".")[0] for n in names}

    modules: dict[str, dict] = {}
    edges: Counter = Counter()

    for rel, full in sorted(files.items()):
        name = _module_name(rel)
        try:
            with open(full, encoding="utf-8") as f:
                src = f.read()
            tree = ast.parse(src)
        except (OSError, SyntaxError):
            continue

        lines = src.split("\n")
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", node.lineno)
                functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "loc": end - node.lineno + 1,
                    "cc": _cyclomatic(node),
                    "nesting": _nesting_depth(node),
                })

        local, external = _imports(tree, name, local_tops)
        resolved = set()
        for imp in local:
            if imp in names:
                resolved.add(imp)
            else:
                # `from sources import X` quando sources é pacote
                candidates = sorted(n for n in names if n == imp or n.startswith(imp + "."))
                if candidates:
                    resolved.add(candidates[0])
        for target in resolved:
            if target != name:
                edges[(name, target)] += 1

        modules[name] = {
            "path": rel,
            "loc": len(lines),
            "code_loc": sum(1 for l in lines if l.strip() and not l.strip().startswith("#")),
            "n_functions": len(functions),
            "sum_cc": sum(f["cc"] for f in functions),
            "max_cc": max((f["cc"] for f in functions), default=0),
            "max_nesting": max((f["nesting"] for f in functions), default=0),
            "longest_fn": max(functions, key=lambda f: f["loc"])["name"] if functions else None,
            "longest_fn_loc": max((f["loc"] for f in functions), default=0),
            "hotspots": sorted((f for f in functions if f["cc"] >= FN_CC_WARN),
                               key=lambda f: -f["cc"])[:8],
            "imports_external": sorted(external),
            "is_test": rel.startswith("tests" + os.sep),
            "is_script": rel.startswith("scripts" + os.sep),
        }

    for name, mod in modules.items():
        mod["imports"] = sorted({t for (f, t) in edges if f == name})
        mod["imported_by"] = sorted({f for (f, t) in edges if t == name})
        mod["fan_out"] = len(mod["imports"])
        mod["fan_in"] = len(mod["imported_by"])
        total = mod["fan_in"] + mod["fan_out"]
        mod["instability"] = round(mod["fan_out"] / total, 2) if total else 0.0

    return modules


def load_coverage(path: str = COVERAGE_PATH) -> dict[str, float]:
    """Caminho do arquivo → % coberto, lido de um coverage.json do pytest-cov.

    Ausente (ninguém rodou com --cov) devolve {} e o painel mostra "—" na
    coluna, em vez de quebrar.
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    out = {}
    for fname, entry in (data.get("files") or {}).items():
        summary = entry.get("summary") or {}
        if "percent_covered" in summary:
            out[os.path.normpath(fname)] = round(summary["percent_covered"], 1)
    return out


def module_risk(mod: dict, coverage_pct: float | None) -> float:
    """Ordem de atenção, não nota.

    Exposição = tamanho × complexidade × quantos dependem do módulo. Multiplica
    pela fração NÃO coberta: um módulo grande e complexo mas testado não é a
    primeira coisa a mexer; o mesmo módulo sem teste é. Sem dado de cobertura
    assume o pior (1.0), porque desconhecido não é o mesmo que seguro.
    """
    exposure = (mod["loc"] / 100) * (1 + mod["sum_cc"] / 50) * (1 + mod["fan_in"] / 5)
    uncovered = 1.0 if coverage_pct is None else max(0.0, (100 - coverage_pct) / 100)
    return round(exposure * uncovered, 2)


def aggregate_architecture(root: str = ROOT, coverage_path: str = COVERAGE_PATH) -> dict:
    """Junta módulos + cobertura + risco, já ordenado por onde olhar primeiro."""
    modules = analyze_modules(root)
    coverage = load_coverage(coverage_path)

    rows = []
    for name, mod in modules.items():
        if mod["is_test"]:
            continue
        pct = coverage.get(os.path.normpath(mod["path"]))
        rows.append({**mod, "module": name, "coverage_pct": pct,
                     "risk": module_risk(mod, pct)})
    rows.sort(key=lambda r: -r["risk"])

    core = [r for r in rows if not r["is_script"]]
    tested = [r for r in core if r["coverage_pct"] is not None]
    return {
        "modules": rows,
        "core": core,
        "n_modules": len(core),
        "total_loc": sum(r["loc"] for r in core),
        "total_cc": sum(r["sum_cc"] for r in core),
        "n_tests_files": sum(1 for m in modules.values() if m["is_test"]),
        "no_coverage": [r["module"] for r in core
                        if r["coverage_pct"] is not None and r["coverage_pct"] <= COV_BAD],
        "has_coverage_data": bool(coverage),
        "avg_coverage": (round(sum(r["coverage_pct"] for r in tested) / len(tested), 1)
                         if tested else None),
        "fragile": [r["module"] for r in core
                    if r["instability"] >= INSTABILITY_FRAGILE and r["fan_out"] >= 3],
        "edges": sorted((r["module"], t) for r in core for t in r["imports"]),
    }


# ════════════════════════════════════════════════════════════════════════
# ② Saúde operacional (GitHub Actions)
# ════════════════════════════════════════════════════════════════════════

def load_actions_runs(path: str = ACTIONS_RUNS_PATH) -> list[dict]:
    """Snapshot dos runs do Actions, gravado por scripts/fetch_actions_runs.py.

    O dashboard roda offline, então não chama a API: lê o snapshot se existir.
    Sem ele a seção diz como gerar, em vez de ficar vazia sem explicação.
    """
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []
    runs = data.get("runs") if isinstance(data, dict) else data
    return runs if isinstance(runs, list) else []


def aggregate_workflows(runs: list[dict], own_only: bool = True) -> dict:
    """Por workflow: runs, taxa de sucesso, falhas, duração e sequência atual.

    `own_only` descarta os workflows que o GitHub roda por conta própria
    (pages-build-deployment, dependabot). Eles respondem por um terço dos runs e
    não são decisão sua — deixá-los dentro faz a média parecer melhor do que a
    saúde dos workflows que você escreveu.
    """
    if own_only:
        runs = [r for r in runs if str(r.get("path") or "").startswith(".github/workflows/")]
    if not runs:
        return {"workflows": [], "n_runs": 0, "range": None}

    by_path: dict[str, list[dict]] = defaultdict(list)
    for r in runs:
        by_path[r.get("path") or r.get("name") or "?"].append(r)

    out = []
    for path, group in by_path.items():
        group.sort(key=lambda r: r.get("created_at") or "")
        decided = [r for r in group if r.get("conclusion") in ("success", "failure")]
        ok = sum(1 for r in decided if r["conclusion"] == "success")
        durations = sorted(d for d in (r.get("duration_s") for r in group)
                           if isinstance(d, (int, float)))

        streak, streak_kind = 0, None
        for r in reversed(decided):
            if streak_kind is None:
                streak_kind = r["conclusion"]
            if r["conclusion"] == streak_kind:
                streak += 1
            else:
                break

        out.append({
            "path": path,
            "name": group[-1].get("name") or path.rsplit("/", 1)[-1],
            "n": len(group),
            "success_pct": round(100 * ok / len(decided), 1) if decided else None,
            "n_failures": sum(1 for r in decided if r["conclusion"] == "failure"),
            "median_s": durations[len(durations) // 2] if durations else None,
            "p90_s": durations[int(len(durations) * 0.9)] if durations else None,
            "last_conclusion": group[-1].get("conclusion"),
            "last_run": (group[-1].get("created_at") or "")[:10],
            "streak": streak,
            "streak_kind": streak_kind,
            "failures": [{"date": (r.get("created_at") or "")[:10],
                          "title": r.get("display_title"),
                          "sha": (r.get("head_sha") or "")[:7]}
                         for r in decided if r["conclusion"] == "failure"][-8:],
        })
    out.sort(key=lambda w: -w["n"])
    dates = sorted((r.get("created_at") or "")[:10] for r in runs if r.get("created_at"))
    return {"workflows": out, "n_runs": len(runs),
            "range": (dates[0], dates[-1]) if dates else None}


# ════════════════════════════════════════════════════════════════════════
# ③ Performance por fonte
# ════════════════════════════════════════════════════════════════════════

def _normalize(name: str) -> str:
    return "".join(c for c in str(name).lower() if c.isalnum())


def source_performance(editions: list[dict], audits: dict[str, dict],
                       sources_config: dict | None = None) -> list[dict]:
    """Por fonte habilitada: contribuição real contra cegueira do judge.

    Duas janelas, de propósito separadas: `sources_used` existe em praticamente
    toda edição e diz quais fontes contribuíram; o campo `source` por item só
    passou a ser gravado na edição 198. Misturar as duas faria uma fonte antiga
    parecer improdutiva só porque a instrumentação é nova.
    """
    real = real_sources(sources_config if sources_config is not None
                        else load_sources_config())

    used = Counter()
    n_with_used = 0
    main_hits, quick_hits = Counter(), Counter()
    item_editions: dict[str, set] = defaultdict(set)

    for ed in editions:
        if ed.get("sources_used"):
            n_with_used += 1
            for s in ed["sources_used"]:
                used[str(s).strip().lower()] += 1

        main = (ed.get("main_find") or {}).get("source", "")
        if main:
            key = str(main).strip().lower()
            main_hits[key] += 1
            item_editions[key].add(ed.get("edition"))
        for item in ed.get("quick_finds") or []:
            s = (item or {}).get("source", "")
            if s:
                key = str(s).strip().lower()
                quick_hits[key] += 1
                item_editions[key].add(ed.get("edition"))

    # o judge escreve o nome bonito da fonte ("SCMP Tech"), não o id da config
    alias = {_normalize(k): k for k in real}
    fn_by_id = Counter()
    for audit in audits.values():
        for fn in audit.get("false_negatives") or []:
            raw = fn.get("source") or ""
            norm = _normalize(raw)
            key = alias.get(norm)
            if key is None and norm.startswith("r") and "reddit" in alias:
                key = "reddit"            # r/artificial, r/LocalLLaMA…
            if key is None:
                key = next((v for k, v in alias.items() if k and (k in norm or norm in k)), None)
            if key:
                fn_by_id[key] += 1

    rows = []
    for sid, conf in real.items():
        items = main_hits[sid] + quick_hits[sid]
        fn = fn_by_id[sid]
        rows.append({
            "source": sid,
            "enabled": bool(conf.get("enabled", True)),
            "weight": conf.get("weight"),
            "used_count": used[sid],
            "used_pct": round(100 * used[sid] / n_with_used, 1) if n_with_used else 0.0,
            "main_find": main_hits[sid],
            "quick_finds": quick_hits[sid],
            "items": items,
            "false_negatives": fn,
            "fn_per_item": round(fn / items, 1) if items else None,
            "item_window_editions": len(item_editions[sid]),
            "idle": used[sid] == 0,
        })
    rows.sort(key=lambda r: (-r["used_count"], -r["items"]))

    item_window = sum(1 for ed in editions
                      if (ed.get("main_find") or {}).get("source")
                      or any((i or {}).get("source") for i in ed.get("quick_finds") or []))
    for r in rows:
        r["_n_with_used"] = n_with_used
        r["_n_item_window"] = item_window
    return rows


# ════════════════════════════════════════════════════════════════════════

def main() -> None:
    p = argparse.ArgumentParser(description="Métricas de arquitetura do repo.")
    p.add_argument("--json", action="store_true", help="Despeja tudo em JSON")
    p.add_argument("--coverage", default=COVERAGE_PATH, help="Caminho do coverage.json")
    args = p.parse_args()

    arch = aggregate_architecture(coverage_path=args.coverage)
    runs = aggregate_workflows(load_actions_runs())

    if args.json:
        print(json.dumps({"architecture": arch, "workflows": runs},
                         ensure_ascii=False, indent=2, default=str))
        return

    print(f"{arch['n_modules']} módulos de produção · {arch['total_loc']} LOC · "
          f"complexidade {arch['total_cc']}")
    if arch["has_coverage_data"]:
        print(f"cobertura média por módulo: {arch['avg_coverage']}% · "
              f"{len(arch['no_coverage'])} em 0%")
    else:
        print("sem coverage.json — rode: pytest --cov=. --cov-report=json")
    print()
    print(f"{'módulo':26} {'LOC':>5} {'CC':>5} {'dep':>4} {'imp':>4} {'inst':>5} "
          f"{'cob':>6} {'risco':>6}")
    for r in arch["core"]:
        cov = "—" if r["coverage_pct"] is None else f"{r['coverage_pct']:.0f}%"
        print(f"{r['module']:26} {r['loc']:5} {r['sum_cc']:5} {r['fan_in']:4} "
              f"{r['fan_out']:4} {r['instability']:5} {cov:>6} {r['risk']:6}")

    if runs["workflows"]:
        print()
        print(f"{runs['n_runs']} runs de Actions · {runs['range'][0]} → {runs['range'][1]}")
        for w in runs["workflows"]:
            print(f"  {w['name'][:34]:34} {w['n']:4} runs  "
                  f"{w['success_pct']}% ok  {w['streak']}×{w['streak_kind']}")
    else:
        print("\nsem ci/actions_runs.json — rode: python scripts/fetch_actions_runs.py")


if __name__ == "__main__":
    main()
