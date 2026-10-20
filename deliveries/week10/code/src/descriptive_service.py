"""Servicio descriptivo integrado de Week 10: RF1 (perfil competitivo + comparables) y RF2 (accesibilidad ATU).

Flujo: validación -> normalización -> perfil competitivo -> posición frente al segmento ->
comparables (+ resumen de sus precios publicados) -> accesibilidad.
La respuesta es JSON-serializable. No incluye predicción de precio, BCRP, forecasting
ni recomendaciones: solo describe la propiedad frente a anuncios reales del dataset.
"""
import math
from statistics import median

from src import accessibility, comparables
from src.clustering import NUMERIC_FEATURES
from src.examples import row_to_property
from src.input_validation import InputValidationError, validate_coordinates

SCOPE_NOTE = (
    "Resultado descriptivo. No es una estimación ni recomendación de precio: los precios mostrados "
    "son los publicados en los anuncios comparables (precios de oferta, no de cierre)."
)
PRICE_SUMMARY_NOTE = (
    "Estas estadísticas resumen únicamente los precios publicados de los anuncios comparables recuperados "
    "y no constituyen una estimación del precio del inmueble analizado."
)


def _resolve_origin(origin, comp_index, errors):
    """Fila del dataset indicada por `id_anuncio_origen` (caso real), o None si es ingreso manual."""
    if origin is None:
        return None
    if not isinstance(origin, int) or isinstance(origin, bool):
        errors.append("'id_anuncio_origen' debe ser un entero (identificador del anuncio del dataset)")
        return None
    matches = comp_index.records.index[comp_index.records["id_anuncio"] == origin]
    if len(matches) == 0:
        errors.append(f"'id_anuncio_origen'={origin} no existe en el dataset de referencia")
        return None
    return comp_index.records.loc[matches[0]]


def _check_origin_consistency(row, prop, coords, model):
    """Un caso real solo es válido si los valores enviados son los de su fila en el CSV."""
    expected = row_to_property(row)
    exp_prop = model.validate(expected)
    diffs = []
    for key in ["distrito", "dormitorios", "banos"]:
        if prop[key] != exp_prop[key]:
            diffs.append(key)
    for key in ["area_total", "antiguedad", "mantenimiento"]:
        a, b = prop[key], exp_prop[key]
        if (a is None) != (b is None) or (a is not None and not math.isclose(a, b)):
            diffs.append(key)
    if prop["amenidades"] != exp_prop["amenidades"]:
        diffs.append("amenidades")
    if not (math.isclose(coords[0], expected["latitud"]) and math.isclose(coords[1], expected["longitud"])):
        diffs.append("latitud/longitud")
    if diffs:
        raise InputValidationError([
            f"los valores enviados no coinciden con el anuncio {int(row['id_anuncio'])} del dataset "
            f"({', '.join(diffs)}); para un ingreso manual no envíe 'id_anuncio_origen'"
        ])


def _segment_comparison(prop, imputed, profile):
    numeric = []
    for col in NUMERIC_FEATURES:
        seg = profile[col]
        numeric.append({
            "variable": col,
            "inmueble": prop[col],
            "imputado_para_perfil": imputed.get(col),
            "mediana_segmento": seg["mediana"],
            "p25_segmento": seg["p25"],
            "p75_segmento": seg["p75"],
        })
    amenities = [
        {"amenidad": a, "presente_en_inmueble": bool(v), "prevalencia_segmento_pct": profile["amenidades_pct"][a]}
        for a, v in prop["amenidades"].items()
    ]
    return {"numericas": numeric, "amenidades": amenities}


def _price_summary(items):
    prices = [c["precio_soles_observado"] for c in items if c["precio_soles_observado"] is not None]
    per_m2 = [c["precio_m2_real_observado"] for c in items if c["precio_m2_real_observado"] is not None]
    return {
        "n_comparables": len(items),
        "n_con_precio_publicado": len(prices),
        "mediana_precio_publicado": round(median(prices), 2) if prices else None,
        "minimo_precio_publicado": min(prices) if prices else None,
        "maximo_precio_publicado": max(prices) if prices else None,
        "mediana_precio_publicado_m2": round(median(per_m2), 2) if per_m2 else None,
        "nota": PRICE_SUMMARY_NOTE,
    }


