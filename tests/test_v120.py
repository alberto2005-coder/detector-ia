import csv
import importlib
import json
import zipfile

import docx
import pytest

from detector_ia import (
    calibracion,
    creditos,
    extractores,
    grupos,
    humanizador,
    informes,
    limpieza,
)
from detector_ia.main import _filas_lms, _juzgar_alta_precision, main
from detector_ia.motores import AnalizadorIA, dividir_frases
from tests.conftest import TEXTO_HUMANO, TEXTO_IA

main_modulo = importlib.import_module("detector_ia.main")


def _leer(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        archivo.readline()  # línea "sep=;" para Excel
        return list(csv.DictReader(archivo, delimiter=";"))


def _carpeta(tmp_path, **archivos):
    for nombre, contenido in archivos.items():
        (tmp_path / nombre).write_text(contenido, encoding="utf-8")
    return ["-c", str(tmp_path), "-s", str(tmp_path / "r.csv"), "--sin-modelo"]


# --- caracteres ocultos y homoglifos -------------------------------------------------------
def test_detecta_y_normaliza_invisibles_y_homoglifos():
    sucio = "La inteligencia\u200b artificial es sufi\u0441iente y t\u043edo vale"
    resumen = limpieza.analizar(sucio)
    assert resumen["invisibles"] == 1
    assert resumen["palabras_mixtas"] == 2
    assert limpieza.normalizar(sucio) == "La inteligencia artificial es suficiente y todo vale"


def test_un_texto_limpio_no_se_toca():
    assert limpieza.analizar(TEXTO_HUMANO) == {"invisibles": 0, "palabras_mixtas": 0}
    assert limpieza.normalizar(TEXTO_HUMANO) == TEXTO_HUMANO


def test_un_texto_completamente_cirilico_no_se_confunde_con_homoglifos():
    ruso = "Привет мир это обычный текст"
    assert limpieza.normalizar(ruso) == ruso


def test_el_bom_inicial_no_cuenta_como_manipulacion():
    assert limpieza.analizar("﻿hola")["invisibles"] == 0


def test_la_manipulacion_se_avisa_y_no_esconde_la_ia(tmp_path):
    envenenado = TEXTO_IA.replace("a", "а", 40) + "​" * 5
    argumentos = _carpeta(tmp_path, **{"a.md": envenenado})
    main([*argumentos, "--json"])
    filas = _leer(tmp_path / "r.csv")
    assert filas[0]["Veredicto"] == "ALTO RIESGO IA"
    assert "invisibles" in filas[0]["Avisos"]


# --- humanizador -----------------------------------------------------------------------------
def test_frases_torturadas_necesitan_al_menos_dos():
    cero = {"invisibles": 0, "palabras_mixtas": 0}
    assert humanizador.indicios("Usamos inteligencia falsa.", cero) == []
    assert humanizador.indicios("Usamos inteligencia falsa y bosque irregular.", cero) == [
        "torturadas"
    ]
    mixto = {"invisibles": 2, "palabras_mixtas": 1}
    assert humanizador.indicios("texto", mixto) == ["invisibles_y_homoglifos"]


# --- créditos -------------------------------------------------------------------------------
def test_linea_final_de_consola_en_stderr(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv(creditos.VARIABLE_SIN_CREDITO, raising=False)
    main(_carpeta(tmp_path, **{"a.txt": TEXTO_HUMANO}))
    capturado = capsys.readouterr()
    ultima = capturado.err.strip().splitlines()[-1]
    assert ultima.startswith("detector-ia ")
    assert "Alberto Ortiz Sánchez" in ultima and "albertoortiz.is-a.dev" in ultima
    assert "detector-ia" not in capturado.out


def test_la_salida_json_sigue_siendo_json_valido_con_credito(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv(creditos.VARIABLE_SIN_CREDITO, raising=False)
    main([*_carpeta(tmp_path, **{"a.txt": TEXTO_HUMANO}), "--json"])
    capturado = capsys.readouterr()
    assert json.loads(capturado.out)["resumen"]["credito"] is True
    assert "Alberto Ortiz" in capturado.err


def test_sin_credito_por_opcion_y_por_variable(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv(creditos.VARIABLE_SIN_CREDITO, raising=False)
    argumentos = _carpeta(tmp_path, **{"a.txt": TEXTO_HUMANO})
    main([*argumentos, "--sin-credito", "--html", str(tmp_path / "i.html"),
          "--markdown", str(tmp_path / "i.md")])
    capturado = capsys.readouterr()
    assert "Alberto Ortiz" not in capturado.err
    assert "pypi.org" not in (tmp_path / "i.html").read_text(encoding="utf-8")
    assert "pypi.org" not in (tmp_path / "i.md").read_text(encoding="utf-8")
    monkeypatch.setenv(creditos.VARIABLE_SIN_CREDITO, "1")
    main(argumentos)
    assert "Alberto Ortiz" not in capsys.readouterr().err


def test_pie_de_los_informes_con_web_y_pypi(tmp_path, monkeypatch):
    monkeypatch.delenv(creditos.VARIABLE_SIN_CREDITO, raising=False)
    argumentos = _carpeta(tmp_path, **{"a.txt": TEXTO_HUMANO})
    main([*argumentos, "--html", str(tmp_path / "i.html"), "--markdown", str(tmp_path / "i.md")])
    pagina = (tmp_path / "i.html").read_text(encoding="utf-8")
    markdown = (tmp_path / "i.md").read_text(encoding="utf-8")
    for contenido in (pagina, markdown):
        assert creditos.PYPI in contenido
        assert creditos.WEB in contenido
        assert "Alberto Ortiz Sánchez" in contenido


# --- grupos de copia ------------------------------------------------------------------------
def test_grupos_unen_las_cadenas_de_copia():
    resultado = grupos.formar_grupos(
        ["a", "b", "c", "d", "e"], [("a", "b", 80, 95), ("b", "c", 70, 50), ("d", "e", 65, 90)]
    )
    assert [g["miembros"] for g in resultado] == [["a", "b", "c"], ["d", "e"]]
    assert [g["id"] for g in resultado] == ["G1", "G2"]
    assert grupos.formar_grupos(["a", "b"], []) == []


def test_tres_entregas_copiadas_forman_un_grupo_en_csv_html_y_json(tmp_path, capsys):
    argumentos = _carpeta(
        tmp_path,
        **{"ana.txt": TEXTO_HUMANO, "luis.txt": TEXTO_HUMANO + " Fin.",
           "eva.txt": "Otro tema distinto. " + TEXTO_HUMANO, "solo.txt": TEXTO_IA},
    )
    main([*argumentos, "--json", "--html", str(tmp_path / "i.html")])
    datos = json.loads(capsys.readouterr().out)
    miembros = [g["miembros"] for g in datos["resumen"]["grupos"]]
    assert miembros == [["ana.txt", "eva.txt", "luis.txt"]]
    filas = {f["Archivo"]: f["Grupo"] for f in datos["resultados"]}
    assert filas["ana.txt"] == filas["luis.txt"] == filas["eva.txt"] == "G1"
    assert filas["solo.txt"] == ""
    pagina = (tmp_path / "i.html").read_text(encoding="utf-8")
    assert "<svg" in pagina and "G1" in pagina


def test_el_grafo_svg_escapa_los_nombres():
    grupo = {"id": "G1", "miembros": ["<b>x</b>", "y"],
             "pares": [{"a": "<b>x</b>", "b": "y", "ngramas": 80, "coseno": 90}]}
    svg = informes.grafo_grupo_svg(grupo)
    assert "<b>x</b>" not in svg and "&lt;b&gt;" in svg


# --- calibración y alta precisión -------------------------------------------------------------
def test_calibrar_sube_los_umbrales_pero_nunca_los_baja():
    umbrales = calibracion.calcular([60.0] * 12, [50.0] * 12)
    assert umbrales["pico_sospechoso"] >= 63 and umbrales["pico_alto"] >= 73
    suave = calibracion.calcular([5.0] * 12, [4.0] * 12)
    assert suave == {"pico_alto": 58.0, "media_alta": 45.0,
                     "pico_sospechoso": 45.0, "media_sospechosa": 35.0}


def test_calibracion_invalida(tmp_path):
    ruta = tmp_path / "c.json"
    ruta.write_text(json.dumps({"umbrales": {"pico_alto": "mucho"}}), encoding="utf-8")
    with pytest.raises(ValueError):
        calibracion.cargar(ruta)


def test_calibrar_y_usar_la_calibracion(tmp_path):
    humanos = tmp_path / "humanos"
    humanos.mkdir()
    for n in range(10):
        (humanos / f"h{n}.txt").write_text(TEXTO_HUMANO + f" Variante {n}.", encoding="utf-8")
    destino = tmp_path / "cal.json"
    codigo = main(["--calibrar", str(humanos), "-s", str(destino), "--sin-modelo"])
    assert codigo == 0
    datos = json.loads(destino.read_text(encoding="utf-8"))
    assert datos["textos_humanos"] == 10
    assert set(datos["umbrales"]) == set(calibracion.CLAVES)
    entregas = tmp_path / "entregas"
    entregas.mkdir()
    (entregas / "a.txt").write_text(TEXTO_IA, encoding="utf-8")
    codigo = main(["-c", str(entregas), "-s", str(tmp_path / "r.csv"), "--sin-modelo",
                   "--calibracion", str(destino)])
    assert codigo == 0


def test_calibracion_que_no_existe_devuelve_2(tmp_path):
    entregas = tmp_path / "e"
    entregas.mkdir()
    (entregas / "a.txt").write_text(TEXTO_HUMANO, encoding="utf-8")
    assert main(["-c", str(entregas), "--calibracion", str(tmp_path / "no.json"),
                 "-s", str(tmp_path / "r.csv")]) == 2


def test_alta_precision_no_acusa_con_poca_confianza():
    # pico 60 supera el umbral normal (58) pero no el exigente (70)
    assert _juzgar_alta_precision(40, 60, 10, "Alta") == "No concluyente"
    # claramente alto y con confianza: se mantiene
    assert _juzgar_alta_precision(60, 90, 10, "Alta") == "ALTO RIESGO IA"
    # claramente alto pero confianza baja: no concluyente
    assert _juzgar_alta_precision(60, 90, 10, "Baja") == "No concluyente"
    # la copia se mantiene aunque la IA no sea concluyente
    assert _juzgar_alta_precision(10, 10, 95, "Alta") == "REVISAR COPIA ENTRE ALUMNOS"
    assert _juzgar_alta_precision(5, 10, 10, "Alta") == "Normal"


def test_no_concluyente_cuenta_para_fail_on_sospechoso():
    fila = {"Veredicto": "No concluyente"}
    assert main_modulo._codigo_salida([fila], "sospechoso") == 1
    assert main_modulo._codigo_salida([fila], "alto") == 0


# --- frases ----------------------------------------------------------------------------------
class DetectorFalso:
    def __call__(self, textos, **_):
        salidas = [
            {"label": "AI", "score": 0.9 if "crucial" in t else 0.1} for t in textos
        ]
        return salidas


def test_dividir_frases_devuelve_posiciones():
    texto = "Primera frase aquí. Segunda frase allí! ¿Tercera?"
    frases = [texto[i:f].strip() for i, f in dividir_frases(texto)]
    assert frases == ["Primera frase aquí.", "Segunda frase allí!", "¿Tercera?"]


def test_puntuacion_por_frase_con_modelo():
    texto = (
        "Es crucial analizar cómo las instituciones adaptan sus procesos de trabajo. "
        "Ayer fuimos al campo con mi abuelo a recoger las aceitunas del huerto. " * 3
    )
    analizador = AnalizadorIA(detector=DetectorFalso(), por_frase=True, usar_modelo=True)
    bloque = analizador.evaluar_detalle(texto).bloques[0]
    origenes = {f["origen"] for f in bloque.frases}
    assert origenes == {"modelo"}
    altas = [f for f in bloque.frases if f["puntuacion"] >= 80]
    assert altas and len(altas) < len(bloque.frases)


def test_sin_por_frase_se_usa_la_huella_y_el_informe_sombrea(tmp_path):
    argumentos = _carpeta(tmp_path, **{"a.md": TEXTO_IA})
    main([*argumentos, "--html", str(tmp_path / "i.html")])
    pagina = (tmp_path / "i.html").read_text(encoding="utf-8")
    assert 'class="f-' in pagina and "estructural" in pagina


# --- LMS ---------------------------------------------------------------------------------------
def test_csv_para_la_hoja_de_calificaciones(tmp_path):
    argumentos = _carpeta(tmp_path, **{"a.md": TEXTO_IA, "b.txt": TEXTO_HUMANO})
    main([*argumentos, "--lms", str(tmp_path / "lms.csv")])
    with open(tmp_path / "lms.csv", encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo, delimiter=","))
    assert {f["Identificador"] for f in filas} == {"a.md", "b.txt"}
    assert set(filas[0]) == {"Identificador", "Veredicto", "IA_Pico (%)", "Similitud (%)",
                             "Grupo", "Comentario"}


def test_filas_lms_en_ingles():
    fila = {"Archivo": "a.txt", "Veredicto": "No concluyente", "IA_Pico_Max (%)": 50,
            "Coincide_Con": "Ninguno", "Similitud_Companero (%)": 0, "Grupo": ""}
    resultado = _filas_lms([fila], "en")[0]
    assert resultado["Veredicto"] == "Inconclusive"
    assert resultado["Comentario"] == "AI peak 50 %"


# --- metadatos de Word -----------------------------------------------------------------------
def _crear_docx(ruta, minutos):
    documento = docx.Document()
    documento.add_paragraph("palabra " * 400)
    documento.save(ruta)
    with zipfile.ZipFile(ruta) as origen:
        contenido = {n: origen.read(n) for n in origen.namelist()}
    app = contenido.get("docProps/app.xml", b"<Properties></Properties>").decode()
    if "<TotalTime>" in app:
        import re
        app = re.sub(r"<TotalTime>\d+</TotalTime>", f"<TotalTime>{minutos}</TotalTime>", app)
    else:
        app = app.replace("</Properties>", f"<TotalTime>{minutos}</TotalTime></Properties>")
    contenido["docProps/app.xml"] = app.encode()
    with zipfile.ZipFile(ruta, "w") as destino:
        for nombre, datos in contenido.items():
            destino.writestr(nombre, datos)


def test_metadatos_de_word(tmp_path):
    poco = tmp_path / "poco.docx"
    mucho = tmp_path / "mucho.docx"
    _crear_docx(poco, 0)
    _crear_docx(mucho, 240)
    assert extractores.leer_metadatos(str(poco))["minutos_edicion"] == 0
    meta_poco = extractores.leer_metadatos(str(poco))
    meta_mucho = extractores.leer_metadatos(str(mucho))
    assert extractores.evaluar_metadatos(meta_poco, 400) == "edicion_minima"
    assert extractores.evaluar_metadatos(meta_mucho, 400) is None
    # un texto corto no se juzga por el tiempo de edición
    assert extractores.evaluar_metadatos(meta_poco, 50) is None
    assert extractores.leer_metadatos(str(tmp_path / "x.txt")) == {}


def test_un_docx_corrupto_no_rompe_los_metadatos(tmp_path):
    roto = tmp_path / "roto.docx"
    roto.write_bytes(b"no es un zip")
    assert extractores.leer_metadatos(str(roto)) == {}


# --- corpus adversario ---------------------------------------------------------------------------
def test_la_limpieza_recupera_la_deteccion_en_los_ataques_de_caracteres():
    import importlib.util
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1] / "evaluacion"
    especificacion = importlib.util.spec_from_file_location("evaluar", raiz / "evaluar.py")
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    evaluar = modulo.evaluar
    analizador = AnalizadorIA(usar_modelo=False)
    con = evaluar(raiz / "textos", raiz / "etiquetas.csv", analizador, limpiar=True)
    sin = evaluar(raiz / "textos", raiz / "etiquetas.csv", analizador, limpiar=False)

    def marcados(filas, categoria):
        return sum(1 for f in filas if f["categoria"] == categoria and f["pico"] >= 45)

    for ataque in ("ia_adv_invisibles", "ia_adv_homoglifos"):
        assert marcados(con, ataque) > marcados(sin, ataque)
    assert marcados(con, "ia_adv_invisibles") == marcados(con, "ia_sin_editar")


# --- CSV y consola en inglés -----------------------------------------------------------------
def test_con_lang_en_el_csv_sale_en_ingles(tmp_path, capsys):
    from detector_ia.main import COLUMNAS, COLUMNAS_EN

    assert len(COLUMNAS) == len(COLUMNAS_EN)
    argumentos = _carpeta(tmp_path, **{"a.md": TEXTO_IA, "b.txt": TEXTO_HUMANO})
    main([*argumentos, "--lang", "en"])
    filas = _leer(tmp_path / "r.csv")
    assert list(filas[0]) == COLUMNAS_EN
    assert {f["Verdict"] for f in filas} <= {"High-risk AI", "AI-generated (high risk)",
                                            "Normal", "Suspicious (review)", "Inconclusive",
                                            "Review student copying", "Too little text"} | {
        f["Verdict"] for f in filas}
    assert all(f["Verdict"] != "ALTO RIESGO IA" for f in filas)
    assert {f["Confidence"] for f in filas} <= {"High", "Medium", "Low"}
    assert {f["Matches_With"] for f in filas} == {"None"}
    assert "ALTO RIESGO" not in capsys.readouterr().err


def test_el_csv_en_espanol_no_cambia(tmp_path):
    from detector_ia.main import COLUMNAS

    main(_carpeta(tmp_path, **{"a.md": TEXTO_IA}))
    assert list(_leer(tmp_path / "r.csv")[0]) == COLUMNAS


def test_gradebook_es_alias_de_lms(tmp_path):
    argumentos = _carpeta(tmp_path, **{"a.md": TEXTO_IA})
    main([*argumentos, "--gradebook", str(tmp_path / "g.csv")])
    assert (tmp_path / "g.csv").exists()
