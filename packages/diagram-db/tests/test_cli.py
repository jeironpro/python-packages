"""Tests de la interfaz de línea de comandos."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from diagram_db.cli import main

requiere_dot = pytest.mark.skipif(
    shutil.which("dot") is None, reason="Graphviz no está instalado"
)


@requiere_dot
def test_genera_svg_en_un_directorio(
    tienda_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main([str(tienda_path), "-o", str(tmp_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert (tmp_path / "tienda.svg").exists()
    assert "escrito:" in captured.out


@requiere_dot
def test_respeta_el_nombre_de_archivo(tienda_path: Path, tmp_path: Path) -> None:
    destino = tmp_path / "modelo.svg"

    assert main([str(tienda_path), "-o", str(destino)]) == 0
    assert destino.exists()


@requiere_dot
def test_genera_svg_y_png(tienda_path: Path, tmp_path: Path) -> None:
    exit_code = main([str(tienda_path), "-o", str(tmp_path), "--format", "svg,png"])

    assert exit_code == 0
    assert (tmp_path / "tienda.svg").exists()
    assert (tmp_path / "tienda.png").exists()


def test_check_no_escribe_archivos(tienda_path: Path, tmp_path: Path) -> None:
    exit_code = main([str(tienda_path), "-o", str(tmp_path), "--check"])

    assert exit_code == 0
    assert list(tmp_path.iterdir()) == []


def test_check_falla_con_spec_invalido(tmp_path: Path) -> None:
    spec = tmp_path / "roto.md"
    spec.write_text(
        "## Entidades\n\n### users\n- id: int PK\nsobra\n", encoding="utf-8"
    )

    assert main([str(spec), "--check"]) == 1


def test_spec_inexistente_devuelve_dos(tmp_path: Path) -> None:
    assert main([str(tmp_path / "no-existe.md")]) == 2


def test_formato_desconocido_devuelve_dos(tienda_path: Path) -> None:
    assert main([str(tienda_path), "--format", "pdf"]) == 2


def test_sufijo_que_no_coincide_devuelve_dos(tienda_path: Path, tmp_path: Path) -> None:
    destino = tmp_path / "modelo.png"

    assert main([str(tienda_path), "-o", str(destino), "--format", "svg"]) == 2


def test_dump_json(tienda_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([str(tienda_path), "--format", "json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["title"] == "Esquema: Tienda"
    assert len(payload["entities"]) == 6
    assert len(payload["relations"]) == 7
    manager = next(
        item for item in payload["relations"] if item["field"] == "manager_id"
    )
    assert manager["label"] == "reporta a"
    assert manager["cardinality"] == "0..1:N"


def test_quiet_silencia_avisos(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = tmp_path / "aviso.md"
    spec.write_text("## Entidades\n\n### logs\n- message: text\n", encoding="utf-8")

    assert main([str(spec), "--check", "--allow-no-pk", "--quiet"]) == 0
    assert capsys.readouterr().err == ""


def test_los_errores_van_a_stderr(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    spec = tmp_path / "roto.md"
    spec.write_text(
        "## Entidades\n\n### orders\n- id: int PK\n- user_id: int FK -> users.id\n",
        encoding="utf-8",
    )

    assert main([str(spec)]) == 1
    error = capsys.readouterr().err
    assert "E004" in error
    assert str(spec) in error
