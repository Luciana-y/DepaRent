import json

import pytest

from conftest import row_to_property
from src.descriptive_service import analyze_descriptive
from src.input_validation import InputValidationError

FULL = {
    "distrito": "Miraflores", "area_total": 85, "dormitorios": 2, "banos": 2, "antiguedad": 5,
    "mantenimiento": 350, "amenidades": ["ascensor", "gimnasio", "piscina"],
    "latitud": -12.1211, "longitud": -77.0297,
}


def test_full_property_json_serializable():
    out = analyze_descriptive(FULL)
    json.dumps(out, allow_nan=False)
    assert {"competitive_profile", "comparables", "accessibility", "warnings", "meta"} <= set(out)
    assert len(out["comparables"]) == 5
    assert out["competitive_profile"]["cluster_name"]
    assert out["accessibility"]["dist_paradero_min_m"] >= 0
    assert not any("precio" in k for k in out["input"]) and not any("precio" in k for k in out["derived"])


def test_missing_optional_fields_produce_warning():
    data = {k: v for k, v in FULL.items() if k != "mantenimiento"}
    out = analyze_descriptive(data)
    assert "mantenimiento" in out["derived"]["imputed_for_profile"]
    assert any("mantenimiento" in w for w in out["warnings"])


def test_real_properties(representative_rows):
    for row in representative_rows:
        out = analyze_descriptive(row_to_property(row), exclude_ids=[row["id_anuncio"]])
        json.dumps(out, allow_nan=False)
        assert row["id_anuncio"] not in [c["id_anuncio"] for c in out["comparables"]]


def test_errors_from_rf1_and_rf2_reported_together():
    bad = dict(FULL, area_total=5000, latitud=None)
    with pytest.raises(InputValidationError) as exc:
        analyze_descriptive(bad)
    assert len(exc.value.errors) == 2
    assert any("area_total" in e for e in exc.value.errors)
    assert any("latitud" in e for e in exc.value.errors)


@pytest.mark.parametrize("bad", [None, [], "Miraflores"])
def test_non_dict_input(bad):
    with pytest.raises(InputValidationError):
        analyze_descriptive(bad)
