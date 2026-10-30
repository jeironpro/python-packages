# Versionado y publicación

Cada paquete se versiona y se publica de forma **independiente**. No existe una
versión del monorepo: existen tantas versiones como paquetes.

## Fuente de verdad de la versión

La versión vive en el código del paquete y `pyproject.toml` la lee de ahí con
`dynamic = ["version"]`:

| Paquete | Módulo | Atributo |
| --- | --- | --- |
| diagram-db | `src/diagram_db/__init__.py` | `diagram_db.__version__` |
| pulsar | `pulsar.py` | `pulsar.__version__` |

Nunca se escribe la versión a mano en `pyproject.toml` ni en el workflow.

## Tags

Formato: `<paquete>-vX.Y.Z`, con SemVer.

```text
diagram-db-v0.2.0
diagram-db-v0.3.0
pulsar-v2.0.1
pulsar-v2.1.0
```

El prefijo es obligatorio: un tag `v1.0.0` a secas no dice qué paquete publicar
y no dispara ninguna release. Los tags históricos de los repositorios
individuales (`diagram-db`, `pulsar`) no se migran; este monorepo empieza su
propio historial de tags.

## Flujo de una release

1. Subir la versión en el módulo del paquete y añadir la entrada en su
   `CHANGELOG.md`.
2. Abrir la PR, esperar la CI y hacer squash a `main`.
3. Etiquetar el commit de `main` y empujar el tag:

   ```bash
   git checkout main && git pull
   git tag -a diagram-db-v0.3.0 -m "diagram-db v0.3.0"
   git push origin diagram-db-v0.3.0
   ```

4. El workflow `release-<paquete>.yml` se encarga del resto:
   - comprueba que la versión del tag coincide con la del módulo;
   - ejecuta los tests del paquete;
   - construye sdist y wheel, y los valida con `twine check --strict`;
   - crea la GitHub Release con los artefactos;
   - publica en PyPI con trusted publishing (OIDC, sin tokens);
   - verifica la versión publicada e instala desde PyPI en un entorno limpio.

## Publicación en PyPI (trusted publishing)

La publicación no usa secretos: PyPI confía en el workflow de GitHub Actions.
Cada proyecto necesita su publisher configurado una sola vez en
<https://pypi.org/manage/account/publishing/> con estos valores:

| Campo | diagram-db | pulsar |
| --- | --- | --- |
| Owner | `jeironpro` | `jeironpro` |
| Repository | `python-packages` | `python-packages` |
| Workflow name | `release-diagram-db.yml` | `release-pulsar.yml` |
| Environment | `pypi` | `pypi` |

Los publishers configurados para los repositorios antiguos (`diagram-db` y
`pulsar`) dejan de aplicar: al integrar los paquetes hay que actualizar el
publisher de cada proyecto a `python-packages`, o la publicación fallará con un
error de identidad de OIDC.

## Reglas

- **Una versión de PyPI no se reutiliza**: si el tag ya existe upstream, hay que
  subir la versión, no borrar el tag.
- **Los tags solo se crean desde `main`** y sobre un commit ya integrado.
- **Borrar un tag no despublica**: PyPI no permite reemplazar una versión.
- **Un tag por paquete**: `pulsar-v2.1.0` no publica `diagram-db`.
- **La release no lleva co-autores**: ni el commit de squash ni el cuerpo de la
  GitHub Release incluyen trailers `Co-Authored-By`.
