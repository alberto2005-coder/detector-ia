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

Son heurísticos y **no** están validados con un corpus grande y representativo. Por eso el corte de "copia" (88 % de similitud) es deliberadamente alto: solo marca casos de texto casi idéntico.

### Cómo comprobar o recalibrar

Hay un corpus etiquetado de ejemplo en `evaluacion/`:

```bash
uv run python evaluacion/evaluar.py              # con modelo neuronal
uv run python evaluacion/evaluar.py --sin-modelo # solo señales estructurales
```

Imprime la puntuación de cada texto y, para los umbrales 45 y 58, precisión, recall, exactitud y número de falsos positivos y negativos.

Ese corpus tiene **12 textos inventados**: sirve para detectar regresiones cuando tocas pesos o umbrales, no para afirmar que el detector acierta un porcentaje concreto. Para calibrar de verdad hace falta un conjunto mucho mayor, variado en registros y materias, etiquetado por quien conoce los textos, y sin datos personales.

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

They are heuristics and are **not** validated against a large, representative corpus. That is why the "copying" cut-off (88 % similarity) is deliberately high: it only flags nearly identical text.

### How to check or recalibrate

There is a small labelled corpus in `evaluacion/`:

```bash
uv run python evaluacion/evaluar.py              # with the neural model
uv run python evaluacion/evaluar.py --sin-modelo # structural signals only
```

It prints each text's score and, for the 45 and 58 thresholds, precision, recall, accuracy and the number of false positives and negatives.

That corpus holds **12 invented texts**: it catches regressions when you touch weights or thresholds, it does not prove the detector is right a given share of the time. Real calibration needs a much larger set, varied in registers and subjects, labelled by someone who knows the texts, with no personal data.

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
