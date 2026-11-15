# Produto — AYA

> last-reviewed: 2026-11-15 · Fonte da verdade de produto, público e métricas. Veio da Product Spec v0.2 (travada em 12/05/2026 no vault) e substitui `docs/historico/PRODUCT-2026-04.md`.

## O que é

Uma newsletter diária de tech & IA, curada e escrita por uma persona de IA com voz editorial própria. Resolve information overload: o leitor recebe um scan do que importa em vez de acompanhar dezenas de feeds.

O que a diferencia:
- **IA como lente, não como tema.** Tudo passa pelo AI Gate: sem ângulo de IA, não entra.
- **Perspectiva fora do eixo US/EU.** Fontes da Ásia, do Sul Global e do Brasil.
- **Voz, não digest.** Factual, sem hype, explica o que algo é e por que importa.

## Público (Spec v0.2)

**Como lê:** scan diário de 60 a 90 segundos, no celular, e clica para se aprofundar fora. A edição é interface de descoberta, não destino.

- **Primário — Tech Operator:** PM, eng, founder ou tech lead brasileiro. Desde 15/11, com foco no PM (ver "Recorte para PMs"). Lê no café ou entre reuniões e quer um bom hit ratio de "vale meu clique".
- **Secundário — Builder-Adjacent:** designer, writer, marketer ou consultor que constrói com IA. Mesmo padrão de leitura.
- **Anti-persona:** quem procura explainer introdutório, leitor movido a hype e quem quer pesquisa acadêmica pura.

## Pilares editoriais

1. **Tools & Launches:** ferramenta ou feature concreta que muda workflow.
2. **Evidence & Benchmarks:** dado, estudo, dataset, pesquisa primária.
3. **Power Moves & Regulation:** decisão de autoridade, regulação, movimentos de big tech, M&A.
4. **Anchored Analysis:** análise com pesquisa original ou framework testável.

**Fica de fora:** manifesto ou thought-leadership sem evento, preço consumer ou funding sem ângulo, crypto/web3, notícia requentada.

## Cadência

Diária, 7h55 BRT, todos os dias, inclusive fim de semana e feriado. Revisar só se o open rate ficar abaixo de 30% por 3 semanas seguidas ou o unsubscribe passar de 2% numa edição.

## Métricas

| Tier | Métrica | Meta | Onde mede |
| --- | --- | --- | --- |
| North Star A | CTR (qualquer link da edição) | ≥ 12% | Buttondown |
| North Star B | Engaged subs (open + click nos últimos 14 dias) | 30% da lista | Buttondown |
| Growth | Novos assinantes por semana | +10/sem orgânico até 250 | Buttondown |
| Surface health | Open rate | ≥ 40% | Buttondown |
| Quality signal | Unsubscribe por edição | < 0,5% | Buttondown |
| Editorial fit | Feedback ratio | ≥ 5% de resposta, 4:1 positivo | Sheet de feedback |
| Retention | Retenção de leitura em 30 dias | ≥ 60% | Buttondown |
| Click distribution | % de assinantes que clicam ≥ 1 link por semana | ≥ 25% | Buttondown |

**Gate:** referral e personalização só depois de 250 engaged subs e 90 dias de dados.

Os números reais ficam fora deste repo, que é público.

## Recorte para PMs (decidido em 15/11/2026)

**Por quê:** a AYA estava "muito dev". Faltava conteúdo que product managers consigam usar. JTBD: "me diz o que essa notícia de IA muda no meu roadmap".

| Pergunta | Decisão |
| --- | --- |
| Persona | **Recorte**, não substituição: o Tech Operator continua sendo o primário, com o PM como foco dentro dele. |
| Curadoria | Critério novo: o item **muda uma decisão de produto**. |
| Escrita | Cada item ganha uma linha de **"o que muda no seu produto"**. |
| Pilar 5 | **IA, consciência/mente e cultura** entra como pilar editorial (ex.: estudos sobre "dor" em modelos, Anthropic e o Vaticano). |
| Sucesso | Mais 🔥 no feedback por edição e mais assinantes novos por semana. |

**Nada disso está no prompt ainda.**

### Ordem de implementação

São três mudanças editoriais. Pela regra de uma por vez, cada uma entra, é medida no Content Report e só então vem a próxima:

1. **Escrita:** a linha "o que muda no seu produto". É a mais barata, só mexe no texto e não muda o que entra.
2. **Curadoria:** o critério "muda uma decisão de produto" no STEP 2.
3. **Pilar 5.** Vem por último porque tem uma tensão a resolver (abaixo).

### Tensão do pilar 5

A v5.4 foi endurecida justamente contra conteúdo cognitivo: o STEP 2 exige que o item seja "acionável (concreto, não cognitivo)" e descarta manifesto e opinião sem evento. Uma pauta como "Anthropic e o Vaticano" tende a ser reprovada por essas regras. Para o pilar 5 existir, o prompt vai precisar de uma exceção explícita. Por exemplo: o item entra se houver um **evento âncora** (estudo, decisão, declaração pública de um player) mesmo sem ser acionável, com no máximo 1 item por edição. Sem isso, o pilar fica só no papel.

### Como medir

Com a base pequena, uma edição sozinha não diz nada. Para cada mudança, compare **4 semanas antes e 4 depois**:
- % de votos 🔥 por edição (sem os votos anômalos de 25/08 a 08/09);
- assinantes novos por semana;
- no Content Report, se os itens trazem de fato a linha nova e se o critério novo aparece no reasoning.

## Decisões relacionadas

Os ADRs ficam no vault (`isis-brain/04-decisoes/`): "Fechar product spec AYA v0.2" (12/05), "Rebrand AYA como entidade autônoma" (20/05), "Consolidar naming em AYA apenas" (20/05), "Fechar tagline da AYA" (20/05), "Recortar AYA para product managers" (15/11).
