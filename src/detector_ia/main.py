import argparse
import glob
import json
import os
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as version_paquete

import pandas as pd

from detector_ia import (
    calibracion,
    confianza,
    creditos,
    grupos,
    humanizador,
    informes,
    limpieza,
    semantica,
    similitud,
)
from detector_ia.creditos import AUTOR, GITHUB_AUTOR, PYPI, REPOSITORIO, WEB
from detector_ia.extractores import evaluar_metadatos, leer_metadatos, procesar_archivo
from detector_ia.motores import MODELO_POR_DEFECTO, AnalizadorIA
from detector_ia.perplejidad import DetectorPerplejidad

EXTENSIONES_VALIDAS = (".ipynb", ".pdf", ".docx", ".txt", ".md")
CARPETA_POR_DEFECTO = "revision_ia"
SALIDA_POR_DEFECTO = "reporte_profesional_ia.csv"

TEXTO_MINIMO = 120
UMBRAL_PICO_ALTO = 58
UMBRAL_MEDIA_ALTA = 45
UMBRAL_PICO_SOSPECHOSO = 45
UMBRAL_MEDIA_SOSPECHOSA = 35
UMBRAL_SIMILITUD_COPIA = 88  # coseno de bolsas de palabras
UMBRAL_SIMILITUD_MOSTRAR = 75
UMBRAL_NGRAMAS_COPIA = 60  # n-gramas con winnowing: % de huellas de la entrega menor compartidas
UMBRAL_NGRAMAS_MOSTRAR = 40
MAXIMO_PARES_INFORME = 15

VEREDICTOS_ALTO = ("ALTO RIESGO IA", "REVISAR COPIA ENTRE ALUMNOS")
VEREDICTOS_SOSPECHA = ("Sospechoso (Revisar)", "No concluyente")

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
    # Añadidas en la 1.1.0 (al final para no mover las columnas anteriores)
    "Similitud_Coseno (%)",
    "Confianza",
    "Avisos",
    "Fragmento_Coincidente",
    "Similitud_Traducida (%)",
    # Añadidas en la 1.2.0
    "Grupo",
]

# Cabeceras del CSV con --lang en (mismo orden que COLUMNAS)
COLUMNAS_EN = [
    "File",
    "Format",
    "AI_Mean (%)",
    "AI_Peak_Max (%)",
    "Peer_Similarity (%)",
    "Matches_With",
    "Verdict",
    "Suspicious_Fragment",
    "Error",
    "Cosine_Similarity (%)",
    "Confidence",
    "Warnings",
    "Matching_Fragment",
    "Translated_Similarity (%)",
    "Group",
]


def _traducir_filas(resultados, idioma):
    """Con `--lang en`, cabeceras y valores del CSV en inglés. El resto del programa usa
    los nombres en español internamente, así que solo se traduce al escribir."""
    if idioma != "en":
        return pd.DataFrame(resultados, columns=COLUMNAS)
    filas = []
    for fila in resultados:
        nueva = dict(fila)
        nueva["Veredicto"] = informes.nombre_veredicto(fila["Veredicto"], "en")
        nueva["Confianza"] = informes.CONFIANZA_EN.get(fila["Confianza"], fila["Confianza"])
        if fila["Coincide_Con"] == "Ninguno":
            nueva["Coincide_Con"] = "None"
        filas.append(nueva)
    df = pd.DataFrame(filas, columns=COLUMNAS)
    df.columns = COLUMNAS_EN
    return df

# Los valores de --fail-on se aceptan en español y en inglés
NIVELES_FAIL_ON = {
    "ninguno": "ninguno",
    "none": "ninguno",
    "error": "error",
    "alto": "alto",
    "high": "alto",
    "sospechoso": "sospechoso",
    "suspicious": "sospechoso",
}

