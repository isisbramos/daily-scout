"""Configuração central do modelo DeepSeek usado na curadoria e nos agentes auxiliares.

A DeepSeek deprecou `deepseek-chat` em 24/07/2026 15:59 UTC, quebrando as edições #125
e #126. O nome do modelo estava repetido em 4 call-sites; centralizar aqui faz da próxima
troca uma linha só. `DEEPSEEK_MODEL` permite trocar por env var, sem esperar deploy.
"""

from __future__ import annotations

import os

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")

# `deepseek-chat` era o v4-flash em modo non-thinking. Os modelos v4 ligam thinking por
# default, e os reasoning tokens consomem o orçamento de max_tokens — o que aproximaria
# o JSON da curadoria da truncação. Desligar preserva o comportamento das edições 1–124.
DEEPSEEK_EXTRA_BODY = {"thinking": {"type": "disabled"}}

# ── Judge (audit_agent.py) ──────────────────────────────────────────────
# LLM-as-judge tolera um modelo mais barato/menor melhor do que a geração tolera —
# o audit só precisa criticar de forma consistente em JSON, não escrever prosa boa.
# Por padrão usa o mesmo provedor/modelo da curadoria (nada muda se você não setar
# nada). Pra trocar por um modelo mais barato, defina as env vars abaixo — se
# AUDIT_BASE_URL apontar pra fora da DeepSeek, o extra_body específico da DeepSeek
# (thinking disabled) é omitido, já que outro provedor não entende esse parâmetro.
AUDIT_BASE_URL = os.environ.get("AUDIT_BASE_URL", DEEPSEEK_BASE_URL)
AUDIT_MODEL = os.environ.get("AUDIT_MODEL", DEEPSEEK_MODEL)
AUDIT_EXTRA_BODY = DEEPSEEK_EXTRA_BODY if AUDIT_BASE_URL == DEEPSEEK_BASE_URL else {}
