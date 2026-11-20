"""Umbrales ajustados a los textos humanos de cada centro (`--calibrar`).

Los umbrales por defecto salen de un corpus pequeño. Con textos que se sabe que escribió una
persona, se miden sus picos y medias y se fijan los umbrales por encima de lo que esos textos
alcanzan, de modo que el falso positivo sobre ese tipo de texto sea bajo.
"""

import json
import math

POR_DEFECTO = {
    "pico_alto": 58.0,
    "media_alta": 45.0,
    "pico_sospechoso": 45.0,
    "media_sospechosa": 35.0,
}
MINIMO_TEXTOS = 10
MARGEN = 3.0
SEPARACION_ALTO = 10.0
CLAVES = tuple(POR_DEFECTO)


def percentil(valores, p):
    """Percentil con interpolación lineal (p entre 0 y 100)."""
    if not valores:
        raise ValueError("sin valores")
    orden = sorted(valores)
    posicion = (len(orden) - 1) * p / 100
    bajo, alto = math.floor(posicion), math.ceil(posicion)
    return orden[bajo] + (orden[alto] - orden[bajo]) * (posicion - bajo)


def calcular(picos, medias):
    """Umbrales a partir de los picos y medias de textos humanos. Nunca bajan de los defecto."""
    sospechoso = max(POR_DEFECTO["pico_sospechoso"], percentil(picos, 95) + MARGEN)
    media_sosp = max(POR_DEFECTO["media_sospechosa"], percentil(medias, 95) + MARGEN)
    alto = max(POR_DEFECTO["pico_alto"], percentil(picos, 99) + MARGEN,
               sospechoso + SEPARACION_ALTO)
    media_alta = max(POR_DEFECTO["media_alta"], percentil(medias, 99) + MARGEN,
                     media_sosp + SEPARACION_ALTO)
    return {
        "pico_alto": round(alto, 1),
        "media_alta": round(media_alta, 1),
        "pico_sospechoso": round(sospechoso, 1),
        "media_sospechosa": round(media_sosp, 1),
    }


def guardar(ruta, umbrales, textos, version):
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump({"version": version, "textos_humanos": textos, "umbrales": umbrales},
                  archivo, ensure_ascii=False, indent=2)


def cargar(ruta):
    """Lee un JSON de calibración. Lanza ValueError si le faltan claves o no son números."""
    with open(ruta, encoding="utf-8") as archivo:
        datos = json.load(archivo)
    umbrales = datos.get("umbrales", datos)
    resultado = dict(POR_DEFECTO)
    for clave in CLAVES:
        if clave in umbrales:
            valor = umbrales[clave]
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise ValueError(f"umbral '{clave}' no es un número")
            resultado[clave] = float(valor)
    return resultado


def endurecer(umbrales, pico=12.0, media=8.0):
    """Umbrales del modo alta precisión: más exigentes que los activos."""
    return {
        "pico_alto": umbrales["pico_alto"] + pico,
        "media_alta": umbrales["media_alta"] + media,
        "pico_sospechoso": umbrales["pico_sospechoso"] + media,
        "media_sospechosa": umbrales["media_sospechosa"] + media,
    }
