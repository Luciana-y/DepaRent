"""RF1 — Propiedades comparables.

Similitud = distancia euclidiana en el mismo espacio estandarizado del clustering
(FEATURES, sin precio). El precio de los comparables solo se muestra como dato observado.

Estrategia:
1. candidatos del mismo cluster que la propiedad consultada;
2. si hay al menos `n` candidatos del mismo distrito, se eligen solo entre ellos;
3. si no, se toman todos los del mismo distrito y se completa con los más cercanos del
   mismo cluster en otros distritos (cada resultado indica `mismo_distrito`);
4. dentro de cada grupo se ordena por distancia (empates por id_anuncio).
"""
from functools import lru_cache

import numpy as np

from src.clustering import FEATURES, PRICE_COLUMNS, get_model, load_training_frame
from src.input_validation import AMENITIES

STRATEGY_DISTRICT = "mismo_cluster_mismo_distrito"
STRATEGY_EXPANDED = "mismo_cluster_ampliado_a_otros_distritos"
SOURCE_LABELS = {"adondevivir": "Adondevivir", "urbania": "Urbania"}


def source_label(fuente):
    """Nombre del portal de origen para mostrar (valor de la columna `fuente`)."""
    return SOURCE_LABELS.get(str(fuente).lower(), str(fuente).title())


def _clean(value):
    """NaN -> None y tipos numpy -> tipos nativos (salida JSON-serializable)."""
    if value is None:
        return None
    if isinstance(value, (np.floating, float)):
        return None if np.isnan(value) else round(float(value), 2)
    if isinstance(value, np.integer):
        return int(value)
    return value


class ComparablesIndex:
    def __init__(self, model=None):
        self.model = model or get_model()
        assert not set(FEATURES) & set(PRICE_COLUMNS), "Una variable de precio está en el espacio de similitud"
        df = load_training_frame(self.model.data_path)
        X_input = df[["distrito", "distrito_norm"] + FEATURES]
        self.X = self.model.scaled_space.transform(X_input)
        self.labels = self.model.pipeline.predict(X_input)
        if not np.array_equal(self.labels, self.model.pipeline.named_steps["kmeans"].labels_):
            raise ValueError("Las etiquetas recalculadas no coinciden con las del entrenamiento")
        self.ids = df["id_anuncio"].to_numpy()
        self.districts = df["distrito"].to_numpy()
        self.records = df.reset_index(drop=True)
        self.dataset_info = {
            "properties_reference_count": int(len(self.records)),
            "source_type": "anuncios inmobiliarios",
            "sources": sorted({source_label(f) for f in self.records["fuente"].dropna()}),
            "listings_by_source": {source_label(k): int(v) for k, v in self.records["fuente"].value_counts().items()},
            "capture_dates": sorted({str(f)[:10] for f in self.records["fecha_scraping"].dropna()}),
            "file": self.model.metadata["source"]["path"],
            "sha256": self.model.metadata["source"]["sha256"],
            "price_type": "precio publicado de oferta (no precio de transacción)",
        }

    def _item(self, i, distance, same_district):
        r = self.records.iloc[i]
        return {
            "id_anuncio": int(r["id_anuncio"]),
            "fuente": source_label(r["fuente"]),
            "url": r["url"],
            "fecha_scraping": r["fecha_scraping"],
            "distrito": r["distrito"],
            "area_total": _clean(r["area_total"]),
            "dormitorios": None if np.isnan(r["dormitorios"]) else int(r["dormitorios"]),
            "banos": None if np.isnan(r["banos"]) else int(r["banos"]),
            "antiguedad": _clean(r["antiguedad"]),
            "mantenimiento": _clean(r["mantenimiento"]),
            "amenidades": [a for a in AMENITIES if r[a] == 1],
            "precio_soles_observado": _clean(r["precio_soles"]),
            "precio_m2_real_observado": _clean(r["precio_m2_real"]),
            "distancia_similitud": round(float(distance), 4),
            "mismo_distrito": bool(same_district),
        }

    def query(self, prop, cid, query_vector, n=5, exclude_ids=None):
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise ValueError("n debe ser un entero >= 1")
        exclude = set(exclude_ids or [])
        cand = np.flatnonzero((self.labels == cid) & ~np.isin(self.ids, list(exclude)))
        dist = np.linalg.norm(self.X[cand] - query_vector, axis=1)
        if not np.isfinite(dist).all():
            raise ValueError("Distancias no finitas en el espacio de similitud")
        same = self.districts[cand] == prop["distrito"]
        order_same = cand[same][np.lexsort((self.ids[cand][same], dist[same]))]
        order_other = cand[~same][np.lexsort((self.ids[cand][~same], dist[~same]))]
        dist_by_idx = dict(zip(cand, dist))
        if same.sum() >= n:
            strategy, chosen = STRATEGY_DISTRICT, list(order_same[:n])
        else:
            strategy = STRATEGY_EXPANDED
            chosen = list(order_same) + list(order_other[: n - same.sum()])
        return {
            "cluster_id": int(cid),
            "strategy": strategy,
            "distrito_consultado": prop["distrito"],
            "candidatos_cluster": int(cand.size),
            "candidatos_mismo_distrito": int(same.sum()),
            "similarity_features": list(FEATURES),
            "comparables": [self._item(i, dist_by_idx[i], self.districts[i] == prop["distrito"]) for i in chosen],
        }

    def get_comparables(self, property_data, n=5, exclude_ids=None):
        prop = self.model.validate(property_data)
        cid, frame = self.model.predict_validated(prop)
        q = self.model.scaled_space.transform(frame)[0]
        return self.query(prop, cid, q, n=n, exclude_ids=exclude_ids)


@lru_cache(maxsize=1)
def get_index():
    return ComparablesIndex()


def get_comparables(property_data, n=5, exclude_ids=None):
    """Top-n propiedades comparables (mismo cluster, prioridad al mismo distrito).

    `exclude_ids` permite excluir anuncios (p. ej. la propia propiedad si proviene del dataset).
    """
    return get_index().get_comparables(property_data, n=n, exclude_ids=exclude_ids)
