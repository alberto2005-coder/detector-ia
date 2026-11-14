import json
import os
import re
from pypdf import PdfReader
import docx

def _extraer_ipynb(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
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
            cod_limpio = "\n".join([l for l in lineas if not l.strip().startswith("#") and l.strip()])
            if cod_limpio:
                codigo.append(cod_limpio)
            comentarios = [l.strip()[1:].strip() for l in lineas if l.strip().startswith("#")]
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
    with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
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
