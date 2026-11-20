"""Datos de autoría y líneas de crédito (consola, HTML y Markdown)."""

import os

AUTOR = "Alberto Ortiz Sánchez"
WEB = "https://albertoortiz.is-a.dev/"
GITHUB_AUTOR = "https://github.com/alberto2005-coder/"
REPOSITORIO = "https://github.com/alberto2005-coder/detector-ia"
PYPI = "https://pypi.org/project/detector-ia/"
VARIABLE_SIN_CREDITO = "DETECTOR_IA_SIN_CREDITO"


def _sin_dominio(url):
    return url.replace("https://", "").replace("http://", "").rstrip("/")


def credito_activo(sin_credito=False):
    """False si se pidió con `--sin-credito` o con la variable de entorno."""
    if sin_credito:
        return False
    valor = os.environ.get(VARIABLE_SIN_CREDITO, "").strip().lower()
    return valor not in ("1", "true", "si", "sí", "yes")


def linea_consola(version):
    return f"detector-ia {version} · {AUTOR} · {_sin_dominio(WEB)}"


def pie_texto(version, idioma="es"):
    """Línea de crédito de los informes (texto plano, sin enlaces)."""
    prefijo = "Generado con" if idioma != "en" else "Generated with"
    return f"{prefijo} detector-ia {version} · {AUTOR} · {WEB} · {PYPI}"


def pie_markdown(version, idioma="es"):
    prefijo = "Generado con" if idioma != "en" else "Generated with"
    return (
        f"{prefijo} [detector-ia {version}]({PYPI}) · "
        f"[{AUTOR}]({WEB})"
    )
