"""Mide el detector contra el corpus etiquetado de `evaluacion/`.

Uso:
    uv run python evaluacion/evaluar.py              # con modelo neuronal
    uv run python evaluacion/evaluar.py --sin-modelo # solo señales estructurales
"""

import argparse
import csv
import sys
from pathlib import Path

from detector_ia.motores import AnalizadorIA

UMBRALES = (45.0, 58.0)
CABECERA = f"{'archivo':<16} {'etiqueta':<9} {'pico':>6} {'media':>6}"


def cargar_etiquetas(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        return [
            (fila["archivo"].strip(), fila["etiqueta"].strip().lower())
            for fila in csv.DictReader(archivo, delimiter=";")
        ]


def metricas(pares, umbral):
    aciertos_ia = falsos_positivos = aciertos_humano = falsos_negativos = 0
    for etiqueta, pico in pares:
        predicho_ia = pico >= umbral
        if etiqueta == "ia":
            aciertos_ia += predicho_ia
            falsos_negativos += not predicho_ia
        else:
            falsos_positivos += predicho_ia
            aciertos_humano += not predicho_ia
    positivos = aciertos_ia + falsos_positivos
    reales_ia = aciertos_ia + falsos_negativos
    return {
        "umbral": umbral,
        "precision": aciertos_ia / positivos if positivos else 0.0,
        "recall": aciertos_ia / reales_ia if reales_ia else 0.0,
        "exactitud": (aciertos_ia + aciertos_humano) / len(pares) if pares else 0.0,
        "falsos_positivos": falsos_positivos,
        "falsos_negativos": falsos_negativos,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evalúa el detector con el corpus etiquetado.")
    parser.add_argument("--corpus", default="evaluacion/textos", help="Carpeta con los textos.")
    parser.add_argument(
        "--etiquetas", default="evaluacion/etiquetas.csv", help="CSV archivo;etiqueta."
    )
    parser.add_argument("--sin-modelo", action="store_true", help="Evalúa sin modelo neuronal.")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    corpus = Path(args.corpus)
    analizador = AnalizadorIA(usar_modelo=not args.sin_modelo)

    print(CABECERA)
    print("-" * len(CABECERA))
    pares = []
    for nombre, etiqueta in cargar_etiquetas(Path(args.etiquetas)):
        texto = (corpus / nombre).read_text(encoding="utf-8")
        media, pico, _ = analizador.evaluar_texto(texto)
        pares.append((etiqueta, pico))
        print(f"{nombre:<16} {etiqueta:<9} {pico:6.2f} {media:6.2f}")

    print(f"\n{'umbral':>7} {'precisión':>10} {'recall':>8} {'exactitud':>10} {'FP':>4} {'FN':>4}")
    print("-" * 48)
    for umbral in UMBRALES:
        m = metricas(pares, umbral)
        print(
            f"{m['umbral']:>7.1f} {m['precision']:>10.2f} {m['recall']:>8.2f} "
            f"{m['exactitud']:>10.2f} {m['falsos_positivos']:>4} {m['falsos_negativos']:>4}"
        )
    print(f"\n{len(pares)} textos del corpus. Un corpus tan pequeño orienta, no valida: "
          "sirve para detectar regresiones al tocar pesos y umbrales.")


if __name__ == "__main__":
    main()
