# CI Health

Histórico de execuções da suíte de testes — separado de `memory/` porque
aquele diretório é memória *editorial* (o que a AYA já publicou); isso aqui é
saúde de engenharia (o código continua funcionando conforme muda).

## `test_runs.jsonl`

Store append-only (uma execução por linha). Gerado por
[`scripts/record_test_run.py`](../scripts/record_test_run.py) a partir do
JUnit XML que o [`tests.yml`](../.github/workflows/tests.yml) produz, e
commitado de volta ao repo pelo mesmo `scripts/persist_to_git.sh` usado pela
memória editorial — só roda em `push`/`schedule`/`workflow_dispatch` (nunca em
`pull_request`, pra não empurrar commit de uma branch de PR direto pra `main`).

Cada registro:

```json
{
  "date": "2026-09-06T20:03:04Z",
  "commit_sha": "2cdf2d1",
  "trigger": "push",
  "python_version": "3.12.14",
  "pytest_version": "9.0.3",
  "total": 125,
  "passed": 125,
  "failed": 0,
  "skipped": 0,
  "duration_s": 1.02,
  "conclusion": "passed"
}
```

## Como é usado

`dashboard.py` lê este arquivo pra mostrar uma seção de saúde de CI (histórico
recente de pass/fail, duração, versão do pytest em uso) — útil pra notar, por
exemplo, quando um bump de dependência (como o do pytest 8→9) mudou o tempo de
execução ou passou a falhar silenciosamente em algum ambiente.
