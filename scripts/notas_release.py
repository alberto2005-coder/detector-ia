"""Imprime en stdout la sección del CHANGELOG correspondiente a una versión.

Uso: python scripts/notas_release.py 0.1.0
"""

import pathlib
import re
import sys


def extraer(version, ruta="CHANGELOG.md"):
    texto = pathlib.Path(ruta).read_text(encoding="utf-8")
    patron = re.compile(rf"^### \[{re.escape(version)}\].*$", re.MULTILINE)
    inicio = patron.search(texto)
    if not inicio:
        return f"No hay entrada para la versión {version} en el CHANGELOG."
    resto = texto[inicio.end():]
    fin = re.search(r"^(### \[|---)", resto, re.MULTILINE)
    cuerpo = resto[: fin.start()] if fin else resto
    return f"### {version}\n" + cuerpo.strip() + "\n"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/notas_release.py <version>")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(extraer(sys.argv[1]))
