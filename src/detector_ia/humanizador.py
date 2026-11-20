"""Indicios de que un texto pasó por un parafraseador o "humanizador".

Es una señal débil y orientativa, no una prueba. Los parafraseadores automáticos sustituyen
términos técnicos por sinónimos que ningún autor escribiría ("frases torturadas", Cabanac y
col.). La lista es corta y se amplía editando `FRASES_TORTURADAS`.
"""

import re

FRASES_TORTURADAS = (
    # español
    "inteligencia falsa", "conciencia falsa", "bosque irregular", "aprendizaje profundo de máquina",
    "mal uso de la información", "enormes datos", "agrupación de k significa",
    "red neuronal profunda profunda", "orden de cosas", "señal de ruido falsa",
    # inglés (documentadas en la literatura)
    "counterfeit consciousness", "fake intelligence", "profound learning",
    "irregular woodland", "bosom peril", "colossal information", "enormous information",
    "flag to commotion", "arbitrary backwoods",
)

MINIMO_FRASES = 2


def frases_torturadas(texto):
    bajo = texto.lower()
    return sorted({f for f in FRASES_TORTURADAS if re.search(re.escape(f), bajo)})


def indicios(texto, limpieza_resumen):
    """Lista de códigos de indicio: `torturadas`, `invisibles_y_homoglifos`."""
    resultado = []
    if len(frases_torturadas(texto)) >= MINIMO_FRASES:
        resultado.append("torturadas")
    if limpieza_resumen["invisibles"] and limpieza_resumen["palabras_mixtas"]:
        resultado.append("invisibles_y_homoglifos")
    return resultado
