"""Informes: HTML autocontenido, Markdown y estructura del JSON.

Todo el texto de los alumnos se escapa antes de escribirlo en el HTML. El archivo no carga
nada de internet (ni fuentes, ni scripts, ni imágenes), así que se puede abrir sin conexión y
no envía los trabajos a ningún sitio.
"""

import html
from datetime import datetime

from detector_ia import confianza

VEREDICTO_CLASE = {
    "ALTO RIESGO IA": "alto",
    "REVISAR COPIA ENTRE ALUMNOS": "copia",
    "Sospechoso (Revisar)": "sosp",
    "Normal": "normal",
}

VEREDICTO_EN = {
    "ALTO RIESGO IA": "HIGH AI RISK",
    "REVISAR COPIA ENTRE ALUMNOS": "CHECK FOR COPYING",
    "Sospechoso (Revisar)": "Suspicious (review)",
    "Normal": "Normal",
    "Poco texto": "Too little text",
    "Error": "Error",
}

CONFIANZA_EN = {"Alta": "High", "Media": "Medium", "Baja": "Low"}

TEXTOS = {
    "es": {
        "titulo": "Informe del detector de IA",
        "meta": "{n} entregas · detector-ia {version} · generado el {fecha}",
        "modelo": "Modelo neuronal: {modelo}",
        "sin_modelo": "Sin modelo neuronal (solo señales estructurales)",
        "perplejidad": "Señal de perplejidad activada (experimental)",
        "aviso": "Aviso",
        "resumen": "Resumen",
        "buscar": "Buscar archivo…",
        "todos": "Todos los veredictos",
        "cols": ["Archivo", "Formato", "IA media", "IA pico", "Confianza", "Similitud",
                 "Coincide con", "Veredicto"],
        "detalle": "Detalle por entrega",
        "bloques": "Puntuación por bloque",
        "bloque": "Bloque",
        "senales": "Señales del bloque más alto",
        "huella": "Huella estructural",
        "uniformidad": "Uniformidad",
        "neuronal": "Red neuronal",
        "perplejidad_senal": "Perplejidad",
        "pico_texto": "Bloque con mayor puntuación",
        "leyenda": "Marcas que suben o bajan la puntuación (pasa el ratón para ver cuál es)",
        "marca_ia": "rasgo típico de IA",
        "marca_humana": "rasgo humano (coloquial o errata)",
        "avisos": "Avisos sobre este resultado",
        "coincidencias": "Pasajes coincidentes con {otro}",
        "sim_ng": "Similitud por n-gramas",
        "sim_cos": "Similitud por coseno",
        "traducida": "Posible traducción de {otro}: {pct}% de frases equivalentes",
        "pares": "Pares de entregas más parecidos",
        "par_cols": ["Entrega A", "Entrega B", "N-gramas", "Coseno"],
        "sin_pares": "No hay pares con parecido relevante.",
        "error": "No se pudo analizar",
        "uso_resp": (
            "Es una ayuda para la revisión, no una prueba. Antes de actuar, lee el trabajo "
            "y habla con el alumno."
        ),
        "en_a": "En este trabajo",
        "en_b": "En {otro}",
        "sin_texto": "Sin texto suficiente.",
        "tokens": "{n} tokens",
    },
    "en": {
        "titulo": "AI detector report",
        "meta": "{n} submissions · detector-ia {version} · generated on {fecha}",
        "modelo": "Neural model: {modelo}",
        "sin_modelo": "No neural model (structural signals only)",
        "perplejidad": "Perplexity signal enabled (experimental)",
        "aviso": "Notice",
        "resumen": "Summary",
        "buscar": "Search file…",
        "todos": "All verdicts",
        "cols": ["File", "Format", "AI mean", "AI peak", "Confidence", "Similarity",
                 "Matches", "Verdict"],
        "detalle": "Detail per submission",
        "bloques": "Score per block",
        "bloque": "Block",
        "senales": "Signals of the highest block",
        "huella": "Structural fingerprint",
        "uniformidad": "Uniformity",
        "neuronal": "Neural network",
        "perplejidad_senal": "Perplexity",
        "pico_texto": "Highest-scoring block",
        "leyenda": "Marks that raise or lower the score (hover to see which one)",
        "marca_ia": "typical AI trait",
        "marca_humana": "human trait (colloquial or typo)",
        "avisos": "Notices about this result",
        "coincidencias": "Passages shared with {otro}",
        "sim_ng": "N-gram similarity",
        "sim_cos": "Cosine similarity",
        "traducida": "Possible translation of {otro}: {pct}% of equivalent sentences",
        "pares": "Most similar pairs of submissions",
        "par_cols": ["Submission A", "Submission B", "N-grams", "Cosine"],
        "sin_pares": "No pairs with relevant similarity.",
        "error": "Could not be analysed",
        "uso_resp": (
            "This is a review aid, not evidence. Before acting, read the work and talk to "
            "the student."
        ),
        "en_a": "In this work",
        "en_b": "In {otro}",
        "sin_texto": "Not enough text.",
        "tokens": "{n} tokens",
    },
}

