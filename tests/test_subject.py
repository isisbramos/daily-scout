"""Assunto do e-mail: edition_headline validada; fallback para o título do achado."""

from pipeline import build_subject, headline_problem

TITLE_245 = "Signal bloqueia screenshots no celular por causa de agentes de IA nos sistemas operacionais"


def _content(headline):
    return {
        "edition_headline": headline,
        "main_find": {"title": TITLE_245, "source": "techcrunch", "entities": ["Signal"]},
        "quick_finds": [
            {"title": "Pesquisadores plantam 2 milhões de iscas", "source": "lobsters", "entities": ["OpenRouter"]},
            {"title": "TechCrunch lista agentes de IA no app de mensagens", "source": "techcrunch", "entities": ["TechCrunch"]},
        ],
    }


def test_usa_headline_boa():
    c = _content("Agentes de IA entram no celular e a privacidade vira o problema")
    assert build_subject(245, c) == "AYA #245 — Agentes de IA entram no celular e a privacidade vira o problema"


def test_limpa_aspas_e_ponto_final():
    c = _content('"Agentes de IA entram no celular e a privacidade vira o problema."')
    assert build_subject(1, c).endswith("vira o problema")


def test_rejeita_lista_de_nomes():
    assert headline_problem("Signal, OpenRouter, Vercel e Inkling-2-Mini", _content("")) is not None


def test_rejeita_fonte():
    assert headline_problem("O que a TechCrunch viu sobre agentes no celular", _content("")) == "cita fonte/veículo"


def test_rejeita_reconta_titulo():
    p = headline_problem("Signal bloqueia screenshots por causa de agentes de IA", _content(""))
    assert p == "reconta o main_find.title"


def test_rejeita_curta_ou_longa():
    assert headline_problem("IA hoje", _content("")) is not None
    assert headline_problem("x" * 120, _content("")) is not None


def test_fallback_titulo_quando_ausente_ou_ruim():
    assert build_subject(7, _content("")) == f"AYA #7 — {TITLE_245}"
    assert build_subject(7, _content("Signal, OpenRouter, TechCrunch e Inkling-2-Mini")) == f"AYA #7 — {TITLE_245}"


def test_exemplo_246_passa():
    c = {"edition_headline": "IA sai do chat e passa a fazer pesquisa: de criptografia a química",
         "main_find": {"title": "MiniMax publica ataques criptográficos descobertos por IA, com papers e código", "source": "technode"},
         "quick_finds": [{"source": "huggingface_papers"}, {"source": "arxiv_ai"}]}
    assert headline_problem(c["edition_headline"], c) is None
