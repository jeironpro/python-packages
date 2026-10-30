"""Modelo intermedio del esquema: entidades, campos y referencias.

El parser produce estas estructuras y el resto del programa no vuelve a leer el
markdown, de modo que añadir nuevos renderizadores no afecta al análisis.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dataclass_field

from .diagnostics import Diagnostic


@dataclass(frozen=True)
class Field:
    """Una columna declarada en el spec.

    ``references`` apunta a ``(entidad, columna)`` tal como aparece en el spec;
    la validación resuelve la columna cuando el spec solo indica la entidad.
    """

    name: str
    type: str
    primary_key: bool = False
    unique: bool = False
    nullable: bool = True
    references: tuple[str, str] | None = None
    line: int = 0


@dataclass(frozen=True)
class Entity:
    """Una entidad (tabla) con sus campos en el orden declarado."""

    name: str
    fields: tuple[Field, ...]
    line: int = 0

    @property
    def primary_keys(self) -> tuple[Field, ...]:
        """Campos que forman la clave primaria, en el orden del spec."""
        return tuple(field for field in self.fields if field.primary_key)

    def field(self, name: str) -> Field | None:
        """Devuelve el campo con ese nombre, o ``None`` si no existe."""
        for field in self.fields:
            if field.name == name:
                return field
        return None


@dataclass(frozen=True)
class RelationOverride:
    """Ajuste declarado en ``## Relaciones`` para una arista concreta.

    ``entity`` y ``field`` identifican el campo FK que origina la relación; los
    marcadores ya vienen traducidos desde la notación del spec.
    """

    entity: str
    field: str
    parent_marker: str
    child_marker: str
    cardinality: str
    label: str | None = None
    line: int = 0


@dataclass(frozen=True)
class Schema:
    """Conjunto de entidades de un spec, con el título del documento."""

    title: str | None
    entities: dict[str, Entity]
    warnings: tuple[Diagnostic, ...] = ()
    overrides: dict[tuple[str, str], RelationOverride] = dataclass_field(
        default_factory=dict
    )
