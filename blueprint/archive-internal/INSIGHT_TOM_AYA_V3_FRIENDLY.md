## Insight — 25 março 2026

**O que eu estava tentando fazer**
Criei uma newsletter automatizada com uma "correspondente" de IA chamada Aya. Ela lê centenas de posts de tech por dia e escreve um resumo curado. O problema: a Aya estava mentindo e exagerando. Escrevia coisas como "revolução no mundo da IA" e inventava detalhes que não existiam nas fontes.

**O que mudou**
Tentei resolver escrevendo instruções cada vez mais detalhadas — "não use essas palavras", "revise antes de responder", "siga este exemplo". Três versões de prompt. A IA ignorou todas.

O que funcionou foi parar de dar instruções e começar a construir restrições concretas:
- Separei as regras em um lugar onde a IA dá mais atenção (como se fosse a "constituição" dela, não um pedido no meio da conversa)
- Defini um formato rígido com campos tipados — em vez de pedir "escreva um JSON", dei a ela um formulário onde cada campo tem limite e descrição
- Criei um filtro automático que lê o texto depois que a IA escreve e rejeita se encontrar palavras de exagero — forçando ela a reescrever

Mas a primeira versão dessa correção foi longe demais. A Aya parou de mentir, mas também parou de explicar qualquer coisa. O texto ficou seco, repetia o título da notícia e não ajudava o leitor a entender nada. O equilíbrio veio quando criei uma regra simples: a IA PODE explicar o que algo é e por que importa. NÃO PODE inventar reações ou exagerar. Parece óbvio, mas pra uma IA, essa fronteira precisa ser explícita.

**Como isso muda meu processo**
A lição principal: IA não segue intenção, segue estrutura. Dizer "não exagere" não funciona. Construir um sistema que detecta e rejeita exagero funciona. É a diferença entre pedir pra alguém dirigir devagar e instalar um limitador de velocidade.

E a calibração nunca é linear. Você corrige o exagero e mata o contexto. Corrige a secura e arrisca voltar o exagero. O ponto certo aparece quando você erra pros dois lados e encontra o meio.

**O que ainda está aberto**
O filtro de exagero é uma lista fixa de palavras. A IA vai encontrar novas formas de dramatizar que eu ainda não previ. Como manter isso atualizado sem virar um jogo infinito de whack-a-mole?
E a temperatura zero (que elimina criatividade) resolve o problema hoje, mas a newsletter precisa de personalidade. Qual o mínimo de criatividade que posso dar sem abrir a porta pro sensacionalismo?

**Semente de post**
Passei 3 versões tentando ensinar uma IA a não exagerar. Ela ignorou todas as instruções. Aí parei de pedir e comecei a construir cercas. A diferença entre pedir "dirija devagar" e instalar um limitador de velocidade.
