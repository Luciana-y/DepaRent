"""Modelo docente de alquiler. Una sola preparación para entrenamiento e inferencia."""
from pathlib import Path
import re
import unicodedata
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parent.parent  # deliveries/week10
SOURCE = ROOT.parent / "week07/data/departamentos_procesados.csv"
NUMERIC = ["area_total", "dormitorios", "banos", "estacionamientos", "antiguedad", "mantenimiento"]
BINARY = ["ascensor", "balcon", "terraza", "piscina", "gimnasio", "pet_friendly"]
FEATURES = ["distrito_norm"] + NUMERIC + BINARY
LIMITS = {"area_total": (25, 450), "dormitorios": (0, 10), "banos": (0, 10),
          "estacionamientos": (0, 10), "antiguedad": (0, 100), "mantenimiento": (0, 5000)}

def normalizar(value):
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text)).strip()

def preparar(frame):
    """Transformaciones sin aprendizaje; imputación aprendida va dentro del pipeline."""
    out = frame.reindex(columns=FEATURES).copy()
    out["distrito_norm"] = out["distrito_norm"].map(normalizar)
    for col in NUMERIC + BINARY:
        out[col] = pd.to_numeric(out[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
    return out

def construir_pipeline():
    pre = ColumnTransformer([
        ("num", SimpleImputer(strategy="median", add_indicator=True), NUMERIC),
        ("bin", SimpleImputer(strategy="most_frequent"), BINARY),
        ("district", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["distrito_norm"]),
    ])
    # Hiperparámetros fijados antes de abrir el conjunto de prueba; sin búsqueda.
    return Pipeline([("preparacion", pre), ("modelo", HistGradientBoostingRegressor(
        max_iter=150, learning_rate=0.08, max_leaf_nodes=15,
        l2_regularization=2.0, early_stopping=False, random_state=42))])

def grupos_inmueble(frame):
    """Conecta posibles duplicados mediante claves sin precio. Puede sobreagrupar."""
    parent = list(range(len(frame)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    seen = {}
    for i, row in enumerate(frame.to_dict("records")):
        area = pd.to_numeric(row.get("area_total"), errors="coerce")
        bedrooms = pd.to_numeric(row.get("dormitorios"), errors="coerce")
        district = normalizar(row.get("distrito_norm"))
        suffix = (district, round(float(area), 0), str(bedrooms))
        keys = []
        identifier = str(row.get("id_anuncio", "")).strip()
        if identifier and identifier != "nan":
            keys.append(("id", identifier))
        address = normalizar(row.get("direccion"))
        if len(address) >= 12:
            keys.append(("address", address, *suffix))
        lat, lon = (pd.to_numeric(row.get(c), errors="coerce") for c in ("latitud", "longitud"))
        if pd.notna(lat) and pd.notna(lon):
            keys.append(("geo", round(float(lat), 4), round(float(lon), 4), *suffix))
        description = normalizar(row.get("descripcion"))
        if len(description) >= 80:
            keys.append(("description", description, *suffix))
        for key in keys:
            if key in seen:
                parent[root(i)] = root(seen[key])
            else:
                seen[key] = i
    return np.array([root(i) for i in range(len(frame))])

def validar_entrada(values, artifact):
    district = normalizar(values.get("distrito_norm"))
    if district not in artifact["distritos"]:
        raise ValueError("Selecciona un distrito conocido del listado.")
    for col, (minimum, maximum) in LIMITS.items():
        value = values.get(col)
        if value is None or value == "":
            if col in ("area_total", "dormitorios", "banos"):
                raise ValueError(f"Falta {col}.")
            continue
        try:
            number = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"{col} debe ser numérico.")
        if not np.isfinite(number) or not minimum <= number <= maximum:
            raise ValueError(f"{col} debe estar entre {minimum} y {maximum}.")
        if col in ("dormitorios", "banos", "estacionamientos") and not number.is_integer():
            raise ValueError(f"{col} debe ser entero.")
    for col in BINARY:
        if values.get(col) not in (None, "", 0, 1, False, True):
            raise ValueError(f"{col} debe ser 0, 1 o desconocido.")
    return preparar(pd.DataFrame([values]))

def predecir(values, artifact):
    data = validar_entrada(values, artifact)
    value = float(artifact["pipeline"].predict(data)[0])
    q = artifact["radio_calibrado_soles"]
    district = data.iloc[0]["distrito_norm"]
    warnings = []
    for col in NUMERIC:
        v = data.iloc[0][col]
        bounds = artifact["rangos_entrenamiento"][col]
        if pd.notna(v) and not bounds[0] <= v <= bounds[1]:
            warnings.append(f"{col} está fuera del rango observado en entrenamiento.")
    return {"precio_estimado_soles": round(value, 2),
            "limite_inferior_soles": round(max(0.0, value - q), 2),
            "limite_superior_soles": round(value + q, 2),
            "baseline_distrital_soles": round(float(artifact["medianas_distrito"].get(district, artifact["mediana_global"])), 2),
            "anuncios_entrenamiento_distrito": artifact["conteos_distrito"].get(district, 0),
            "advertencias": warnings}
