"""Inferencia de cardinalidades a partir de las claves foráneas.

El spec no declara participación total, así que el lado hijo siempre es
opcional (``o``) y solo se distinguen 1:1, 1:N y N:M. La sección opcional
``## Relaciones`` puede sobrescribir los marcadores y la etiqueta de una arista.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Schema

EXACTLY_ONE = "exactly_one"
ZERO_OR_ONE = "zero_or_one"
ZERO_MANY = "zero_many"
ONE_OR_MANY = "one_or_many"

# Atajos: (marcador del padre, marcador del hijo, texto de la arista).
_SHORTHANDS = {
    "1:1": (EXACTLY_ONE, ZERO_OR_ONE, "1:1"),
    "1:N": (EXACTLY_ONE, ZERO_MANY, "1:N"),
    "N:M": (EXACTLY_ONE, ZERO_MANY, "N:M"),
}

_PARENT_TOKENS = {
    "1": EXACTLY_ONE,
    "0..1": ZERO_OR_ONE,
}

_CHILD_TOKENS = {
    "1": EXACTLY_ONE,
    "0..1": ZERO_OR_ONE,
    "N": ZERO_MANY,
    "0..N": ZERO_MANY,
    "1..N": ONE_OR_MANY,
}


@dataclass(frozen=True)
class Relation:
    """Arista del diagrama: del padre (destino del FK) al hijo (origen)."""

    parent: str
    child: str
    field: str
    parent_marker: str
    child_marker: str
    cardinality: str
    is_junction: bool = False
    label: str | None = None

    @property
    def is_self(self) -> bool:
        """Indica si la relación es una auto-referencia."""
        return self.parent == self.child


def parse_cardinality(token: str) -> tuple[str, str, str] | None:
    """Traduce una cardinalidad del spec a ``(padre, hijo, texto)``.

    Acepta los atajos ``1:1``, ``1:N`` y ``N:M``, y la forma explícita
    ``<padre>:<hijo>`` con ``1`` o ``0..1`` en el lado del padre y ``1``,
    ``0..1``, ``N``, ``0..N`` o ``1..N`` en el del hijo. Devuelve ``None`` si la
    notación no es válida.
    """
    shorthand = _SHORTHANDS.get(token)
    if shorthand is not None:
        return shorthand

    parent, separator, child = token.partition(":")
    if not separator:
        return None
    parent_marker = _PARENT_TOKENS.get(parent.strip())
    child_token = child.strip()
    child_marker = _CHILD_TOKENS.get(child_token)
    if parent_marker is None or child_marker is None:
        return None

    normalized_child = "N" if child_token == "0..N" else child_token
    return parent_marker, child_marker, f"{parent.strip()}:{normalized_child}"


def junction_entities(schema: Schema) -> set[str]:
    """Entidades cuya PK está compuesta solo por FK (dos o más).

    Se dibujan como entidad propia porque el spec declara esa tabla, pero sus
    aristas se etiquetan como N:M.
    """
    junctions: set[str] = set()
    for entity in schema.entities.values():
        keys = entity.primary_keys
        if len(keys) >= 2 and all(key.references for key in keys):
            junctions.add(entity.name)
    return junctions


def build_relations(schema: Schema) -> tuple[Relation, ...]:
    """Construye las aristas del diagrama aplicando los overrides del spec."""
    junctions = junction_entities(schema)
    relations: list[Relation] = []

    for entity in schema.entities.values():
        is_junction = entity.name in junctions
        for field in entity.fields:
            if field.references is None:
                continue
            parent = field.references[0]
            if parent not in schema.entities:
                # El validador ya reportó el destino inexistente (E004).
                continue

            override = schema.overrides.get((entity.name, field.name))
            if override is not None:
                parent_marker = override.parent_marker
                child_marker = override.child_marker
                cardinality = override.cardinality
                label = override.label
            else:
                one_to_one = field.unique
                if one_to_one:
                    cardinality = "1:1"
                    child_marker = ZERO_OR_ONE
                else:
                    cardinality = "N:M" if is_junction else "1:N"
                    child_marker = ZERO_MANY
                parent_marker = ZERO_OR_ONE if field.nullable else EXACTLY_ONE
                label = None

            relations.append(
                Relation(
                    parent=parent,
                    child=entity.name,
                    field=field.name,
                    parent_marker=parent_marker,
                    child_marker=child_marker,
                    cardinality=cardinality,
                    is_junction=is_junction,
                    label=label,
                )
            )

    return tuple(relations)
