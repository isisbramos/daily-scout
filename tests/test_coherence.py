"""Rec. 6 — coerência: troca do destaque registra, anota o reasoning e reescreve a introdução."""

from __future__ import annotations

import copy
import json
from types import SimpleNamespace

import coherence as co


def _content():
    return {
        "reasoning": {"main_find_rationale": "Escolhi a frota de agentes chinesa porque..."},
        "correspondent_intro": "Hoje tem uma frota de agentes de AI rastreada por pesquisadores. Analisei 302 posts de 22 fontes.",
        "main_find": {"title": "Cloudflare lança API de busca na web para agentes de AI", "body": "Corpo do novo destaque.", "bullets": []},
        "quick_finds": [{"title": "Outro achado", "signal": "s"}],
    }


OLD = {"title": "Pesquisadores rastreiam frota de agentes de AI chinesa"}


def _client(payload):
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    create = lambda **kw: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


class TestNoteMainSwap:
    def test_records_swap_and_annotates_reasoning(self):
        c = _content()
        co.note_main_swap(c, OLD, "repetição de edição recente")
        assert c["main_swaps"] == [{"from": OLD["title"], "to": c["main_find"]["title"],
                                    "reason": "repetição de edição recente", "intro_refreshed": False}]
        r = c["reasoning"]["main_find_rationale"]
        assert r.startswith("[AJUSTE AUTOMÁTICO") and OLD["title"] in r and "Escolhi a frota" in r

    def test_reasoning_not_a_dict_is_ignored(self):
        c = _content()
        c["reasoning"] = "texto"
        co.note_main_swap(c, OLD, "x")
        assert c["reasoning"] == "texto" and len(c["main_swaps"]) == 1


class TestRefreshIntro:
    def test_no_swaps_does_nothing_and_never_calls_llm(self):
        c = _content()
        before = copy.deepcopy(c)

        def boom(**kw):
            raise AssertionError("não deveria chamar o LLM")
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=boom)))
        assert co.refresh_after_swaps(c, client=client) is None
        assert c == before

    def test_llm_rewrite_is_applied(self):
        c = _content()
        co.note_main_swap(c, OLD, "x")
        new = "A Cloudflare abriu busca na web para agentes. Analisei 302 posts de 22 fontes pra você não precisar garimpar tudo."
        res = co.refresh_after_swaps(c, client=_client({"correspondent_intro": new}))
        assert res["method"] == "llm" and c["correspondent_intro"] == new
        assert c["main_swaps"][0]["intro_refreshed"] is True

    def test_runs_only_once_per_swap(self):
        c = _content()
        co.note_main_swap(c, OLD, "x")
        co.refresh_after_swaps(c, client=_client({"correspondent_intro": "A Cloudflare abriu busca para agentes de AI hoje."}))
        assert co.refresh_after_swaps(c, client=_client({})) is None

    def test_llm_error_uses_deterministic_fallback(self):
        c = _content()
        co.note_main_swap(c, OLD, "x")

        def boom(**kw):
            raise RuntimeError("API fora")
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=boom)))
        res = co.refresh_after_swaps(c, client=client)
        assert res["method"] == "fallback"
        assert c["correspondent_intro"].startswith("O destaque de hoje: Cloudflare lança API")
        assert "302 posts de 22 fontes" in c["correspondent_intro"]       # frase de volume preservada
        assert "frota" not in c["correspondent_intro"].lower()            # nada do destaque antigo

    def test_reply_that_mentions_old_main_is_rejected(self):
        c = _content()
        co.note_main_swap(c, OLD, "x")
        bad = "Pesquisadores rastreiam frota de agentes de AI chinesa e a Cloudflare lança busca."
        res = co.refresh_after_swaps(c, client=_client({"correspondent_intro": bad}))
        assert res["method"] == "fallback" and "Pesquisadores rastreiam" not in c["correspondent_intro"]

    def test_tone_check_rejects_hype(self):
        c = _content()
        co.note_main_swap(c, OLD, "x")
        hype = "Uma novidade revolucionária da Cloudflare para agentes de AI chegou hoje."
        res = co.refresh_after_swaps(c, tone_check=lambda t: "revolucion" in t, client=_client({"correspondent_intro": hype}))
        assert res["method"] == "fallback"

    def test_invalid_json_or_length_falls_back(self):
        for payload in ("não é json", {"correspondent_intro": "curto"}, {"correspondent_intro": "x" * 600}, {"outra": 1}):
            c = _content()
            co.note_main_swap(c, OLD, "x")
            assert co.refresh_after_swaps(c, client=_client(payload))["method"] == "fallback"