MENSAJES = {
    "es": {
        "analizando": "Analizando {n} {unidad} (Jupyter, PDF, Word, Markdown, TXT)...",
        "entrega": "entrega",
        "entregas": "entregas",
        "sin_archivos": "No se encontraron archivos compatibles en '{ruta}'.",
        "listo": "\n¡Listo! Reporte guardado en '{salida}'.",
        "aviso_errores": "Aviso: {n} archivo(s) no se pudieron analizar (ver columna Error).",
        "error_lectura": "✖ [{tipo}] {nombre} -> no se pudo leer: {error}",
        "error_puntuacion": "✖ [{tipo}] {nombre} -> no se pudo puntuar: {error}",
        "resultado": "✔ [{tipo}] {nombre} -> IA Pico: {pico}% | Similitud: {sim}% ({veredicto})",
        "html_listo": "Informe HTML guardado en '{ruta}'.",
        "md_listo": "Informe Markdown guardado en '{ruta}'.",
        "cargando_semantico": "Cargando modelo semántico para el plagio traducido...",
        "cargando_perplejidad": "Cargando modelos de perplejidad (experimental)...",
        "base_vacia": "Aviso: no se pudo leer nada de la plantilla base '{ruta}'.",
        "lms_listo": "CSV para la hoja de calificaciones guardado en '{ruta}'.",
        "calibrando": "Calibrando con {n} textos humanos de '{ruta}'...",
        "calibracion_pocos": (
            "Aviso: con menos de {minimo} textos la calibración es poco fiable; "
            "usa más textos humanos."
        ),
        "calibracion_lista": (
            "Calibración guardada en '{ruta}': pico alto {pico_alto}, pico sospechoso "
            "{pico_sospechoso}, media alta {media_alta}, media sospechosa {media_sospechosa}."
        ),
        "calibracion_sin_textos": "No hay textos legibles en '{ruta}' para calibrar.",
        "calibracion_invalida": "No se pudo leer la calibración '{ruta}': {error}",
        "grupos_detectados": "Grupos de copia detectados: {n}.",
    },
    "en": {
        "analizando": "Analysing {n} {unidad} (Jupyter, PDF, Word, Markdown, TXT)...",
        "entrega": "submission",
        "entregas": "submissions",
        "sin_archivos": "No supported files found in '{ruta}'.",
        "listo": "\nDone! Report saved to '{salida}'.",
        "aviso_errores": "Warning: {n} file(s) could not be analysed (see the Error column).",
        "error_lectura": "✖ [{tipo}] {nombre} -> could not read it: {error}",
        "error_puntuacion": "✖ [{tipo}] {nombre} -> could not score it: {error}",
        "resultado": "✔ [{tipo}] {nombre} -> AI Peak: {pico}% | Similarity: {sim}% ({veredicto})",
        "html_listo": "HTML report saved to '{ruta}'.",
        "md_listo": "Markdown report saved to '{ruta}'.",
        "cargando_semantico": "Loading the semantic model for translated plagiarism...",
        "cargando_perplejidad": "Loading the perplexity models (experimental)...",
        "base_vacia": "Warning: nothing could be read from the base template '{ruta}'.",
        "lms_listo": "Gradebook CSV saved to '{ruta}'.",
        "calibrando": "Calibrating with {n} human texts from '{ruta}'...",
        "calibracion_pocos": (
            "Warning: with fewer than {minimo} texts calibration is unreliable; "
            "use more human texts."
        ),
        "calibracion_lista": (
            "Calibration saved to '{ruta}': high peak {pico_alto}, suspicious peak "
            "{pico_sospechoso}, high mean {media_alta}, suspicious mean {media_sospechosa}."
        ),
        "calibracion_sin_textos": "No readable texts in '{ruta}' to calibrate.",
        "calibracion_invalida": "Could not read the calibration '{ruta}': {error}",
        "grupos_detectados": "Copy groups detected: {n}.",
    },
}


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
            "entregas de alumnos, y genera un reporte CSV.\n"
            "Detects AI-generated text and possible copying between student "
            "submissions, and produces a CSV report."
        ),
        epilog=(
            "Ejemplos / Examples:\n"
            "  detector-ia -c revision_ia --salida reporte.csv\n"
            "  detector-ia -c revision_ia/entrega.pdf --sin-modelo\n"
            "  detector-ia --folder entregas --output reporte.csv --lang en\n"
            "  detector-ia -c entregas --html informe.html --base enunciado.ipynb\n\n"
            f"Desarrollado por / Developed by {AUTOR}\n"
            f"  Web / Website: {WEB}\n"
            f"  GitHub:        {GITHUB_AUTOR}\n"
            f"  PyPI:          {PYPI}\n"
            f"  Código / Source: {REPOSITORIO}\n"
            f"  Incidencias / Issues: {REPOSITORIO}/issues\n"
            "Licencia / License: MIT"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--carpeta",
        "--ruta",
        "--folder",
        "--path",
        dest="carpeta",
        default=CARPETA_POR_DEFECTO,
        help=(
            "Carpeta con las entregas o ruta de un archivo "
            f"(por defecto/default: {CARPETA_POR_DEFECTO}/). "
            "Folder of submissions or path to a single file."
        ),
    )
    parser.add_argument(
        "-s",
        "--salida",
        "--output",
        dest="salida",
        default=SALIDA_POR_DEFECTO,
        help=(
            "Ruta del reporte CSV · CSV report path "
            f"(por defecto/default: {SALIDA_POR_DEFECTO})."
        ),
    )
    parser.add_argument(
        "-m",
        "--modelo",
        "--model",
        dest="modelo",
        default=None,
        help="Modelo de Hugging Face · Hugging Face model (default: AI-detection RoBERTa).",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {_version()}\n{AUTOR} · {WEB}",
        help="Muestra la versión y sale · Print the version and exit.",
    )
    parser.add_argument(
        "--sin-modelo",
        "--no-model",
        dest="sin_modelo",
        action="store_true",
        help=(
            "Analiza solo con las señales estructurales, sin descargar el modelo · "
            "Structural signals only, no model download."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help=(
            "Resultado en JSON por la salida estándar y progreso por la de errores · "
            "JSON on stdout and progress on stderr."
        ),
    )
    parser.add_argument(
        "--html",
        dest="html",
        metavar="RUTA",
        default=None,
        help=(
            "Guarda además un informe HTML autocontenido · "
            "Also save a self-contained HTML report."
        ),
    )
    parser.add_argument(
        "--markdown",
        "--md",
        dest="markdown",
        metavar="RUTA",
        default=None,
        help="Guarda además un informe Markdown · Also save a Markdown report.",
    )
    parser.add_argument(
        "--base",
        dest="base",
        metavar="RUTA",
        default=None,
        help=(
            "Plantilla o enunciado (archivo o carpeta): lo que coincida con ella no cuenta "
            "como copia · Template (file or folder): matches with it do not count as copying."
        ),
    )
    parser.add_argument(
        "--perplejidad",
        "--perplexity",
        dest="perplejidad",
        action="store_true",
        help=(
            "Añade la señal de perplejidad tipo Binoculars (experimental, requiere el extra "
            "'modelo') · Adds the Binoculars-style perplexity signal (experimental)."
        ),
    )
    parser.add_argument(
        "--traduccion",
        "--translation",
        dest="traduccion",
        action="store_true",
        help=(
            "Busca plagio traducido entre español e inglés (requiere el extra 'semantica') "
            "· Looks for translated plagiarism between Spanish and English."
        ),
    )
    parser.add_argument(
        "--separador",
        "--separator",
        "--sep",
        dest="separador",
        choices=(";", ",", "tab"),
        default=";",
        help=(
            "Separador de columnas del CSV: ; (por defecto), , o tab · "
            "CSV column separator: ; (default), , or tab."
        ),
    )
    parser.add_argument(
        "--csv-limpio",
        "--plain-csv",
        dest="csv_limpio",
        action="store_true",
        help=(
            "No añade la primera línea 'sep=;' que hace que Excel separe bien las columnas "
            "en cualquier configuración regional; úsalo si lees el CSV con pandas u otro "
            "programa · Omits the 'sep=' first line that makes Excel split columns correctly "
            "in any regional setting; use it when reading the CSV with pandas or other tools."
        ),
    )
    parser.add_argument(
        "--sin-credito",
        "--no-credit",
        dest="sin_credito",
        action="store_true",
        help=(
            "No imprime la línea de crédito final ni el pie de los informes (también con la "
            f"variable {creditos.VARIABLE_SIN_CREDITO}=1) · Omits the closing credit line and "
            "the report footer."
        ),
    )
    parser.add_argument(
        "--calibrar",
        "--calibrate",
        dest="calibrar",
        metavar="CARPETA",
        default=None,
        help=(
            "Mide una carpeta de textos escritos por personas y guarda los umbrales ajustados "
            "(JSON en --salida si termina en .json, o calibracion.json) · Measures a folder of "
            "human-written texts and saves tuned thresholds."
        ),
    )
    parser.add_argument(
        "--calibracion",
        "--calibration",
        dest="calibracion",
        metavar="JSON",
        default=None,
        help="Usa los umbrales de un JSON creado con --calibrar · Use thresholds from --calibrar.",
    )
    parser.add_argument(
        "--alta-precision",
        "--high-precision",
        dest="alta_precision",
        action="store_true",
        help=(
            "Umbrales más exigentes: ante la duda el veredicto es 'No concluyente' en vez de "
            "acusar · Stricter thresholds: when in doubt the verdict is 'No concluyente'."
        ),
    )
    parser.add_argument(
        "--frases",
        "--sentences",
        dest="frases",
        action="store_true",
        help=(
            "Puntúa cada frase con el modelo neuronal para resaltarlas en el informe (más lento) "
            "· Scores each sentence with the neural model for the report (slower)."
        ),
    )
    parser.add_argument(
        "--lms",
        "--gradebook",
        dest="lms",
        metavar="RUTA",
        default=None,
        help=(
            "CSV genérico (coma, UTF-8) con identificador, veredicto y comentario para "
            "copiar a la hoja de calificaciones de Moodle/Canvas · Generic CSV (comma, UTF-8) "
            "with id, verdict and comment to paste into a gradebook."
        ),
    )
    parser.add_argument(
        "--fail-on",
        dest="fail_on",
        choices=tuple(NIVELES_FAIL_ON),
        default="ninguno",
        help=(
            "Código de salida 1 al alcanzar ese nivel: ninguno/none, error, alto/high, "
            "sospechoso/suspicious (por defecto/default: ninguno)."
        ),
    )
    parser.add_argument(
        "--lang",
        "--idioma",
        dest="idioma",
        choices=("es", "en"),
        default="es",
        help="Idioma de los mensajes de consola · Console message language (es/en).",
    )
    return parser.parse_args(argv)


UMBRALES_POR_DEFECTO = {
    "pico_alto": UMBRAL_PICO_ALTO,
    "media_alta": UMBRAL_MEDIA_ALTA,
    "pico_sospechoso": UMBRAL_PICO_SOSPECHOSO,
    "media_sospechosa": UMBRAL_MEDIA_SOSPECHOSA,
}


def _es_copia(coseno, ngramas):
    return coseno > UMBRAL_SIMILITUD_COPIA or ngramas >= UMBRAL_NGRAMAS_COPIA


def _juzgar(media_ia, max_ia, max_sim, *, max_ngramas=0, umbrales=None):
    """`max_sim` es el coseno (medida clásica); `max_ngramas` la similitud por n-gramas."""
    u = umbrales or UMBRALES_POR_DEFECTO
    if max_ia >= u["pico_alto"] or media_ia >= u["media_alta"]:
        return "ALTO RIESGO IA"
    if _es_copia(max_sim, max_ngramas):
        return "REVISAR COPIA ENTRE ALUMNOS"
    if max_ia >= u["pico_sospechoso"] or media_ia >= u["media_sospechosa"]:
        return "Sospechoso (Revisar)"
    return "Normal"


def _juzgar_alta_precision(media_ia, max_ia, max_sim, nivel_confianza, *, max_ngramas=0,
                           umbrales=None):
    """Como `_juzgar`, pero solo acusa de IA con umbrales exigentes y confianza suficiente.

    Si el veredicto normal habría sido de IA (alto o sospechoso) y no se cumplen esas
    condiciones, el resultado es 'No concluyente', salvo que haya copia entre entregas.
    """
    base = umbrales or UMBRALES_POR_DEFECTO
    normal = _juzgar(media_ia, max_ia, max_sim, max_ngramas=max_ngramas, umbrales=base)
    if normal not in ("ALTO RIESGO IA", "Sospechoso (Revisar)"):
        return normal
    estricto = _juzgar(media_ia, max_ia, max_sim, max_ngramas=max_ngramas,
                       umbrales=calibracion.endurecer(base))
    if estricto == "ALTO RIESGO IA" and nivel_confianza != "Baja":
        return estricto
    if _es_copia(max_sim, max_ngramas):
        return "REVISAR COPIA ENTRE ALUMNOS"
    return "No concluyente"


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
                 "Coincide_Con": "Ninguno", "Similitud_Coseno (%)": 0,
                 "Similitud_Traducida (%)": 0, "Grupo": ""})
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
    return 1 if any(v in VEREDICTOS_SOSPECHA for v in veredictos) else 0




