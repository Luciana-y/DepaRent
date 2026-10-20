"""RF1 — Perfil competitivo: preprocesamiento, entrenamiento e inferencia del clustering.

Versión productiva del K-Means de Week 7 sin variables de precio. La lógica de imputación
replica la de la celda In[19] del notebook canónico (mediana por distrito para antigüedad y
mantenimiento, moda por dormitorios para baños), pero sus parámetros se aprenden en `fit`
y quedan persistidos: en inferencia nunca se recalculan con la propiedad nueva.
"""
import hashlib
import json
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from config import MODELS_DIR, find_data_file
from src.input_validation import AMENITIES, RANGES, normalize_district_name, validate_property

SOURCE_FILE = "departamentos_procesados.csv"
NUMERIC_FEATURES = ["area_total", "dormitorios", "banos", "antiguedad", "mantenimiento"]
FEATURES = NUMERIC_FEATURES + AMENITIES

# Columnas que nunca deben entrar al clustering ni a la similitud.
PRICE_COLUMNS = ["precio", "precio_soles", "precio_m2", "precio_m2_real"]
EXCLUDED_FEATURES = {
    "precio_soles": "variable de precio (aún no la conoce el propietario)",
    "precio_m2_real": "transformación directa del precio",
    "precio": "precio original del anuncio",
    "precio_m2": "transformación directa del precio",
    "cochera": "constante (1) en todas las filas no nulas: no informativa",
    "estacionamientos": "nulos ambiguos (89.25% no confirmables); excluida también en Week 7",
    "medios_banos": "78% de nulos en el dataset de entrenamiento",
    "piso": "43% de nulos y no forma parte del clustering canónico",
    "*_imputado": "banderas de calidad del anuncio, no características del inmueble",
    "bcrp_*": "BCRP fuera del alcance de Week 10",
    "dist_*/paraderos_*": "accesibilidad ATU se reporta como RF2 independiente",
    "distrito": "se usa para priorizar comparables e imputar, no como distancia numérica",
}

PIPELINE_FILE = "clustering_pipeline.joblib"
METADATA_FILE = "clustering_metadata.json"
NAMES_FILE = "cluster_names.json"


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_training_frame(path=None):
    """Carga el dataset canónico y aplica la limpieza previa al entrenamiento.

    - `distrito` se normaliza con el `distrito_map` canónico (sin agrupar en "Otros").
    - Valores fuera de RANGES pasan a NaN (y luego se imputan), con el mismo criterio
      que rechaza la validación de entrada.
    """
    path = path or find_data_file(SOURCE_FILE)
    df = pd.read_csv(path, low_memory=False)
    needed = ["id_anuncio", "distrito", "distrito_norm"] + FEATURES
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas {missing} en {path}")
    df = df.copy()
    df["distrito"] = df["distrito"].map(normalize_district_name)
    out_of_range = {}
    for col, (lo, hi) in RANGES.items():
        bad = df[col].notna() & ~df[col].between(lo, hi)
        out_of_range[col] = int(bad.sum())
        df[col] = df[col].where(~bad)
    df.attrs["out_of_range"] = out_of_range
    if df[["area_total", "dormitorios"]].isna().any().any():
        raise ValueError("area_total y dormitorios no pueden tener nulos en el dataset de entrenamiento")
    return df


class ClusteringPreprocessor(BaseEstimator, TransformerMixin):
    """Imputación con parámetros aprendidos en entrenamiento.

    Entrada: DataFrame con `distrito` (normalizado) + FEATURES.
    - antiguedad / mantenimiento: mediana del grupo distrital (`distrito_norm` de Week 7,
      donde los distritos con < 20 anuncios forman "Otros"); si el grupo no tiene valores,
      mediana global.
    - banos: moda según dormitorios; si no hay, moda global.
    Salida: matriz numpy con FEATURES en orden fijo.
    """

    def __init__(self, group_column="distrito_norm"):
        self.group_column = group_column

    def fit(self, X, y=None):
        self.district_to_group_ = (
            X[["distrito", self.group_column]].drop_duplicates().set_index("distrito")[self.group_column].to_dict()
        )
        if len(self.district_to_group_) != X["distrito"].nunique():
            raise ValueError("Un mismo distrito aparece asignado a más de un grupo distrital")
        groups = X["distrito"].map(self.district_to_group_)
        self.group_medians_ = {}
        self.global_medians_ = {}
        for col in ["antiguedad", "mantenimiento"]:
            med = X[col].groupby(groups).median()
            self.group_medians_[col] = {g: float(v) for g, v in med.dropna().items()}
            self.global_medians_[col] = float(X[col].median())
        modes = X.dropna(subset=["banos"]).groupby("dormitorios")["banos"].agg(lambda s: s.mode().iloc[0])
        self.banos_mode_by_dorm_ = {int(k): float(v) for k, v in modes.items()}
        self.banos_global_mode_ = float(X["banos"].mode().iloc[0])
        self.feature_names_out_ = list(FEATURES)
        return self

    def impute(self, X):
        """Imputa con los parámetros aprendidos; devuelve el DataFrame completo."""
        X = X.copy()
        unknown = sorted(set(X["distrito"]) - set(self.district_to_group_))
        if unknown:
            raise ValueError(f"Distritos sin parámetros de imputación: {unknown}")
        groups = X["distrito"].map(self.district_to_group_)
        for col in ["antiguedad", "mantenimiento"]:
            fill = groups.map(self.group_medians_[col]).fillna(self.global_medians_[col])
            X[col] = X[col].fillna(fill)
        fill_banos = X["dormitorios"].map(self.banos_mode_by_dorm_).fillna(self.banos_global_mode_)
        X["banos"] = X["banos"].fillna(fill_banos)
        return X

    def transform(self, X):
        out = self.impute(X)[FEATURES].astype(float)
        if out.isna().any().any():
            raise ValueError(f"Quedaron nulos tras imputar en: {out.columns[out.isna().any()].tolist()}")
        return out.to_numpy()

    def get_feature_names_out(self, input_features=None):
        return np.array(self.feature_names_out_, dtype=object)


