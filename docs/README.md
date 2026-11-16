# Detector IA — Documentación / Documentation

[Español](#español) · [English](#english)

---

## Español

Herramienta de línea de comandos que analiza una carpeta de entregas (Jupyter, PDF, Word, Markdown y TXT) y genera un CSV con el porcentaje de indicios de texto de IA y la similitud entre trabajos.

```bash
uv sync --extra modelo
uv run detector-ia
```

Requiere Python 3.13 o superior. El extra `modelo` añade `torch` y `transformers`; sin él se puede usar `--sin-modelo`. La primera ejecución descarga el modelo (~500 MB) en `cache_modelo/`.

| Documento | Contenido |
| --- | --- |
| [Guía completa](../README.md) | Qué hace, método con pesos, instalación, uso, opciones, reporte, umbrales, estructura y privacidad |
| [Uso y formatos](USAGE.md) | Qué se extrae de cada formato y solución de problemas |
| [Método y calibración](METODO.md) | De dónde salen los pesos y los umbrales, y cómo revisarlos |
| [Uso responsable](USO_RESPONSABLE.md) | Qué hacer con un caso marcado antes de actuar |
| [Changelog](../CHANGELOG.md) | Historial de cambios por versión |
| [Seguridad](../SECURITY.md) | Cómo reportar un problema y qué datos no compartir |
| [Contribuir](../CONTRIBUTING.md) | Entorno, estructura del código y convención de commits |

Aviso: es una ayuda a la revisión, no una prueba. Un porcentaje alto solo justifica leer el trabajo a mano.

---

## English

A command-line tool that scans a folder of submissions (Jupyter, PDF, Word, Markdown and TXT) and produces a CSV with the AI-text likelihood score and the similarity between files.

```bash
uv sync --extra modelo
uv run detector-ia
```

Requires Python 3.13 or newer. The `modelo` extra adds `torch` and `transformers`; without it you can use `--sin-modelo`. The first run downloads the model (~500 MB) into `cache_modelo/`.

| Document | Contents |
| --- | --- |
| [Full guide](../README.md) | What it does, method with weights, install, usage, options, report, thresholds, layout and privacy |
| [Usage and formats](USAGE.md) | What is extracted from each format and troubleshooting |
| [Method and calibration](METODO.md) | Where the weights and thresholds come from, and how to review them |
| [Responsible use](USO_RESPONSABLE.md) | What to do with a flagged case before acting |
| [Changelog](../CHANGELOG.md) | Change history per version |
| [Security](../SECURITY.md) | How to report an issue and which data never to share |
| [Contributing](../CONTRIBUTING.md) | Environment, code layout and commit convention |

Caveat: this is a review aid, not evidence. A high score only justifies reading the work by hand.
