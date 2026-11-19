"""Similitud entre entregas: n-gramas con winnowing y localización de fragmentos.

La bolsa de palabras (coseno) marca como parecidos dos trabajos que solo hablan del mismo
tema. Aquí se compara el *orden*: se parte cada entrega en n-gramas de tokens, se eligen
huellas con winnowing (Schleimer, Wilkerson y Aiken, 2003; la idea de MOSS) y se mide qué
parte de la entrega más pequeña aparece en la otra. En el código se normalizan los nombres
de variables, los números y las cadenas, de modo que renombrar variables no esconde la copia.
"""

import hashlib
import keyword
import math
import re
import unicodedata
from collections import Counter

# Parámetros de los n-gramas: tokens por n-grama (k) y ventana del winnowing (w)
K_TEXTO = 5
W_TEXTO = 4
K_CODIGO = 8
W_CODIGO = 4

# Un fragmento coincidente debe tener al menos estos tokens para mostrarse
MINIMO_FRAGMENTO_TEXTO = 12
MINIMO_FRAGMENTO_CODIGO = 20

# Con menos huellas que estas no hay base para afirmar nada
MINIMO_HUELLAS = 3

_PALABRA = re.compile(r"\w+", re.UNICODE)
_CODIGO = re.compile(
    r"""("(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')"""  # cadenas
    r"|([^\W\d]\w*)"  # identificadores y palabras clave
    r"|(\d+(?:\.\d+)?)"  # números
    r"|(\S)",  # operadores y signos
    re.UNICODE,
)
_PALABRAS_CLAVE = frozenset(keyword.kwlist)

_ES = frozenset(
    "el la los las de del que y en un una es por con para se no su al lo como mas pero sus le "
    "ya o este si porque esta entre cuando muy sin sobre tambien me hasta hay donde".split()
)
_EN = frozenset(
    "the of and to in is that it for with as are was on this by be at from or an which have "
    "has not but they their we you can will more all".split()
)


def _sin_acentos(palabra):
    descompuesta = unicodedata.normalize("NFD", palabra)
    return "".join(c for c in descompuesta if unicodedata.category(c) != "Mn")


def tokens_texto(texto):
    """Palabras en minúsculas y sin acentos, con su posición en el texto original."""
    return [
        (_sin_acentos(m.group().lower()), m.start(), m.end())
        for m in _PALABRA.finditer(texto)
    ]


def tokens_codigo(codigo):
    """Código normalizado: nombres -> ID, números -> NUM, cadenas -> STR."""
    resultado = []
    for m in _CODIGO.finditer(codigo):
        cadena, nombre, numero, signo = m.groups()
        if cadena is not None:
            token = "STR"
        elif nombre is not None:
            token = nombre if nombre in _PALABRAS_CLAVE else "ID"
        elif numero is not None:
            token = "NUM"
        else:
            token = signo
        resultado.append((token, m.start(), m.end()))
    return resultado


