from detector_ia import informes
from detector_ia.motores import AnalizadorIA, marcas_huella
from tests.conftest import TEXTO_HUMANO, TEXTO_IA


def test_resaltar_escapa_el_html_y_envuelve_las_marcas():
    texto = "Hola <b>mundo</b> — adiós"
    marcas = [{"inicio": texto.index("—"), "fin": texto.index("—") + 1,
               "tipo": "guion", "etiqueta": "Guion largo"}]
    resultado = informes.resaltar(texto, marcas)
    assert "&lt;b&gt;mundo&lt;/b&gt;" in resultado
    assert '<mark class="m-guion" title="Guion largo">—</mark>' in resultado
    assert "<b>" not in resultado


def test_resaltar_omite_las_marcas_solapadas():
    marcas = [
        {"inicio": 0, "fin": 6, "tipo": "conector", "etiqueta": "a"},
        {"inicio": 3, "fin": 9, "tipo": "guion", "etiqueta": "b"},
    ]
    assert informes.resaltar("abcdefghij", marcas).count("<mark") == 1


def test_resaltar_sin_marcas_devuelve_el_texto_escapado():
    assert informes.resaltar("a & b", []) == "a &amp; b"


def test_marcas_huella_localiza_los_rasgos_de_ia_y_los_humanos():
    marcas = marcas_huella(TEXTO_IA)
    tipos = {m["tipo"] for m in marcas}
    assert {"guion", "lista", "encabezado", "conector"} <= tipos
    for marca in marcas:
        assert TEXTO_IA[marca["inicio"]:marca["fin"]]
    assert any(m["tipo"] == "humana" for m in marcas_huella(TEXTO_HUMANO))


def test_las_marcas_son_coherentes_con_la_huella():
    analizador = AnalizadorIA(usar_modelo=False)
    for texto in (TEXTO_IA, TEXTO_HUMANO):
        hay_ia = any(m["tipo"] != "humana" for m in marcas_huella(texto))
        assert hay_ia == (analizador._huella_llm_espanol(texto) > 0)


def test_evaluar_detalle_devuelve_bloques_con_posiciones_y_marcas():
    texto = TEXTO_IA * 6  # varios bloques
    evaluacion = AnalizadorIA(usar_modelo=False).evaluar_detalle(texto)
    assert len(evaluacion.bloques) >= 2
    assert evaluacion.bloques[0].inicio == 0
    assert evaluacion.bloques[1].inicio == 1500
    assert all(b.marcas for b in evaluacion.bloques)
    assert evaluacion.pico == max(evaluacion.puntuaciones) or abs(
        evaluacion.pico - max(evaluacion.puntuaciones)
    ) < 0.01


def test_evaluar_texto_coincide_con_evaluar_detalle(analizador):
    detalle = analizador.evaluar_detalle(TEXTO_IA)
    assert analizador.evaluar_texto(TEXTO_IA) == (detalle.media, detalle.pico, detalle.fragmento)


def test_informe_html_muestra_los_bloques_las_marcas_y_los_avisos():
    analizador = AnalizadorIA(usar_modelo=False)
    evaluacion = analizador.evaluar_detalle(TEXTO_IA)
    fila = {
        "Archivo": "ensayo.md", "Formato": ".MD", "IA_Media (%)": evaluacion.media,
        "IA_Pico_Max (%)": evaluacion.pico, "Confianza": "Baja",
        "Similitud_Companero (%)": 0, "Coincide_Con": "Ninguno",
        "Veredicto": "ALTO RIESGO IA", "Error": "",
    }
    detalles = {"ensayo.md": {"evaluacion": evaluacion, "avisos": ["pocos_bloques"],
                              "confianza": "Baja", "coincidencia": None, "traducida": None}}
    resumen = {"version": "9.9.9", "modelo": None, "perplejidad": True}

    pagina = informes.informe_html([fila], detalles, resumen, [], "es")

    assert "9.9.9" in pagina
    assert "Señal de perplejidad" in pagina
    assert "m-conector" in pagina
    assert "Texto corto" in pagina


def test_informe_html_de_una_entrega_con_error():
    fila = {
        "Archivo": "roto.ipynb", "Formato": ".IPYNB", "IA_Media (%)": 0, "IA_Pico_Max (%)": 0,
        "Confianza": "", "Similitud_Companero (%)": 0, "Coincide_Con": "Ninguno",
        "Veredicto": "Error", "Error": "JSONDecodeError: <mal>",
    }
    pagina = informes.informe_html(
        [fila], {}, {"version": "1", "modelo": None}, [], "es"
    )
    assert "JSONDecodeError: &lt;mal&gt;" in pagina


def test_detalle_json_vacio_si_no_hay_detalle():
    assert informes.detalle_json(None) == {}
