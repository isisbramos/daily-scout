---
tipo: insight
criado: 2026-11-25
tags: [insight, tema-provisorio/seguran-a-de-agentes, tema-provisorio/modelos-abertos, tema-provisorio/regula-o-de-plataformas, tema-provisorio/pesquisa-aplicada]
temas: [Editorial]
projetos: [AYA]
fonte_edicao: 248
---

# Pesquisa mostra como histórico benigno de conversa vira vetor de injeção de prompt

O ContextLure é um framework de red-teaming (teste adversarial) descrito no arXiv: o atacante observa silenciosamente conversas legítimas do agente — resultados de tarefas, restrições operacionais, preocupações do usuário — e usa essas evidências para montar injeções de prompt indiretas mais eficazes, sem precisar controlar turnos anteriores. Injeção indireta é quando instruções maliciosas chegam ao modelo por um conteúdo que ele lê no meio do fluxo (um documento, uma página, um retorno de ferramenta), não pelo que o usuário digitou. O ponto central é que o material usado no ataque é benigno: nada no histórico precisa ter sido plantado pelo atacante. Agentes que mantêm memória longa e executam ferramentas acumulam exatamente esse tipo de evidência.
- Agentes de longa duração guardam resultados de tarefas e restrições do usuário — o ContextLure mostra que esse acervo ajuda um atacante a calibrar o golpe.
- A defesa não é só filtrar entrada maliciosa: o histórico legítimo também precisa ser tratado como dado sensível.
- Vale conferir, no seu fornecedor de agente, o que fica retido entre sessões e quem consegue ler esse histórico.

Fonte: https://arxiv.org/abs/2611.31424

---
**Temas:** [[Editorial]]
**Projeto:** [[AYA]]
**Daily:** [[2026-11-25]]
