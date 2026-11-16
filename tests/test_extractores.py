import json

import docx
import pytest

from detector_ia.extractores import procesar_archivo


def test_texto_plano_y_markdown(tmp_path):
    ruta = tmp_path / "apuntes.md"
    ruta.write_text("# Titulo\n\nContenido de prueba.", encoding="utf-8")
    texto, codigo = procesar_archivo(str(ruta))
    assert "Contenido de prueba" in texto
    assert codigo == ""


def test_notebook_separa_respuestas_y_codigo(tmp_path):
    cuaderno = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["Enunciado del profesor\n", "Respuestas: mi respuesta"],
            },
            {"cell_type": "code", "source": ["# comentario del alumno\n", "print(1)\n"]},
        ]
    }
    ruta = tmp_path / "entrega.ipynb"
    ruta.write_text(json.dumps(cuaderno), encoding="utf-8")
    texto, codigo = procesar_archivo(str(ruta))
    assert "mi respuesta" in texto
    assert "comentario del alumno" in texto
    assert "Enunciado del profesor" not in texto
    assert "print(1)" in codigo
    assert "comentario del alumno" not in codigo


def test_docx_extrae_parrafos(tmp_path):
    documento = docx.Document()
    documento.add_paragraph("Primer parrafo del informe.")
    documento.add_paragraph("Segundo parrafo con mas contenido.")
    ruta = tmp_path / "informe.docx"
    documento.save(str(ruta))
    texto, codigo = procesar_archivo(str(ruta))
    assert "Primer parrafo" in texto and "Segundo parrafo" in texto
    assert codigo == ""


def test_extension_no_soportada_devuelve_vacio(tmp_path):
    ruta = tmp_path / "datos.xyz"
    ruta.write_text("contenido", encoding="utf-8")
    assert procesar_archivo(str(ruta)) == ("", "")


def test_pdf_corrupto_lanza_excepcion(tmp_path):
    ruta = tmp_path / "roto.pdf"
    ruta.write_bytes(b"esto no es un PDF")
    try:
        procesar_archivo(str(ruta))
    except Exception:  # pypdf no garantiza un tipo concreto de error
        return
    pytest.fail("un PDF corrupto deberia lanzar una excepcion")
