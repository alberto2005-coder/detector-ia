import glob
import os
import pandas as pd
from detector_ia.extractores import procesar_archivo
from detector_ia.motores import AnalizadorIA


EXTENSIONES_VALIDAS = (".ipynb", ".pdf", ".docx", ".txt", ".md")

def main():
    carpeta = "revision_ia"
    archivos = [
        f for f in glob.glob(f"{carpeta}/*") 
        if f.lower().endswith(EXTENSIONES_VALIDAS)
    ]
    
    if not archivos:
        print(f"No se encontraron archivos compatibles en '{carpeta}/'.")
        return

    analizador = AnalizadorIA()
    print(f"Analizando {len(archivos)} entregas (Jupyter, PDF, Word, Markdown, TXT)...")

    entregas = []
    for ruta in archivos:
        texto, codigo = procesar_archivo(ruta)
        entregas.append({
            "nombre": os.path.basename(ruta),
            "tipo": os.path.splitext(ruta)[1].upper(),
            "texto": texto,
            "codigo": codigo
        })

    resultados = []
    for i, item in enumerate(entregas):
        if len(item["texto"]) < 120:
            resultados.append({
                "Archivo": item["nombre"],
                "Formato": item["tipo"],
                "IA_Media (%)": 0,
                "IA_Pico_Max (%)": 0,
                "Similitud_Companero (%)": 0,
                "Coincide_Con": "Ninguno",
                "Veredicto": "Poco texto",
                "Fragmento_Sospechoso": ""
            })
            continue

        media_ia, max_ia, fragmento = analizador.evaluar_texto(item["texto"])

        # Compara código si es .ipynb, o texto redactado si es .pdf/.docx/.txt/.md
        max_sim = 0.0
        companero = "Ninguno"
        base_comp = item["codigo"] if item["codigo"] else item["texto"]

        for j, otro in enumerate(entregas):
            if i == j:
                continue
            otro_comp = otro["codigo"] if otro["codigo"] else otro["texto"]
            sim = analizador.similitud_coseno(base_comp, otro_comp)
            if sim > max_sim:
                max_sim = sim
                companero = otro["nombre"]

        if max_ia >= 58 or media_ia >= 45:
            veredicto = "ALTO RIESGO IA"
        elif max_sim > 88:
            veredicto = "REVISAR COPIA ENTRE ALUMNOS"
        elif max_ia >= 45 or media_ia >= 35:
            veredicto = "Sospechoso (Revisar)"
        else:
            veredicto = "Normal"


        resultados.append({
            "Archivo": item["nombre"],
            "Formato": item["tipo"],
            "IA_Media (%)": media_ia,
            "IA_Pico_Max (%)": max_ia,
            "Similitud_Companero (%)": max_sim,
            "Coincide_Con": companero if max_sim > 75 else "Ninguno",
            "Veredicto": veredicto,
            "Fragmento_Sospechoso": fragmento
        })
        print(f"✔ [{item['tipo']}] {item['nombre']} -> IA Pico: {max_ia}% | Similitud: {max_sim}% ({veredicto})")

    df = pd.DataFrame(resultados)
    df = df.sort_values(by=["IA_Pico_Max (%)", "Similitud_Companero (%)"], ascending=False)
    df.to_csv("reporte_profesional_ia.csv", index=False, sep=";", encoding="utf-8-sig")
    print("\n¡Listo! Reporte guardado en 'reporte_profesional_ia.csv'.")

if __name__ == "__main__":
    main()
