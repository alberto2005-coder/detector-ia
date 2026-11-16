# Seguridad / Security

[Español](#español) · [English](#english)

---

## Español

### Versiones con soporte

Solo la última versión publicada, actualmente `0.1.x`.

### Cómo reportar un problema

No abras un issue público con detalles de explotación. Usa la pestaña **Security → Report a vulnerability** del repositorio, que abre un aviso privado visible solo para los mantenedores.

Cuenta qué hace falta para reproducirlo, la versión de Python, el sistema operativo y el formato del archivo implicado. Si el fallo está en una dependencia (`torch`, `transformers`, `pypdf`, `python-docx`), indícalo y, si puedes, la versión afectada.

### Qué entra en el alcance

- Fallos al procesar un documento malicioso o corrupto (`.pdf`, `.docx`, `.ipynb`, `.txt`, `.md`) que provoquen ejecución de código, salida del directorio de trabajo o un cuelgue sin salida.
- Fugas de datos: que el contenido de una entrega acabe en el repositorio, en un log o en la descarga del modelo.
- Dependencias comprometidas o fijadas a versiones vulnerables en `uv.lock`.

### Riesgos conocidos que no son vulnerabilidades

- **Los detectores de IA no son fiables.** Un porcentaje alto o bajo no prueba nada: hay falsos positivos con textos formales o traducidos y falsos negativos con texto generado y luego editado.
- **La herramienta lee archivos no confiables.** Procesa los documentos en local con `pypdf`, `python-docx` y `json`; un archivo dañado puede lanzar una excepción, pero no se ejecuta su contenido.
- **Solo hay conexión de red para descargar el modelo** desde Hugging Face la primera vez, en `cache_modelo/`.

### Datos de alumnos

Los documentos de `revision_ia/` y los reportes `reporte_*.csv` son datos personales y están excluidos de git. No los adjuntes en un issue, en un aviso de seguridad ni en una captura: describe el problema con texto inventado que reproduzca el mismo caso.

---

## English

### Supported versions

Only the latest published release, currently `0.1.x`.

### Reporting a problem

Do not open a public issue with exploitation details. Use the repository's **Security → Report a vulnerability** tab, which opens a private advisory visible only to maintainers.

Describe the steps to reproduce it, your Python version, operating system and the file format involved. If the flaw is in a dependency (`torch`, `transformers`, `pypdf`, `python-docx`), say so and include the affected version if you know it.

### In scope

- Crashes or unsafe behaviour when processing a malicious or corrupt document (`.pdf`, `.docx`, `.ipynb`, `.txt`, `.md`) that lead to code execution, escaping the working directory, or hanging without exit.
- Data leaks: submission content ending up in the repository, in a log, or in the model download.
- Compromised dependencies, or versions pinned to vulnerable releases in `uv.lock`.

### Known risks that are not vulnerabilities

- **AI detectors are unreliable.** A high or low score proves nothing: there are false positives on formal or translated writing, and false negatives on generated text that was later edited.
- **The tool reads untrusted files.** Documents are parsed locally with `pypdf`, `python-docx` and `json`; a damaged file can raise an exception, but its content is not executed.
- **The only network access is the first model download** from Hugging Face, into `cache_modelo/`.

### Student data

Files in `revision_ia/` and the `reporte_*.csv` reports are personal data and are excluded from git. Never attach them to an issue, a security advisory or a screenshot: describe the problem with made-up text that reproduces the same case.
