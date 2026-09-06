"""
Testes de contrato para pipeline.py::curate_and_write.

curate_and_write() tem bastante código defensivo pra lidar com a API do DeepSeek
respondendo torto (JSON truncado, JSON inválido, campos ausentes) — esses testes
provam que esse código defensivo realmente funciona, mockando o cliente OpenAI
para simular cada tipo de resposta ruim sem bater na rede.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import pipeline
from exceptions import CurationError
from sources.base import SourceItem


VALID_CONTENT = {
    "main_find": {"title": "Achado principal", "body": "corpo", "bullets": ["b1"]},
    "quick_finds": [{"title": "QF1", "signal": "sinal", "entities": ["OpenAI"]}],
    "correspondent_intro": "intro",
}

SOME_ITEMS = [
    SourceItem(title="t1", url="u1", source_id="a", source_label="A"),
    SourceItem(title="t2", url="u2", source_id="b", source_label="B"),
]


class FakeChatCompletions:
    """Substitui client.chat.completions — consome `responses` em ordem.

    Cada entrada é um dict {"content": str, "finish_reason": str} pra simular
    uma resposta da API, ou uma Exception pra simular erro de rede/rate limit.
    """

    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        message = SimpleNamespace(content=item["content"])
        choice = SimpleNamespace(message=message, finish_reason=item.get("finish_reason", "stop"))
        return SimpleNamespace(choices=[choice])


def _fake_openai(responses):
    """Patch-able factory: OpenAI(...) -> client com .chat.completions.create fake."""
    client = SimpleNamespace(chat=SimpleNamespace(completions=FakeChatCompletions(responses)))
    return lambda *args, **kwargs: client


def _response(content: dict | str, finish_reason: str = "stop") -> dict:
    text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    return {"content": text, "finish_reason": finish_reason}


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    """Isola curate_and_write de estado real: API key fake, sem memória editorial
    do disco (evita acoplar esses testes ao histórico real de 168+ edições) e
    sem sleep de verdade entre retries."""
    monkeypatch.setattr(pipeline, "DEEPSEEK_API_KEY", "fake-key")
    monkeypatch.setattr(pipeline, "load_recent_editions", lambda n=7: [])
    monkeypatch.setattr(pipeline.time, "sleep", lambda *a, **k: None)


class TestValidResponse:
    def test_returns_content_on_first_try(self):
        with patch("openai.OpenAI", _fake_openai([_response(VALID_CONTENT)])):
            content = pipeline.curate_and_write(SOME_ITEMS)
        assert content["main_find"]["title"] == "Achado principal"
        assert content["quick_finds"][0]["title"] == "QF1"

    def test_double_encoded_json_string_is_parsed(self):
        """DeepSeek às vezes devolve uma string JSON contendo o JSON (double-encoded)."""
        double_encoded = json.dumps(json.dumps(VALID_CONTENT, ensure_ascii=False))
        with patch("openai.OpenAI", _fake_openai([_response(double_encoded)])):
            content = pipeline.curate_and_write(SOME_ITEMS)
        assert content["main_find"]["title"] == "Achado principal"


class TestTruncatedResponse:
    def test_recovers_on_retry(self):
        responses = [
            _response(VALID_CONTENT, finish_reason="length"),
            _response(VALID_CONTENT, finish_reason="stop"),
        ]
        with patch("openai.OpenAI", _fake_openai(responses)):
            content = pipeline.curate_and_write(SOME_ITEMS, max_retries=3)
        assert content["main_find"]["title"] == "Achado principal"

    def test_exhausts_retries_raises_curation_error(self):
        responses = [_response(VALID_CONTENT, finish_reason="length") for _ in range(3)]
        with patch("openai.OpenAI", _fake_openai(responses)):
            with pytest.raises(CurationError):
                pipeline.curate_and_write(SOME_ITEMS, max_retries=3)


class TestMalformedJson:
    def test_retries_then_succeeds(self):
        responses = [_response("{not valid json"), _response(VALID_CONTENT)]
        with patch("openai.OpenAI", _fake_openai(responses)):
            content = pipeline.curate_and_write(SOME_ITEMS, max_retries=3)
        assert content["main_find"]["title"] == "Achado principal"

    def test_exhausts_retries_raises_curation_error(self):
        responses = [_response("{not valid json") for _ in range(3)]
        with patch("openai.OpenAI", _fake_openai(responses)):
            with pytest.raises(CurationError):
                pipeline.curate_and_write(SOME_ITEMS, max_retries=3)


class TestMissingFields:
    def test_missing_main_find_key_retries_then_succeeds(self):
        responses = [_response({"quick_finds": []}), _response(VALID_CONTENT)]
        with patch("openai.OpenAI", _fake_openai(responses)):
            content = pipeline.curate_and_write(SOME_ITEMS, max_retries=3)
        assert content["main_find"]["title"] == "Achado principal"

    def test_missing_main_find_key_exhausts_retries(self):
        responses = [_response({"quick_finds": []}) for _ in range(3)]
        with patch("openai.OpenAI", _fake_openai(responses)):
            with pytest.raises(CurationError):
                pipeline.curate_and_write(SOME_ITEMS, max_retries=3)

    def test_missing_title_in_main_find_is_rejected(self):
        bad = {"main_find": {"body": "sem título"}, "quick_finds": []}
        responses = [_response(bad), _response(VALID_CONTENT)]
        with patch("openai.OpenAI", _fake_openai(responses)):
            content = pipeline.curate_and_write(SOME_ITEMS, max_retries=3)
        assert content["main_find"]["title"] == "Achado principal"

    def test_optional_main_find_fields_get_safe_defaults(self):
        minimal = {"main_find": {"title": "só título"}, "quick_finds": [{"title": "qf sem campos"}]}
        with patch("openai.OpenAI", _fake_openai([_response(minimal)])):
            content = pipeline.curate_and_write(SOME_ITEMS, max_retries=1)

        mf = content["main_find"]
        assert mf["body"] == ""
        assert mf["bullets"] == []
        assert mf["url"] == ""
        assert mf["display_url"] == ""
        assert mf["source"] == ""
        assert mf["entities"] == []

        qf = content["quick_finds"][0]
        assert qf["signal"] == ""
        assert qf["url"] == ""
        assert qf["display_url"] == ""
        assert qf["source"] == ""
        assert qf["entities"] == []

        assert content["themes"] == []
        assert content["radar"] == []

    def test_empty_quick_finds_retries_then_accepted_on_last_attempt(self):
        empty_qf = {"main_find": {"title": "Achado sem quick finds"}, "quick_finds": []}
        responses = [_response(empty_qf), _response(empty_qf)]
        with patch("openai.OpenAI", _fake_openai(responses)):
            content = pipeline.curate_and_write(SOME_ITEMS, max_retries=2)
        assert content["quick_finds"] == []

    def test_missing_quick_finds_key_treated_as_empty(self):
        no_qf_key = {"main_find": {"title": "Achado sem chave quick_finds"}}
        with patch("openai.OpenAI", _fake_openai([_response(no_qf_key)])):
            content = pipeline.curate_and_write(SOME_ITEMS, max_retries=1)
        assert content["quick_finds"] == []
