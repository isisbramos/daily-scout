---
tipo: insight
criado: 2026-11-03
tags: [insight, tema-provisorio/agentes-de-c-digo, tema-provisorio/open-source-de-ai, tema-provisorio/economia-de-modelos-chineses, tema-provisorio/regula-o-e-pol-tica-de-ai]
temas: [Editorial]
projetos: [AYA]
fonte_edicao: 226
---

# Nvidia publica auto-ontology open source para estruturar dados de agentes

A Nvidia publicou no GitHub o auto-ontology, projeto open source que apareceu no HackerNews com 194 pontos e 65 comentários. Ontologia, no contexto de dados, é a camada que define quais entidades existem num domínio e como elas se relacionam — é o que permite um agente de AI consultar dados sem precisar adivinhar o esquema a cada pergunta. A publicação sinaliza que a Nvidia está mirando a camada de organização de dados para agentes, não só o hardware que roda os modelos. → Desenvolvedores que constroem agentes sobre bases internas podem testar o projeto como alternativa a montar ontologia à mão antes de plugar um LLM nos dados.
- O repositório é público e o projeto é open source — dá para clonar e avaliar o escopo antes de decidir se vale integrar ao pipeline de dados.
- A camada de ontologia é justamente onde agentes costumam falhar em produção: sem definição explícita de entidades, o modelo inventa relações que não existem no banco.
- Vale acompanhar se a Nvidia vai publicar benchmarks de acurácia em consulta a dados reais, ou se o projeto fica só como utilitário de geração de esquema.

Fonte: https://github.com/NVIDIA/auto-ontology

---
**Temas:** [[Editorial]]
**Projeto:** [[AYA]]
**Daily:** [[2026-11-03]]
