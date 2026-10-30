# pulsar · documentación

Documentación del paquete `pulsar` (distribución `pulsar-psr`). Todo lo
específico del formato y de la librería vive aquí; las convenciones comunes del
monorepo están en [docs/](../../../docs/README.md).

## Contenido

| Documento | Contenido |
| --- | --- |
| [README](../README.md) | Especificación del formato `.psr`, instalación, CLI `psr` y uso como librería |
| [CONTRIBUTING](../CONTRIBUTING.md) | Cómo proponer cambios al formato y a la librería |
| [CHANGELOG](../CHANGELOG.md) | Historial de versiones |
| [ejemplo.psr](../ejemplo.psr) | Documento de ejemplo usado por los tests y el smoke test del CLI |
| [landing/](../landing/) | Sitio estático del formato con playground |

## Cómo se organiza el paquete

```text
packages/pulsar/
├── pyproject.toml        # metadata, CLI, ruff; el módulo se empaqueta con py-modules
├── pulsar.py             # implementación completa (lexer, parser, validación, CLI)
├── __main__.py           # entrada para python -m pulsar
├── tests/                # unittest
├── landing/              # sitio estático; landing/pulsar.py copia pulsar.py
├── Dockerfile            # imagen con el CLI instalado
└── docs/                 # esta documentación
```

## Documentar cambios

- Un cambio en el formato o en la API actualiza el [README](../README.md) y el
  [CHANGELOG](../CHANGELOG.md) en la misma pull request.
- La versión del CHANGELOG debe coincidir con `pulsar.__version__` y con el tag
  `pulsar-vX.Y.Z` que dispara la publicación
  ([versionado](../../../docs/versionado.md)).
- Si se modifica `pulsar.py`, hay que sincronizar la copia del playground:
  `cp pulsar.py landing/pulsar.py`. La CI lo verifica.
