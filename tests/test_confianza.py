from detector_ia import confianza
from detector_ia.motores import AnalizadorIA, Bloque, Evaluacion
from tests.conftest import TEXTO_HUMANO, TEXTO_IA


def _bloque(puntuacion, huella=50.0, neuronal=None):
    return Bloque(0, 1500, "x" * 1500, huella, 50.0, neuronal, None, puntuacion)


def _evaluacion(*puntuaciones, huella=50.0, neuronal=None):
    evaluacion = Evaluacion(bloques=[_bloque(p, huella, neuronal) for p in puntuaciones])
    evaluacion.pico = max(puntuaciones)
    evaluacion.media = sum(puntuaciones) / len(puntuaciones)
    return evaluacion


def test_un_solo_bloque_da_confianza_baja():
    nivel, avisos = confianza.evaluar_confianza(_evaluacion(70.0), "texto")
    assert nivel == "Baja"
    assert "pocos_bloques" in avisos


def test_varios_bloques_coherentes_dan_confianza_alta():
    nivel, avisos = confianza.evaluar_confianza(_evaluacion(60.0, 62.0, 58.0), "texto")
    assert (nivel, avisos) == ("Alta", [])


def test_bloques_muy_dispares_sugieren_texto_mixto():
    nivel, avisos = confianza.evaluar_confianza(_evaluacion(10.0, 12.0, 75.0), "texto")
    assert "posible_mixto" in avisos
    assert nivel == "Media"


def test_resultado_alto_que_solo_viene_de_la_uniformidad_da_confianza_baja():
    evaluacion = _evaluacion(60.0, 62.0, 61.0, huella=0.0, neuronal=10.0)
    nivel, avisos = confianza.evaluar_confianza(evaluacion, "texto")
    assert "solo_uniformidad" in avisos
    assert nivel == "Baja"


def test_un_modelo_que_apoya_el_resultado_evita_el_aviso_de_uniformidad():
    evaluacion = _evaluacion(60.0, 62.0, 61.0, huella=0.0, neuronal=90.0)
    assert "solo_uniformidad" not in confianza.evaluar_confianza(evaluacion, "texto")[1]


def test_muchas_citas_generan_aviso():
    cita = "«" + "una frase citada literalmente de un libro de texto " * 4 + "»"
    nivel, avisos = confianza.evaluar_confianza(_evaluacion(30.0, 31.0), cita + " mi opinion")
    assert "citas" in avisos
    assert nivel == "Media"


def test_los_avisos_tienen_mensaje_en_ambos_idiomas():
    for codigo in confianza.AVISOS:
        assert confianza.mensaje(codigo, "es")
        assert confianza.mensaje(codigo, "en")
        assert confianza.mensaje(codigo, "es") != confianza.mensaje(codigo, "en")


def test_integracion_con_el_analizador_sin_modelo():
    analizador = AnalizadorIA(usar_modelo=False)
    for texto in (TEXTO_IA, TEXTO_HUMANO):
        evaluacion = analizador.evaluar_detalle(texto)
        nivel, avisos = confianza.evaluar_confianza(evaluacion, texto)
        assert nivel in confianza.NIVELES
        assert all(codigo in confianza.AVISOS for codigo in avisos)
