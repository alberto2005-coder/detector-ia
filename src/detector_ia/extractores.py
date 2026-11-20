import json
import os
import re
import zipfile

import docx
from pypdf import PdfReader


def _extraer_ipynb(ruta):
    with open(ruta, encoding="utf-8") as f:
        cuaderno = json.load(f)
    
    respuestas, codigo = [], []
    for celda in cuaderno.get("cells", []):
        lineas = celda.get("source", [])
        contenido = "".join(lineas)
        
        if celda.get("cell_type") == "markdown":
            # Extrae solo lo que va después de "Respuestas:" para ignorar tus enunciados
            if "respuestas:" in contenido.lower():
                parte_alumno = re.split(r"respuestas:\*?", contenido, flags=re.IGNORECASE)[-1]
                respuestas.append(parte_alumno)
        elif celda.get("cell_type") == "code":
            cod_limpio = "\n".join(
                linea for linea in lineas if not linea.strip().startswith("#") and linea.strip()
            )
            if cod_limpio:
                codigo.append(cod_limpio)
            comentarios = [
                linea.strip()[1:].strip()
                for linea in lineas
                if linea.strip().startswith("#")
            ]
            if comentarios:
                respuestas.append(" ".join(comentarios))
                
    return "\n".join(respuestas).strip(), "\n".join(codigo).strip()

def _extraer_pdf(ruta):
    lector = PdfReader(ruta)
    paginas = [p.extract_text() or "" for p in lector.pages]
    return "\n".join(paginas).strip(), ""

def _extraer_docx(ruta):
    doc = docx.Document(ruta)
    parrafos = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(parrafos).strip(), ""

def _extraer_texto_plano(ruta):
    with open(ruta, encoding="utf-8", errors="ignore") as f:
        return f.read().strip(), ""

def procesar_archivo(ruta):
    """Detecta la extensión y devuelve (texto_redactado, codigo_fuente)."""
    ext = os.path.splitext(ruta)[1].lower()
    if ext == ".ipynb":
        return _extraer_ipynb(ruta)
    elif ext == ".pdf":
        return _extraer_pdf(ruta)
    elif ext == ".docx":
        return _extraer_docx(ruta)
    elif ext in [".txt", ".md"]:
        return _extraer_texto_plano(ruta)
    return "", ""


PALABRAS_MINIMAS_METADATOS = 300


def leer_metadatos(ruta):
    """Metadatos de edición de un .docx (autor, fechas, revisiones, minutos). {} si no hay."""
    if os.path.splitext(ruta)[1].lower() != ".docx":
        return {}
    try:
        propiedades = docx.Document(ruta).core_properties
        meta = {
            "autor": propiedades.author or "",
            "ultimo_autor": propiedades.last_modified_by or "",
            "creado": propiedades.created.isoformat() if propiedades.created else "",
            "modificado": propiedades.modified.isoformat() if propiedades.modified else "",
            "revision": propiedades.revision,
            "minutos_edicion": None,
        }
        with zipfile.ZipFile(ruta) as paquete:
            if "docProps/app.xml" in paquete.namelist():
                xml = paquete.read("docProps/app.xml").decode("utf-8", errors="ignore")
                encontrado = re.search(r"<TotalTime>(\d+)</TotalTime>", xml)
                if encontrado:
                    meta["minutos_edicion"] = int(encontrado.group(1))
    except Exception:  # un metadato ilegible nunca debe impedir el análisis
        return {}
    return meta


def evaluar_metadatos(meta, palabras):
    """Código de aviso si los metadatos no casan con la extensión del texto, o None.

    Es un dato orientativo: un texto pegado desde otro editor o un Word creado por una
    herramienta en línea también muestran pocos minutos. No prueba nada por sí solo.
    """
    if not meta or palabras < PALABRAS_MINIMAS_METADATOS:
        return None
    minutos = meta.get("minutos_edicion")
    if minutos is not None and minutos <= 1:
        return "edicion_minima"
    return None
