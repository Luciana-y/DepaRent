"""Validación temporal: el modelo de precio congelado (entrenado con septiembre) frente a anuncios de octubre.

Responde la limitación declarada del modelo: "no valida períodos futuros". No reentrena nada.

1. Toma la captura diaria más reciente que esté completa (data_diaria/snapshots, fuera de git).
2. La procesa con las mismas reglas de la Semana 7 (preprocesar.py) y los distritos con que se entrenó.
3. Quita los anuncios que ya estaban en septiembre y sus posibles duplicados (misma heurística de grupos
   que separó entrenamiento y prueba), y deja un anuncio por posible inmueble.
4. Mide error, cobertura del rango calibrado, baselines y error por distrito, y los compara con la prueba de septiembre.

Uso, desde deliveries/week10/code:  python validar_octubre.py [--captura AAAA-MM-DD]
Escribe resultados/validacion_octubre/ sin ids, direcciones ni textos de los anuncios.
"""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error, r2_score

from escenarios import verificar_modelo_congelado
from modelo import ROOT, SOURCE, grupos_inmueble, normalizar, preparar
from preprocesar import elegir_captura, procesar

CRUDO_SEPTIEMBRE = ROOT.parent / "week04/data/departamentos_alquiler_lima.csv"
SALIDA = ROOT / "resultados/validacion_octubre"
MINIMO_DISTRITO = 20    # el mismo umbral orientativo de la evidencia por distrito
SEMILLA = 42


def metricas(y, pred):
    return {"MAE_soles": float(mean_absolute_error(y, pred)), "RMSE_soles": float(np.sqrt(mean_squared_error(y, pred))),
            "MAPE_porcentaje": float(mean_absolute_percentage_error(y, pred) * 100), "R2": float(r2_score(y, pred))}


def intervalo_bootstrap(errores, n=2000, semilla=SEMILLA):
    """IC del 95% del error absoluto medio, remuestreando anuncios."""
    rng = np.random.default_rng(semilla)
    medias = rng.choice(errores, size=(n, len(errores)), replace=True).mean(axis=1)
    return [float(np.percentile(medias, 2.5)), float(np.percentile(medias, 97.5))]


