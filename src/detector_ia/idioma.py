"""Idioma activo del programa (es/en) para los mensajes que salen de módulos profundos.

`main` lo fija una vez al empezar; los módulos que no reciben el idioma como argumento
(carga de modelos, calibración) lo consultan aquí.
"""

import os

IDIOMAS = ("es", "en")
VARIABLE = "DETECTOR_IA_LANG"
_actual = "es"


def por_defecto():
    """Idioma de la variable de entorno DETECTOR_IA_LANG, o `es` si falta o no es válida."""
    valor = os.environ.get(VARIABLE, "").strip().lower()[:2]
    return valor if valor in IDIOMAS else "es"


def fijar(idioma):
    global _actual
    _actual = idioma if idioma in IDIOMAS else "es"


def actual():
    return _actual


def t(es, en):
    """Devuelve el texto en el idioma activo."""
    return en if _actual == "en" else es
