"""Preprocesamiento de anuncios crudos con las mismas reglas del notebook de la Semana 7.

Recibe una captura con las 43 columnas de week04 (la de septiembre o una descarga diaria de
data_diaria/) y devuelve las columnas que usan los modelos. Se valida reproduciendo
week07/data/departamentos_procesados.csv a partir de la captura cruda de septiembre.

Solo cubre lo que necesita el modelo de precio; los cruces con el BCRP y la ATU quedan en el notebook.
"""
import numpy as np
import pandas as pd

from modelo import normalizar

AMENITY_KEYWORDS = {
    "ascensor": ["ascensor", "elevador", "ascensores"],
    "balcon": ["balcón", "balcon", "balcones"],
    "terraza": ["terraza", "terrazas", "rooftop", "azotea"],
    "piscina": ["piscina", "piscinas", "alberca"],
    "gimnasio": ["gimnasio", "gym", "fitness"],
    "deposito": ["depósito", "deposito", "storage"],
    "vista_al_mar": ["vista al mar", "frente al mar", "malecón", "malecon"],
    "parrilla": ["parrilla", "bbq", "zona de parrilla"],
    "areas_verdes": ["áreas verdes", "areas verdes", "jardín", "jardin"],
    "seguridad_24_7": ["seguridad", "vigilancia", "guardianía", "portería", "recepción 24"],
    "coworking": ["coworking", "co-working", "business center", "sala de reuniones"],
    "juegos_infantiles": ["juegos para niños", "kids zone", "área de juegos", "juegos infantiles"],
    "pet_friendly": ["pet friendly", "mascotas", "pet zone", "admite mascotas"],
}
AMENITY_NEGATIONS = {
    "pet_friendly": r"no\s+se\s+(?:aceptan?|admiten?|permiten?)\s+mascotas|\b(?:no|sin)\s+(?:(?:aceptan?|admiten?|permiten?)\s+)?(?:mascotas|pets?)\b|mascotas\s*:?\s*no\b",
}
DISTRITO_MAP = {"Santiago de Surco": "Surco", "Magdalena del Mar": "Magdalena", "Jesús María": "Jesus Maria",
                "Cercado de Lima": "Lima", "Barranca": "Barranco"}
UMBRAL_OTROS = 20


def recuperar_del_texto(df):
    """Completa piso, antigüedad, estacionamientos y mantenimiento desde el texto del anuncio (Semana 7, celda 10)."""
    if "texto_amenidades_crudo" not in df.columns:
        df["texto_amenidades_crudo"] = df["titulo"].fillna("") + " | " + df["descripcion"].fillna("") + " | " + df["caracteristicas"].fillna("")
    corpus = df["texto_amenidades_crudo"].fillna("").str.lower().str.replace("º", "").str.replace("°", "")
    ext_piso = corpus.str.extract(r"(?:piso|nivel)\s*(\d{1,2})|(\d{1,2})\s*(?:er|do|ro|to|mo|vo|no)?\.?\s*piso")
    piso = ext_piso[0].fillna(ext_piso[1]).astype(float)
    df["piso"] = df["piso"].fillna(piso.where((piso >= 1) & (piso <= 45)))
    ant = corpus.str.extract(r"(\d{1,2})\s*a[nñ]os?\s*(?:de\s*)?antig[uü]edad")[0].astype(float)
    estreno = corpus.str.contains(r"\b(?:estreno|a estrenar|de estreno)\b", regex=True)
    df["antiguedad"] = df["antiguedad"].fillna(ant.fillna(estreno.map({True: 0.0})))
    est = corpus.str.extract(r"(\d{1,2})\s*(?:cocheras?|estacionamientos?|garajes?|parqueos?)")[0].astype(float)
    con_cochera = corpus.str.contains(r"\b(?:con cochera|incluye cochera|1 cochera|cochera techada|cochera incluida)\b", regex=True)
    df["estacionamientos"] = df["estacionamientos"].fillna(est.fillna(con_cochera.map({True: 1.0})))
    mant = corpus.str.extract(r"(?:mantenimiento|mant\.?|cuota)\s*(?:aprox\.?|es\s*de|de)?\s*(?:s\/?\.?|soles|\$)?\s*(\d{2,4})")[0].astype(float)
    df["mantenimiento"] = df["mantenimiento"].fillna(mant.where((mant >= 50) & (mant <= 2500)))
    return df


def extraer_amenidades(df):
    """Amenidades por palabras clave, con las negaciones de pet_friendly (Semana 7, celda 13)."""
    texto = df["texto_amenidades_crudo"].fillna("").str.lower()
    for col, palabras in AMENITY_KEYWORDS.items():
        if df[col].isna().all():
            df[col] = texto.apply(lambda t, kws=palabras: 1 if any(k in t for k in kws) else 0)
            if col in AMENITY_NEGATIONS:
                df.loc[texto.str.contains(AMENITY_NEGATIONS[col], regex=True), col] = 0
    if "cochera" not in df.columns or df["cochera"].isna().all():
        df["cochera"] = np.where(df["estacionamientos"].notna(), (df["estacionamientos"] > 0).astype(int), np.nan)
    return df


def procesar(crudo, distritos_conocidos=None):
    """Captura cruda → filas válidas con las columnas del modelo.

    distritos_conocidos: distritos con los que se entrenó el modelo (en minúsculas o con su nombre).
    Con una captura nueva se pasan siempre: los demás van a "Otros", como en el entrenamiento.
    Sin ellos se recalcula el umbral de 20 anuncios, que es lo que hizo la Semana 7 con septiembre.
    """
    df = recuperar_del_texto(crudo.copy())
    df = extraer_amenidades(df)
    for col in ["antiguedad", "mantenimiento", "estacionamientos", "banos", "area_construida"]:
        df[f"{col}_imputado"] = df[col].isna().astype(int)
    # Anuncios de venta y alquiler: el precio capturado es de venta (Semana 7, celda 19).
    doble_modalidad = df["titulo"].str.lower().str.contains(r"\b(?:venta|vendo|se vende)\b", regex=True, na=False)
    valido = (df["precio_soles"].notna() & df["precio_soles"].between(800, 25000)
              & df["area_total"].notna() & df["area_total"].between(25, 450)
              & df["latitud"].notna() & df["longitud"].notna()
              & df["latitud"].between(-12.35, -11.75) & df["longitud"].between(-77.20, -76.80)
              & ~doble_modalidad)
    limpio = df[valido].copy()
    limpio["distrito_norm"] = limpio["distrito"].str.strip().map(lambda x: DISTRITO_MAP.get(x, x))
    if distritos_conocidos is None:
        conteo = limpio["distrito_norm"].value_counts()
        raros = set(conteo[conteo < UMBRAL_OTROS].index)
        limpio["distrito_norm"] = limpio["distrito_norm"].where(~limpio["distrito_norm"].isin(raros), "Otros")
    else:
        # La misma normalización del modelo (minúsculas y sin tildes): "San Martín de Porres" es "san martin de porres".
        conocidos = {normalizar(d) for d in distritos_conocidos}
        limpio["distrito_norm"] = limpio["distrito_norm"].where(limpio["distrito_norm"].map(normalizar).isin(conocidos), "Otros")
    limpio["area_construida"] = limpio["area_construida"].fillna(limpio["area_total"])
    limpio["precio_m2_real"] = np.round(limpio["precio_soles"] / limpio["area_total"], 2)
    return limpio.reset_index(drop=True)
