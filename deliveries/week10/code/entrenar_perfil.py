"""Entrena el modelo 1 (perfil competitivo) y guarda el artefacto y sus métricas.

No toca el modelo de precio del profesor (models/modelo_docente.joblib).
Uso, desde deliveries/week10/code:  python entrenar_perfil.py
"""
import json
import platform

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

from modelo import ROOT, SOURCE
from perfil_competitivo import (ARCHIVO, K, SEMILLA, VARIABLES, construir_pipeline, nombrar_perfiles,
                                preparar_referencia, resumen_perfiles)


def main():
    frame = pd.read_csv(SOURCE, low_memory=False)
    ref = preparar_referencia(frame)
    X = ref[VARIABLES]
    # Selección de k: silhouette y estabilidad entre semillas para k = 2..7.
    seleccion = []
    for k in range(2, 8):
        pipe = construir_pipeline(k).fit(X)
        Z = pipe[:-1].transform(X)
        etiquetas = pipe.named_steps["kmeans"].labels_
        ari = [adjusted_rand_score(etiquetas, KMeans(k, random_state=s, n_init=10).fit_predict(Z)) for s in (1, 2, 3)]
        seleccion.append({"k": k, "silhouette": float(silhouette_score(Z, etiquetas)),
                          "ari_medio_semillas": float(np.mean(ari)), "tamanos": np.bincount(etiquetas).tolist()})
    pipe = construir_pipeline(K).fit(X)
    etiquetas = pipe.named_steps["kmeans"].labels_
    ref["cluster"] = etiquetas
    resumen = resumen_perfiles(ref, etiquetas)
    nombres = nombrar_perfiles(resumen)
    elegido = next(s for s in seleccion if s["k"] == K)
    metricas = {
        "modelo": "K-Means sobre variables estandarizadas, sin precio", "k": K, "semilla": SEMILLA,
        "variables": VARIABLES, "filas": len(ref),
        "silhouette": elegido["silhouette"], "ari_medio_semillas": elegido["ari_medio_semillas"],
        "seleccion_k": seleccion,
        "justificacion_k": "k=4 tiene el mayor silhouette entre 2 y 7, es estable (ARI ~1) y mantiene los 4 perfiles del diseño.",
        "referencia_semana7": "K-Means k=4 con 19 variables que incluían precio por m²: silhouette 0.1776.",
        "perfiles": {nombres[c]: {k: (round(float(v), 3)) for k, v in fila.items()} for c, fila in resumen.iterrows()},
        "entorno": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                    "numpy": np.__version__, "pandas": pd.__version__, "joblib": joblib.__version__},
        "limites": ["Silhouette bajo: segmentación heurística.",
                    "El perfil 'Moderno que admite mascotas' queda definido casi solo por pet_friendly.",
                    "Amenidades extraídas del texto de los anuncios con reglas; pueden tener errores."],
    }
    artifact = {"pipeline": pipe, "nombres": nombres, "resumen": resumen, "referencia": ref, "metricas": metricas}
    ARCHIVO.parent.mkdir(exist_ok=True)
    joblib.dump(artifact, ARCHIVO)
    (ROOT / "resultados").mkdir(exist_ok=True)
    (ROOT / "resultados/metricas_perfil.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: metricas[k] for k in ("k", "silhouette", "ari_medio_semillas", "perfiles")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
