"""Parser del spec markdown.

La gramática es deliberadamente estricta: cada entidad es un encabezado ``###``
y cada campo una línea ``- nombre: tipo modificadores``. Todo lo que no encaja
se reporta con su número de línea en lugar de ignorarse.
"""

from __future__ import annotations

import re

from .cardinality import parse_cardinality
from .diagnostics import WARNING, Diagnostic, SpecError
from .model import Entity, Field, RelationOverride, Schema

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_QUALIFIED = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
_TITLE = re.compile(r"^#\s+(?P<title>.+?)\s*$")
_SECTION = re.compile(r"^##\s+entidades\s*$", re.IGNORECASE)
_RELATIONS_SECTION = re.compile(r"^##\s+relaciones\s*$", re.IGNORECASE)
_HEADING = re.compile(r"^###\s+(?P<name>.+?)\s*$")
_FIELD = re.compile(r"^-\s+(?P<body>.+?)\s*$")

# Modificadores al final del segmento del tipo, por ejemplo "decimal(10,2) PK".
_MOD_AT_END = re.compile(
    r"\s+(?:"
    r"(?P<pk>pk)\b"
    r"|(?P<uk>uk|unique)\b"
    r"|(?P<nn>nn)\b"
    r"|(?P<notnull>not\s+null)\b"
    r"|(?P<null>nullable|null)\b"
    r"|(?P<fk>fk)\s*->\s*(?P<target>[A-Za-z_][A-Za-z0-9_.]*)"
    r")\s*$",
    re.IGNORECASE,
)

# Modificadores al inicio de un segmento posterior a la primera coma.
_MOD_AT_START = re.compile(
    r"^\s*(?:"
    r"(?P<fk>fk)\s*->\s*(?P<target>[A-Za-z_][A-Za-z0-9_.]*)"
    r"|(?P<pk>pk)\b"
    r"|(?P<uk>uk|unique)\b"
    r"|(?P<nn>nn)\b"
    r"|(?P<notnull>not\s+null)\b"
    r"|(?P<null>nullable|null)\b"
    r")\s*",
    re.IGNORECASE,
)


