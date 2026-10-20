import sys

import pytest

import app as app_module
from conftest import CODE_DIR, row_to_property
from src.clustering import get_model

VALID = {
    "distrito": "Miraflores", "area_total": 85, "dormitorios": 2, "banos": 2, "antiguedad": 5,
    "mantenimiento": 350, "amenidades": ["ascensor", "gimnasio"], "latitud": -12.1211, "longitud": -77.0297,
}
DESCRIPTIVE_PRICE_KEYS = {"precio_soles_observado", "precio_m2_real_observado"}
SUMMARY_PRICE_KEYS = {"mediana_precio_publicado", "minimo_precio_publicado", "maximo_precio_publicado",
                      "mediana_precio_publicado_m2", "n_con_precio_publicado"}
PREDICTIVE_FRAGMENTS = ["estimat", "estimad", "predic", "predict", "forecast", "recomend", "recommend", "esperado",
                        "expected", "rent"]


@pytest.fixture(scope="module")
def client():
    return app_module.create_app().test_client()


def _all_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{path}.{k}", k
            yield from _all_keys(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for v in obj:
            yield from _all_keys(v, f"{path}[]")


def test_index_renders_form_with_supported_districts(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Analizar inmueble" in html
    for d in get_model().known_districts:
        assert f'<option value="{d}">' in html
    for word in ["Predecir", "precio esperado", "Precio estimado", "Precio recomendado"]:
        assert word.lower() not in html.lower()


def test_static_assets_served(client):
    assert client.get("/static/css/styles.css").status_code == 200
    assert client.get("/static/js/app.js").status_code == 200


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_analyze_valid_property(client):
    resp = client.post("/analyze", json=VALID)
    assert resp.status_code == 200
    body = resp.get_json()
    assert {"competitive_profile", "comparables", "accessibility", "warnings"} <= set(body)
    assert len(body["comparables"]) == 5
    assert body["competitive_profile"]["cluster_name"]


def test_analyze_one_case_per_cluster(client, representative_rows):
    seen = set()
    for row in representative_rows:
        resp = client.post("/analyze", json=row_to_property(row))
        assert resp.status_code == 200
        seen.add(resp.get_json()["competitive_profile"]["cluster_id"])
    assert seen == {0, 1, 2}


def test_no_price_prediction_fields(client):
    body = client.post("/analyze", json=VALID).get_json()
    for path, key in _all_keys(body):
        low = key.lower()
        assert not any(f in low for f in PREDICTIVE_FRAGMENTS), path
        if "precio" in low:
            # Solo se permiten precios publicados observados de los comparables y su resumen descriptivo.
            assert (path.startswith(".comparables[].") and key in DESCRIPTIVE_PRICE_KEYS) or (
                path.startswith(".comparables_summary.") and key in SUMMARY_PRICE_KEYS), path


def test_comparable_prices_are_observed_listing_prices(client, training_frame):
    body = client.post("/analyze", json=VALID).get_json()
    observed = training_frame.set_index("id_anuncio")["precio_soles"]
    for c in body["comparables"]:
        assert c["precio_soles_observado"] == pytest.approx(float(observed[c["id_anuncio"]]))
    assert "precio_soles" not in body["comparables_method"]["similarity_features"]


@pytest.mark.parametrize("change", [
    {"area_total": 5000},
    {"dormitorios": "dos"},
    {"amenidades": "ascensor"},
    {"banos": None},
])
def test_analyze_invalid_returns_400(client, change):
    resp = client.post("/analyze", json=dict(VALID, **change))
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"] == "validation_error"
    assert isinstance(body["details"], list) and body["details"]


def test_invalid_district_explicit_error(client):
    resp = client.post("/analyze", json=dict(VALID, distrito="Narnia"))
    assert resp.status_code == 400
    assert any("Narnia" in d and "sin cobertura" in d for d in resp.get_json()["details"])


@pytest.mark.parametrize("lat, lon", [(-16.40, -71.54), (None, -77.03), ("-12.1", -77.03)])
def test_invalid_coordinates(client, lat, lon):
    resp = client.post("/analyze", json=dict(VALID, latitud=lat, longitud=lon))
    assert resp.status_code == 400
    assert any("latitud" in d or "longitud" in d for d in resp.get_json()["details"])


@pytest.mark.parametrize("payload", [None, "texto", [1, 2]])
def test_non_object_body_returns_400(client, payload):
    if payload is None:
        resp = client.post("/analyze", data="no es json", content_type="application/json")
    else:
        resp = client.post("/analyze", json=payload)
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "validation_error"


def test_unexpected_error_returns_generic_500(monkeypatch):
    def boom(_):
        raise RuntimeError("detalle interno secreto")

    monkeypatch.setattr(app_module, "analyze_descriptive", boom)
    resp = app_module.create_app().test_client().post("/analyze", json=VALID)
    assert resp.status_code == 500
    text = resp.get_data(as_text=True)
    assert resp.get_json()["error"] == "internal_error"
    assert "secreto" not in text and "Traceback" not in text


def test_old_estimator_placeholder_not_used(client):
    assert not (CODE_DIR / "inference.py").exists()
    assert "inference" not in sys.modules
    source = (CODE_DIR / "app.py").read_text(encoding="utf-8")
    assert "Estimator" not in source and "inference" not in source
    assert client.post("/predict", json={"distrito": "Lince"}).status_code == 404


def test_debug_not_hardcoded():
    source = (CODE_DIR / "app.py").read_text(encoding="utf-8")
    assert "debug=True" not in source
