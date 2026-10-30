# diagram-db · documentación

Documentación del paquete `diagram-db`. Todo lo específico de esta herramienta
vive aquí; las convenciones comunes del monorepo están en
[docs/](../../../docs/README.md).

## Contenido

| Documento | Contenido |
| --- | --- |
| [README](../README.md) | Requisitos, instalación, uso del CLI, formato del `spec.md` y API |
| [CHANGELOG](../CHANGELOG.md) | Historial de versiones |
| [examples/](../examples/) | Specs de ejemplo: `tienda`, `biblioteca` y `prestamos_taveras` |
| [landing/](../landing/) | Sitio estático con el playground que ejecuta el analizador en el navegador |

## Cómo se organiza el paquete

```text
packages/diagram-db/
├── pyproject.toml        # metadata, dependencias, CLI, ruff y pytest
├── src/diagram_db/       # paquete instalable
├── tests/                # pytest
├── examples/             # specs de ejemplo incluidos en el sdist
├── landing/              # sitio estático; vendor/diagram_db copia src/diagram_db
└── docs/                 # esta documentación
```

## Documentar cambios

- Un cambio de comportamiento actualiza el [README](../README.md) y el
  [CHANGELOG](../CHANGELOG.md) en la misma pull request.
- La versión del CHANGELOG debe coincidir con `diagram_db.__version__` y con el
  tag `diagram-db-vX.Y.Z` que dispara la publicación
  ([versionado](../../../docs/versionado.md)).
- Si se modifica `src/diagram_db/`, hay que sincronizar la copia del playground:
  `cp src/diagram_db/*.py landing/vendor/diagram_db/`. La CI y el hook lo
  verifican.
