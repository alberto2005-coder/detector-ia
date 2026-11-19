import numpy as np

from detector_ia import semantica

ES = [
    "El agua hierve a cien grados al nivel del mar en condiciones normales.",
    "Los alumnos entregaron el trabajo la semana pasada sin ningun problema.",
    "La Revolucion Francesa cambio el rumbo politico de toda Europa.",
]
EN = [
    "Water boils at one hundred degrees at sea level under normal conditions.",
    "The students handed in the assignment last week without any problem.",
    "Photosynthesis happens inside the chloroplasts of plant cells every day.",
]


def _codificador():
    """Embeddings falsos: cada frase y su traducción comparten un eje de significado."""
    ejes = {ES[0]: 0, EN[0]: 0, ES[1]: 1, EN[1]: 1, ES[2]: 2, EN[2]: 3}

    def codificar(frases):
        matriz = np.zeros((len(frases), 4))
        for i, frase in enumerate(frases):
            matriz[i, ejes[frase]] = 1.0
        return matriz

    return codificar


def test_frases_descarta_las_demasiado_cortas():
    resultado = semantica.frases("Hola. Esta frase si tiene suficientes palabras para contar.")
    assert resultado == ["Esta frase si tiene suficientes palabras para contar."]


def test_frases_respeta_el_maximo():
    texto = " ".join(f"Esta es la frase numero {n} del texto de prueba." for n in range(10))
    assert len(semantica.frases(texto, maximo=3)) == 3


def test_detecta_frases_equivalentes_entre_idiomas():
    porcentaje, ejemplos = semantica.similitud_traducida(
        " ".join(ES), " ".join(EN), _codificador()
    )
    assert porcentaje == 66.67  # dos de las tres frases tienen equivalente
    assert ejemplos[0][2] == 1.0


def test_textos_sin_relacion_no_dan_coincidencias():
    porcentaje, ejemplos = semantica.similitud_traducida(ES[2], EN[2], _codificador())
    assert (porcentaje, ejemplos) == (0.0, [])


def test_texto_sin_frases_utiles_devuelve_cero():
    assert semantica.similitud_traducida("Hola.", " ".join(EN), _codificador()) == (0.0, [])


def test_el_resultado_es_simetrico_en_porcentaje():
    a, _ = semantica.similitud_traducida(" ".join(ES), " ".join(EN), _codificador())
    b, _ = semantica.similitud_traducida(" ".join(EN), " ".join(ES), _codificador())
    assert a == b
