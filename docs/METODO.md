# Método y calibración / Method and calibration

[Español](#español) · [English](#english)

Los pesos y los umbrales exactos están en el README y en `src/detector_ia/motores.py` y `main.py`. Este documento explica **de dónde salen** y **cómo comprobarlos**.

---

## Español

### Por qué esos pesos (50/30/20)

- **Huella estructural (50 %)**: es la señal que mejor funciona en español de secundaria y universidad. Los patrones que mide —guiones largos, listas con negrita, encabezados numerados, conectores enciclopédicos— casi no aparecen en un trabajo escrito a mano, y su ausencia de erratas lo refuerza. Al no depender de un modelo entrenado en inglés, es la base del cálculo.
- **Uniformidad (30 %)**: el texto generado tiende a frases de longitud parecida. Como señal sola es débil (un alumno puede escribir de forma regular), pero descarta textos caóticos y suma cuando coincide con la huella.
- **Red neuronal (20 %)**: el modelo disponible está entrenado en inglés, así que en español aporta poco y a veces estorba. Se mantiene con peso bajo porque detecta texto traducido o generado en inglés y luego pasado al español.

El orden de magnitud importa más que el decimal: si cambias un peso, cambia también el significado de los umbrales.

### De dónde salen los umbrales

Están puestos a partir de la observación de tres grupos de textos: trabajos escritos a mano en clase, textos generados sin editar y textos generados y luego reescritos. El criterio fue que un trabajo humano no llegara a 45 de media, y que un texto generado sin tocar superara 58 de pico con holgura.

Son heurísticos y **no** están validados con un corpus grande y representativo. Por eso el corte de "copia" es deliberadamente alto (60 % de n-gramas compartidos o 88 % de coseno): solo marca casos de texto casi idéntico.

### Cómo comprobar o recalibrar

Hay un corpus etiquetado de ejemplo en `evaluacion/`:

```bash
uv run python evaluacion/evaluar.py              # con modelo neuronal
uv run python evaluacion/evaluar.py --sin-modelo # solo señales estructurales
uv run python evaluacion/evaluar.py --sin-modelo --perplejidad  # con la señal experimental
```

Ese corpus tiene **42 textos sintéticos** en siete categorías: IA sin editar, humano coloquial, humano formal, IA retocada a mano, IA pedida «como un estudiante», humano traducido con un traductor automático y texto mixto (humano con una conclusión pegada de una IA). Los escribió una persona con ayuda de un modelo, no son trabajos reales: sirve para detectar regresiones cuando tocas pesos o umbrales y para ver **en qué casos falla cada señal**, no para afirmar que el detector acierta un porcentaje concreto. Para calibrar de verdad hace falta un conjunto mucho mayor, con trabajos reales de varias materias, etiquetado por quien conoce los textos, y sin datos personales.

El script imprime la puntuación de cada texto, un resumen por categoría, un barrido de umbrales de 30 a 80 y, con `--json`, todo en un formato que se puede guardar y comparar entre versiones. Los textos mixtos no entran en precisión ni recall porque no tienen una respuesta binaria correcta.

#### Qué midió la 1.1.0 (solo señales estructurales)

Resultado de `evaluar.py --sin-modelo` con el umbral de pico 45. El modelo neuronal y la perplejidad **no se midieron** (requieren descargar modelos); ejecútalos tú con el mismo script.

| Categoría | Etiqueta | Textos | Pico medio | Marcados |
| --- | --- | --- | --- | --- |
| IA sin editar | ia | 6 | 53,3 | 5 de 6 |
| IA retocada a mano | ia | 8 | 28,7 | 0 de 8 |
| IA «como un estudiante» | ia | 6 | 25,4 | 0 de 6 |
| Humano coloquial | humano | 6 | 18,8 | 0 de 6 |
| Humano formal | humano | 8 | 27,6 | 0 de 8 |
| Humano traducido | humano | 4 | 25,9 | 0 de 4 |
| Mixto | mixto | 4 | 47,8 | 2 de 4 |

Lectura: con el umbral 45 no hay falsos positivos, pero solo se detectan 5 de las 20 muestras de IA (recall 0,25), todas sin editar. La IA retocada a mano o escrita «como un estudiante» se solapa con el humano formal (picos de 20 a 39 la IA retocada o «de estudiante», de 22 a 36 el humano formal), así que **ningún umbral de pico separa ambos grupos con las señales estructurales**: bajarlo para cazar más IA crearía falsos positivos con trabajos humanos formales o traducidos. Por eso los umbrales no se han tocado. Las señales que sí pueden aportar en esos casos son el modelo neuronal y la perplejidad, y falta medirlas.

### Plagio por n-gramas

La similitud de coseno entre bolsas de palabras da valores muy altos a dos trabajos que solo tratan el mismo tema. Desde la 1.1.0 la copia se mide con el orden de las palabras:

1. Cada entrega se parte en n-gramas de 5 palabras (8 *tokens* en código), sin acentos ni mayúsculas.
2. De ellos se eligen las huellas con *winnowing* (ventana de 4): en cada ventana se guarda el hash más pequeño. Así la selección es estable aunque se inserten o quiten palabras.
3. La similitud es el porcentaje de huellas de la entrega **más pequeña** que aparecen en la otra. Detecta, por tanto, que un trabajo corto esté contenido en uno largo.
4. En código, los nombres de variables, los números y las cadenas se sustituyen por marcadores (`ID`, `NUM`, `STR`) antes de partir en n-gramas, de modo que renombrar variables no esconde la copia.
5. Con `--base` se restan los n-gramas del enunciado o la plantilla, tanto de las huellas como de la bolsa de palabras del coseno.

Se marca como posible copia con **≥ 60 %** de n-gramas o **> 88 %** de coseno, y se muestra la coincidencia a partir del 40 % de n-gramas (o 75 % de coseno). Son umbrales razonados con textos de ejemplo, no calibrados con un corpus real. Limitaciones conocidas: dos trabajos que citan el mismo texto largo parecerán copiados, y el código muy corto o muy estándar (por ejemplo, cargar un CSV) comparte n-gramas sin que haya copia; para eso sirve `--base`.

### Señal de perplejidad (experimental)

`--perplejidad` añade una cuarta señal inspirada en [Binoculars](https://arxiv.org/abs/2401.12070) (Hans et al., 2024): la perplejidad del texto bajo un modelo de lenguaje dividida entre la entropía cruzada entre dos modelos emparentados. Un valor bajo indica texto muy predecible. La pareja por defecto es `Qwen/Qwen2.5-0.5B` y `Qwen/Qwen2.5-0.5B-Instruct`, pequeña y multilingüe. Con la señal activada los pesos pasan a 40 % huella, 20 % uniformidad, 15 % red neuronal y 25 % perplejidad.

Es **experimental**: el cálculo está probado con datos sintéticos, pero los límites que convierten la puntuación en un porcentaje (`BINO_ALTO` = 0,75 y `BINO_BAJO` = 1,00 en `perplejidad.py`) son una elección razonable, no un valor calibrado para español con esa pareja de modelos. Los autores del método advierten además de que funciona peor fuera del inglés. Antes de usarla para algo, ejecuta `evaluar.py --perplejidad` y mira si separa tus categorías.

### Confianza y avisos

La columna `Confianza` (`Alta`, `Media`, `Baja`) **no es la probabilidad de acertar**: indica cuánta base tiene el análisis. Baja si se puntuó menos de 2 bloques o si un resultado alto viene solo de la uniformidad de las frases (huella < 20 y ningún modelo lo apoya); Media si hay bloques muy dispares (≥ 35 puntos de diferencia, posible texto mixto) o más de un 25 % del texto entre comillas; Alta en el resto.

### Sesgo con quien no escribe en su lengua

Los detectores fallan más con textos de personas que escriben en una lengua que no es la suya: un estudio de Stanford (Liang et al., 2023) encontró que los detectores marcaban como IA más del 61 % de los ensayos TOEFL de hablantes no nativos de inglés, y un estudio con textos en español concluyó que ninguna herramienta evaluada era fiable con textos híbridos. Las razones son parecidas a las de los textos traducidos: vocabulario más acotado, frases más regulares y menos variación. Este detector no está exento. Por eso cada informe lleva un aviso visible y la confianza baja cuando el resultado descansa solo en la uniformidad.

### Qué acierta y qué no

**Suele acertar** con texto generado sin editar, con salida de LLM pegada tal cual y con informes con estructura muy marcada.

**Falla** en estos casos conocidos:

- **Falsos positivos**: textos traducidos con traductor automático, trabajos muy formales de cursos superiores, apuntes de alguien que escribe con cuidado y sin erratas, y fragmentos de normativa o de libros de texto citados dentro del trabajo.
- **Falsos negativos**: texto generado y luego reescrito a mano, texto generado con instrucciones de "escribe como un estudiante", y textos cortos (por debajo de 300 caracteres por bloque no se puntúa nada).
- **Sesgo de formato**: un `.pdf` exportado con márgenes raros puede perder saltos de línea y alterar la uniformidad medida.

### Qué no puede afirmar

El reporte no dice "este alumno ha usado IA". Dice "este bloque se parece a texto generado", con un margen de error que no se puede cuantificar con los datos disponibles. Cualquier uso que convierta ese número en una acusación o en una nota está fuera de lo que la herramienta puede sostener. Ver [uso responsable](USO_RESPONSABLE.md).

### Licencias

El código de este repositorio es MIT. El modelo que descarga es un proyecto aparte: `fakespot-ai/roberta-base-ai-text-detection-v1` se distribuye bajo **Apache-2.0**, igual que su modelo base `FacebookAI/roberta-base`. Esa licencia no la concede este repositorio: si redistribuyes el modelo o un derivado, cita su autoría y conserva su aviso.

---

## English

The exact weights and thresholds live in the README and in `src/detector_ia/motores.py` and `main.py`. This document explains **where they come from** and **how to check them**.

### Why these weights (50/30/20)

- **Structural fingerprint (50 %)**: the signal that works best on Spanish high-school and university writing. The patterns it measures — em dashes, bold-led lists, numbered headings, encyclopedic connectors — rarely appear in hand-written work, and the absence of typos reinforces it. Since it does not depend on a model trained on English, it carries the score.
- **Uniformity (30 %)**: generated text tends to have sentences of similar length. On its own it is weak (a student can write regularly), but it rules out chaotic texts and adds weight when it agrees with the fingerprint.
- **Neural network (20 %)**: the available model is trained on English, so in Spanish it adds little and sometimes misleads. It stays at a low weight because it catches text generated in English and then translated.

The order of magnitude matters more than the decimal: change a weight and you also change what the thresholds mean.

### Where the thresholds come from

They were set from three groups of texts: work written by hand in class, generated text with no edits, and generated text later rewritten. The rule was that human work should not reach a mean of 45, and untouched generated text should clearly exceed a peak of 58.

They are heuristics and are **not** validated against a large, representative corpus. That is why the "copying" cut-off is deliberately high (60 % shared n-grams or 88 % cosine): it only flags nearly identical text.

### How to check or recalibrate

There is a small labelled corpus in `evaluacion/`:

```bash
uv run python evaluacion/evaluar.py              # with the neural model
uv run python evaluacion/evaluar.py --sin-modelo # structural signals only
uv run python evaluacion/evaluar.py --sin-modelo --perplejidad  # with the experimental signal
```

That corpus holds **42 synthetic texts** in seven categories: unedited AI, colloquial human, formal human, AI edited by hand, AI prompted to "write like a student", human text run through a machine translator, and mixed text (human with an AI conclusion pasted in). They were written by a person with the help of a model, and are not real student work: they catch regressions when you touch weights or thresholds and show **where each signal fails**, they do not prove the detector is right a given share of the time. Real calibration needs a much larger set of real work from several subjects, labelled by someone who knows the texts, with no personal data.

The script prints each text's score, a per-category summary, a threshold sweep from 30 to 80 and, with `--json`, everything in a format you can save and compare between versions. Mixed texts are excluded from precision and recall because they have no correct binary answer.

#### What 1.1.0 measured (structural signals only)

Result of `evaluar.py --sin-modelo` at the peak threshold of 45. The neural model and the perplexity signal **were not measured** (they need model downloads); run them yourself with the same script.

| Category | Label | Texts | Mean peak | Flagged |
| --- | --- | --- | --- | --- |
| Unedited AI | ia | 6 | 53.3 | 5 of 6 |
| AI edited by hand | ia | 8 | 28.7 | 0 of 8 |
| AI "like a student" | ia | 6 | 25.4 | 0 of 6 |
| Colloquial human | humano | 6 | 18.8 | 0 of 6 |
| Formal human | humano | 8 | 27.6 | 0 of 8 |
| Translated human | humano | 4 | 25.9 | 0 of 4 |
| Mixed | mixto | 4 | 47.8 | 2 of 4 |

Reading: at threshold 45 there are no false positives, but only 5 of the 20 AI samples are caught (recall 0.25), all of them unedited. AI edited by hand or written "like a student" overlaps with formal human writing (peaks of 20 to 39 for edited or "student" AI, 22 to 36 for formal human), so **no peak threshold separates the two groups with the structural signals**: lowering it to catch more AI would create false positives on formal or translated human work. That is why the thresholds were not touched. The signals that could help in those cases are the neural model and perplexity, and they still need measuring.

### N-gram plagiarism

Cosine similarity between bags of words gives very high values to two pieces of work that merely cover the same topic. Since 1.1.0, copying is measured with word order:

1. Each submission is split into 5-word n-grams (8 tokens for code), without accents or capitals.
2. Fingerprints are chosen from them with *winnowing* (window of 4): the smallest hash in each window is kept. The selection stays stable when words are inserted or removed.
3. Similarity is the share of fingerprints of the **smaller** submission found in the other, so a short piece of work contained in a long one is detected.
4. In code, variable names, numbers and strings are replaced by markers (`ID`, `NUM`, `STR`) before splitting into n-grams, so renaming variables does not hide the copy.
5. With `--base`, the n-grams of the brief or template are subtracted, both from the fingerprints and from the bag of words used by the cosine.

A pair is flagged as possible copying at **≥ 60 %** n-grams or **> 88 %** cosine, and the match is shown from 40 % n-grams (or 75 % cosine). These thresholds were reasoned from example texts, not calibrated on a real corpus. Known limits: two pieces of work quoting the same long text will look copied, and very short or very standard code (such as loading a CSV) shares n-grams without any copying; `--base` is there for that.

### Perplexity signal (experimental)

`--perplejidad` adds a fourth signal inspired by [Binoculars](https://arxiv.org/abs/2401.12070) (Hans et al., 2024): the perplexity of the text under one language model divided by the cross-entropy between two related models. A low value means very predictable text. The default pair is `Qwen/Qwen2.5-0.5B` and `Qwen/Qwen2.5-0.5B-Instruct`, small and multilingual. With the signal on, the weights become 40 % fingerprint, 20 % uniformity, 15 % neural network and 25 % perplexity.

It is **experimental**: the calculation is tested with synthetic data, but the limits that turn the score into a percentage (`BINO_ALTO` = 0.75 and `BINO_BAJO` = 1.00 in `perplejidad.py`) are a reasonable choice, not a value calibrated for Spanish with that model pair. The method's authors also warn that it works worse outside English. Before relying on it, run `evaluar.py --perplejidad` and see whether it separates your categories.

### Confidence and notices

The `Confianza` column (`Alta`, `Media`, `Baja`) is **not the probability of being right**: it says how much basis the analysis has. Low when fewer than 2 blocks were scored or when a high result comes only from sentence uniformity (fingerprint < 20 and no model backs it); Medium when blocks disagree sharply (≥ 35 points apart, possibly mixed text) or more than 25 % of the text is quoted; High otherwise.

### Bias against people not writing in their first language

Detectors fail more often on text by people writing in a language that is not their first: a Stanford study (Liang et al., 2023) found detectors flagged more than 61 % of TOEFL essays by non-native English speakers as AI, and a study on Spanish texts concluded that none of the tools it evaluated was reliable with hybrid texts. The reasons resemble those for translated text: a narrower vocabulary, more regular sentences and less variation. This detector is not exempt. That is why every report carries a visible notice and why confidence drops when a result rests only on uniformity.

### What it gets right and wrong

**Usually right** on generated text with no edits, on LLM output pasted as-is, and on reports with very marked structure.

**It fails** in these known cases:

- **False positives**: machine-translated writing, very formal work from advanced courses, notes by someone who writes carefully with no typos, and quoted regulations or textbook passages inside the assignment.
- **False negatives**: generated text then rewritten by hand, text generated with "write like a student" instructions, and short texts (nothing is scored below 300 characters per block).
- **Format bias**: a `.pdf` exported with odd margins can lose line breaks and distort the uniformity measure.

### What it cannot claim

The report does not say "this student used AI". It says "this block looks like generated text", with an error margin that cannot be quantified with the available data. Any use that turns that number into an accusation or a grade is beyond what the tool can support. See [responsible use](USO_RESPONSABLE.md).

### Licences

The code in this repository is MIT. The model it downloads is a separate project: `fakespot-ai/roberta-base-ai-text-detection-v1` is distributed under **Apache-2.0**, as is its base model `FacebookAI/roberta-base`. That licence is not granted by this repository: if you redistribute the model or a derivative, credit its authors and keep their notice.

## Robustez frente a trucos (1.2.0)

Los benchmarks de robustez (RAID) muestran que los detectores se dejan engañar con ataques baratos. Antes de puntuar, la herramienta normaliza los espacios de ancho cero y los homoglifos (letras cirílicas o griegas dentro de palabras latinas) y lo avisa. Con las señales estructurales, en el corpus adversario (`evaluacion/generar_adversarios.py`, 24 textos derivados de los 6 de IA sin editar), la detección sin esta limpieza baja de 5/6 a 1–2/6 con invisibles y homoglifos, y con ella vuelve a 5/6. Las erratas y el cambio de orden de palabras casi no afectan a esas señales; no se ha medido su efecto sobre el modelo neuronal ni sobre la perplejidad (no hay acceso al modelo en el entorno de desarrollo). El corpus es sintético y pequeño: sirve para detectar regresiones, no para dar un porcentaje de acierto.

El «indicio de humanizador» busca frases torturadas (sinónimos que ningún autor escribiría) y es una señal débil; no detecta reescrituras limpias. Los minutos de edición de un Word son orientativos: un texto pegado desde otro editor también los muestra bajos.

---

## Robustness against tricks (1.2.0)

Robustness benchmarks (RAID) show that detectors are fooled by cheap attacks. Before scoring, the tool normalises zero-width spaces and homoglyphs (Cyrillic or Greek letters inside Latin words) and flags them. With the structural signals, on the adversarial corpus (`evaluacion/generar_adversarios.py`, 24 texts derived from the 6 unedited AI ones), detection without this cleaning drops from 5/6 to 1–2/6 for invisibles and homoglyphs, and with it returns to 5/6. Typos and word-order swaps barely affect those signals; their effect on the neural model and perplexity has not been measured (no model access in the development environment). The corpus is synthetic and small: it detects regressions, it does not give an accuracy percentage.

The "humaniser hint" looks for tortured phrases (synonyms no author would write) and is a weak signal; it does not detect clean rewrites. Word editing minutes are indicative: text pasted from another editor also shows low minutes.
