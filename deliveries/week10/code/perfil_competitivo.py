"""Modelo 1: perfil competitivo (K-Means) y departamentos comparables (vecinos cercanos).

El clustering usa solo lo que el propietario conoce antes de publicar: no usa precio
ni precio por m². El precio de los anuncios solo describe cada perfil y los comparables.
Entrenar:  python entrenar_perfil.py   (escribe models/perfil_competitivo.joblib)
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from modelo import ROOT, BINARY, preparar, normalizar, grupos_inmueble

ARCHIVO = ROOT / "models/perfil_competitivo.joblib"
# estacionamientos queda fuera, como en la Semana 7: el 89% de sus nulos es ambiguo.
NUMERICAS = ["area_total", "dormitorios", "banos", "antiguedad", "mantenimiento"]
VARIABLES = NUMERICAS + BINARY
K = 4
SEMILLA = 42
AVISO = ("Los perfiles son una segmentación heurística (silhouette bajo): ayudan a elegir con quién compararse, "
         "no son grupos naturalmente separados. Los comparables son anuncios de septiembre de 2026 con precio pedido, no contratos.")


def construir_pipeline(k=K, semilla=SEMILLA):
    pre = ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), NUMERICAS),
        ("bin", SimpleImputer(strategy="most_frequent"), BINARY),
    ])
    return Pipeline([("preparacion", pre), ("escala", StandardScaler()),
                     ("kmeans", KMeans(n_clusters=k, random_state=semilla, n_init=10))])


def nombrar_perfiles(resumen):
    """Nombres por reglas sobre el resumen de cada cluster, para que no dependan del número asignado."""
    nombres, libres = {}, set(resumen.index)
    for nombre, columna in (("Amplio de alta gama", "area_total"), ("Moderno que admite mascotas", "pet_friendly"),
                            ("Compacto moderno con amenidades", "gimnasio")):
        elegido = resumen.loc[sorted(libres), columna].idxmax()
        nombres[int(elegido)] = nombre
        libres.discard(elegido)
    for resto in libres:
        nombres[int(resto)] = "Estándar tradicional"
    return nombres


def preparar_referencia(frame):
    """Columnas que se conservan de los anuncios: sin dirección, coordenadas, URL ni descripción."""
    X = preparar(frame)
    ref = X[["distrito_norm"] + VARIABLES].copy()
    ref["precio_soles"] = pd.to_numeric(frame["precio_soles"], errors="coerce").to_numpy()
    ref["precio_m2"] = pd.to_numeric(frame["precio_m2_real"], errors="coerce").to_numpy()
    ref["grupo"] = grupos_inmueble(frame)
    # Id de la ficha del anuncio (el id del portal): sirve para enlazar cada comparable.
    ref["anuncio_id"] = ("m" + frame["id_anuncio"].astype(str)).to_numpy()
    return ref.reset_index(drop=True)


def resumen_perfiles(ref, etiquetas):
    datos = ref.assign(cluster=etiquetas)
    resumen = datos.groupby("cluster").agg(
        anuncios=("precio_soles", "size"),
        **{c: (c, "median") for c in NUMERICAS},
        **{c: (c, "mean") for c in BINARY},
        precio_p25=("precio_soles", lambda s: s.quantile(0.25)),
        precio_mediana=("precio_soles", "median"),
        precio_p75=("precio_soles", lambda s: s.quantile(0.75)),
        precio_m2_mediana=("precio_m2", "median"))
    return resumen


def _entrada_df(values):
    return preparar(pd.DataFrame([values]))[VARIABLES]


def asignar_perfil(values, artifact):
    X = _entrada_df(values)
    cluster = int(artifact["pipeline"].predict(X)[0])
    fila = artifact["resumen"].loc[cluster]
    return {"cluster": cluster, "perfil": artifact["nombres"][cluster],
            "anuncios_en_perfil": int(fila["anuncios"]),
            "precio_mediana_perfil_soles": round(float(fila["precio_mediana"]), 2),
            "precio_p25_perfil_soles": round(float(fila["precio_p25"]), 2),
            "precio_p75_perfil_soles": round(float(fila["precio_p75"]), 2)}


def _espacio(artifact, X):
    pipe = artifact["pipeline"]
    return pipe.named_steps["escala"].transform(pipe.named_steps["preparacion"].transform(X))


def comparables(values, artifact, k=8, excluir=None):
    """k anuncios más parecidos: mismo perfil y distrito primero; un anuncio por posible inmueble.
    excluir: id de ficha ("m...") del anuncio que no debe compararse consigo mismo ni con sus duplicados."""
    perfil = asignar_perfil(values, artifact)
    ref = artifact["referencia"]
    if "_Z" not in artifact:
        artifact["_Z"] = _espacio(artifact, ref[VARIABLES])
    z = _espacio(artifact, _entrada_df(values))[0]
    distrito = normalizar(values.get("distrito_norm"))
    candidatos = ref.assign(distancia=np.linalg.norm(artifact["_Z"] - z, axis=1),
                            mismo_perfil=ref["cluster"] == perfil["cluster"],
                            mismo_distrito=ref["distrito_norm"] == distrito)
    # Orden: mismo distrito y perfil, luego mismo distrito, luego mismo perfil en otros distritos.
    candidatos["prioridad"] = np.select([candidatos.mismo_distrito & candidatos.mismo_perfil, candidatos.mismo_distrito,
                                         candidatos.mismo_perfil], [0, 1, 2], 3)
    if excluir is not None:
        propios = ref.loc[ref["anuncio_id"] == excluir, "grupo"]
        candidatos = candidatos[~candidatos["grupo"].isin(propios)]
    elegidos = (candidatos.sort_values(["prioridad", "distancia"]).drop_duplicates("grupo").head(k))
    tabla = [{"anuncio_id": r.anuncio_id,
              "Distrito": r.distrito_norm.title(), "Perfil": artifact["nombres"][int(r.cluster)],
              "Área (m²)": r.area_total, "Dormitorios": r.dormitorios, "Baños": r.banos,
              "Antigüedad": r.antiguedad, "Mantenimiento (S/)": r.mantenimiento,
              "Precio pedido (S/)": r.precio_soles, "S/ por m²": round(r.precio_m2, 2),
              "Similitud": round(float(1 / (1 + r.distancia)), 3)} for r in elegidos.itertuples()]
    precios = elegidos["precio_soles"].to_numpy(float)
    return {"perfil": perfil, "comparables": tabla,
            "en_mismo_distrito": int(elegidos["mismo_distrito"].sum()),
            "precio_p25_soles": round(float(np.percentile(precios, 25)), 2),
            "precio_mediana_soles": round(float(np.median(precios)), 2),
            "precio_p75_soles": round(float(np.percentile(precios, 75)), 2),
            "aviso": AVISO}
