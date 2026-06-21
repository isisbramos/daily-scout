# Inventário — Persona antiga (aya-avatar.png)

> Gerado em 2026-05-24 no P1 do rebrand visual AYA.
> **NÃO substitua nada ainda** — este doc é só inventário.
> A persona nova (field-operator negra, cyberpunk-editorial) será fornecida pela Isis manualmente.
> Executar a substituição em P2 (landing) e P3 (newsletter template).

---

## Arquivo físico da persona antiga

| Caminho | Tamanho | Dimensões | Nota |
|---|---|---|---|
| `assets/aya-avatar.png` | 6.4 MB | 2048×2048 RGBA | **Arquivo canônico** — o que os HTMLs referenciam |
| `aya-avatar.png` (root) | 6.4 MB | 2048×2048 RGBA | Duplicata na raiz — mesma imagem |

> Persona antiga: mulher anime / mixed-ambiguous, criada via Nano Banana em 2026-05-20.
> Spec para substituição: SYSTEM.md seção 6.

---

## Ocorrências por arquivo

### `index.html` (landing principal — assineaya.com.br)

| Linha | Tipo | Uso atual | O que substituir |
|---|---|---|---|
| 14 | `<meta property="og:image">` | OG card do site | `https://assineaya.com.br/brand-assets/og-default.png` (já gerado em P1) |
| 21 | `<meta name="twitter:image">` | Twitter/X card | `https://assineaya.com.br/brand-assets/og-default.png` |
| 24 | `<link rel="icon" type="image/png">` | Favicon (persona como favicon!) | Remover — P2 já troca por `brand-assets/favicon.svg` + `favicon.ico` |
| 1320 | `<img src="./assets/aya-avatar.png">` | Hero section — imagem principal, `alt="AYA — AI correspondent"` | Crop A (full body 9:16) da nova persona |
| 1354–1361 | `.meet-aya-portrait` com `<img>` | Seção "conheça a AYA" — portrait com overlay animado | Crop B (mid-shot 4:5) ou Crop A |

CSS relacionado no `index.html`:
- Linha 337: `.hero-visual` — container do hero (class `hero-portrait`)  
- Linhas 514–549: `.meet-aya-portrait`, `.portrait-overlay`, `.portrait-caption`, `.portrait-transmission` — bloco visual da seção "meet AYA"

### `about/index.html`

| Linha | Tipo | Uso atual | O que substituir |
|---|---|---|---|
| 13 | `<meta property="og:image">` | OG card da página About | `https://assineaya.com.br/brand-assets/og-default.png` |
| 17 | `<link rel="icon" type="image/png">` | Favicon (persona como favicon!) | Remover — trocar por `../brand-assets/favicon.svg` |
| 801 | `<img src="../assets/aya-avatar.png">` | Retrato na página About, `alt="AYA portrait"` | Crop A (full body) ou Crop B (mid-shot) |

### `archive/index.html`

| Linha | Tipo | Uso atual | O que substituir |
|---|---|---|---|
| 13 | `<meta property="og:image">` | OG card do arquivo | `https://assineaya.com.br/brand-assets/og-default.png` |
| 17 | `<link rel="icon" type="image/png">` | Favicon (persona como favicon!) | Remover — trocar por `../brand-assets/favicon.svg` |

### `templates/email.html` (Jinja2 — newsletter diária)

| Linha | Tipo | Uso atual | O que substituir |
|---|---|---|---|
| 272 | `<img src="{{ aya_avatar_url \| default('...') }}">` | Header do email | P3 substitui por `vesica-animated.gif` / `vesica-static.png` via GIF+MSO pattern |

O default hardcoded aponta para:
`https://raw.githubusercontent.com/isisbramos/daily-scout/main/aya-avatar.png`

### `pipeline.py` (sistema de geração)

| Linha | Tipo | Uso atual | O que fazer |
|---|---|---|---|
| 52–54 | `AYA_AVATAR_URL` env var | URL da avatar passada pro template do email | Atualizar default para URL da nova persona após P3 |
| 451 | `aya_avatar_url=AYA_AVATAR_URL` | Passada pro template Jinja | Acompanha mudança no template |

### `test_dry_run.py`

| Linha | Tipo | Uso atual | O que fazer |
|---|---|---|---|
| 155 | `aya_avatar_url=` hardcoded | Mock para testes dry-run | Atualizar URL após P3 |

---

## Resumo das ações pendentes por fase

| Fase | Arquivos a tocar | Ação |
|---|---|---|
| **P2** | `index.html`, `about/index.html`, `archive/index.html` | Substituir `<img>` da persona por placeholder + trocar favicon + trocar OG meta tags |
| **P3** | `templates/email.html` | Substituir `<img>` da persona por vesica GIF/PNG pattern |
| **Após persona nova** | `assets/` | Adicionar crops A, B, C, D da nova persona; atualizar `pipeline.py` + `test_dry_run.py` |

---

## URL canônica atual da persona antiga

```
https://isisbramos.github.io/daily-scout/assets/aya-avatar.png
https://raw.githubusercontent.com/isisbramos/daily-scout/main/aya-avatar.png
```

Ambas apontam pra mesma imagem. Continuarão funcionando até o rebrand ir ao ar.
Após P2 + deploy, serão obsoletas (OG cards atualizados apontam pra og-default.png).