CSS = """
:root{--bg:#fff;--fg:#1d2330;--mut:#5b6475;--bd:#d9dde5;--card:#f6f7fa;--ac:#2457c5;
--alto:#b3261e;--copia:#8a3ffc;--sosp:#b26a00;--normal:#1b7a43;--otro:#5b6475;
--mia:#fde2e0;--mhum:#dcf3e4;--mcopia:#e8dcff}
@media(prefers-color-scheme:dark){:root{--bg:#14171f;--fg:#e6e9f0;--mut:#9aa3b5;--bd:#2c3242;
--card:#1c2030;--ac:#7aa2ff;--alto:#ff8a80;--copia:#c6a6ff;--sosp:#ffc266;--normal:#7fd6a0;
--mia:#5a2220;--mhum:#1d4a30;--mcopia:#3d2a66}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 18px 60px}
h1{font-size:26px;margin:0 0 4px}h2{font-size:19px;margin:34px 0 12px}
.meta{color:var(--mut);margin:0 0 16px}
.aviso{background:var(--card);border-left:4px solid var(--sosp);padding:12px 16px;
border-radius:6px;margin:14px 0}
.tarjetas{display:flex;gap:10px;flex-wrap:wrap}
.tarjeta{background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:10px 16px;
min-width:130px}.tarjeta b{display:block;font-size:24px}
.controles{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}
input,select{font:inherit;padding:6px 10px;border:1px solid var(--bd);border-radius:6px;
background:var(--bg);color:var(--fg)}
table{border-collapse:collapse;width:100%}th,td{padding:8px 10px;border-bottom:1px solid var(--bd);
text-align:left;vertical-align:top}th{cursor:pointer;user-select:none;white-space:nowrap;
background:var(--card)}td.n{text-align:right;font-variant-numeric:tabular-nums}
a{color:var(--ac)}
.v{display:inline-block;padding:2px 9px;border-radius:99px;font-size:13px;font-weight:600;
border:1px solid currentColor;white-space:nowrap}
.v-alto{color:var(--alto)}.v-copia{color:var(--copia)}.v-sosp{color:var(--sosp)}
.v-normal{color:var(--normal)}.v-otro{color:var(--otro)}
details{border:1px solid var(--bd);border-radius:8px;margin:10px 0;background:var(--bg)}
summary{cursor:pointer;padding:10px 14px;font-weight:600;display:flex;gap:10px;flex-wrap:wrap;
align-items:center}
.cuerpo{padding:4px 16px 16px}h3{font-size:15px;margin:18px 0 8px}
.barra{display:flex;align-items:center;gap:8px;margin:3px 0;font-size:13px}
.barra span.et{width:70px;color:var(--mut)}
.barra .pista{flex:1;height:10px;background:var(--card);border-radius:5px;overflow:hidden;
border:1px solid var(--bd)}.barra .rel{display:block;height:100%;background:var(--ac)}
.barra .rel.alto{background:var(--alto)}.barra .rel.sosp{background:var(--sosp)}
.texto{white-space:pre-wrap;background:var(--card);border:1px solid var(--bd);
border-radius:6px;padding:10px 12px;font-size:14px;overflow-wrap:anywhere}
mark{border-radius:3px;padding:0 2px;color:inherit}
.m-guion,.m-lista,.m-encabezado,.m-conector{background:var(--mia)}
.m-humana{background:var(--mhum)}.m-copia{background:var(--mcopia)}
.dos{display:grid;grid-template-columns:1fr 1fr;gap:10px}
@media(max-width:700px){.dos{grid-template-columns:1fr}}
.mut{color:var(--mut)}ul.av{margin:6px 0;padding-left:20px}
footer{margin-top:40px;color:var(--mut);font-size:13px}
@media print{details{break-inside:avoid}details>*{display:block}.controles{display:none}}
"""

