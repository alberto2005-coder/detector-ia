import argparse
import glob
import json
import os
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as version_paquete

import pandas as pd

from detector_ia.extractores import procesar_archivo
from detector_ia.motores import MODELO_POR_DEFECTO, AnalizadorIA

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

VEREDICTOS_ALTO = ("ALTO RIESGO IA", "REVISAR COPIA ENTRE ALUMNOS")

COLUMNAS = [
    "Archivo",
    "Formato",
    "IA_Media (%)",
    "IA_Pico_Max (%)",
    "Similitud_Companero (%)",
    "Coincide_Con",
    "Veredicto",
    "Fragmento_Sospechoso",
    "Error",
]


def _version():
    try:
        return version_paquete("detector-ia")
    except PackageNotFoundError:  # ejecución desde el código sin instalar
        return "0.0.0"


def _parsear_argumentos(argv=None):
    parser = argparse.ArgumentParser(
        prog="detector-ia",
        description=(
            "Detecta indicios de texto generado por IA y posibles copias entre "
            "entregas de alumnos, y genera un reporte CSV."
        ),
        epilog=(
            "Ejemplos:\n"
            "  detector-ia -c revision_ia --salida reporte.csv\n"
            "  detector-ia -c revision_ia/entrega.pdf --sin-modelo\n\n"
            "Autor: Alberto Ortiz Sánchez · Licencia MIT\n"
            "https://github.com/alberto2005-coder/detector-ia"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--carpeta",
        "--ruta",
        dest="carpeta",
        default=CARPETA_POR_DEFECTO,
        help=(
            "Carpeta con las entregas o ruta de un archivo concreto "
            f"(por defecto: {CARPETA_POR_DEFECTO}/)."
        ),
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
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {_version()}",
        help="Muestra la versión y sale.",
    )
    parser.add_argument(
        "--sin-modelo",
        action="store_true",
        help="Analiza solo con las señales estructurales, sin descargar el modelo neuronal.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Escribe el resultado en JSON por la salida estándar y el progreso por la de errores.",
    )
    parser.add_argument(
        "--fail-on",
        choices=("ninguno", "error", "alto", "sospechoso"),
        default="ninguno",
        help=(
            "Devuelve código de salida 1 si el reporte alcanza ese nivel "
            "(por defecto: ninguno, siempre 0)."
        ),
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


def _sin_extension(nombre):
    return os.path.splitext(os.path.basename(nombre))[0].strip().lower()


def _listar_archivos(ruta):
    """Acepta una carpeta con entregas o la ruta de un único archivo."""
    if os.path.isfile(ruta):
        candidatos = [ruta]
    else:
        candidatos = sorted(glob.glob(os.path.join(ruta, "*")))
    return [c for c in candidatos if c.lower().endswith(EXTENSIONES_VALIDAS)]


def _fila(datos):
    fila = {columna: "" for columna in COLUMNAS}
    fila.update({"IA_Media (%)": 0, "IA_Pico_Max (%)": 0, "Similitud_Companero (%)": 0,
                 "Coincide_Con": "Ninguno"})
    fila.update(datos)
    return fila


def _imprimir(mensaje):
    print(mensaje, file=sys.stderr, flush=True)


def _codigo_salida(resultados, nivel):
    """Traduce el nivel pedido en --fail-on al código de salida del proceso."""
    if nivel == "ninguno":
        return 0
    veredictos = [fila["Veredicto"] for fila in resultados]
    if "Error" in veredictos:
        return 1
    if nivel == "error":
        return 0
    if any(v in VEREDICTOS_ALTO for v in veredictos):
        return 1
    if nivel == "alto":
        return 0
    return 1 if "Sospechoso (Revisar)" in veredictos else 0


def main(argv=None):
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

    args = _parsear_argumentos(argv)
    ruta = args.carpeta

    archivos = _listar_archivos(ruta)

    if not archivos:
        _imprimir(f"No se encontraron archivos compatibles en '{ruta}'.")
        return 0

    analizador = AnalizadorIA(
        modelo=args.modelo or MODELO_POR_DEFECTO,
        usar_modelo=not args.sin_modelo,
    )
    cuantas = "entrega" if len(archivos) == 1 else "entregas"
    _imprimir(f"Analizando {len(archivos)} {cuantas} (Jupyter, PDF, Word, Markdown, TXT)...")

    resultados = []
    validas = []

    for ruta in archivos:
        nombre = os.path.basename(ruta)
        tipo = os.path.splitext(ruta)[1].upper()
        try:
            texto, codigo = procesar_archivo(ruta)
        except Exception as error:  # un archivo roto no debe tumbar el lote
            resultados.append(
                _fila(
                    {
                        "Archivo": nombre,
                        "Formato": tipo,
                        "Veredicto": "Error",
                        "Error": f"{type(error).__name__}: {error}",
                    }
                )
            )
            _imprimir(f"✖ [{tipo}] {nombre} -> no se pudo leer: {error}")
            continue

        if len(texto) < TEXTO_MINIMO:
            resultados.append(
                _fila({"Archivo": nombre, "Formato": tipo, "Veredicto": "Poco texto"})
            )
            continue

        validas.append({"nombre": nombre, "tipo": tipo, "texto": texto, "codigo": codigo})

    for i, item in enumerate(validas):
        try:
            media_ia, max_ia, fragmento = analizador.evaluar_texto(item["texto"])

            # Compara código si es .ipynb, o texto redactado si es .pdf/.docx/.txt/.md
            max_sim = 0.0
            companero = "Ninguno"
            base_comp = item["codigo"] if item["codigo"] else item["texto"]
            nombre_base = _sin_extension(item["nombre"])

            for j, otro in enumerate(validas):
                if i == j:
                    continue
                # El mismo trabajo entregado en dos formatos (p. ej. PDF y TXT) no es copia
                if _sin_extension(otro["nombre"]) == nombre_base:
                    continue
                otro_comp = otro["codigo"] if otro["codigo"] else otro["texto"]
                sim = analizador.similitud_coseno(base_comp, otro_comp)
                if sim > max_sim:
                    max_sim = sim
                    companero = otro["nombre"]

            veredicto = _juzgar(media_ia, max_ia, max_sim)
            coincidencia = companero if max_sim > UMBRAL_SIMILITUD_MOSTRAR else "Ninguno"
            resultados.append(
                _fila(
                    {
                        "Archivo": item["nombre"],
                        "Formato": item["tipo"],
                        "IA_Media (%)": media_ia,
                        "IA_Pico_Max (%)": max_ia,
                        "Similitud_Companero (%)": max_sim,
                        "Coincide_Con": coincidencia,
                        "Veredicto": veredicto,
                        "Fragmento_Sospechoso": fragmento,
                    }
                )
            )
            _imprimir(
                f"✔ [{item['tipo']}] {item['nombre']} -> IA Pico: {max_ia}% | "
                f"Similitud: {max_sim}% ({veredicto})"
            )
        except Exception as error:  # fallo al puntuar: se anota y se sigue
            resultados.append(
                _fila(
                    {
                        "Archivo": item["nombre"],
                        "Formato": item["tipo"],
                        "Veredicto": "Error",
                        "Error": f"{type(error).__name__}: {error}",
                    }
                )
            )
            _imprimir(f"✖ [{item['tipo']}] {item['nombre']} -> no se pudo puntuar: {error}")

    df = pd.DataFrame(resultados, columns=COLUMNAS)
    df = df.sort_values(
        by=["IA_Pico_Max (%)", "Similitud_Companero (%)"], ascending=False
    )
    carpeta_salida = os.path.dirname(args.salida)
    if carpeta_salida:
        os.makedirs(carpeta_salida, exist_ok=True)
    df.to_csv(args.salida, index=False, sep=";", encoding="utf-8-sig")

    errores = sum(1 for fila in resultados if fila["Veredicto"] == "Error")
    resumen = {
        "ruta": ruta,
        "reporte": args.salida,
        "modelo": None if args.sin_modelo else (args.modelo or MODELO_POR_DEFECTO),
        "total": len(resultados),
        "errores": errores,
    }

    if args.json:
        salida_json = {"resumen": resumen, "resultados": resultados}
        print(json.dumps(salida_json, ensure_ascii=False, indent=2))
    else:
        _imprimir(f"\n¡Listo! Reporte guardado en '{args.salida}'.")
    if errores:
        _imprimir(f"Aviso: {errores} archivo(s) no se pudieron analizar (ver columna Error).")

    return _codigo_salida(resultados, args.fail_on)


if __name__ == "__main__":
    raise SystemExit(main())
