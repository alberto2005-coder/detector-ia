"""Mide el detector contra el corpus etiquetado de `evaluacion/`.

Uso:
    uv run python evaluacion/evaluar.py                    # con modelo neuronal
    uv run python evaluacion/evaluar.py --sin-modelo       # solo señales estructurales
    uv run python evaluacion/evaluar.py --sin-modelo --perplejidad   # + señal Binoculars
    uv run python evaluacion/evaluar.py --sin-modelo --json          # para guardar o comparar

El corpus es sintético (lo escribió una persona con ayuda de un modelo, no son trabajos
reales), así que sirve para detectar regresiones y ver en qué casos falla cada señal, no para
afirmar un porcentaje de acierto. Las etiquetas son `ia`, `humano` y `mixto`; los mixtos se
describen aparte porque no tienen una respuesta binaria correcta.
"""

import argparse
import csv
import json
import sys
from pathlib import Path

from detector_ia import limpieza
from detector_ia.motores import AnalizadorIA

UMBRALES = (45.0, 58.0)
BARRIDO = tuple(float(u) for u in range(30, 81, 5))
CABECERA = f"{'archivo':<22} {'categoria':<17} {'etiq.':<7} {'pico':>6} {'media':>6}"


def cargar_etiquetas(ruta):
    """Lee el CSV y devuelve (archivo, etiqueta, categoria); la categoría es opcional."""
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        return [
            (
                fila["archivo"].strip(),
                fila["etiqueta"].strip().lower(),
                (fila.get("categoria") or fila["etiqueta"]).strip().lower(),
            )
            for fila in csv.DictReader(archivo, delimiter=";")
        ]


def metricas(pares, umbral):
    """Precisión, recall y errores para las etiquetas `ia` y `humano` (ignora `mixto`)."""
    aciertos_ia = falsos_positivos = aciertos_humano = falsos_negativos = 0
    binarios = [(etiqueta, pico) for etiqueta, pico in pares if etiqueta in ("ia", "humano")]
    for etiqueta, pico in binarios:
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
        "exactitud": (aciertos_ia + aciertos_humano) / len(binarios) if binarios else 0.0,
        "falsos_positivos": falsos_positivos,
        "falsos_negativos": falsos_negativos,
    }


def por_categoria(filas, umbral):
    """Resumen de cada categoría: cuántos textos, pico medio y cuántos superan el umbral."""
    categorias = {}
    for fila in filas:
        categorias.setdefault(fila["categoria"], []).append(fila)
    resumen = {}
    for categoria, grupo in categorias.items():
        picos = [f["pico"] for f in grupo]
        resumen[categoria] = {
            "etiqueta": grupo[0]["etiqueta"],
            "textos": len(grupo),
            "pico_medio": round(sum(picos) / len(picos), 2),
            "pico_min": min(picos),
            "pico_max": max(picos),
            "marcados": sum(1 for p in picos if p >= umbral),
        }
    return resumen


def evaluar(corpus, etiquetas, analizador, *, limpiar=True):
    """`limpiar` aplica la normalización de caracteres ocultos y homoglifos, como el CLI."""
    filas = []
    for nombre, etiqueta, categoria in cargar_etiquetas(etiquetas):
        texto = (corpus / nombre).read_text(encoding="utf-8")
        if limpiar:
            texto = limpieza.normalizar(texto)
        media, pico, _ = analizador.evaluar_texto(texto)
        filas.append(
            {"archivo": nombre, "etiqueta": etiqueta, "categoria": categoria,
             "pico": pico, "media": media}
        )
    return filas


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evalúa el detector con el corpus etiquetado.")
    parser.add_argument("--corpus", default="evaluacion/textos", help="Carpeta con los textos.")
    parser.add_argument(
        "--etiquetas", default="evaluacion/etiquetas.csv", help="CSV archivo;etiqueta[;categoria]."
    )
    parser.add_argument("--sin-modelo", action="store_true", help="Evalúa sin modelo neuronal.")
    parser.add_argument(
        "--perplejidad", action="store_true", help="Añade la señal de perplejidad (experimental)."
    )
    parser.add_argument(
        "--sin-limpieza", action="store_true",
        help="No normaliza invisibles ni homoglifos: mide cuánto engañan los ataques.",
    )
    parser.add_argument("--json", action="store_true", help="Resultado en JSON por la salida.")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    perplejidad = None
    if args.perplejidad:
        from detector_ia.perplejidad import DetectorPerplejidad

        perplejidad = DetectorPerplejidad()
    analizador = AnalizadorIA(usar_modelo=not args.sin_modelo, perplejidad=perplejidad)
    filas = evaluar(
        Path(args.corpus), Path(args.etiquetas), analizador, limpiar=not args.sin_limpieza
    )
    pares = [(f["etiqueta"], f["pico"]) for f in filas]

    if args.json:
        resultado = {
            "textos": filas,
            "umbrales": [metricas(pares, u) for u in UMBRALES],
            "barrido": [metricas(pares, u) for u in BARRIDO],
            "categorias": {str(u): por_categoria(filas, u) for u in UMBRALES},
        }
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return

    print(CABECERA)
    print("-" * len(CABECERA))
    for f in filas:
        print(
            f"{f['archivo']:<22} {f['categoria']:<17} {f['etiqueta']:<7} "
            f"{f['pico']:6.2f} {f['media']:6.2f}"
        )

    for umbral in UMBRALES:
        print(f"\nPor categoría (umbral de pico {umbral:.0f}):")
        print(f"{'categoria':<18} {'etiq.':<7} {'n':>3} {'medio':>7} {'min':>6} {'max':>6} "
              f"{'marcados':>9}")
        for categoria, r in por_categoria(filas, umbral).items():
            print(f"{categoria:<18} {r['etiqueta']:<7} {r['textos']:>3} {r['pico_medio']:>7.2f} "
                  f"{r['pico_min']:>6.2f} {r['pico_max']:>6.2f} "
                  f"{r['marcados']:>4}/{r['textos']:<4}")

    print(f"\n{'umbral':>7} {'precisión':>10} {'recall':>8} {'exactitud':>10} {'FP':>4} {'FN':>4}")
    print("-" * 48)
    for umbral in BARRIDO:
        m = metricas(pares, umbral)
        marca = " <" if umbral in UMBRALES else ""
        print(
            f"{m['umbral']:>7.1f} {m['precision']:>10.2f} {m['recall']:>8.2f} "
            f"{m['exactitud']:>10.2f} {m['falsos_positivos']:>4} {m['falsos_negativos']:>4}{marca}"
        )
    binarios = sum(1 for etiqueta, _ in pares if etiqueta in ("ia", "humano"))
    print(
        f"\n{len(pares)} textos ({binarios} con etiqueta ia/humano; los mixtos no entran en "
        "las métricas). Es un corpus sintético y pequeño: orienta y detecta regresiones, "
        "no valida un porcentaje de acierto."
    )


if __name__ == "__main__":
    main()
