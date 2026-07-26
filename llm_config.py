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
