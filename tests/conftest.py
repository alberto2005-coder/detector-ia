"""Fixtures compartidas: un detector falso evita descargar el modelo en las pruebas."""

import pytest

from detector_ia.motores import AnalizadorIA

TEXTO_IA = (
    "### 1. Introduccion al analisis\n\n"
    "El analisis de datos resulta fundamental en el contexto actual. Por tanto, es crucial "
    "comprender que la estadistica descriptiva constituye la base de cualquier estudio "
    "riguroso. A diferencia de los metodos cualitativos, permite cuantificar fenomenos "
    "complejos de manera sistematica y reproducible.\n\n"
    "* **Media aritmetica:** valor central de la distribucion.\n"
    "* **Mediana:** valor que divide la muestra en dos mitades.\n\n"
    "En resumen, cabe destacar que el dominio de estas herramientas \u2014junto con una "
    "interpretacion critica\u2014 permite extraer conclusiones fiables. Asimismo conviene "
    "recordar que la calidad del dato condiciona todo el proceso posterior del estudio.\n"
)

TEXTO_HUMANO = (
    "Bueno pues aqui van mis apuntes de la clase. La media es sumar todo y dividir entre el "
    "numero de datos, lo guay es que la mediana no se ve afectada por los valores raros. "
    "El profe dijo que la desviacion tipica mide cuanto se separan los datos de la media, y "
    "segun el eso pasaria lo mismo con cualquier muestra parecida. Hay cosas que no me "
    "quedan claras, sobre todo cuando hay muchos valores extremos porque lo que hace es "
    "deformar todo el calculo y ya no sabes si fiarte del resultado, la verdad.\n"
)


class DetectorFalso:
    """Imita a transformers.pipeline devolviendo una probabilidad de IA fija."""

    def __init__(self, prob_ia=0.95):
        self.prob_ia = prob_ia
        self.llamadas = []

    def __call__(self, textos, **kwargs):
        if isinstance(textos, str):
            textos = [textos]
        self.llamadas.append(list(textos))
        return [{"label": "AI", "score": self.prob_ia} for _ in textos]


@pytest.fixture
def detector_falso():
    return DetectorFalso()


@pytest.fixture
def analizador(detector_falso):
    return AnalizadorIA(detector=detector_falso)
