import csv
import json

import pytest

from detector_ia import __version__
from detector_ia.main import COLUMNAS, _codigo_salida, _juzgar, main
from tests.conftest import TEXTO_HUMANO, TEXTO_IA


def _leer(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        return list(csv.DictReader(archivo, delimiter=";"))


def _escribir(carpeta, nombre, contenido):
    ruta = carpeta / nombre
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def test_genera_el_csv_con_las_columnas_esperadas(tmp_path):
    _escribir(tmp_path, "ensayo.md", TEXTO_IA)
    _escribir(tmp_path, "apuntes.txt", TEXTO_HUMANO)
    salida = tmp_path / "reporte.csv"

    codigo = main(["-c", str(tmp_path), "-s", str(salida), "--sin-modelo"])

    assert codigo == 0
    with open(salida, encoding="utf-8-sig", newline="") as archivo:
        cabecera = archivo.readline().strip().split(";")
    assert cabecera == COLUMNAS
    filas = _leer(salida)
    assert len(filas) == 2
    veredictos = {fila["Veredicto"] for fila in filas}
    assert veredictos <= {"ALTO RIESGO IA", "Normal", "Sospechoso (Revisar)"}


def test_un_archivo_corrupto_no_tumba_el_lote(tmp_path):
    (tmp_path / "roto.ipynb").write_text("{no es json", encoding="utf-8")
    _escribir(tmp_path, "bien.txt", TEXTO_HUMANO)
    salida = tmp_path / "reporte.csv"

    codigo = main(["-c", str(tmp_path), "-s", str(salida), "--sin-modelo"])

    assert codigo == 0
    filas = {fila["Archivo"]: fila for fila in _leer(salida)}
    assert filas["roto.ipynb"]["Veredicto"] == "Error"
    assert "JSONDecodeError" in filas["roto.ipynb"]["Error"]
    assert filas["bien.txt"]["Veredicto"] != "Error"


def test_el_mismo_trabajo_en_dos_formatos_no_es_copia(tmp_path):
    _escribir(tmp_path, "duplicado.md", TEXTO_HUMANO)
    _escribir(tmp_path, "duplicado.txt", TEXTO_HUMANO)
    _escribir(tmp_path, "otro.txt", "Texto completamente distinto sobre historia medieval.")
    salida = tmp_path / "reporte.csv"

    main(["-c", str(tmp_path), "-s", str(salida), "--sin-modelo"])

    filas = {fila["Archivo"]: fila for fila in _leer(salida)}
    for nombre in ("duplicado.md", "duplicado.txt"):
        assert float(filas[nombre]["Similitud_Companero (%)"]) < 100
        assert filas[nombre]["Coincide_Con"] == "Ninguno"


def test_texto_corto_se_marca(tmp_path):
    _escribir(tmp_path, "nota.txt", "hola")
    salida = tmp_path / "reporte.csv"

    main(["-c", str(tmp_path), "-s", str(salida), "--sin-modelo"])

    assert _leer(salida)[0]["Veredicto"] == "Poco texto"


def test_version_en_la_cli(capsys):
    with pytest.raises(SystemExit) as salida:
        main(["--version"])
    assert salida.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_sin_archivos_no_genera_reporte(tmp_path):
    salida = tmp_path / "reporte.csv"
    assert main(["-c", str(tmp_path), "-s", str(salida), "--sin-modelo"]) == 0
    assert not salida.exists()


def test_fail_on_alto_devuelve_uno(tmp_path):
    _escribir(tmp_path, "ensayo.md", TEXTO_IA)
    salida = tmp_path / "reporte.csv"

    base = ["-c", str(tmp_path), "-s", str(salida), "--sin-modelo"]
    assert main([*base, "--fail-on", "ninguno"]) == 0
    assert float(_leer(salida)[0]["IA_Pico_Max (%)"]) >= 58
    assert main([*base, "--fail-on", "alto"]) == 1


def test_fail_on_error_devuelve_uno_solo_con_errores(tmp_path):
    (tmp_path / "roto.ipynb").write_text("{no es json", encoding="utf-8")
    _escribir(tmp_path, "bien.txt", TEXTO_HUMANO)
    salida = tmp_path / "reporte.csv"

    assert main(["-c", str(tmp_path), "-s", str(salida), "--sin-modelo", "--fail-on", "error"]) == 1


def test_json_por_la_salida_estandar(tmp_path, capsys):
    _escribir(tmp_path, "ensayo.md", TEXTO_IA)
    salida = tmp_path / "reporte.csv"

    main(["-c", str(tmp_path), "-s", str(salida), "--sin-modelo", "--json"])

    datos = json.loads(capsys.readouterr().out)
    assert datos["resumen"]["total"] == 1
    assert datos["resumen"]["errores"] == 0
    assert datos["resultados"][0]["Archivo"] == "ensayo.md"


@pytest.mark.parametrize(
    ("media", "pico", "similitud", "esperado"),
    [
        (0, 58, 0, "ALTO RIESGO IA"),
        (45, 0, 0, "ALTO RIESGO IA"),
        (0, 0, 88.5, "REVISAR COPIA ENTRE ALUMNOS"),
        (0, 44.9, 88, "Normal"),
        (35, 0, 0, "Sospechoso (Revisar)"),
        (34.9, 44.9, 10, "Normal"),
    ],
)
def test_juzgar_limites(media, pico, similitud, esperado):
    assert _juzgar(media, pico, similitud) == esperado


@pytest.mark.parametrize(
    ("veredictos", "nivel", "esperado"),
    [
        (["Normal"], "ninguno", 0),
        (["Normal"], "alto", 0),
        (["Normal"], "sospechoso", 0),
        (["ALTO RIESGO IA"], "alto", 1),
        (["ALTO RIESGO IA"], "sospechoso", 1),
        (["Sospechoso (Revisar)"], "alto", 0),
        (["Sospechoso (Revisar)"], "sospechoso", 1),
        (["Error"], "error", 1),
        (["Error"], "ninguno", 0),
    ],
)
def test_codigo_salida(veredictos, nivel, esperado):
    assert _codigo_salida([{"Veredicto": v} for v in veredictos], nivel) == esperado
