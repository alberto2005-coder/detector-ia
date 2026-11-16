# Detector IA

[Español](#español) · [English](#english)

---

## Español

Herramienta de línea de comandos para **detectar indicios de texto generado por IA** y **posibles copias entre entregas** de alumnos, y generar un reporte CSV ordenado por riesgo.

Analiza cuadernos de Jupyter (`.ipynb`), PDF, Word (`.docx`), Markdown (`.md`) y texto plano (`.txt`) en una sola pasada.

> Es una ayuda para la revisión, **no una prueba**. Un porcentaje alto es un motivo para hablar con el alumno o revisar el trabajo a mano; nunca un veredicto automático.

### Documentación

Guías en español e inglés dentro de cada archivo:

- [Uso y formatos](docs/USAGE.md): qué se extrae de cada formato y solución de problemas.
- [Changelog](CHANGELOG.md): historial de cambios por versión.
- [Seguridad](SECURITY.md): cómo reportar un problema y qué datos no compartir.
- [Método y calibración](docs/METODO.md): de dónde salen los pesos y los umbrales, y cómo recalibrar.
- [Uso responsable](docs/USO_RESPONSABLE.md): qué hacer con un caso marcado antes de hablar con el alumno.
- [Contribuir](CONTRIBUTING.md): entorno, estructura del código y convención de commits.
- [Índice de documentación](docs/README.md).

### Cómo funciona

Cada entrega se parte en bloques de ~1500 caracteres y cada bloque de más de 300 caracteres se puntúa combinando tres señales:

| Señal | Peso | Qué mide |
| --- | --- | --- |
| Huella estructural en español | 50 % | Guiones largos (—), listas `* **Concepto:**`, encabezados `### 1.`, conectores enciclopédicos (*por tanto*, *cabe destacar*, *en última instancia*) y ausencia de erratas/coloquialismos |
| Uniformidad estadística | 30 % | Baja variación en la longitud de las frases, típica de texto generado |
| Red neuronal | 20 % | [fakespot-ai/roberta-base-ai-text-detection-v1](https://huggingface.co/fakespot-ai/roberta-base-ai-text-detection-v1) |

Además se calcula la **similitud de coseno** (bolsa de palabras) entre todas las entregas: en los cuadernos se compara el código (o el texto, si el cuaderno no tiene código) y en el resto el texto redactado. Un mismo trabajo entregado en dos formatos (por ejemplo PDF y TXT) no se cuenta como copia.

### Instalación

Requiere Python 3.13 o superior y, si no tienes `uv`, puedes instalarlo desde [astral.sh/uv](https://astral.sh/uv).

```bash
git clone https://github.com/alberto2005-coder/detector-ia.git
cd detector-ia
uv sync --extra modelo
```

El extra `modelo` instala `torch` y `transformers`; sin él la herramienta sigue funcionando con `--sin-modelo`, usando solo las señales estructurales. La primera ejecución descarga el modelo (~500 MB) en `cache_modelo/`, que está fuera del control de versiones. Las siguientes arrancan sin conexión.

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
uv run detector-ia --modelo fakespot-ai/roberta-base-ai-text-detection-v1
```

También funciona sin `uv`, con el entorno activado:

```bash
python -m detector_ia --carpeta revision_ia
```

#### Opciones

| Opción | Por defecto | Descripción |
| --- | --- | --- |
| `-c`, `--carpeta` | `revision_ia` | Carpeta con las entregas a analizar |
| `-s`, `--salida` | `reporte_profesional_ia.csv` | Ruta del reporte generado |
| `-m`, `--modelo` | RoBERTa de detección de IA | Modelo de Hugging Face a usar |
| `--sin-modelo` | desactivado | Analiza solo con las señales estructurales, sin descargar el modelo |
| `--json` | desactivado | Escribe el resultado en JSON por la salida estándar y el progreso por la de errores |
| `--fail-on` | `ninguno` | Devuelve código de salida 1 si el reporte alcanza `error`, `alto` o `sospechoso` |
| `-V`, `--version` | — | Muestra la versión instalada y sale |

### Reporte

El CSV se guarda en UTF-8 con BOM y separador `;` para que abra directamente en Excel en español. Columnas:

- **Archivo / Formato**: nombre y extensión de la entrega.
- **IA_Media (%)**: media de la puntuación híbrida de los bloques evaluados.
- **IA_Pico_Max (%)**: bloque con la puntuación más alta, el que más se parece a texto de IA.
- **Similitud_Companero (%)** y **Coincide_Con**: entrega más parecida y su nombre si supera el 75 %.
- **Veredicto**: `ALTO RIESGO IA`, `REVISAR COPIA ENTRE ALUMNOS`, `Sospechoso (Revisar)`, `Normal` o `Poco texto`.
- **Fragmento_Sospechoso**: el bloque con mayor puntuación, para leerlo en contexto.
- **Error**: vacía salvo que el archivo no se pudiera leer o puntuar; en ese caso el veredicto es `Error` y aquí aparece el motivo, sin detener el resto del lote.

Umbrales actuales (en `src/detector_ia/main.py`): pico ≥ 58 % o media ≥ 45 % es alto riesgo; pico ≥ 45 % o media ≥ 35 % es sospechoso; similitud > 88 % es posible copia.

### Estructura

```
detector-ia/
├── src/detector_ia/
│   ├── main.py          # CLI, umbrales y generación del reporte
│   ├── extractores.py   # Lectura de .ipynb, .pdf, .docx, .txt y .md
│   └── motores.py       # Modelo neuronal, huella estructural y similitud
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

### Licencia

Distribuido bajo la licencia MIT. Consulta [LICENSE](LICENSE) para el texto completo.

---

## English

A command-line tool to **spot AI-generated text** and **possible copying between students' submissions**, and to produce a CSV report sorted by risk.

It analyses Jupyter notebooks (`.ipynb`), PDF, Word (`.docx`), Markdown (`.md`) and plain text (`.txt`) in a single pass.

> This is a review aid, **not evidence**. A high score is a reason to talk to the student or read the work by hand; never an automatic verdict.

### Documentation

Guides in Spanish and English within each file:

- [Usage and formats](docs/USAGE.md): what is extracted from each format and troubleshooting.
- [Changelog](CHANGELOG.md): change history per version.
- [Security](SECURITY.md): how to report a problem and which data never to share.
- [Method and calibration](docs/METODO.md): where the weights and thresholds come from, and how to recalibrate.
- [Responsible use](docs/USO_RESPONSABLE.md): what to do with a flagged case before talking to the student.
- [Contributing](CONTRIBUTING.md): environment, code layout and commit convention.
- [Documentation index](docs/README.md).

### How it works

Each submission is split into blocks of ~1500 characters, and every block longer than 300 characters is scored by combining three signals:

| Signal | Weight | What it measures |
| --- | --- | --- |
| Spanish structural fingerprint | 50 % | Em dashes (—), `* **Term:**` lists, `### 1.` headings, encyclopedic connectors (*por tanto*, *cabe destacar*, *en última instancia*) and absence of typos or colloquialisms |
| Statistical uniformity | 30 % | Low variation in sentence length, typical of generated text |
| Neural network | 20 % | [fakespot-ai/roberta-base-ai-text-detection-v1](https://huggingface.co/fakespot-ai/roberta-base-ai-text-detection-v1) |

**Cosine similarity** (bag of words) is also computed between all submissions: notebooks are compared by code (or by their text, when they have no code), everything else by written text. The same assignment submitted in two formats (say PDF and TXT) is not counted as copying.

### Install

Requires Python 3.13 or newer; if you don't have `uv`, install it from [astral.sh/uv](https://astral.sh/uv).

```bash
git clone https://github.com/alberto2005-coder/detector-ia.git
cd detector-ia
uv sync --extra modelo
```

The `modelo` extra installs `torch` and `transformers`; without it the tool still works with `--sin-modelo`, using only the structural signals. The first run downloads the model (~500 MB) into `cache_modelo/`, which is not tracked by git. Later runs start offline.

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
uv run detector-ia --modelo fakespot-ai/roberta-base-ai-text-detection-v1
```

It also works without `uv`, with the environment active:

```bash
python -m detector_ia --carpeta revision_ia
```

#### Options

| Option | Default | Description |
| --- | --- | --- |
| `-c`, `--carpeta` | `revision_ia` | Folder with the submissions to analyse |
| `-s`, `--salida` | `reporte_profesional_ia.csv` | Path of the generated report |
| `-m`, `--modelo` | AI-detection RoBERTa | Hugging Face model to use |
| `--sin-modelo` | off | Structural signals only, without downloading the model |
| `--json` | off | Write the result as JSON on stdout and progress on stderr |
| `--fail-on` | `ninguno` | Exit with code 1 when the report reaches `error`, `alto` or `sospechoso` |
| `-V`, `--version` | — | Print the installed version and exit |

### Report

The CSV is written in UTF-8 with BOM and a `;` separator so it opens directly in Spanish-locale Excel. Columns:

- **Archivo / Formato**: file name and extension of the submission.
- **IA_Media (%)**: mean hybrid score of the scored blocks.
- **IA_Pico_Max (%)**: highest-scoring block, the most AI-like passage.
- **Similitud_Companero (%)** and **Coincide_Con**: most similar submission, with its name when similarity is above 75 %.
- **Veredicto**: `ALTO RIESGO IA`, `REVISAR COPIA ENTRE ALUMNOS`, `Sospechoso (Revisar)`, `Normal` or `Poco texto`.
- **Fragmento_Sospechoso**: the highest-scoring block, to read it in context.
- **Error**: empty unless the file could not be read or scored; the verdict is then `Error` and the reason appears here, without stopping the rest of the batch.

Current thresholds (in `src/detector_ia/main.py`): peak ≥ 58 % or mean ≥ 45 % is high risk; peak ≥ 45 % or mean ≥ 35 % is suspicious; similarity > 88 % is possible copying.

### Layout

```
detector-ia/
├── src/detector_ia/
│   ├── main.py          # CLI, thresholds and report generation
│   ├── extractores.py   # Readers for .ipynb, .pdf, .docx, .txt and .md
│   └── motores.py       # Neural model, structural fingerprint and similarity
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

### License

Distributed under the MIT license. See [LICENSE](LICENSE) for the full text.
