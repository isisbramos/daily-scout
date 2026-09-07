---
tipo: decisao
criado: 2026-09-06
tags: [decisao]
temas: [Editorial]
projetos: [AYA]
---

# Aperta critério de sinal de mercado

O `audit_agent` apontou a mesma falha em 8 edições diferentes (093-162): itens sem novidade real de produto/estratégia passando na curadoria só por parecerem "de negócio" — resultado financeiro (Cambricon, MiniMax, Z.ai), hardware fraco (T-Head), roundup genérico, e funding round de empresa de referência (OpenAI $7B) sem nenhuma info além do valor.

Causa raiz: o critério "sinal de mercado" era vago o bastante pra qualquer notícia com cara de negócio se encaixar, e a exceção pra funding round de OpenAI/Anthropic/DeepMind virou passe livre em vez de só reduzir a barra de novidade exigida.

**Mudança em `prompts/curation_template.txt`:** critério de sinal de mercado agora exclui explicitamente resultado financeiro sem novidade e panorama de mercado sem evento de um player específico; dois anti-signals novos (resultado financeiro, roundup genérico); exceção de funding round deixa de ser passe livre.

Efeito só aparece na próxima edição gerada — verificar via dashboard (sparkline de score, hipóteses recorrentes) se as duas hipóteses somem.

---
**Temas:** [[Editorial]]
**Projeto:** [[AYA]]
**Daily:** [[2026-09-06]]
