# Marca e visual

> last-reviewed: 2026-11-15 · Resumo do sistema de marca da AYA. Fonte detalhada (specs técnicas, SVGs, histórico decisão por decisão): `~/Documents/isis-brain/10-projetos/newsletter-aya/brand-system/SYSTEM.md` e `Brand Rebrand Registry.md` no vault — leia-os antes de tocar em qualquer asset, template ou copy visual. Este arquivo é o resumo que fica no repo público; o vault tem o detalhe e o porquê completo.

## Regra de marca (vale pra qualquer texto ou asset)

**AYA é uma entidade editorial autônoma — a marca não orbita a fundadora.** Toda comunicação pública (site, e-mail, social) opera com a AYA como sujeito, nunca com a pessoa por trás dela em primeiro plano. Isso significa: nunca coloque história pessoal, biografia ou a origem do nome "AYA" em nada versionado neste repo, que é público. Se precisar desse contexto, ele vive só no vault.

## Naming

A marca pública é **AYA**, só isso — sem descritor. "Daily Scout", "AYA's Daily" e "AYA's Daily Scout" são nomes legados (do repo técnico e de arquivos antigos) e nunca devem aparecer em texto novo, público ou interno.

Tagline oficial: **"curadoria de novidades sobre IA. todo dia."** — lowercase em "todo dia" intencional (postura anti-hype tipográfica, não erro de digitação).

## Sistema visual dual

Dois elementos com papéis diferentes, que não se confundem:

- **Vesica piscis = marca sistêmica (operacional).** É o olho/amêndoa horizontal (proporção 2.8:1, sem ponto central — de propósito, pra não ler como íris, CBS Eye ou Sauron). Aparece em **todo touchpoint**: favicon, header da newsletter diária, footer, loading/error state, nav do site. Tem motion própria (blink + scan-line) nos canais que suportam; em e-mail (Gmail/Outlook), cai pra GIF ou PNG estático.
- **Persona = rosto cerimonial.** Mulher negra, cabelo cacheado preto-e-verde, traje cyber field-operator, interagindo com HUD/holograma verde — vibe cyberpunk-editorial **realista, não anime**. Aparece em só ~25% dos touchpoints, nunca anima, nunca é sobreposta pela vesica, nunca aparece sem o wordmark "AYA" por perto, e **nunca vai na newsletter diária** — hoje aparece na assinatura do e-mail (`persona-face-circular.jpg`, via `AYA_AVATAR_URL` em `pipeline.py`), no hero do site e em contextos especiais (about, press kit, OG card e capa de edição especial).

**A persona anime foi descartada.** A primeira versão do avatar (usada até 21/06/2026) era uma persona anime/estilizada com estética eurocêntrica padrão — substituída pela persona field-operator realista acima, decidida em 24/05/2026. Nenhum asset da versão anime deve voltar a ser usado.

## Onde cada uma aparece

| Touchpoint | Vesica | Persona |
| --- | --- | --- |
| Favicon / app icon | ✅ | — |
| Header da newsletter diária | ✅ | — |
| Footer / assinatura do e-mail | ✅ | ✅ (face circular) |
| Loading / error state | ✅ | — |
| Hero do site, about, press kit | ✅ | ✅ |
| OG card padrão / social diário | ✅ | — |
| OG card especial / capa de edição especial | ✅ | ✅ |

Regra heurística pra touchpoint não listado: vesica é o default; persona só entra em momento de apresentação cerimonial, com tempo de leitura ≥ 5s.

## Paleta

Tokens canônicos (extraídos da landing, não inventados):

| Token | Hex | Uso |
| --- | --- | --- |
| Ink | `#060A09` | Background near-black |
| Ink soft | `#0E1612` | Surfaces secundárias |
| Cream | `#F4F2EA` | Texto primário, outline da vesica |
| Green primary | `#1FE070` | Scan-line, CTA, indicador "transmitindo" |
| Green soft | `#4FAE74` | Accent de serif, hover |
| Mute | `#6B7370` | Metadata, timestamps |

**Atenção:** `templates/email.html` hoje usa uma paleta diferente desses tokens (`#0F172A`/`#22C55E`/`#334155`/`#94A3B8` — tons slate + verde, não os hex exatos acima). Antes de alterar cor em qualquer asset, confirme com a Isis se isso é uma adaptação deliberada pra e-mail ou drift a corrigir — não assuma nenhum dos dois.

## Anti-padrões inegociáveis

- Nunca usar "Daily Scout" / "DAILY AI SCOUT" / "AYA's Daily Scout" em texto novo.
- Persona nunca anima, nunca aparece sem o wordmark, nunca vai na newsletter diária, nunca usa foto diferente da source canônica, não é anime nem estilizada.
- Vesica nunca é preenchida (sempre outline) e nunca tem ponto central.
- Sem símbolos de cultura específica (Adinkra, japonesa, etc.) em nenhum dos dois elementos — o registro visual da AYA é construído, não emprestado de uma cultura real.
- Nunca colocar a fundadora no centro da narrativa pública.
- Nunca expor qual modelo de LLM a AYA usa (regra editorial, não de marca, mas reforça o mesmo princípio de a AYA ser a protagonista).
