# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y versionado [SemVer](https://semver.org/lang/es/).
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [SemVer](https://semver.org/).

[Español](#español) · [English](#english)

---

## Español

### [1.3.0] — 2026-11-21

#### Añadido

- **App 100 % bilingüe**: con `--lang en` (o `--en`) sale en inglés **todo**: consola, ayuda `-h`, veredictos, avisos, informes HTML y Markdown, CSV, CSV de calificaciones y claves del JSON (`summary`, `results`, `Verdict`, `Detail`…). Con `--es`, o sin ningún flag de idioma, sale todo en español.
- **Atajos `--en` y `--es`**, y variable de entorno `DETECTOR_IA_LANG` (la línea de comandos gana).
- **`-h` en un solo idioma** al elegir `--en` o `--es` (sin flag sigue bilingüe); los nombres de opciones, descripciones y ejemplos salen en el idioma elegido (todos los alias siguen funcionando).
- Nombre del CSV por defecto en inglés: `professional_ai_report.csv` con `--en`.
- Mensaje en consola para las entregas con demasiado poco texto (antes solo aparecían en el CSV).
- `evaluar.py` bilingüe (`--lang`/`--en`/`--es`, alias `--no-model`, `--perplexity`, `--no-cleaning`, `--labels`).
- Los errores de dependencias opcionales y de calibración salen en el idioma elegido.
- **Analizar un texto directamente**: `detector-ia --texto "…"` (alias `-t`, `--text`) revisa un texto pegado sin necesidad de carpeta ni archivo. Con `--texto -` lo lee de la entrada estándar (`cat redaccion.txt | detector-ia --texto -`; acepta UTF-8, con BOM y UTF-16, el de PowerShell).
- El resultado sale por pantalla (veredicto, IA pico y media, confianza, avisos y fragmento más sospechoso) y **no se crea CSV** salvo que pongas `-s`. Funcionan `--json`, `--html`, `--markdown`, `--fail-on`, `--alta-precision`, `--frases` y la limpieza de caracteres ocultos. Todo en español o inglés según `--lang`/`--en`.
- `python -m detector_ia` devuelve ahora el código de salida (antes lo ignoraba).

#### Cambiado

- El JSON con `--lang en` usa claves en inglés (con español no cambia).
- `-h` con `--en` o `--es` sale en un solo idioma; sin flag de idioma sigue saliendo bilingüe (el resto de la salida, en español).
- La tabla del HTML/Markdown en inglés muestra `None` en vez de `Ninguno`.

#### Límites

- Los textos analizados y los fragmentos citados se muestran tal cual (no se traducen).
- Los mensajes propios de `argparse` (por ejemplo «invalid choice») siguen el idioma del sistema, no el de `--lang`.
- La carpeta por defecto sigue llamándose `revision_ia`.
- Con un solo texto no hay comparación entre entregas: solo se evalúa la IA, no la copia.
- Los textos cortos (menos de unos 2 bloques) dan una confianza baja; el aviso lo indica.

### [1.2.0] — 2026-11-20

#### Añadido

- **Línea final en consola**: al terminar cada análisis se imprime `detector-ia 1.2.0 · Alberto Ortiz Sánchez · albertoortiz.is-a.dev` por la salida de errores, así que `--json` y las tuberías no se rompen. Se quita con `--sin-credito` o con `DETECTOR_IA_SIN_CREDITO=1`.
- **Pie de crédito en los informes HTML y Markdown** con la web del autor y el enlace a PyPI (también se quita con `--sin-credito`).
- **Caracteres ocultos y homoglifos**: se detectan espacios de ancho cero y letras cirílicas o griegas que imitan letras latinas, se normaliza el texto antes de puntuar y se avisa. En el corpus adversario, sin esta limpieza la detección bajaba de 5/6 a 1–2/6 con estos ataques; con ella se recupera.
- **Corpus adversario** (24 textos, `evaluacion/generar_adversarios.py`): invisibles, homoglifos, erratas y palabras cambiadas de orden; `evaluar.py --sin-limpieza` mide cuánto engañan.
- **Indicio de humanizador** (señal débil): frases torturadas típicas de parafraseadores o caracteres manipulados.
- **`--calibrar CARPETA`** y **`--calibracion JSON`**: ajusta los umbrales a textos humanos de tu centro. Nunca baja de los umbrales por defecto.
- **`--alta-precision`**: umbrales más exigentes; ante la duda el veredicto es `No concluyente` en vez de acusar.
- **`--frases`**: puntúa cada frase con el modelo y las sombrea en el informe HTML. Sin esa opción se sombrean con la huella estructural.
- **Grupos de copia**: si A≈B y B≈C se muestran como un grupo (`Grupo` en el CSV, grafo en el HTML, lista en Markdown y JSON).
- **`--lms RUTA`**: CSV genérico (identificador, veredicto, similitud, grupo, comentario) para copiar a una hoja de calificaciones.
- **Metadatos de Word**: aviso orientativo si un `.docx` largo registra casi 0 minutos de edición.
- **`--separador`** y **`--csv-limpio`** para el CSV.
- **Con `--lang en`** también se traducen los veredictos de la consola y el CSV (cabeceras y valores: `File`, `Verdict`, `HIGH AI RISK`, `None`…). `--json` mantiene los nombres en español. Alias `--gradebook` para `--lms`.

#### Cambiado

- **El CSV empieza ahora con una línea `sep=;`** para que Excel separe bien las columnas con cualquier configuración regional. Si lo lees con pandas u otro programa, usa `--csv-limpio` (o `skiprows=1`).
- Nueva columna `Grupo` al final del CSV.
- Veredicto nuevo `No concluyente` (solo con `--alta-precision`); cuenta como sospechoso en `--fail-on sospechoso`.

#### Límites

- Las erratas y el cambio de orden de palabras no afectan a las señales estructurales; su efecto sobre el modelo neuronal y la perplejidad no está medido en este corpus.
- El indicio de humanizador usa una lista corta de frases; no detecta reescrituras limpias.
- Los minutos de edición de Word son un dato orientativo (un texto pegado desde otro editor también los muestra bajos).
- El CSV para hojas de calificaciones es genérico: no se ha probado contra ninguna plataforma concreta.

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

### [1.3.0] — 2026-11-21

#### Added

- **100 % bilingual app**: with `--lang en` (or `--en`) **everything** comes out in English: console, `-h` help, verdicts, warnings, HTML and Markdown reports, CSV, gradebook CSV and JSON keys (`summary`, `results`, `Verdict`, `Detail`…). With `--es`, or with no language flag at all, everything comes out in Spanish.
- **`--en` and `--es` shortcuts**, and the `DETECTOR_IA_LANG` environment variable (the command line wins).
- **`-h` in a single language** when you choose `--en` or `--es` (with no flag it stays bilingual); option names, descriptions and examples appear in the chosen language (every alias still works).
- Default CSV name in English: `professional_ai_report.csv` with `--en`.
- Console message for submissions with too little text (before they only appeared in the CSV).
- Bilingual `evaluar.py` (`--lang`/`--en`/`--es`, aliases `--no-model`, `--perplexity`, `--no-cleaning`, `--labels`).
- Optional-dependency and calibration errors appear in the chosen language.
- **Analyse a text directly**: `detector-ia --text "…"` (aliases `-t`, `--texto`) checks a pasted text with no folder or file. With `--text -` it reads standard input (`cat essay.txt | detector-ia --text -`; it accepts UTF-8, with BOM, and UTF-16, as used by PowerShell).
- The result is printed (verdict, AI peak and mean, confidence, warnings and most suspicious fragment) and **no CSV is created** unless you pass `-s`. `--json`, `--html`, `--markdown`, `--fail-on`, `--high-precision`, `--sentences` and the hidden-character cleaning all work. Everything in Spanish or English according to `--lang`/`--en`.
- `python -m detector_ia` now returns the exit code (it used to ignore it).

#### Changed

- With `--lang en` the JSON uses English keys (with Spanish nothing changes).
- `-h` with `--en` or `--es` prints in a single language; with no language flag it is still bilingual (everything else, in Spanish).
- The HTML/Markdown table in English shows `None` instead of `Ninguno`.

#### Limits

- Analysed texts and quoted fragments are shown as they are (not translated).
- `argparse`'s own messages (for example "invalid choice") follow the system language, not `--lang`.
- The default folder is still called `revision_ia`.
- With a single text there is no comparison between submissions: only AI is assessed, not copying.
- Short texts (fewer than about 2 blocks) get low confidence; the warning says so.

### [1.2.0] — 2026-11-20

#### Added

- **Closing console line**: after every analysis it prints `detector-ia 1.2.0 · Alberto Ortiz Sánchez · albertoortiz.is-a.dev` to stderr, so `--json` and pipes are unaffected. Disable it with `--no-credit` or `DETECTOR_IA_SIN_CREDITO=1`.
- **Credit footer in the HTML and Markdown reports** with the author's website and the PyPI link (also removed by `--no-credit`).
- **Hidden characters and homoglyphs**: zero-width spaces and Cyrillic/Greek letters that mimic Latin ones are detected, the text is normalised before scoring, and a notice is shown. In the adversarial corpus, without this cleaning detection dropped from 5/6 to 1–2/6 under these attacks; with it, it recovers.
- **Adversarial corpus** (24 texts, `evaluacion/generar_adversarios.py`): invisibles, homoglyphs, typos and swapped words; `evaluar.py --sin-limpieza` measures how much they fool it.
- **Humaniser hint** (weak signal): tortured phrases typical of paraphrasers, or manipulated characters.
- **`--calibrar FOLDER`** and **`--calibracion JSON`**: tune thresholds to your institution's human texts. They never go below the defaults.
- **`--high-precision`**: stricter thresholds; when in doubt the verdict is `No concluyente` instead of an accusation.
- **`--sentences`**: scores each sentence with the model and shades them in the HTML report. Without it, sentences are shaded using the structural fingerprint.
- **Copy groups**: if A≈B and B≈C they appear as one group (`Grupo` column, graph in HTML, list in Markdown and JSON).
- **`--lms PATH`**: generic CSV (id, verdict, similarity, group, comment) to paste into a gradebook.
- **Word metadata**: an indicative notice when a long `.docx` records almost 0 editing minutes.
- **`--separator`** and **`--plain-csv`** for the CSV.
- **With `--lang en`** the console verdicts and the CSV (headers and values: `File`, `Verdict`, `HIGH AI RISK`, `None`…) are now translated too. `--json` keeps the Spanish names. Alias `--gradebook` for `--lms`.

#### Changed

- **The CSV now starts with a `sep=;` line** so Excel splits the columns under any regional setting. If you read it with pandas or another tool, use `--plain-csv` (or `skiprows=1`).
- New `Grupo` column at the end of the CSV.
- New verdict `No concluyente` (only with `--high-precision`); it counts as suspicious for `--fail-on suspicious`.

#### Limits

- Typos and word-order swaps do not affect the structural signals; their effect on the neural model and perplexity is not measured on this corpus.
- The humaniser hint uses a short phrase list; it does not detect clean rewrites.
- Word editing minutes are indicative only (text pasted from another editor also shows low minutes).
- The gradebook CSV is generic: it has not been tested against any specific platform.

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
