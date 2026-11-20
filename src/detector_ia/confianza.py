"""Confianza del resultado y avisos sobre los casos en que el detector se equivoca más.

La confianza NO es la probabilidad de que el veredicto sea correcto: no se puede calcular
con los datos disponibles. Indica cuánta base tiene el análisis (cuánto texto, si las señales
coinciden, si hay citas) para que quien revisa sepa cuánto fiarse del número.
"""

import re

NIVELES = ("Alta", "Media", "Baja")

# Un bloque por debajo de esto no puntúa; con menos de 2 bloques puntuados el resultado es frágil
MINIMO_BLOQUES = 2
# Diferencia entre el bloque más alto y el más bajo que sugiere un texto mixto (humano + IA)
DISPERSION_MIXTO = 35.0
# Con la huella estructural por debajo de esto, un resultado alto descansa solo en la uniformidad
HUELLA_MINIMA_CONFIABLE = 20.0
UMBRAL_SOSPECHOSO = 45.0
# Proporción de texto entre comillas a partir de la cual puede inflar la puntuación
PROPORCION_CITAS = 0.25

_CITAS = re.compile(r"«[^»]{20,}»|“[^”]{20,}”|\"[^\"\n]{20,}\"")

# Código -> (mensaje en español, mensaje en inglés). El CSV usa el español; el HTML, --lang.
AVISOS = {
    "pocos_bloques": (
        "Texto corto: se han puntuado menos de 2 bloques, el resultado es poco estable.",
        "Short text: fewer than 2 blocks were scored, so the result is not stable.",
    ),
    "posible_mixto": (
        "Posible texto mixto: unos bloques puntúan alto y otros bajo; la media lo diluye.",
        "Possibly mixed text: some blocks score high and others low; the mean hides it.",
    ),
    "solo_uniformidad": (
        "La puntuación alta viene solo de la uniformidad de las frases, la señal más débil.",
        "The high score comes only from sentence uniformity, the weakest signal.",
    ),
    "traduccion": (
        "Posible plagio traducido: hay frases con el mismo significado en otra entrega "
        "escrita en otro idioma.",
        "Possible translated plagiarism: some sentences have the same meaning as another "
        "submission written in a different language.",
    ),
    "caracteres_ocultos": (
        "El texto tenía caracteres invisibles o letras de otro alfabeto que imitan letras "
        "latinas; se han normalizado antes de puntuar. Es un truco habitual para despistar "
        "a los detectores.",
        "The text contained invisible characters or letters from another alphabet that mimic "
        "Latin ones; they were normalised before scoring. This is a common trick to fool "
        "detectors.",
    ),
    "posible_humanizador": (
        "Indicios de reescritura automática (frases torturadas o caracteres manipulados). "
        "Señal débil: confírmalo leyendo el texto.",
        "Signs of automatic rewriting (tortured phrases or manipulated characters). Weak "
        "signal: confirm it by reading the text.",
    ),
    "edicion_minima": (
        "El Word registra muy pocos minutos de edición para su extensión; puede haberse "
        "pegado desde otro sitio. Dato orientativo, no prueba nada.",
        "The Word file records very few editing minutes for its length; it may have been "
        "pasted from elsewhere. Indicative only, not proof.",
    ),
    "citas": (
        "Mucho texto entre comillas: las citas formales pueden inflar la puntuación.",
        "A lot of quoted text: formal quotations can inflate the score.",
    ),
}

AVISO_SESGO = (
    "Los detectores fallan más con quien escribe en una lengua que no es la suya, con textos "
    "traducidos y con redacciones muy formales o muy esquemáticas. Un resultado alto es un "
    "motivo para leer el trabajo y hablar con el alumno, no una prueba.",
    "Detectors fail more often with people writing in a language that is not their first, "
    "with translated text and with very formal or very schematic writing. A high result is "
    "a reason to read the work and talk to the student, not evidence.",
)


def evaluar_confianza(evaluacion, texto, extra=()):
    """Devuelve (nivel, códigos de aviso) para una `Evaluacion` y el texto original.

    `extra` son avisos ya detectados fuera (caracteres ocultos, humanizador, metadatos).
    """
    bloques = evaluacion.bloques
    avisos = list(extra)

    if len(bloques) < MINIMO_BLOQUES:
        avisos.append("pocos_bloques")

    puntuaciones = evaluacion.puntuaciones
    if len(bloques) >= 3 and max(puntuaciones) - min(puntuaciones) >= DISPERSION_MIXTO:
        avisos.append("posible_mixto")

    if bloques and evaluacion.pico >= UMBRAL_SOSPECHOSO:
        pico = max(bloques, key=lambda b: b.puntuacion)
        sin_modelo_fuerte = (pico.neuronal or 0) < 50 and (pico.perplejidad or 0) < 50
        if pico.huella < HUELLA_MINIMA_CONFIABLE and sin_modelo_fuerte:
            avisos.append("solo_uniformidad")

    if texto:
        citado = sum(len(m.group()) for m in _CITAS.finditer(texto))
        if citado / len(texto) >= PROPORCION_CITAS:
            avisos.append("citas")

    if "pocos_bloques" in avisos or "solo_uniformidad" in avisos:
        nivel = "Baja"
    elif avisos:
        nivel = "Media"
    else:
        nivel = "Alta"
    return nivel, avisos


def mensaje(codigo, idioma="es"):
    es, en = AVISOS[codigo]
    return en if idioma == "en" else es
