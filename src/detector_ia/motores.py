import os
os.environ["HF_HOME"] = "./cache_modelo"

import re
import math
from collections import Counter
from transformers import pipeline

class AnalizadorIA:
    def __init__(self, modelo="fakespot-ai/roberta-base-ai-text-detection-v1"):
        print("Cargando motor híbrido (Neuronal + Huella Estructural Español + Anti-Plagio)...")
        self.detector = pipeline("text-classification", model=modelo)

    def _huella_llm_espanol(self, texto):
        """
        Detecta patrones característicos de ChatGPT/Claude en español:
        - Uso de guiones largos (—)
        - Listas con negrita y dos puntos (**Concepto:**)
        - Encabezados Markdown (###)
        - Conectores enciclopédicos formales
        - Ausencia de erratas o coloquialismos
        """
        puntos_ia = 0.0

        # 1. Guiones largos (—), rarísimos en teclados de alumnos españoles pero constantes en ChatGPT
        guiones_largos = texto.count("—")
        if guiones_largos >= 1:
            puntos_ia += min(30.0, guiones_largos * 15.0)

        # 2. Patrón típico de lista IA: "* **Texto:**" o "- **Texto:**"
        listas_negrita = len(re.findall(r'[\*\-]\s+\*\*[^\*]+:\*\*', texto))
        if listas_negrita >= 1:
            puntos_ia += min(35.0, listas_negrita * 15.0)

        # 3. Encabezados estructurados tipo informe (### 1. Título)
        encabezados = len(re.findall(r'###\s+\d+\.', texto))
        if encabezados >= 1:
            puntos_ia += 20.0

        # 4. Conectores formales típicos de LLM en español
        conectores = [
            "por tanto,", "a diferencia de", "en resumen,", "en conclusión,",
            "cabe destacar", "por otro lado,", "en este sentido,", "asimismo,",
            "no obstante,", "resulta fundamental", "es crucial", "en última instancia"
        ]
        texto_lower = texto.lower()
        hits_conectores = sum(1 for c in conectores if c in texto_lower)
        puntos_ia += min(30.0, hits_conectores * 10.0)

        # 5. Penalización inversa (señales humanas: falta de tildes en palabras clave o expresiones coloquiales)
        senales_humanas = [
            "porque lo que", "estuciado", "ausetes", "ahria", "segun ", "seria ",
            "pasarian", "lo guay", "de lujo", "un monton", "un montón", "pasan olimpicamente"
        ]
        hits_humanos = sum(1 for h in senales_humanas if h in texto_lower)
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

    def evaluar_texto(self, texto, tamano_bloque=1500):
        bloques = [texto[i:i+tamano_bloque] for i in range(0, len(texto), tamano_bloque)]
        puntuaciones = []
        max_prob = 0.0
        peor_bloque = ""

        for bloque in bloques:
            if len(bloque.strip()) < 300:
                continue
            salida = self.detector(bloque, truncation=True, max_length=512)
            prediccion = salida[0] if isinstance(salida, list) else salida
            etiqueta = prediccion["label"].upper()
            es_ia = any(k in etiqueta for k in ["AI", "FAKE", "GENERATED", "1", "MACHINE"])
            prob_neuronal = (prediccion["score"] if es_ia else (1 - prediccion["score"])) * 100
            prob_est = self._uniformidad_estadistica(bloque)
            prob_huella = self._huella_llm_espanol(bloque)

            # Ponderación calibrada para español:
            # 50% Huella Estructural Español + 30% Uniformidad + 20% Red Neuronal
            score_hibrido = (prob_huella * 0.50) + (prob_est * 0.30) + (prob_neuronal * 0.20)
            puntuaciones.append(score_hibrido)

            if score_hibrido > max_prob:
                max_prob = score_hibrido
                peor_bloque = bloque.replace("\n", " ").replace("\r", " ").replace(";", ",").strip()

        if not puntuaciones:
            return 0.0, 0.0, ""
        return round(sum(puntuaciones) / len(puntuaciones), 2), round(max_prob, 2), peor_bloque

    @staticmethod
    def similitud_coseno(texto1, texto2):
        if not texto1 or not texto2:
            return 0.0
        p1 = Counter(re.findall(r'\w+', texto1.lower()))
        p2 = Counter(re.findall(r'\w+', texto2.lower()))
        comunes = set(p1.keys()) & set(p2.keys())
        num = sum(p1[x] * p2[x] for x in comunes)
        den = math.sqrt(sum(v**2 for v in p1.values())) * math.sqrt(sum(v**2 for v in p2.values()))
        return round((num / den) * 100, 2) if den else 0.0
