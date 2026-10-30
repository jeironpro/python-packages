"""Interfaz de línea de comandos de diagram-db."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from .cardinality import Relation, build_relations
from .diagnostics import Diagnostic, SpecError
from .model import Schema
from .parser import parse_spec
from .render import RenderError, render, to_dot
from .validate import validate

FORMATS = ("svg", "png", "dot", "json")
RANKDIRS = ("TB", "LR", "BT", "RL")
IMAGE_FORMATS = ("svg", "png")


class UsageError(Exception):
    """Error de uso de la CLI; se traduce al código de salida 2."""


def main(argv: Sequence[str] | None = None) -> int:
    """Punto de entrada de la CLI; devuelve el código de salida."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    spec_path = Path(args.spec)

    try:
        text = spec_path.read_text(encoding="utf-8")
    except OSError as exc:
        _write_error(f"no se pudo leer {spec_path}: {exc.strerror or exc}")
        return 2

    try:
        schema = parse_spec(text)
    except SpecError as exc:
        _write_diagnostics(spec_path, exc.diagnostics, quiet=False)
        return 1

    schema, diagnostics = validate(schema, allow_no_pk=args.allow_no_pk)
    _write_diagnostics(spec_path, (*schema.warnings, *diagnostics), quiet=args.quiet)
    if any(item.is_error for item in diagnostics):
        return 1
    if args.check:
        return 0

    try:
        formats = _parse_formats(args.format)
    except UsageError as exc:
        _write_error(str(exc))
        return 2

    relations = build_relations(schema)
    if "dot" in formats:
        sys.stdout.write(to_dot(schema, relations, rankdir=args.rankdir))
    if "json" in formats:
        payload = json.dumps(_as_dict(schema, relations), indent=2, ensure_ascii=False)
        sys.stdout.write(payload + "\n")

    images = [fmt for fmt in formats if fmt in IMAGE_FORMATS]
    try:
        targets = _image_targets(spec_path, args.output, images)
    except UsageError as exc:
        _write_error(str(exc))
        return 2

    for fmt, target in targets.items():
        try:
            written = render(
                schema,
                target,
                fmt=fmt,
                rankdir=args.rankdir,
                relations=relations,
            )
        except RenderError as exc:
            _write_error(str(exc))
            return 1
        if not args.quiet:
            sys.stdout.write(f"escrito: {written}\n")

    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Construye el analizador de argumentos."""
    parser = argparse.ArgumentParser(
        prog="diagram-db",
        description="Genera un diagrama entidad-relación a partir de un spec.md",
    )
    parser.add_argument("spec", help="ruta del spec markdown")
    parser.add_argument(
        "-o",
        "--output",
        help="directorio de salida, o archivo .svg/.png si se pide un solo formato",
    )
    parser.add_argument(
        "--format",
        default="svg",
        help=f"formatos separados por comas: {', '.join(FORMATS)}",
    )
    parser.add_argument(
        "--rankdir",
        default="TB",
        choices=RANKDIRS,
        help="dirección del grafo (TB por defecto)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="solo valida el spec, sin escribir archivos",
    )
    parser.add_argument(
        "--allow-no-pk",
        action="store_true",
        help="trata la falta de PK como aviso en lugar de error",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="no muestra avisos ni mensajes de éxito",
    )
    return parser


def _parse_formats(raw: str) -> list[str]:
    """Normaliza y valida la lista de formatos pedidos."""
    formats: list[str] = []
    for item in raw.split(","):
        name = item.strip().lower()
        if not name:
            continue
        if name not in FORMATS:
            raise UsageError(f"formato no válido: '{name}' (usa {', '.join(FORMATS)})")
        if name not in formats:
            formats.append(name)
    if not formats:
        raise UsageError("no se pidió ningún formato")
    return formats


def _image_targets(
    spec_path: Path, output: str | None, images: list[str]
) -> dict[str, Path]:
    """Calcula la ruta de destino de cada formato de imagen."""
    if not images:
        return {}
    base = _base_name(spec_path)
    if output is None:
        return {fmt: spec_path.parent / f"{base}.{fmt}" for fmt in images}

    destination = Path(output)
    if destination.suffix.lower() in {".svg", ".png"}:
        if len(images) != 1:
            raise UsageError(
                "con -o a un archivo solo se puede pedir un formato de imagen"
            )
        expected = images[0]
        if destination.suffix.lower() != f".{expected}":
            raise UsageError(
                f"el sufijo de -o no coincide con el formato pedido ({expected})"
            )
        return {expected: destination}

    return {fmt: destination / f"{base}.{fmt}" for fmt in images}


def _base_name(spec_path: Path) -> str:
    """Nombre base de salida: sin la extensión ni el sufijo ``.spec``."""
    base = spec_path.stem
    if base.lower().endswith(".spec"):
        base = base[: -len(".spec")]
    return base


def _as_dict(schema: Schema, relations: tuple[Relation, ...]) -> dict[str, object]:
    """Convierte el esquema y sus relaciones a una estructura serializable."""
    return {
        "title": schema.title,
        "entities": [
            {
                "name": entity.name,
                "fields": [
                    {
                        "name": field.name,
                        "type": field.type,
                        "primary_key": field.primary_key,
                        "unique": field.unique,
                        "nullable": field.nullable,
                        "references": (
                            {
                                "entity": field.references[0],
                                "column": field.references[1],
                            }
                            if field.references
                            else None
                        ),
                    }
                    for field in entity.fields
                ],
            }
            for entity in schema.entities.values()
        ],
        "relations": [
            {
                "parent": relation.parent,
                "child": relation.child,
                "field": relation.field,
                "cardinality": relation.cardinality,
                "label": relation.label,
                "junction": relation.is_junction,
                "self": relation.is_self,
            }
            for relation in relations
        ],
    }


def _write_diagnostics(
    source: Path, diagnostics: tuple[Diagnostic, ...], *, quiet: bool
) -> None:
    """Escribe los diagnósticos en stderr, omitiendo avisos si ``quiet``."""
    for diagnostic in diagnostics:
        if diagnostic.is_error or not quiet:
            sys.stderr.write(diagnostic.format(str(source)) + "\n")


def _write_error(message: str) -> None:
    """Escribe un error de la propia herramienta en stderr."""
    sys.stderr.write(f"diagram-db: {message}\n")
