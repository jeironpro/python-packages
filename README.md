# python-packages

Monorepo de los paquetes Python de [jeironpro](https://github.com/jeironpro).
Cada paquete vive en `packages/` y conserva su identidad: nombre de
distribución, `pyproject.toml`, versión, dependencias, tests, CLI y publicación
en PyPI propios.

El repositorio aporta solo lo compartido: CI selectiva, Issues comunes,
convenciones de trabajo y una documentación coordinada.

## Paquetes

| Paquete | Distribución en PyPI | CLI | Python | Documentación |
| --- | --- | --- | --- | --- |
| [diagram-db](packages/diagram-db) | `diagram-db` | `diagram-db` | ≥ 3.10 | [docs](packages/diagram-db/docs/README.md) |
| [pulsar](packages/pulsar) | `pulsar-psr` | `psr` | ≥ 3.10 | [docs](packages/pulsar/docs/README.md) |

## Estructura

```text
.
├── packages/
│   ├── diagram-db/            # nombre real del paquete, con su propio pyproject
│   │   ├── docs/              # documentación del paquete
│   │   ├── src/diagram_db/
│   │   └── tests/
│   └── pulsar/
│       ├── docs/
│       ├── landing/           # sitio estático y playground
│       └── tests/
├── docs/                      # documentación compartida del monorepo
└── .github/workflows/         # CI general selectiva y releases por tag
```

Cada `packages/<paquete>/` es autocontenido: se puede empaquetar, testear y
publicar sin depender de la raíz.

## Trabajo local

```bash
cd packages/diagram-db
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r test-requirements.txt
.venv/bin/pip install -e .
.venv/bin/pytest
```

Los hooks de calidad se ejecutan una sola vez para todo el repo:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Convenciones compartidas

- **Versionado independiente** con tags `<paquete>-vX.Y.Z`. Ver
  [docs/versionado.md](docs/versionado.md).
- **CI selectiva**: solo se ejecutan los jobs de los paquetes que cambian. Ver
  [docs/ci.md](docs/ci.md).
- **Issues compartidas**: un único tablero para todos los paquetes, con
  etiquetas `package:<paquete>`.
- **Documentación coordinada y separada**: la raíz explica lo común
  ([docs/](docs/README.md)) y cada paquete documenta lo suyo en
  `packages/<paquete>/docs/`.
- **Flujo de trabajo por PR**: ramas `prefijo/categoria`, squash a `main` y sin
  co-autores. Ver [CONTRIBUTING.md](CONTRIBUTING.md).

## Licencia

Este proyecto está bajo la licencia **MIT**. Consulta el archivo
[LICENSE](LICENSE) para más detalles.
