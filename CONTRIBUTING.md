# Contribuir / Contributing

[Español](#español) · [English](#english)

---

## Español

### Entorno

```bash
uv sync              # crea .venv e instala las dependencias del uv.lock
uv run detector-ia --help
```

Si tocas dependencias, usa `uv add` o `uv remove` y sube también el `uv.lock` actualizado. No edites el lock a mano.

### Estructura

```text
detector-ia/
├── src/detector_ia/
│   ├── main.py          # CLI, umbrales, veredictos y generación del CSV
│   ├── extractores.py   # Lectura de cada formato
│   └── motores.py       # Modelo neuronal, huella estructural y similitud
├── tests/               # Pruebas con detector falso (uv run pytest)
├── docs/                # Índice, método, uso responsable y formatos
├── ejemplos/            # Textos inventados de prueba
├── evaluacion/          # Corpus etiquetado y script de métricas
├── scripts/             # Notas de release desde el CHANGELOG
├── .github/             # CI, releases, Dependabot y plantillas
├── revision_ia/         # Entregas de entrada (ignorada por git)
├── README.md            # Guía completa, en español e inglés
├── CONTRIBUTING.md      # Esta guía
├── SECURITY.md          # Política de seguridad
├── CODE_OF_CONDUCT.md   # Código de conducta
├── CHANGELOG.md         # Historial de cambios por versión
├── LICENSE              # Licencia MIT
├── pyproject.toml       # Dependencias, extras y entry point
├── uv.lock              # Versiones exactas de las dependencias
├── .gitattributes       # Finales de línea normalizados
└── .gitignore           # Excluye .venv, cache_modelo y entregas
```

### Ideas para contribuir

- **Nuevo formato de entrada**: añade un `_extraer_*` en `extractores.py` y engánchalo en `procesar_archivo`. Registra también la extensión en `EXTENSIONES_VALIDAS` de `main.py` y añade la dependencia con `uv add`.
- **Afinar el detector**: los patrones de la huella española están en `_huella_llm_espanol` y los pesos en `evaluar_texto`, ambos en `motores.py`. Si cambias pesos o umbrales, explica en el commit con qué textos lo has comprobado.
- **Otro idioma**: la huella estructural es específica de español; un idioma nuevo requiere su propia función de patrones, no solo cambiar los pesos.

### Pruebas

```bash
uv run ruff check .
uv run pytest
```

Las pruebas usan un detector falso, así que no descargan el modelo ni necesitan el extra `modelo`. Si cambias la detección, añade o ajusta un caso en `tests/`; si tocas pesos o umbrales, pásalos por `evaluacion/evaluar.py`.

Para probar la CLI a mano hay textos inventados: `uv run detector-ia -c ejemplos -s reporte_prueba.csv`. **No subas nunca entregas reales de alumnos** ni los CSV generados: son datos personales.

### Publicar una versión

1. Sube la versión en `pyproject.toml` y añade su entrada en `CHANGELOG.md`, igual en español y en inglés.
2. Construye y revisa los artefactos antes de subir nada:

```bash
uv build
uv publish --dry-run dist/*
```

3. Crea el tag y súbelo: `git tag v0.x.y && git push origin v0.x.y`. Ese push lanza la release de GitHub con las notas extraídas del CHANGELOG.
4. Para PyPI, configura **Trusted Publishing** en el proyecto y publica con `uv publish`. Nunca commitees tokens: no hay ningún secreto en el repositorio.

### Commits

- Mensajes en imperativo y con prefijo: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`.
- Un commit por cambio con sentido propio, con el porqué en el cuerpo si no es obvio.
- Sin pies de atribución automáticos ni `Co-Authored-By` de herramientas.

### Estilo

- Nombres y mensajes en español, siguiendo el código existente.
- 4 espacios, sin tabs, líneas razonablemente cortas.
- Comentarios solo donde el motivo no es evidente.

---

## English

### Environment

```bash
uv sync              # creates .venv and installs from uv.lock
uv run detector-ia --help
```

If you touch dependencies, use `uv add` or `uv remove` and commit the updated `uv.lock`. Never edit the lock file by hand.

### Layout

```text
detector-ia/
├── src/detector_ia/
│   ├── main.py          # CLI, thresholds, verdicts and CSV output
│   ├── extractores.py   # One reader per format
│   └── motores.py       # Neural model, structural fingerprint and similarity
├── tests/               # Tests with a fake detector (uv run pytest)
├── docs/                # Index, method, responsible use and formats
├── ejemplos/            # Invented test texts
├── evaluacion/          # Labelled corpus and metrics script
├── scripts/             # Release notes from the CHANGELOG
├── .github/             # CI, releases, Dependabot and templates
├── revision_ia/         # Input submissions (git-ignored)
├── README.md            # Full guide, in Spanish and English
├── CONTRIBUTING.md      # This guide
├── SECURITY.md          # Security policy
├── CODE_OF_CONDUCT.md   # Code of conduct
├── CHANGELOG.md         # Change history per version
├── LICENSE              # MIT license
├── pyproject.toml       # Dependencies, extras and entry point
├── uv.lock              # Exact dependency versions
├── .gitattributes       # Normalized line endings
└── .gitignore           # Excludes .venv, cache_modelo and submissions
```

### Good places to help

- **New input format**: add an `_extraer_*` function in `extractores.py` and hook it into `procesar_archivo`. Register the extension in `EXTENSIONES_VALIDAS` in `main.py` and add the dependency with `uv add`.
- **Tuning the detector**: Spanish fingerprint patterns live in `_huella_llm_espanol`, weights in `evaluar_texto`, both in `motores.py`. When changing weights or thresholds, say in the commit which texts you checked them against.
- **Another language**: the structural fingerprint is Spanish-specific; a new language needs its own pattern function, not just different weights.

### Testing

```bash
uv run ruff check .
uv run pytest
```

The tests use a fake detector, so they neither download the model nor need the `modelo` extra. If you change detection, add or adjust a case in `tests/`; if you touch weights or thresholds, run them through `evaluacion/evaluar.py`.

To try the CLI by hand there are invented texts: `uv run detector-ia -c ejemplos -s reporte_prueba.csv`. **Never commit real student work** or generated CSVs: that is personal data.

### Publishing a release

1. Bump the version in `pyproject.toml` and add its entry to `CHANGELOG.md`, in Spanish and English alike.
2. Build and inspect the artifacts before pushing anything:

```bash
uv build
uv publish --dry-run dist/*
```

3. Tag and push: `git tag v0.x.y && git push origin v0.x.y`. That push triggers the GitHub release with notes taken from the CHANGELOG.
4. For PyPI, set up **Trusted Publishing** on the project and publish with `uv publish`. Never commit tokens: the repository holds no secrets.

### Commits

- Imperative messages with a prefix: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`.
- One commit per self-contained change, with the reasoning in the body when it is not obvious.
- No automatic attribution footers or tool `Co-Authored-By` lines.

### Style

- Names and messages in Spanish, following the existing code.
- 4 spaces, no tabs, reasonably short lines.
- Comments only where the reason is not evident.
