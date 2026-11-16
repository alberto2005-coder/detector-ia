import pytest

from detector_ia.motores import (
    BLOQUE_MINIMO,
    PESO_HUELLA,
    PESO_UNIFORMIDAD,
    AnalizadorIA,
)
from tests.conftest import TEXTO_HUMANO, TEXTO_IA


def test_huella_detecta_marcadores_de_ia(analizador):
    assert analizador._huella_llm_espanol(TEXTO_IA) >= 80


def test_huella_penaliza_senales_humanas(analizador):
    assert analizador._huella_llm_espanol(TEXTO_HUMANO) == 0.0


def test_uniformidad_con_pocas_frases_devuelve_neutro(analizador):
    assert analizador._uniformidad_estadistica("Una sola frase corta.") == 50.0


def test_uniformidad_alta_con_frases_iguales(analizador):
    texto = ". ".join(["Esta frase tiene exactamente ocho palabras ahora"] * 6) + "."
    assert analizador._uniformidad_estadistica(texto) > 80


def test_uniformidad_baja_con_longitudes_muy_distintas(analizador):
    texto = (
        "Corta frase aqui. "
        "Esta otra frase es muchisimo mas larga que la anterior porque encadena muchas "
        "palabras seguidas sin ningun motivo aparente. "
        "Otra. "
        "Y esta ultima tiene un tamano intermedio entre las dos anteriores."
    )
    assert analizador._uniformidad_estadistica(texto) < 60


@pytest.mark.parametrize(
    ("etiqueta", "score", "esperado"),
    [("AI", 0.9, 90.0), ("LABEL_1", 0.8, 80.0), ("Human", 0.9, 10.0), ("LABEL_0", 0.75, 25.0)],
)
def test_prob_ia_interpreta_etiquetas(etiqueta, score, esperado):
    assert AnalizadorIA._prob_ia({"label": etiqueta, "score": score}) == pytest.approx(esperado)


def test_evaluar_texto_pide_los_bloques_en_una_sola_llamada(analizador, detector_falso):
    media, pico, fragmento = analizador.evaluar_texto(TEXTO_IA)
    assert len(detector_falso.llamadas) == 1
    assert isinstance(detector_falso.llamadas[0], list)
    assert media > 0 and pico >= media
    assert fragmento


def test_bloques_demasiado_cortos_se_ignoran(analizador):
    corto = "Texto corto sin patrones claros."
    assert len(corto) < BLOQUE_MINIMO
    assert analizador.evaluar_texto(corto) == (0.0, 0.0, "")


def test_sin_modelo_renormaliza_los_pesos():
    analizador = AnalizadorIA(usar_modelo=False)
    assert analizador.detector is None
    media, pico, _ = analizador.evaluar_texto(TEXTO_IA)
    esperado = (95.0 * PESO_HUELLA + 50.0 * PESO_UNIFORMIDAD) / (PESO_HUELLA + PESO_UNIFORMIDAD)
    assert 0 < pico <= 100
    mensaje = f"el texto de IA deberia puntuar alto sin modelo (media={media}, ref={esperado})"
    assert media > 40, mensaje


def test_similitud_coseno_extremos():
    assert AnalizadorIA.similitud_coseno("hola mundo", "hola mundo") == 100.0
    assert AnalizadorIA.similitud_coseno("hola mundo", "adios planeta") == 0.0
    assert AnalizadorIA.similitud_coseno("", "texto") == 0.0


def test_similitud_coseno_parcial():
    sim = AnalizadorIA.similitud_coseno(
        "la media es el valor central de los datos",
        "la media es un valor central de la muestra",
    )
    assert 50 < sim < 100
