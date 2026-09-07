---
tipo: insight
criado: 2026-09-06
tags: [insight, tema-provisorio/fontes-de-dados]
temas: [Observability]
projetos: [AYA]
---

# Três fontes mortas voltam a contribuir

O dashboard apontava 6 fontes "ociosas" (0 seleções em 74 edições) com uma explicação genérica ("avalie peso/pre-filter"). Fui checar ao vivo e achei 3 causas concretas e diferentes — nenhuma era peso/competição:

- **huggingface_papers** — `papers.rss` nunca existiu de fato (404, issue aberta há anos no repo `huggingface/blog` sem resolução). Trocado pra API JSON oficial `/api/daily_papers`.
- **meta_ai_blog** — feed vivo com posts novos, mas sem `published_parsed`/`updated_parsed` reconhecível pelo `feedparser`. O fallback era timestamp `0.0`, que o filtro de recência de 24h sempre reprova (parece "de 1970"). Fallback trocado pra "agora".
- **mistral_releases** — URL apontava pro changelog de um repo GitHub que a Mistral não usa mais (post mais recente: 535 dias). Achei o RSS oficial via `<link rel=alternate>` em `mistral.ai/news/` — posts de 13-26 dias.

**Aprendizado:** "fonte ociosa" pode ter causas totalmente diferentes por trás do mesmo sintoma — vale sempre testar o feed ao vivo (status HTTP + idade do post mais recente) antes de assumir que é peso/critério editorial.

`ethan_mollick` e `qwen_blog` ficaram sem fix: o primeiro posta a cada 1-2 semanas (incompatível com janela de 24h, decisão de produto pendente); o segundo já usa a URL oficial correta, só está desatualizado do lado deles.

---
**Temas:** [[Observability]]
**Projeto:** [[AYA]]
**Daily:** [[2026-09-06]]
