"""Tests del parser del spec."""

from __future__ import annotations

import pytest

from diagram_db.diagnostics import SpecError
from diagram_db.parser import parse_spec


def _spec(body: str) -> str:
    """Envuelve el cuerpo de entidades en un documento válido."""
    return f"# Esquema: Prueba\n\n## Entidades\n\n{body}"


def _codes(errors: SpecError) -> list[str]:
    return [diagnostic.code for diagnostic in errors.diagnostics]


def test_parsea_el_spec_de_ejemplo(tienda_text: str) -> None:
    schema = parse_spec(tienda_text)

    assert schema.title == "Esquema: Tienda"
    assert list(schema.entities) == [
        "users",
        "categories",
        "products",
        "orders",
        "order_items",
        "payments",
    ]
    assert len(schema.entities["order_items"].fields) == 4


def test_conserva_la_coma_dentro_del_tipo() -> None:
    schema = parse_spec(_spec("### products\n- price: decimal(10,2), not null"))

    field = schema.entities["products"].fields[0]
    assert field.type == "decimal(10,2)"
    assert field.nullable is False


def test_ignora_bloques_de_codigo() -> None:
    text = _spec(
        "### users\n- id: int PK\n\n```markdown\n### inventada\n- campo: int PK\n```\n"
    )

    schema = parse_spec(text)
    assert list(schema.entities) == ["users"]


def test_la_prosa_previa_admite_vinetas() -> None:
    text = (
        "# Esquema: Préstamos\n\n"
        "- uuid es un hash SHA-256 de 64 caracteres\n"
        "- pagos.empleado_id apunta a un usuario EMPLEADO\n\n"
        "## Entidades\n\n### users\n- id: int PK\n"
    )

    schema = parse_spec(text)

    assert schema.title == "Esquema: Préstamos"
    assert list(schema.entities) == ["users"]


def test_acepta_nombres_entre_comillas_invertidas() -> None:
    schema = parse_spec(_spec("### `sales.order`\n- id: int PK"))

    assert list(schema.entities) == ["sales.order"]


def test_los_modificadores_no_dependen_del_orden() -> None:
    schema = parse_spec(
        _spec("### orders\n- id: int not null PK\n- total: decimal(10,2) nullable")
    )

    identifier, total = schema.entities["orders"].fields
    assert identifier.primary_key is True
    assert identifier.nullable is False
    assert total.nullable is True


def test_fk_sin_columna_se_guarda_para_resolver() -> None:
    schema = parse_spec(
        _spec("### users\n- id: int PK\n\n### orders\n- user_id: int FK -> users")
    )

    assert schema.entities["orders"].fields[0].references == ("users", None)


def test_falta_la_seccion_de_entidades() -> None:
    with pytest.raises(SpecError) as error:
        parse_spec("# Solo un título\n")

    assert _codes(error.value) == ["E000"]


def test_entidad_duplicada() -> None:
    text = _spec("### users\n- id: int PK\n\n### users\n- id: int PK")

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    assert _codes(error.value) == ["E001"]


def test_campo_duplicado() -> None:
    text = _spec("### users\n- id: int PK\n- id: int PK")

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    assert _codes(error.value) == ["E002"]


def test_entidad_sin_campos() -> None:
    text = _spec("### users\n\n### orders\n- id: int PK")

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    assert _codes(error.value) == ["E003"]


def test_linea_no_reconocida_informa_la_linea() -> None:
    text = _spec("### users\n- id: int PK\n\nesto no debería estar aquí")

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    [diagnostic] = error.value.diagnostics
    assert diagnostic.code == "E008"
    assert diagnostic.line == 8


def test_nombre_de_entidad_invalido() -> None:
    text = _spec("### users robados\n- id: int PK")

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    assert _codes(error.value) == ["E009"]


def test_nombre_de_campo_invalido() -> None:
    text = _spec("### users\n- user id: int PK")

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    assert _codes(error.value) == ["E010"]


def test_campo_sin_dos_puntos() -> None:
    text = _spec("### users\n- id int PK")

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    assert _codes(error.value) == ["E011"]


def test_campo_sin_tipo() -> None:
    text = _spec("### users\n- id:")

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    assert _codes(error.value) == ["E012"]


def test_modificador_desconocido() -> None:
    text = _spec("### users\n- id: int PK, obligatorio")

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    assert _codes(error.value) == ["E013"]


def test_parsea_la_seccion_de_relaciones() -> None:
    text = _spec(
        "### users\n- id: int PK\n- manager_id: int FK -> users.id\n"
        '\n## Relaciones\n\n- users.manager_id: 1:N "reporta a"\n'
    )

    schema = parse_spec(text)

    override = schema.overrides[("users", "manager_id")]
    assert override.cardinality == "1:N"
    assert override.label == "reporta a"


def test_relacion_con_cardinalidad_invalida() -> None:
    text = _spec(
        "### users\n- id: int PK\n- manager_id: int FK -> users.id\n"
        "\n## Relaciones\n\n- users.manager_id: 1:X\n"
    )

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    assert _codes(error.value) == ["E023"]


def test_relacion_sin_dos_puntos() -> None:
    text = _spec("### users\n- id: int PK\n\n## Relaciones\n\n- users.id 1:N\n")

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    assert _codes(error.value) == ["E020"]


def test_etiqueta_de_relacion_sin_cerrar() -> None:
    text = _spec(
        "### users\n- id: int PK\n- manager_id: int FK -> users.id\n"
        '\n## Relaciones\n\n- users.manager_id: 1:N "reporta\n'
    )

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    assert _codes(error.value) == ["E020"]


def test_relacion_duplicada() -> None:
    text = _spec(
        "### users\n- id: int PK\n- manager_id: int FK -> users.id\n"
        "\n## Relaciones\n\n"
        "- users.manager_id: 1:N\n"
        '- users.manager_id: 0..1:N "reporta a"\n'
    )

    with pytest.raises(SpecError) as error:
        parse_spec(text)

    assert _codes(error.value) == ["E024"]


def test_pk_con_null_emite_aviso() -> None:
    schema = parse_spec(_spec("### users\n- id: int PK, null"))

    [warning] = schema.warnings
    assert warning.code == "W003"
    assert schema.entities["users"].fields[0].nullable is False
