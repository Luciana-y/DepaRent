"""Entrenamiento reproducible y evaluación reservada de un MVP educativo."""
import hashlib
import json
import math
import platform
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from modelo import ROOT, SOURCE, NUMERIC, FEATURES, preparar, grupos_inmueble, construir_pipeline, predecir

def metrics(y, pred):
    return {"MAE_soles": float(mean_absolute_error(y, pred)),
            "RMSE_soles": float(np.sqrt(mean_squared_error(y, pred))),
            "MAPE_porcentaje": float(mean_absolute_percentage_error(y, pred) * 100),
            "R2": float(r2_score(y, pred))}

def main():
    original = pd.read_csv(SOURCE, low_memory=False)
    # El procesamiento original ya aplicó filtros documentados. Solo verificamos contrato.
    target = pd.to_numeric(original["precio_soles"], errors="coerce")
    area = pd.to_numeric(original["area_total"], errors="coerce")
    frame = original.loc[target.between(800, 25000) & area.between(25, 450)].copy().reset_index(drop=True)
    X, y = preparar(frame), frame["precio_soles"].astype(float)
    groups = grupos_inmueble(frame)
    development, test = next(GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=42).split(X, y, groups))
    fit_local, calibration_local = next(GroupShuffleSplit(n_splits=1, test_size=0.20, random_state=43).split(
        X.iloc[development], y.iloc[development], groups[development]))
    fit, calibration = development[fit_local], development[calibration_local]
    assert not set(groups[fit]) & set(groups[test])
    assert not set(groups[fit]) & set(groups[calibration])
    assert not set(groups[test]) & set(groups[calibration])
    model = construir_pipeline().fit(X.iloc[fit], y.iloc[fit])
    cal_errors = np.sort(np.abs(y.iloc[calibration].to_numpy() - model.predict(X.iloc[calibration])))
    level = 0.90
    rank = min(len(cal_errors), math.ceil((len(cal_errors) + 1) * level))
    radius = float(cal_errors[rank - 1])
    training = X.iloc[fit].assign(target=y.iloc[fit].to_numpy())
    medians = training.groupby("distrito_norm")["target"].median().to_dict()
    global_median = float(y.iloc[fit].median())
    district_baseline = X.iloc[test]["distrito_norm"].map(medians).fillna(global_median).to_numpy()
    prediction = model.predict(X.iloc[test])
    lower, upper = np.maximum(0, prediction - radius), prediction + radius
    result = {
        "fecha": "2026-10-18", "version": "docente-1",
        "commit_fuente": "fb81bb32c20c14185feaf4caa486fa99ef3570e9",
        "sha256_datos_fuente": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "filas_originales": len(original), "filas_utilizadas": len(frame),
        "grupos_posibles_inmuebles": int(len(np.unique(groups))),
        "filas_en_grupos_multiples": int(pd.Series(groups).duplicated(keep=False).sum()),
        "particiones": {"entrenamiento": len(fit), "calibracion": len(calibration), "prueba": len(test)},
        "interseccion_grupos": 0, "semillas": {"prueba": 42, "calibracion": 43},
        "features": FEATURES, "seleccion_modelo": "HistGradientBoosting fijado antes de evaluar, sin tuning",
        "metricas_prueba": {"mediana_global": metrics(y.iloc[test], np.full(len(test), global_median)),
                            "mediana_distrital": metrics(y.iloc[test], district_baseline),
                            "HistGradientBoosting": metrics(y.iloc[test], prediction)},
        "intervalo": {"metodo": "Residuos absolutos en calibración separada; radio global constante",
                      "nivel_nominal": level, "radio_soles": radius,
                      "cobertura_observada_prueba": float(np.mean((y.iloc[test] >= lower) & (y.iloc[test] <= upper))),
                      "ancho_medio_soles": float(np.mean(upper - lower))},
        "entorno": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "sklearn": sklearn.__version__, "joblib": joblib.__version__},
        "limites": ["Holdout agrupado de captura única; no valida períodos futuros.",
                    "Grupos heurísticos pueden omitir duplicados o unir viviendas diferentes.",
                    "Intervalo global; cobertura por subgrupo o futura no garantizada.",
                    "Precio de anuncio y atributos extraídos por alumnos; no precio de contrato.",
                    "Evaluación distinta del notebook original; las métricas no son una comparación directa."]}
    artifact = {"pipeline": model, "radio_calibrado_soles": radius,
                "medianas_distrito": medians, "mediana_global": global_median,
                "distritos": sorted(medians), "conteos_distrito": training.groupby("distrito_norm").size().to_dict(),
                "rangos_entrenamiento": {c: [float(X.iloc[fit][c].min()), float(X.iloc[fit][c].max())] for c in NUMERIC},
                "metricas": result}
    (ROOT / "models").mkdir(exist_ok=True)
    (ROOT / "resultados").mkdir(exist_ok=True)
    joblib.dump(artifact, ROOT / "models/modelo_docente.joblib")
    (ROOT / "resultados/metricas.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    predictions = pd.DataFrame({"fila_fuente": test, "grupo": groups[test], "distrito": X.iloc[test]["distrito_norm"].to_numpy(),
                                "real_soles": y.iloc[test].to_numpy(), "prediccion_soles": prediction,
                                "baseline_distrital_soles": district_baseline, "inferior_soles": lower, "superior_soles": upper})
    predictions.to_csv(ROOT / "resultados/predicciones_prueba.csv", index=False)
    partition = np.full(len(frame), "", dtype=object)
    partition[fit], partition[calibration], partition[test] = "entrenamiento", "calibracion", "prueba"
    pd.DataFrame({"fila_fuente": np.arange(len(frame)), "grupo": groups, "particion": partition}).to_csv(ROOT / "resultados/particiones.csv", index=False)
    segment_metrics = []
    for district, rows in predictions.groupby("distrito"):
        segment_metrics.append({"distrito": district, "n": len(rows),
                                "MAE_soles": float(np.abs(rows.real_soles - rows.prediccion_soles).mean()),
                                "MAPE_porcentaje": float((np.abs(rows.real_soles - rows.prediccion_soles) / rows.real_soles).mean() * 100)})
    pd.DataFrame(segment_metrics).to_csv(ROOT / "resultados/error_por_distrito.csv", index=False)
    demos = json.loads((ROOT / "data/demo_casos.json").read_text(encoding="utf-8"))
    for demo in demos:
        demo["resultado"] = predecir(demo["entrada"], artifact)
    (ROOT / "resultados/demos_ejecutadas.json").write_text(json.dumps(demos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