JS = """
(function(){
var t=document.getElementById('tabla');if(!t)return;
var cuerpo=t.tBodies[0],filas=[].slice.call(cuerpo.rows);
var q=document.getElementById('q'),f=document.getElementById('f');
function filtrar(){var b=q.value.toLowerCase(),v=f.value;
filas.forEach(function(r){var ok=(!b||r.cells[0].textContent.toLowerCase().indexOf(b)>-1)
&&(!v||r.dataset.v===v);r.style.display=ok?'':'none';});}
q.addEventListener('input',filtrar);f.addEventListener('change',filtrar);
[].forEach.call(t.tHead.rows[0].cells,function(th,i){var asc=false;
th.addEventListener('click',function(){asc=!asc;
filas.sort(function(a,b){var x=a.cells[i].dataset.o||a.cells[i].textContent,
y=b.cells[i].dataset.o||b.cells[i].textContent,nx=parseFloat(x),ny=parseFloat(y);
var c=(!isNaN(nx)&&!isNaN(ny))?nx-ny:String(x).localeCompare(String(y));
return asc?c:-c;});filas.forEach(function(r){cuerpo.appendChild(r);});});});
})();
"""


def _e(valor):
    return html.escape(str(valor), quote=True)


def _clase_veredicto(veredicto):
    return VEREDICTO_CLASE.get(veredicto, "otro")


def _nombre_veredicto(veredicto, idioma):
    return VEREDICTO_EN.get(veredicto, veredicto) if idioma == "en" else veredicto


def _nombre_confianza(nivel, idioma):
    return CONFIANZA_EN.get(nivel, nivel) if idioma == "en" else nivel


def resaltar(texto, marcas, clase_prefijo="m-"):
    """Escapa `texto` y envuelve en <mark> los tramos de `marcas` (los solapados se omiten)."""
    partes = []
    posicion = 0
    for marca in sorted(marcas, key=lambda m: (m["inicio"], -m["fin"])):
        if marca["inicio"] < posicion:
            continue
        partes.append(_e(texto[posicion:marca["inicio"]]))
        partes.append(
            f'<mark class="{clase_prefijo}{_e(marca["tipo"])}" title="{_e(marca["etiqueta"])}">'
            f'{_e(texto[marca["inicio"]:marca["fin"]])}</mark>'
        )
        posicion = marca["fin"]
    partes.append(_e(texto[posicion:]))
    return "".join(partes)


def _barra(etiqueta, valor, clase=""):
    ancho = max(0.0, min(100.0, float(valor)))
    return (
        f'<div class="barra"><span class="et">{_e(etiqueta)}</span>'
        f'<span class="pista"><span class="rel {clase}" style="width:{ancho:.1f}%"></span></span>'
        f"<span>{ancho:.1f}</span></div>"
    )


def _clase_puntuacion(valor, pico_alto, pico_sosp):
    if valor >= pico_alto:
        return "alto"
    return "sosp" if valor >= pico_sosp else ""


def _envolver(indice, cabecera, cuerpo):
    contenido = "".join(cuerpo)
    return f'<details id="f-{indice}">{cabecera}<div class="cuerpo">{contenido}</div></details>'


