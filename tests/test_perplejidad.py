import math

import numpy as np
import pytest

from detector_ia import perplejidad
from detector_ia.motores import PESO_HUELLA, PESOS_CON_PERPLEJIDAD, AnalizadorIA
from detector_ia.perplejidad import DetectorPerplejidad, probabilidad_ia, puntuacion_binoculars
from tests.conftest import TEXTO_IA


def test_modelos_uniformes_dan_puntuacion_uno():
    # Si ambos modelos reparten la probabilidad por igual, perplejidad y entropía cruzada
    # coinciden y la puntuación es 1 (ni más ni menos predecible que el azar).
    logits = np.zeros((6, 50))
    ids = np.arange(6)
    assert puntuacion_binoculars(logits, logits, ids) == pytest.approx(1.0)


def test_texto_muy_predecible_puntua_bajo():
    # El ejecutor asigna casi toda la probabilidad al token que de verdad aparece, mientras
    # que el observador espera otra cosa: perplejidad baja respecto a la entropía cruzada.
    ids = np.array([3, 3, 3, 3])
    ejecutor = np.full((4, 10), -5.0)
    ejecutor[:, 3] = 5.0
    observador = np.zeros((4, 10))
    assert puntuacion_binoculars(observador, ejecutor, ids) < 0.2


def test_texto_sorprendente_puntua_mas_alto_que_uno_predecible():
    ejecutor = np.full((4, 10), -5.0)
    ejecutor[:, 3] = 5.0
    observador = ejecutor.copy()
    predecible = puntuacion_binoculars(observador, ejecutor, np.array([3, 3, 3, 3]))
    sorprendente = puntuacion_binoculars(observador, ejecutor, np.array([1, 2, 4, 5]))
    assert sorprendente > predecible


def test_sin_tokens_no_hay_puntuacion():
    assert puntuacion_binoculars(np.zeros((0, 5)), np.zeros((0, 5)), np.array([])) is None


def test_los_logits_enormes_no_desbordan():
    logits = np.array([[1000.0, 0.0, -1000.0]] * 3)
    valor = puntuacion_binoculars(logits, logits, np.array([0, 0, 0]))
    assert valor is None or math.isfinite(valor)


@pytest.mark.parametrize(
    ("puntuacion", "esperado"),
    [
        (perplejidad.BINO_ALTO, 100.0),
        (perplejidad.BINO_ALTO - 0.3, 100.0),
        (perplejidad.BINO_BAJO, 0.0),
        (perplejidad.BINO_BAJO + 0.5, 0.0),
        ((perplejidad.BINO_ALTO + perplejidad.BINO_BAJO) / 2, 50.0),
        (None, None),
    ],
)
def test_probabilidad_ia(puntuacion, esperado):
    assert probabilidad_ia(puntuacion) == esperado


def test_el_detector_acepta_un_calculador_inyectado():
    detector = DetectorPerplejidad(calculador=lambda texto: 0.8 if "IA" in texto else 1.2)
    assert detector.probabilidades(["texto IA", "texto humano"]) == [
        probabilidad_ia(0.8),
        0.0,
    ]


def test_los_pesos_con_perplejidad_suman_uno():
    assert sum(PESOS_CON_PERPLEJIDAD.values()) == pytest.approx(1.0)


def test_sin_perplejidad_el_resultado_no_cambia(analizador):
    base = analizador.evaluar_texto(TEXTO_IA)
    explicito = AnalizadorIA(detector=analizador.detector, perplejidad=None)
    assert explicito.evaluar_texto(TEXTO_IA) == base


def test_la_perplejidad_se_integra_en_la_puntuacion():
    alto = DetectorPerplejidad(calculador=lambda texto: 0.7)  # muy parecido a IA
    bajo = DetectorPerplejidad(calculador=lambda texto: 1.3)  # muy humano
    con_alto = AnalizadorIA(usar_modelo=False, perplejidad=alto).evaluar_detalle(TEXTO_IA)
    con_bajo = AnalizadorIA(usar_modelo=False, perplejidad=bajo).evaluar_detalle(TEXTO_IA)
    sin = AnalizadorIA(usar_modelo=False).evaluar_detalle(TEXTO_IA)
    assert con_alto.pico > sin.pico > con_bajo.pico
    assert con_alto.bloques[0].perplejidad == 100.0


def test_si_un_bloque_no_se_puede_puntuar_se_renormaliza_sin_la_perplejidad():
    inservible = DetectorPerplejidad(calculador=lambda texto: None)
    con = AnalizadorIA(usar_modelo=False, perplejidad=inservible).evaluar_detalle(TEXTO_IA)
    huella = con.bloques[0].huella
    uniformidad = con.bloques[0].uniformidad
    esperado = (huella * 0.40 + uniformidad * 0.20) / 0.60
    assert con.bloques[0].perplejidad is None
    assert con.pico == pytest.approx(esperado, abs=0.01)
    assert PESO_HUELLA > 0
