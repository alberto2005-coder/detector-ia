"""La app debe ser bilingüe de verdad: todo lo que ve el usuario sale en el idioma elegido."""

import csv
import importlib
import json
import re
import sys

import pytest

from detector_ia import confianza, idioma, informes
from detector_ia.main import MENSAJES, main
from tests.conftest import TEXTO_HUMANO, TEXTO_IA

main_modulo = importlib.import_module("detector_ia.main")

# Palabras que solo aparecen en la interfaz en español (no en los textos analizados)
MARCAS_ES = re.compile(
    r"\b(Archivo|Formato|Veredicto|Confianza|Avisos|Similitud|Coincide|Reporte|¡Listo|"
    r"Analizando|entregas|Fragmento|Grupo|Resumen|Informe|Aviso|ALTO RIESGO|REVISAR COPIA|"
    r"Sospechoso|Poco texto|Ninguno|Uso responsable|Bloque|Puntuación)\b"
)


def _entregas(tmp_path):
    (tmp_path / "ia.txt").write_text(TEXTO_IA, encoding="utf-8")
    (tmp_path / "copia.txt").write_text(TEXTO_IA, encoding="utf-8")
    (tmp_path / "humano.txt").write_text(TEXTO_HUMANO, encoding="utf-8")
    (tmp_path / "corto.txt").write_text("hola", encoding="utf-8")
    return str(tmp_path)


def _sin_texto_analizado(contenido):
    """Quita los fragmentos de texto analizado (en español por naturaleza)."""
    contenido = re.sub(r"<style.*?</style>", "", contenido, flags=re.S)
    # claves internas de filtro y ordenación
    contenido = re.sub(r' (?:data-[vo]|value)="[^"]*"', "", contenido)
    contenido = re.sub(r"<(div|blockquote)[^>]*class=\"(texto|frag)[^>]*>.*?</\1>", "",
                       contenido, flags=re.S)
    return "\n".join(
        linea for linea in contenido.splitlines()
        if not linea.lstrip().startswith(("> ", "- «", "La transformación", "Bueno,"))
    )


@pytest.fixture(autouse=True)
def _idioma_limpio(monkeypatch, tmp_path_factory):
    monkeypatch.chdir(tmp_path_factory.mktemp("cwd"))  # el CSV por defecto cae aquí
    monkeypatch.delenv(idioma.VARIABLE, raising=False)
    monkeypatch.delenv("DETECTOR_IA_SIN_CREDITO", raising=False)
    yield
    idioma.fijar("es")


# --- tablas de textos completas ---------------------------------------------------------------
def test_los_mensajes_de_consola_existen_en_los_dos_idiomas():
    assert set(MENSAJES["es"]) == set(MENSAJES["en"])


def test_los_textos_de_los_informes_existen_en_los_dos_idiomas():
    assert set(informes.TEXTOS["es"]) == set(informes.TEXTOS["en"])


def test_todos_los_avisos_y_veredictos_tienen_traduccion():
    for codigo, textos in confianza.AVISOS.items():
        assert len(textos) == 2 and all(textos), codigo
    for veredicto in informes.VEREDICTO_CLASE:
        assert veredicto in informes.VEREDICTO_EN, veredicto
    assert set(main_modulo.CLAVES_JSON_EN) >= set(main_modulo.COLUMNAS)


def test_los_textos_de_evaluar_existen_en_los_dos_idiomas():
    import importlib.util
    from pathlib import Path

    ruta = Path(__file__).resolve().parents[1] / "evaluacion" / "evaluar.py"
    especificacion = importlib.util.spec_from_file_location("evaluar_bi", ruta)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    assert set(modulo.TEXTOS["es"]) == set(modulo.TEXTOS["en"])


