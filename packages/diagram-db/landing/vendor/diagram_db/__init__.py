"""diagram-db: diagramas entidad-relación a partir de un spec markdown."""

from __future__ import annotations

from .cardinality import Relation, build_relations, junction_entities
from .diagnostics import Diagnostic, SpecError
from .model import Entity, Field, Schema
from .parser import parse_spec
from .render import RenderError, render, to_dot
from .validate import validate

__version__ = "0.2.0"

__all__ = [
    "Diagnostic",
    "Entity",
    "Field",
    "Relation",
    "RenderError",
    "Schema",
    "SpecError",
    "__version__",
    "build_relations",
    "junction_entities",
    "parse_spec",
    "render",
    "to_dot",
    "validate",
]
