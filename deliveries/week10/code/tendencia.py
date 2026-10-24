"""Modelo 4: tendencia del alquiler distrital (SARIMA sobre series del BCRP).

Lee los pronósticos guardados por entrenar_tendencia.py; no reajusta en cada consulta.
"""
import json
from functools import lru_cache

import numpy as np

from modelo import ROOT, normalizar

ARCHIVO = ROOT / "resultados/tendencia_distrital.json"
HORIZONTE = 4
UMBRAL_PORCENTAJE = 2.0
SERIE_GENERAL = "promedio"
AVISO = ("Tendencia de una serie trimestral del BCRP derivada del precio de venta y el PER (S/ por m²), no de alquileres "
         "observados. Es contexto de mercado: no cambia la estimación del precio ni garantiza la evolución futura.")


def clasificar_tendencia(ultimos_observados, pronostico, umbral=UMBRAL_PORCENTAJE):
    base, futuro = float(np.mean(ultimos_observados)), float(np.mean(pronostico))
    cambio = 100 * (futuro - base) / base
    etiqueta = "Al alza" if cambio > umbral else "A la baja" if cambio < -umbral else "Estable"
    return {"tendencia": etiqueta, "cambio_porcentaje": round(cambio, 2),
            "promedio_ultimos_4": round(base, 4), "promedio_pronostico_4": round(futuro, 4)}


@lru_cache(maxsize=1)
def cargar_tendencias(archivo=ARCHIVO):
    return json.loads(archivo.read_text(encoding="utf-8"))


def tendencia_distrital(distrito, datos=None):
    """Serie del distrito o, si el BCRP no la publica, la serie promedio (marcada como tal)."""
    datos = datos or cargar_tendencias()
    clave = normalizar(distrito)
    propia = clave in datos["series"]
    serie = datos["series"][clave if propia else SERIE_GENERAL]
    return {**serie, "serie_propia": propia, "aviso": AVISO, "regla": datos["regla_tendencia"]}
