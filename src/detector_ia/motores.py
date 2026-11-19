"""Motores de detección: huella estructural, uniformidad, modelo neuronal y similitud."""

import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from detector_ia import similitud

MODELO_POR_DEFECTO = "fakespot-ai/roberta-base-ai-text-detection-v1"

# Ponderación calibrada para español: 50 % huella + 30 % uniformidad + 20 % red neuronal
PESO_HUELLA = 0.50
PESO_UNIFORMIDAD = 0.30
PESO_NEURONAL = 0.20

# Con la señal de perplejidad activada (--perplejidad) los pesos se reparten así
PESOS_CON_PERPLEJIDAD = {
    "huella": 0.40,
    "uniformidad": 0.20,
    "neuronal": 0.15,
    "perplejidad": 0.25,
}

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


@dataclass
class Bloque:
    """Un bloque de ~1500 caracteres con sus señales y las marcas que lo explican."""

    inicio: int
    fin: int
    texto: str
    huella: float
    uniformidad: float
    neuronal: float | None
    perplejidad: float | None
    puntuacion: float
    marcas: list = field(default_factory=list)  # posiciones relativas al inicio del bloque


@dataclass
class Evaluacion:
    """Resultado detallado de una entrega: lo que `evaluar_texto` resume en tres valores."""

    media: float = 0.0
    pico: float = 0.0
    fragmento: str = ""
    bloques: list = field(default_factory=list)

    @property
    def puntuaciones(self):
        return [b.puntuacion for b in self.bloques]


_PATRONES_ESTRUCTURA = (
    ("guion", "Guion largo (—)", re.compile("—")),
    ("lista", "Lista con negrita", re.compile(r"[\*\-]\s+\*\*[^\*]+:\*\*")),
    ("encabezado", "Encabezado numerado", re.compile(r"###\s+\d+\.")),
)


def marcas_huella(texto):
    """Fragmentos que disparan la huella estructural (y los que la rebajan), con su posición.

    Devuelve diccionarios {inicio, fin, tipo, etiqueta}; `tipo` es "humana" para las señales
    que restan puntos. Sirve para explicar por qué un bloque puntúa alto en el informe HTML.
    """
    marcas = []
    for tipo, etiqueta, patron in _PATRONES_ESTRUCTURA:
        for m in patron.finditer(texto):
            marcas.append({"inicio": m.start(), "fin": m.end(), "tipo": tipo, "etiqueta": etiqueta})
    for conector in CONECTORES_IA:
        for m in re.finditer(re.escape(conector), texto, flags=re.IGNORECASE):
            marcas.append(
                {
                    "inicio": m.start(),
                    "fin": m.end(),
                    "tipo": "conector",
                    "etiqueta": "Conector enciclopédico",
                }
            )
    for senal in SENALES_HUMANAS:
        for m in re.finditer(re.escape(senal), texto, flags=re.IGNORECASE):
            marcas.append(
                {
                    "inicio": m.start(),
                    "fin": m.end(),
                    "tipo": "humana",
                    "etiqueta": "Rasgo coloquial o errata",
                }
            )
    marcas.sort(key=lambda marca: (marca["inicio"], -marca["fin"]))
    return marcas


class AnalizadorIA:
    """Combina la huella estructural, la uniformidad y un modelo neuronal.

    El detector neuronal se puede inyectar para poder probar la lógica sin
    descargar el modelo, y `usar_modelo=False` permite trabajar sin él.
    """

    def __init__(
        self,
        modelo=MODELO_POR_DEFECTO,
        detector=None,
        usar_modelo=True,
        idioma="es",
        perplejidad=None,
    ):
        self.modelo = modelo
        self.usar_modelo = usar_modelo
        self.detector = detector
        self.perplejidad = perplejidad  # DetectorPerplejidad o equivalente (señal opcional)
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

    def _pesos(self):
        if self.perplejidad is not None:
            pesos = dict(PESOS_CON_PERPLEJIDAD)
        else:
            pesos = {
                "huella": PESO_HUELLA,
                "uniformidad": PESO_UNIFORMIDAD,
                "neuronal": PESO_NEURONAL,
            }
        if not self.usar_modelo:
            pesos.pop("neuronal")
        return pesos

    def evaluar_detalle(self, texto, tamano_bloque=TAMANO_BLOQUE):
        """Evalúa una entrega y devuelve las señales y las marcas de cada bloque."""
        inicios = [
            i for i in range(0, len(texto), tamano_bloque)
            if len(texto[i:i + tamano_bloque].strip()) >= BLOQUE_MINIMO
        ]
        if not inicios:
            return Evaluacion()
        trozos = [texto[i:i + tamano_bloque] for i in inicios]

        neuronales = (
            self._probabilidades_neuronales(trozos) if self.usar_modelo else [None] * len(trozos)
        )
        perplejidades = (
            self.perplejidad.probabilidades(trozos)
            if self.perplejidad is not None
            else [None] * len(trozos)
        )
        pesos = self._pesos()

        evaluacion = Evaluacion()
        for inicio, trozo, p_neuronal, p_perplejidad in zip(
            inicios, trozos, neuronales, perplejidades, strict=True
        ):
            senales = {
                "huella": self._huella_llm_espanol(trozo),
                "uniformidad": self._uniformidad_estadistica(trozo),
                "neuronal": p_neuronal,
                "perplejidad": p_perplejidad,
            }
            # Si una señal opcional no pudo calcularse en este bloque, se renormaliza sin ella
            usadas = {n: p for n, p in pesos.items() if senales[n] is not None}
            total = sum(usadas.values())
            puntuacion = sum(senales[n] * p for n, p in usadas.items()) / total
            evaluacion.bloques.append(
                Bloque(
                    inicio=inicio,
                    fin=inicio + len(trozo),
                    texto=trozo,
                    huella=senales["huella"],
                    uniformidad=senales["uniformidad"],
                    neuronal=p_neuronal,
                    perplejidad=p_perplejidad,
                    puntuacion=puntuacion,
                    marcas=marcas_huella(trozo),
                )
            )

        peor = max(evaluacion.bloques, key=lambda b: b.puntuacion)
        evaluacion.pico = round(peor.puntuacion, 2)
        evaluacion.media = round(
            sum(evaluacion.puntuaciones) / len(evaluacion.bloques), 2
        )
        evaluacion.fragmento = (
            peor.texto.replace("\n", " ").replace("\r", " ").replace(";", ",").strip()
            if peor.puntuacion > 0
            else ""
        )
        return evaluacion

    def evaluar_texto(self, texto, tamano_bloque=TAMANO_BLOQUE):
        """Devuelve (media, pico máximo, fragmento con mayor puntuación)."""
        evaluacion = self.evaluar_detalle(texto, tamano_bloque)
        return evaluacion.media, evaluacion.pico, evaluacion.fragmento

    @staticmethod
    def similitud_coseno(texto1, texto2):
        return similitud.similitud_coseno(texto1, texto2)
