import sys
from pathlib import Path

import numpy as np
import pytest

CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

from src.clustering import FEATURES, get_model, load_training_frame  # noqa: E402
from src import examples  # noqa: E402


def row_to_property(row, with_location=True):
    """Fila real del dataset -> diccionario de entrada del contrato (sin precio)."""
    prop = examples.row_to_property(row)
    if not with_location:
        prop.pop("latitud")
        prop.pop("longitud")
    return prop


@pytest.fixture(scope="session")
def model():
    return get_model()


@pytest.fixture(scope="session")
def training_frame():
    return load_training_frame()


@pytest.fixture(scope="session")
def representative_rows(model, training_frame):
    """Para cada cluster, el anuncio real más cercano a su centroide (con banos informado)."""
    df = training_frame.dropna(subset=["banos"])
    X = model.scaled_space.transform(df[["distrito", "distrito_norm"] + FEATURES])
    labels = model.pipeline.predict(df[["distrito", "distrito_norm"] + FEATURES])
    centers = model.pipeline.named_steps["kmeans"].cluster_centers_
    rows = []
    for cid in range(len(centers)):
        idx = np.flatnonzero(labels == cid)
        best = idx[np.argmin(np.linalg.norm(X[idx] - centers[cid], axis=1))]
        rows.append(df.iloc[best])
    return rows
