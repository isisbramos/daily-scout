---
tipo: insight
criado: 2026-11-15
tags: [insight, tema-provisorio/seguran-a-em-plataformas-de-ai, tema-provisorio/modelos-de-pesos-abertos, tema-provisorio/caso-nvidia, tema-provisorio/conte-do-gerado-por-ai]
temas: [Editorial]
projetos: [AYA]
fonte_edicao: 238
---

# Apps feitos no Lovable expõem passaportes e mais de 200 mil mensagens privadas

Uma pesquisa publicada no site crissyfield.de e em destaque no HackerNews (898 pontos, 342 comentários) encontrou dados sensíveis expostos em aplicações construídas com o Lovable, plataforma que gera apps a partir de descrições em linguagem natural. Entre os dados vazados estão detalhes de passaporte e mais de 200 mil mensagens privadas. O caso aponta para um padrão de risco específico das plataformas de 'vibe coding': quando o app é gerado automaticamente, configurações de banco de dados e controle de acesso podem ficar no padrão aberto sem que o criador perceba. → Quem publicou app feito no Lovable deve auditar agora as regras de acesso do backend e verificar se dados de usuários estão acessíveis sem autenticação.
- O problema não é o modelo gerar código errado, e sim a configuração de infraestrutura que vem por padrão nessas plataformas — banco de dados acessível publicamente é um erro recorrente em apps gerados sem revisão.
- A escala do vazamento (mais de 200 mil mensagens) sugere que os apps afetados já estavam em produção com usuários reais, não em ambiente de teste.
- Vale acompanhar se o Lovable vai publicar comunicado oficial e se outras plataformas de geração de app vão revisar os padrões de segurança que entregam por default.

Fonte: https://www.crissyfield.de/research/lovable-en/

---
**Temas:** [[Editorial]]
**Projeto:** [[AYA]]
**Daily:** [[2026-11-15]]
