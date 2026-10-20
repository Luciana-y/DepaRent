"""Casos reales del dataset, estadísticas de perfiles, resumen de precios y procedencia de los datos.

Las verificaciones leen el CSV canónico directamente (sin pasar por el código de producción).
"""
import json
from statistics import median

import numpy as np
import pandas as pd
import pytest

import app as app_module
from conftest import CODE_DIR
from src.clustering import FEATURES, NUMERIC_FEATURES, PRICE_COLUMNS
from src.descriptive_service import analyze_descriptive
from src.examples import get_example_properties
from src.input_validation import AMENITIES, InputValidationError, normalize_district_name

CANONICAL_CSV = CODE_DIR.parents[1] / "week07" / "data" / "departamentos_procesados.csv"
ATU_COLUMNS = ["dist_paradero_min_m", "paraderos_300m", "paraderos_500m", "paraderos_1000m",
               "dist_troncal_brt_m", "dist_corredor_m", "paradero_cercano_tipo"]
PREDICTIVE_FRAGMENTS = ["estimat", "estimad", "predic", "forecast", "recomend", "recommend", "sugerid",
                        "esperado", "expected", "valor"]


@pytest.fixture(scope="module")
def raw():
    return pd.read_csv(CANONICAL_CSV, low_memory=False).set_index("id_anuncio")


@pytest.fixture(scope="module")
def cases():
    return get_example_properties()


@pytest.fixture(scope="module")
def case_results(cases):
    return [analyze_descriptive(dict(c["property"], id_anuncio_origen=c["id_anuncio"])) for c in cases]


def _keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v)


def test_cases_exist_in_canonical_csv(cases, raw):
    assert len(cases) == 3
    for c in cases:
        assert c["id_anuncio"] in raw.index
        assert c["fuente"].lower() == raw.loc[c["id_anuncio"], "fuente"]
        assert c["fecha_scraping"] == raw.loc[c["id_anuncio"], "fecha_scraping"]


def test_case_values_come_from_csv(cases, raw):
    for c in cases:
        row, p = raw.loc[c["id_anuncio"]], c["property"]
        assert p["distrito"] == normalize_district_name(row["distrito"])
        for col in ["area_total", "dormitorios", "banos", "antiguedad", "mantenimiento", "latitud", "longitud"]:
            assert p[col] == pytest.approx(float(row[col])), col
        assert p["amenidades"] == [a for a in AMENITIES if row[a] == 1]
        assert not set(p) & (set(PRICE_COLUMNS) | {"url", "titulo", "descripcion"})


def test_cases_not_hardcoded_in_frontend(cases):
    js = (CODE_DIR / "static" / "js" / "app.js").read_text(encoding="utf-8")
    html = (CODE_DIR / "templates" / "index.html").read_text(encoding="utf-8")
    assert "/api/example-properties" in js
    for c in cases:
        for token in [str(c["id_anuncio"]), str(c["property"]["latitud"]), str(c["property"]["longitud"])]:
            assert token not in js and token not in html


def test_case_selection_is_deterministic_and_documented(model, training_frame, cases):
    """Recalcula la regla documentada: anuncio completo más cercano al centroide de cada cluster."""
    X_in = training_frame[["distrito", "distrito_norm"] + FEATURES]
    X = model.scaled_space.transform(X_in)
    labels = model.pipeline.named_steps["kmeans"].labels_
    complete = training_frame[["banos", "antiguedad", "mantenimiento"]].notna().all(axis=1).to_numpy()
    ids = training_frame["id_anuncio"].to_numpy()
    expected = []
    for cid, center in enumerate(model.pipeline.named_steps["kmeans"].cluster_centers_):
        rows = np.flatnonzero(complete & (labels == cid))
        d = np.linalg.norm(X[rows] - center, axis=1)
        expected.append(int(ids[rows][np.lexsort((ids[rows], d))[0]]))
    assert [c["id_anuncio"] for c in cases] == expected


def test_each_case_runs_full_flow_one_per_cluster(cases, case_results):
    assert {r["competitive_profile"]["cluster_id"] for r in case_results} == {0, 1, 2}
    for c, r in zip(cases, case_results):
        json.dumps(r, allow_nan=False)
        assert r["input_source"]["type"] == "dataset" and r["input_source"]["id_anuncio"] == c["id_anuncio"]
        assert c["id_anuncio"] in r["comparables_method"]["excluded_ids"]
        assert c["id_anuncio"] not in [x["id_anuncio"] for x in r["comparables"]]


def test_comparables_are_real_rows(case_results, raw):
    for r in case_results:
        assert len(r["comparables"]) == 5
        for x in r["comparables"]:
            row = raw.loc[x["id_anuncio"]]
            assert x["url"] == row["url"] and x["fuente"].lower() == row["fuente"]
            assert x["fecha_scraping"] == row["fecha_scraping"]
            assert x["area_total"] == pytest.approx(row["area_total"])
            assert x["precio_soles_observado"] == pytest.approx(row["precio_soles"])
            assert x["precio_m2_real_observado"] == pytest.approx(row["precio_m2_real"])


