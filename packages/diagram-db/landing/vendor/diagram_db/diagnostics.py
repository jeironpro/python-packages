"""Diagnósticos del análisis del spec.

Un ``Diagnostic`` es un error o un aviso con su código estable (E001, W001...) y
la línea del spec donde se detectó, para que la CLI pueda informarlos todos.
"""

from __future__ import annotations

from dataclasses import dataclass

ERROR = "error"
WARNING = "warning"


@dataclass(frozen=True)
class Diagnostic:
    """Error o aviso detectado al analizar el spec."""

    code: str
    message: str
    line: int = 0
    severity: str = ERROR

    @property
    def is_error(self) -> bool:
        """Indica si el diagnóstico impide generar el diagrama."""
        return self.severity == ERROR

    def format(self, source: str) -> str:
        """Devuelve ``archivo:línea: código mensaje`` para mostrar al usuario."""
        location = f"{source}:{self.line}" if self.line else source
        return f"{location}: {self.code} {self.message}"


class SpecError(Exception):
    """Agrupa los errores de sintaxis para informarlos todos a la vez."""

    def __init__(self, diagnostics: list[Diagnostic]) -> None:
        self.diagnostics = tuple(diagnostics)
        super().__init__("; ".join(item.message for item in self.diagnostics))
