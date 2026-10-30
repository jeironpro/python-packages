"""Tests de la inferencia de cardinalidades."""

from __future__ import annotations

from diagram_db.cardinality import (
    EXACTLY_ONE,
    ONE_OR_MANY,
    ZERO_MANY,
    ZERO_OR_ONE,
    Relation,
    build_relations,
    junction_entities,
)
from diagram_db.parser import parse_spec
from diagram_db.validate import validate


def _relations(tienda_text: str) -> tuple[Relation, ...]:
    schema, _ = validate(parse_spec(tienda_text))
    return build_relations(schema)


def _find(relations: tuple[Relation, ...], child: str, field: str) -> Relation:
    for relation in relations:
        if relation.child == child and relation.field == field:
            return relation
    raise AssertionError(f"no hay relación para {child}.{field}")


def test_numero_de_relaciones_del_ejemplo(tienda_text: str) -> None:
    assert len(_relations(tienda_text)) == 7


def test_fk_obligatoria_es_uno_a_muchos(tienda_text: str) -> None:
    relation = _find(_relations(tienda_text), "orders", "user_id")

    assert relation.parent == "users"
    assert relation.cardinality == "1:N"
    assert relation.parent_marker == EXACTLY_ONE
    assert relation.child_marker == ZERO_MANY


def test_fk_anulable_admite_padre_ausente(tienda_text: str) -> None:
    relation = _find(_relations(tienda_text), "categories", "parent_id")

    assert relation.is_self is True
    assert relation.parent_marker == ZERO_OR_ONE


def test_fk_unica_es_uno_a_uno(tienda_text: str) -> None:
    relation = _find(_relations(tienda_text), "payments", "order_id")

    assert relation.cardinality == "1:1"
    assert relation.child_marker == ZERO_OR_ONE


def test_tabla_puente_produce_n_a_m(tienda_text: str) -> None:
    schema, _ = validate(parse_spec(tienda_text))
    assert junction_entities(schema) == {"order_items"}

    relations = _relations(tienda_text)
    order_item = _find(relations, "order_items", "order_id")
    assert order_item.cardinality == "N:M"
    assert order_item.is_junction is True


def test_override_cambia_etiqueta_y_cardinalidad(tienda_text: str) -> None:
    relation = _find(_relations(tienda_text), "users", "manager_id")

    assert relation.label == "reporta a"
    assert relation.cardinality == "0..1:N"
    assert relation.parent_marker == ZERO_OR_ONE


def test_override_con_hijo_obligatorio() -> None:
    text = (
        "# Esquema: Prueba\n\n## Entidades\n\n"
        "### users\n- id: int PK\n\n"
        "### orders\n- id: int PK\n- user_id: int FK -> users.id, not null\n\n"
        '## Relaciones\n\n- orders.user_id: 0..1:1..N "realiza"\n'
    )
    schema, _ = validate(parse_spec(text))

    [relation] = build_relations(schema)

    assert relation.parent_marker == ZERO_OR_ONE
    assert relation.child_marker == ONE_OR_MANY
    assert relation.cardinality == "0..1:1..N"
    assert relation.label == "realiza"


def test_dos_fk_que_no_son_pk_no_forman_puente() -> None:
    text = (
        "# Esquema: Prueba\n\n## Entidades\n\n"
        "### users\n- id: int PK\n\n"
        "### products\n- id: int PK\n\n"
        "### views\n- id: int PK\n- user_id: int FK -> users.id\n"
        "- product_id: int FK -> products.id"
    )
    schema, _ = validate(parse_spec(text))

    assert junction_entities(schema) == set()
    assert build_relations(schema)[0].cardinality == "1:N"
