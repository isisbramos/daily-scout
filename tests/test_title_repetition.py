"""Guard de redundância entre camadas (ed. 244): Transmissão e 1ª frase do corpo não recontam o título."""

from pipeline import check_title_repetition, repeats_title, validate_tone

TITLE_244 = "METR atualiza gráfico de horizonte de tempo: capacidade segue exponencial, mas falha em tarefas de julgamento"


def test_flags_edicao_244():
    content = {
        "correspondent_intro": "Novo relatório do METR mostra que a capacidade dos modelos segue trajetória exponencial no horizonte de tempo.",
        "main_find": {
            "title": TITLE_244,
            "body": "Segundo o MIT Technology Review, um novo relatório do METR, organização sem fins lucrativos que avalia a capacidade de modelos de IA, atualizou seu gráfico de horizonte de tempo. Outra frase.",
        },
    }
    w = check_title_repetition(content)
    assert any("correspondent_intro" in x for x in w)
    assert any("main_find.body" in x for x in w)
    assert len([x for x in validate_tone(content) if x.startswith("[REPEAT]")]) == 2


def test_ok_quando_transmissao_da_o_recorte():
    content = {
        "correspondent_intro": "Hoje a edição junta dois lados dos agentes: quanto tempo eles aguentam trabalhando sozinhos e o primeiro teste deles pagando com cartão de verdade.",
        "main_find": {
            "title": TITLE_244,
            "body": "O METR é uma organização sem fins lucrativos que mede quanto tempo de trabalho humano um modelo de IA consegue completar sozinho; a atualização foi reportada pelo MIT Technology Review. Depois o corpo pode falar de capacidade, horizonte de tempo e julgamento à vontade.",
        },
    }
    assert check_title_repetition(content) == []


def test_exemplo_11c_correto_passa():
    title = "Tencent lança Hy4 preview com 770B parâmetros e contexto de 1M tokens"
    good = "O Hy4 é a linha de modelos de linguagem da Tencent, e quem trouxe o preview foi o Hacker News."
    bad = "Segundo o Hacker News, a Tencent lançou o Hy4 preview, com 770B parâmetros e contexto de 1M tokens."
    assert not repeats_title(good, title)
    assert repeats_title(bad, title)


def test_titulo_vazio_nao_dispara():
    assert check_title_repetition({"correspondent_intro": "qualquer", "main_find": {"title": "", "body": "x"}}) == []
