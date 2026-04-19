## Insight — 25 março 2026

**O que eu estava tentando fazer**
Corrigir o tom de voz da Aya no Daily Scout. A edição #003 saiu com hallucination pesada (inventou contexto sobre Sora que não estava no input) e sensacionalismo ("reviravolta", "choque", "ganhos massivos") — apesar de já ter um prompt v2 com few-shots, positive-only framing, e constraints por campo.

**O que mudou**
Descobri que guardrails textuais dentro do prompt não funcionam com o Gemini Flash em modo JSON. O modelo prioriza gerar JSON válido, não meta-cognição sobre tom. Listar 20 palavras proibidas (negative priming) ou pedir uma "checklist de revisão" não tem efeito porque o Flash não faz self-review — ele gera tokens sequencialmente.

A solução foi trocar de abordagem: em vez de tentar convencer o modelo com texto, construí defesas estruturais em 5 camadas:
1. System instruction separada (pesa mais no attention window que texto no user prompt)
2. Temperature 0.0 (elimina variação criativa)
3. Pydantic response_schema (structured output — o modelo valida contra um schema tipado)
4. Recency bias: constraint final posicionado logo antes dos dados
5. validate_tone() — regex pós-processamento que rejeita output com hype e força retry

Mas a virada mais importante veio na v3.1. A v3 corrigiu a hallucination mas matou o contexto — o body ficou repetindo o título. O pêndulo foi longe demais. O unlock real foi criar uma régua explícita de PODE/NÃO PODE: o modelo PODE explicar o que algo é e por que importa pro leitor, NÃO PODE inventar reações, consequências ou qualificar intensidade. Essa distinção — explicar vs inventar — é onde mora o tom editorial.

**Como isso muda meu processo**
- Prompt engineering pra modelos menores (Flash, Haiku) precisa ser structural, não conversational. Regras no corpo do prompt são sugestões; system instructions, schemas e pós-processamento são enforcement.
- O ciclo de calibração de tom não é v1 → v2 → pronto. É v1 → v2 → v3 (overcorrigiu) → v3.1 (acertou). A overcorreção é parte do processo — o ponto ótimo aparece quando você erra pros dois lados.
- Pós-processamento com heurísticas (regex) é uma safety net barata e eficaz. Não substitui o prompt, mas pega o que escapa.

**O que ainda está aberto**
O validate_tone() é uma blocklist estática. Conforme o Flash encontrar novas formas de sensacionalismo (e vai), preciso expandir os patterns. Seria possível usar um segundo LLM call como "editor" que avalia o tom? Custo vs benefício?
A temperatura 0.0 elimina variação — mas a newsletter precisa de alguma variação entre edições pra não soar robótica. Qual o sweet spot? 0.1? 0.15?

**Semente de post**
Passei 3 versões tentando domar um modelo de IA com instruções cada vez mais elaboradas. Ele ignorou todas. Aí parei de pedir e comecei a construir cercas. Funcionou.
