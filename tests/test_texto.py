"""Análisis de un texto suelto con --texto, en vez de una carpeta o un archivo."""

import io
import json

import pytest

from detector_ia import idioma
from detector_ia.main import main
from tests.conftest import TEXTO_HUMANO, TEXTO_IA


@pytest.fixture(autouse=True)
def _entorno(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # un CSV accidental caería aquí y no en el proyecto
    monkeypatch.delenv(idioma.VARIABLE, raising=False)
    monkeypatch.delenv("DETECTOR_IA_SIN_CREDITO", raising=False)
    yield
    idioma.fijar("es")


def test_un_texto_se_analiza_y_se_muestra_por_pantalla_sin_crear_csv(tmp_path, capsys):
    codigo = main(["--texto", TEXTO_IA, "--sin-modelo"])
    captura = capsys.readouterr()
    assert codigo == 0
    assert "Veredicto: ALTO RIESGO IA" in captura.out
    assert "IA: pico" in captura.out and "confianza:" in captura.out
    assert "Fragmento más sospechoso" in captura.out
    assert "Analizando el texto" in captura.err
    assert list(tmp_path.glob("*.csv")) == []


def test_un_texto_humano_no_muestra_fragmento_sospechoso(capsys):
    main(["-t", TEXTO_HUMANO, "--sin-modelo"])
    salida = capsys.readouterr().out
    assert "Veredicto: Normal" in salida
    assert "Fragmento" not in salida


def test_con_salida_explicita_si_se_escribe_el_csv(tmp_path):
    main(["--texto", TEXTO_IA, "--sin-modelo", "-s", str(tmp_path / "t.csv"), "--csv-limpio"])
    filas = (tmp_path / "t.csv").read_text(encoding="utf-8-sig").splitlines()
    assert filas[1].startswith("texto;TEXTO;")


def test_el_texto_se_lee_de_la_entrada_estandar(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(TEXTO_IA.encode("utf-8"))))
    assert main(["--texto", "-", "--sin-modelo"]) == 0
    assert "ALTO RIESGO IA" in capsys.readouterr().out


def test_entrada_estandar_con_bom_y_utf16(monkeypatch, capsys):
    for datos in (b"\xef\xbb\xbf" + TEXTO_IA.encode("utf-8"), TEXTO_IA.encode("utf-16")):
        monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(datos)))
        main(["--texto", "-", "--sin-modelo"])
        assert "ALTO RIESGO IA" in capsys.readouterr().out


def test_texto_vacio_devuelve_2_y_explica(capsys):
    assert main(["--texto", "   ", "--sin-modelo"]) == 2
    assert "El texto está vacío" in capsys.readouterr().err


def test_texto_demasiado_corto(capsys):
    assert main(["--texto", "hola", "--sin-modelo"]) == 0
    assert "demasiado poco texto" in capsys.readouterr().out


def test_texto_con_json(capsys):
    main(["--texto", TEXTO_IA, "--sin-modelo", "--json"])
    datos = json.loads(capsys.readouterr().out)
    assert datos["resultados"][0]["Archivo"] == "texto"
    assert datos["resultados"][0]["Formato"] == "TEXTO"
    assert datos["resultados"][0]["Veredicto"] == "ALTO RIESGO IA"


def test_texto_en_ingles(capsys):
    main(["--text", TEXTO_IA, "--sin-modelo", "--en"])
    captura = capsys.readouterr()
    assert "Verdict: HIGH AI RISK" in captura.out
    assert "confidence:" in captura.out and "Analysing the text" in captura.err
    assert "Veredicto" not in captura.out + captura.err


def test_texto_con_informes_html_y_markdown(tmp_path):
    main(["--texto", TEXTO_IA, "--sin-modelo", "--html", str(tmp_path / "i.html"),
          "--markdown", str(tmp_path / "i.md")])
    assert "texto" in (tmp_path / "i.html").read_text(encoding="utf-8")
    assert "texto" in (tmp_path / "i.md").read_text(encoding="utf-8")


def test_fail_on_funciona_con_un_texto():
    assert main(["--texto", TEXTO_IA, "--sin-modelo", "--fail-on", "alto"]) == 1
    assert main(["--texto", TEXTO_HUMANO, "--sin-modelo", "--fail-on", "alto"]) == 0


def test_los_caracteres_ocultos_tambien_se_detectan_en_un_texto(capsys):
    main(["--texto", TEXTO_IA.replace("a", "a​", 30), "--sin-modelo"])
    salida = capsys.readouterr().out
    assert "ALTO RIESGO IA" in salida and "invisibles" in salida


def test_texto_ignora_la_carpeta_y_no_la_lee(tmp_path, capsys):
    main(["--texto", TEXTO_HUMANO, "-c", str(tmp_path / "no_existe"), "--sin-modelo"])
    assert "Veredicto: Normal" in capsys.readouterr().out


def test_la_ayuda_menciona_texto_en_los_dos_idiomas(capsys):
    for bandera, esperado in (("--es", "--texto"), ("--en", "--text")):
        with pytest.raises(SystemExit):
            main([bandera, "-h"])
        ayuda = capsys.readouterr().out
        assert esperado in ayuda
