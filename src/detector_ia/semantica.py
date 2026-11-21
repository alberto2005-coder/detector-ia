"""Plagio traducido: frases con el mismo significado en entregas de idiomas distintos.

Es opcional y usa embeddings multilingües (`pip install "detector-ia[semantica]"`). Se compara
cada frase de una entrega con las de la otra y se cuenta cuántas tienen un significado casi
idéntico. Un porcentaje alto entre un texto en español y otro en inglés sugiere traducción,
pero es solo un indicio: dos trabajos sobre el mismo tema también comparten frases parecidas.
"""

import re

import numpy as np

from detector_ia.idioma import t

MODELO_SEMANTICO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

UMBRAL_FRASE = 0.82  # similitud de coseno entre embeddings para dar dos frases por equivalentes
UMBRAL_AVISO = 35.0  # % de frases equivalentes a partir del cual se avisa
MINIMO_PALABRAS = 6
MAXIMO_FRASES = 200

_DIVISOR = re.compile(r"(?<=[.!?])\s+|\n+")


def frases(texto, maximo=MAXIMO_FRASES):
    """Frases con contenido suficiente para compararlas por significado."""
    candidatas = (f.strip() for f in _DIVISOR.split(texto))
    utiles = [f for f in candidatas if len(f.split()) >= MINIMO_PALABRAS]
    return utiles[:maximo]


def cargar_codificador(modelo=MODELO_SEMANTICO):
    """Devuelve una función frases -> matriz de embeddings (carga perezosa del modelo)."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as error:  # depende del extra opcional "semantica"
        raise SystemExit(
            t(
                "Falta el modelo semántico. Instálalo con:\n"
                '  pip install "detector-ia[semantica]"\n'
                "o ejecuta el análisis sin --traduccion.",
                "The semantic model is missing. Install it with:\n"
                '  pip install "detector-ia[semantica]"\n'
                "or run the analysis without --translation.",
            )
        ) from error
    from detector_ia.motores import configurar_cache_modelo

    configurar_cache_modelo()
    transformador = SentenceTransformer(modelo)
    return lambda lista: transformador.encode(lista, show_progress_bar=False)


def _normalizar(matriz):
    matriz = np.asarray(matriz, dtype=float)
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    normas[normas == 0] = 1.0
    return matriz / normas


def similitud_traducida(texto_a, texto_b, codificador, umbral=UMBRAL_FRASE):
    """Devuelve (porcentaje de frases de la entrega menor con equivalente, ejemplos).

    Los ejemplos son hasta tres pares (frase_a, frase_b, similitud) ordenados de mayor
    a menor similitud.
    """
    fa, fb = frases(texto_a), frases(texto_b)
    if not fa or not fb:
        return 0.0, []
    ea = _normalizar(codificador(fa))
    eb = _normalizar(codificador(fb))
    matriz = ea @ eb.T
    # Se mira desde la entrega con menos frases: es la que podría estar contenida en la otra
    if len(fa) <= len(fb):
        mejores = matriz.max(axis=1)
        parejas = matriz.argmax(axis=1)
        pares = [(fa[i], fb[parejas[i]], float(mejores[i])) for i in range(len(fa))]
    else:
        mejores = matriz.max(axis=0)
        parejas = matriz.argmax(axis=0)
        pares = [(fa[parejas[j]], fb[j], float(mejores[j])) for j in range(len(fb))]
    coinciden = [p for p in pares if p[2] >= umbral]
    porcentaje = round(100.0 * len(coinciden) / len(pares), 2)
    coinciden.sort(key=lambda p: p[2], reverse=True)
    return porcentaje, coinciden[:3]
