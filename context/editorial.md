# Regras editoriais — o porquê

> last-reviewed: 2026-11-15 · Este arquivo explica **por que** cada regra editorial existe. O prompt (`prompts/system_instruction.txt` + `prompts/curation_template.txt`) é a **fonte de execução** — é o que roda de fato. Quando os dois discordarem, o prompt venceu na produção, mas isso é sinal de que este arquivo ficou desatualizado: atualize-o. Não copie o texto do prompt aqui; mudança de regra passa por dry run (`CLAUDE.md` → Regras de produção), não por este arquivo.

## A restrição de base: só título e metadados

Tudo abaixo existe em função de uma restrição física: a AYA nunca lê o corpo dos artigos, só título e metadados (`prompts/system_instruction.txt`, bloco "RESTRIÇÃO FUNDAMENTAL"). Isso é deliberado — ler o artigo completo custaria mais e abriria mais superfície para alucinação. A consequência é que toda regra de acurácia (o que PODE/NÃO PODE, a regra de certeza que preserva "may/could/reportedly", o `claim_status`) existe para impedir que a AYA invente o que não está no título. O v3 do pipeline (mar/2026) documentou esse problema do jeito mais caro: a primeira versão alucinava e sensacionalizava, e a correção foi em 5 camadas (system instruction separada, temperatura 0.0, schema tipado, lembrete final, retry com detector de hype) — ver `docs/historico/ROADMAP.md`, "Semana 1 — Pipeline & Tone".

## AI Gate (STEP 1)

Todo post é classificado como relação DIRETA, TANGENCIAL ou NENHUMA com AI/ML antes de qualquer outro critério. Isso existe porque o diferencial do produto é "IA como lente, não como tema" (`context/produto.md`) — sem o gate, a curadoria tenderia a virar um agregador de tech genérico. O caso que motivou o gate (discovery editorial de 26/mar): um post sobre mercados de previsão com 539 pontos no HackerNews quase virou destaque por tração, sem nenhum ângulo de IA, enquanto uma notícia menor mas relevante (Gemini importando histórico de chats) ficava de fora. Tração não é proxy de relevância editorial.

## Source Bias Check (STEP 1.5)

Blogs corporativos oficiais (Anthropic, OpenAI, DeepMind, Google, Apple, AWS) só passam se anunciam algo testável agora — thought-leadership e posicionamento de marca são descartados. A razão é estrutural, não de conteúdo: essas fontes têm weight 0.7–0.8 em `sources_config.json` (o mais baixo do sistema) justamente porque "blogs corporativos são marketing-heavy" — o peso já desconfia da fonte antes do conteúdo ser avaliado. arXiv e HuggingFace Papers são a exceção: têm tier `T1` e weight 1.3 (o mais alto) porque são pesquisa acadêmica original, não marketing — por isso o STEP 1.5 não se aplica a eles. A mesma lógica (sem anúncio de ferramenta, sem dado novo, sem evento concreto → descarte) vale para blogs pessoais com conteúdo de manifesto, com uma exceção simétrica: ensaio com pesquisa original (benchmark próprio, dataset) é tratado como fonte primária.

## Critérios do STEP 2 (2 de 3: acionável, sinal de mercado, afeta fluxos de trabalho)

Esta é a régua de "vale a pena publicar" — e é a régua que o recorte para PMs (decidido 15/11, `context/produto.md`) pretende apertar com um critério extra ("muda uma decisão de produto"), ainda não implementado. Hoje os três critérios já empurram nessa direção: "acionável" exclui mudança de mindset sem decisão concreta, e "sinal de mercado" exclui resultado financeiro isolado (receita, lucro, valuation) sem novidade de produto ou estratégia — exatamente o tipo de notícia que o passo 2 do recorte PM quer filtrar mais.

## Anti-signal (STEP 3)

Esta lista existe porque o framework v5.4 (abr/2026) descobriu, pelo Plano de melhoria editorial de out/2026 (`docs/historico/EDITORIAL_IMPROVEMENT_PLAN.md`), que o modelo **conhece as regras e não as cumpre**: o reasoning dizia "roundups são descartados" e a edição publicava dois panoramas na mesma semana. Por isso duas das regras do STEP 3 — rodada de investimento e resultado financeiro sem novidade — têm reforço mecânico fora do prompt: `pre_filter.py` multiplica o score desses títulos por 0.5 (`scoring.funding_penalty` em `sources_config.json`) antes mesmo de chegarem ao LLM. A regra em código funciona melhor que a regra em texto porque não depende do modelo "lembrar" de aplicá-la. As demais entradas (notícia requentada, manifesto sem ancoragem, tema saturado na memória editorial) seguem só no prompt — são mais difíceis de capturar deterministicamente porque dependem de contexto (o que já foi dito em edições recentes, se o título traz informação nova sobre um evento velho).

## Diversidade (dentro do STEP 4)

