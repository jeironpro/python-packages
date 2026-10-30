"""Renderizado del diagrama ER con Graphviz.

Cada entidad se dibuja como una tabla HTML (cabecera con el nombre y una fila
por campo con su insignia PK/FK/UK) y cada relación como una arista con
marcadores de pata de cuervo.

Diseño: tono técnico y austero sobre papel cálido. Los identificadores, tipos y
claves usan JetBrains Mono; los nombres de campo y las etiquetas, Noto Sans.
Hay un solo acento (terracota) reservado a las claves primarias y a la
cardinalidad, para que el ojo encuentre primero lo que estructura el modelo.
"""

from __future__ import annotations

import html
from pathlib import Path

try:  # el paquete solo hace falta para rasterizar; el DOT se arma sin él
    import graphviz
    from graphviz.backend.execute import ExecutableNotFound
except ImportError:  # pragma: no cover - depende del entorno
    graphviz = None
    ExecutableNotFound = None

from .cardinality import Relation, build_relations
from .model import Entity, Schema

# --- Tokens de diseño -------------------------------------------------------
# Un único lugar para color y tipografía: nada de valores sueltos más abajo.
PAPER = "#FAF7F2"
INK = "#211D19"
INK_SOFT = "#6B6259"
RULE = "#D9CBB9"
RULE_LIGHT = "#EBE1D4"
ALERT = "#7A2E1E"
ACCENT = "#A64B2A"
EDGE = "#8A7F74"

# Con fallback en la lista: el SVG lo respeta y fontconfig resuelve la
# primera familia disponible al rasterizar el PNG.
FONT_SANS = "Noto Sans, sans-serif"
FONT_MONO = "JetBrains Mono, monospace"

SIZE_TITLE = "19"
SIZE_ENTITY = "11.5"
SIZE_FIELD = "10"
SIZE_TYPE = "9"
SIZE_BADGE = "8"
SIZE_EDGE = "9.5"
SIZE_CARDINALITY = "8.5"

# Aire dentro de la tabla: el texto nunca toca el filete del borde.
PAD_CELL = "6"
# Columna vacía entre el nombre del campo y su tipo: sin ella, un nombre largo
# se lee pegado al tipo.
GAP_NAME_TYPE = "10"

# Marcadores de Graphviz para cada extremo de la relación.
_MARKERS = {
    "exactly_one": "teetee",
    "zero_or_one": "odottee",
    "zero_many": "crow",
    "one_or_many": "crowtee",
}


class RenderError(Exception):
    """Error al generar la imagen (por ejemplo, si falta el binario ``dot``)."""


def to_dot(
    schema: Schema,
    relations: tuple[Relation, ...] | None = None,
    *,
    rankdir: str = "TB",
) -> str:
    """Devuelve el documento DOT del esquema."""
    if relations is None:
        relations = build_relations(schema)

    attributes = [
        f'bgcolor="{PAPER}"',
        'dpi="150"',
        f'fontname="{FONT_SANS}"',
        f'fontsize="{SIZE_TITLE}"',
        'nodesep="0.7"',
        'pad="0.4"',
        f'rankdir="{rankdir}"',
        'ranksep="0.95"',
        'splines="spline"',
    ]
    if schema.title:
        # Título como cabecera: texto alineado a la izquierda y una regla
        # corta debajo que lo separa del grafo.
        title = html.escape(schema.title)
        attributes.append(
            'label=<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" '
            'CELLPADDING="0">'
            f'<TR><TD ALIGN="LEFT"><FONT FACE="{FONT_SANS}" '
            f'POINT-SIZE="{SIZE_TITLE}" COLOR="{INK}">{title}</FONT>'
            "</TD></TR>"
            f'<TR><TD BGCOLOR="{INK}" HEIGHT="1" CELLPADDING="0"></TD></TR>'
            '<TR><TD HEIGHT="12" CELLPADDING="0"></TD></TR>'
            "</TABLE>>"
        )
        attributes.append('labelloc="t"')
        attributes.append('labeljust="l"')

    lines = [
        "digraph schema {",
        f"  graph [{', '.join(attributes)}];",
        f'  node [fontname="{FONT_SANS}", fontsize="{SIZE_FIELD}", '
        'margin="0", shape="plaintext"];',
        f'  edge [arrowsize="1.15", color="{EDGE}", fontcolor="{INK_SOFT}", '
        f'penwidth="1.0", splines="spline"];',
    ]
    lines.extend(_node(entity) for entity in schema.entities.values())
    lines.extend(_edge(relation) for relation in relations)
    lines.append("}")
    return "\n".join(lines) + "\n"


def render(
    schema: Schema,
    path: Path,
    *,
    fmt: str,
    rankdir: str = "TB",
    relations: tuple[Relation, ...] | None = None,
) -> Path:
    """Renderiza el diagrama en ``path`` y devuelve la ruta escrita."""
    if graphviz is None:
        raise RenderError(
            "falta el paquete 'graphviz'; instálalo para generar SVG o PNG "
            "(pip install diagram-db)"
        )
    if relations is None:
        relations = build_relations(schema)
    source = graphviz.Source(to_dot(schema, relations, rankdir=rankdir))
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        rendered = source.render(
            filename=str(path.with_suffix("")), format=fmt, cleanup=True
        )
    except ExecutableNotFound as exc:
        raise RenderError(
            "no se encontró el binario 'dot' de Graphviz; instálalo para "
            "generar SVG o PNG"
        ) from exc
    return Path(rendered)


