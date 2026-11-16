"""Motores de detección: huella estructural, uniformidad, modelo neuronal y similitud."""

import math
import os
import re
from collections import Counter
from pathlib import Path

MODELO_POR_DEFECTO = "fakespot-ai/roberta-base-ai-text-detection-v1"

# Ponderación calibrada para español: 50 % huella + 30 % uniformidad + 20 % red neuronal
PESO_HUELLA = 0.50
PESO_UNIFORMIDAD = 0.30
PESO_NEURONAL = 0.20

TAMANO_BLOQUE = 1500
BLOQUE_MINIMO = 300

# Etiquetas que los modelos de Hugging Face usan para la clase "generado por IA"
ETIQUETAS_IA = ("AI", "FAKE", "GENERATED", "MACHINE", "LABEL_1")

SENALES_HUMANAS = (
    "porque lo que", "estuciado", "ausetes", "ahria", "segun ", "seria ",
    "pasarian", "lo guay", "de lujo", "un monton", "un montón", "pasan olimpicamente",
)

CONECTORES_IA = (
    "por tanto,", "a diferencia de", "en resumen,", "en conclusión,",
    "cabe destacar", "por otro lado,", "en este sentido,", "asimismo,",
    "no obstante,", "resulta fundamental", "es crucial", "en última instancia",
)


def configurar_cache_modelo():
    """Deja el modelo dentro del proyecto aunque se ejecute desde otra carpeta."""
    if os.environ.get("HF_HOME"):
        return
    raiz = Path(__file__).resolve().parents[2]
    es_repositorio = (raiz / "pyproject.toml").exists()
    destino = (raiz if es_repositorio else Path.cwd()) / "cache_modelo"
    os.environ["HF_HOME"] = str(destino)


