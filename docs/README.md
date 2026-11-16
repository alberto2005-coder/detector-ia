# Detector IA — Documentación / Documentation

[Español](#español) · [English](#english)

---

## Español

Herramienta de línea de comandos que analiza una carpeta de entregas (Jupyter, PDF, Word, Markdown y TXT) y genera un CSV con el porcentaje de indicios de texto de IA y la similitud entre trabajos.

```bash
uv sync
uv run detector-ia
```

Requiere Python 3.13 o superior. La primera ejecución descarga el modelo (~500 MB) en `cache_modelo/`.

| Documento | Contenido |
| --- | --- |
| [Guía completa](../README.md) | Qué hace, método con pesos, instalación, uso, opciones, reporte, umbrales, estructura y privacidad |
| [Uso y formatos](USAGE.md) | Qué se extrae de cada formato y solución de problemas |
| [Changelog](CHANGELOG.md) | Historial de cambios por versión |
| [Contribuir](CONTRIBUTING.md) | Entorno, estructura del código y convención de commits |

Aviso: es una ayuda a la revisión, no una prueba. Un porcentaje alto solo justifica leer el trabajo a mano.

---

## English

A command-line tool that scans a folder of submissions (Jupyter, PDF, Word, Markdown and TXT) and produces a CSV with the AI-text likelihood score and the similarity between files.

```bash
uv sync
uv run detector-ia
```

Requires Python 3.13 or newer. The first run downloads the model (~500 MB) into `cache_modelo/`.

| Document | Contents |
| --- | --- |
| [Full guide](../README.md) | What it does, method with weights, install, usage, options, report, thresholds, layout and privacy |
| [Usage and formats](USAGE.md) | What is extracted from each format and troubleshooting |
| [Changelog](CHANGELOG.md) | Change history per version |
| [Contributing](CONTRIBUTING.md) | Environment, code layout and commit convention |

Caveat: this is a review aid, not evidence. A high score only justifies reading the work by hand.
