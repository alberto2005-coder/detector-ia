# Detector IA

Herramienta de línea de comandos para **detectar indicios de texto generado por IA** y **posibles copias entre entregas** de alumnos, y generar un reporte CSV ordenado por riesgo.

Analiza cuadernos de Jupyter (`.ipynb`), PDF, Word (`.docx`), Markdown (`.md`) y texto plano (`.txt`) en una sola pasada.

> Es una ayuda para la revisión, **no una prueba**. Un porcentaje alto es un motivo para hablar con el alumno o revisar el trabajo a mano; nunca un veredicto automático.

## Documentación

Guías en español e inglés dentro de cada archivo:

- [Uso y formatos](docs/USAGE.md): qué se extrae de cada formato y solución de problemas.
- [Changelog](CHANGELOG.md): historial de cambios por versión.
- [Contribuir](CONTRIBUTING.md): entorno, estructura y convención de commits.
- [Índice de documentación](docs/README.md).

## Cómo funciona

Cada entrega se parte en bloques de ~1500 caracteres y cada bloque de más de 300 caracteres se puntúa combinando tres señales:

| Señal | Peso | Qué mide |
| --- | --- | --- |
| Huella estructural en español | 50 % | Guiones largos (—), listas `* **Concepto:**`, encabezados `### 1.`, conectores enciclopédicos (*por tanto*, *cabe destacar*, *en última instancia*) y ausencia de erratas/coloquialismos |
| Uniformidad estadística | 30 % | Baja variación en la longitud de las frases, típica de texto generado |
| Red neuronal | 20 % | [fakespot-ai/roberta-base-ai-text-detection-v1](https://huggingface.co/fakespot-ai/roberta-base-ai-text-detection-v1) |

Además se calcula la **similitud de coseno** (bolsa de palabras) entre todas las entregas: en los cuadernos se compara el código (o el texto, si el cuaderno no tiene código) y en el resto el texto redactado. Un mismo trabajo entregado en dos formatos (por ejemplo PDF y TXT) no se cuenta como copia.

## Instalación

Requiere Python 3.13 o superior y, si no tienes `uv`, puedes instalarlo desde [astral.sh/uv](https://astral.sh/uv).

```bash
git clone <URL-del-repositorio>
cd detector-ia
uv sync
```

La primera ejecución descarga el modelo (~500 MB) en `cache_modelo/`, que está fuera del control de versiones. Las siguientes arrancan sin conexión.

## Uso

Copia las entregas a analizar en `revision_ia/` y ejecuta:

```bash
uv run detector-ia
```

Eso lee `revision_ia/`, imprime el progreso y guarda `reporte_profesional_ia.csv`.

Con opciones:

```bash
uv run detector-ia --carpeta entregas --salida reportes/marzo.csv
uv run detector-ia --modelo fakespot-ai/roberta-base-ai-text-detection-v1
```

También funciona sin `uv`, con el entorno activado:

```bash
python -m detector_ia --carpeta revision_ia
```

### Opciones

| Opción | Por defecto | Descripción |
| --- | --- | --- |
| `-c`, `--carpeta` | `revision_ia` | Carpeta con las entregas a analizar |
| `-s`, `--salida` | `reporte_profesional_ia.csv` | Ruta del reporte generado |
| `-m`, `--modelo` | RoBERTa de detección de IA | Modelo de Hugging Face a usar |

## Reporte

El CSV se guarda en UTF-8 con BOM y separador `;` para que abra directamente en Excel en español. Columnas:

- **Archivo / Formato**: nombre y extensión de la entrega.
- **IA_Media (%)**: media de la puntuación híbrida de los bloques evaluados.
- **IA_Pico_Max (%)**: bloque con la puntuación más alta, el que más se parece a texto de IA.
- **Similitud_Companero (%)** y **Coincide_Con**: entrega más parecida y su nombre si supera el 75 %.
- **Veredicto**: `ALTO RIESGO IA`, `REVISAR COPIA ENTRE ALUMNOS`, `Sospechoso (Revisar)`, `Normal` o `Poco texto`.
- **Fragmento_Sospechoso**: el bloque con mayor puntuación, para leerlo en contexto.

Umbrales actuales (en `src/detector_ia/main.py`): pico ≥ 58 % o media ≥ 45 % es alto riesgo; pico ≥ 45 % o media ≥ 35 % es sospechoso; similitud > 88 % es posible copia.

## Estructura

```
src/detector_ia/
├── main.py          # CLI, umbrales y generación del reporte
├── extractores.py   # Lectura de .ipynb, .pdf, .docx, .txt y .md
└── motores.py       # Modelo neuronal, huella estructural y similitud
docs/                # Índice y detalles de uso (bilingües)
revision_ia/         # Entregas de entrada (ignoradas por git)
```

## Privacidad

Las entregas de los alumnos y los reportes generados están excluidos de git (`.gitignore`), porque contienen trabajos reales y nombres de archivo. No los subas al repositorio ni compartas los CSV fuera del ámbito docente.

## Licencia

Distribuido bajo la licencia MIT. Consulta [LICENSE](LICENSE) para el texto completo.
