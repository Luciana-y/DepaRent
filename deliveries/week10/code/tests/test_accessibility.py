import numpy as np
import pandas as pd
import pytest

from config import find_data_file
from src.accessibility import get_accessibility, get_index
from src.input_validation import InputValidationError

EXPECTED_KEYS = {
    "dist_paradero_min_m", "paradero_cercano_tipo", "paradero_cercano_afluencia", "paradero_cercano_nombre",
    "paraderos_300m", "paraderos_500m", "paraderos_1000m", "dist_troncal_brt_m", "dist_corredor_m", "fuente",
}


def test_valid_coordinates():
    out = get_accessibility(-12.085, -77.035)
    assert set(out) == EXPECTED_KEYS
    assert out["dist_paradero_min_m"] >= 0
    assert 0 <= out["paraderos_300m"] <= out["paraderos_500m"] <= out["paraderos_1000m"]
    assert out["paradero_cercano_tipo"] in {"Transporte Regular", "Alimentador", "Corredor", "Troncal"}
    assert out["fuente"]["n_paraderos"] == 3233


def test_index_built_once():
    assert get_index() is get_index()


def test_matches_canonical_week07_features():
    """Recalcular RF2 para los 3,128 departamentos reproduce exactamente las columnas de Week 7."""
    df = pd.read_csv(find_data_file("departamentos_procesados.csv"), low_memory=False)
    out = get_index().compute_many(df["latitud"], df["longitud"])
    for col in ["dist_paradero_min_m", "paraderos_300m", "paraderos_500m", "paraderos_1000m",
                "dist_troncal_brt_m", "dist_corredor_m"]:
        assert np.array_equal(out[col].to_numpy(), df[col].to_numpy()), col
    for col in ["paradero_cercano_tipo", "paradero_cercano_afluencia"]:
        assert (out[col].to_numpy() == df[col].to_numpy()).all(), col


@pytest.mark.parametrize("lat, lon", [
    (-16.40, -71.54),            # Arequipa: fuera de Lima/Callao
    (-12.08, -70.0),
    (float("nan"), -77.03),
    (None, -77.03),
    ("-12.08", -77.03),
    (True, -77.03),
    (-12.08, float("inf")),
])
def test_invalid_coordinates(lat, lon):
    with pytest.raises(InputValidationError):
        get_accessibility(lat, lon)
