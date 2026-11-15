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

- **Primário — Tech Operator:** PM, eng, founder ou tech lead brasileiro. Lê no café ou entre reuniões e quer um bom hit ratio de "vale meu clique".
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

## Direção em definição (nov/2026)

O que a Isis já decidiu:
- [2026-11] O direcionamento que falta é de produto: conteúdo que product managers consigam usar.
- [2026-11] JTBD: "me diz o que essa notícia de IA muda no meu roadmap".
- [2026-11] Hoje a AYA está "muito dev".

O que ela quer, mas ainda sem regra:
- Algum viés editorial para IA e consciência/mente e cultura (ex.: estudos sobre "dor" em modelos, Anthropic e o Vaticano).

**Nada disso está no prompt ainda.** Mudar o prompt exige dry run e uma mudança por vez.

## Perguntas em aberto

Responder antes de mexer no prompt:

1. O PM vira a persona primária, no lugar do Tech Operator, ou é um recorte dentro dele?
2. O que muda na **curadoria**? Um critério novo no STEP 2 ("muda uma decisão de produto")? Peso diferente entre os pilares?
3. O que muda na **escrita**? Cada item ganha uma linha de "o que muda pro seu roadmap"?
4. O viés IA/consciência/cultura entra como pilar 5, como seção de radar ou fica fora?
5. Que métrica vai mostrar que a mudança funcionou?

## Decisões relacionadas

Os ADRs ficam no vault (`isis-brain/04-decisoes/`): "Fechar product spec AYA v0.2" (12/05), "Rebrand AYA como entidade autônoma" (20/05), "Consolidar naming em AYA apenas" (20/05), "Fechar tagline da AYA" (20/05).