def _cargar_base(ruta, idioma):
    """Lee la plantilla base y devuelve (huellas de texto, huellas de código)."""
    textos, codigos = [], []
    for archivo in _listar_archivos(ruta):
        try:
            texto, codigo = procesar_archivo(archivo)
        except Exception:  # una plantilla ilegible no debe impedir el análisis
            continue
        if texto:
            textos.append(texto)
        if codigo:
            codigos.append(codigo)
    if not textos and not codigos:
        _imprimir(MENSAJES[idioma]["base_vacia"].format(ruta=ruta))
    return (
        similitud.huellas_base(textos, es_codigo=False),
        similitud.huellas_base(codigos, es_codigo=True),
    )


def _codificador_con_cache(codificador):
    """Evita codificar de nuevo las mismas frases al comparar cada entrega con varias."""
    cache = {}

    def codificar(lista):
        clave = tuple(lista)
        if clave not in cache:
            cache[clave] = codificador(lista)
        return cache[clave]

    return codificar


def _elegir_companero(i, comparaciones):
    """Entre las demás entregas, la que más se acerca a los umbrales de copia.

    `comparaciones` es un diccionario {(i, j): (n-gramas, coseno)} con i < j. Devuelve
    (j, n-gramas, coseno) de la entrega elegida, o (None, 0, 0) si no hay con quién comparar.
    """
    mejor = (None, 0.0, 0.0)
    mejor_razon = -1.0
    for (a, b), (ngramas, coseno) in comparaciones.items():
        if i not in (a, b):
            continue
        otro = b if a == i else a
        razon = max(ngramas / UMBRAL_NGRAMAS_COPIA, coseno / UMBRAL_SIMILITUD_COPIA)
        if razon > mejor_razon:
            mejor, mejor_razon = (otro, ngramas, coseno), razon
    return mejor


