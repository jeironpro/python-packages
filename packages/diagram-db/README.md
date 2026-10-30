# diagram-db

Genera diagramas entidad-relación a partir de un `spec.md` en markdown.

Las entidades, sus campos y las claves PK/FK se declaran en el spec; la
herramienta valida el modelo (referencias, tipos, claves) y produce un diagrama
con pata de cuervo en SVG o PNG usando Graphviz. Sin base de datos, sin ORM y
sin servicios externos.

- Landing y [playground](landing/) (sitio estático) que ejecuta el analizador
  real en el navegador.
- Paquete en [PyPI](https://pypi.org/project/diagram-db/).

## Requisitos

- Python 3.10 o superior.
- Graphviz con el binario `dot` (`dnf install graphviz` / `apt install graphviz`).

## Instalación

```bash
pip install diagram-db
```

Para trabajar sobre el código, con el entorno virtual del repo:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
```

En los dos casos queda disponible el comando `diagram-db` y también
`python -m diagram_db`. Si falta el paquete `graphviz`, los formatos `dot` y
`json` siguen funcionando; solo la generación de imágenes falla con un mensaje
claro.

## Uso

```bash
diagram-db examples/tienda.spec.md -o salida/
# escribe salida/tienda.svg
```

| Opción | Efecto |
|---|---|
| `-o, --output` | Directorio de salida, o archivo `.svg`/`.png` si se pide un solo formato |
| `--format` | `svg` (por defecto), `png`, `dot` o `json`; se combinan con comas |
| `--rankdir` | `TB` (por defecto), `LR`, `BT` o `RL` |
| `--check` | Solo valida el spec, sin escribir archivos |
| `--allow-no-pk` | Una entidad sin PK pasa de error a aviso |
| `--quiet` | Oculta avisos y mensajes de éxito |

Códigos de salida: `0` correcto, `1` errores en el spec, `2` error de uso.

## Formato del spec

```markdown
# Esquema: Tienda

## Entidades

### users
- id: int PK
- email: varchar(255) UK, not null
- manager_id: int FK -> users.id, null

### products
- id: int PK
- sku: varchar(40) UK, not null
- price: decimal(10,2), not null

### orders
- id: int PK
- user_id: int FK -> users.id, not null
- total: decimal(10,2), not null

### order_items
- order_id: int PK, FK -> orders.id
- product_id: int PK, FK -> products.id
- qty: int, not null
```

Reglas:

- `## Entidades` es obligatoria; lo que haya antes se ignora y el `# Título` se
  usa como título del diagrama.
- Cada entidad es un `### nombre`. Los nombres con punto (por ejemplo
  `sales.order`) se encierran en comillas invertidas dentro del encabezado.
- Cada campo es `- nombre: tipo` seguido de modificadores opcionales, en
  cualquier orden y separados por comas o espacios.
- Las comas dentro de paréntesis no separan modificadores: `decimal(10,2)` se
  conserva como un solo tipo.
- Los bloques de código y los comentarios `<!-- ... -->` se ignoran.
- Un campo es anulable por defecto; una PK siempre es obligatoria.

### Modificadores

| Modificador | Alias | Efecto |
|---|---|---|
| `PK` | `pk` | Clave primaria; varias líneas forman una PK compuesta |
| `UK` | `uk`, `unique` | Clave única |
| `FK -> tabla.columna` | `fk` | Clave foránea; la columna es opcional si la PK destino es simple |
| `not null` | `nn` | Campo obligatorio |
| `null` | `nullable` | Fuerza la nulabilidad |

### Cardinalidades

Se infieren del propio FK: si el campo es anulable el padre es opcional, y si
es `UK` la relación es 1:1. Una entidad cuya PK se compone solo de FK se dibuja
como tabla puente y sus aristas se etiquetan `N:M`.

Para sobrescribir una arista concreta, usa la sección opcional `## Relaciones`:

```markdown
## Relaciones

- users.manager_id: 0..1:N "reporta a"
- orders.user_id: 1:N "realiza"
```

- `1:1`, `1:N` y `N:M` son atajos; la forma explícita es `<padre>:<hijo>`, con
  `1` o `0..1` en el padre y `1`, `0..1`, `N`, `0..N` o `1..N` en el hijo.
- El texto entre comillas reemplaza el nombre del campo en la etiqueta; la
  cardinalidad se sigue mostrando (`reporta a  0..1:N`).

## Cómo leer el diagrama

- Cabecera con el nombre de la entidad y un filete terracota debajo; el
  filete se vuelve rojizo si la entidad no declara PK.
- Insignias por columna: `PK`, `FK`, `UK`, combinables.
- `?` al final del tipo indica que el campo es anulable.
- Cada arista va del padre al hijo con el nombre del campo y su cardinalidad
  al lado del punto medio, sin tapar la línea; las puntas terminan en el borde
  de la tabla.
- Marcadores: `teetee` (doble barra) = exactamente uno, `odottee` (círculo y
  barra) = cero o uno, `crow` = cero o muchos, `crowtee` = uno o muchos.

## Diagnósticos

Cada problema se informa como `archivo:línea: CÓDIGO mensaje` por stderr. Los
errores impiden generar el diagrama; los avisos no.

| Código | Tipo | Cuándo aparece |
|---|---|---|
| E000 | error | Falta `## Entidades` |
| E001 | error | Entidad duplicada |
| E002 | error | Campo duplicado en la misma entidad |
| E003 | error | Entidad sin campos |
| E004 | error | FK a una entidad inexistente |
| E005 | error | FK a una columna inexistente |
| E006 | error | FK sin columna y la PK destino no es simple |
| E007 | error | Entidad sin PK |
| E008 | error | Línea no reconocida dentro de `## Entidades` |
| E009 | error | Nombre de entidad no válido |
| E010 | error | Nombre de campo no válido |
| E011 | error | Línea de campo sin `:` |
| E012 | error | Campo sin tipo |
| E013 | error | Modificador no reconocido |
| E020 | error | Línea de `## Relaciones` mal formada |
| E021 | error | La relación apunta a una entidad o campo inexistente |
| E022 | error | La relación apunta a un campo que no es FK |
| E023 | error | Cardinalidad no válida |
| E024 | error | Relación duplicada para el mismo FK |
| W001 | aviso | FK a una columna que no es PK ni UK |
| W002 | aviso | Tipo del FK distinto del tipo destino |
| W003 | aviso | Campo `PK` declarado como `null` (gana `PK`) |
| W004 | aviso | Entidad sin PK con `--allow-no-pk` |

## Landing y playground

La web vive en [`landing/`](landing/index.html) y se publica en GitHub Pages. Es
HTML, CSS y JavaScript sin compilación; el playground descarga Pyodide solo
cuando se pide el primer análisis y ejecuta el mismo paquete que instala `pip`,
servido desde `landing/vendor/diagram_db`.

La publicación es un paso manual de una sola vez: activar Pages en
**Settings → Pages → Source: GitHub Actions** y definir la variable de
repositorio `PAGES_ENABLED=true`. Hasta entonces el workflow queda omitido, así
que `main` no falla mientras no esté activado.

Esa copia es la fuente única del playground y CI falla si diverge. Tras tocar
`src/diagram_db`, sincronízala:

```bash
cp src/diagram_db/*.py landing/vendor/diagram_db/
```

Para verla en local basta servir la carpeta:

```bash
python3 -m http.server 8765 --directory landing
```

## Desarrollo

```bash
.venv/bin/pip install -r test-requirements.txt
ruff check .
ruff format --check .
pre-commit run --all-files
.venv/bin/python -m pytest
```

Las dependencias se gestionan con `pip-tools` a partir de `pyproject.toml`:

```bash
pip-compile pyproject.toml -o requirements.txt
pip-compile --extra dev pyproject.toml -o test-requirements.txt
```

CI (`.github/workflows/ci.yml`) corre Ruff, comprueba que la copia del playground
no diverja, pasa pytest en Python 3.10–3.13, construye el sdist y el wheel,
valida los metadatos con `twine check --strict` y prueba el wheel instalado en un
entorno limpio.

El release sale por tag `v*`: `.github/workflows/release.yml` corre los tests,
crea el GitHub Release con los artefactos, publica en PyPI con trusted
publishing (OIDC, sin tokens) y verifica que la versión instalada genera un
diagrama.

La landing se publica con `.github/workflows/pages.yml`, que queda omitido hasta
que Pages esté activado en el repositorio y la variable `PAGES_ENABLED` valga
`true`.

## Publicación

La versión vive en `diagram_db.__version__` y `pyproject.toml` la lee de ahí, así
que un release es un tag:

```bash
git tag v0.2.0 && git push origin v0.2.0
```

El workflow de release corre los tests, crea el GitHub Release con los
artefactos, publica en PyPI con trusted publishing (OIDC, sin tokens) y verifica
que `pip install diagram-db==<versión>` genera un diagrama. El publisher se
configura una sola vez en <https://pypi.org/manage/account/publishing/> con el
repositorio `jeironpro/diagram-db`, el workflow `release.yml` y el entorno
`pypi`.

## Licencia

Este proyecto está bajo la licencia **MIT**. Consulta el archivo
[LICENSE](LICENSE) para más detalles.
