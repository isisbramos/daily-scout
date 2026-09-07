# Avisos ao leitor

Mecanismo one-shot pra anunciar mudanças no email (ex: "ajustamos a curadoria")
sem precisar lembrar de desligar depois. Lógica em [`notices.py`](../notices.py).

## Como usar

Peça no chat o texto do aviso. Depois de combinado, `notices/pending.json` é
criado e commitado:

```json
{"text": "...", "requested_at": "2026-09-06T22:00:00-03:00"}
```

Na próxima edição **realmente enviada** (dry run não conta), `pipeline.py`:

1. Lê `pending.json` e usa o texto no topo do email.
2. Registra o envio em `sent_log.jsonl` (histórico append-only).
3. Apaga `pending.json`.

O workflow `daily-scout.yml` persiste isso de volta pro repo (mesmo padrão da
memória editorial). Resultado: o aviso sai uma vez só, e não tem nada pra
lembrar de tirar depois.

## `sent_log.jsonl`

Um registro por aviso já enviado:

```json
{"text": "...", "edition": "169", "sent_at": "2026-09-07T03:41:00-03:00"}
```
