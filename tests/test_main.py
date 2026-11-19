import csv
import importlib
import json

import numpy as np
import pytest

from detector_ia import __version__
from detector_ia.main import COLUMNAS, _codigo_salida, _juzgar, main
from tests.conftest import TEXTO_HUMANO, TEXTO_IA

main_modulo = importlib.import_module("detector_ia.main")


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


def test_acepta_la_ruta_de_un_solo_archivo(tmp_path):
    _escribir(tmp_path, "uno.md", TEXTO_IA)
    _escribir(tmp_path, "dos.txt", TEXTO_HUMANO)
    salida = tmp_path / "reporte.csv"

    codigo = main(["-c", str(tmp_path / "uno.md"), "-s", str(salida), "--sin-modelo"])

    assert codigo == 0
    assert [fila["Archivo"] for fila in _leer(salida)] == ["uno.md"]


def test_alias_ruta_hace_lo_mismo_que_carpeta(tmp_path):
    _escribir(tmp_path, "uno.md", TEXTO_IA)
    salida = tmp_path / "reporte.csv"

    codigo = main(["--ruta", str(tmp_path / "uno.md"), "-s", str(salida), "--sin-modelo"])

    assert codigo == 0
    assert len(_leer(salida)) == 1


def test_archivo_no_soportado_no_genera_reporte(tmp_path):
    (tmp_path / "datos.xyz").write_text("contenido", encoding="utf-8")
    salida = tmp_path / "reporte.csv"

    assert main(["-c", str(tmp_path / "datos.xyz"), "-s", str(salida)]) == 0
    assert not salida.exists()


def test_help_incluye_version_ruta_y_autor(capsys):
    with pytest.raises(SystemExit) as salida:
        main(["-h"])
    texto = capsys.readouterr().out
    assert salida.value.code == 0
    assert "--version" in texto
    assert "--ruta" in texto
    assert "Alberto Ortiz Sánchez" in texto


def test_los_alias_en_ingles_funcionan(tmp_path):
    _escribir(tmp_path, "ensayo.md", TEXTO_IA)
    salida = tmp_path / "reporte.csv"

    codigo = main(["--folder", str(tmp_path), "--output", str(salida), "--no-model"])

    assert codigo == 0
    assert [fila["Archivo"] for fila in _leer(salida)] == ["ensayo.md"]


def test_lang_en_traduce_los_mensajes(tmp_path, capsys):
    _escribir(tmp_path, "ensayo.md", TEXTO_IA)
    salida = tmp_path / "reporte.csv"

    main(["-c", str(tmp_path), "-s", str(salida), "--sin-modelo", "--lang", "en"])

    errores = capsys.readouterr().err
    assert "Analysing 1 submission" in errores
    assert "Done! Report saved to" in errores


def test_idioma_es_alias_de_lang(tmp_path, capsys):
    _escribir(tmp_path, "ensayo.md", TEXTO_IA)
    salida = tmp_path / "reporte.csv"

    main(["-c", str(tmp_path), "-s", str(salida), "--sin-modelo", "--idioma", "es"])

    assert "Analizando 1 entrega" in capsys.readouterr().err


def test_fail_on_acepta_el_valor_en_ingles(tmp_path):
    _escribir(tmp_path, "ensayo.md", TEXTO_IA)
    salida = tmp_path / "reporte.csv"

    base = ["-c", str(tmp_path), "-s", str(salida), "--sin-modelo"]
    assert main([*base, "--fail-on", "none"]) == 0
    assert main([*base, "--fail-on", "high"]) == 1


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


# ---------------------------------------------------------------- novedades de la 1.1.0

PARRAFO = (
    "La fotosintesis es el proceso por el que las plantas transforman la luz del sol en energia "
    "quimica. Ocurre en los cloroplastos y necesita agua y dioxido de carbono. El resultado es "
    "glucosa y oxigeno, que la planta libera al aire. Gracias a este proceso existe casi toda la "
    "vida en la Tierra, porque los animales dependen directa o indirectamente de las plantas."
)
TEMA_DISTINTO = (
    "La Revolucion Francesa empezo en 1789 con la toma de la Bastilla y acabo con el poder "
    "absoluto del rey. Entre sus consecuencias estuvo la Declaracion de los Derechos del Hombre, "
    "que defendia la igualdad ante la ley. Mas tarde llegaron el Terror y el ascenso de Napoleon."
)


def _base(tmp_path):
    return ["-c", str(tmp_path), "-s", str(tmp_path / "reporte.csv"), "--sin-modelo"]


def test_las_columnas_nuevas_se_añaden_al_final():
    assert COLUMNAS[:9] == [
        "Archivo", "Formato", "IA_Media (%)", "IA_Pico_Max (%)", "Similitud_Companero (%)",
        "Coincide_Con", "Veredicto", "Fragmento_Sospechoso", "Error",
    ]
    assert COLUMNAS[9:] == [
        "Similitud_Coseno (%)", "Confianza", "Avisos", "Fragmento_Coincidente",
        "Similitud_Traducida (%)",
    ]