def property_to_frame(prop):
    """Propiedad validada (salida de validate_property) -> DataFrame de una fila."""
    row = {"distrito": prop["distrito"]}
    row.update({c: (np.nan if prop[c] is None else prop[c]) for c in NUMERIC_FEATURES})
    row.update(prop["amenidades"])
    return pd.DataFrame([row])


def build_cluster_profiles(df, labels):
    """Perfil descriptivo de cada cluster con valores observados (antes de imputar)."""
    total = len(df)
    profiles = {}
    for cid in sorted(np.unique(labels)):
        part = df[labels == cid]
        prof = {"n": int(len(part)), "pct": round(len(part) / total * 100, 2)}
        for col in NUMERIC_FEATURES:
            s = part[col].dropna()
            prof[col] = {
                "mediana": round(float(s.median()), 2),
                "media": round(float(s.mean()), 2),
                "p25": round(float(s.quantile(0.25)), 2),
                "p75": round(float(s.quantile(0.75)), 2),
                "n_observados": int(s.size),
            }
        prof["amenidades_pct"] = {a: round(float(part[a].mean() * 100), 1) for a in AMENITIES}
        top = part["distrito"].value_counts(normalize=True).head(5) * 100
        prof["distritos_principales_pct"] = {d: round(float(v), 1) for d, v in top.items()}
        profiles[int(cid)] = prof
    return profiles


class ClusteringModel:
    """Modelo de perfil competitivo cargado desde models/."""

    def __init__(self, models_dir=MODELS_DIR, verify_data=True):
        pipeline_path = models_dir / PIPELINE_FILE
        metadata_path = models_dir / METADATA_FILE
        names_path = models_dir / NAMES_FILE
        for p in (pipeline_path, metadata_path, names_path):
            if not p.exists():
                raise FileNotFoundError(
                    f"Falta el artefacto {p}. Ejecutar scripts/train_clustering.py y definir {NAMES_FILE}."
                )
        self.pipeline = joblib.load(pipeline_path)
        self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        names = json.loads(names_path.read_text(encoding="utf-8"))
        sizes = [self.metadata["cluster_profiles"][str(i)]["n"] for i in range(self.metadata["k_selected"])]
        if names.get("k") != self.metadata["k_selected"] or names.get("cluster_sizes") != sizes:
            raise ValueError(
                f"{NAMES_FILE} no corresponde al modelo entrenado (k o tamaños distintos). "
                "Revisar los perfiles y actualizar los nombres."
            )
        self.names = {int(k): v["name"] for k, v in names["clusters"].items()}
        self.data_path = find_data_file(self.metadata["source"]["file"])
        if verify_data and sha256_of(self.data_path) != self.metadata["source"]["sha256"]:
            raise ValueError(
                f"El dataset {self.data_path} cambió respecto al usado en entrenamiento (SHA-256 distinto)."
            )
        self.known_districts = sorted(self.pipeline.named_steps["prep"].district_to_group_)

    @property
    def scaled_space(self):
        """Preprocesamiento + escalado (sin K-Means): espacio de similitud."""
        return self.pipeline[:-1]

    def validate(self, property_data):
        return validate_property(property_data, self.known_districts)

    def predict_validated(self, prop):
        frame = property_to_frame(prop)
        cid = int(self.pipeline.predict(frame)[0])
        return cid, frame

    def describe(self, cid):
        return {
            "cluster_id": cid,
            "cluster_name": self.names[cid],
            "cluster_profile": self.metadata["cluster_profiles"][str(cid)],
        }

    def predict_cluster(self, property_data):
        prop = self.validate(property_data)
        cid, _ = self.predict_validated(prop)
        return self.describe(cid)


@lru_cache(maxsize=1)
def get_model():
    return ClusteringModel()


def predict_cluster(property_data):
    """Asigna el perfil competitivo a una propiedad nueva.

    Devuelve {"cluster_id", "cluster_name", "cluster_profile"}; levanta
    InputValidationError si la entrada no es válida.
    """
    return get_model().predict_cluster(property_data)