def parse_spec(text: str) -> Schema:
    """Convierte el contenido de un spec markdown en un ``Schema``.

    Lanza ``SpecError`` con todos los errores de sintaxis encontrados. Los
    avisos (por ejemplo, un PK declarado además como ``null``) se devuelven en
    ``Schema.warnings``.
    """
    entities: dict[str, Entity] = {}
    overrides: dict[tuple[str, str], RelationOverride] = {}
    errors: list[Diagnostic] = []
    warnings: list[Diagnostic] = []
    title: str | None = None
    section_found = False
    in_relations = False
    in_fence = False
    in_comment = False

    current_name: str | None = None
    current_line = 0
    current_fields: list[Field] = []
    current_names: set[str] = set()
    # Indica si la entidad actual ya declaró al menos una línea de campo; así no
    # se acumula un E003 cuando el único campo tenía otro error.
    current_declared = False
    # Descarta el contenido de una entidad cuyo encabezado no es válido.
    discarding = False

    def flush() -> None:
        """Cierra la entidad en construcción y la añade al esquema."""
        nonlocal current_name, current_fields, current_names, current_declared
        if current_name is None:
            return
        if not current_declared:
            errors.append(
                Diagnostic(
                    "E003",
                    f"la entidad '{current_name}' no declara campos",
                    current_line,
                )
            )
        entities[current_name] = Entity(
            name=current_name, fields=tuple(current_fields), line=current_line
        )
        current_name = None
        current_fields = []
        current_names = set()
        current_declared = False

    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()

        # Los bloques de código y los comentarios HTML se ignoran por completo,
        # para poder documentar ejemplos dentro del propio spec.
        if in_fence:
            if line.startswith("```") or line.startswith("~~~"):
                in_fence = False
            continue
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        if line.startswith("```") or line.startswith("~~~"):
            in_fence = True
            continue
        if line.startswith("<!--"):
            if "-->" not in line:
                in_comment = True
            continue
        if not line:
            continue

        if _SECTION.match(line):
            flush()
            section_found = True
            in_relations = False
            continue

        if _RELATIONS_SECTION.match(line):
            flush()
            in_relations = True
            continue

        if in_relations:
            relation_line = _FIELD.match(line)
            if relation_line is None:
                errors.append(
                    Diagnostic(
                        "E020",
                        f"línea no reconocida en '## Relaciones': '{line}'",
                        number,
                    )
                )
                continue
            override = _parse_override(relation_line.group("body"), number, errors)
            if override is not None:
                key = (override.entity, override.field)
                if key in overrides:
                    errors.append(
                        Diagnostic(
                            "E024",
                            f"relación duplicada para "
                            f"'{override.entity}.{override.field}'",
                            number,
                        )
                    )
                else:
                    overrides[key] = override
            continue

        title_line = _TITLE.match(line)
        if title_line and title is None and not section_found:
            title = title_line.group("title")
            continue

        if not section_found:
            # Todo lo anterior a '## Entidades' es prosa libre: viñetas, notas o
            # ejemplos no deben interpretarse como parte del modelo.
            continue

        heading = _HEADING.match(line)
        if heading:
            flush()
            raw_name = heading.group("name").strip()
            name, valid = _entity_name(raw_name)
            if not valid:
                errors.append(
                    Diagnostic(
                        "E009", f"nombre de entidad no válido: '{raw_name}'", number
                    )
                )
                discarding = True
                current_name = None
                continue
            discarding = False
            if name in entities:
                errors.append(
                    Diagnostic("E001", f"entidad duplicada: '{name}'", number)
                )
            current_name = name
            current_line = number
            current_declared = False
            continue

        field_line = _FIELD.match(line)
        if field_line:
            if discarding:
                continue
            if current_name is None:
                errors.append(Diagnostic("E008", "campo fuera de una entidad", number))
                continue
            current_declared = True
            parsed = _parse_field(
                field_line.group("body"),
                number,
                current_name,
                current_names,
                errors,
                warnings,
            )
            if parsed is not None:
                current_fields.append(parsed)
                current_names.add(parsed.name)
            continue

        errors.append(Diagnostic("E008", f"línea no reconocida: '{line}'", number))

    flush()

    if not section_found:
        errors.append(Diagnostic("E000", "falta la sección '## Entidades'"))
    if errors:
        raise SpecError(errors)
    return Schema(
        title=title,
        entities=entities,
        warnings=tuple(warnings),
        overrides=overrides,
    )


def _parse_override(
    body: str, line: int, errors: list[Diagnostic]
) -> RelationOverride | None:
    """Convierte una línea de ``## Relaciones`` en un override validado."""
    target, separator, remainder = body.partition(":")
    if not separator:
        errors.append(
            Diagnostic(
                "E020",
                f"la relación '{body.strip()}' debe ser 'entidad.campo: cardinalidad'",
                line,
            )
        )
        return None

    entity_name, dot, field_name = target.strip().partition(".")
    if not dot or not _IDENT.match(entity_name) or not _IDENT.match(field_name):
        errors.append(
            Diagnostic(
                "E020",
                f"referencia de relación no válida: '{target.strip()}' "
                "(usa 'entidad.campo')",
                line,
            )
        )
        return None

    remainder = remainder.strip()
    label: str | None = None
    quote = remainder.find('"')
    if quote != -1:
        if not remainder.endswith('"') or len(remainder) - quote < 2:
            errors.append(
                Diagnostic(
                    "E020",
                    "la etiqueta de la relación no está cerrada con comillas dobles",
                    line,
                )
            )
            return None
        label = remainder[quote + 1 : -1]
        if '"' in label:
            errors.append(
                Diagnostic(
                    "E020",
                    "la etiqueta de la relación no puede contener comillas dobles",
                    line,
                )
            )
            return None
        remainder = remainder[:quote].strip()

    if not remainder:
        errors.append(
            Diagnostic(
                "E020",
                f"la relación '{entity_name}.{field_name}' no declara cardinalidad",
                line,
            )
        )
        return None

    parsed = parse_cardinality(remainder)
    if parsed is None:
        errors.append(
            Diagnostic(
                "E023",
                f"cardinalidad no válida: '{remainder}' "
                "(usa 1:1, 1:N, N:M o la forma 0..1:1..N)",
                line,
            )
        )
        return None

    parent_marker, child_marker, cardinality = parsed
    return RelationOverride(
        entity=entity_name,
        field=field_name,
        parent_marker=parent_marker,
        child_marker=child_marker,
        cardinality=cardinality,
        label=label or None,
        line=line,
    )


