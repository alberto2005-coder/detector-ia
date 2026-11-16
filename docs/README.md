# Detector IA — Documentación / Documentation

[Español](#español) · [English](#english)

---

## Español

Documentación del proyecto. El README principal está en la raíz del repositorio.

| Documento | Contenido |
| --- | --- |
| [USAGE.md](USAGE.md) | Opciones del comando, formato del reporte, umbrales y solución de problemas |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios por versión |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Cómo montar el entorno, estilo de código y convención de commits |

### Qué hace

Analiza una carpeta de entregas (cuadernos de Jupyter, PDF, Word, Markdown y texto plano) y genera un reporte CSV con dos señales por archivo:

- **Indicios de texto generado por IA**, en porcentaje.
- **Similitud con el resto de entregas**, para detectar copias.

### Instalación rápida

```bash
git clone <URL-del-repositorio>
cd detector-ia
uv sync
```

Requiere Python 3.13 o superior. La primera ejecución descarga el modelo (~500 MB) en `cache_modelo/`, que está fuera del control de versiones.

### Uso rápido

```bash
uv run detector-ia                          # lee revision_ia/ y escribe reporte_profesional_ia.csv
uv run detector-ia -c entregas -s marzo.csv # carpeta y reporte personalizados
uv run detector-ia --help                   # todas las opciones
```

### Método

Cada entrega se divide en bloques de unos 1500 caracteres y cada bloque se puntúa combinando tres señales:

| Señal | Peso | Qué mide |
| --- | --- | --- |
| Huella estructural en español | 50 % | Guiones largos (—), listas `* **Concepto:**`, encabezados `### 1.`, conectores enciclopédicos y ausencia de erratas o coloquialismos |
| Uniformidad estadística | 30 % | Variación de la longitud de las frases; el texto generado suele ser muy regular |
| Red neuronal | 20 % | Modelo RoBERTa de detección de texto de IA |

La similitud entre entregas se calcula con coseno sobre bolsa de palabras: en los cuadernos se compara el código y en el resto el texto redactado.

### Límites importantes

- Es una **herramienta de apoyo**, no una prueba. Un porcentaje alto justifica revisar el trabajo a mano o hablar con el alumno, nada más.
- Los detectores de IA dan **falsos positivos** con textos muy formales o traducidos, y falsos negativos con texto generado y luego editado.
- El detector neuronal está entrenado en inglés; su peso es bajo (20 %) precisamente por eso.
- Los umbrales son heurísticos y están pensados para español de secundaria o universidad. Ajustables en `src/detector_ia/main.py`.

### Privacidad

`revision_ia/` y los reportes `reporte_*.csv` están en `.gitignore`: contienen trabajos reales de alumnos y no deben subirse al repositorio ni compartirse fuera del ámbito docente.

---

## English

Project documentation. The main README lives at the repository root.

| Document | Contents |
| --- | --- |
| [USAGE.md](USAGE.md) | Command options, report format, thresholds and troubleshooting |
| [CHANGELOG.md](CHANGELOG.md) | Change history per version |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Environment setup, code style and commit convention |

### What it does

It scans a folder of student submissions (Jupyter notebooks, PDF, Word, Markdown and plain text) and produces a CSV report with two signals per file:

- **Likelihood of AI-generated text**, as a percentage.
- **Similarity against the other submissions**, to spot copying.

### Quick install

```bash
git clone <repository-URL>
cd detector-ia
uv sync
```

Requires Python 3.13 or newer. The first run downloads the model (~500 MB) into `cache_modelo/`, which is not tracked by git.

### Quick usage

```bash
uv run detector-ia                          # reads revision_ia/ and writes reporte_profesional_ia.csv
uv run detector-ia -c entregas -s marzo.csv # custom folder and report path
uv run detector-ia --help                   # every option
```

### How it scores

Each submission is split into blocks of about 1500 characters, and every block is scored by combining three signals:

| Signal | Weight | What it measures |
| --- | --- | --- |
| Spanish structural fingerprint | 50 % | Em dashes (—), `* **Term:**` lists, `### 1.` headings, encyclopedic connectors, absence of typos or colloquialisms |
| Statistical uniformity | 30 % | Sentence-length variation; generated text tends to be very regular |
| Neural network | 20 % | RoBERTa AI-text-detection model |

Similarity between submissions uses cosine over a bag of words: notebooks are compared by code, everything else by written text.

### Important limits

- This is a **review aid, not evidence**. A high score only justifies reading the work by hand or talking to the student.
- AI detectors produce **false positives** on very formal or translated writing, and false negatives on generated text that was later edited.
- The neural detector is trained on English, which is exactly why its weight is low (20 %).
- Thresholds are heuristics tuned for Spanish high-school or university writing. They live in `src/detector_ia/main.py`.

### Privacy

`revision_ia/` and the `reporte_*.csv` reports are listed in `.gitignore`: they hold real student work and must not be pushed to the repository or shared outside the classroom.
