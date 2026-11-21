"""Señal de perplejidad tipo Binoculars (experimental y opcional).

Binoculars (Hans et al., 2024) compara dos modelos de lenguaje emparentados: la perplejidad
del texto bajo uno de ellos, dividida entre la entropía cruzada entre ambos. Un valor bajo
indica texto muy predecible, típico de los modelos. No necesita entrenar con ejemplos de IA.

Aquí el cálculo es NumPy puro y la carga de los modelos es perezosa (extra `modelo`). Por
defecto se usa una pareja pequeña y multilingüe. Los límites que convierten la puntuación en
un porcentaje (`BINO_ALTO`, `BINO_BAJO`) NO están calibrados para español con este par de
modelos: hay que medirlos con `evaluacion/evaluar.py --perplejidad` antes de fiarse.
"""

import numpy as np

from detector_ia.idioma import t

MODELO_OBSERVADOR = "Qwen/Qwen2.5-0.5B"
MODELO_EJECUTOR = "Qwen/Qwen2.5-0.5B-Instruct"

# Puntuación Binoculars -> probabilidad de IA (lineal entre ambos extremos). Sin calibrar.
BINO_ALTO = 0.75  # a partir de aquí o por debajo: 100 % IA
BINO_BAJO = 1.00  # a partir de aquí o por encima: 0 % IA


def _log_softmax(logits):
    desplazado = logits - logits.max(axis=-1, keepdims=True)
    return desplazado - np.log(np.exp(desplazado).sum(axis=-1, keepdims=True))


def puntuacion_binoculars(logits_observador, logits_ejecutor, ids_siguientes):
    """Puntuación Binoculars de un texto.

    `logits_*` tienen forma (T, V): la predicción de cada modelo para el token siguiente,
    e `ids_siguientes` (T,) son los tokens que realmente aparecen. Devuelve
    log-perplejidad (ejecutor) / entropía cruzada (observador, ejecutor); cuanto más baja,
    más parecido a texto generado. Con menos de un token devuelve None.
    """
    ids = np.asarray(ids_siguientes)
    if ids.size == 0:
        return None
    log_p_ejecutor = _log_softmax(np.asarray(logits_ejecutor, dtype=float))
    prob_observador = np.exp(_log_softmax(np.asarray(logits_observador, dtype=float)))
    log_ppl = -log_p_ejecutor[np.arange(ids.size), ids].mean()
    entropia_cruzada = -(prob_observador * log_p_ejecutor).sum(axis=-1).mean()
    if entropia_cruzada <= 0:
        return None
    return float(log_ppl / entropia_cruzada)


def probabilidad_ia(puntuacion):
    """Convierte la puntuación en 0-100 (más alto = más parecido a IA)."""
    if puntuacion is None:
        return None
    fraccion = (BINO_BAJO - puntuacion) / (BINO_BAJO - BINO_ALTO)
    return round(100.0 * min(1.0, max(0.0, fraccion)), 2)


class DetectorPerplejidad:
    """Puntúa bloques de texto. Los modelos se pueden inyectar para probar sin descargarlos."""

    def __init__(self, calculador=None, observador=MODELO_OBSERVADOR, ejecutor=MODELO_EJECUTOR):
        self.calculador = calculador or self._cargar(observador, ejecutor)

    @staticmethod
    def _cargar(observador, ejecutor):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as error:  # depende del extra opcional "modelo"
            raise SystemExit(
                t(
                    "Falta el modelo de lenguaje. Instálalo con:\n"
                    '  pip install "detector-ia[modelo]"\n'
                    "o ejecuta el análisis sin --perplejidad.",
                    "The language model is missing. Install it with:\n"
                    '  pip install "detector-ia[modelo]"\n'
                    "or run the analysis without --perplexity.",
                )
            ) from error
        from detector_ia.motores import configurar_cache_modelo

        configurar_cache_modelo()
        tokenizador = AutoTokenizer.from_pretrained(observador)
        modelo_o = AutoModelForCausalLM.from_pretrained(observador).eval()
        modelo_e = AutoModelForCausalLM.from_pretrained(ejecutor).eval()

        def calcular(texto):
            codificado = tokenizador(texto, return_tensors="pt", truncation=True, max_length=512)
            ids = codificado["input_ids"]
            if ids.shape[1] < 2:
                return None
            with torch.no_grad():
                lo = modelo_o(**codificado).logits[0, :-1].float().cpu().numpy()
                le = modelo_e(**codificado).logits[0, :-1].float().cpu().numpy()
            return puntuacion_binoculars(lo, le, ids[0, 1:].cpu().numpy())

        return calcular

    def probabilidades(self, bloques):
        """Probabilidad de IA (0-100) de cada bloque; None si no se pudo puntuar."""
        return [probabilidad_ia(self.calculador(bloque)) for bloque in bloques]
