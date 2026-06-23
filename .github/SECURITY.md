# Segurança — Daily Scout (AYA)

Proteções de dependências e segredos do repositório.

## Segredos usados

O pipeline depende dos seguintes secrets (configurados em **Settings → Secrets and variables → Actions**):

| Secret | Uso |
| --- | --- |
| `DEEPSEEK_API_KEY` | Curadoria/redação via API DeepSeek |
| `BUTTONDOWN_API_KEY` | Envio da newsletter (Buttondown) |
| `FEEDBACK_BASE_URL` | URL base dos links de feedback |
| Credenciais do Google Sheets | Leitura de fontes / planilhas |

Esses valores **nunca** devem aparecer em commits, logs ou artifacts. Use sempre `secrets.*` nos workflows.

## Atualização automática de dependências

[`dependabot.yml`](dependabot.yml) monitora semanalmente (segunda, 06:00 BRT):

- **pip** — `requirements.txt` na raiz
- **github-actions** — versões das actions nos 4 workflows

Atualizações de patch/minor do Python são agrupadas num único PR para reduzir ruído.

## Auditoria de vulnerabilidades

[`workflows/security.yml`](workflows/security.yml) roda `pip-audit` contra `requirements.txt`:

- semanalmente (segunda, 06:00 UTC)
- em PRs que alteram `requirements.txt`
- sob demanda (`workflow_dispatch`)

É um workflow **isolado** do `daily-scout.yml`: uma vulnerabilidade detectada gera um job vermelho de aviso, mas **não bloqueia o envio diário da newsletter**.

## Secret scanning (configuração na UI — não é código)

GitHub secret scanning e push protection precisam ser habilitados nas configurações do repositório:

1. Vá em **Settings → Code security and analysis** (ou **Security → Code security**).
2. Habilite **Secret scanning**.
3. Habilite **Push protection** — bloqueia commits que contenham um segredo conhecido *antes* do push.
4. (Recomendado) Habilite **Dependabot alerts** e **Dependabot security updates** para receber PRs automáticos de correção de vulnerabilidades.

> Em repositórios **públicos** essas opções são gratuitas. Em repositórios **privados**, secret scanning exige GitHub Advanced Security. Se este repo for privado e não tiver GHAS, o `pip-audit` + Dependabot já cobrem o essencial.

## Como reportar

Encontrou um problema de segurança? Abra uma issue privada ou um Security Advisory em **Security → Advisories**.
