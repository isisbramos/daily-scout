"""
Dry run: testa fetch multi-source + pre-filter + render do template (sem LLM, sem Buttondown).
Valida que a nova arquitetura plugável funciona end-to-end.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from jinja2 import Environment, FileSystemLoader

# Add project root
sys.path.insert(0, os.path.dirname(__file__))
from pipeline import load_config, fetch_all_sources, filter_items
from sources.base import SourceRegistry

BRT = timezone(timedelta(hours=-3))


def test_config():
    """Test config loading."""
    print("=" * 50)
    print("TEST 0: Load Config")
    print("=" * 50)

    config = load_config()
    sources = config.get("sources", {})
    enabled = [sid for sid, conf in sources.items() if isinstance(conf, dict) and conf.get("enabled", True)]
    print(f"  Config loaded: {len(sources)} sources defined, {len(enabled)} enabled")
    print(f"  Enabled: {enabled}")
    print(f"  Available in registry: {SourceRegistry.available_sources()}")
    print()
    return config


def test_fetch(config):
    """Test multi-source fetching."""
    print("=" * 50)
    print("TEST 1: Fetch Sources (Multi-Source)")
    print("=" * 50)

    items = fetch_all_sources(config)
    print(f"\nTotal raw items fetched: {len(items)}")

    # Source distribution
    dist = {}
    for item in items:
        dist[item.source_id] = dist.get(item.source_id, 0) + 1
    print("Source distribution:")
    for sid, count in sorted(dist.items()):
        print(f"  {sid}: {count}")

    if items:
        print(f"\nTop 5 by raw_score:")
        sorted_items = sorted(items, key=lambda x: x.raw_score, reverse=True)
        for i, item in enumerate(sorted_items[:5]):
            print(f"  [{i+1}] {item.title[:70]}...")
            print(f"      src: {item.source_label} | score: {item.raw_score} | cat: {item.category}")
            print()

    return items


def test_pre_filter(items, config):
    """Test pre-filter pipeline."""
    print("=" * 50)
    print("TEST 2: Pre-Filter Pipeline")
    print("=" * 50)

    filtered = filter_items(items, config)
    print(f"\nFiltered: {len(items)} → {len(filtered)} items")

    # Source distribution after filter
    dist = {}
    for item in filtered:
        dist[item.source_id] = dist.get(item.source_id, 0) + 1
    print("Filtered distribution:")
    for sid, count in sorted(dist.items()):
        print(f"  {sid}: {count}")

    return filtered


def test_render():
    """Test HTML rendering with multi-source mock data."""
    print("=" * 50)
    print("TEST 3: Render HTML Template")
    print("=" * 50)

    mock_content = {
        "correspondent_intro": "Hoje o destaque vai pra aquisição da PayAI pela Stripe por US$ 200 milhões — consolidação no mercado de fintech com IA. Analisei 142 posts de 4 fontes.",
        "main_find": {
            "title": "Stripe adquire startup de pagamentos com IA por US$ 200 milhões",
            "source": "TechCrunch",
            "body": "Segundo o TechCrunch, a Stripe fechou a aquisição da PayAI, startup que usava LLMs pra detectar fraude em tempo real. A aquisição confirma que pagamentos + IA viraram a nova arena de disputa — e que as grandes fintechs estão comprando em vez de construir. Valor sinaliza que detecção de fraude com LLM já é diferencial competitivo mensurável. → Quem constrói fintech em cima de arquiteturas de código aberto tem agora uma referência de aquisição pra calibrar avaliação de mercado e rota de saída.",
            "bullets": [
                "Por que importa: sinaliza consolidação no mercado de fintech com IA",
                "Impacto: startups do setor vão ter rota de saída mais clara, mas a concorrência fica mais dura",
                "O que observar: se a Stripe integra no Radar (detecção de fraude) ou cria produto novo",
            ],
            "url": "https://techcrunch.com/2026/03/24/stripe-acquires-payai",
            "display_url": "techcrunch.com/stripe-acquires-payai",
        },
        "quick_finds": [
            {
                "title": "Benchmarks vazados do Llama 4 mostram salto em geração de código",
                "source": "r/LocalLLaMA",
                "signal": "Benchmarks vazados apontam que o Llama 4 superou o GPT-4 Turbo em HumanEval e MBPP. Se confirmado, o código aberto fecha a distância para os modelos de ponta em geração de código. → Desenvolvedores que pagam por API de geração de código podem rodar provas de conceito com Llama 4 local antes de renovar contratos anuais.",
                "url": "https://reddit.com/r/LocalLLaMA/comments/123",
                "display_url": "r/LocalLLaMA",
            },
            {
                "title": "Show HN: interpretador Python que roda 100% no navegador via WASM",
                "source": "HackerNews",
                "signal": "Projeto de código aberto compila o CPython pra WebAssembly e roda sem backend. Ferramentas de desenvolvimento cada vez mais sem instalação — bom pra educação e prototipagem. → Times que mantêm sandbox pra onboarding ou tutoriais podem eliminar a infraestrutura de execução remota.",
                "url": "https://news.ycombinator.com/item?id=456",
                "display_url": "news.ycombinator.com",
            },
            {
                "title": "Thread: por que SQLite está substituindo Redis em 80% dos casos de uso",
                "source": "Lobsters",
                "signal": "Análise mostra que o SQLite com WAL sustenta vazão similar ao Redis pra cache e armazenamento de sessão, sem cluster. Simplificação de arquitetura é tendência forte — menos componentes móveis significa menos custo operacional. → Quem roda Redis só como cache compartilhado pode reavaliar se vale manter outra peça na infraestrutura.",
                "url": "https://lobste.rs/s/abc123",
                "display_url": "lobste.rs",
            },
        ],
        "meta": {
            "total_analyzed": 142,
            "sources_used": ["reddit", "hackernews", "techcrunch", "lobsters"],
            "editorial_note": "Dia movimentado — fintech e ferramentas de desenvolvimento dominaram o campo.",
        },
    }

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("email.html")

    now = datetime.now(BRT)
    active_sources = ["reddit", "hackernews", "techcrunch", "lobsters"]
    sources_detail = " + ".join(s.replace("_", " ").title() for s in active_sources)

    html = template.render(
        edition_number="003",
        date=now.strftime("%d/%m/%Y"),
        correspondent_intro=mock_content["correspondent_intro"],
        sources_count=142,
        finds_count=4,
        num_sources=len(active_sources),
        main_find=mock_content["main_find"],
        quick_finds=mock_content["quick_finds"],
        sources_detail=sources_detail,
        active_sources=active_sources,
        posts_analyzed=142,
        signal_ratio="4/142",
        runtime="12.3s",
        feedback_base_url="https://example.github.io/daily-scout/feedback.html",
        aya_avatar_url="https://raw.githubusercontent.com/isisbramos/daily-scout/main/aya-avatar.png",
    )

    os.makedirs("output", exist_ok=True)
    output_path = "output/dry_run_v3.html"
    with open(output_path, "w") as f:
        f.write(html)

    print(f"\nHTML rendered: {len(html)} chars")
    print(f"Saved to: {output_path}")
    print(f"Main find: {mock_content['main_find']['title']}")
    print(f"Quick finds: {len(mock_content['quick_finds'])} (from {len(set(qf['source'] for qf in mock_content['quick_finds']))} different sources)")

    return html


if __name__ == "__main__":
    print("\n🛰️  DAILY SCOUT — DRY RUN v3.0 (Multi-Source)\n")

    # Test 0: Config
    config = test_config()

    # Test 1: Fetch
    items = test_fetch(config)

    # Test 2: Pre-Filter
    filtered = test_pre_filter(items, config) if items else []

    # Test 3: Render
    html = test_render()

    print("\n" + "=" * 50)
    print("DRY RUN COMPLETE")
    print("=" * 50)
    print(f"  Config OK: {'YES' if config else 'NO'}")
    print(f"  Sources working: {'YES' if items else 'NO'}")
    print(f"  Items fetched: {len(items)}")
    print(f"  Items after filter: {len(filtered)}")
    print(f"  Template renders: {'YES' if html else 'NO'}")
    print(f"  Output: output/dry_run_v3.html")
    print(f"\nOpen the HTML file in a browser to preview the email!")
