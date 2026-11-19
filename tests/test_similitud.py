import pytest

from detector_ia import similitud
from detector_ia.similitud import Documento
from tests.conftest import TEXTO_HUMANO, TEXTO_IA

PARRAFO_A = (
    "La fotosintesis es el proceso por el que las plantas transforman la luz del sol en energia "
    "quimica. Ocurre en los cloroplastos y necesita agua y dioxido de carbono. El resultado es "
    "glucosa y oxigeno, que la planta libera al aire. Gracias a este proceso existe casi toda la "
    "vida en la Tierra, porque los animales dependen directa o indirectamente de las plantas."
)
PARRAFO_B = (
    "La Revolucion Francesa empezo en 1789 con la toma de la Bastilla y acabo con el poder "
    "absoluto del rey. Entre sus consecuencias estuvo la Declaracion de los Derechos del Hombre, "
    "que defendia la igualdad ante la ley. Mas tarde llegaron el Terror y el ascenso de Napoleon, "
    "que cambiaron por completo el rumbo del pais durante los años siguientes."
)


def test_tokens_texto_normaliza_acentos_y_mayusculas():
    tokens = [t[0] for t in similitud.tokens_texto("Camión, AÑO y Árbol")]
    assert tokens == ["camion", "ano", "y", "arbol"]


def test_tokens_texto_conservan_la_posicion_original():
    texto = "Hola mundo"
    _, inicio, fin = similitud.tokens_texto(texto)[1]
    assert texto[inicio:fin] == "mundo"


def test_tokens_codigo_normalizan_nombres_numeros_y_cadenas():
    tokens = [t[0] for t in similitud.tokens_codigo('total = suma(3.5, "hola")')]
    assert tokens == ["ID", "=", "ID", "(", "NUM", ",", "STR", ")"]


def test_tokens_codigo_conservan_las_palabras_clave():
    tokens = [t[0] for t in similitud.tokens_codigo("for x in datos:")]
    assert tokens[:3] == ["for", "ID", "in"]


def test_winnowing_es_determinista_y_no_vacio():
    hashes = similitud.hashes_ngramas(similitud.tokens_texto(PARRAFO_A), 5)
    assert similitud.winnowing(hashes, 4) == similitud.winnowing(hashes, 4)
    assert len(similitud.winnowing(hashes, 4)) > 3
    assert similitud.winnowing([], 4) == set()


def test_textos_identicos_tienen_similitud_100():
    a, b = Documento(PARRAFO_A), Documento(PARRAFO_A)
    assert similitud.similitud_ngramas(a, b) == 100.0


def test_textos_sobre_temas_distintos_no_se_parecen():
    assert similitud.similitud_ngramas(Documento(PARRAFO_A), Documento(PARRAFO_B)) == 0.0


def test_copia_con_retoques_sigue_siendo_alta():
    retocado = PARRAFO_A.replace("Ocurre en los cloroplastos", "Sucede en los cloroplastos")
    sim = similitud.similitud_ngramas(Documento(PARRAFO_A), Documento(retocado))
    assert 50 < sim < 100


def test_mismo_tema_con_otras_palabras_puntua_menos_en_ngramas_que_en_coseno():
    parafraseado = (
        "Las plantas convierten la energia del sol en energia quimica mediante la fotosintesis, "
        "que tiene lugar en los cloroplastos y que requiere agua y dioxido de carbono. De ahi "
        "salen glucosa y oxigeno, que va a la atmosfera. Casi toda la vida terrestre depende "
        "de este proceso, ya que los animales se alimentan de las plantas."
    )
    a, b = Documento(PARRAFO_A), Documento(parafraseado)
    assert similitud.similitud_ngramas(a, b) < similitud.similitud_coseno_docs(a, b)


def test_la_similitud_ngramas_es_simetrica():
    a, b = Documento(PARRAFO_A), Documento(PARRAFO_A + " " + PARRAFO_B)
    assert similitud.similitud_ngramas(a, b) == similitud.similitud_ngramas(b, a)


def test_texto_demasiado_corto_no_da_similitud():
    assert similitud.similitud_ngramas(Documento("hola mundo"), Documento("hola mundo")) == 0.0


def test_reordenar_parrafos_no_esconde_la_copia():
    a = Documento(PARRAFO_A + " " + PARRAFO_B)
    b = Documento(PARRAFO_B + " " + PARRAFO_A)
    assert similitud.similitud_ngramas(a, b) > 85


CODIGO_A = """
import pandas as pd
datos = pd.read_csv("ventas.csv")
total = 0
for fila in datos.itertuples():
    if fila.importe > 100:
        total = total + fila.importe
print("Total:", total)
"""
CODIGO_RENOMBRADO = """
import pandas as pd
tabla = pd.read_csv("compras.csv")
acumulado = 0
for registro in tabla.itertuples():
    if registro.importe > 250:
        acumulado = acumulado + registro.importe
print("Suma:", acumulado)
"""


def test_renombrar_variables_no_esconde_la_copia_de_codigo():
    a = Documento(CODIGO_A, es_codigo=True)
    b = Documento(CODIGO_RENOMBRADO, es_codigo=True)
    assert similitud.similitud_ngramas(a, b) > 60


def test_comparar_codigo_con_texto_no_da_similitud():
    assert similitud.similitud_ngramas(
        Documento(CODIGO_A, es_codigo=True), Documento(PARRAFO_A)
    ) == 0.0


def test_los_ngramas_de_la_plantilla_no_cuentan_como_copia():
    base = similitud.huellas_base([CODIGO_A], es_codigo=True)
    a = Documento(CODIGO_A, es_codigo=True, excluir=base)
    b = Documento(CODIGO_RENOMBRADO, es_codigo=True, excluir=base)
    assert similitud.similitud_ngramas(a, b) == 0.0


def test_fragmentos_comunes_devuelve_el_pasaje_copiado():
    copia = "Introduccion distinta. " + PARRAFO_A + " Y una conclusion propia que no se parece."
    a, b = Documento(PARRAFO_A), Documento(copia)
    fragmentos = similitud.fragmentos_comunes(a, b)
    assert fragmentos
    mejor = fragmentos[0]
    assert mejor["tokens"] >= 30
    assert "cloroplastos" in mejor["texto_a"] and "cloroplastos" in mejor["texto_b"]
    assert PARRAFO_A[mejor["inicio_a"]:mejor["fin_a"]].startswith("La fotosintesis")


def test_fragmentos_comunes_vacio_si_no_hay_coincidencias():
    assert similitud.fragmentos_comunes(Documento(PARRAFO_A), Documento(PARRAFO_B)) == []


def test_fragmentos_comunes_respeta_el_maximo_y_recorta():
    largo = " ".join([PARRAFO_A] * 3)
    fragmentos = similitud.fragmentos_comunes(
        Documento(largo), Documento(largo), maximo=1, recorte=50
    )
    assert len(fragmentos) == 1
    assert len(fragmentos[0]["texto_a"]) <= 50


def test_similitud_coseno_extremos():
    assert similitud.similitud_coseno("hola mundo", "hola mundo") == 100.0
    assert similitud.similitud_coseno("hola mundo", "adios planeta") == 0.0
    assert similitud.similitud_coseno("", "texto") == 0.0


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        (TEXTO_HUMANO, "es"),
        (TEXTO_IA, "es"),
        (
            "The results of the study show that the students who used the new method were more "
            "likely to finish the course and that they had a better opinion of it than the rest.",
            "en",
        ),
        ("Muy corto", "desconocido"),
    ],
)
def test_detectar_idioma(texto, esperado):
    assert similitud.detectar_idioma(texto) == esperado
