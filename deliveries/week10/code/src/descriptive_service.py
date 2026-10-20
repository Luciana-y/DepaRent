"""Servicio descriptivo integrado de Week 10: RF1 (perfil competitivo + comparables) y RF2 (accesibilidad ATU).

Flujo: validación -> normalización -> perfil competitivo -> comparables -> accesibilidad.
La respuesta es JSON-serializable. No incluye predicción de precio, BCRP, forecasting
ni recomendaciones: solo describe la propiedad frente a anuncios reales del dataset.
"""
from src import accessibility, comparables
from src.input_validation import InputValidationError, validate_coordinates

SCOPE_NOTE = (
    "Resultado descriptivo. No es una estimación ni recomendación de precio: los precios mostrados "
    "son los publicados en los anuncios comparables (precios de oferta, no de cierre)."
)


def analyze_descriptive(property_data, n_comparables=5, exclude_ids=None):
    """Analiza una propiedad nueva.

    property_data: dict con distrito, area_total, dormitorios, banos, amenidades (lista),
    latitud, longitud y opcionalmente antiguedad y mantenimiento.
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
    if errors:
        raise InputValidationError(errors)

    cid, frame = model.predict_validated(prop)
    query_vector = model.scaled_space.transform(frame)[0]
    comp = comp_index.query(prop, cid, query_vector, n=n_comparables, exclude_ids=exclude_ids)
    access = acc_index.get_accessibility(*coords)

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
        "derived": {"imputed_for_profile": imputed, "grupo_distrital": prep.district_to_group_[prop["distrito"]]},
        "competitive_profile": model.describe(cid),
        "comparables": comp["comparables"],
        "comparables_method": {k: v for k, v in comp.items() if k != "comparables"},
        "accessibility": access,
        "warnings": warnings,
        "meta": {
            "scope": SCOPE_NOTE,
            "clustering": {
                "k": meta["k_selected"],
                "silhouette": meta["silhouette"],
                "trained_at_utc": meta["trained_at_utc"],
                "source": meta["source"]["path"],
                "source_sha256": meta["source"]["sha256"],
            },
        },
    }