def test_una_copia_retocada_se_detecta_y_muestra_el_fragmento(tmp_path):
    _escribir(tmp_path, "ana.txt", PARRAFO)
    _escribir(tmp_path, "luis.txt", PARRAFO.replace("Ocurre en", "Sucede en"))
    _escribir(tmp_path, "marta.txt", TEMA_DISTINTO)

    main(_base(tmp_path))

    filas = {f["Archivo"]: f for f in _leer(tmp_path / "reporte.csv")}
    assert filas["ana.txt"]["Veredicto"] == "REVISAR COPIA ENTRE ALUMNOS"
    assert filas["ana.txt"]["Coincide_Con"] == "luis.txt"
    assert float(filas["ana.txt"]["Similitud_Companero (%)"]) >= 60
    assert "cloroplastos" in filas["ana.txt"]["Fragmento_Coincidente"]
    assert filas["marta.txt"]["Veredicto"] != "REVISAR COPIA ENTRE ALUMNOS"
    assert filas["marta.txt"]["Coincide_Con"] == "Ninguno"


def test_hablar_del_mismo_tema_no_es_copia(tmp_path):
    otro = (
        "Las plantas convierten la energia solar en energia quimica mediante la fotosintesis, "
        "que tiene lugar en los cloroplastos y necesita agua y dioxido de carbono. De ahi salen "
        "glucosa y oxigeno. Casi toda la vida terrestre depende de este proceso, ya que los "
        "animales se alimentan de las plantas, y por eso es tan importante cuidarlas bien."
    )
    _escribir(tmp_path, "ana.txt", PARRAFO)
    _escribir(tmp_path, "luis.txt", otro)

    main(_base(tmp_path))

    for fila in _leer(tmp_path / "reporte.csv"):
        assert fila["Veredicto"] != "REVISAR COPIA ENTRE ALUMNOS"


def test_la_plantilla_base_no_cuenta_como_copia(tmp_path):
    entregas = tmp_path / "entregas"
    entregas.mkdir()
    _escribir(entregas, "ana.txt", PARRAFO)
    _escribir(entregas, "luis.txt", PARRAFO)
    plantilla = _escribir(tmp_path, "enunciado.txt", PARRAFO)

    main(["-c", str(entregas), "-s", str(tmp_path / "con.csv"), "--sin-modelo"])
    main(["-c", str(entregas), "-s", str(tmp_path / "sin.csv"), "--sin-modelo",
          "--base", str(plantilla)])

    assert _leer(tmp_path / "con.csv")[0]["Veredicto"] == "REVISAR COPIA ENTRE ALUMNOS"
    for fila in _leer(tmp_path / "sin.csv"):
        assert fila["Veredicto"] != "REVISAR COPIA ENTRE ALUMNOS"
        assert float(fila["Similitud_Companero (%)"]) == 0


def test_cuadernos_con_el_mismo_codigo_renombrado_se_marcan(tmp_path):
    def cuaderno(nombre_variable, archivo):
        celdas = [
            {"cell_type": "markdown", "source": ["Enunciado\n", "Respuestas: " + "texto " * 30]},
            {"cell_type": "code", "source": [
                "import pandas as pd\n",
                f'{nombre_variable} = pd.read_csv("datos.csv")\n',
                "acumulado = 0\n",
                f"for fila in {nombre_variable}.itertuples():\n",
                "    if fila.importe > 100:\n",
                "        acumulado = acumulado + fila.importe\n",
                'print("Total:", acumulado)\n',
            ]},
        ]
        (tmp_path / archivo).write_text(json.dumps({"cells": celdas}), encoding="utf-8")

    cuaderno("datos", "ana.ipynb")
    cuaderno("tabla", "luis.ipynb")

    main(_base(tmp_path))

    for fila in _leer(tmp_path / "reporte.csv"):
        assert fila["Veredicto"] == "REVISAR COPIA ENTRE ALUMNOS"


def test_informe_html_autocontenido_y_con_el_texto_escapado(tmp_path):
    peligroso = TEXTO_IA + "\n<script>alert('x')</script> & <img src=x onerror=alert(1)>\n"
    _escribir(tmp_path, "ensayo.md", peligroso)
    salida = tmp_path / "informe.html"

    codigo = main([*_base(tmp_path), "--html", str(salida)])

    contenido = salida.read_text(encoding="utf-8")
    assert codigo == 0
    assert contenido.startswith("<!DOCTYPE html>")
    assert "<script>alert" not in contenido
    assert "<img src=x" not in contenido
    assert "&lt;script&gt;alert" in contenido
    # Sin recursos externos: ni scripts, ni hojas de estilo, ni imágenes de internet
    assert "src=\"http" not in contenido and "href=\"http" not in contenido
    assert "ensayo.md" in contenido and "mark" in contenido


