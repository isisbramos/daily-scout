# Fila de ajustes editoriais

> Movido de `docs/EDITOR_NOTES.md` (migração de contexto, Fase 2). Mesmas instruções de uso de antes.

Espaço livre pra você (Isis, como leitora) anotar, assim que perceber, quando um
tema ou achado de uma edição não bateu com o que esperava da AYA. Sem formato
rígido — só data, edição (se souber o número) e o que não te convenceu. Escreva
aqui direto, ou me conte numa sessão do Claude Code e eu registro.

Isso vira a matéria-prima quando a gente senta pra revisar
[`prompts/system_instruction.txt`](../prompts/system_instruction.txt) (voz, regras
de acurácia, idioma) ou [`prompts/curation_template.txt`](../prompts/curation_template.txt)
(o que entra/sai, ranking, anti-signal) — mesmo processo de discovery que gerou
[`EDITORIAL_RETROSPECTIVE.md`](../docs/EDITORIAL_RETROSPECTIVE.md) na v4.

Depois de uma sessão de ajuste que resolve uma entrada, mova o resumo pra
`EDITORIAL_RETROSPECTIVE.md` como registro histórico do que mudou e por quê, e
apague a entrada daqui — este arquivo é só a fila de coisas ainda não tratadas.

---

<!--
## AAAA-MM-DD — edição #NNN
Tema/achado: o que foi selecionado que não deveria, ou o que ficou de fora e deveria ter entrado
Por que não bateu: sua intuição, mesmo que ainda não esteja articulada como critério
Critério novo (preenchido durante a sessão de ajuste, não precisa vir pronto): —
-->

## 2026-11-23 — edições #245 e #246
Tema/achado: o assunto virou lista de nomes ("Signal, OpenRouter, TechCrunch e Inkling-2-Mini"; "MiniMax, Clover-35B-A3B-Preview, NoPeBench e Ant Group"). Não diz o que a edição traz e, na 245, incluiu a fonte (TechCrunch) como se fosse protagonista.
Por que não bateu: o assunto tem que encapsular o conteúdo do dia, não enumerar entidades.
Critério novo: `edition_headline`, escrita pelo LLM por último: até 70 caracteres com o fio entre os achados, do ponto de vista de quem decide produto; não repete o título do achado, não lista nomes, não cita fonte. O código valida (tamanho, repetição do título, vírgulas, fonte) e, se falhar, o assunto usa o título do achado. Se o destaque for trocado e a headline falar do antigo, ela é descartada. Medir: % de edições com `[HEADLINE]` (fallback) no log do Actions. Os ledes da 245 e 246 já não recontam o título (mudança de 21/11 funcionando).

## 2026-11-21 — edição #244
Tema/achado: o mesmo fato aparecia 5 vezes antes do corpo: assunto do e-mail, título no topo (Buttondown), Transmissão, título do achado e 1ª frase do corpo ("METR atualiza gráfico de horizonte de tempo…" em todas). Nas 240 edições arquivadas, 168 (70%) abrem o corpo recontando o título.
Por que não bateu: cada camada tinha o mesmo trabalho (anunciar o fato). Leitura repetitiva.
Critério novo: uma camada, um trabalho. Assunto = protagonistas da edição; Transmissão = recorte do dia, sem recontar o achado; título do achado = o fato (único lugar); 1ª frase do corpo = contexto que o título não dá. Aplicado em 21/11 (PR "redundância entre camadas"), quebrando o freeze por decisão da Isis. Guard `[REPEAT]` em `validate_tone` (1 retry no máximo). Medir: % de edições com `[REPEAT]` no log e % de excerpts do arquivo que recontam o título (base: 70%).

## 2026-11-19 — edição #242
Tema/achado: o achado do dia (Gemini 4 Neon) falava do título em vez do lançamento: "nenhum desses pontos está no título", "o título não detalha preço". O mesmo padrão aparece em 6 de 82 notas do `vault-outbox` (Gemini 4 Carbon, FTC, China, GPT-6.2, OpenAI).
Por que não bateu: o leitor não vê o input. E a causa era o input: fora de arXiv e HF Papers, o LLM recebia só o título.
Critério novo: "não falar do input para o leitor (título, post, summary); se falta um dado que muda a decisão, dizer o que conferir no anúncio oficial". Tratado em #76 (summary em todas as fontes), #79 (excerpt dos 10 primeiros itens + regra no prompt + check `[META]`). **Em medição desde a ed. 243:** contagem de `[META]` por edição (meta zero) e taxa de excerpt. Mover para `EDITORIAL_RETROSPECTIVE.md` depois de 5 edições.

