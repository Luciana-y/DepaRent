"""Modelo 2: perfil de accesibilidad a transporte público (paraderos ATU).

No es aprendizaje automático. Replica la ingeniería de variables espaciales del
notebook de la Semana 7 (cKDTree sobre coordenadas proyectadas a metros) como una
función reutilizable. El inventario de paraderos es de mayo de 2021.
"""
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from modelo import ROOT, SOURCE, normalizar

PARADEROS = ROOT.parent / "week07/data/paraderos_procesado.csv"
# Misma proyección local que el notebook (aproximación plana centrada en Lima).
_LAT_CENTRO = np.radians(-12.05)
M_POR_GRADO_LAT = 111132.954 - 559.822 * np.cos(2 * _LAT_CENTRO)
M_POR_GRADO_LON = 111412.84 * np.cos(_LAT_CENTRO)
# Mismo recorte geográfico que el preprocesamiento de anuncios.
LIMITES = {"latitud": (-12.35, -11.75), "longitud": (-77.20, -76.80)}
RADIOS_M = (300, 500, 1000)
AVISO = ("Paraderos del inventario ATU de mayo de 2021; la red actual puede ser distinta. "
         "Las distancias son en línea recta, no recorridos a pie. El nivel es una regla de apoyo, no una norma urbana.")


def _a_metros(lat, lon):
    return np.column_stack([np.asarray(lat, float) * M_POR_GRADO_LAT, np.asarray(lon, float) * M_POR_GRADO_LON])


@lru_cache(maxsize=1)
def cargar_red(paraderos=PARADEROS, departamentos=SOURCE):
    """Carga paraderos, índices espaciales y la referencia de anuncios (una vez por proceso)."""
    stops = pd.read_csv(paraderos)
    stops = stops.dropna(subset=["latitud", "longitud"]).reset_index(drop=True)
    xy = _a_metros(stops["latitud"], stops["longitud"])
    trees = {"todos": cKDTree(xy)}
    for tipo in ("Troncal", "Corredor"):
        mask = (stops["tipo_transporte"] == tipo).to_numpy()
        trees[tipo] = cKDTree(xy[mask])
    listings = pd.read_csv(departamentos, low_memory=False,
                           usecols=["distrito_norm", "latitud", "longitud", "dist_paradero_min_m", "paraderos_500m"])
    listings["distrito_norm"] = listings["distrito_norm"].map(normalizar)
    centros = listings.groupby("distrito_norm")[["latitud", "longitud"]].median()
    return {"paraderos": stops, "arboles": trees,
            "ref_distancia": np.sort(listings["dist_paradero_min_m"].dropna().to_numpy()),
            "ref_500m_mediana": float(listings["paraderos_500m"].median()),
            "centros": {d: (float(r.latitud), float(r.longitud)) for d, r in centros.iterrows()}}


def centro_distrito(distrito, red=None):
    """Mediana de coordenadas de los anuncios del distrito; aproximación cuando no hay dirección."""
    red = red or cargar_red()
    return red["centros"].get(normalizar(distrito))


def validar_coordenadas(lat, lon):
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        raise ValueError("Latitud y longitud deben ser numéricas.")
    for nombre, valor in (("latitud", lat), ("longitud", lon)):
        minimo, maximo = LIMITES[nombre]
        if not np.isfinite(valor) or not minimo <= valor <= maximo:
            raise ValueError(f"La {nombre} debe estar entre {minimo} y {maximo} (Lima Metropolitana y Callao).")
    return lat, lon


def nivel_accesibilidad(distancia_m, paraderos_500m, mediana_500m):
    """Regla heurística: 300 m equivale a unos 4 minutos a pie."""
    if distancia_m <= 300 and paraderos_500m >= mediana_500m:
        return "Alta"
    if distancia_m > 500:
        return "Baja"
    return "Media"


def accesibilidad(lat, lon, red=None, cercanos=5):
    """Devuelve las mismas variables del notebook para una ubicación, más contexto para el propietario."""
    lat, lon = validar_coordenadas(lat, lon)
    red = red or cargar_red()
    punto = _a_metros([lat], [lon])[0]
    stops, trees = red["paraderos"], red["arboles"]
    k = min(cercanos, len(stops))
    distancias, indices = trees["todos"].query(punto, k=k)
    distancias, indices = np.atleast_1d(distancias), np.atleast_1d(indices)
    nearest = stops.iloc[indices[0]]
    conteos = {f"paraderos_{r}m": len(trees["todos"].query_ball_point(punto, r=r)) for r in RADIOS_M}
    distancia_min = round(float(distancias[0]), 1)
    # Proporción de anuncios con un paradero más lejano que esta ubicación.
    mejor_que = float(1 - np.searchsorted(red["ref_distancia"], distancia_min, side="right") / len(red["ref_distancia"]))
    return {
        "latitud": lat, "longitud": lon,
        "dist_paradero_min_m": distancia_min,
        "paradero_cercano_nombre": str(nearest["nombre_paradero"]),
        "paradero_cercano_tipo": str(nearest["tipo_transporte"]),
        "paradero_cercano_afluencia": str(nearest["nivel_afluencia_desc"]),
        **conteos,
        "dist_troncal_brt_m": round(float(trees["Troncal"].query(punto, k=1)[0]), 1),
        "dist_corredor_m": round(float(trees["Corredor"].query(punto, k=1)[0]), 1),
        "nivel": nivel_accesibilidad(distancia_min, conteos["paraderos_500m"], red["ref_500m_mediana"]),
        "porcentaje_anuncios_mas_lejos": round(100 * mejor_que, 1),
        "cercanos": [{"Paradero": str(stops.iloc[i]["nombre_paradero"]), "Tipo": str(stops.iloc[i]["tipo_transporte"]),
                      "Distancia (m)": round(float(d), 1), "latitud": float(stops.iloc[i]["latitud"]),
                      "longitud": float(stops.iloc[i]["longitud"])} for d, i in zip(distancias, indices)],
        "aviso": AVISO,
    }


def variables_lote(latitudes, longitudes, red=None):
    """Distancia al paradero más cercano y paraderos a 500 m para muchas ubicaciones a la vez."""
    red = red or cargar_red()
    puntos = _a_metros(latitudes, longitudes)
    distancia, _ = red["arboles"]["todos"].query(puntos, k=1)
    a_500 = red["arboles"]["todos"].query_ball_point(puntos, r=500, return_length=True)
    return np.round(distancia, 1), np.asarray(a_500, dtype=int)
