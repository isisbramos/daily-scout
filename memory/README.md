# Editorial Memory

Memória editorial da AYA — o que dá à curadoria consciência das edições anteriores.

## `editions.jsonl`

Store append-only (uma edição por linha). Gerado por [`memory_store.py`](../memory_store.py)
ao fim de cada edição **enviada** (dry runs não escrevem aqui). O CI é efêmero, então o
arquivo é **commitado de volta ao repo** pelo workflow [`daily-scout.yml`](../.github/workflows/daily-scout.yml).

Cada registro é um snapshot leve:

```json
{
  "edition": "091",
  "date": "2026-06-22",
  "main_find": { "title": "...", "entities": ["OpenAI", "GPT-5.2"], "claim_status": "confirmado" },
  "quick_finds": [{ "title": "...", "entities": ["Anthropic"] }],
  "themes": ["agentes de código", "regulação UE"],
  "sources_used": ["hackernews", "arxiv"],
  "feedback_score": null
}
```

## Como é usado

No início da curadoria, `load_recent_editions()` lê as últimas ~7 edições e
`format_memory_block()` as injeta no prompt. A AYA usa isso para **evitar repetir**
achados e **conectar desdobramentos** (campo `continuity_note`).

`feedback_score` fica `null` no envio — reservado para o loop de feedback (🔥/👍/😐)
preencher depois, como base de calibração futura.