# --- salida completa en inglés ----------------------------------------------------------------
def test_todo_sale_en_ingles_con_en(tmp_path, capsys):
    carpeta = _entregas(tmp_path)
    salidas = {n: tmp_path / "out" / n for n in ("r.csv", "i.html", "i.md", "l.csv")}
    (tmp_path / "out").mkdir()
    main(["-c", carpeta, "-s", str(salidas["r.csv"]), "--html", str(salidas["i.html"]),
          "--markdown", str(salidas["i.md"]), "--lms", str(salidas["l.csv"]),
          "--sin-modelo", "--en", "--alta-precision"])
    consola = capsys.readouterr().err
    assert not MARCAS_ES.search(consola), consola
    assert "too little text" in consola
    for nombre, ruta in salidas.items():
        contenido = _sin_texto_analizado(ruta.read_text(encoding="utf-8-sig"))
        assert not MARCAS_ES.search(contenido), (nombre, MARCAS_ES.search(contenido))
    assert 'lang="en"' in salidas["i.html"].read_text(encoding="utf-8")


def test_todo_sale_en_espanol_por_defecto(tmp_path, capsys):
    carpeta = _entregas(tmp_path)
    (tmp_path / "out").mkdir()
    main(["-c", carpeta, "-s", str(tmp_path / "out" / "r.csv"),
          "--html", str(tmp_path / "out" / "i.html"), "--sin-modelo"])
    assert "Analizando" in capsys.readouterr().err
    assert 'lang="es"' in (tmp_path / "out" / "i.html").read_text(encoding="utf-8")


def test_json_en_ingles_tiene_las_claves_traducidas(tmp_path, capsys):
    main(["-c", _entregas(tmp_path), "--json", "--sin-modelo", "--lang", "en"])
    datos = json.loads(capsys.readouterr().out)
    assert set(datos) == {"summary", "results"}
    assert "Verdict" in datos["results"][0] and "Detail" in datos["results"][0]
    assert "blocks" in datos["results"][0]["Detail"]
    assert datos["summary"]["language"] == "en"
    assert {f["Verdict"] for f in datos["results"]} >= {"Too little text"}
    assert "ALTO RIESGO IA" not in json.dumps(datos)


def test_json_en_espanol_no_cambia(tmp_path, capsys):
    main(["-c", _entregas(tmp_path), "--json", "--sin-modelo"])
    datos = json.loads(capsys.readouterr().out)
    assert set(datos) == {"resumen", "resultados"}
    assert "Veredicto" in datos["resultados"][0]


