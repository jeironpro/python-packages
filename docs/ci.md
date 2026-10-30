# CI selectiva

El repositorio tiene **una sola puerta de entrada** (`.github/workflows/ci.yml`)
y un workflow reutilizable por paquete (`ci-<paquete>.yml`). Así el estado de la
PR es único y, a la vez, cada paquete mantiene sus propios jobs.

## Cómo funciona

1. El job `cambios` compara los archivos tocados por la PR con los patrones de
   cada paquete.
2. Solo se invoca el workflow reutilizable de los paquetes afectados. Si la PR
   no toca un paquete, sus jobs no se ejecutan.
3. Los archivos compartidos (este workflow, `ci-<paquete>.yml`,
   `.pre-commit-config.yaml` y `.github/scripts/`) activan **todos** los
   paquetes, porque un cambio ahí puede romper cualquiera.
4. El job `higiene` ejecuta pre-commit sobre todo el repositorio y siempre corre.

## Qué se ejecuta por paquete

| Paquete | Lint (ruff) | Tests | Build + metadatos | Comprobaciones propias |
| --- | --- | --- | --- | --- |
| diagram-db | `ruff check` y `ruff format --check` | `pytest` en Python 3.10–3.13 con Graphviz instalado | sdist + wheel, `twine check --strict` y smoke test del wheel instalado | `landing/vendor/diagram_db` idéntico a `src/diagram_db`, assets de la landing existentes |
| pulsar | `ruff check` y `ruff format --check` | `unittest` en Python 3.10–3.14 + smoke test del CLI | sdist + wheel y `twine check --strict` | `landing/pulsar.py` idéntico a `pulsar.py`, assets de la landing existentes |

Ruff usa la configuración del `pyproject.toml` más cercano a cada archivo, así
que cada paquete conserva su `line-length` y sus reglas aunque los hooks sean
comunes.

## Equivalente local

```bash
pre-commit run --all-files                     # higiene, lint y formato

cd packages/diagram-db && pytest               # tests
cd packages/pulsar && python -m unittest discover -s tests -v

cd packages/<paquete> && python -m build       # sdist + wheel
```

## Añadir un paquete

1. Crear `packages/<paquete>/` con su `pyproject.toml`, código, `tests/`,
   `docs/` y `CHANGELOG.md`.
2. Añadir `ci-<paquete>.yml` con `on: workflow_call` y los jobs del paquete.
3. Añadir el patrón de rutas del paquete al job `cambios` de `ci.yml` y una
   llamada al workflow reutilizable.
4. Añadir `release-<paquete>.yml` con el disparador `tags: ["<paquete>-v*"]`.
5. Registrar el paquete en este documento, en `docs/versionado.md`, en
   `docs/README.md` y en la tabla del `README.md` raíz.
6. Configurar el publisher de PyPI para el nuevo workflow (ver
   [versionado.md](versionado.md)).

## Checks obligatorios

Si se activan checks obligatorios en `main`, marca solo los jobs que siempre
existen (`higiene` y el job `cambios`). Los jobs de un paquete que no cambia
quedan en `skipped`, que no bloquea la PR.