def analyze_descriptive(property_data, n_comparables=5, exclude_ids=None):
    """Analiza una propiedad.

    property_data: dict con distrito, area_total, dormitorios, banos, amenidades (lista),
    latitud, longitud y opcionalmente antiguedad, mantenimiento e id_anuncio_origen (caso real
    del dataset: sus valores deben coincidir con el CSV y el anuncio se excluye de sus comparables).
    Levanta InputValidationError con todos los problemas de la entrada.
    """
    comp_index = comparables.get_index()
    model = comp_index.model
    acc_index = accessibility.get_index()

    if not isinstance(property_data, dict):
        raise InputValidationError([f"se esperaba un diccionario, se recibió {type(property_data).__name__}"])
    errors = []
    prop = coords = None
    try:
        prop = model.validate(property_data)
    except InputValidationError as e:
        errors.extend(e.errors)
    try:
        coords = validate_coordinates(property_data.get("latitud"), property_data.get("longitud"))
    except InputValidationError as e:
        errors.extend(e.errors)
    origin_row = _resolve_origin(property_data.get("id_anuncio_origen"), comp_index, errors)
    if errors:
        raise InputValidationError(errors)

    exclude = [int(i) for i in (exclude_ids or [])]
    if origin_row is not None:
        _check_origin_consistency(origin_row, prop, coords, model)
        exclude.append(int(origin_row["id_anuncio"]))
        input_source = {
            "type": "dataset",
            "id_anuncio": int(origin_row["id_anuncio"]),
            "fuente": comparables.source_label(origin_row["fuente"]),
            "fecha_scraping": origin_row["fecha_scraping"],
            "url": origin_row["url"],
        }
    else:
        input_source = {"type": "manual"}

    cid, frame = model.predict_validated(prop)
    query_vector = model.scaled_space.transform(frame)[0]
    comp = comp_index.query(prop, cid, query_vector, n=n_comparables, exclude_ids=exclude)
    access = acc_index.get_accessibility(*coords)
    profile = model.describe(cid)

    prep = model.pipeline.named_steps["prep"]
    imputed_row = prep.impute(frame).iloc[0]
    warnings = []
    imputed = {}
    for col in ("antiguedad", "mantenimiento"):
        if prop[col] is None:
            imputed[col] = round(float(imputed_row[col]), 2)
            warnings.append(
                f"'{col}' no informado: para el perfil se usó la mediana de entrenamiento del grupo "
                f"distrital '{prep.district_to_group_[prop['distrito']]}' ({imputed[col]})."
            )
    if comp["strategy"] == comparables.STRATEGY_EXPANDED:
        warnings.append(
            f"Solo {comp['candidatos_mismo_distrito']} comparables del mismo cluster en {prop['distrito']}; "
            "se completó con propiedades del mismo cluster de otros distritos."
        )

    meta = model.metadata
    return {
        "input": {**{k: v for k, v in prop.items() if k != "amenidades"},
                  "amenidades": [a for a, v in prop["amenidades"].items() if v],
                  "latitud": coords[0], "longitud": coords[1]},
        "input_source": input_source,
        "derived": {"imputed_for_profile": imputed, "grupo_distrital": prep.district_to_group_[prop["distrito"]]},
        "competitive_profile": profile,
        "segment_comparison": _segment_comparison(prop, imputed, profile["cluster_profile"]),
        "comparables": comp["comparables"],
        "comparables_summary": _price_summary(comp["comparables"]),
        "comparables_method": {**{k: v for k, v in comp.items() if k != "comparables"},
                               "excluded_ids": exclude},
        "accessibility": access,
        "warnings": warnings,
        "meta": {
            "scope": "descriptive",
            "note": SCOPE_NOTE,
            "dataset": comp_index.dataset_info,
            "clustering": {
                "k": meta["k_selected"],
                "silhouette": meta["silhouette"],
                "trained_at_utc": meta["trained_at_utc"],
                "features": meta["features"],
            },
            "accessibility_source": acc_index.source,
        },
    }
