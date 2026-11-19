import csv
import importlib.util
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
ESPECIFICACION = importlib.util.spec_from_file_location(
    "evaluar", RAIZ / "evaluacion" / "evaluar.py"
)
evaluar = importlib.util.module_from_spec(ESPECIFICACION)
ESPECIFICACION.loader.exec_module(evaluar)

ETIQUETAS = RAIZ / "evaluacion" / "etiquetas.csv"
CORPUS = RAIZ / "evaluacion" / "textos"


def test_metricas_ignoran_los_textos_mixtos():
    pares = [("ia", 80), ("ia", 20), ("humano", 10), ("humano", 70), ("mixto", 99)]
    m = evaluar.metricas(pares, 50)
    assert (m["falsos_positivos"], m["falsos_negativos"]) == (1, 1)
    assert m["precision"] == pytest.approx(0.5)
    assert m["recall"] == pytest.approx(0.5)
    assert m["exactitud"] == pytest.approx(0.5)


def test_metricas_sin_datos_no_dividen_por_cero():
    assert evaluar.metricas([], 50)["exactitud"] == 0.0


def test_el_corpus_esta_completo_y_bien_etiquetado():
    filas = evaluar.cargar_etiquetas(ETIQUETAS)
    assert len(filas) >= 40
    assert {etiqueta for _, etiqueta, _ in filas} == {"ia", "humano", "mixto"}
    nombres = [nombre for nombre, _, _ in filas]
    assert len(nombres) == len(set(nombres))
    for nombre in nombres:
        assert (CORPUS / nombre).exists(), nombre
    # ningún archivo del corpus queda sin etiquetar
    assert {p.name for p in CORPUS.glob("*.txt")} == set(nombres)


def test_las_etiquetas_son_coherentes_con_el_nombre_de_la_categoria():
    for _, etiqueta, categoria in evaluar.cargar_etiquetas(ETIQUETAS):
        assert categoria.startswith(etiqueta) or etiqueta == "mixto"


def test_todos_los_textos_del_corpus_son_lo_bastante_largos_para_puntuar():
    from detector_ia.motores import BLOQUE_MINIMO

    for ruta in CORPUS.glob("*.txt"):
        assert len(ruta.read_text(encoding="utf-8").strip()) >= BLOQUE_MINIMO, ruta.name


def test_los_textos_mixtos_tienen_al_menos_dos_bloques_puntuables():
    from detector_ia.motores import BLOQUE_MINIMO, TAMANO_BLOQUE

    for ruta in CORPUS.glob("mixto_*.txt"):
        assert len(ruta.read_text(encoding="utf-8").strip()) - TAMANO_BLOQUE >= BLOQUE_MINIMO


def test_regresion_la_ia_sin_editar_puntua_mas_que_el_humano_coloquial():
    from detector_ia.motores import AnalizadorIA

    analizador = AnalizadorIA(usar_modelo=False)
    filas = evaluar.evaluar(CORPUS, ETIQUETAS, analizador)
    resumen = evaluar.por_categoria(filas, 45.0)
    assert resumen["ia_sin_editar"]["pico_medio"] > resumen["humano_coloquial"]["pico_max"]
    assert resumen["ia_sin_editar"]["marcados"] >= 4
    assert resumen["humano_coloquial"]["marcados"] == 0


def test_el_csv_de_etiquetas_usa_punto_y_coma():
    with open(ETIQUETAS, encoding="utf-8-sig", newline="") as f:
        cabecera = next(csv.reader(f, delimiter=";"))
    assert cabecera == ["archivo", "etiqueta", "categoria"]
