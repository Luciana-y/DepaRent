"""Búsqueda para inquilinos: anuncios de mercado y departamentos publicados en DepaRent.

Cada resultado se compara con el precio que estima el modelo 3 para sus características.
Muchos anuncios de mercado se usaron para entrenar ese modelo, así que la comparación es orientativa.
"""
import numpy as np
import pandas as pd

from modelo import BINARY, SOURCE, normalizar, preparar

ORDENES = {"precio": ("precio_soles", True), "precio_desc": ("precio_soles", False), "area": ("area_total", False),
           "paradero": ("dist_paradero_min_m", True), "oportunidad": ("relacion_estimado", True)}
UMBRAL_VALORACION = 0.10
VALORACIONES = {"por_debajo": "Por debajo del estimado", "en_linea": "En línea con el estimado",
                "por_encima": "Por encima del estimado"}
AVISO = ("Anuncios de septiembre de 2026 sin dirección ni contacto: es una muestra del mercado, no una lista de ofertas vigentes. "
         "La comparación con el precio estimado es orientativa: muchos de estos anuncios se usaron para entrenar el modelo.")


def valoracion(relacion):
    if relacion < 1 - UMBRAL_VALORACION:
        return "Por debajo del estimado"
    if relacion > 1 + UMBRAL_VALORACION:
        return "Por encima del estimado"
    return "En línea con el estimado"


def construir_mercado(modelo_precio, modelo_perfil):
    """Tabla de anuncios de mercado, un registro por posible inmueble (se quitan duplicados entre portales)."""
    frame = pd.read_csv(SOURCE, low_memory=False)
    X = preparar(frame)
    ref = modelo_perfil["referencia"]
    tabla = X.copy()
    tabla["id"] = ["m" + str(i) for i in range(len(frame))]
    tabla["origen"] = "Anuncio de mercado (sep. 2026)"
    tabla["nombre"] = None
    tabla["precio_soles"] = pd.to_numeric(frame["precio_soles"], errors="coerce").to_numpy()
    tabla["dist_paradero_min_m"] = frame["dist_paradero_min_m"].to_numpy()
    tabla["paraderos_500m"] = frame["paraderos_500m"].to_numpy()
    tabla["perfil"] = ref["cluster"].map(modelo_perfil["nombres"]).to_numpy()
    tabla["precio_estimado"] = modelo_precio["pipeline"].predict(X)
    tabla["grupo"] = ref["grupo"].to_numpy()
    return tabla.drop_duplicates("grupo").drop(columns="grupo").reset_index(drop=True)


def filtrar(tabla, filtros):
    mascara = pd.Series(True, index=tabla.index)
    distritos = [normalizar(d) for d in filtros.get("distritos") or []]
    if distritos:
        mascara &= tabla["distrito_norm"].isin(distritos)
    for campo, columna, operador in (("precio_min", "precio_soles", "ge"), ("precio_max", "precio_soles", "le"),
                                     ("area_min", "area_total", "ge"), ("area_max", "area_total", "le"),
                                     ("dormitorios_min", "dormitorios", "ge"), ("banos_min", "banos", "ge"),
                                     ("paradero_max_m", "dist_paradero_min_m", "le")):
        valor = filtros.get(campo)
        if valor is not None:
            mascara &= getattr(tabla[columna], operador)(float(valor))
    for amenidad in filtros.get("amenidades") or []:
        if amenidad not in BINARY:
            raise ValueError(f"Amenidad desconocida: {amenidad}.")
        mascara &= tabla[amenidad] == 1
    return tabla[mascara]


def buscar(mercado, propios, filtros, limite=24):
    """mercado: construir_mercado(); propios: DataFrame con las mismas columnas para los publicados en DepaRent."""
    orden = filtros.get("orden") or "precio"
    if orden not in ORDENES:
        raise ValueError("Orden de resultados no válido.")
    tabla = pd.concat([propios, mercado], ignore_index=True) if len(propios) else mercado
    tabla = tabla.assign(relacion_estimado=tabla["precio_soles"] / tabla["precio_estimado"])
    encontrados = filtrar(tabla, filtros)
    grupos = encontrados["relacion_estimado"].map(valoracion)
    # Conteos de la vista filtrada, antes de elegir un grupo: alimentan las tarjetas que filtran.
    conteos = {clave: int((grupos == etiqueta).sum()) for clave, etiqueta in VALORACIONES.items()}
    elegido = filtros.get("valoracion")
    if elegido:
        if elegido not in VALORACIONES:
            raise ValueError("Valoración no válida.")
        encontrados = encontrados[grupos == VALORACIONES[elegido]]
    columna, ascendente = ORDENES[orden]
    # Los publicados en DepaRent van primero; dentro de cada grupo se respeta el orden elegido.
    encontrados = encontrados.assign(_propio=encontrados["origen"] != "Publicado en DepaRent").sort_values(
        ["_propio", columna], ascending=[True, ascendente], na_position="last")
    precios = encontrados["precio_soles"].to_numpy(float)
    resumen = None
    if len(encontrados):
        resumen = {"precio_p25_soles": float(np.percentile(precios, 25)), "precio_mediana_soles": float(np.median(precios)),
                   "precio_p75_soles": float(np.percentile(precios, 75)),
                   "por_debajo_del_estimado": int((encontrados["relacion_estimado"] < 1 - UMBRAL_VALORACION).sum())}
    resultados = [formatear(fila) for fila in encontrados.head(limite).to_dict("records")]
    return {"total": int(len(encontrados)), "conteos": conteos, "resumen": resumen, "resultados": resultados, "aviso": AVISO}


CAMPOS_VIVIENDA = ["distrito_norm", "area_total", "dormitorios", "banos", "estacionamientos", "antiguedad", "mantenimiento", *BINARY]


def formatear(fila):
    """Un anuncio como lo ve el inquilino: sin dirección, coordenadas, URL ni texto del anuncio original."""
    relacion = fila["precio_soles"] / fila["precio_estimado"]
    return {
        "id": fila["id"], "origen": fila["origen"], "nombre": fila["nombre"],
        "distrito": fila["distrito_norm"], "precio_soles": round(float(fila["precio_soles"]), 2),
        "precio_estimado_soles": round(float(fila["precio_estimado"]), 2),
        "valoracion": valoracion(relacion),
        "diferencia_estimado_porcentaje": round(100 * (relacion - 1), 1),
        **{c: fila[c] for c in ("area_total", "dormitorios", "banos", "estacionamientos", "antiguedad", "mantenimiento",
                                "dist_paradero_min_m", "paraderos_500m", "perfil")},
        "amenidades": [a for a in BINARY if fila[a] == 1],
    }


def ubicar(mercado, propios, anuncio_id):
    """Fila del anuncio por su id ("m123" de mercado o "d4" publicado en DepaRent), o None."""
    for tabla in (propios, mercado):
        if len(tabla):
            encontrada = tabla[tabla["id"] == anuncio_id]
            if len(encontrada):
                return encontrada.iloc[0].to_dict()
    return None


def vivienda_de(fila):
    """Las entradas del modelo a partir de una fila de la tabla de búsqueda."""
    return {c: (None if pd.isna(fila[c]) else (int(fila[c]) if c != "distrito_norm" and float(fila[c]).is_integer() else fila[c]))
            for c in CAMPOS_VIVIENDA}
