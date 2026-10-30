# Documentación del monorepo

Este directorio contiene la documentación **compartida** por todos los
paquetes: convenciones, versionado, CI y flujo de publicación. La documentación
**de cada paquete** vive dentro del propio paquete, en
`packages/<paquete>/docs/`, para que se pueda leer y publicar por separado.

Sitio publicado: <https://jeironpro.github.io/python-packages/> — catálogo del
monorepo en la raíz y una landing por paquete en `/<paquete>/`
([cómo se publica](ci.md#publicación-de-las-landings)).

## Guías compartidas

| Guía | Contenido |
| --- | --- |
| [versionado.md](versionado.md) | Versión independiente por paquete, tags y publicación en PyPI |
| [ci.md](ci.md) | CI general con ejecuciones selectivas y cómo añadir un paquete |

## Documentación por paquete

| Paquete | Índice | Referencia de uso | Historial |
| --- | --- | --- | --- |
| diagram-db | [docs](../packages/diagram-db/docs/README.md) | [README](../packages/diagram-db/README.md) | [CHANGELOG](../packages/diagram-db/CHANGELOG.md) |
| pulsar | [docs](../packages/pulsar/docs/README.md) | [README](../packages/pulsar/README.md) | [CHANGELOG](../packages/pulsar/CHANGELOG.md) |

## Reglas de la documentación

- **Coordinada**: los cambios que afectan a varios paquetes (convenciones,
  versionado, CI) se documentan aquí y en una sola PR.
- **Separada**: nada específico de un paquete se documenta en la raíz. El
  paquete es dueño de su README, su CHANGELOG y su `docs/`.
- **En la misma PR**: un cambio de comportamiento actualiza la documentación del
  paquete afectado en la misma pull request.
- **Idioma**: castellano, igual que el código y los comentarios del repositorio.
- **Historial**: cada paquete mantiene su `CHANGELOG.md` basado en
  [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). La versión del
  CHANGELOG debe coincidir con la del módulo y con el tag de publicación.
