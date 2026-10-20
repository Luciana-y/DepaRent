import copy

import numpy as np
import pytest

from conftest import row_to_property
from src.clustering import FEATURES, PRICE_COLUMNS, predict_cluster
from src.input_validation import AMENITIES, InputValidationError

VALID = {
    "distrito": "Lince", "area_total": 70, "dormitorios": 2, "banos": 2,
    "antiguedad": 8, "mantenimiento": 250, "amenidades": ["ascensor"],
}


def test_model_loads_with_metadata(model):
    meta = model.metadata
    for key in ["source", "trained_at_utc", "n_observations", "features", "excluded_features", "imputation",
                "scaling", "k_selected", "silhouette", "cluster_sizes", "cluster_pcts", "random_state", "versions"]:
        assert key in meta
    assert set(meta["versions"]) == {"python", "numpy", "pandas", "scipy", "scikit-learn", "joblib"}
    assert len(meta["source"]["sha256"]) == 64
    assert set(model.names) == set(range(meta["k_selected"]))


def test_no_price_in_clustering_features(model):
    assert not set(FEATURES) & set(PRICE_COLUMNS)
    assert "cochera" not in FEATURES
    assert list(model.pipeline.named_steps["prep"].get_feature_names_out()) == FEATURES
    assert model.pipeline.named_steps["scaler"].n_features_in_ == len(FEATURES)


def test_predict_cluster_output():
    out = predict_cluster(VALID)
    assert set(out) == {"cluster_id", "cluster_name", "cluster_profile"}
    assert isinstance(out["cluster_id"], int)
    assert isinstance(out["cluster_name"], str) and out["cluster_name"]
    assert {"n", "pct", "area_total", "amenidades_pct"} <= set(out["cluster_profile"])


def test_training_labels_reproduced(model, training_frame):
    X = training_frame[["distrito", "distrito_norm"] + FEATURES]
    assert np.array_equal(model.pipeline.predict(X), model.pipeline.named_steps["kmeans"].labels_)


def test_real_property_gets_its_training_cluster(model, training_frame, representative_rows):
    labels = model.pipeline.named_steps["kmeans"].labels_
    for row in representative_rows:
        expected = labels[training_frame.index.get_loc(row.name)]
        assert predict_cluster(row_to_property(row, with_location=False))["cluster_id"] == expected


def test_missing_optional_uses_persisted_medians(model):
    prep = model.pipeline.named_steps["prep"]
    before = copy.deepcopy((prep.group_medians_, prep.global_medians_, prep.banos_mode_by_dorm_))
    without = {k: v for k, v in VALID.items() if k not in ("antiguedad", "mantenimiento")}
    explicit = dict(without, antiguedad=prep.group_medians_["antiguedad"]["Lince"],
                    mantenimiento=prep.group_medians_["mantenimiento"]["Lince"])
    assert predict_cluster(without)["cluster_id"] == predict_cluster(explicit)["cluster_id"]
    assert (prep.group_medians_, prep.global_medians_, prep.banos_mode_by_dorm_) == before


def test_district_aliases_normalized(model):
    assert model.validate(dict(VALID, distrito="  santiago de surco "))["distrito"] == "Surco"
    assert model.validate(dict(VALID, distrito="JESÚS MARÍA"))["distrito"] == "Jesus Maria"


@pytest.mark.parametrize("change, fragment", [
    ({"area_total": None}, "'area_total' es obligatorio"),
    ({"area_total": "70"}, "debe ser numérico"),
    ({"area_total": 10}, "fuera del rango"),
    ({"dormitorios": 2.5}, "entero"),
    ({"banos": True}, "debe ser numérico"),
    ({"mantenimiento": float("nan")}, "NaN"),
    ({"distrito": "Narnia"}, "sin cobertura"),
    ({"amenidades": ["jacuzzi"]}, "no reconocidas"),
    ({"amenidades": None}, "'amenidades' es obligatorio"),
])
def test_invalid_inputs_raise_explicit_errors(change, fragment):
    with pytest.raises(InputValidationError) as exc:
        predict_cluster(dict(VALID, **change))
    assert any(fragment in e for e in exc.value.errors)


def test_all_errors_reported_together():
    with pytest.raises(InputValidationError) as exc:
        predict_cluster({"distrito": "Lince", "area_total": -1, "dormitorios": "dos", "banos": 2, "amenidades": []})
    assert len(exc.value.errors) == 2


def test_amenities_list_maps_to_all_flags(model):
    prop = model.validate(dict(VALID, amenidades=[]))
    assert prop["amenidades"] == {a: 0 for a in AMENITIES}
