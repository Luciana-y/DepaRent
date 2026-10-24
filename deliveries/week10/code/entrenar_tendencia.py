"""Entrena el modelo 4 (tendencia distrital, SARIMA) y guarda sus pronósticos.

Para cada serie trimestral del BCRP (12 distritos y el promedio):
1. Reserva los últimos 4 trimestres y elige el orden SARIMA por AIC con el resto.
2. Compara ese pronóstico contra dos baselines: naive estacional (mismo trimestre del año anterior) y naive (último valor).
3. Reajusta con la serie completa y pronostica 4 trimestres con intervalo de 80%.
Las series cambian solo con una nueva publicación del BCRP, así que la app consulta este archivo en vez de reajustar.
Uso, desde deliveries/week10/code:  python entrenar_tendencia.py   (escribe resultados/tendencia_distrital.json)
"""
import itertools
import json
import platform
import warnings

import numpy as np
import pandas as pd
import statsmodels
from statsmodels.tsa.statespace.sarimax import SARIMAX

from modelo import ROOT, normalizar
from tendencia import ARCHIVO, HORIZONTE, clasificar_tendencia

SERIES = ROOT.parent / "week07/data/bcrp_serie_completa.csv"
VALIDACION = 4
ORDENES = [((p, 1, q), (P, D, Q, 4)) for p, q, P, D, Q in itertools.product((0, 1), (0, 1), (0, 1), (0, 1), (0, 1))]


def _ajustar(y, orden, estacional):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return SARIMAX(y, order=orden, seasonal_order=estacional, trend="n",
                       enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)


def elegir_orden(y):
    candidatos = []
    for orden, estacional in ORDENES:
        try:
            ajuste = _ajustar(y, orden, estacional)
        except (ValueError, np.linalg.LinAlgError):
            continue
        if np.isfinite(ajuste.aic):
            candidatos.append((ajuste.aic, orden, estacional))
    aic, orden, estacional = min(candidatos, key=lambda c: c[0])
    return orden, estacional, float(aic)


def _metricas(real, pred):
    real, pred = np.asarray(real, float), np.asarray(pred, float)
    return {"MAE": float(np.mean(np.abs(real - pred))), "MAPE_porcentaje": float(np.mean(np.abs(real - pred) / real) * 100)}


def trimestres_siguientes(ultimo, n):
    anio, trimestre = int(ultimo[:4]), int(ultimo[-1])
    salida = []
    for _ in range(n):
        anio, trimestre = (anio + 1, 1) if trimestre == 4 else (anio, trimestre + 1)
        salida.append(f"{anio}-T{trimestre}")
    return salida


def main():
    datos = pd.read_csv(SERIES).sort_values(["Distrito", "Trimestre"])
    resultado = {}
    for distrito, serie in datos.groupby("Distrito"):
        y = serie["Alquiler_Mensual_Soles"].to_numpy(float)
        trimestres = serie["Trimestre"].tolist()
        entrenamiento, prueba = y[:-VALIDACION], y[-VALIDACION:]
        orden, estacional, aic = elegir_orden(entrenamiento)
        pred_sarima = _ajustar(entrenamiento, orden, estacional).forecast(VALIDACION)
        pred_estacional = entrenamiento[-4:][:VALIDACION]
        pred_naive = np.repeat(entrenamiento[-1], VALIDACION)
        validacion = {"trimestres": trimestres[-VALIDACION:], "SARIMA": _metricas(prueba, pred_sarima),
                      "naive_estacional": _metricas(prueba, pred_estacional), "naive": _metricas(prueba, pred_naive)}
        validacion["sarima_supera_naive_estacional"] = validacion["SARIMA"]["MAE"] < validacion["naive_estacional"]["MAE"]
        validacion["sarima_supera_naive"] = validacion["SARIMA"]["MAE"] < validacion["naive"]["MAE"]
        final = _ajustar(y, orden, estacional)
        pronostico = final.get_forecast(HORIZONTE)
        media, intervalo = pronostico.predicted_mean, pronostico.conf_int(alpha=0.20)
        futuros = trimestres_siguientes(trimestres[-1], HORIZONTE)
        resultado[normalizar(distrito)] = {
            "distrito": distrito, "orden": list(orden), "orden_estacional": list(estacional), "aic_entrenamiento": aic,
            "historia": [{"trimestre": t, "valor": round(float(v), 4)} for t, v in zip(trimestres, y)],
            "pronostico": [{"trimestre": t, "valor": round(float(m), 4), "inferior_80": round(float(lo), 4),
                            "superior_80": round(float(hi), 4)} for t, m, (lo, hi) in zip(futuros, media, intervalo)],
            "validacion": validacion,
            **clasificar_tendencia(y[-4:], media),
        }
    supera = sum(r["validacion"]["sarima_supera_naive_estacional"] for r in resultado.values())
    supera_naive = sum(r["validacion"]["sarima_supera_naive"] for r in resultado.values())
    salida = {
        "fecha": pd.Timestamp.today().strftime("%Y-%m-%d"),
        "fuente": "BCRP, series trimestrales 2013-T3 a 2026-T1; Alquiler_Mensual_Soles = precio de venta × tipo de cambio ÷ PER ÷ 12 (S/ por m²)",
        "metodo": "SARIMA (p,1,q)(P,D,Q,4) con orden elegido por AIC sobre los primeros 47 trimestres",
        "validacion": f"Últimos {VALIDACION} trimestres reservados; SARIMA supera al naive estacional en {supera} y al naive (último valor) en {supera_naive} de {len(resultado)} series",
        "regla_tendencia": "Cambio entre el promedio pronosticado de 4 trimestres y el promedio de los últimos 4 observados: más de +2% al alza, menos de -2% a la baja; si no, estable",
        "entorno": {"python": platform.python_version(), "statsmodels": statsmodels.__version__},
        "limites": ["La serie es derivada del precio de venta y el PER; no es alquiler observado en anuncios.",
                    "Solo 12 distritos tienen serie propia; los demás usan el promedio.",
                    "Validación con 4 trimestres: poca evidencia para comparar métodos."],
        "series": resultado,
    }
    ARCHIVO.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    tabla = pd.DataFrame([{"serie": r["distrito"], "orden": f"{tuple(r['orden'])}{tuple(r['orden_estacional'])}",
                           "MAPE_SARIMA": r["validacion"]["SARIMA"]["MAPE_porcentaje"],
                           "MAPE_naive_est": r["validacion"]["naive_estacional"]["MAPE_porcentaje"],
                           "MAPE_naive": r["validacion"]["naive"]["MAPE_porcentaje"],
                           "cambio_%": r["cambio_porcentaje"], "tendencia": r["tendencia"]} for r in resultado.values()])
    print(tabla.round(2).to_string(index=False))
    print(salida["validacion"])


if __name__ == "__main__":
    main()