def test_informe_html_en_ingles(tmp_path):
    _escribir(tmp_path, "ensayo.md", TEXTO_IA)
    salida = tmp_path / "informe.html"

    main([*_base(tmp_path), "--html", str(salida), "--lang", "en"])

    contenido = salida.read_text(encoding="utf-8")
    assert '<html lang="en">' in contenido
    assert "AI detector report" in contenido
    assert "HIGH AI RISK" in contenido


def test_informe_markdown(tmp_path):
    _escribir(tmp_path, "ensayo.md", TEXTO_IA)
    _escribir(tmp_path, "otro.txt", TEXTO_HUMANO)
    salida = tmp_path / "informe.md"

    main([*_base(tmp_path), "--markdown", str(salida)])

    contenido = salida.read_text(encoding="utf-8")
    assert contenido.startswith("# Informe del detector de IA")
    assert "| Archivo |" in contenido
    assert "ensayo.md" in contenido and "otro.txt" in contenido
    assert "## Casos a revisar" in contenido


def test_el_json_incluye_el_detalle_de_cada_entrega(tmp_path, capsys):
    _escribir(tmp_path, "ensayo.md", TEXTO_IA)

    main([*_base(tmp_path), "--json"])

    datos = json.loads(capsys.readouterr().out)
    detalle = datos["resultados"][0]["Detalle"]
    assert detalle["confianza"] in ("Alta", "Media", "Baja")
    assert detalle["bloques"][0]["puntuacion"] > 0
    assert "version" in datos["resumen"] and "aviso" in datos["resumen"]


def test_la_perplejidad_se_activa_con_su_opcion(tmp_path, monkeypatch):
    class Falso:
        llamadas = 0

        def probabilidades(self, bloques):
            Falso.llamadas += 1
            return [100.0] * len(bloques)

    monkeypatch.setattr(main_modulo, "DetectorPerplejidad", Falso)
    _escribir(tmp_path, "ensayo.md", TEXTO_HUMANO)

    main([*_base(tmp_path), "--perplejidad"])

    assert Falso.llamadas == 1


def test_el_plagio_traducido_avisa_sin_cambiar_el_veredicto(tmp_path, monkeypatch):
    espanol = (
        "El agua hierve a cien grados al nivel del mar en condiciones normales. "
        "Los alumnos entregaron el trabajo la semana pasada sin ningun problema. "
        "Estos resultados confirman lo que explico el profesor durante la clase de ayer. "
        "En el laboratorio medimos la temperatura cada minuto para dibujar la grafica."
    )
    ingles = (
        "The water boils at one hundred degrees at the sea level in normal conditions. "
        "The students handed in the work last week with no problem at all, as the teacher "
        "expected from them. These results confirm what the professor explained in the class "
        "yesterday. In the laboratory we measured the temperature every minute to draw it."
    )

    def codificador_falso(frases):
        # Mismo eje para la frase n-ésima de cada idioma: cuenta como "mismo significado"
        matriz = np.zeros((len(frases), 8))
        for i in range(len(frases)):
            matriz[i, i % 8] = 1.0
        return matriz

    monkeypatch.setattr("detector_ia.semantica.cargar_codificador", lambda: codificador_falso)
    _escribir(tmp_path, "ana.txt", espanol)
    _escribir(tmp_path, "john.txt", ingles)

    main([*_base(tmp_path), "--traduccion"])

    filas = {f["Archivo"]: f for f in _leer(tmp_path / "reporte.csv")}
    assert float(filas["ana.txt"]["Similitud_Traducida (%)"]) >= 35
    assert "traducido" in filas["ana.txt"]["Avisos"]
    assert filas["ana.txt"]["Veredicto"] != "REVISAR COPIA ENTRE ALUMNOS"


def test_juzgar_con_ngramas_marca_la_copia():
    assert _juzgar(0, 0, 10, max_ngramas=60) == "REVISAR COPIA ENTRE ALUMNOS"
    assert _juzgar(0, 0, 10, max_ngramas=59.9) == "Normal"


def test_la_ayuda_muestra_el_autor_y_su_web(capsys):
    with pytest.raises(SystemExit) as salida:
        main(["--help"])
    texto = capsys.readouterr().out
    assert salida.value.code == 0
    assert "Alberto Ortiz Sánchez" in texto
    assert "https://albertoortiz.is-a.dev/" in texto
    assert "https://pypi.org/project/detector-ia/" in texto
    for opcion in ("--html", "--markdown", "--base", "--perplejidad", "--traduccion"):
        assert opcion in texto


def test_h_corto_equivale_a_help(capsys):
    with pytest.raises(SystemExit) as salida:
        main(["-h"])
    assert salida.value.code == 0
    assert "usage: detector-ia" in capsys.readouterr().out


def test_la_version_incluye_el_autor_y_la_web(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
    texto = capsys.readouterr().out
    assert __version__ in texto
    assert "Alberto Ortiz Sánchez" in texto and "albertoortiz.is-a.dev" in texto
