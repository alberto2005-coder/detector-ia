# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y versionado [SemVer](https://semver.org/lang/es/).
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [SemVer](https://semver.org/).

[Español](#español) · [English](#english)

---

## Español

### [1.1.0] — 2026-11-19

#### Añadido

- **Plagio por n-gramas con winnowing** (la idea de MOSS): compara el orden de las palabras, no solo el vocabulario. En los cuadernos normaliza el código (variables, números y cadenas), así que renombrar variables no esconde la copia.
- **Pasajes coincidentes**: el informe y la columna `Fragmento_Coincidente` muestran qué texto comparten dos entregas.
- **`--base`**: enunciado o plantilla (archivo o carpeta) cuyo contenido no cuenta como copia, ni en los n-gramas ni en el coseno.
- **`--html`**: informe HTML autocontenido y sin conexión, con resumen, tabla ordenable y filtrable, puntuación por bloque, rasgos marcados dentro del texto, pasajes copiados lado a lado y pares más parecidos. El texto de los alumnos se escapa.
- **`--markdown`** (`--md`): informe en Markdown, útil para resúmenes de GitHub Actions.
- **Confianza y avisos**: columnas `Confianza` (`Alta`/`Media`/`Baja`) y `Avisos` (texto corto, posible texto mixto, puntuación solo por uniformidad, muchas citas) y aviso visible sobre el sesgo con quien no escribe en su lengua.
- **`--perplejidad`** (experimental): señal tipo Binoculars con dos modelos de lenguaje pequeños. Sus límites no están calibrados para español.
- **`--traduccion`** (extra `semantica`): avisa de posible plagio traducido entre español e inglés comparando frases por significado. Solo avisa; no cambia el veredicto.
- `--json` incluye el detalle de cada bloque, la confianza, los avisos y los pasajes coincidentes.
- `--help` y `--version` muestran el autor, su web y los enlaces del proyecto.
- `docs/CI.md`: guía para usar `--fail-on` y los informes en GitHub Actions.
- Corpus de evaluación ampliado de 12 a 42 textos sintéticos en siete categorías, y `evaluar.py` con resumen por categoría, barrido de umbrales y `--json`.

#### Cambiado

- `Similitud_Companero (%)` ahora es la similitud por n-gramas; el coseno clásico pasa a `Similitud_Coseno (%)`. Se marca copia con n-gramas ≥ 60 % o coseno > 88 %.
- Las columnas nuevas del CSV se añaden al final, así que las anteriores no cambian de posición.
- La publicación en PyPI usa `pypa/gh-action-pypi-publish` con atestaciones de procedencia (desde la 1.0.2).
- `numpy` pasa a ser una dependencia declarada.
- CI también en macOS y comprobación del paquete (`twine check`).

#### Medido

- Con solo las señales estructurales, el texto de IA sin editar se detecta (5 de 6), pero no el retocado a mano ni el escrito «como un estudiante» (0 de 14), cuyas puntuaciones se solapan con las del humano formal. Los umbrales no se han cambiado. El modelo neuronal y la perplejidad no se pudieron medir en este entorno; ver [Método y calibración](docs/METODO.md).

### [1.0.2] — 2026-11-18

#### Cambiado

- La publicación en PyPI usa `pypa/gh-action-pypi-publish` con atestaciones, así que la ficha muestra la procedencia verificada del paquete.

### [1.0.1] — 2026-11-18

#### Cambiado

- Metadatos de PyPI completados: mantenedor, enlaces (documentación, método, uso responsable, seguridad, autor y web), clasificadores y palabras clave.
- README: insignias (PyPI, Python, CI, licencia), línea de autoría, enlaces a ejemplos y evaluación, y sección «Autor».

### [1.0.0] — 2026-11-17

#### Añadido

- `-c` acepta también la ruta de un único archivo (`--ruta`), no solo una carpeta.
- Todos los flags tienen alias en inglés (`--folder`, `--path`, `--output`, `--model`, `--no-model`) y `--fail-on` acepta también `none`, `high` y `suspicious`.
- `--lang {es,en}` (`--idioma`) traduce los mensajes de consola; el CSV y los veredictos no cambian.
- Autor, licencia y repositorio en la ayuda de `-h`, y `__author__` en el paquete con el nombre completo.
- Publicación automática en PyPI con Trusted Publishing desde el workflow de release.

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
- Enlaces del repositorio (homepage, issues y changelog) en los metadatos del paquete.

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

### [1.1.0] — 2026-11-19

#### Added

- **N-gram plagiarism with winnowing** (the idea behind MOSS): compares word order, not just vocabulary. In notebooks it normalises the code (variables, numbers and strings), so renaming variables does not hide the copy.
- **Shared passages**: the report and the `Fragmento_Coincidente` column show which text two submissions share.
- **`--base`**: an assignment brief or template (file or folder) whose content does not count as copying, neither in the n-grams nor in the cosine.
- **`--html`**: self-contained, offline HTML report with a summary, a sortable and filterable table, per-block scores, traits marked inside the text, copied passages side by side and the most similar pairs. Student text is escaped.
- **`--markdown`** (`--md`): Markdown report, handy for GitHub Actions summaries.
- **Confidence and notices**: `Confianza` (`Alta`/`Media`/`Baja`) and `Avisos` columns (short text, possibly mixed text, score from uniformity only, many quotations) and a visible notice about bias against people not writing in their first language.
- **`--perplejidad`** (experimental): a Binoculars-style signal with two small language models. Its limits are not calibrated for Spanish.
- **`--traduccion`** (`semantica` extra): flags possible translated plagiarism between Spanish and English by comparing sentences by meaning. It only flags; it does not change the verdict.
- `--json` includes the detail of every block, the confidence, the notices and the shared passages.
- `--help` and `--version` show the author, their website and the project links.
- `docs/CI.md`: guide to using `--fail-on` and the reports in GitHub Actions.
- Evaluation corpus grown from 12 to 42 synthetic texts in seven categories, and `evaluar.py` with a per-category summary, a threshold sweep and `--json`.

#### Changed

- `Similitud_Companero (%)` is now the n-gram similarity; the classic cosine moves to `Similitud_Coseno (%)`. A pair is flagged as copying at n-grams ≥ 60 % or cosine > 88 %.
- The new CSV columns are appended at the end, so the earlier ones keep their position.
- PyPI publishing uses `pypa/gh-action-pypi-publish` with provenance attestations (since 1.0.2).
- `numpy` becomes a declared dependency.
- CI also on macOS and package check (`twine check`).

#### Measured

- With the structural signals alone, unedited AI text is detected (5 of 6), but text edited by hand or written "like a student" is not (0 of 14), and its scores overlap with formal human writing. The thresholds were not changed. The neural model and perplexity could not be measured in this environment; see [Method and calibration](docs/METODO.md).

### [1.0.2] — 2026-11-18

#### Changed

- PyPI publishing now uses `pypa/gh-action-pypi-publish` with attestations, so the project page shows the package's verified provenance.

### [1.0.1] — 2026-11-18

#### Changed

- PyPI metadata completed: maintainer, links (documentation, method, responsible use, security, author and website), classifiers and keywords.
- README: badges (PyPI, Python, CI, licence), credit line, links to examples and evaluation, and an "Author" section.

### [1.0.0] — 2026-11-17

#### Added

- `-c` also accepts the path of a single file (`--ruta`), not just a folder.
- Every flag has an English alias (`--folder`, `--path`, `--output`, `--model`, `--no-model`) and `--fail-on` also accepts `none`, `high` and `suspicious`.
- `--lang {es,en}` (`--idioma`) translates the console messages; the CSV and the verdicts do not change.
- Author, licence and repository in the `-h` help, and `__author__` in the package with the full name.
- Automatic PyPI publishing with Trusted Publishing from the release workflow.

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
- Repository links (homepage, issues and changelog) in the package metadata.
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
