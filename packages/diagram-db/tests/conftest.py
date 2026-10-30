"""Fixtures compartidas por los tests."""

from __future__ import annotations

from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.fixture
def tienda_path() -> Path:
    """Ruta del spec de ejemplo del repositorio."""
    return EXAMPLES / "tienda.spec.md"


@pytest.fixture
def tienda_text(tienda_path: Path) -> str:
    """Contenido del spec de ejemplo."""
    return tienda_path.read_text(encoding="utf-8")
