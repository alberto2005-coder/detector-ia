"""Caracteres ocultos y homoglifos: trucos baratos para despistar a un detector.

Los benchmarks de robustez (p. ej. RAID) muestran que insertar espacios de ancho cero o
sustituir letras latinas por cirílicas casi idénticas basta para engañar a muchos detectores.
Aquí se detectan, se avisa y se normaliza el texto antes de puntuarlo.
"""

import re
import unicodedata

INVISIBLES = frozenset(
    "​‌‍⁠­᠎‪‫‬‭‮"
    "⁦⁧⁨⁩﻿"
)

# Letras cirílicas y griegas que se confunden a simple vista con letras latinas
HOMOGLIFOS = {
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y", "х": "x", "і": "i",
    "ј": "j", "ѕ": "s", "ԁ": "d", "ɡ": "g",
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O", "Р": "P",
    "С": "C", "Т": "T", "Х": "X", "І": "I", "Ј": "J", "Ѕ": "S",
    "ο": "o", "Ο": "O", "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I",
    "Κ": "K", "Μ": "M", "Ν": "N", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X", "ν": "v",
}

_PALABRA = re.compile(r"\w+", re.UNICODE)


def _alfabeto(letra):
    try:
        nombre = unicodedata.name(letra)
    except ValueError:
        return ""
    for alfabeto in ("LATIN", "CYRILLIC", "GREEK"):
        if nombre.startswith(alfabeto):
            return alfabeto
    return ""


def _palabra_mixta(palabra):
    alfabetos = {_alfabeto(c) for c in palabra if c.isalpha()} - {""}
    return len(alfabetos) > 1


def analizar(texto):
    """Cuenta invisibles y palabras que mezclan alfabetos (señal de homoglifos)."""
    invisibles = sum(1 for c in texto if c in INVISIBLES and c != "﻿")
    mixtas = sum(1 for m in _PALABRA.finditer(texto) if _palabra_mixta(m.group()))
    return {"invisibles": invisibles, "palabras_mixtas": mixtas}


def hay_manipulacion(resumen):
    return resumen["invisibles"] > 0 or resumen["palabras_mixtas"] > 0


def normalizar(texto):
    """Quita los caracteres ocultos y sustituye los homoglifos dentro de palabras mixtas."""
    texto = "".join(c for c in texto if c not in INVISIBLES)

    def _arreglar(m):
        palabra = m.group()
        if not _palabra_mixta(palabra):
            return palabra
        return "".join(HOMOGLIFOS.get(c, c) for c in palabra)

    return _PALABRA.sub(_arreglar, texto)
