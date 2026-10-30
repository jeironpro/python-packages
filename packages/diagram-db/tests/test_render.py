"""Tests del renderizado con Graphviz."""

from __future__ import annotations

import importlib
import shutil
from pathlib import Path

import pytest

from diagram_db.cardinality import build_relations
from diagram_db.parser import parse_spec
from diagram_db.render import RenderError, render, to_dot
from diagram_db.validate import validate

requiere_dot = pytest.mark.skipif(
    shutil.which("dot") is None, reason="Graphviz no está instalado"
)


def _schema(tienda_text: str):
    return validate(parse_spec(tienda_text))[0]


def test_render_sin_paquete_graphviz(
    tienda_text: str, tmp_path: Path, monkeypatch
) -> None:
    """Sin el paquete graphviz el DOT sigue disponible, la imagen no."""
    modulo = importlib.import_module("diagram_db.render")
    schema = _schema(tienda_text)
    monkeypatch.setattr(modulo, "graphviz", None)

    assert to_dot(schema, build_relations(schema))
    with pytest.raises(RenderError, match="graphviz"):
        render(schema, tmp_path / "esquema.svg", fmt="svg")


def test_dot_contiene_una_tabla_por_entidad(tienda_text: str) -> None:
    schema = _schema(tienda_text)
    dot = to_dot(schema, build_relations(schema))

    for entity in schema.entities:
        assert f'"{entity}" [label=<' in dot
    # Solo las entidades usan tabla con borde; las aristas llevan etiqueta
    # HTML sin borde.
    assert dot.count('<TABLE BORDER="1"') == 6
    assert "PK" in dot
    assert ">user_id</FONT>" in dot
    assert "1:N</FONT>" in dot


def test_dot_etiqueta_las_aristas_de_puente(tienda_text: str) -> None:
    schema = _schema(tienda_text)
    dot = to_dot(schema, build_relations(schema))

    assert '"orders" -> "order_items"' in dot
    assert ">order_id</FONT>" in dot
    assert "N:M</FONT>" in dot


def test_dot_usa_la_etiqueta_de_la_relacion(tienda_text: str) -> None:
    schema = _schema(tienda_text)
    dot = to_dot(schema, build_relations(schema))

    assert ">reporta a</FONT>" in dot
    assert "0..1:N</FONT>" in dot
    assert ">paga</FONT>" in dot
    assert "1:1</FONT>" in dot


def test_dot_usa_los_tokens_de_diseno(tienda_text: str) -> None:
    schema = _schema(tienda_text)
    dot = to_dot(schema, build_relations(schema))

    assert 'bgcolor="#FAF7F2"' in dot
    assert 'fontname="Noto Sans, sans-serif"' in dot
    assert 'FACE="JetBrains Mono, monospace"' in dot
    assert 'COLOR="#A64B2A"' in dot


def test_dot_cabecera_clara_con_filete_de_acento(tienda_text: str) -> None:
    schema = _schema(tienda_text)
    dot = to_dot(schema, build_relations(schema))

    # La cabecera no es una banda oscura: el nombre va en tinta sobre papel y
    # el filete de acento marca el corte con el cuerpo.
    assert dot.count('BGCOLOR="#A64B2A" COLSPAN="4" HEIGHT="1"') == 6
    assert 'BGCOLOR="#2A2420" COLSPAN="4"' not in dot


def test_dot_no_tapa_las_aristas_con_la_etiqueta(tienda_text: str) -> None:
    schema = _schema(tienda_text)
    dot = to_dot(schema, build_relations(schema))

    # Las etiquetas no llevan fondo: la línea de cada arista se dibuja entera.
    for line in dot.splitlines():
        if " -> " in line:
            assert "BGCOLOR" not in line


def test_dot_desplaza_la_etiqueta_del_punto_medio(tienda_text: str) -> None:
    schema = _schema(tienda_text)
    dot = to_dot(schema, build_relations(schema))

    aristas = len(build_relations(schema))
    assert dot.count('<TR><TD WIDTH="6" HEIGHT="14">') == aristas


def test_dot_deja_margen_de_papel_para_las_flechas(tienda_text: str) -> None:
    schema = _schema(tienda_text)
    dot = to_dot(schema, build_relations(schema))

    # El marco de 1 pt hace que la punta de la flecha termine en el borde
    # visible de la tabla y no lo pise.
    assert dot.count('CELLPADDING="5" BGCOLOR="#FAF7F2"') == 6


def test_dot_deja_aire_al_texto_dentro_de_la_tabla(tienda_text: str) -> None:
    schema = _schema(tienda_text)
    dot = to_dot(schema, build_relations(schema))

    # El relleno interno es mayor que el del marco exterior y cada fila lleva
    # una columna vacía entre el nombre y el tipo, para que no se lean pegados.
    assert dot.count('CELLBORDER="0" CELLSPACING="0" CELLPADDING="6"') == 6
    filas = sum(len(entity.fields) for entity in schema.entities.values())
    assert dot.count('<TD WIDTH="10">&#160;</TD>') == filas


def test_dot_alerta_entidad_sin_pk_con_filete_rojo() -> None:
    schema = validate(
        parse_spec("# Sin PK\n\n## Entidades\n\n### auditoria\n- evento: text"),
        allow_no_pk=True,
    )[0]

    dot = to_dot(schema, build_relations(schema))

    assert 'BGCOLOR="#7A2E1E" COLSPAN="4" HEIGHT="1"' in dot


def test_dot_admite_nombres_cualificados() -> None:
    schema = parse_spec(
        "# Esquema: Prueba\n\n## Entidades\n\n### `sales.order`\n- id: int PK"
    )

    dot = to_dot(schema, build_relations(schema))

    assert '"sales.order" [label=<' in dot


@requiere_dot
def test_renderiza_svg(tienda_text: str, tmp_path: Path) -> None:
    schema = _schema(tienda_text)

    written = render(schema, tmp_path / "tienda.svg", fmt="svg")

    assert written == tmp_path / "tienda.svg"
    content = written.read_text(encoding="utf-8")
    assert content.startswith("<?xml")
    assert "users" in content
    assert "order_items" in content
    assert "1:N" in content


@requiere_dot
def test_renderiza_hijo_obligatorio(tmp_path: Path) -> None:
    schema = validate(
        parse_spec(
            "# Esquema: Prueba\n\n## Entidades\n\n"
            "### users\n- id: int PK\n\n"
            "### orders\n- id: int PK\n- user_id: int FK -> users.id\n\n"
            "## Relaciones\n\n- orders.user_id: 1:1..N\n"
        )
    )[0]

    written = render(schema, tmp_path / "obligatorio.svg", fmt="svg")

    assert written.exists()
    assert "1:1..N" in written.read_text(encoding="utf-8")


@requiere_dot
def test_renderiza_png(tienda_text: str, tmp_path: Path) -> None:
    schema = _schema(tienda_text)

    written = render(schema, tmp_path / "tienda.png", fmt="png")

    assert written.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
