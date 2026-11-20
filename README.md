# Detector IA

[![PyPI](https://img.shields.io/pypi/v/detector-ia?label=PyPI)](https://pypi.org/project/detector-ia/)
[![Python](https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![CI](https://github.com/alberto2005-coder/detector-ia/actions/workflows/ci.yml/badge.svg)](https://github.com/alberto2005-coder/detector-ia/actions/workflows/ci.yml)
[![MIT](https://img.shields.io/badge/Licencia-MIT-green)](https://github.com/alberto2005-coder/detector-ia/blob/main/LICENSE)

[Español](#español) · [English](#english)

> Desarrollado por **[Alberto Ortiz Sánchez](https://github.com/alberto2005-coder/)** · [albertoortiz.is-a.dev](https://albertoortiz.is-a.dev/) · [PyPI](https://pypi.org/project/detector-ia/) · [GitHub](https://github.com/alberto2005-coder/detector-ia)

```bash
pip install detector-ia && detector-ia --version
```

---

## Español

Herramienta de línea de comandos para **detectar indicios de texto generado por IA** y **posibles copias entre entregas** de alumnos, y generar un reporte CSV ordenado por riesgo.

Analiza cuadernos de Jupyter (`.ipynb`), PDF, Word (`.docx`), Markdown (`.md`) y texto plano (`.txt`) en una sola pasada.

> Es una ayuda para la revisión, **no una prueba**. Un porcentaje alto es un motivo para hablar con el alumno o revisar el trabajo a mano; nunca un veredicto automático.

### Documentación

Guías en español e inglés dentro de cada archivo:

- [Uso y formatos](https://github.com/alberto2005-coder/detector-ia/blob/main/docs/USAGE.md): qué se extrae de cada formato y solución de problemas.
- [Changelog](https://github.com/alberto2005-coder/detector-ia/blob/main/CHANGELOG.md): historial de cambios por versión.
- [Integración continua](https://github.com/alberto2005-coder/detector-ia/blob/main/docs/CI.md): usar `--fail-on` y los informes en GitHub Actions.
- [Seguridad](https://github.com/alberto2005-coder/detector-ia/blob/main/SECURITY.md): cómo reportar un problema y qué datos no compartir.
- [Método y calibración](https://github.com/alberto2005-coder/detector-ia/blob/main/docs/METODO.md): de dónde salen los pesos y los umbrales, y cómo recalibrar.
- [Uso responsable](https://github.com/alberto2005-coder/detector-ia/blob/main/docs/USO_RESPONSABLE.md): qué hacer con un caso marcado antes de hablar con el alumno.
- [Contribuir](https://github.com/alberto2005-coder/detector-ia/blob/main/CONTRIBUTING.md): entorno, estructura del código y convención de commits.
- [Ejemplos](https://github.com/alberto2005-coder/detector-ia/blob/main/ejemplos/README.md): textos inventados para probar la herramienta.
- [Evaluación](https://github.com/alberto2005-coder/detector-ia/blob/main/evaluacion/etiquetas.csv): corpus etiquetado y script de métricas ([`evaluar.py`](https://github.com/alberto2005-coder/detector-ia/blob/main/evaluacion/evaluar.py)).
- [Reportar un error](https://github.com/alberto2005-coder/detector-ia/issues/new/choose) · [Código de conducta](https://github.com/alberto2005-coder/detector-ia/blob/main/CODE_OF_CONDUCT.md).
- [Índice de documentación](https://github.com/alberto2005-coder/detector-ia/blob/main/docs/README.md).

### Cómo funciona

Cada entrega se parte en bloques de ~1500 caracteres y cada bloque de más de 300 caracteres se puntúa combinando tres señales:

| Señal | Peso | Qué mide |
| --- | --- | --- |
| Huella estructural en español | 50 % | Guiones largos (—), listas `* **Concepto:**`, encabezados `### 1.`, conectores enciclopédicos (*por tanto*, *cabe destacar*, *en última instancia*) y ausencia de erratas/coloquialismos |
| Uniformidad estadística | 30 % | Baja variación en la longitud de las frases, típica de texto generado |
| Red neuronal | 20 % | [fakespot-ai/roberta-base-ai-text-detection-v1](https://huggingface.co/fakespot-ai/roberta-base-ai-text-detection-v1) |

Opcionalmente (`--perplejidad`, **experimental**) se añade una cuarta señal tipo [Binoculars](https://arxiv.org/abs/2401.12070): la perplejidad del texto bajo dos modelos de lenguaje emparentados. No necesita entrenar con ejemplos de IA, pero sus límites no están calibrados para español: mídela con `evaluacion/evaluar.py --perplejidad` antes de fiarte.

Cada resultado lleva una **confianza** (`Alta`, `Media` o `Baja`) y **avisos** cuando hay poca base: texto corto, bloques que se contradicen (posible texto mixto), puntuación que viene solo de la uniformidad o muchas citas. La confianza no es la probabilidad de acertar; indica cuánto se puede fiar uno del número.

#### Plagio entre entregas

Se compara el *orden* de las palabras, no solo el vocabulario: cada entrega se parte en n-gramas y se seleccionan huellas con *winnowing* (la idea de MOSS). La similitud es el porcentaje de huellas de la entrega más pequeña que aparecen en la otra, así que detecta también la copia parcial y no se deja engañar por trabajos que solo hablan del mismo tema. En los cuadernos se normaliza el código (nombres de variables, números y cadenas), de modo que renombrar variables no esconde la copia. El informe muestra los **pasajes coincidentes** de las dos entregas. El coseno clásico (bolsa de palabras) se sigue calculando como segunda opinión, en la columna `Similitud_Coseno (%)`.

Con `--base` se indica el enunciado o la plantilla que reciben todos los alumnos, para que lo compartido no cuente como copia. Con `--traduccion` (extra `semantica`) se buscan frases con el mismo significado entre entregas en español e inglés; solo genera un aviso, nunca cambia el veredicto. Un mismo trabajo entregado en dos formatos (por ejemplo PDF y TXT) no se cuenta como copia.

#### Qué no hace bien

Con las señales estructurales, el texto generado **sin editar** se detecta mucho mejor que el retocado a mano o el escrito «como un estudiante»; y los textos muy formales, traducidos o de quien escribe en una lengua que no es la suya pueden dar falsos positivos. El detalle y las cifras del corpus de pruebas están en [Método y calibración](https://github.com/alberto2005-coder/detector-ia/blob/main/docs/METODO.md).

### Instalación

Requiere Python 3.13 o superior.

```bash
pip install detector-ia            # desde PyPI: señales estructurales, sin modelo neuronal
pip install "detector-ia[modelo]"  # con el modelo neuronal (torch + transformers)
pip install "detector-ia[semantica]"  # solo para --traduccion (sentence-transformers)
```

El extra `modelo` instala `torch` y `transformers`; sin él la herramienta sigue funcionando con `--sin-modelo`, usando solo las señales estructurales. La primera ejecución descarga el modelo (~500 MB) en `cache_modelo/`, que está fuera del control de versiones. Las siguientes arrancan sin conexión.

Con el paquete instalado el comando es `detector-ia`; comprueba que responde con `detector-ia --version`.

#### Desde el código fuente

Si prefieres trabajar sobre el repositorio, clona y sincroniza. Para esto hace falta [`uv`](https://astral.sh/uv):

```bash
git clone https://github.com/alberto2005-coder/detector-ia.git
cd detector-ia
uv sync --extra modelo
```

Dentro del repositorio los comandos del resto de la guía se ejecutan con `uv run detector-ia`.

### Uso

Copia las entregas a analizar en `revision_ia/` y ejecuta:

```bash
uv run detector-ia
```

Eso lee `revision_ia/`, imprime el progreso y guarda `reporte_profesional_ia.csv`. Hay textos inventados de prueba en `ejemplos/`:

```bash
uv run detector-ia -c ejemplos -s reporte_ejemplos.csv
```

Con opciones:

```bash
uv run detector-ia --carpeta entregas --salida reportes/marzo.csv
uv run detector-ia -c ejemplos/misma_entrega.md --sin-modelo   # un solo archivo
uv run detector-ia --folder entregas --output reporte.csv --lang en
uv run detector-ia --modelo fakespot-ai/roberta-base-ai-text-detection-v1
uv run detector-ia -c entregas --html informe.html --markdown informe.md   # informes para leer
uv run detector-ia -c entregas --base enunciado.ipynb                      # sin contar la plantilla
```

También funciona sin `uv`, con el entorno activado:

```bash
python -m detector_ia --carpeta revision_ia
```

#### Opciones

| Opción | Por defecto | Descripción |
| --- | --- | --- |
| `-c`, `--carpeta`, `--ruta`, `--folder`, `--path` | `revision_ia` | Carpeta con las entregas o ruta de un archivo concreto |
| `-s`, `--salida`, `--output` | `reporte_profesional_ia.csv` | Ruta del reporte generado |
| `-m`, `--modelo`, `--model` | RoBERTa de detección de IA | Modelo de Hugging Face a usar |
| `--sin-modelo`, `--no-model` | desactivado | Analiza solo con las señales estructurales, sin descargar el modelo |
| `--html RUTA` | — | Guarda además un informe HTML autocontenido (sin conexión, con marcas por frase y pasajes coincidentes) |
| `--markdown RUTA`, `--md` | — | Guarda además un informe en Markdown |
| `--base RUTA` | — | Enunciado o plantilla (archivo o carpeta): lo que coincida con ella no cuenta como copia |
| `--perplejidad`, `--perplexity` | desactivado | Añade la señal de perplejidad tipo Binoculars (experimental; requiere el extra `modelo`) |
| `--traduccion`, `--translation` | desactivado | Busca plagio traducido entre español e inglés (requiere el extra `semantica`) |
| `--alta-precision`, `--high-precision` | desactivado | Umbrales más exigentes; ante la duda el veredicto es `No concluyente` en vez de acusar |
| `--calibrar CARPETA`, `--calibrate` | — | Mide textos escritos por personas y guarda umbrales ajustados (JSON); nunca bajan de los de por defecto |
| `--calibracion JSON`, `--calibration` | — | Usa los umbrales de un archivo creado con `--calibrar` |
| `--frases`, `--sentences` | desactivado | Puntúa cada frase con el modelo y la sombrea en el informe HTML (más lento) |
| `--lms RUTA`, `--gradebook` | — | CSV genérico (coma) con identificador, veredicto, similitud, grupo y comentario para una hoja de calificaciones |
| `--separador`, `--separator` | `;` | Separador del CSV: `;`, `,` o `tab` |
| `--csv-limpio`, `--plain-csv` | desactivado | No añade la línea `sep=;` del principio (úsalo para leer el CSV con pandas) |
| `--sin-credito`, `--no-credit` | desactivado | Quita la línea final de consola y el pie de los informes (también con `DETECTOR_IA_SIN_CREDITO=1`) |
| `--json` | desactivado | Escribe el resultado en JSON por la salida estándar (con el detalle de cada bloque) y el progreso por la de errores |
| `--fail-on` | `ninguno` | Devuelve código de salida 1 si el reporte alcanza `error`, `alto`/`high` o `sospechoso`/`suspicious` (también vale `none`) |
| `--lang`, `--idioma` | `es` | Idioma de los mensajes de consola (`es`/`en`); el CSV no cambia |
| `-V`, `--version` | — | Muestra la versión instalada y sale |

Todos los flags, sus valores y la ayuda de `-h` se pueden escribir en español o en inglés: `--carpeta entregas` y `--folder entregas` hacen lo mismo, igual que `--salida`/`--output`. Con `--lang en` se traducen los mensajes de consola, los veredictos y el CSV (cabeceras `File`, `Format`, `AI_Mean (%)`, `AI_Peak_Max (%)`, `Peer_Similarity (%)`, `Matches_With`, `Verdict`, `Suspicious_Fragment`, `Error`, `Cosine_Similarity (%)`, `Confidence`, `Warnings`, `Matching_Fragment`, `Translated_Similarity (%)`, `Group`). Sin `--lang en` todo queda en español como siempre. La salida `--json` mantiene siempre los nombres en español para que los programas que la leen no cambien. Si lees el CSV desde un programa, fija el idioma para que las columnas no varíen.

### Reporte

El CSV se guarda en UTF-8 con BOM y separador `;`. La primera línea es `sep=;`, una pista que hace que Excel separe bien las columnas con cualquier configuración regional (sin ella, un Excel configurado con coma lo mete todo en una sola columna). Si lo lees con pandas u otro programa, usa `--csv-limpio` o `skiprows=1`. Columnas:

- **Archivo / Formato**: nombre y extensión de la entrega.
- **IA_Media (%)**: media de la puntuación híbrida de los bloques evaluados.
- **IA_Pico_Max (%)**: bloque con la puntuación más alta, el que más se parece a texto de IA.
- **Similitud_Companero (%)** y **Coincide_Con**: similitud por n-gramas con la entrega más parecida y su nombre si llega al 40 % (o si el coseno supera el 75 %). *Desde la 1.1.0 esta columna ya no es el coseno; el coseno está en `Similitud_Coseno (%)`.*
- **Veredicto**: `ALTO RIESGO IA`, `REVISAR COPIA ENTRE ALUMNOS`, `Sospechoso (Revisar)`, `Normal`, `Poco texto` o, solo con `--alta-precision`, `No concluyente`.
- **Fragmento_Sospechoso**: el bloque con mayor puntuación, para leerlo en contexto.
- **Error**: vacía salvo que el archivo no se pudiera leer o puntuar; en ese caso el veredicto es `Error` y aquí aparece el motivo, sin detener el resto del lote.
- Columnas añadidas en la 1.1.0, al final para no mover las anteriores: **Similitud_Coseno (%)**, **Confianza** (`Alta`/`Media`/`Baja`), **Avisos**, **Fragmento_Coincidente** (el pasaje más largo que comparte con `Coincide_Con`) y **Similitud_Traducida (%)** (solo con `--traduccion`).
- Columna añadida en la 1.2.0: **Grupo** (`G1`, `G2`… si varias entregas se copian entre sí; vacía si no).

Umbrales actuales (en `src/detector_ia/main.py`): pico ≥ 58 % o media ≥ 45 % es alto riesgo; pico ≥ 45 % o media ≥ 35 % es sospechoso; similitud por n-gramas ≥ 60 % o coseno > 88 % es posible copia.

#### Qué hay de nuevo en la 1.2.0

- **Crédito**: al terminar cada análisis se imprime `detector-ia 1.2.0 · Alberto Ortiz Sánchez · albertoortiz.is-a.dev` por la salida de errores, y los informes HTML y Markdown llevan un pie con la web del autor y el enlace a PyPI. `--sin-credito` lo quita.
- **Trucos con caracteres**: los espacios de ancho cero y las letras cirílicas que imitan letras latinas se detectan, se normalizan y se avisan. Medido en el corpus adversario (solo señales estructurales), sin esa limpieza la detección bajaba de 5/6 a 1–2/6; con ella vuelve a 5/6. Las erratas y el cambio de orden de palabras no afectan a esas señales; su efecto sobre el modelo neuronal no está medido.
- **Calibración**: `detector-ia --calibrar textos_humanos/ -s calibracion.json` y luego `--calibracion calibracion.json`. Hacen falta al menos 10 textos; con pocos, los umbrales no son fiables.
- **Grupos de copia**, **`--lms`**, **metadatos de Word** y **puntuación por frase**: ver el changelog. Los minutos de edición de Word y el indicio de humanizador son señales débiles y orientativas.

#### Informe HTML

`--html informe.html` genera una sola página que se abre sin conexión (no carga nada de internet): resumen por veredicto, tabla que se ordena y se filtra, puntuación de cada bloque, los rasgos que suben o bajan la puntuación marcados dentro del texto, los pasajes copiados lado a lado y los pares de entregas más parecidos. El texto de los alumnos se escapa, así que no puede ejecutar nada. Como contiene trabajos reales, trátalo igual que el CSV.

### Estructura

```
detector-ia/
├── src/detector_ia/
│   ├── main.py          # CLI, umbrales y generación del reporte
│   ├── extractores.py   # Lectura de .ipynb, .pdf, .docx, .txt y .md
│   ├── motores.py       # Modelo neuronal, huella estructural y puntuación por bloques
│   ├── perplejidad.py   # Señal tipo Binoculars (opcional, experimental)
│   ├── similitud.py     # N-gramas con winnowing, fragmentos copiados y plantilla base
│   ├── semantica.py     # Plagio traducido por significado (opcional)
│   ├── confianza.py     # Nivel de confianza y avisos
│   └── informes.py      # Informes HTML y Markdown
├── tests/               # Pruebas con un detector falso, sin descargar el modelo
├── docs/                # Índice, método, uso responsable y formatos
├── ejemplos/            # Textos inventados para probar
├── evaluacion/          # Corpus etiquetado y script de métricas
├── scripts/             # Notas de release a partir del CHANGELOG
├── .github/             # CI, releases, Dependabot y plantillas
├── revision_ia/         # Entregas de entrada (ignoradas por git)
├── README.md            # Guía completa, en español e inglés
├── CONTRIBUTING.md      # Cómo contribuir
├── SECURITY.md          # Política de seguridad
├── CODE_OF_CONDUCT.md   # Código de conducta
├── CHANGELOG.md         # Historial de cambios por versión
├── LICENSE              # Licencia MIT
├── pyproject.toml       # Metadatos, dependencias y entry point
├── uv.lock              # Versiones exactas de las dependencias
├── .gitattributes       # Finales de línea normalizados
└── .gitignore           # Excluye .venv, cache_modelo y entregas
```

### Privacidad

Las entregas de los alumnos y los reportes generados están excluidos de git (`.gitignore`), porque contienen trabajos reales y nombres de archivo. No los subas al repositorio ni compartas los CSV fuera del ámbito docente.

### Autor

Desarrollado por **Alberto Ortiz Sánchez**.

- GitHub: <https://github.com/alberto2005-coder/>
- Web personal: <https://albertoortiz.is-a.dev/>
- PyPI: <https://pypi.org/project/detector-ia/>
- Incidencias: <https://github.com/alberto2005-coder/detector-ia/issues>

### Licencia

Distribuido bajo la licencia MIT. Consulta [LICENSE](https://github.com/alberto2005-coder/detector-ia/blob/main/LICENSE). © 2026 Alberto Ortiz Sánchez.

---

## English

A command-line tool to **spot AI-generated text** and **possible copying between students' submissions**, and to produce a CSV report sorted by risk.

It analyses Jupyter notebooks (`.ipynb`), PDF, Word (`.docx`), Markdown (`.md`) and plain text (`.txt`) in a single pass.

> This is a review aid, **not evidence**. A high score is a reason to talk to the student or read the work by hand; never an automatic verdict.

### Documentation

Guides in Spanish and English within each file:

- [Usage and formats](https://github.com/alberto2005-coder/detector-ia/blob/main/docs/USAGE.md): what is extracted from each format and troubleshooting.
- [Changelog](https://github.com/alberto2005-coder/detector-ia/blob/main/CHANGELOG.md): change history per version.
- [Continuous integration](https://github.com/alberto2005-coder/detector-ia/blob/main/docs/CI.md): using `--fail-on` and the reports in GitHub Actions.
- [Security](https://github.com/alberto2005-coder/detector-ia/blob/main/SECURITY.md): how to report a problem and which data never to share.
- [Method and calibration](https://github.com/alberto2005-coder/detector-ia/blob/main/docs/METODO.md): where the weights and thresholds come from, and how to recalibrate.
- [Responsible use](https://github.com/alberto2005-coder/detector-ia/blob/main/docs/USO_RESPONSABLE.md): what to do with a flagged case before talking to the student.
- [Contributing](https://github.com/alberto2005-coder/detector-ia/blob/main/CONTRIBUTING.md): environment, code layout and commit convention.
- [Examples](https://github.com/alberto2005-coder/detector-ia/blob/main/ejemplos/README.md): invented texts for trying the tool.
- [Evaluation](https://github.com/alberto2005-coder/detector-ia/blob/main/evaluacion/etiquetas.csv): labelled corpus and metrics script ([`evaluar.py`](https://github.com/alberto2005-coder/detector-ia/blob/main/evaluacion/evaluar.py)).
- [Report a bug](https://github.com/alberto2005-coder/detector-ia/issues/new/choose) · [Code of conduct](https://github.com/alberto2005-coder/detector-ia/blob/main/CODE_OF_CONDUCT.md).
- [Documentation index](https://github.com/alberto2005-coder/detector-ia/blob/main/docs/README.md).

### How it works

Each submission is split into blocks of ~1500 characters, and every block longer than 300 characters is scored by combining three signals:

| Signal | Weight | What it measures |
| --- | --- | --- |
| Spanish structural fingerprint | 50 % | Em dashes (—), `* **Term:**` lists, `### 1.` headings, encyclopedic connectors (*por tanto*, *cabe destacar*, *en última instancia*) and absence of typos or colloquialisms |
| Statistical uniformity | 30 % | Low variation in sentence length, typical of generated text |
| Neural network | 20 % | [fakespot-ai/roberta-base-ai-text-detection-v1](https://huggingface.co/fakespot-ai/roberta-base-ai-text-detection-v1) |

Optionally (`--perplejidad`, **experimental**) a fourth signal in the style of [Binoculars](https://arxiv.org/abs/2401.12070) is added: the perplexity of the text under two related language models. It needs no training on AI examples, but its limits are not calibrated for Spanish: measure it with `evaluacion/evaluar.py --perplejidad` before trusting it.

Every result carries a **confidence** (`Alta`, `Media` or `Baja`) and **notices** when the basis is thin: short text, blocks that disagree (possibly mixed text), a score that comes only from uniformity, or many quotations. Confidence is not the probability of being right; it tells you how far the number can be trusted.

#### Plagiarism between submissions

The *order* of the words is compared, not just the vocabulary: every submission is split into n-grams and fingerprints are chosen with *winnowing* (the idea behind MOSS). Similarity is the share of fingerprints of the smaller submission found in the other, so it also catches partial copying and is not fooled by pieces of work that merely cover the same topic. In notebooks the code is normalised (variable names, numbers and strings), so renaming variables does not hide the copy. The report shows the **shared passages** from both submissions. The classic cosine (bag of words) is still computed as a second opinion, in the `Similitud_Coseno (%)` column.

`--base` takes the assignment brief or template every student receives, so what is shared does not count as copying. `--traduccion` (the `semantica` extra) looks for sentences with the same meaning across Spanish and English submissions; it only raises a notice and never changes the verdict. The same assignment submitted in two formats (say PDF and TXT) is not counted as copying.

#### What it does not do well

With the structural signals, **unedited** generated text is detected far better than text edited by hand or written "like a student"; and very formal or translated text, or text by people not writing in their first language, can produce false positives. The details and the numbers from the test corpus are in [Method and calibration](https://github.com/alberto2005-coder/detector-ia/blob/main/docs/METODO.md).

### Install

Requires Python 3.13 or newer.

```bash
pip install detector-ia            # from PyPI: structural signals, no neural model
pip install "detector-ia[modelo]"  # with the neural model (torch + transformers)
pip install "detector-ia[semantica]"  # only for --traduccion (sentence-transformers)
```

The `modelo` extra installs `torch` and `transformers`; without it the tool still works with `--sin-modelo`, using only the structural signals. The first run downloads the model (~500 MB) into `cache_modelo/`, which is not tracked by git. Later runs start offline.

Once installed, the command is `detector-ia`; check it with `detector-ia --version`.

#### From source

If you prefer working on the repository, clone and sync. This needs [`uv`](https://astral.sh/uv):

```bash
git clone https://github.com/alberto2005-coder/detector-ia.git
cd detector-ia
uv sync --extra modelo
```

Inside the repository, the commands in the rest of this guide run as `uv run detector-ia`.

### Usage

Copy the submissions into `revision_ia/` and run:

```bash
uv run detector-ia
```

That reads `revision_ia/`, prints progress and writes `reporte_profesional_ia.csv`. There are invented test texts in `ejemplos/`:

```bash
uv run detector-ia -c ejemplos -s reporte_ejemplos.csv
```

With options:

```bash
uv run detector-ia --carpeta entregas --salida reportes/marzo.csv
uv run detector-ia -c ejemplos/misma_entrega.md --sin-modelo   # a single file
uv run detector-ia --folder entregas --output reporte.csv --lang en
uv run detector-ia --modelo fakespot-ai/roberta-base-ai-text-detection-v1
uv run detector-ia -c entregas --html report.html --markdown report.md   # reports to read
uv run detector-ia -c entregas --base brief.ipynb                        # ignore the template
```

It also works without `uv`, with the environment active:

```bash
python -m detector_ia --carpeta revision_ia
```

#### Options

| Option | Default | Description |
| --- | --- | --- |
| `-c`, `--carpeta`, `--ruta`, `--folder`, `--path` | `revision_ia` | Folder with the submissions, or the path of a single file |
| `-s`, `--salida`, `--output` | `reporte_profesional_ia.csv` | Path of the generated report |
| `-m`, `--modelo`, `--model` | AI-detection RoBERTa | Hugging Face model to use |
| `--sin-modelo`, `--no-model` | off | Structural signals only, without downloading the model |
| `--html PATH` | — | Also save a self-contained HTML report (works offline, with per-sentence marks and shared passages) |
| `--markdown PATH`, `--md` | — | Also save a Markdown report |
| `--base PATH` | — | Assignment brief or template (file or folder): what matches it does not count as copying |
| `--perplejidad`, `--perplexity` | off | Add the Binoculars-style perplexity signal (experimental; needs the `modelo` extra) |
| `--traduccion`, `--translation` | off | Look for translated plagiarism between Spanish and English (needs the `semantica` extra) |
| `--high-precision`, `--alta-precision` | off | Stricter thresholds; when in doubt the verdict is `No concluyente` instead of an accusation |
| `--calibrate FOLDER`, `--calibrar` | — | Measures human-written texts and saves tuned thresholds (JSON); they never go below the defaults |
| `--calibration JSON`, `--calibracion` | — | Uses the thresholds from a file created with `--calibrate` |
| `--sentences`, `--frases` | off | Scores each sentence with the model and shades it in the HTML report (slower) |
| `--lms PATH`, `--gradebook` | — | Generic CSV (comma) with id, verdict, similarity, group and comment for a gradebook |
| `--separator`, `--separador` | `;` | CSV separator: `;`, `,` or `tab` |
| `--plain-csv`, `--csv-limpio` | off | Do not add the `sep=;` first line (use it to read the CSV with pandas) |
| `--no-credit`, `--sin-credito` | off | Removes the closing console line and the report footer (also with `DETECTOR_IA_SIN_CREDITO=1`) |
| `--json` | off | Write the result as JSON on stdout (with per-block detail) and progress on stderr |
| `--fail-on` | `ninguno` | Exit with code 1 when the report reaches `error`, `alto`/`high` or `sospechoso`/`suspicious` (`none` works too) |
| `--lang`, `--idioma` | `es` | Language of the console messages (`es`/`en`); the CSV does not change |
| `-V`, `--version` | — | Print the installed version and exit |

Every flag, its values and the `-h` help can be written in Spanish or in English: `--carpeta entregas` and `--folder entregas` are the same thing, as are `--salida`/`--output`. With `--lang en` the console messages, the verdicts and the CSV are translated (headers `File`, `Format`, `AI_Mean (%)`, `AI_Peak_Max (%)`, `Peer_Similarity (%)`, `Matches_With`, `Verdict`, `Suspicious_Fragment`, `Error`, `Cosine_Similarity (%)`, `Confidence`, `Warnings`, `Matching_Fragment`, `Translated_Similarity (%)`, `Group`). Without `--lang en` everything stays in Spanish as before. The `--json` output always keeps the Spanish names so programs that read it do not change. If you read the CSV from a program, fix the language so the columns do not vary.

### Report

The CSV is written in UTF-8 with BOM and a `;` separator. Its first line is `sep=;`, a hint that makes Excel split the columns correctly under any regional setting (without it, an Excel set to use commas puts everything in one column). If you read it with pandas or another tool, use `--plain-csv` or `skiprows=1`. Columns:

- **Archivo / Formato**: file name and extension of the submission.
- **IA_Media (%)**: mean hybrid score of the scored blocks.
- **IA_Pico_Max (%)**: highest-scoring block, the most AI-like passage.
- **Similitud_Companero (%)** and **Coincide_Con**: n-gram similarity with the most similar submission, and its name when it reaches 40 % (or the cosine is above 75 %). *Since 1.1.0 this column is no longer the cosine; the cosine is in `Similitud_Coseno (%)`.*
- **Veredicto**: `ALTO RIESGO IA`, `REVISAR COPIA ENTRE ALUMNOS`, `Sospechoso (Revisar)`, `Normal`, `Poco texto` or, only with `--high-precision`, `No concluyente`.
- **Fragmento_Sospechoso**: the highest-scoring block, to read it in context.
- **Error**: empty unless the file could not be read or scored; the verdict is then `Error` and the reason appears here, without stopping the rest of the batch.
- Columns added in 1.1.0, at the end so the earlier ones do not move: **Similitud_Coseno (%)**, **Confianza** (`Alta`/`Media`/`Baja`), **Avisos**, **Fragmento_Coincidente** (the longest passage shared with `Coincide_Con`) and **Similitud_Traducida (%)** (only with `--traduccion`).
- Column added in 1.2.0: **Grupo** (`G1`, `G2`… when several submissions copy each other; empty otherwise).

Current thresholds (in `src/detector_ia/main.py`): peak ≥ 58 % or mean ≥ 45 % is high risk; peak ≥ 45 % or mean ≥ 35 % is suspicious; n-gram similarity ≥ 60 % or cosine > 88 % is possible copying.

#### What is new in 1.2.0

- **Credit**: after each analysis `detector-ia 1.2.0 · Alberto Ortiz Sánchez · albertoortiz.is-a.dev` is printed to stderr, and the HTML and Markdown reports carry a footer with the author's website and the PyPI link. `--no-credit` removes it.
- **Character tricks**: zero-width spaces and Cyrillic letters that mimic Latin ones are detected, normalised and flagged. Measured on the adversarial corpus (structural signals only), without this cleaning detection fell from 5/6 to 1–2/6; with it it returns to 5/6. Typos and word-order swaps do not affect those signals; their effect on the neural model is not measured.
- **Calibration**: `detector-ia --calibrate human_texts/ -s calibration.json`, then `--calibration calibration.json`. At least 10 texts are needed; with fewer, the thresholds are not reliable.
- **Copy groups**, **`--lms`**, **Word metadata** and **per-sentence scoring**: see the changelog. Word editing minutes and the humaniser hint are weak, indicative signals.

#### HTML report

`--html report.html` writes a single page that opens offline (it loads nothing from the internet): a summary by verdict, a sortable and filterable table, the score of every block, the traits that raise or lower the score marked inside the text, copied passages side by side and the most similar pairs of submissions. Student text is escaped, so it cannot run anything. Since it contains real work, treat it like the CSV.

### Layout

```
detector-ia/
├── src/detector_ia/
│   ├── main.py          # CLI, thresholds and report generation
│   ├── extractores.py   # Readers for .ipynb, .pdf, .docx, .txt and .md
│   ├── motores.py       # Neural model, structural fingerprint and per-block scoring
│   ├── perplejidad.py   # Binoculars-style signal (optional, experimental)
│   ├── similitud.py     # N-grams with winnowing, copied passages and base template
│   ├── semantica.py     # Translated plagiarism by meaning (optional)
│   ├── confianza.py     # Confidence level and notices
│   └── informes.py      # HTML and Markdown reports
├── tests/               # Tests with a fake detector, no model download
├── docs/                # Index, method, responsible use and formats
├── ejemplos/            # Invented texts for trying the tool
├── evaluacion/          # Labelled corpus and metrics script
├── scripts/             # Release notes from the CHANGELOG
├── .github/             # CI, releases, Dependabot and templates
├── revision_ia/         # Input submissions (git-ignored)
├── README.md            # Full guide, in Spanish and English
├── CONTRIBUTING.md      # How to contribute
├── SECURITY.md          # Security policy
├── CODE_OF_CONDUCT.md   # Code of conduct
├── CHANGELOG.md         # Change history per version
├── LICENSE              # MIT license
├── pyproject.toml       # Metadata, dependencies and entry point
├── uv.lock              # Exact dependency versions
├── .gitattributes       # Normalized line endings
└── .gitignore           # Excludes .venv, cache_modelo and submissions
```

### Privacy

Student submissions and generated reports are excluded from git (`.gitignore`), because they contain real work and file names. Do not push them to the repository or share the CSVs outside the classroom.

### Author

Developed by **Alberto Ortiz Sánchez**.

- GitHub: <https://github.com/alberto2005-coder/>
- Personal website: <https://albertoortiz.is-a.dev/>
- PyPI: <https://pypi.org/project/detector-ia/>
- Issues: <https://github.com/alberto2005-coder/detector-ia/issues>

### License

Distributed under the MIT license. See [LICENSE](https://github.com/alberto2005-coder/detector-ia/blob/main/LICENSE). © 2026 Alberto Ortiz Sánchez.
