# Uso y formatos / Usage and formats

[Español](#español) · [English](#english)

Las opciones del comando, las columnas del reporte y los umbrales están en la [guía completa](../README.md); aquí solo van los detalles que no aparecen allí.
Command options, report columns and thresholds live in the [full guide](../README.md); this page only covers details not covered there.

---

## Español

### Preparar las entregas

Crea una carpeta (por defecto `revision_ia/`) y copia dentro los archivos a analizar. Si solo quieres revisar uno, pasa su ruta directamente: `-c revision_ia/entrega.pdf`.

| Extensión | Qué se extrae |
| --- | --- |
| `.ipynb` | El texto que va después de "Respuestas:" en las celdas Markdown, los comentarios `#` y el código |
| `.pdf` | El texto de todas las páginas |
| `.docx` | Los párrafos, sin encabezados ni pies de página |
| `.txt`, `.md` | El contenido completo |

Los archivos con menos de 120 caracteres de texto útil se marcan como `Poco texto` y no se puntúan.

En los cuadernos la similitud se calcula sobre el código (o sobre su texto, si el cuaderno no tiene código); en el resto de formatos, sobre el texto redactado. Un mismo trabajo entregado en dos formatos (por ejemplo `.pdf` y `.txt`) no se cuenta como copia entre alumnos.

### Salida por consola

```text
Cargando motor híbrido (Neuronal + Huella Estructural Español + Anti-Plagio)...
Analizando 4 entregas (Jupyter, PDF, Word, Markdown, TXT)...
✔ [.MD] ensayo.md -> IA Pico: 88.41% | Similitud: 57.43% (ALTO RIESGO IA)
```

### Informes y plantilla base

- `--html informe.html` genera una página autocontenida con el resumen, el detalle por entrega y los pasajes copiados. Ábrela con el navegador, sin conexión. Contiene trabajos reales: no la subas a ningún sitio público.
- `--markdown informe.md` genera lo mismo en texto, útil para pegarlo en una incidencia o en el resumen de una acción de GitHub.
- Si todos los alumnos parten de un enunciado o de un cuaderno con celdas ya escritas, pásalo con `--base enunciado.ipynb` (archivo o carpeta). Lo que coincida con él no cuenta como copia.
- Con `--traduccion` (necesita `pip install "detector-ia[semantica]"`) se avisa si una entrega parece traducción de otra escrita en otro idioma. Es solo un aviso.

### Solución de problemas

**Tarda mucho la primera vez.** Descarga el modelo (~500 MB) en `cache_modelo/`. Las siguientes ejecuciones son rápidas y funcionan sin conexión.

**El modelo se guarda en otro sitio.** La herramienta define `HF_HOME=./cache_modelo` solo si no está ya definido; exporta `HF_HOME` si quieres otro caché.

**La consola muestra basura en lugar de acentos.** El programa fuerza UTF-8 en su salida; si aun así pasa, ejecuta `chcp 65001` en Windows o redirige a un archivo.

**Un PDF sale con poco texto.** Suele ser un PDF escaneado, sin capa de texto. Habría que pasarlo por OCR antes.

**Los porcentajes no te cuadran.** El detector es heurístico y está calibrado para español académico. Ajusta los umbrales o los pesos en `src/detector_ia/main.py` y `src/detector_ia/motores.py`.

### Datos personales

`revision_ia/` y los reportes `reporte_*.csv` están en `.gitignore`. No los subas al repositorio ni los compartas fuera del ámbito docente.

---

## English

### Preparing the submissions

Create a folder (default `revision_ia/`) and copy the files to analyse into it. If you only want one, pass its path directly: `-c revision_ia/entrega.pdf`.

| Extension | What is extracted |
| --- | --- |
| `.ipynb` | Text after "Respuestas:" in markdown cells, `#` comments and code |
| `.pdf` | Text from every page |
| `.docx` | Paragraphs, without headers or footers |
| `.txt`, `.md` | The whole file |

Files with fewer than 120 characters of usable text are reported as `Poco texto` and not scored.

In notebooks similarity is computed over code (or over their text, when the notebook has no code); in every other format, over the written text. The same assignment submitted in two formats (say `.pdf` and `.txt`) is not counted as student-to-student copying.

### Console output

```text
Cargando motor híbrido (Neuronal + Huella Estructural Español + Anti-Plagio)...
Analizando 4 entregas (Jupyter, PDF, Word, Markdown, TXT)...
✔ [.MD] ensayo.md -> IA Pico: 88.41% | Similitud: 57.43% (ALTO RIESGO IA)
```

### Reports and base template

- `--html report.html` writes a self-contained page with the summary, the detail per submission and the copied passages. Open it in a browser, offline. It contains real work: do not upload it anywhere public.
- `--markdown report.md` writes the same as text, handy to paste into an issue or into a GitHub Actions summary.
- If every student starts from a brief or from a notebook with cells already written, pass it with `--base brief.ipynb` (file or folder). What matches it does not count as copying.
- With `--traduccion` (needs `pip install "detector-ia[semantica]"`) you get a notice when a submission looks like a translation of one written in another language. It is only a notice.

### Troubleshooting

**The first run is slow.** It downloads the model (~500 MB) into `cache_modelo/`. Later runs are fast and work offline.

**The model is cached somewhere else.** The tool sets `HF_HOME=./cache_modelo` only when it is not already defined; export `HF_HOME` if you prefer another cache.

**The console prints garbage instead of accents.** The program forces UTF-8 on its output; if it still happens, run `chcp 65001` on Windows or redirect to a file.

**A PDF yields very little text.** It is probably a scanned PDF with no text layer. Run it through OCR first.

**The percentages look off.** The detector is a heuristic calibrated for academic Spanish. Tune the thresholds or the weights in `src/detector_ia/main.py` and `src/detector_ia/motores.py`.

### Personal data

`revision_ia/` and the `reporte_*.csv` reports are listed in `.gitignore`. Do not push them to the repository or share them outside the classroom.
