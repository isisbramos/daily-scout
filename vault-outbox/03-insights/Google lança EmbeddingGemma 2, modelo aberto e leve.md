---
tipo: insight
criado: 2026-10-07
tags: [insight, tema-provisorio/modelos-abertos, tema-provisorio/agentes-aut-nomos, tema-provisorio/rag-e-embeddings, tema-provisorio/parcerias-enterprise-de-ia]
temas: [Editorial]
projetos: [AYA]
fonte_edicao: 199
---

# Google lança EmbeddingGemma 2, modelo aberto e leve de embedding multimodal

O Google publicou o EmbeddingGemma 2, um modelo de embedding (representação numérica de texto e imagens usada em busca e recomendação) aberto e leve, segundo o HackerNews — a notícia também apareceu no blog do DeepMind. Embeddings são a camada que permite a um sistema encontrar 'coisas parecidas' sem depender de palavras-chave exatas: é o que sustenta busca semântica, RAG (buscar trechos relevantes antes de o LLM responder) e sistemas de recomendação. A versão anterior, EmbeddingGemma, já era usada como alternativa gratuita a APIs pagas de embedding da OpenAI e Cohere. → Quem constrói busca interna, RAG ou recomendação pode rodar esse modelo localmente e cortar custo por token de embedding.
- O diferencial declarado é ser multimodal — processa texto e imagem no mesmo espaço vetorial, o que permite buscar por similaridade entre modalidades sem pipeline separado.
- Modelos de embedding abertos e leves são a peça mais fácil de substituir num stack de RAG: se o custo de API pesa, é o primeiro componente a migrar pra rodar local.
- Vale acompanhar os benchmarks de recuperação (retrieval) contra os concorrentes fechados — é o número que decide se compensa trocar.

Fonte: https://blog.google/innovation-and-ai/technology/developers-tools/embeddinggemma-2/

---
**Temas:** [[Editorial]]
**Projeto:** [[AYA]]
**Daily:** [[2026-10-07]]