def _node(entity: Entity) -> str:
    """Construye el nodo de una entidad como tabla HTML."""
    has_pk = bool(entity.primary_keys)
    rows = [
        f'<TR><TD ALIGN="LEFT" COLSPAN="4">'
        f'<FONT FACE="{FONT_MONO}" POINT-SIZE="{SIZE_ENTITY}" '
        f'COLOR="{INK}"><B>{html.escape(entity.name)}</B></FONT>'
        "</TD></TR>",
        # Filete de acento: separa la cabecera del cuerpo. Si falta la PK, el
        # filete se vuelve rojizo: la alerta no necesita una cabecera entera.
        f'<TR><TD BGCOLOR="{ACCENT if has_pk else ALERT}" '
        'COLSPAN="4" HEIGHT="1" CELLPADDING="0"></TD></TR>',
    ]

    for field in entity.fields:
        badges = []
        if field.primary_key:
            badges.append("PK")
        if field.references is not None:
            badges.append("FK")
        if field.unique and not field.primary_key:
            badges.append("UK")

        # La PK lleva el acento; FK y UK se quedan en la tinta para no competir.
        if field.primary_key:
            badge_color = ACCENT
        elif field.references is not None:
            badge_color = INK
        else:
            badge_color = INK_SOFT

        type_text = html.escape(field.type)
        if field.nullable and not field.primary_key:
            type_text += "?"

        name = html.escape(field.name)
        if field.primary_key:
            name = f"<B>{name}</B>"

        # Graphviz rechaza celdas vacías dentro de una etiqueta HTML, así que
        # las filas sin insignia usan un espacio duro.
        badge_text = " ".join(badges) or "&#160;"
        rows.append(
            "<TR>"
            f'<TD ALIGN="LEFT"><FONT FACE="{FONT_MONO}" '
            f'POINT-SIZE="{SIZE_BADGE}" COLOR="{badge_color}">'
            f"{badge_text}</FONT></TD>"
            f'<TD ALIGN="LEFT"><FONT FACE="{FONT_MONO}" '
            f'POINT-SIZE="{SIZE_FIELD}">{name}</FONT></TD>'
            f'<TD WIDTH="{GAP_NAME_TYPE}">&#160;</TD>'
            f'<TD ALIGN="LEFT"><FONT FACE="{FONT_MONO}" '
            f'POINT-SIZE="{SIZE_TYPE}" COLOR="{INK_SOFT}">'
            f"{type_text}</FONT></TD>"
            "</TR>"
        )
        # Filete entre filas: guía la lectura en tablas anchas sin competir
        # con el acento de la cabecera.
        if field is not entity.fields[-1]:
            rows.append(
                f'<TR><TD BGCOLOR="{RULE_LIGHT}" COLSPAN="4" HEIGHT="1" '
                'CELLPADDING="0"></TD></TR>'
            )

    # El marco de papel deja la punta de la flecha en el borde visible: Graphviz
    # mete ~3.8 pt del marcador dentro del nodo, así que el margen tiene que ser
    # mayor que eso o la flecha se dibuja encima del filete.
    table = (
        '<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="5" '
        f'BGCOLOR="{PAPER}"><TR><TD>'
        '<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" '
        f'CELLPADDING="{PAD_CELL}" COLOR="{RULE}">' + "".join(rows) + "</TABLE>"
        "</TD></TR></TABLE>"
    )
    return f"  {_quote(entity.name)} [label=<{table}>];"


def _edge(relation: Relation) -> str:
    """Construye la arista con el nombre en sans y la cardinalidad en mono."""
    arrow_tail = _MARKERS[relation.parent_marker]
    arrow_head = _MARKERS[relation.child_marker]
    name = html.escape(relation.label or relation.field, quote=False)
    # La etiqueta no lleva fondo: la línea de la arista tiene que verse
    # completa. La esquina vacía de la tabla la desplaza del punto medio, así
    # que la línea pasa por el hueco y nunca por encima de las letras, tanto en
    # aristas verticales como horizontales. El separador va dentro del tramo
    # mono porque, si queda fuera, se pinta con la fuente por defecto.
    label = (
        '<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0">'
        '<TR><TD WIDTH="6" HEIGHT="14">&#160;</TD><TD>&#160;</TD></TR>'
        '<TR><TD>&#160;</TD><TD ALIGN="LEFT">'
        f'<FONT FACE="{FONT_SANS}" POINT-SIZE="{SIZE_EDGE}">{name}</FONT>'
        f'<FONT FACE="{FONT_MONO}" POINT-SIZE="{SIZE_CARDINALITY}" '
        f'COLOR="{ACCENT}">&#160;&#160;{relation.cardinality}</FONT>'
        "</TD></TR></TABLE>"
    )
    return (
        f"  {_quote(relation.parent)} -> {_quote(relation.child)} "
        f'[dir="both", arrowtail="{arrow_tail}", arrowhead="{arrow_head}", '
        f"label=<{label}>];"
    )


def _quote(text: str) -> str:
    """Escapa un identificador o etiqueta para DOT."""
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
