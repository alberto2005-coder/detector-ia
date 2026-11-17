import importlib.util
import pathlib

import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "notas_release", RAIZ / "scripts" / "notas_release.py"
)
notas_release = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(notas_release)


@pytest.fixture(scope="module")
def notas():
    return notas_release.notas("1.0.0")


def test_incluye_la_instalacion_con_pip(notas):
    assert 'pip install "detector-ia[modelo]"' in notas
    assert "pip install detector-ia" in notas


def test_incluye_las_dos_lenguas(notas):
    assert "## Español" in notas
    assert "## English" in notas
    assert "alias en inglés" in notas  # bullet español
    assert "English alias" in notas  # bullet inglés


def test_enlaza_pypi_y_el_repositorio(notas):
    assert notas_release.PYPI in notas
    assert notas_release.REPO in notas


def test_version_inexistente_avisa():
    assert "No hay entrada para la versión 9.9.9" in notas_release.notas("9.9.9")