Três constraints, cada uma nascida de um problema observado:
- **Geográfica** (máx. 2 itens da mesma região): nasceu do oposto do que se esperaria — o v5.0 (mar/2026) tinha "echo chamber ocidental" e depois over-representation de fontes asiáticas quando SCMP/TechNode entraram; o cap existe pra não deixar nenhuma região dominar, nos dois sentidos.
- **Epistêmica** (≥1 item de produto/lançamento, pesquisa/dado, regulação/crítica): existe pra a edição não virar só anúncio de feature — força pelo menos um ângulo de dado e um de regulação/crítica por dia.
- **De audiência**: existe porque o público tem um primário (Tech Operator/PM) e um secundário (Builder-Adjacent) com leituras diferentes — sem o constraint, a edição tenderia a convergir tudo pra "desenvolvedores".

## RADAR (STEP 4.5)

Dá um lugar pra sinal fraco ("cedo demais pra ser achado") sem forçar a barra do STEP 2 pra baixo só pra preencher espaço. Sem essa válvula de escape, pesquisa acadêmica early-stage (arXiv) tenderia a ser descartada por inteiro, já que raramente é "acionável agora".

## Checagem antibajulação (STEP 4.75)

Adicionada depois do mesmo diagnóstico do Plano de melhoria editorial: regra existir no prompt não é o mesmo que ser cumprida. É uma auto-checagem antes do STEP 5 — pergunta ao próprio modelo se a seleção está equilibrada ou só "mais fácil de justificar". É a camada de defesa mais barata (sem chamada extra de LLM) contra o gap que o revisor final (abaixo) ataca com uma segunda chamada.

## Teste final e claim_status (STEP 5)

Cada item precisa completar uma de quatro frases-molde usando só informação do título; se não completa, é descartado. Isso é o AI Gate de novo, mas para "isso é evento ou é opinião" em vez de "isso é AI ou não" — e é o motivo de manifestos bem escritos por autores credíveis ainda serem descartados (Exemplo 12 do template: "AI Should Elevate Your Thinking, Not Replace It" não completa nenhuma frase porque expressa posição, não evento). `claim_status` (confirmado/especulativo/em_andamento) existe pra garantir que o tom de "estaria"/"segundo relatos" sobreviva da classificação até o texto final — sem isso, a regra de certeza do system instruction teria que confiar só na memória do modelo dentro da mesma resposta.

## Barra mínima do main_find (fora do prompt — guard em código)

O destaque da edição (main_find) não pode ser um post do Reddit sem corroboração de outra fonte; se for, o pipeline troca automaticamente pelo primeiro quick_find elegível. Essa regra **não está no prompt** — é um guard determinístico em `pipeline.py`/`memory_store.py` (Rec. 2 do plano de melhoria, PR #38), porque o motivo que a gerou é inverificável por regra de texto: o RSS do Reddit não traz score, então "tração" não pode ser confirmada, e em 6 de 105 audits o destaque foi um post anônimo sem fonte primária. Trocar por código elimina a dependência de o modelo "lembrar" de desconfiar do Reddit.

## Revisor final em modo shadow

Depois que a curadoria monta a edição, uma segunda chamada de LLM (curta, `prompts/final_review_prompt.txt`) confere cada item publicado contra as mesmas categorias do STEP 3 (funding, panorama, opinião, não verificado, requentado, fora de escopo) e aponta até 2 candidatos fortes deixados de fora. Existe porque Editorial (2.17/5) e Reasoning (2.27/5) eram os eixos mais fracos do audit — exatamente os eixos de "a curadoria sabe a regra e não a aplica". Está em modo `shadow` (`sources_config.json` → `final_review.mode`) e não `enforce` de propósito: é a mudança de maior risco do plano — um LLM revisando outro pode errar, e em `enforce` chegaria a remover itens bons. Antes de ligar `enforce`, mede-se se o revisor concorda com o `audit_agent` (critério e método em `docs/historico/EDITORIAL_IMPROVEMENT_PLAN.md`, Rec. 1).

## Regras de voz (`prompts/system_instruction.txt`)

- **PODE/NÃO PODE + regra de certeza**: a mesma restrição de base (só título/metadados) aplicada à escrita — pode explicar o que uma coisa É, não pode inventar reação/consequência, e tem que preservar "may/reportedly/pergunta" como incerteza, nunca convertendo em afirmação.
- **Voz**: frases curtas, verbos factuais, tom de colunista — existe pra diferenciar a AYA de um agregador robótico sem cair em hype (o oposto do problema que o v3 corrigiu).
- **"→ No seu produto:"**: linha obrigatória em todo achado desde 15/11 (passo 1 do recorte PM, PR #51) — resposta concreta a "o que isso muda no produto de quem lê", nunca genérica ("fique atento às tendências" é exemplo inválido no próprio prompt).
- **Regra de idioma (PT-BR)**: glossário de o que fica em inglês (jargão técnico consagrado, nomes próprios) vs. o que é traduzido (gírias anglófonas evitáveis) — existe porque o público é brasileiro e a voz da AYA não é a de quem traduz literalmente do inglês, mas também não força tradução de termos que o leitor técnico já usa em inglês no dia a dia.
