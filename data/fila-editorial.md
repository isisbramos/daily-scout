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

## 2026-11-17 — edição #240
Tema/achado: o item do pacto global (COP31) saiu com uma linha "No seu produto" que falava de operação no Brasil exigindo transparência energética — contexto que o título não traz. Em geral, a edição soa técnica demais (papers, chips, modelos de fronteira).
Por que não bateu: a AYA é para quem constrói COM IA e usa IA no dia a dia para ajudar o negócio, não para quem constrói IA.
Critério novo: tratado no passo 1.1 (PR da branch `feat/linha-no-seu-trabalho`): linha vira "→ No seu trabalho:" e o prompt proíbe inventar contexto. **Ainda aberto:** o passo 2 (critério de curadoria no STEP 2) deve usar a mesma redação de leitor ("quem usa IA no trabalho"), e vale checar o peso das fontes (arxiv_ai e huggingface_papers têm o maior weight, 1.3).
