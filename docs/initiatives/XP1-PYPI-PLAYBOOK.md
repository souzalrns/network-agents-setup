# XP1 — Playbook de publicação no PyPI (planwright · skill-scout · auditron)

Levar os três pacotes `oss/` ao PyPI, para qualquer pessoa fazer
`pip install planwright`. Por **Trusted Publishing** (OIDC): **sem tokens nem
secrets** no repo — o GitHub Actions prova a identidade ao PyPI com um id-token
de curta duração. O workflow é `.github/workflows/publish-pypi.yml`.

> **Padrão ouro, decisão do maestro:** o 1.º publish de cada pacote é um passo
> **deliberado** (precisa do setup no PyPI, abaixo). O workflow fica **inerte**
> até existir uma tag `<pacote>-v*`. Nada vai para o PyPI sozinho.

## 0. Prontidão (verificado 2026-10-10)

| Pacote | Nome no PyPI | Estado | `build`+`twine check` | Licença | CHANGELOG |
|--------|--------------|--------|-----------------------|---------|-----------|
| planwright | `planwright` | **livre** (HTTP 404) | ✅ PASSED | MIT | ✅ |
| skill-scout | `skill-scout` | **livre** (HTTP 404) | ✅ PASSED | ver `LICENSE` | ✅ |
| auditron | `auditron` | **livre** (HTTP 404) | ✅ PASSED | ver `LICENSE` | ✅ |

Reconfirmar a disponibilidade do nome antes do setup:

```bash
for n in planwright skill-scout auditron; do
  echo "$n -> HTTP $(curl -s -o /dev/null -w '%{http_code}' https://pypi.org/pypi/$n/json)"
done   # 404 = livre
```

## 1. Setup no PyPI — uma vez por pacote (só o maestro; precisa de conta PyPI)

Trusted Publishing para um projeto que **ainda não existe** usa um *pending
publisher*. Em <https://pypi.org/manage/account/publishing/>, **Add a pending
publisher** e preencher, por cada pacote:

| Campo | Valor |
|-------|-------|
| PyPI Project Name | `planwright` (e depois `skill-scout`, `auditron`) |
| Owner | `souzalrns` |
| Repository name | `network-agents-setup` |
| Workflow name | `publish-pypi.yml` |
| Environment name | `pypi` |

Opcional mas recomendado: em **Settings → Environments → `pypi`** do repo, pôr
uma *required reviewer* (o maestro) — assim cada publish fica à espera de um
clique, além da tag.

## 2. Ação de publish fixada por SHA (convenção do repo)

Já fixada: `pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33`
(**v1.14.2**, tip de `release/v1`). O semgrep do SEC-2 **bloqueia** refs mutáveis,
por isso o SHA é obrigatório. Para subir de versão no futuro, resolver o SHA novo
e trocar a linha `uses:` (mantendo o comentário `# vX.Y.Z`):

```bash
git clone --filter=blob:none https://github.com/pypa/gh-action-pypi-publish.git /tmp/ghapp
git -C /tmp/ghapp tag --sort=-v:refname | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | head -1   # última versão
git -C /tmp/ghapp rev-list -n1 <tag>                                                        # o SHA
```

## 3. Lançar uma versão (por pacote)

1. **Garantir a `main` verde** (é de onde se corta a tag).
2. Bumpar a versão em `oss/<pacote>/pyproject.toml` **e** no `__init__.py`, e
   abrir a entrada no `oss/<pacote>/CHANGELOG.md`. Commit via PR, merge.
3. Cortar e empurrar a tag **por-pacote** (a versão TEM de bater com o pyproject
   — o workflow falha fechado se divergir):

   ```bash
   git tag planwright-v0.3.0 && git push origin planwright-v0.3.0
   ```

4. O workflow `publish-pypi.yml` corre: escolhe o pacote pela tag, valida a
   versão, `build` + `twine check --strict`, e publica por OIDC. (Com a tag
   `skill-scout-v0.1.0` publica o skill-scout; `auditron-v0.1.0`, o auditron.)
5. **Verificar**:

   ```bash
   pip install planwright==0.3.0 && python -c "import planwright; print('ok')"
   ```

Publicar à mão (sem tag), depois do setup: **Actions → Publish to PyPI → Run
workflow**, escolher o pacote.

## 4. Esquema de tags e versões

- Tags **por-pacote**: `planwright-vX.Y.Z`, `skill-scout-vX.Y.Z`,
  `auditron-vX.Y.Z`. Cada pacote versiona-se sozinho (SemVer).
- A tag genérica `vX.Y.Z` continua a ser do `release.yml` (GitHub Release do
  monorepo) e **não** publica no PyPI — são coisas diferentes, sem colisão.

## 5. Primeiras versões sugeridas

`planwright-v0.3.0` · `skill-scout-v0.1.0` · `auditron-v0.1.0` — exatamente as
versões já nos `pyproject.toml`, todas com build + twine verdes.

## 6. Rollback

No PyPI **não se apaga** uma versão para a republicar — só se faz **yank**
(esconde-a dos resolvers novos, mantém quem já a fixou). Um problema corrige-se
**avançando** a versão (0.3.0 → 0.3.1), nunca reutilizando uma. Por isso o 1.º
publish de cada pacote merece um olhar antes da tag.

## 7. O que falta (fora deste playbook)

- O setup do PyPI (§1) e o SHA-pin (§2) são do maestro — precisam da conta PyPI
  e de rede para o github.com, ambos fora deste ambiente.
- Depois do 1.º publish, considerar um `README` com badge de versão e o
  `pip install` no topo de cada pacote (pequeno, cosmético).