def _detalle_html(indice, fila, detalle, t, idioma, umbrales):
    veredicto = fila["Veredicto"]
    cabecera = (
        f'<summary><span>{_e(fila["Archivo"])}</span>'
        f'<span class="v v-{_clase_veredicto(veredicto)}">'
        f"{_e(_nombre_veredicto(veredicto, idioma))}</span>"
        f'<span class="mut">{fila["IA_Pico_Max (%)"]} %</span></summary>'
    )
    cuerpo = []
    if fila.get("Error"):
        cuerpo.append(f'<p><b>{_e(t["error"])}:</b> {_e(fila["Error"])}</p>')
        return _envolver(indice, cabecera, cuerpo)

    evaluacion = detalle.get("evaluacion") if detalle else None
    if evaluacion is None or not evaluacion.bloques:
        cuerpo.append(f'<p class="mut">{_e(t["sin_texto"])}</p>')
    else:
        cuerpo.append(f'<h3>{_e(t["bloques"])}</h3>')
        for n, bloque in enumerate(evaluacion.bloques, 1):
            clase = _clase_puntuacion(bloque.puntuacion, umbrales[0], umbrales[1])
            cuerpo.append(_barra(f'{t["bloque"]} {n}', bloque.puntuacion, clase))

        pico = max(evaluacion.bloques, key=lambda b: b.puntuacion)
        cuerpo.append(f'<h3>{_e(t["senales"])}</h3>')
        cuerpo.append(_barra(t["huella"], pico.huella))
        cuerpo.append(_barra(t["uniformidad"], pico.uniformidad))
        if pico.neuronal is not None:
            cuerpo.append(_barra(t["neuronal"], pico.neuronal))
        if pico.perplejidad is not None:
            cuerpo.append(_barra(t["perplejidad_senal"], pico.perplejidad))

        cuerpo.append(f'<h3>{_e(t["pico_texto"])}</h3>')
        cuerpo.append(f'<p class="mut">{_e(t["leyenda"])}: '
                      f'<mark class="m-conector">{_e(t["marca_ia"])}</mark> '
                      f'<mark class="m-humana">{_e(t["marca_humana"])}</mark></p>')
        cuerpo.append(f'<div class="texto">{resaltar(pico.texto, pico.marcas)}</div>')

    avisos = detalle.get("avisos", []) if detalle else []
    if avisos:
        elementos = "".join(f"<li>{_e(confianza.mensaje(c, idioma))}</li>" for c in avisos)
        cuerpo.append(f'<h3>{_e(t["avisos"])}</h3><ul class="av">{elementos}</ul>')

    coincidencia = detalle.get("coincidencia") if detalle else None
    if coincidencia and coincidencia.get("fragmentos"):
        otro = coincidencia["companero"]
        cuerpo.append(f'<h3>{_e(t["coincidencias"].format(otro=otro))}</h3>')
        cuerpo.append(
            f'<p class="mut">{_e(t["sim_ng"])}: {coincidencia["ngramas"]} % · '
            f'{_e(t["sim_cos"])}: {coincidencia["coseno"]} %</p>'
        )
        for fragmento in coincidencia["fragmentos"]:
            cuerpo.append(
                '<div class="dos">'
                f'<div><div class="mut">{_e(t["en_a"])} · '
                f'{_e(t["tokens"].format(n=fragmento["tokens"]))}</div>'
                f'<div class="texto"><mark class="m-copia">'
                f'{_e(fragmento["texto_a"])}</mark></div></div>'
                f'<div><div class="mut">{_e(t["en_b"].format(otro=otro))}</div>'
                f'<div class="texto"><mark class="m-copia">'
                f'{_e(fragmento["texto_b"])}</mark></div></div>'
                "</div>"
            )

    traducida = detalle.get("traducida") if detalle else None
    if traducida:
        frase = t["traducida"].format(
            otro=traducida["companero"], pct=traducida["porcentaje"]
        )
        cuerpo.append(f"<p>{_e(frase)}</p>")
        for frase_a, frase_b, similitud in traducida["ejemplos"]:
            cuerpo.append(
                '<div class="dos">'
                f'<div class="texto">{_e(frase_a)}</div>'
                f'<div class="texto">{_e(frase_b)} '
                f'<span class="mut">({similitud:.2f})</span></div>'
                "</div>"
            )
    return _envolver(indice, cabecera, cuerpo)