def _plagio_traducido(i, validas, codificador):
    """Mejor coincidencia por significado con una entrega escrita en otro idioma."""
    mejor = None
    for j, otro in enumerate(validas):
        if i == j or {validas[i]["idioma_texto"], otro["idioma_texto"]} != {"es", "en"}:
            continue
        if _sin_extension(otro["nombre"]) == _sin_extension(validas[i]["nombre"]):
            continue
        porcentaje, ejemplos = semantica.similitud_traducida(
            validas[i]["texto"], otro["texto"], codificador
        )
        if mejor is None or porcentaje > mejor["porcentaje"]:
            mejor = {"companero": otro["nombre"], "porcentaje": porcentaje, "ejemplos": ejemplos}
    return mejor


def _calibrar(args, analizador, texto):
    """Mide textos humanos y guarda los umbrales ajustados. Devuelve el código de salida."""
    archivos = _listar_archivos(args.calibrar)
    picos, medias = [], []
    for archivo in archivos:
        try:
            contenido, _ = procesar_archivo(archivo)
        except Exception:  # un archivo ilegible no cuenta para la calibración
            continue
        if len(contenido) < TEXTO_MINIMO:
            continue
        evaluacion = analizador.evaluar_detalle(limpieza.normalizar(contenido))
        if evaluacion.bloques:
            picos.append(evaluacion.pico)
            medias.append(evaluacion.media)
    if not picos:
        _imprimir(texto["calibracion_sin_textos"].format(ruta=args.calibrar))
        return 1
    _imprimir(texto["calibrando"].format(n=len(picos), ruta=args.calibrar))
    if len(picos) < calibracion.MINIMO_TEXTOS:
        _imprimir(texto["calibracion_pocos"].format(minimo=calibracion.MINIMO_TEXTOS))
    umbrales = calibracion.calcular(picos, medias)
    destino = args.salida if args.salida.lower().endswith(".json") else "calibracion.json"
    calibracion.guardar(destino, umbrales, len(picos), _version())
    _imprimir(texto["calibracion_lista"].format(ruta=destino, **umbrales))
    return 0


