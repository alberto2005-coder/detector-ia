# Uso / Usage

[Español](#español) · [English](#english)

---

## Español

### Preparar las entregas

Crea una carpeta (por defecto `revision_ia/`) y copia dentro los archivos a analizar. Se admiten:

| Extensión | Qué se extrae |
| --- | --- |
| `.ipynb` | El texto que va después de "Respuestas:" en las celdas Markdown, los comentarios `#` y el código |
| `.pdf` | El texto de todas las páginas |
| `.docx` | Los párrafos, sin encabezados ni pies de página |
| `.txt`, `.md` | El contenido completo |

Los archivos con menos de 120 caracteres de texto útil se marcan como `Poco texto` y no se puntúan.

### Comando

```bash
uv run detector-ia [opciones]
```

| Opción | Por defecto | Descripción |
| --- | --- | --- |
| `-c`, `--carpeta` | `revision_ia` | Carpeta con las entregas |
| `-s`, `--salida` | `reporte_profesional_ia.csv` | Ruta del reporte; se crean las carpetas intermedias |
| `-m`, `--modelo` | RoBERTa de detección de IA | Modelo de Hugging Face alternativo |
| `-h`, `--help` | — | Ayuda |

Sin `uv`, con el entorno virtual activado:

```bash
python -m detector_ia -c revision_ia -s reporte.csv
```

### Salida por consola

```text
Cargando motor híbrido (Neuronal + Huella Estructural Español + Anti-Plagio)...
Analizando 4 entregas (Jupyter, PDF, Word, Markdown, TXT)...
✔ [.MD] ensayo.md -> IA Pico: 88.41% | Similitud: 57.43% (ALTO RIESGO IA)
```

### El reporte

CSV en UTF-8 con BOM y separador `;`, ordenado por pico de IA y luego por similitud, para abrirlo directamente en Excel en español.

| Columna | Significado |
| --- | --- |
| `Archivo` | Nombre del fichero |
| `Formato` | Extensión en mayúsculas |
| `IA_Media (%)` | Media de la puntuación de todos los bloques |
| `IA_Pico_Max (%)` | Mejor bloque, el más parecido a texto de IA |
| `Similitud_Companero (%)` | Entrega más parecida del grupo |
| `Coincide_Con` | Nombre de esa entrega si la similitud supera el 75 % |
| `Veredicto` | Categoría final |
| `Fragmento_Sospechoso` | El bloque con mayor puntuación, para leerlo en contexto |

### Umbrales y veredictos

| Veredicto | Condición |
| --- | --- |
| `ALTO RIESGO IA` | Pico ≥ 58 % o media ≥ 45 % |
| `REVISAR COPIA ENTRE ALUMNOS` | Similitud > 88 % |
| `Sospechoso (Revisar)` | Pico ≥ 45 % o media ≥ 35 % |
| `Normal` | Todo lo demás |
| `Poco texto` | Menos de 120 caracteres útiles |

Los valores están como constantes al principio de `src/detector_ia/main.py`. El mismo trabajo entregado en dos formatos (por ejemplo `.pdf` y `.txt`) no se cuenta como copia entre alumnos.

### Solución de problemas

**Tarda mucho la primera vez.** Descarga el modelo (~500 MB) en `cache_modelo/`. Las siguientes ejecuciones son rápidas y funcionan sin conexión.

**Se guarda el modelo en otro sitio.** La herramienta define `HF_HOME=./cache_modelo` solo si no está ya definido; exporta `HF_HOME` si quieres otro caché.

**La consola muestra basura en lugar de acentos.** El programa fuerza UTF-8 en su salida; si aun así pasa, ejecuta `chcp 65001` en Windows o redirige a un archivo.

**Un PDF sale con poco texto.** Suele ser un PDF escaneado, sin capa de texto. Habría que pasarlo por OCR antes.

**Los porcentajes no te cuadran.** El detector es heurístico y está calibrado para español académico. Ajusta los umbrales o los pesos en `motores.py` si tu caso es distinto.

---

## English

### Preparing the submissions

Create a folder (default `revision_ia/`) and copy the files to analyse into it. Supported formats:

| Extension | What is extracted |
| --- | --- |
| `.ipynb` | Text after "Respuestas:" in markdown cells, `#` comments and code |
| `.pdf` | Text from every page |
| `.docx` | Paragraphs, without headers or footers |
| `.txt`, `.md` | The whole file |

Files with fewer than 120 characters of usable text are reported as `Poco texto` and not scored.

### Command

```bash
uv run detector-ia [options]
```

| Option | Default | Description |
| --- | --- | --- |
| `-c`, `--carpeta` | `revision_ia` | Folder with the submissions |
| `-s`, `--salida` | `reporte_profesional_ia.csv` | Report path; parent folders are created |
| `-m`, `--modelo` | AI-detection RoBERTa | Alternative Hugging Face model |
| `-h`, `--help` | — | Help |

Without `uv`, with the virtual environment active:

```bash
python -m detector_ia -c revision_ia -s reporte.csv
```

### The report

CSV in UTF-8 with BOM and `;` separator, sorted by AI peak and then by similarity, so it opens directly in Spanish-locale Excel.

| Column | Meaning |
| --- | --- |
| `Archivo` | File name |
| `Formato` | Uppercase extension |
| `IA_Media (%)` | Mean score across blocks |
| `IA_Pico_Max (%)` | Highest block, the most AI-like passage |
| `Similitud_Companero (%)` | Most similar submission in the batch |
| `Coincide_Con` | That submission's name when similarity is above 75 % |
| `Veredicto` | Final category |
| `Fragmento_Sospechoso` | The highest-scoring block, for reading in context |

### Thresholds and verdicts

| Verdict | Condition |
| --- | --- |
| `ALTO RIESGO IA` | Peak ≥ 58 % or mean ≥ 45 % |
| `REVISAR COPIA ENTRE ALUMNOS` | Similarity > 88 % |
| `Sospechoso (Revisar)` | Peak ≥ 45 % or mean ≥ 35 % |
| `Normal` | Everything else |
| `Poco texto` | Fewer than 120 usable characters |

The values are constants at the top of `src/detector_ia/main.py`. The same assignment submitted in two formats (say `.pdf` and `.txt`) is not counted as student-to-student copying.

### Troubleshooting

**The first run is slow.** It downloads the model (~500 MB) into `cache_modelo/`. Later runs are fast and work offline.

**The model is cached somewhere else.** The tool sets `HF_HOME=./cache_modelo` only when it is not already defined; export `HF_HOME` if you prefer another cache.

**The console prints garbage instead of accents.** The program forces UTF-8 on its output; if it still happens, run `chcp 65001` on Windows or redirect to a file.

**A PDF yields very little text.** It is probably a scanned PDF with no text layer. Run it through OCR first.

**The percentages look off.** The detector is a heuristic calibrated for academic Spanish. Tune the thresholds or the weights in `motores.py` for your own case.