def informe_html(resultados, detalles, resumen, pares, idioma="es", umbrales=(58, 45)):
    """Devuelve el informe como una página HTML completa y autocontenida."""
    t = TEXTOS.get(idioma, TEXTOS["es"])
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    if resumen.get("modelo"):
        modelo = t["modelo"].format(modelo=resumen["modelo"])
    else:
        modelo = t["sin_modelo"]
    if resumen.get("perplejidad"):
        modelo += " · " + t["perplejidad"]

    conteo = {}
    for fila in resultados:
        conteo[fila["Veredicto"]] = conteo.get(fila["Veredicto"], 0) + 1
    tarjetas = "".join(
        f'<div class="tarjeta"><b>{n}</b><span class="v v-{_clase_veredicto(v)}">'
        f"{_e(_nombre_veredicto(v, idioma))}</span></div>"
        for v, n in sorted(conteo.items(), key=lambda par: -par[1])
    )
    opciones = "".join(
        f'<option value="{_e(v)}">{_e(_nombre_veredicto(v, idioma))}</option>' for v in conteo
    )

    filas = []
    for indice, fila in enumerate(resultados):
        veredicto = fila["Veredicto"]
        nivel = fila.get("Confianza", "")
        filas.append(
            f'<tr data-v="{_e(veredicto)}">'
            f'<td><a href="#f-{indice}">{_e(fila["Archivo"])}</a></td>'
            f'<td>{_e(fila["Formato"])}</td>'
            f'<td class="n">{fila["IA_Media (%)"]}</td>'
            f'<td class="n">{fila["IA_Pico_Max (%)"]}</td>'
            f"<td>{_e(_nombre_confianza(nivel, idioma))}</td>"
            f'<td class="n">{fila["Similitud_Companero (%)"]}</td>'
            f'<td>{_e(fila["Coincide_Con"])}</td>'
            f'<td data-o="{_e(veredicto)}"><span class="v v-{_clase_veredicto(veredicto)}">'
            f"{_e(_nombre_veredicto(veredicto, idioma))}</span></td></tr>"
        )
    cabeceras = "".join(f"<th>{_e(c)}</th>" for c in t["cols"])

    detalle = "".join(
        _detalle_html(i, fila, detalles.get(fila["Archivo"]), t, idioma, umbrales)
        for i, fila in enumerate(resultados)
    )

    if pares:
        filas_pares = "".join(
            f"<tr><td>{_e(p['a'])}</td><td>{_e(p['b'])}</td>"
            f"<td class='n'>{p['ngramas']}</td><td class='n'>{p['coseno']}</td></tr>"
            for p in pares
        )
        bloque_pares = (
            f"<table><thead><tr>{''.join(f'<th>{_e(c)}</th>' for c in t['par_cols'])}</tr></thead>"
            f"<tbody>{filas_pares}</tbody></table>"
        )
    else:
        bloque_pares = f'<p class="mut">{_e(t["sin_pares"])}</p>'

    aviso = confianza.AVISO_SESGO[1 if idioma == "en" else 0]
    return f"""<!DOCTYPE html>
<html lang="{_e(idioma)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex">
<title>{_e(t["titulo"])}</title>
<style>{CSS}</style>
</head>
<body>
<main>
<h1>{_e(t["titulo"])}</h1>
<p class="meta">{_e(t["meta"].format(n=len(resultados), version=resumen["version"], fecha=fecha))}
· {_e(modelo)}</p>
<div class="aviso"><b>{_e(t["aviso"])}:</b> {_e(aviso)}</div>
<h2>{_e(t["resumen"])}</h2>
<div class="tarjetas">{tarjetas}</div>
<div class="controles">
<input id="q" type="search" placeholder="{_e(t["buscar"])}">
<select id="f"><option value="">{_e(t["todos"])}</option>{opciones}</select>
</div>
<table id="tabla"><thead><tr>{cabeceras}</tr></thead><tbody>{"".join(filas)}</tbody></table>
<h2>{_e(t["pares"])}</h2>
{bloque_pares}
<h2>{_e(t["detalle"])}</h2>
{detalle}
<footer>{_e(t["uso_resp"])}</footer>
</main>
<script>{JS}</script>
</body>
</html>
"""


def _md(texto):
    return " ".join(str(texto).split()).replace("|", "\\|")


