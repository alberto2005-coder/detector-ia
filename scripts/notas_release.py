"""Notas de release bilingües (español e inglés) a partir del CHANGELOG.

Uso: python scripts/notas_release.py 1.0.0
"""

import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
CHANGELOG = RAIZ / "CHANGELOG.md"

REPO = "https://github.com/alberto2005-coder/detector-ia"
PYPI = "https://pypi.org/project/detector-ia/"

INSTALACION = """\
## Instalación · Install

```bash
pip install detector-ia            # sin modelo neuronal / structural signals only
pip install "detector-ia[modelo]"  # con el modelo neuronal / with the neural model
pip install "detector-ia[semantica]"  # plagio traducido (--traduccion) / translated plagiarism
```

```bash
detector-ia -c revision_ia              # carpeta de entregas / submissions folder
detector-ia -c revision_ia/entrega.pdf  # una sola entrega / a single file
detector-ia -c revision_ia --html informe.html   # informe para leer / report to read
detector-ia --help                      # opciones, en los dos idiomas / options in both languages
```
"""


def _trozos(texto):
    """Separa el CHANGELOG en sus dos mitades: {'Español': ..., 'English': ...}."""
    partes = re.split(r"^## (Español|English)\s*$", texto, flags=re.MULTILINE)
    return {partes[i]: partes[i + 1] for i in range(1, len(partes) - 1, 2)}


def _bloque(cuerpo, version):
    """Devuelve el cuerpo de la sección de esa versión, o None si no existe."""
    patron = re.compile(rf"^### \[{re.escape(version)}\].*$", re.MULTILINE)
    inicio = patron.search(cuerpo)
    if not inicio:
        return None
    resto = cuerpo[inicio.end():]
    fin = re.search(r"^(### \[|## |---)", resto, re.MULTILINE)
    return resto[: fin.start()].strip()


def notas(version, ruta=CHANGELOG):
    """Notas completas para la release: instalación, cambios en español y en inglés."""
    trozos = _trozos(pathlib.Path(ruta).read_text(encoding="utf-8"))
    secciones = []
    for idioma in ("Español", "English"):
        bloque = _bloque(trozos.get(idioma, ""), version)
        if bloque is None:
            if idioma == "Español":
                return f"No hay entrada para la versión {version} en el CHANGELOG."
            continue
        secciones.append(f"## {idioma}\n\n{bloque}")
    return (
        f"{INSTALACION}\n"
        + "\n\n".join(secciones)
        + "\n\n---\n\n"
        + f"**PyPI**: <{PYPI}> · **Código / Source**: <{REPO}> · "
        + f"**Historial completo / Full changelog**: <{REPO}/blob/main/CHANGELOG.md>\n"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/notas_release.py <version>")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(notas(sys.argv[1]))
