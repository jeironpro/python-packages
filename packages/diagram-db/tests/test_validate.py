"""Tests de la validación semántica."""

from __future__ import annotations

from diagram_db.diagnostics import Diagnostic
from diagram_db.parser import parse_spec
from diagram_db.validate import validate


def _spec(body: str) -> str:
    return f"# Esquema: Prueba\n\n## Entidades\n\n{body}"


def _codes(diagnostics: tuple[Diagnostic, ...]) -> list[str]:
    return [diagnostic.code for diagnostic in diagnostics]


def test_fk_a_entidad_inexistente() -> None:
    text = _spec("### orders\n- id: int PK\n- user_id: int FK -> users.id")

    _, diagnostics = validate(parse_spec(text))

    assert _codes(diagnostics) == ["E004"]


def test_fk_a_columna_inexistente() -> None:
    text = _spec(
        "### users\n- id: int PK\n\n"
        "### orders\n- id: int PK\n- user_id: int FK -> users.uuid"
    )

    _, diagnostics = validate(parse_spec(text))

    assert _codes(diagnostics) == ["E005"]


def test_fk_sin_columna_sobre_pk_compuesta_es_ambiguo() -> None:
    text = _spec(
        "### order_items\n- order_id: int PK, FK -> orders.id\n"
        "- product_id: int PK, FK -> products.id\n\n"
        "### products\n- id: int PK\n\n"
        "### orders\n- id: int PK\n\n"
        "### shipments\n- id: int PK\n- order_id: int FK -> order_items"
    )

    _, diagnostics = validate(parse_spec(text))

    assert _codes(diagnostics) == ["E006"]


def test_entidad_sin_pk_es_error_por_defecto() -> None:
    text = _spec("### logs\n- message: text")

    _, diagnostics = validate(parse_spec(text))

    assert _codes(diagnostics) == ["E007"]
    assert diagnostics[0].is_error


def test_entidad_sin_pk_puede_ser_aviso() -> None:
    text = _spec("### logs\n- message: text")

    _, diagnostics = validate(parse_spec(text), allow_no_pk=True)

    assert _codes(diagnostics) == ["W004"]
    assert not diagnostics[0].is_error


def test_fk_a_columna_no_unica_emite_aviso() -> None:
    text = _spec(
        "### users\n- id: int PK\n- nickname: varchar(40)\n\n"
        "### orders\n- id: int PK\n- nick: varchar(40) FK -> users.nickname"
    )

    _, diagnostics = validate(parse_spec(text))

    assert _codes(diagnostics) == ["W001"]


def test_tipos_incompatibles_emiten_aviso() -> None:
    text = _spec(
        "### users\n- id: uuid PK\n\n"
        "### orders\n- id: int PK\n- user_id: int FK -> users.id"
    )

    _, diagnostics = validate(parse_spec(text))

    assert _codes(diagnostics) == ["W002"]


def test_override_sobre_campo_inexistente() -> None:
    text = _spec("### users\n- id: int PK\n\n## Relaciones\n\n- users.nope: 1:N\n")

    _, diagnostics = validate(parse_spec(text))

    assert _codes(diagnostics) == ["E021"]


def test_override_sobre_campo_que_no_es_fk() -> None:
    text = _spec("### users\n- id: int PK\n\n## Relaciones\n\n- users.id: 1:N\n")

    _, diagnostics = validate(parse_spec(text))

    assert _codes(diagnostics) == ["E022"]


def test_resuelve_la_columna_implicita_del_fk() -> None:
    text = _spec(
        "### users\n- id: int PK\n\n"
        "### orders\n- id: int PK\n- user_id: int FK -> users"
    )

    schema, diagnostics = validate(parse_spec(text))

    assert diagnostics == ()
    user_id = schema.entities["orders"].field("user_id")
    assert user_id is not None
    assert user_id.references == ("users", "id")


def test_resuelve_el_ejemplo_completo(tienda_text: str) -> None:
    schema, diagnostics = validate(parse_spec(tienda_text))

    assert [item for item in diagnostics if item.is_error] == []
    order_id = schema.entities["order_items"].field("order_id")
    assert order_id is not None
    assert order_id.references == ("orders", "id")