def test_cluster_statistics_reproducible(model, training_frame):
    labels = model.pipeline.named_steps["kmeans"].labels_
    profiles = model.metadata["cluster_profiles"]
    assert sum(p["n"] for p in profiles.values()) == len(pd.read_csv(CANONICAL_CSV, usecols=["id_anuncio"]))
    for cid, prof in profiles.items():
        part = training_frame[labels == int(cid)]
        assert prof["n"] == len(part)
        assert prof["pct"] == pytest.approx(len(part) / len(training_frame) * 100, abs=0.01)
        for col in NUMERIC_FEATURES:
            s = part[col].dropna()
            assert prof[col]["mediana"] == pytest.approx(s.median())
            assert prof[col]["p25"] == pytest.approx(s.quantile(0.25), abs=0.01)
            assert prof[col]["p75"] == pytest.approx(s.quantile(0.75), abs=0.01)
        for a in AMENITIES:
            assert prof["amenidades_pct"][a] == pytest.approx(part[a].mean() * 100, abs=0.05)


def test_segment_comparison_uses_input_and_profile(case_results):
    for r in case_results:
        prof = r["competitive_profile"]["cluster_profile"]
        for row in r["segment_comparison"]["numericas"]:
            assert row["inmueble"] == r["input"][row["variable"]]
            assert row["mediana_segmento"] == prof[row["variable"]]["mediana"]


def test_price_summary_matches_returned_comparables(case_results):
    for r in case_results:
        prices = [x["precio_soles_observado"] for x in r["comparables"]]
        per_m2 = [x["precio_m2_real_observado"] for x in r["comparables"]]
        s = r["comparables_summary"]
        assert s["n_comparables"] == 5 == s["n_con_precio_publicado"]
        assert s["mediana_precio_publicado"] == pytest.approx(median(prices))
        assert s["minimo_precio_publicado"] == min(prices) and s["maximo_precio_publicado"] == max(prices)
        assert s["mediana_precio_publicado_m2"] == pytest.approx(median(per_m2))
        assert "no constituyen una estimación" in s["nota"]


def test_price_not_used_and_no_predictions(case_results):
    for r in case_results:
        assert not set(r["meta"]["clustering"]["features"]) & set(PRICE_COLUMNS)
        assert not set(r["comparables_method"]["similarity_features"]) & set(PRICE_COLUMNS)
        for k in _keys(r):
            assert not any(f in k.lower() for f in PREDICTIVE_FRAGMENTS), k


def test_rf2_uses_real_coordinates_of_case(cases, case_results, raw):
    for c, r in zip(cases, case_results):
        row = raw.loc[c["id_anuncio"]]
        assert r["input"]["latitud"] == pytest.approx(row["latitud"])
        assert r["input"]["longitud"] == pytest.approx(row["longitud"])
        for col in ATU_COLUMNS:
            assert r["accessibility"][col] == row[col], col


def test_meta_reports_dataset(case_results, raw):
    ds = case_results[0]["meta"]["dataset"]
    assert case_results[0]["meta"]["scope"] == "descriptive"
    assert ds["properties_reference_count"] == len(raw)
    assert ds["sources"] == ["Adondevivir", "Urbania"]
    assert sum(ds["listings_by_source"].values()) == len(raw)
    assert ds["capture_dates"] == sorted({d[:10] for d in raw["fecha_scraping"]})


def test_origin_must_match_csv(cases):
    c = cases[0]
    with pytest.raises(InputValidationError) as exc:
        analyze_descriptive(dict(c["property"], area_total=c["property"]["area_total"] + 10,
                                 id_anuncio_origen=c["id_anuncio"]))
    assert "no coinciden" in exc.value.errors[0] and "area_total" in exc.value.errors[0]


@pytest.mark.parametrize("origin", [999, True, "150419968"])
def test_invalid_origin(cases, origin):
    with pytest.raises(InputValidationError):
        analyze_descriptive(dict(cases[0]["property"], id_anuncio_origen=origin))


def test_manual_input_marked_manual(cases):
    r = analyze_descriptive(cases[0]["property"])
    assert r["input_source"] == {"type": "manual"}


def test_example_endpoint_and_analysis_via_flask(cases):
    client = app_module.create_app().test_client()
    resp = client.get("/api/example-properties")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["cases"] == cases
    for c in body["cases"]:
        assert set(c) == {"case_id", "id_anuncio", "fuente", "fecha_scraping", "property"}
        r = client.post("/analyze", json=dict(c["property"], id_anuncio_origen=c["id_anuncio"]))
        assert r.status_code == 200
        assert r.get_json()["input_source"]["id_anuncio"] == c["id_anuncio"]
