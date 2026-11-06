---
tipo: insight
criado: 2026-11-06
tags: [insight, tema-provisorio/privacidade-em-ferramentas-de-c-digo, tema-provisorio/modelos-abertos, tema-provisorio/ado-o-empresarial-de-ai, tema-provisorio/resist-ncia-a-data-centers]
temas: [Editorial]
projetos: [AYA]
fonte_edicao: 229
---

# Claude Code estaria enviando endereço de e-mail do usuário para sites visitados

Uma issue aberta no repositório do Claude Code no GitHub, com alta tração no HackerNews (1.342 pontos, 423 comentários), relata que a ferramenta de código da Anthropic estaria enviando o endereço de e-mail do usuário para sites que o agente visita durante a execução. O Claude Code é o agente de linha de comando da Anthropic para tarefas de programação — ele acessa páginas web para consultar documentação e referências enquanto trabalha. Se confirmado, o comportamento expõe um identificador pessoal em requisições que deveriam ser anônimas do ponto de vista do site visitado. A discussão no HackerNews indica que desenvolvedores estão tratando o caso como problema de privacidade concreto, não como detalhe técnico menor. → Quem usa Claude Code em ambiente corporativo deve verificar se o e-mail exposto é o corporativo e revisar políticas de proxy ou isolamento de rede antes de rodar o agente em projetos sensíveis.
- A issue está no repositório oficial da Anthropic no GitHub — é o canal onde a própria empresa acompanha relatos de bug, então a discussão tende a gerar resposta oficial ou correção em release futura.
- O ponto prático não é só o vazamento em si: se o e-mail vai junto em requisições HTTP, sites visitados pelo agente podem correlacionar atividade de desenvolvimento a uma identidade específica.
- Vale acompanhar se a Anthropic vai tratar como bug (correção pontual) ou como comportamento esperado documentado — a diferença muda o que empresas precisam ajustar nas próprias políticas de uso.

Fonte: https://github.com/anthropics/claude-code/issues/107757

---
**Temas:** [[Editorial]]
**Projeto:** [[AYA]]
**Daily:** [[2026-11-06]]
