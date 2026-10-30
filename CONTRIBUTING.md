# Contribuir

El repositorio se trabaja **por ticket, en ramas individuales y mediante pull
requests**. Nada se empuja directamente a `main`.

## 1. Crear la rama

Siempre desde `main` actualizado:

```bash
git checkout main && git pull
git checkout -b <prefijo>/<categoria>
```

Prefijos válidos: `feature`, `bugfix`, `fix`, `hotfix`, `release`, `docs`,
`refactor`, `test`, `chore`, `ci`. La categoría va en minúsculas y separada por
guiones: `feature/version-por-paquete`, `ci/ejecuciones-selectivas`.

## 2. Implementar y verificar

- Los tests del paquete tocado deben pasar en local antes de abrir la PR.
- `pre-commit run --all-files` debe pasar sin cambios pendientes.
- Un cambio de comportamiento actualiza el `CHANGELOG.md` del paquete.

## 3. Commit

Formato: `<prefijo>/<categoria>: <mensaje>`, el mismo que el título de la PR.

- Mensaje en minúsculas (salvo nombres propios), en imperativo y sin punto
  final. Resume el conjunto de la rama, no un cambio suelto.
- Ejemplo: `feature/monorepo-base: añade convenciones y ci selectiva`

```bash
git add .
git commit -m "feature/monorepo-base: añade convenciones y ci selectiva"
```

**Sin co-autores.** Ni los commits, ni el título o cuerpo de la PR, ni el commit
de squash hacia `main` llevan trailers `Co-Authored-By`, `Signed-off-by` de
terceros ni atribución a herramientas. El workflow `Sin co-autores` falla si
aparecen.

## 4. Pull request

```bash
gh pr create --base main --title "<prefijo>/<categoria>: <mensaje>" --body "<descripción>"
```

La descripción sigue la plantilla de `.github/pull_request_template.md`: qué
cambia, qué paquetes afecta y qué se comprobó.

## 5. CI y merge

- Si la CI falla, se corrige **en la misma rama con un commit nuevo** (nunca
  `amend` sobre commits ya empujados) y se vuelve a verificar.
- Con la CI en verde, se integra con squash y se borra la rama:

```bash
gh pr merge --squash --delete-branch
```

El repositorio solo permite squash merge, con el título de la PR como asunto y
su cuerpo como descripción del commit en `main`.

## Issues

Las issues son compartidas por todos los paquetes. Al abrir una, indica el
paquete en el título y añade la etiqueta correspondiente:

- `package:diagram-db`
- `package:pulsar`
- `infra` para CI, documentación compartida o tooling del monorepo

## Publicación

Las releases se disparan con tags `<paquete>-vX.Y.Z`; el detalle está en
[docs/versionado.md](docs/versionado.md). No se publica desde una rama.