def informe_markdown(resultados, detalles, resumen, pares, idioma="es"):
    """Informe en Markdown: tabla resumen y detalle de los casos que hay que revisar."""
    es = idioma != "en"
    lineas = [
        f"# {'Informe del detector de IA' if es else 'AI detector report'}",
        "",
        f"detector-ia {resumen['version']} · "
        f"{len(resultados)} {'entregas' if es else 'submissions'} · "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"> {confianza.AVISO_SESGO[0 if es else 1]}",
        "",
        "| " + " | ".join(
            ["Archivo", "Formato", "IA media", "IA pico", "Confianza", "Similitud",
             "Coincide con", "Veredicto"]
            if es else
            ["File", "Format", "AI mean", "AI peak", "Confidence", "Similarity", "Matches",
             "Verdict"]
        ) + " |",
        "|" + " --- |" * 8,
    ]
    for fila in resultados:
        lineas.append(
            "| " + " | ".join(
                [
                    _md(fila["Archivo"]), _md(fila["Formato"]), str(fila["IA_Media (%)"]),
                    str(fila["IA_Pico_Max (%)"]),
                    _md(_nombre_confianza(fila.get("Confianza", ""), idioma)),
                    str(fila["Similitud_Companero (%)"]), _md(fila["Coincide_Con"]),
                    _md(_nombre_veredicto(fila["Veredicto"], idioma)),
                ]
            ) + " |"
        )

    revisar = [f for f in resultados if f["Veredicto"] not in ("Normal", "Poco texto")]
    if revisar:
        lineas += ["", f"## {'Casos a revisar' if es else 'Cases to review'}"]
    for fila in revisar:
        veredicto = _md(_nombre_veredicto(fila["Veredicto"], idioma))
        lineas += ["", f"### {_md(fila['Archivo'])} — {veredicto}"]
        if fila.get("Error"):
            lineas.append(f"- Error: {_md(fila['Error'])}")
            continue
        lineas.append(
            f"- {'IA pico' if es else 'AI peak'}: {fila['IA_Pico_Max (%)']} % · "
            f"{'IA media' if es else 'AI mean'}: {fila['IA_Media (%)']} %"
        )
        detalle = detalles.get(fila["Archivo"], {})
        for codigo in detalle.get("avisos", []):
            aviso = _md(confianza.mensaje(codigo, idioma))
            lineas.append(f"- {'Aviso' if es else 'Notice'}: {aviso}")
        if fila["Fragmento_Sospechoso"]:
            lineas += ["", f"> {_md(fila['Fragmento_Sospechoso'])[:400]}"]
        coincidencia = detalle.get("coincidencia")
        if coincidencia and coincidencia.get("fragmentos"):
            lineas += ["", f"{'Pasajes coincidentes con' if es else 'Passages shared with'} "
                       f"**{_md(coincidencia['companero'])}**:"]
            for fragmento in coincidencia["fragmentos"]:
                lineas.append(f"- «{_md(fragmento['texto_a'])}»")
    if pares:
        lineas += ["", f"## {'Pares más parecidos' if es else 'Most similar pairs'}", "",
                   "| A | B | n-gramas | coseno |", "| --- | --- | --- | --- |"]
        lineas += [f"| {_md(p['a'])} | {_md(p['b'])} | {p['ngramas']} | {p['coseno']} |"
                   for p in pares]
    lineas += ["", f"*{TEXTOS['es' if es else 'en']['uso_resp']}*", ""]
    return "\n".join(lineas)


def detalle_json(detalle):
    """Versión serializable del detalle de una entrega, para `--json`."""
    if not detalle:
        return {}
    evaluacion = detalle.get("evaluacion")
    resultado = {
        "confianza": detalle.get("confianza"),
        "avisos": detalle.get("avisos", []),
        "bloques": [
            {
                "inicio": b.inicio,
                "fin": b.fin,
                "puntuacion": round(b.puntuacion, 2),
                "huella": b.huella,
                "uniformidad": b.uniformidad,
                "neuronal": None if b.neuronal is None else round(b.neuronal, 2),
                "perplejidad": b.perplejidad,
            }
            for b in (evaluacion.bloques if evaluacion else [])
        ],
        "coincidencia": detalle.get("coincidencia"),
        "traducida": detalle.get("traducida"),
    }
    return resultado