def main():
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--captura", help="fecha AAAA-MM-DD de la captura; por defecto la más reciente completa")
    archivo = elegir_captura(argumentos.parse_args().captura)

    verificar_modelo_congelado()
    artefacto = joblib.load(ROOT / "models/modelo_docente.joblib")
    metricas_septiembre = json.loads((ROOT / "resultados/metricas.json").read_text(encoding="utf-8"))
    error_septiembre = pd.read_csv(ROOT / "resultados/error_por_distrito.csv").set_index("distrito")

    crudo = pd.read_csv(archivo, low_memory=False)
    octubre = procesar(crudo, distritos_conocidos=artefacto["distritos"], alias_portal=True)
    septiembre = pd.read_csv(SOURCE, low_memory=False)
    ids_septiembre = set(pd.read_csv(CRUDO_SEPTIEMBRE, usecols=["id_anuncio"])["id_anuncio"].astype(str))

    # Sin fuga: fuera los anuncios vistos en septiembre y cualquiera que la heurística una a uno de ellos.
    nuevos = octubre[~octubre["id_anuncio"].astype(str).isin(ids_septiembre)].reset_index(drop=True)
    juntos = pd.concat([septiembre.assign(_origen="sep"), nuevos.assign(_origen="oct")], ignore_index=True)
    grupos = grupos_inmueble(juntos)
    grupos_septiembre = set(grupos[(juntos["_origen"] == "sep").to_numpy()])
    grupos_octubre = grupos[(juntos["_origen"] == "oct").to_numpy()]
    nuevos = nuevos.assign(_grupo=grupos_octubre)
    sin_cruce = nuevos[~nuevos["_grupo"].isin(grupos_septiembre)]
    evaluados = sin_cruce.drop_duplicates("_grupo").reset_index(drop=True)

    y = evaluados["precio_soles"].to_numpy(float)
    X = preparar(evaluados)
    pred = artefacto["pipeline"].predict(X)
    radio = float(artefacto["radio_calibrado_soles"])
    errores = np.abs(y - pred)
    distrito = X["distrito_norm"]
    base_distrital = distrito.map(artefacto["medianas_distrito"]).fillna(artefacto["mediana_global"]).to_numpy(float)
    base_global = np.full(len(y), float(artefacto["mediana_global"]))
    mae_sep = metricas_septiembre["metricas_prueba"]["HistGradientBoosting"]["MAE_soles"]

    por_distrito = []
    for d, idx in pd.Series(range(len(y))).groupby(distrito.to_numpy()):
        e = errores[idx.to_numpy()]
        sep = error_septiembre.loc[d] if d in error_septiembre.index else None
        por_distrito.append({"distrito": d, "n_octubre": len(e), "MAE_octubre": float(e.mean()),
                             "MAPE_octubre": float(np.mean(e / y[idx.to_numpy()]) * 100),
                             "n_septiembre": int(sep["n"]) if sep is not None else 0,
                             "MAE_septiembre": float(sep["MAE_soles"]) if sep is not None else None,
                             "muestra_pequena": bool(len(e) < MINIMO_DISTRITO or (sep is None or sep["n"] < MINIMO_DISTRITO))})
    por_distrito = pd.DataFrame(por_distrito).sort_values("n_octubre", ascending=False)

    # Sensibilidad: excluir solo por id (sin la heurística, que puede unir viviendas distintas del mismo edificio).
    solo_id = nuevos.drop_duplicates("_grupo").reset_index(drop=True)
    y_id = solo_id["precio_soles"].to_numpy(float)
    pred_id = artefacto["pipeline"].predict(preparar(solo_id))

    resultado = {
        "captura": archivo.name.replace(".csv.gz", ""),
        "modelo": "modelo_docente.joblib, congelado (hashes verificados), entrenado con la captura del 14-sep-2026",
        "flujo": {"anuncios_en_captura": len(crudo), "validos_tras_preprocesar": len(octubre),
                  "ya_estaban_en_septiembre_por_id": int(len(octubre) - (~octubre["id_anuncio"].astype(str).isin(ids_septiembre)).sum()),
                  "posibles_duplicados_de_septiembre": int(len(nuevos) - len(sin_cruce)),
                  "duplicados_dentro_de_octubre": int(len(sin_cruce) - len(evaluados)),
                  "evaluados": len(evaluados)},
        "metricas_octubre": {"HistGradientBoosting": metricas(y, pred), "mediana_distrital": metricas(y, base_distrital),
                             "mediana_global": metricas(y, base_global)},
        "metricas_septiembre_prueba": metricas_septiembre["metricas_prueba"],
        "MAE_octubre_IC95": intervalo_bootstrap(errores),
        "sensibilidad_excluyendo_solo_por_id": {"evaluados": len(solo_id), **metricas(y_id, pred_id),
                                                "cobertura": float(np.mean(np.abs(y_id - pred_id) <= radio))},
        "cambio_MAE_porcentaje": float((errores.mean() / mae_sep - 1) * 100),
        "intervalo": {"radio_soles": radio, "nivel_nominal": 0.90,
                      "cobertura_octubre": float(np.mean(errores <= radio)),
                      "cobertura_septiembre_prueba": metricas_septiembre["intervalo"]["cobertura_observada_prueba"]},
        "sesgo": {"mediana_real_menos_estimado_soles": float(np.median(y - pred)),
                  "porcentaje_por_encima_del_estimado": float(np.mean(y > pred) * 100)},
        "limites": ["Precios pedidos, no de contrato.",
                    "Una captura de octubre (5-6 semanas después del entrenamiento): mide un desfase corto, no estacionalidad.",
                    "La heurística de duplicados puede omitir republicaciones con otro texto o unir viviendas distintas.",
                    "La captura puede tener páginas faltantes por bloqueos del portal (error 403)."],
    }
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "metricas.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    por_distrito.to_csv(SALIDA / "error_por_distrito.csv", index=False)
    pd.DataFrame({"distrito": distrito, "real_soles": y, "prediccion_soles": pred.round(2),
                  "baseline_distrital_soles": base_distrital}).to_csv(SALIDA / "predicciones.csv", index=False)

    m, s = resultado["metricas_octubre"]["HistGradientBoosting"], metricas_septiembre["metricas_prueba"]["HistGradientBoosting"]
    print(f"Captura {resultado['captura']}: {resultado['flujo']}")
    print(f"MAE   octubre S/ {m['MAE_soles']:,.2f} (IC95 {resultado['MAE_octubre_IC95'][0]:,.0f}-{resultado['MAE_octubre_IC95'][1]:,.0f}) | septiembre S/ {s['MAE_soles']:,.2f}")
    print(f"MAPE  octubre {m['MAPE_porcentaje']:.2f}% | septiembre {s['MAPE_porcentaje']:.2f}%")
    print(f"R2    octubre {m['R2']:.4f} | septiembre {s['R2']:.4f}")
    print(f"Cobertura del rango de 90%: octubre {resultado['intervalo']['cobertura_octubre']:.1%} | septiembre {resultado['intervalo']['cobertura_septiembre_prueba']:.1%}")
    b = resultado["metricas_octubre"]
    print(f"Baselines octubre: mediana distrital MAE S/ {b['mediana_distrital']['MAE_soles']:,.2f} · global S/ {b['mediana_global']['MAE_soles']:,.2f}")
    v = resultado["sensibilidad_excluyendo_solo_por_id"]
    print(f"Sensibilidad (solo por id, {v['evaluados']} anuncios): MAE S/ {v['MAE_soles']:,.2f} · MAPE {v['MAPE_porcentaje']:.2f}% · R2 {v['R2']:.4f} · cobertura {v['cobertura']:.1%}")
    print(f"Sesgo: mediana (real - estimado) S/ {resultado['sesgo']['mediana_real_menos_estimado_soles']:,.2f}; {resultado['sesgo']['porcentaje_por_encima_del_estimado']:.1f}% por encima")
    print(por_distrito.round(1).to_string(index=False))


if __name__ == "__main__":
    main()