def test_nombre_del_csv_por_defecto_segun_idioma(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    entregas = tmp_path / "e"
    entregas.mkdir()
    (entregas / "a.txt").write_text(TEXTO_HUMANO, encoding="utf-8")
    main(["-c", str(entregas), "--sin-modelo", "--en"])
    main(["-c", str(entregas), "--sin-modelo"])
    assert (tmp_path / "professional_ai_report.csv").exists()
    assert (tmp_path / "reporte_profesional_ia.csv").exists()


def test_cabeceras_del_csv_de_calificaciones(tmp_path):
    (tmp_path / "a.txt").write_text(TEXTO_HUMANO, encoding="utf-8")
    destino = tmp_path / "l.csv"
    main(["-c", str(tmp_path), "-s", str(tmp_path / "r.csv"), "--sin-modelo", "--en",
          "--gradebook", str(destino)])
    with open(destino, encoding="utf-8-sig", newline="") as archivo:
        cabecera = next(csv.reader(archivo))
    assert cabecera == ["Identifier", "Verdict", "AI_Peak (%)", "Similarity (%)", "Group",
                        "Comment"]


# --- selección del idioma -----------------------------------------------------------------------
def test_atajos_es_en_y_la_ultima_gana(tmp_path, capsys):
    carpeta = _entregas(tmp_path)
    main(["-c", carpeta, "-s", str(tmp_path / "r.csv"), "--sin-modelo", "--en", "--es"])
    assert "Analizando" in capsys.readouterr().err
    main(["-c", carpeta, "-s", str(tmp_path / "r.csv"), "--sin-modelo", "--lang", "es", "--en"])
    assert "Analysing" in capsys.readouterr().err


def test_variable_de_entorno_detector_ia_lang(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv(idioma.VARIABLE, "en")
    main(["-c", _entregas(tmp_path), "-s", str(tmp_path / "r.csv"), "--sin-modelo"])
    assert "Analysing" in capsys.readouterr().err
    # un valor inválido se ignora
    monkeypatch.setenv(idioma.VARIABLE, "fr")
    assert idioma.por_defecto() == "es"
    # la opción de la línea de comandos gana a la variable
    monkeypatch.setenv(idioma.VARIABLE, "en")
    main(["-c", _entregas(tmp_path), "-s", str(tmp_path / "r.csv"), "--sin-modelo", "--es"])
    assert "Analizando" in capsys.readouterr().err


# --- ayuda en un solo idioma --------------------------------------------------------------------
def _ayuda(capsys, *argumentos):
    with pytest.raises(SystemExit):
        main([*argumentos, "-h"])
    return capsys.readouterr().out


def test_ayuda_en_ingles_no_mezcla_idiomas(capsys):
    ayuda = _ayuda(capsys, "--en")
    for esperado in ("--perplexity", "--no-model", "--high-precision", "--folder", "options:",
                     "usage:", "FOLDER", "--gradebook", "-t, --text TEXT"):
        assert esperado in ayuda, esperado
    for ajeno in ("--perplejidad", "--sin-modelo", "--alta-precision", "--carpeta", "--texto",
                  "opciones:", "uso:", "Carpeta", "Ejemplos", "Desarrollado"):
        assert ajeno not in ayuda, ajeno


def test_ayuda_en_espanol_no_mezcla_idiomas(capsys):
    ayuda = _ayuda(capsys, "--es")
    for esperado in ("--perplejidad", "--sin-modelo", "--alta-precision", "--carpeta",
                     "opciones:", "uso:", "Ejemplos", "Desarrollado"):
        assert esperado in ayuda, esperado
    for ajeno in ("--perplexity", "--no-model", "--high-precision", "--folder", "Examples",
                  "Developed by", "show this help"):
        assert ajeno not in ayuda, ajeno


def test_ayuda_sin_idioma_es_bilingue(capsys):
    ayuda = _ayuda(capsys)
    for esperado in ("Ejemplos:", "Examples:", "Carpeta con las entregas",
                     "Folder of submissions", "--carpeta", "--folder"):
        assert esperado in ayuda, esperado


def test_sin_flag_de_idioma_todo_lo_demas_sale_en_espanol(tmp_path, capsys):
    main(["-c", _entregas(tmp_path), "-s", str(tmp_path / "r.csv"), "--sin-modelo"])
    assert "Analizando" in capsys.readouterr().err
    assert _leer_cabecera(tmp_path / "r.csv")[0] == "Archivo"


def _leer_cabecera(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        archivo.readline()  # línea "sep=;" para Excel
        return next(csv.reader(archivo, delimiter=";"))


def test_todos_los_alias_siguen_funcionando_aunque_la_ayuda_los_oculte(tmp_path):
    (tmp_path / "a.txt").write_text(TEXTO_HUMANO, encoding="utf-8")
    for alias in ("--sin-modelo", "--no-model"):
        assert main(["-c", str(tmp_path), "-s", str(tmp_path / "r.csv"), alias, "--en"]) == 0


# --- errores de dependencias opcionales ---------------------------------------------------------
@pytest.mark.parametrize("idioma_pedido, trozo", [("es", "Falta el modelo"), ("en", "is missing")])
def test_errores_de_modelos_en_el_idioma_activo(monkeypatch, idioma_pedido, trozo):
    from detector_ia import semantica

    idioma.fijar(idioma_pedido)
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    with pytest.raises(SystemExit) as error:
        semantica.cargar_codificador()
    assert trozo in str(error.value)


def test_error_de_calibracion_invalida_en_ingles(tmp_path, capsys):
    ruta = tmp_path / "c.json"
    ruta.write_text(json.dumps({"umbrales": {"pico_alto": "x"}}), encoding="utf-8")
    (tmp_path / "a.txt").write_text(TEXTO_HUMANO, encoding="utf-8")
    codigo = main(["-c", str(tmp_path), "--calibracion", str(ruta), "--en",
                   "-s", str(tmp_path / "r.csv")])
    assert codigo == 2
    assert "is not a number" in capsys.readouterr().err