def _hash(tokens):
    resumen = hashlib.blake2b(" ".join(tokens).encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(resumen, "big")


def hashes_ngramas(tokens, k):
    """Hash de cada n-grama de k tokens consecutivos, en orden."""
    palabras = [t[0] for t in tokens]
    return [_hash(palabras[i:i + k]) for i in range(len(palabras) - k + 1)]


def winnowing(hashes, w):
    """Selecciona el hash mínimo de cada ventana de w hashes (huellas del documento)."""
    if not hashes:
        return set()
    if len(hashes) <= w:
        return {min(hashes)}
    return {min(hashes[i:i + w]) for i in range(len(hashes) - w + 1)}


class Documento:
    """Entrega lista para comparar: tokens, huellas y texto original."""

    def __init__(self, texto, es_codigo=False, excluir=frozenset()):
        self.texto = texto
        self.es_codigo = es_codigo
        self.k = K_CODIGO if es_codigo else K_TEXTO
        self.w = W_CODIGO if es_codigo else W_TEXTO
        self.tokens = tokens_codigo(texto) if es_codigo else tokens_texto(texto)
        self.hashes = hashes_ngramas(self.tokens, self.k)
        # `excluir` son n-gramas del código base/plantilla, que no cuentan como copia
        self.hashes_utiles = [None if h in excluir else h for h in self.hashes]
        self.huellas = winnowing([h for h in self.hashes if h not in excluir], self.w)
        # Los tokens que forman parte de la plantilla tampoco cuentan en la bolsa de palabras,
        # para que el coseno no marque como copia lo que solo es el enunciado compartido
        cubiertos = set()
        for i, h in enumerate(self.hashes):
            if h in excluir:
                cubiertos.update(range(i, i + self.k))
        self.contador = Counter(
            t[0] for i, t in enumerate(self.tokens) if i not in cubiertos
        )

    def bolsa(self):
        return self.contador


def huellas_base(textos, es_codigo=False):
    """Conjunto de n-gramas de la plantilla o enunciado, para excluirlos de la comparación."""
    k = K_CODIGO if es_codigo else K_TEXTO
    conjunto = set()
    for texto in textos:
        tokens = tokens_codigo(texto) if es_codigo else tokens_texto(texto)
        conjunto.update(hashes_ngramas(tokens, k))
    return frozenset(conjunto)


def similitud_ngramas(a, b):
    """Porcentaje de huellas de la entrega más pequeña que aparecen en la otra."""
    if a.es_codigo != b.es_codigo:
        return 0.0
    menor = min(len(a.huellas), len(b.huellas))
    if menor < MINIMO_HUELLAS:
        return 0.0
    return round(100.0 * len(a.huellas & b.huellas) / menor, 2)


def similitud_coseno(texto1, texto2):
    """Coseno entre bolsas de palabras (medida clásica, se mantiene como segunda opinión)."""
    if not texto1 or not texto2:
        return 0.0
    p1 = Counter(re.findall(r"\w+", texto1.lower()))
    p2 = Counter(re.findall(r"\w+", texto2.lower()))
    return _coseno(p1, p2)


def similitud_coseno_docs(a, b):
    return _coseno(a.bolsa(), b.bolsa())


def _coseno(p1, p2):
    comunes = set(p1) & set(p2)
    num = sum(p1[x] * p2[x] for x in comunes)
    den = math.sqrt(sum(v ** 2 for v in p1.values())) * math.sqrt(sum(v ** 2 for v in p2.values()))
    return round((num / den) * 100, 2) if den else 0.0


def fragmentos_comunes(a, b, maximo=3, minimo=None, recorte=400):
    """Pasajes que aparecen en ambas entregas, del más largo al más corto.

    Devuelve diccionarios con el texto en `a` y en `b`, su posición y los tokens que
    coinciden. Los n-gramas de la plantilla (`excluir`) no generan fragmentos.
    """
    if a.es_codigo != b.es_codigo:
        return []
    k = a.k
    minimo = minimo or (MINIMO_FRAGMENTO_CODIGO if a.es_codigo else MINIMO_FRAGMENTO_TEXTO)
    indice = {}
    for posicion, h in enumerate(b.hashes_utiles):
        if h is not None:
            indice.setdefault(h, []).append(posicion)

    palabras_a = [t[0] for t in a.tokens]
    palabras_b = [t[0] for t in b.tokens]
    corridas = []
    i = 0
    while i < len(a.hashes_utiles):
        candidatas = indice.get(a.hashes_utiles[i]) if a.hashes_utiles[i] is not None else None
        if not candidatas:
            i += 1
            continue
        mejor = 0
        mejor_j = None
        for j in candidatas[:20]:
            largo = 0
            while (
                i + largo < len(palabras_a)
                and j + largo < len(palabras_b)
                and palabras_a[i + largo] == palabras_b[j + largo]
            ):
                largo += 1
            if largo > mejor:
                mejor, mejor_j = largo, j
        if mejor >= max(k, minimo):
            corridas.append((i, mejor_j, mejor))
            i += mejor - k + 1
        else:
            i += 1

    corridas.sort(key=lambda c: c[2], reverse=True)
    resultado = []
    for inicio_a, inicio_b, largo in corridas[:maximo]:
        ta = a.tokens[inicio_a:inicio_a + largo]
        tb = b.tokens[inicio_b:inicio_b + largo]
        resultado.append(
            {
                "tokens": largo,
                "inicio_a": ta[0][1],
                "fin_a": ta[-1][2],
                "inicio_b": tb[0][1],
                "fin_b": tb[-1][2],
                "texto_a": _recortar(a.texto[ta[0][1]:ta[-1][2]], recorte),
                "texto_b": _recortar(b.texto[tb[0][1]:tb[-1][2]], recorte),
            }
        )
    return resultado


def _recortar(texto, limite):
    texto = " ".join(texto.split())
    return texto if len(texto) <= limite else texto[: limite - 1].rstrip() + "…"


def detectar_idioma(texto):
    """Heurística por palabras frecuentes: 'es', 'en' o 'desconocido'."""
    palabras = [_sin_acentos(m.group().lower()) for m in _PALABRA.finditer(texto)]
    if len(palabras) < 20:
        return "desconocido"
    es = sum(1 for p in palabras if p in _ES)
    en = sum(1 for p in palabras if p in _EN)
    if es > en * 1.5 and es >= 5:
        return "es"
    if en > es * 1.5 and en >= 5:
        return "en"
    return "desconocido"