def _filas_lms(resultados, idioma):
    """Filas del CSV genérico para hoja de calificaciones (identificador, veredicto, nota)."""
    es = idioma != "en"
    filas = []
    for fila in resultados:
        veredicto = fila["Veredicto"]
        partes = [f"{'IA pico' if es else 'AI peak'} {fila['IA_Pico_Max (%)']} %"]
        if fila["Coincide_Con"] not in ("", "Ninguno"):
            partes.append(
                f"{'similar a' if es else 'similar to'} {fila['Coincide_Con']} "
                f"({fila['Similitud_Companero (%)']} %)"
            )
        if fila.get("Grupo"):
            partes.append(f"{'grupo' if es else 'group'} {fila['Grupo']}")
        filas.append(
            {
                "Identificador": fila["Archivo"],
                "Veredicto": informes.nombre_veredicto(veredicto, idioma),
                "IA_Pico (%)": fila["IA_Pico_Max (%)"],
                "Similitud (%)": fila["Similitud_Companero (%)"],
                "Grupo": fila.get("Grupo", ""),
                "Comentario": "; ".join(partes),
            }
        )
    return filas


def main(argv=None):
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

    args = _parsear_argumentos(argv)
    texto = MENSAJES[args.idioma]
    ruta = args.carpeta
    nivel = NIVELES_FAIL_ON[args.fail_on]

    umbrales = dict(UMBRALES_POR_DEFECTO)
    if args.calibracion:
        try:
            umbrales = calibracion.cargar(args.calibracion)
        except (OSError, ValueError) as error:
            _imprimir(texto["calibracion_invalida"].format(ruta=args.calibracion, error=error))
            return 2

    archivos = [] if args.calibrar else _listar_archivos(ruta)

    if not archivos and not args.calibrar:
        _imprimir(texto["sin_archivos"].format(ruta=ruta))
        return 0

    perplejidad = None
    if args.perplejidad:
        _imprimir(texto["cargando_perplejidad"])
        perplejidad = DetectorPerplejidad()
    analizador = AnalizadorIA(
        modelo=args.modelo or MODELO_POR_DEFECTO,
        usar_modelo=not args.sin_modelo,
        idioma=args.idioma,
        perplejidad=perplejidad,
        por_frase=args.frases,
    )
    if args.calibrar:
        return _calibrar(args, analizador, texto)
    codificador = None
    if args.traduccion:
        _imprimir(texto["cargando_semantico"])
        codificador = _codificador_con_cache(semantica.cargar_codificador())

    base_texto, base_codigo = (frozenset(), frozenset())
    if args.base:
        base_texto, base_codigo = _cargar_base(args.base, args.idioma)

    unidad = texto["entrega"] if len(archivos) == 1 else texto["entregas"]
    _imprimir(texto["analizando"].format(n=len(archivos), unidad=unidad))

    resultados = []
    validas = []
    detalles = {}

    for ruta_archivo in archivos:
        nombre = os.path.basename(ruta_archivo)
        tipo = os.path.splitext(ruta_archivo)[1].upper()
        try:
            contenido, codigo = procesar_archivo(ruta_archivo)
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
            _imprimir(texto["error_lectura"].format(tipo=tipo, nombre=nombre, error=error))
            continue

        if len(contenido) < TEXTO_MINIMO:
            resultados.append(
                _fila({"Archivo": nombre, "Formato": tipo, "Veredicto": "Poco texto"})
            )
            continue

        resumen_limpieza = limpieza.analizar(contenido)
        extras = []
        if limpieza.hay_manipulacion(resumen_limpieza):
            extras.append("caracteres_ocultos")
            contenido = limpieza.normalizar(contenido)
            codigo = limpieza.normalizar(codigo)
        if humanizador.indicios(contenido, resumen_limpieza):
            extras.append("posible_humanizador")
        metadatos = leer_metadatos(ruta_archivo)
        if evaluar_metadatos(metadatos, len(contenido.split())):
            extras.append("edicion_minima")

        validas.append(
            {"nombre": nombre, "tipo": tipo, "texto": contenido, "codigo": codigo,
             "extras": extras, "metadatos": metadatos, "limpieza": resumen_limpieza}
        )

    # Documentos para comparar: código normalizado si lo hay, texto redactado si no
    for item in validas:
        base_comp = item["codigo"] if item["codigo"] else item["texto"]
        es_codigo = bool(item["codigo"])
        item["comparable"] = base_comp
        item["documento"] = similitud.Documento(
            base_comp, es_codigo=es_codigo, excluir=base_codigo if es_codigo else base_texto
        )
        item["idioma_texto"] = similitud.detectar_idioma(item["texto"])

    # Todas las parejas una sola vez; el mismo trabajo en dos formatos (PDF y TXT) no es copia
    comparaciones = {}
    for i, a in enumerate(validas):
        for j in range(i + 1, len(validas)):
            b = validas[j]
            if _sin_extension(a["nombre"]) == _sin_extension(b["nombre"]):
                continue
            comparaciones[(i, j)] = (
                similitud.similitud_ngramas(a["documento"], b["documento"]),
                similitud.similitud_coseno_docs(a["documento"], b["documento"]),
            )

    for i, item in enumerate(validas):
        try:
            evaluacion = analizador.evaluar_detalle(item["texto"])
            media_ia, max_ia, fragmento = evaluacion.media, evaluacion.pico, evaluacion.fragmento

            j, ngramas, coseno = _elegir_companero(i, comparaciones)
            companero = validas[j]["nombre"] if j is not None else "Ninguno"
            mostrar = j is not None and (
                ngramas >= UMBRAL_NGRAMAS_MOSTRAR or coseno > UMBRAL_SIMILITUD_MOSTRAR
            )

            fragmentos = []
            if mostrar:
                fragmentos = similitud.fragmentos_comunes(
                    item["documento"], validas[j]["documento"]
                )

            traducida = None
            if codificador is not None:
                traducida = _plagio_traducido(i, validas, codificador)
                if traducida and traducida["porcentaje"] < semantica.UMBRAL_AVISO:
                    traducida = None

            nivel_confianza, avisos = confianza.evaluar_confianza(
                evaluacion, item["texto"], extra=item["extras"]
            )
            if traducida:
                avisos.append("traduccion")
            if args.alta_precision:
                veredicto = _juzgar_alta_precision(
                    media_ia, max_ia, coseno, nivel_confianza,
                    max_ngramas=ngramas, umbrales=umbrales,
                )
            else:
                veredicto = _juzgar(
                    media_ia, max_ia, coseno, max_ngramas=ngramas, umbrales=umbrales
                )

            detalles[item["nombre"]] = {
                "evaluacion": evaluacion,
                "confianza": nivel_confianza,
                "avisos": avisos,
                "coincidencia": {
                    "companero": companero,
                    "ngramas": ngramas,
                    "coseno": coseno,
                    "fragmentos": fragmentos,
                }
                if mostrar
                else None,
                "traducida": traducida,
                "metadatos": item["metadatos"],
                "limpieza": item["limpieza"],
            }
            resultados.append(
                _fila(
                    {
                        "Archivo": item["nombre"],
                        "Formato": item["tipo"],
                        "IA_Media (%)": media_ia,
                        "IA_Pico_Max (%)": max_ia,
                        "Similitud_Companero (%)": ngramas,
                        "Similitud_Coseno (%)": coseno,
                        "Coincide_Con": companero if mostrar else "Ninguno",
                        "Veredicto": veredicto,
                        "Fragmento_Sospechoso": fragmento,
                        "Confianza": nivel_confianza,
                        "Avisos": " | ".join(confianza.mensaje(c, args.idioma) for c in avisos),
                        "Fragmento_Coincidente": (
                            fragmentos[0]["texto_a"].replace(";", ",")[:300] if fragmentos else ""
                        ),
                        "Similitud_Traducida (%)": traducida["porcentaje"] if traducida else 0,
                        "Grupo": "",
                    }
                )
            )
            _imprimir(
                texto["resultado"].format(
                    tipo=item["tipo"],
                    nombre=item["nombre"],
                    pico=max_ia,
                    sim=ngramas,
                    veredicto=informes.nombre_veredicto(veredicto, args.idioma),
                )
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
            _imprimir(
                texto["error_puntuacion"].format(
                    tipo=item["tipo"], nombre=item["nombre"], error=error
                )
            )

    pares_copia = [
        (validas[i]["nombre"], validas[j]["nombre"], ngramas, coseno)
        for (i, j), (ngramas, coseno) in comparaciones.items()
        if _es_copia(coseno, ngramas)
    ]
    lista_grupos = grupos.formar_grupos([v["nombre"] for v in validas], pares_copia)
    grupo_de = {m: g["id"] for g in lista_grupos for m in g["miembros"]}
    for fila in resultados:
        fila["Grupo"] = grupo_de.get(fila["Archivo"], "")
    if lista_grupos:
        _imprimir(texto["grupos_detectados"].format(n=len(lista_grupos)))

    resultados.sort(
        key=lambda fila: (fila["IA_Pico_Max (%)"], fila["Similitud_Companero (%)"]), reverse=True
    )
    df = _traducir_filas(resultados, args.idioma)
    carpeta_salida = os.path.dirname(args.salida)
    if carpeta_salida:
        os.makedirs(carpeta_salida, exist_ok=True)
    _escribir_csv(df, args.salida, args.separador, pista_excel=not args.csv_limpio)

    errores = sum(1 for fila in resultados if fila["Veredicto"] == "Error")
    resumen = {
        "version": _version(),
        "ruta": ruta,
        "reporte": args.salida,
        "modelo": None if args.sin_modelo else (args.modelo or MODELO_POR_DEFECTO),
        "perplejidad": args.perplejidad,
        "traduccion": args.traduccion,
        "idioma": args.idioma,
        "total": len(resultados),
        "errores": errores,
        "aviso": confianza.AVISO_SESGO[1 if args.idioma == "en" else 0],
        "credito": creditos.credito_activo(args.sin_credito),
        "alta_precision": args.alta_precision,
        "umbrales": umbrales,
        "grupos": lista_grupos,
    }

    pares = sorted(
        (
            {
                "a": validas[i]["nombre"],
                "b": validas[j]["nombre"],
                "ngramas": ngramas,
                "coseno": coseno,
            }
            for (i, j), (ngramas, coseno) in comparaciones.items()
            if ngramas >= 20 or coseno >= 60
        ),
        key=lambda par: (par["ngramas"], par["coseno"]),
        reverse=True,
    )[:MAXIMO_PARES_INFORME]

    if args.html:
        _escribir_informe(
            args.html,
            informes.informe_html(
                resultados, detalles, resumen, pares, args.idioma,
                umbrales=(umbrales["pico_alto"], umbrales["pico_sospechoso"]),
            ),
        )
        _imprimir(texto["html_listo"].format(ruta=args.html))
    if args.markdown:
        _escribir_informe(
            args.markdown,
            informes.informe_markdown(resultados, detalles, resumen, pares, args.idioma),
        )
        _imprimir(texto["md_listo"].format(ruta=args.markdown))

    if args.lms:
        carpeta_lms = os.path.dirname(args.lms)
        if carpeta_lms:
            os.makedirs(carpeta_lms, exist_ok=True)
        pd.DataFrame(_filas_lms(resultados, args.idioma)).to_csv(
            args.lms, index=False, sep=",", encoding="utf-8-sig"
        )
        _imprimir(texto["lms_listo"].format(ruta=args.lms))

    if args.json:
        filas_json = [
            {**fila, "Detalle": informes.detalle_json(detalles.get(fila["Archivo"]))}
            for fila in resultados
        ]
        print(json.dumps({"resumen": resumen, "resultados": filas_json},
                         ensure_ascii=False, indent=2))
    else:
        _imprimir(texto["listo"].format(salida=args.salida))
    if errores:
        _imprimir(texto["aviso_errores"].format(n=errores))
    if resumen["credito"]:
        _imprimir(creditos.linea_consola(resumen["version"]))

    return _codigo_salida(resultados, nivel)


def _escribir_csv(df, ruta, separador=";", *, pista_excel=True):
    """Escribe el CSV en UTF-8 con BOM.

    Excel separa las columnas según la configuración regional del equipo (`;` en España, `,`
    en EE. UU.), así que un CSV con `;` abierto con doble clic puede aparecer en una sola
    columna. La línea `sep=X` del principio le indica el separador real, sea cual sea su
    configuración. Con `pista_excel=False` el archivo es un CSV estándar sin esa línea.
    """
    separador = "\t" if separador == "tab" else separador
    with open(ruta, "w", encoding="utf-8-sig", newline="") as archivo:
        if pista_excel:
            archivo.write(f"sep={separador}\r\n")
        df.to_csv(archivo, index=False, sep=separador, lineterminator="\r\n")


def _escribir_informe(ruta, contenido):
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)


if __name__ == "__main__":
    raise SystemExit(main())