## 2026-11-17 — edição #240
Tema/achado: o item do pacto global (COP31) saiu com uma linha "No seu produto" que falava de operação no Brasil exigindo transparência energética — contexto que o título não traz. Em geral, a edição soa técnica demais (papers, chips, modelos de fronteira).
Por que não bateu: a AYA é para quem constrói COM IA e usa IA no dia a dia para ajudar o negócio, não para quem constrói IA.
Critério novo: tratado no passo 1.1 (PR da branch `feat/linha-no-seu-trabalho`): linha vira "→ No seu trabalho:" e o prompt proíbe inventar contexto. **Ainda aberto:** o passo 2 (critério de curadoria no STEP 2) deve usar a mesma redação de leitor ("quem usa IA no trabalho"), e vale checar o peso das fontes (arxiv_ai e huggingface_papers têm o maior weight, 1.3).

## 2026-11-17 — edição de teste (dry run da v5.5.1)
Tema/achado: ficaram de fora três papers que a Isis achou interessantes (controle de vídeo longo multi-plano, agente de uso de computador, resolução de ambiguidade em LLMs), além de itens de IA no seguro (MIT Tech Review Brasil), "We don't need more apps. We need better open source" (HN) e Uber/Zipline.
Por que não bateu: a v5.5.1 descartava paper sem resultado no título, e o LLM nunca via o abstract.
Critério novo: tratado no passo 2.1 (v5.5.2): resumo no input + regra por capacidade concreta. **Ainda aberto (um por vez):** teto geográfico derrubou o Qwen4-Max; AI Gate corta tech sem IA (Uber); item de IA no seguro sem causa confirmada (hipótese: título em tom de tese).

## 2026-11-17 — edição de teste (dry run da v5.5.1), follow-ups removidos
Tema/achado: Qwen4-Max lançado só como API fechada (após prometer open source) e o alerta de bolha do Robin Li ficaram de fora, embora o LLM os tenha escolhido como follow-up.
Por que não bateu: o guard de repetição por entidades (2+ em comum com as últimas 7 edições) remove sem olhar o título, contradizendo a exceção "informação nova" do prompt. O teto geográfico não teve relação.
Critério novo: tratado no passo 2.2 (v5.5.3): campo `follow_up` + exceção no guard (máx. 1 por edição, só quick_find, título distinto). **Ainda aberto:** AI Gate corta tech sem IA (Uber/Zipline); item de IA no seguro sem causa confirmada.

## 2026-11-17 — dry run do #69 (v5.5.3) e revisão do processo
Tema/achado: (1) o resumo de 320 caracteres cortava o abstract antes do resultado (Ask Precisely foi descartado por "sem capacidade nomeada"); (2) radar saiu sem url/display_url, o e-mail renderizaria link vazio; (3) o texto de um follow-up dizia "a edição anterior cobriu…" (meta-linguagem vazada, causada pelo Exemplo 17 / contrato do follow-up; e a edição citada era a 234, não a anterior); (4) a abertura da edição se apoiou num item só do Reddit que o revisor reprovou (unverified); (5) o main_find virou paper de desenvolvedores (Termination Lag); (6) `entities` inclui nome de fonte ("TechCrunch"); (7) IA no seguro confirmado como "opinião setorial → descarte".
Por que não bateu: o prompt cresceu 41% em um dia (4,5 mil → 6,4 mil palavras no `curation_template`; proibições de 26 para 42) com 5 commits de prompt, e cada rodada de teste foi uma amostra única com entrada diferente — não dava para separar efeito da mudança, aleatoriedade e feed do dia.
Critério novo: tratado no passo 2.3 (PR do replay): (1) e (2) viram parâmetro e guard de código, sem texto de prompt. **Congelado até 5 edições reais:** (3), (4), (5), (6). Depois, passo 2.4 (limpeza do prompt) medido no replay.


## 2026-11-18 — edição #241
Tema/achado: o achado do dia (GPT-6.2 Astra e Sol) saiu com o bullet "o título não detalha diferenças de capacidade, preço ou disponibilidade entre elas" — meta-linguagem falando com o leitor sobre o input da AYA.
Por que não bateu: a proibição de mencionar "o título" entrou na v5.5.1 só para o `why_watch` do radar; nada impede o mesmo no main_find e nos quick_finds. E o `prompt_lint` conta meta-linguagem no `body`/`signal` e no radar, mas não nos `bullets` do main_find, onde este caso apareceu — o replay não pegaria.
Critério novo: **congelado até 5 edições reais** (junto com o item (3) da entrada anterior). Candidatos: (a) lint conta `bullets` em `meta_linguagem` (ferramenta, não muda produção); (b) estender a regra do radar para todo texto do leitor, medido no replay no passo 2.4.
