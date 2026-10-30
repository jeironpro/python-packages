# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).
El proyecto usa [versionado semántico](https://semver.org/lang/es/).

## [Sin publicar]

### Cambiado

- El paquete pasa a vivir en el monorepo `python-packages`
  (`packages/diagram-db/`), conservando su nombre, su `pyproject.toml`, su
  versión y sus dependencias.
- Las URLs del proyecto y de las Issues apuntan al monorepo; la documentación
  del paquete se organiza en `docs/`.
- La publicación en PyPI se dispara con tags `diagram-db-vX.Y.Z` y comprueba
  que el tag coincide con `diagram_db.__version__`.
- La landing se publica en <https://jeironpro.github.io/python-packages/diagram-db/>,
  junto al catálogo del monorepo que reúne todos los paquetes.

## [0.2.0] — 2026-10-29

Primera versión distribuible como paquete de Python.

### Añadido

- Paquete instalable con `pip install diagram-db` y el comando `diagram-db`.
- Landing pública en <https://jeironpro.github.io/diagram-db/> con un
  playground que ejecuta el analizador real en el navegador.
- `import graphviz` deja de ser obligatorio: sin el paquete se pueden exportar
  `--format dot` y `--format json`, y solo el render de imagen falla con un
  mensaje claro.
- Publicación automática en PyPI al empujar un tag `v*`, con verificación
  posterior de la versión publicada.

## [0.1.0] — 2026-10-21

### Añadido

- Lectura de specs markdown con entidades, campos y modificadores `PK`, `UK`,
  `FK -> tabla.columna`, `not null` y `null`.
- Cardinalidades inferidas del FK y sección opcional `## Relaciones` con
  atajos `1:1`, `1:N` y `N:M`.
- Validación con diagnósticos `E0xx` y avisos `W0xx`, código de salida por
  severidad.
- Render SVG y PNG con Graphviz: tablas con insignias, pata de cuervo y
  etiquetas con el campo y la cardinalidad.
- Export `--format dot` y `--format json`, `--rankdir`, `--check` y
  `--allow-no-pk`.
