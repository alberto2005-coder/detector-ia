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
├── docs/                # Índice y detalles de uso (bilingües)
├── revision_ia/         # Entregas de entrada (ignorada por git)
├── README.md            # Guía completa, en español e inglés
├── CONTRIBUTING.md      # Esta guía
├── SECURITY.md          # Política de seguridad
├── CHANGELOG.md         # Historial de cambios por versión
├── LICENSE              # Licencia MIT
├── pyproject.toml       # Dependencias y entry point detector-ia
├── uv.lock              # Versiones exactas de las dependencias
└── .gitignore           # Excluye .venv, cache_modelo y entregas
```

### Ideas para contribuir

- **Nuevo formato de entrada**: añade un `_extraer_*` en `extractores.py` y engánchalo en `procesar_archivo`. Registra también la extensión en `EXTENSIONES_VALIDAS` de `main.py` y añade la dependencia con `uv add`.
- **Afinar el detector**: los patrones de la huella española están en `_huella_llm_espanol` y los pesos en `evaluar_texto`, ambos en `motores.py`. Si cambias pesos o umbrales, explica en el commit con qué textos lo has comprobado.
- **Otro idioma**: la huella estructural es específica de español; un idioma nuevo requiere su propia función de patrones, no solo cambiar los pesos.

### Pruebas

No hay suite automática todavía. Antes de abrir un cambio, comprueba al menos:

```bash
uv run detector-ia --help
uv run detector-ia -c <carpeta-de-prueba> -s reporte_prueba.csv
```

Con una entrega claramente generada y otra escrita a mano, para ver que los veredictos tienen sentido. **No subas nunca entregas reales de alumnos** ni los CSV generados: son datos personales.

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
├── docs/                # Index and usage details (bilingual)
├── revision_ia/         # Input submissions (git-ignored)
├── README.md            # Full guide, in Spanish and English
├── CONTRIBUTING.md      # This guide
├── SECURITY.md          # Security policy
├── CHANGELOG.md         # Change history per version
├── LICENSE              # MIT license
├── pyproject.toml       # Dependencies and detector-ia entry point
├── uv.lock              # Exact dependency versions
└── .gitignore           # Excludes .venv, cache_modelo and submissions
```

### Good places to help

- **New input format**: add an `_extraer_*` function in `extractores.py` and hook it into `procesar_archivo`. Register the extension in `EXTENSIONES_VALIDAS` in `main.py` and add the dependency with `uv add`.
- **Tuning the detector**: Spanish fingerprint patterns live in `_huella_llm_espanol`, weights in `evaluar_texto`, both in `motores.py`. When changing weights or thresholds, say in the commit which texts you checked them against.
- **Another language**: the structural fingerprint is Spanish-specific; a new language needs its own pattern function, not just different weights.

### Testing

There is no automated suite yet. Before opening a change, at least check:

```bash
uv run detector-ia --help
uv run detector-ia -c <test-folder> -s reporte_prueba.csv
```

Use one clearly generated submission and one hand-written one, to confirm the verdicts make sense. **Never commit real student work** or generated CSVs: that is personal data.

### Commits

- Imperative messages with a prefix: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`.
- One commit per self-contained change, with the reasoning in the body when it is not obvious.
- No automatic attribution footers or tool `Co-Authored-By` lines.

### Style

- Names and messages in Spanish, following the existing code.
- 4 spaces, no tabs, reasonably short lines.
- Comments only where the reason is not evident.
