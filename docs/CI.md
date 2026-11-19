# Integración continua / Continuous integration

[Español](#español) · [English](#english)

---

## Español

`detector-ia` se puede ejecutar en una acción de GitHub o en cualquier CI para revisar las entregas de un repositorio (por ejemplo, un repo de classroom donde los alumnos suben sus trabajos). El código de salida y los informes están pensados para eso.

> Antes de automatizar nada, lee [Uso responsable](USO_RESPONSABLE.md). Un resultado alto es un motivo para revisar a mano, no para suspender ni sancionar. Pensado para **avisar al profesorado**, no para bloquear a un alumno.

### Códigos de salida

`--fail-on` decide cuándo el proceso termina con código 1. Sin la opción, el código es siempre 0 (salvo que falle la propia herramienta).

| Valor | Sale con 1 si hay… |
| --- | --- |
| `ninguno` / `none` (por defecto) | nunca |
| `error` | algún archivo que no se pudo leer o puntuar |
| `alto` / `high` | `Error`, `ALTO RIESGO IA` o `REVISAR COPIA ENTRE ALUMNOS` |
| `sospechoso` / `suspicious` | lo anterior o `Sospechoso (Revisar)` |

Los informes (`--html`, `--markdown`, el CSV) se escriben **antes** de devolver el código, así que se generan aunque el paso falle.

### Ejemplo con GitHub Actions

```yaml
name: Revisión de entregas
on:
  pull_request:
    paths: ["entregas/**"]

jobs:
  revisar:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - run: pip install detector-ia          # sin modelo neuronal: rápido y sin descargas

      - name: Analizar
        id: analisis
        continue-on-error: true               # el informe debe subirse aunque haya avisos
        run: >
          detector-ia -c entregas --sin-modelo --base enunciado
          --salida informe/reporte.csv --html informe/informe.html
          --markdown informe/informe.md --fail-on alto

      - name: Resumen en la página de la ejecución
        if: always()
        run: cat informe/informe.md >> "$GITHUB_STEP_SUMMARY"

      - uses: actions/upload-artifact@v5
        if: always()
        with:
          name: informe-entregas
          path: informe/
          retention-days: 14

      - name: Marcar el paso si hay casos que revisar
        if: steps.analisis.outcome == 'failure'
        run: echo "::warning::Hay entregas que conviene revisar a mano. Descarga el informe."
```

Consejos:

- Los informes contienen trabajos reales. Un artefacto de un repositorio público lo ve cualquiera: usa un repositorio **privado** y un plazo de retención corto.
- `--sin-modelo` evita descargar ~500 MB en cada ejecución. Si quieres el modelo neuronal, cachea `cache_modelo/` con `actions/cache`.
- `--json` escribe el resultado por la salida estándar y el progreso por la de errores, por si prefieres procesarlo con `jq`: `detector-ia -c entregas --sin-modelo --json | jq '.resultados[] | select(.Veredicto != "Normal")'`.
- Si solo te interesa el plagio, usa `--fail-on alto` y filtra por el veredicto `REVISAR COPIA ENTRE ALUMNOS` en el JSON.

---

## English

`detector-ia` can run in a GitHub Action or any CI to review the submissions in a repository (for example a classroom repo where students push their work). The exit code and the reports are designed for that.

> Before automating anything, read [Responsible use](USO_RESPONSABLE.md). A high result is a reason to review by hand, not to fail or sanction anyone. It is meant to **alert the teaching staff**, not to block a student.

### Exit codes

`--fail-on` decides when the process exits with code 1. Without the option the code is always 0 (unless the tool itself fails).

| Value | Exits with 1 when there is… |
| --- | --- |
| `ninguno` / `none` (default) | never |
| `error` | any file that could not be read or scored |
| `alto` / `high` | `Error`, `ALTO RIESGO IA` or `REVISAR COPIA ENTRE ALUMNOS` |
| `sospechoso` / `suspicious` | the above or `Sospechoso (Revisar)` |

The reports (`--html`, `--markdown`, the CSV) are written **before** the exit code is returned, so they exist even when the step fails.

### GitHub Actions example

```yaml
name: Submission review
on:
  pull_request:
    paths: ["entregas/**"]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v6
        with:
          python-version: "3.13"
      - run: pip install detector-ia          # no neural model: fast, no downloads

      - name: Analyse
        id: analysis
        continue-on-error: true               # the report must be uploaded even with notices
        run: >
          detector-ia -c entregas --sin-modelo --base enunciado
          --salida informe/reporte.csv --html informe/informe.html
          --markdown informe/informe.md --fail-on alto

      - name: Summary on the run page
        if: always()
        run: cat informe/informe.md >> "$GITHUB_STEP_SUMMARY"

      - uses: actions/upload-artifact@v5
        if: always()
        with:
          name: submission-report
          path: informe/
          retention-days: 14

      - name: Flag the step when there are cases to review
        if: steps.analysis.outcome == 'failure'
        run: echo "::warning::Some submissions deserve a manual review. Download the report."
```

Tips:

- The reports contain real student work. An artifact of a public repository is visible to anyone: use a **private** repository and a short retention period.
- `--sin-modelo` avoids downloading ~500 MB on every run. If you want the neural model, cache `cache_modelo/` with `actions/cache`.
- `--json` writes the result to stdout and progress to stderr, in case you prefer processing it with `jq`: `detector-ia -c entregas --sin-modelo --json | jq '.resultados[] | select(.Veredicto != "Normal")'`.
- If you only care about plagiarism, use `--fail-on alto` and filter on the `REVISAR COPIA ENTRE ALUMNOS` verdict in the JSON.