def _entity_name(raw: str) -> tuple[str, bool]:
    """Separa las comillas invertidas de un nombre de entidad y lo valida."""
    if len(raw) >= 2 and raw.startswith("`") and raw.endswith("`"):
        candidate = raw[1:-1]
        return candidate, bool(_QUALIFIED.match(candidate))
    return raw, bool(_IDENT.match(raw))


def _split_top_level(text: str) -> list[str]:
    """Divide por comas ignorando las que están dentro de paréntesis o corchetes.

    Así ``decimal(10,2)`` se mantiene como un único tipo.
    """
    parts: list[str] = []
    buffer: list[str] = []
    depth = 0
    for char in text:
        if char in "([":
            depth += 1
        elif char in ")]":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            parts.append("".join(buffer))
            buffer = []
        else:
            buffer.append(char)
    parts.append("".join(buffer))
    return parts


def _parse_field(
    body: str,
    line: int,
    entity: str,
    seen: set[str],
    errors: list[Diagnostic],
    warnings: list[Diagnostic],
) -> Field | None:
    """Convierte el cuerpo de una línea de campo en un ``Field``."""
    raw_name, separator, remainder = body.partition(":")
    if not separator:
        errors.append(
            Diagnostic(
                "E011", f"el campo '{body.strip()}' no tiene ':' antes del tipo", line
            )
        )
        return None

    name = raw_name.strip()
    if not _IDENT.match(name):
        errors.append(Diagnostic("E010", f"nombre de campo no válido: '{name}'", line))
        return None
    if name in seen:
        errors.append(
            Diagnostic("E002", f"campo duplicado en '{entity}': '{name}'", line)
        )
        return None

    remainder = remainder.strip()
    if not remainder:
        errors.append(Diagnostic("E012", f"el campo '{name}' no declara tipo", line))
        return None

    segments = _split_top_level(remainder)
    head = segments[0].strip()
    state: dict[str, object] = {
        "primary_key": False,
        "unique": False,
        "nullable": True,
        "declared_null": False,
        "references": None,
    }

    while True:
        match = _MOD_AT_END.search(head)
        if match is None:
            break
        _apply_modifier(match, state)
        head = head[: match.start()].rstrip()

    type_text = head.strip()
    if not type_text:
        errors.append(Diagnostic("E012", f"el campo '{name}' no declara tipo", line))
        return None

    for segment in segments[1:]:
        rest = segment.strip()
        while rest:
            match = _MOD_AT_START.match(rest)
            if match is None:
                errors.append(
                    Diagnostic("E013", f"modificador no reconocido: '{rest}'", line)
                )
                break
            _apply_modifier(match, state)
            rest = rest[match.end() :].strip()

    primary_key = bool(state["primary_key"])
    declared_null = bool(state["declared_null"])
    if primary_key and declared_null:
        warnings.append(
            Diagnostic(
                "W003",
                f"el campo '{entity}.{name}' es PK y declara null; se ignora null",
                line,
                WARNING,
            )
        )

    return Field(
        name=name,
        type=type_text,
        primary_key=primary_key,
        unique=bool(state["unique"]),
        nullable=False if primary_key else bool(state["nullable"]),
        references=state["references"],  # type: ignore[arg-type]
        line=line,
    )


def _apply_modifier(match: re.Match[str], state: dict[str, object]) -> None:
    """Vuelca los grupos capturados de un modificador al estado del campo."""
    groups = match.groupdict()
    if groups.get("pk"):
        state["primary_key"] = True
    if groups.get("uk"):
        state["unique"] = True
    if groups.get("nn") or groups.get("notnull"):
        state["nullable"] = False
    if groups.get("null"):
        state["nullable"] = True
        state["declared_null"] = True
    target = groups.get("target")
    if target:
        target_entity, _, target_column = target.partition(".")
        state["references"] = (target_entity, target_column or None)
