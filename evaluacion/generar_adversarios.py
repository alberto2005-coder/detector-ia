"""Genera la categoría adversaria del corpus a partir de los textos de IA sin editar.

Cuatro ataques baratos, de los que miden los benchmarks de robustez (RAID):
  - invisibles:  espacios de ancho cero dentro de las palabras
  - homoglifos:  letras latinas sustituidas por cirílicas casi idénticas
  - erratas:     faltas de ortografía y letras intercambiadas
  - orden:       intercambio de palabras contiguas

Es determinista (semilla fija). Uso:
    python evaluacion/generar_adversarios.py
Escribe `evaluacion/textos/adv_<ataque>_<n>.txt` y añade sus filas a `etiquetas.csv`.
"""

import csv
import random
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
TEXTOS = RAIZ / "textos"
ETIQUETAS = RAIZ / "etiquetas.csv"
ORIGEN = "ia_sin_editar"
SEMILLA = 120
HOMOGLIFOS = {"a": "а", "e": "е", "o": "о", "c": "с", "p": "р", "x": "х", "i": "і"}


def invisibles(texto, azar):
    palabras = texto.split(" ")
    return " ".join(
        p[: len(p) // 2] + "​" + p[len(p) // 2:] if len(p) > 3 and azar.random() < 0.5 else p
        for p in palabras
    )


def homoglifos(texto, azar):
    return "".join(
        HOMOGLIFOS[c] if c in HOMOGLIFOS and azar.random() < 0.35 else c for c in texto
    )


def erratas(texto, azar):
    palabras = texto.split(" ")
    for n, p in enumerate(palabras):
        if len(p) > 5 and p.isalpha() and azar.random() < 0.12:
            k = azar.randrange(1, len(p) - 2)
            palabras[n] = p[:k] + p[k + 1] + p[k] + p[k + 2:]
    return " ".join(palabras)


def orden(texto, azar):
    palabras = re.split(r"(\s+)", texto)
    contenido = [i for i, p in enumerate(palabras) if p.strip()]
    for a, b in zip(contenido[::2], contenido[1::2], strict=False):
        if azar.random() < 0.15 and palabras[a].isalpha() and palabras[b].isalpha():
            palabras[a], palabras[b] = palabras[b], palabras[a]
    return "".join(palabras)


ATAQUES = {
    "invisibles": invisibles,
    "homoglifos": homoglifos,
    "erratas": erratas,
    "orden": orden,
}


def main():
    with open(ETIQUETAS, encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo, delimiter=";"))
    filas = [f for f in filas if not f["archivo"].startswith("adv_")]
    origenes = [f["archivo"] for f in filas if f["categoria"] == ORIGEN]
    nuevas = []
    for nombre_ataque, ataque in ATAQUES.items():
        for n, origen in enumerate(origenes, 1):
            azar = random.Random(f"{SEMILLA}-{nombre_ataque}-{origen}")
            texto = (TEXTOS / origen).read_text(encoding="utf-8")
            destino = f"adv_{nombre_ataque}_{n:02d}.txt"
            (TEXTOS / destino).write_text(ataque(texto, azar), encoding="utf-8")
            nuevas.append(
                {"archivo": destino, "etiqueta": "ia", "categoria": f"ia_adv_{nombre_ataque}"}
            )
    with open(ETIQUETAS, "w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(
            archivo, fieldnames=["archivo", "etiqueta", "categoria"], delimiter=";",
            lineterminator="\n",
        )
        escritor.writeheader()
        escritor.writerows(filas + nuevas)
    print(f"{len(nuevas)} textos adversarios generados.")


if __name__ == "__main__":
    main()
