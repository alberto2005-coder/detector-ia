import argparse
import glob
import json
import os
import sys
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as version_paquete

import pandas as pd

from detector_ia import confianza, informes, semantica, similitud
from detector_ia.extractores import procesar_archivo
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
]

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
    },
}


AUTOR = "Alberto Ortiz Sánchez"
WEB = "https://albertoortiz.is-a.dev/"
GITHUB_AUTOR = "https://github.com/alberto2005-coder/"
REPOSITORIO = "https://github.com/alberto2005-coder/detector-ia"
PYPI = "https://pypi.org/project/detector-ia/"


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


def _es_copia(coseno, ngramas):
    return coseno > UMBRAL_SIMILITUD_COPIA or ngramas >= UMBRAL_NGRAMAS_COPIA


def _juzgar(media_ia, max_ia, max_sim, *, max_ngramas=0):
    """`max_sim` es el coseno (medida clásica); `max_ngramas` la similitud por n-gramas."""
    if max_ia >= UMBRAL_PICO_ALTO or media_ia >= UMBRAL_MEDIA_ALTA:
        return "ALTO RIESGO IA"
    if _es_copia(max_sim, max_ngramas):
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
                 "Coincide_Con": "Ninguno", "Similitud_Coseno (%)": 0,
                 "Similitud_Traducida (%)": 0})
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


def main(argv=None):
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

    args = _parsear_argumentos(argv)
    texto = MENSAJES[args.idioma]
    ruta = args.carpeta
    nivel = NIVELES_FAIL_ON[args.fail_on]

    archivos = _listar_archivos(ruta)

    if not archivos:
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
    )
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

        validas.append(
            {"nombre": nombre, "tipo": tipo, "texto": contenido, "codigo": codigo}
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

            veredicto = _juzgar(media_ia, max_ia, coseno, max_ngramas=ngramas)
            nivel_confianza, avisos = confianza.evaluar_confianza(evaluacion, item["texto"])
            if traducida:
                avisos.append("traduccion")

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
                        "Avisos": " | ".join(confianza.mensaje(c) for c in avisos),
                        "Fragmento_Coincidente": (
                            fragmentos[0]["texto_a"].replace(";", ",")[:300] if fragmentos else ""
                        ),
                        "Similitud_Traducida (%)": traducida["porcentaje"] if traducida else 0,
                    }
                )
            )
            _imprimir(
                texto["resultado"].format(
                    tipo=item["tipo"],
                    nombre=item["nombre"],
                    pico=max_ia,
                    sim=ngramas,
                    veredicto=veredicto,
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

    resultados.sort(
        key=lambda fila: (fila["IA_Pico_Max (%)"], fila["Similitud_Companero (%)"]), reverse=True
    )
    df = pd.DataFrame(resultados, columns=COLUMNAS)
    carpeta_salida = os.path.dirname(args.salida)
    if carpeta_salida:
        os.makedirs(carpeta_salida, exist_ok=True)
    df.to_csv(args.salida, index=False, sep=";", encoding="utf-8-sig")

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
                umbrales=(UMBRAL_PICO_ALTO, UMBRAL_PICO_SOSPECHOSO),
            ),
        )
        _imprimir(texto["html_listo"].format(ruta=args.html))
    if args.markdown:
        _escribir_informe(
            args.markdown,
            informes.informe_markdown(resultados, detalles, resumen, pares, args.idioma),
        )
        _imprimir(texto["md_listo"].format(ruta=args.markdown))

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

    return _codigo_salida(resultados, nivel)


def _escribir_informe(ruta, contenido):
    carpeta = os.path.dirname(ruta)
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)


if __name__ == "__main__":
    raise SystemExit(main())
