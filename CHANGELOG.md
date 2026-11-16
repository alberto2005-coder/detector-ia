# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y versionado [SemVer](https://semver.org/lang/es/).
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [SemVer](https://semver.org/).

[Español](#español) · [English](#english)

---

## Español

### [0.2.0] — 2026-11-16

#### Añadido

- Documentación bilingüe: español e inglés dentro de cada archivo.
- README principal bilingüe y política de seguridad en `SECURITY.md`.
- Guía de contribución en `CONTRIBUTING.md`: entorno, estructura, cómo añadir un formato de entrada y cómo probar los cambios.
- Licencia MIT en `LICENSE` y declarada en los metadatos del paquete.
- Pruebas con `pytest` sobre motores, extractores y CLI, usando un detector falso para no descargar el modelo.
- `--sin-modelo` para analizar sin la red neuronal, `--json` para consumir el resultado desde otro programa y `--fail-on` para devolver código de salida según la gravedad.
- Columna `Error`: un archivo ilegible se anota con su motivo y el resto del lote continúa.
- Integración continua en Windows y Linux, Dependabot y workflow de release que publica la nota extraída del CHANGELOG.
- `docs/METODO.md` y `docs/USO_RESPONSABLE.md`, código de conducta y plantillas de issue y pull request.
- `ejemplos/` con textos inventados y `evaluacion/` con corpus etiquetado y script de métricas.
- Flag `-V/--version` y metadatos del paquete bilingües, para que PyPI muestre el resumen en español e inglés.

#### Cambiado

- `CHANGELOG.md` se queda en la raíz, donde GitHub lo reconoce, y `docs/` pasa a ser solo el índice y los detalles de uso.
- `torch` y `transformers` pasan a ser el extra opcional `modelo`, y `openpyxl` deja de declararse por no usarse.
- La inferencia neuronal va por lotes y la caché del modelo se resuelve contra el repositorio, no contra el directorio actual.
- La versión se lee de los metadatos del paquete en lugar de estar escrita en dos sitios, y los finales de línea se normalizan con `.gitattributes`.

### [0.1.0] — 2026-11-16

Primera versión utilizable del detector.

#### Añadido

- Análisis de entregas en `.ipynb`, `.pdf`, `.docx`, `.md` y `.txt`.
- Motor híbrido: huella estructural en español (50 %), uniformidad estadística (30 %) y modelo neuronal RoBERTa (20 %).
- Detección de copia entre entregas por similitud de coseno, con código para cuadernos y texto redactado para el resto.
- Reporte CSV en UTF-8 con BOM y separador `;`, ordenado por riesgo, con veredicto y fragmento sospechoso.
- Argumentos de línea de comandos `-c/--carpeta`, `-s/--salida` y `-m/--modelo`.
- README principal con el método, los pesos y los umbrales.

#### Corregido

- El comando `detector-ia` y `python -m detector_ia` fallaban por falta de `src/detector_ia/__init__.py`.
- La ejecución se interrumpía antes de escribir el CSV en consolas Windows cp1252, porque el ✔ del progreso no se podía codificar.
- Un mismo trabajo entregado en dos formatos (por ejemplo PDF y TXT) se marcaba al 100 % de similitud consigo mismo y aparecía como copia entre alumnos.

#### Cambiado

- La carpeta de entrada, el reporte y el modelo ya no están fijos en el código: los umbrales son constantes con nombre y las rutas son argumentos.
- `HF_HOME` solo se define si no estaba ya configurado, para respetar un caché de modelos propio.
- `reporte_*.csv` y el contenido de `revision_ia/` quedan fuera de git; se añade `revision_ia/.gitkeep` para que el repositorio se pueda clonar y usar.

#### Notas

- La herramienta es una ayuda a la revisión: no es una prueba de uso de IA y puede dar falsos positivos y negativos.

---

## English

### [0.2.0] — 2026-11-16

#### Added

- Bilingual documentation: Spanish and English within each file.
- Bilingual root README and a security policy in `SECURITY.md`.
- Tests with `pytest` covering engines, extractors and CLI, using a fake detector so no model is downloaded.
- `--sin-modelo` to analyse without the neural network, `--json` to consume the result from another program and `--fail-on` to exit with a code based on severity.
- `Error` column: an unreadable file is recorded with its reason and the rest of the batch continues.
- Continuous integration on Windows and Linux, Dependabot, and a release workflow that publishes notes extracted from the CHANGELOG.
- `docs/METODO.md` and `docs/USO_RESPONSABLE.md`, code of conduct and issue/pull request templates.
- `ejemplos/` with invented texts and `evaluacion/` with a labelled corpus and metrics script.
- `-V/--version` flag and bilingual package metadata, so PyPI shows the summary in Spanish and English.
- Contributing guide in `CONTRIBUTING.md`: environment, layout, how to add an input format and how to test changes.
- MIT license in `LICENSE`, declared in the package metadata.

#### Changed

- `CHANGELOG.md` stays at the repository root, where GitHub detects it, and `docs/` is now only the index and usage details.
- `torch` and `transformers` become the optional `modelo` extra, and `openpyxl` is no longer declared since nothing uses it.
- Neural inference runs in batches and the model cache resolves against the repository, not the current directory.
- The version is read from package metadata instead of being written in two places, and line endings are normalised via `.gitattributes`.

### [0.1.0] — 2026-11-16

First usable release of the detector.

#### Added

- Analysis of `.ipynb`, `.pdf`, `.docx`, `.md` and `.txt` submissions.
- Hybrid engine: Spanish structural fingerprint (50 %), statistical uniformity (30 %) and RoBERTa neural model (20 %).
- Copy detection between submissions using cosine similarity, on code for notebooks and on written text for the rest.
- CSV report in UTF-8 with BOM and `;` separator, sorted by risk, with a verdict and the suspicious passage.
- Command-line arguments `-c/--carpeta`, `-s/--salida` and `-m/--modelo`.
- Main README describing the method, weights and thresholds.

#### Fixed

- The `detector-ia` command and `python -m detector_ia` failed because `src/detector_ia/__init__.py` was missing.
- Runs aborted before writing the CSV on Windows cp1252 consoles, because the progress ✔ could not be encoded.
- The same assignment submitted in two formats (for example PDF and TXT) scored 100 % similarity against itself and was reported as student-to-student copying.

#### Changed

- Input folder, report path and model are no longer hardcoded: thresholds are named constants and paths are arguments.
- `HF_HOME` is only set when not already configured, so a custom model cache is respected.
- `reporte_*.csv` and the contents of `revision_ia/` are excluded from git; `revision_ia/.gitkeep` is added so the repository can be cloned and used.

#### Notes

- This is a review aid: it is not proof of AI use and can produce both false positives and false negatives.
