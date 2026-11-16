import argparse
import glob
import os
import sys

import pandas as pd

from detector_ia.extractores import procesar_archivo
from detector_ia.motores import AnalizadorIA

EXTENSIONES_VALIDAS = (".ipynb", ".pdf", ".docx", ".txt", ".md")
CARPETA_POR_DEFECTO = "revision_ia"
SALIDA_POR_DEFECTO = "reporte_profesional_ia.csv"

TEXTO_MINIMO = 120
UMBRAL_PICO_ALTO = 58
UMBRAL_MEDIA_ALTA = 45
UMBRAL_PICO_SOSPECHOSO = 45
UMBRAL_MEDIA_SOSPECHOSA = 35
UMBRAL_SIMILITUD_COPIA = 88
UMBRAL_SIMILITUD_MOSTRAR = 75


def _parsear_argumentos(argv=None):
    parser = argparse.ArgumentParser(
        prog="detector-ia",
        description=(
            "Detecta indicios de texto generado por IA y posibles copias entre "
            "entregas de alumnos, y genera un reporte CSV."
        ),
        epilog=(
            "Ejemplo: detector-ia --carpeta revision_ia --salida reporte.csv"
        ),
    )
    parser.add_argument(
        "-c",
        "--carpeta",
        default=CARPETA_POR_DEFECTO,
        help=f"Carpeta con las entregas a analizar (por defecto: {CARPETA_POR_DEFECTO}/).",
    )
    parser.add_argument(
        "-s",
        "--salida",
        default=SALIDA_POR_DEFECTO,
        help=f"Ruta del reporte CSV generado (por defecto: {SALIDA_POR_DEFECTO}).",
    )
    parser.add_argument(
        "-m",
        "--modelo",
        default=None,
        help="Modelo de Hugging Face a usar (por defecto, el RoBERTa de detección de IA).",
    )
    return parser.parse_args(argv)


def _juzgar(media_ia, max_ia, max_sim):
    if max_ia >= UMBRAL_PICO_ALTO or media_ia >= UMBRAL_MEDIA_ALTA:
        return "ALTO RIESGO IA"
    if max_sim > UMBRAL_SIMILITUD_COPIA:
        return "REVISAR COPIA ENTRE ALUMNOS"
    if max_ia >= UMBRAL_PICO_SOSPECHOSO or media_ia >= UMBRAL_MEDIA_SOSPECHOSA:
        return "Sospechoso (Revisar)"
    return "Normal"


def main(argv=None):
    # En consolas de Windows (cp1252) los acentos y el ✔ del progreso rompen el print
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

    args = _parsear_argumentos(argv)
    carpeta = args.carpeta

    archivos = sorted(
        f
        for f in glob.glob(os.path.join(carpeta, "*"))
        if f.lower().endswith(EXTENSIONES_VALIDAS)
    )

    if not archivos:
        print(f"No se encontraron archivos compatibles en '{carpeta}/'.")
        return

    analizador = AnalizadorIA() if args.modelo is None else AnalizadorIA(modelo=args.modelo)
    print(f"Analizando {len(archivos)} entregas (Jupyter, PDF, Word, Markdown, TXT)...")

    entregas = []
    for ruta in archivos:
        texto, codigo = procesar_archivo(ruta)
        entregas.append(
            {
                "nombre": os.path.basename(ruta),
                "tipo": os.path.splitext(ruta)[1].upper(),
                "texto": texto,
                "codigo": codigo,
            }
        )

    resultados = []
    for i, item in enumerate(entregas):
        if len(item["texto"]) < TEXTO_MINIMO:
            resultados.append(
                {
                    "Archivo": item["nombre"],
                    "Formato": item["tipo"],
                    "IA_Media (%)": 0,
                    "IA_Pico_Max (%)": 0,
                    "Similitud_Companero (%)": 0,
                    "Coincide_Con": "Ninguno",
                    "Veredicto": "Poco texto",
                    "Fragmento_Sospechoso": "",
                }
            )
            continue

        media_ia, max_ia, fragmento = analizador.evaluar_texto(item["texto"])

        # Compara código si es .ipynb, o texto redactado si es .pdf/.docx/.txt/.md
        max_sim = 0.0
        companero = "Ninguno"
        base_comp = item["codigo"] if item["codigo"] else item["texto"]

        for j, otro in enumerate(entregas):
            if i == j:
                continue
            otro_comp = otro["codigo"] if otro["codigo"] else otro["texto"]
            sim = analizador.similitud_coseno(base_comp, otro_comp)
            if sim > max_sim:
                max_sim = sim
                companero = otro["nombre"]

        veredicto = _juzgar(media_ia, max_ia, max_sim)

        resultados.append(
            {
                "Archivo": item["nombre"],
                "Formato": item["tipo"],
                "IA_Media (%)": media_ia,
                "IA_Pico_Max (%)": max_ia,
                "Similitud_Companero (%)": max_sim,
                "Coincide_Con": companero if max_sim > UMBRAL_SIMILITUD_MOSTRAR else "Ninguno",
                "Veredicto": veredicto,
                "Fragmento_Sospechoso": fragmento,
            }
        )
        print(
            f"✔ [{item['tipo']}] {item['nombre']} -> IA Pico: {max_ia}% | "
            f"Similitud: {max_sim}% ({veredicto})"
        )

    df = pd.DataFrame(resultados)
    df = df.sort_values(
        by=["IA_Pico_Max (%)", "Similitud_Companero (%)"], ascending=False
    )
    carpeta_salida = os.path.dirname(args.salida)
    if carpeta_salida:
        os.makedirs(carpeta_salida, exist_ok=True)
    df.to_csv(args.salida, index=False, sep=";", encoding="utf-8-sig")
    print(f"\n¡Listo! Reporte guardado en '{args.salida}'.")


if __name__ == "__main__":
    main()
