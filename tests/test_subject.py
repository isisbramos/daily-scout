from delivery import build_subject


def test_subject_lista_protagonistas_sem_repetir_titulo():
    content = {
        "main_find": {"title": "METR atualiza gráfico de horizonte de tempo", "entities": ["METR", "MIT Technology Review"]},
        "quick_finds": [
            {"title": "Apple apresenta Depth Pro 2", "entities": ["Apple", "Depth Pro 2"]},
            {"title": "Animoca testa pagamentos na Visa", "entities": ["Animoca Brands", "Visa"]},
        ],
    }
    s = build_subject(244, content)
    assert s == "AYA #244 — METR, Apple e Animoca Brands"
    assert content["main_find"]["title"] not in s


def test_subject_fallback_sem_entidades():
    content = {"main_find": {"title": "Título", "entities": []}, "quick_finds": []}
    assert build_subject(1, content) == "AYA #1 — Título"


def test_subject_dedup_entidade_repetida():
    content = {
        "main_find": {"title": "x", "entities": ["OpenAI"]},
        "quick_finds": [{"entities": ["openai"]}, {"entities": ["Google"]}],
    }
    assert build_subject(2, content) == "AYA #2 — OpenAI e Google"
