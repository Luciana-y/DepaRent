"""RF2 — Perfil de accesibilidad con paraderos ATU.

Refactor de la celda In[17] de deliveries/week07/code/EDA_week07.ipynb, sin cambiar la
metodología: proyección equirectangular centrada en lat -12.05, cKDTree sobre todos los
paraderos (más cercano y conteos por radio) y árboles separados para Troncal y Corredor.
Los árboles se construyen una sola vez por índice y se reutilizan en cada consulta.
"""
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from config import find_data_file
from src.input_validation import validate_coordinates

SOURCE_FILE = "paraderos_procesado.csv"
RADII_M = (300, 500, 1000)
TYPED_DISTANCES = {"Troncal": "dist_troncal_brt_m", "Corredor": "dist_corredor_m"}

LAT_CENTER_RAD = np.radians(-12.05)
M_PER_DEG_LAT = 111132.954 - 559.822 * np.cos(2 * LAT_CENTER_RAD)
M_PER_DEG_LON = 111412.84 * np.cos(LAT_CENTER_RAD)


def project(lat, lon):
    """(lat, lon) en grados -> coordenadas planas en metros (misma fórmula que Week 7)."""
    return np.column_stack([np.asarray(lat, dtype=float) * M_PER_DEG_LAT, np.asarray(lon, dtype=float) * M_PER_DEG_LON])


class AccessibilityIndex:
    def __init__(self, path=None):
        self.path = path or find_data_file(SOURCE_FILE)
        stops = pd.read_csv(self.path)
        needed = ["nombre_paradero", "latitud", "longitud", "tipo_transporte", "nivel_afluencia_desc", "timestamp_oficial"]
        missing = [c for c in needed if c not in stops.columns]
        if missing:
            raise ValueError(f"Faltan columnas {missing} en {self.path}")
        self.stops = stops.reset_index(drop=True)
        xy = project(stops["latitud"], stops["longitud"])
        self.tree_all = cKDTree(xy)
        self.typed_trees = {}
        for tipo, col in TYPED_DISTANCES.items():
            mask = (stops["tipo_transporte"] == tipo).to_numpy()
            if mask.sum() == 0:
                raise ValueError(f"No hay paraderos de tipo '{tipo}' en {self.path}")
            self.typed_trees[col] = cKDTree(xy[mask])
        self.source = {
            "file": self.path.name,
            "n_paraderos": int(len(stops)),
            "corte_datos": sorted(stops["timestamp_oficial"].dropna().unique().tolist()),
        }

    def compute_many(self, lat, lon):
        """Indicadores para varios puntos (sin validar). Devuelve un DataFrame."""
        xy = project(lat, lon)
        dist, idx = self.tree_all.query(xy, k=1)
        out = pd.DataFrame({"dist_paradero_min_m": np.round(dist, 1)})
        out["paradero_cercano_tipo"] = self.stops["tipo_transporte"].to_numpy()[idx]
        out["paradero_cercano_afluencia"] = self.stops["nivel_afluencia_desc"].to_numpy()[idx]
        out["paradero_cercano_nombre"] = self.stops["nombre_paradero"].to_numpy()[idx]
        for r in RADII_M:
            out[f"paraderos_{r}m"] = [len(v) for v in self.tree_all.query_ball_point(xy, r=r)]
        for col, tree in self.typed_trees.items():
            d, _ = tree.query(xy, k=1)
            out[col] = np.round(d, 1)
        return out

    def get_accessibility(self, lat, lon):
        lat, lon = validate_coordinates(lat, lon)
        row = self.compute_many([lat], [lon]).iloc[0]
        result = {
            "dist_paradero_min_m": float(row["dist_paradero_min_m"]),
            "paradero_cercano_tipo": row["paradero_cercano_tipo"],
            "paradero_cercano_afluencia": row["paradero_cercano_afluencia"],
            "paradero_cercano_nombre": row["paradero_cercano_nombre"],
        }
        result.update({f"paraderos_{r}m": int(row[f"paraderos_{r}m"]) for r in RADII_M})
        result.update({col: float(row[col]) for col in TYPED_DISTANCES.values()})
        result["fuente"] = self.source
        return result


@lru_cache(maxsize=1)
def get_index():
    return AccessibilityIndex()


def get_accessibility(lat, lon):
    """Indicadores ATU para un punto en Lima/Callao. Levanta InputValidationError si las coordenadas no son válidas."""
    return get_index().get_accessibility(lat, lon)