class AnalizadorIA:
    """Combina la huella estructural, la uniformidad y un modelo neuronal.

    El detector neuronal se puede inyectar para poder probar la lógica sin
    descargar el modelo, y `usar_modelo=False` permite trabajar sin él.
    """

    def __init__(self, modelo=MODELO_POR_DEFECTO, detector=None, usar_modelo=True, idioma="es"):
        self.modelo = modelo
        self.usar_modelo = usar_modelo
        self.detector = detector
        if usar_modelo and detector is None:
            self.detector = self._cargar_modelo(modelo, idioma)
        self.historial_probabilidades = []  # diagnóstico y pruebas

    @staticmethod
    def _cargar_modelo(modelo, idioma="es"):
        configurar_cache_modelo()
        try:
            from transformers import pipeline
        except ImportError as error:  # depende del extra opcional "modelo"
            raise SystemExit(
                "Falta el modelo neuronal. Instálalo con:\n"
                "  uv sync --extra modelo\n"
                "o ejecuta el análisis sin modelo con --sin-modelo."
            ) from error
        aviso = {
            "es": "Cargando motor híbrido (Neuronal + Huella Estructural Español + Anti-Plagio)...",
            "en": (
                "Loading hybrid engine (neural + Spanish structural fingerprint "
                "+ anti-plagiarism)..."
            ),
        }
        print(aviso.get(idioma, aviso["es"]))
        return pipeline("text-classification", model=modelo)

    def _huella_llm_espanol(self, texto):
        """Patrones característicos de ChatGPT/Claude en español."""
        puntos_ia = 0.0

        guiones_largos = texto.count("—")
        if guiones_largos >= 1:
            puntos_ia += min(30.0, guiones_largos * 15.0)

        listas_negrita = len(re.findall(r'[\*\-]\s+\*\*[^\*]+:\*\*', texto))
        if listas_negrita >= 1:
            puntos_ia += min(35.0, listas_negrita * 15.0)

        encabezados = len(re.findall(r'###\s+\d+\.', texto))
        if encabezados >= 1:
            puntos_ia += 20.0

        texto_lower = texto.lower()
        hits_conectores = sum(1 for c in CONECTORES_IA if c in texto_lower)
        puntos_ia += min(30.0, hits_conectores * 10.0)

        hits_humanos = sum(1 for h in SENALES_HUMANAS if h in texto_lower)
        puntos_ia -= hits_humanos * 25.0

        return round(max(0.0, min(100.0, puntos_ia)), 2)

    def _uniformidad_estadistica(self, texto):
        frases = [f.strip() for f in re.split(r'[.!?]+', texto) if len(f.strip().split()) > 3]
        if len(frases) < 4:
            return 50.0
        longitudes = [len(f.split()) for f in frases]
        media = sum(longitudes) / len(longitudes)
        desviacion = math.sqrt(sum((x - media) ** 2 for x in longitudes) / len(longitudes))
        coef_variacion = desviacion / media if media > 0 else 0
        return round(max(0.0, min(100.0, (1 - (coef_variacion / 0.8)) * 100)), 2)

    @staticmethod
    def _prob_ia(prediccion):
        etiqueta = str(prediccion["label"]).upper()
        score = float(prediccion["score"])
        es_ia = any(clave in etiqueta for clave in ETIQUETAS_IA)
        return (score if es_ia else 1 - score) * 100

    def _probabilidades_neuronales(self, bloques, tamano_lote=8):
        salidas = self.detector(bloques, truncation=True, max_length=512, batch_size=tamano_lote)
        if isinstance(salidas, dict):  # detectores simples devuelven una sola predicción
            salidas = [salidas]
        probabilidades = [self._prob_ia(prediccion) for prediccion in salidas]
        self.historial_probabilidades.extend(probabilidades)
        return probabilidades

    def evaluar_texto(self, texto, tamano_bloque=TAMANO_BLOQUE):
        """Devuelve (media, pico máximo, fragmento con mayor puntuación)."""
        bloques = [texto[i:i + tamano_bloque] for i in range(0, len(texto), tamano_bloque)]
        bloques = [b for b in bloques if len(b.strip()) >= BLOQUE_MINIMO]
        if not bloques:
            return 0.0, 0.0, ""

        if self.usar_modelo:
            probabilidades = self._probabilidades_neuronales(bloques)
            peso_total = PESO_HUELLA + PESO_UNIFORMIDAD + PESO_NEURONAL
        else:
            probabilidades = [None] * len(bloques)
            peso_total = PESO_HUELLA + PESO_UNIFORMIDAD

        puntuaciones = []
        max_prob = 0.0
        peor_bloque = ""

        for bloque, prob_neuronal in zip(bloques, probabilidades, strict=True):
            prob_huella = self._huella_llm_espanol(bloque)
            prob_est = self._uniformidad_estadistica(bloque)
            if prob_neuronal is None:
                suma_estructural = prob_huella * PESO_HUELLA + prob_est * PESO_UNIFORMIDAD
                score_hibrido = suma_estructural / peso_total
            else:
                score_hibrido = (
                    prob_huella * PESO_HUELLA
                    + prob_est * PESO_UNIFORMIDAD
                    + prob_neuronal * PESO_NEURONAL
                )
            puntuaciones.append(score_hibrido)

            if score_hibrido > max_prob:
                max_prob = score_hibrido
                peor_bloque = bloque.replace("\n", " ").replace("\r", " ").replace(";", ",").strip()

        return (
            round(sum(puntuaciones) / len(puntuaciones), 2),
            round(max_prob, 2),
            peor_bloque,
        )

    @staticmethod
    def similitud_coseno(texto1, texto2):
        if not texto1 or not texto2:
            return 0.0
        p1 = Counter(re.findall(r'\w+', texto1.lower()))
        p2 = Counter(re.findall(r'\w+', texto2.lower()))
        comunes = set(p1.keys()) & set(p2.keys())
        num = sum(p1[x] * p2[x] for x in comunes)
        norma1 = math.sqrt(sum(v ** 2 for v in p1.values()))
        norma2 = math.sqrt(sum(v ** 2 for v in p2.values()))
        den = norma1 * norma2
        return round((num / den) * 100, 2) if den else 0.0
