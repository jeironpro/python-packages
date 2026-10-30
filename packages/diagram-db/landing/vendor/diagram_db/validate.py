"""Validación semántica del esquema.

Comprueba la integridad de las referencias y devuelve un esquema con las
columnas destino ya resueltas, que es lo que consumen las cardinalidades y el
renderizador.
"""

from __future__ import annotations

from dataclasses import replace

from .diagnostics import ERROR, WARNING, Diagnostic
from .model import Entity, Field, Schema

# Familias de tipos para comparar FK y destino sin falsos positivos por
# sinónimos habituales (int/integer, varchar/text...).
_TYPE_FAMILIES = {
    "int": "integer",
    "integer": "integer",
    "int2": "integer",
    "smallint": "integer",
    "int4": "integer",
    "int8": "integer",
    "bigint": "integer",
    "serial": "integer",
    "bigserial": "integer",
    "uuid": "uuid",
    "text": "string",
    "varchar": "string",
    "char": "string",
    "character": "string",
    "nvarchar": "string",
    "bool": "boolean",
    "boolean": "boolean",
    "date": "date",
    "timestamp": "timestamp",
    "timestamptz": "timestamp",
    "datetime": "timestamp",
    "numeric": "decimal",
    "decimal": "decimal",
    "float": "decimal",
    "double": "decimal",
    "real": "decimal",
}


def validate(
    schema: Schema, *, allow_no_pk: bool = False
) -> tuple[Schema, tuple[Diagnostic, ...]]:
    """Valida un esquema y resuelve el destino de cada clave foránea.

    Devuelve el esquema resuelto y todos los diagnósticos encontrados. Los
    errores (``severity='error'``) impiden generar el diagrama; los avisos no.
    """
    diagnostics: list[Diagnostic] = []
    resolved: dict[str, Entity] = {}

    for entity in schema.entities.values():
        if not entity.primary_keys:
            diagnostics.append(
                Diagnostic(
                    "W004" if allow_no_pk else "E007",
                    f"la entidad '{entity.name}' no declara ninguna PK",
                    entity.line,
                    WARNING if allow_no_pk else ERROR,
                )
            )

        fields: list[Field] = []
        for field in entity.fields:
            if field.references is None:
                fields.append(field)
                continue
            resolved_field = _resolve_reference(schema, entity, field, diagnostics)
            fields.append(resolved_field)
        resolved[entity.name] = replace(entity, fields=tuple(fields))

    _validate_overrides(schema, diagnostics)

    return (
        Schema(
            title=schema.title,
            entities=resolved,
            warnings=schema.warnings,
            overrides=schema.overrides,
        ),
        tuple(diagnostics),
    )


def _validate_overrides(schema: Schema, diagnostics: list[Diagnostic]) -> None:
    """Comprueba que cada override apunte a un FK existente."""
    for override in schema.overrides.values():
        owner = schema.entities.get(override.entity)
        if owner is None:
            diagnostics.append(
                Diagnostic(
                    "E021",
                    f"la relación '{override.entity}.{override.field}' apunta "
                    "a una entidad inexistente",
                    override.line,
                )
            )
            continue

        target = owner.field(override.field)
        if target is None:
            diagnostics.append(
                Diagnostic(
                    "E021",
                    f"la relación '{override.entity}.{override.field}' apunta "
                    "a un campo inexistente",
                    override.line,
                )
            )
            continue

        if target.references is None:
            diagnostics.append(
                Diagnostic(
                    "E022",
                    f"'{override.entity}.{override.field}' no es un FK; no hay "
                    "relación que sobrescribir",
                    override.line,
                )
            )


def _resolve_reference(
    schema: Schema,
    entity: Entity,
    field: Field,
    diagnostics: list[Diagnostic],
) -> Field:
    """Comprueba que el destino del FK existe y devuelve el campo resuelto."""
    target_name, target_column = field.references  # type: ignore[misc]
    target = schema.entities.get(target_name)
    if target is None:
        diagnostics.append(
            Diagnostic(
                "E004",
                f"el FK {entity.name}.{field.name} apunta a la entidad "
                f"'{target_name}', que no existe",
                field.line,
            )
        )
        return field

    if target_column is None:
        target_keys = target.primary_keys
        if len(target_keys) != 1:
            diagnostics.append(
                Diagnostic(
                    "E006",
                    f"el FK {entity.name}.{field.name} no indica columna y "
                    f"'{target_name}' no tiene una PK simple",
                    field.line,
                )
            )
            return field
        target_column = target_keys[0].name

    target_field = target.field(target_column)
    if target_field is None:
        diagnostics.append(
            Diagnostic(
                "E005",
                f"el FK {entity.name}.{field.name} apunta a "
                f"'{target_name}.{target_column}', que no existe",
                field.line,
            )
        )
        return field

    if not (target_field.primary_key or target_field.unique):
        diagnostics.append(
            Diagnostic(
                "W001",
                f"el FK {entity.name}.{field.name} apunta a "
                f"'{target_name}.{target_column}', que no es PK ni UK",
                field.line,
                WARNING,
            )
        )

    field_family = _type_family(field.type)
    target_family = _type_family(target_field.type)
    if field_family and target_family and field_family != target_family:
        diagnostics.append(
            Diagnostic(
                "W002",
                f"el tipo de {entity.name}.{field.name} ('{field.type}') no "
                f"coincide con '{target_name}.{target_column}' "
                f"('{target_field.type}')",
                field.line,
                WARNING,
            )
        )

    return replace(field, references=(target_name, target_column))


def _type_family(type_text: str) -> str | None:
    """Devuelve la familia de un tipo, o ``None`` si no se reconoce."""
    base = type_text.lower().split("(")[0].strip()
    return _TYPE_FAMILIES.get(base)
