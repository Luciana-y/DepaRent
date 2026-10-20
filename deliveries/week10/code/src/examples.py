"""Casos reales del dataset para demostrar el producto.

Selección determinista: para cada cluster, el anuncio de departamentos_procesados.csv más
cercano a su centroide (distancia euclidiana en el espacio estandarizado del clustering)
entre los que tienen informados baños, antigüedad y mantenimiento. Empates: menor id_anuncio.
Solo se devuelven las características del formulario; ningún resultado se precalcula.
"""
import math
from functools import lru_cache

import numpy as np

from src.comparables import get_index, source_label
from src.input_validation import AMENITIES

SELECTION_CRITERION = (
    "Por cada cluster, el anuncio más cercano al centroide en el espacio estandarizado del clustering, "
    "entre los que tienen baños, antigüedad y mantenimiento informados (empates: menor id_anuncio)."
)


def row_to_property(row):
    """Fila del dataset -> diccionario de entrada del contrato (sin precio ni columnas internas)."""
    prop = {
        "distrito": row["distrito"],
        "area_total": float(row["area_total"]),
        "dormitorios": int(row["dormitorios"]),
        "banos": int(row["banos"]),
        "amenidades": [a for a in AMENITIES if row[a] == 1],
        "latitud": float(row["latitud"]),
        "longitud": float(row["longitud"]),
    }
    for col in ("antiguedad", "mantenimiento"):
        if not math.isnan(row[col]):
            prop[col] = float(row[col])
    return prop


def select_example_properties(index):
    """Un caso real por cluster a partir del índice de comparables (datos ya cargados)."""
    df = index.records
    complete = df[["banos", "antiguedad", "mantenimiento"]].notna().all(axis=1).to_numpy()
    centers = index.model.pipeline.named_steps["kmeans"].cluster_centers_
    cases = []
    for cid, center in enumerate(centers):
        rows = np.flatnonzero(complete & (index.labels == cid))
        if rows.size == 0:
            raise ValueError(f"El cluster {cid} no tiene anuncios completos para usar como caso real")
        dist = np.linalg.norm(index.X[rows] - center, axis=1)
        best = rows[np.lexsort((index.ids[rows], dist))[0]]
        row = df.iloc[best]
        cases.append({
            "case_id": f"caso_{cid + 1}",
            "id_anuncio": int(row["id_anuncio"]),
            "fuente": source_label(row["fuente"]),
            "fecha_scraping": row["fecha_scraping"],
            "property": row_to_property(row),
        })
    return cases


@lru_cache(maxsize=1)
def get_example_properties():
    return select_example_properties(get_index())
