---
tipo: decisao
criado: 2026-09-15
tags: [decisao]
temas: [Editorial]
projetos: [AYA]
---

# Varia posição da atribuição editorial

A AYA soava correta mas monótona — toda edição, todo achado abria com "Segundo [fonte], ..." ou "De acordo com [fonte], ...". Isso nasceu como fix de acurácia (v1→v2, ver `PROMPT_FIX_TOM_AYA_V3.md`): o Gemini Flash alucinava contexto quando tinha mais liberdade de voz, e forçar a atribuição no início de toda frase foi a trava que resolveu. Só que o efeito colateral matou qualquer ritmo — 3 edições reais seguidas (168, 169, 170) tinham a mesma cadência exata.

**Decisão:** soltar a POSIÇÃO da atribuição (pode vir no fim ou embutida no meio da frase, varia entre itens da mesma edição), sem soltar a OBRIGATORIEDADE dela nem tocar em nenhuma guardrail de acurácia (adjetivo de intensidade continua banido, certeza epistêmica continua preservada). Mudança feita só em `prompts/curation_template.txt`, nada em `system_instruction.txt`. Também soltei o `correspondent_intro` pra endereçar o leitor diretamente ("você"/"a gente") e variar o formato de abertura entre edições.

Testado em 6 dry runs com DeepSeek real (08 e 15/09). Dois bugs apareceram e foram corrigidos no processo: uma frase pessoal ficava cortada ("...pra você não precisar." sem completar não precisar de quê), e um item perdeu a atribuição à fonte por completo quando a notícia já citava um ator humano dentro dela (ex: "um matemático da NYU acusa a OpenAI" — o modelo achou que nomear o matemático já bastava e esqueceu de citar o TechCrunch). Corrigido explicitando que nomear um ator na notícia não substitui citar a fonte que reportou.

Resultado: 0 ocorrências de "Segundo [fonte]," abrindo frase nos últimos 3 runs (era 100% antes), zero warnings de hype em nenhum dos 6 testes. Padrão residual observado: o modelo convergiu quase todo item pra uma única variação nova ("[fato], segundo [fonte], [complemento]") em vez de alternar de verdade — próximo passo é um few-shot mostrando 3 posições diferentes lado a lado.

**Status:** mudança só no working tree local, não commitada, não deployada. Produção (edições 171-177) ainda roda o prompt antigo. Registro completo com antes/depois real em `docs/EDITORIAL_RETROSPECTIVE.md` (Capítulo 6).

---
**Temas:** [[Editorial]]
**Projeto:** [[AYA]]
**Daily:** [[2026-09-15]]
