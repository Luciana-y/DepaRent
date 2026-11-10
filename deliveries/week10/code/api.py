"""API del prototipo: componentes analíticos, cuentas de propietarios y búsqueda para inquilinos.

Local (desde deliveries/week10/code):
    python -m uvicorn api:app --port 8000
y abrir http://127.0.0.1:8000 (la API también sirve ../frontend).
En despliegue, DEPARENT_ORIGENES limita qué dominios pueden llamar a la API (por ejemplo, el de Netlify).
"""
import json
import math
import os
import re
from urllib.parse import urlparse
from typing import List, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import cuentas
from accesibilidad import accesibilidad, cargar_red, centro_distrito, nivel_accesibilidad, validar_coordenadas
from ayuda_interfaz import ETIQUETAS, avisos_coherencia
from busqueda import AVISO as AVISO_MERCADO, buscar, construir_mercado, formatear, ubicar, vivienda_de
from escenarios import ADVERTENCIA, CAMBIABLES, comparar, verificar_modelo_congelado
from escenarios_precio import escenarios_publicacion
from direcciones import BusquedaNoDisponible, buscar_direccion, distrito_de
from evidencia_distrital import evidencia_distrital
from laboratorio_area import AVISO as AVISO_AREA, explorar_area
from modelo import BINARY, LIMITS, ROOT, predecir, preparar
from perfil_competitivo import ARCHIVO as ARCHIVO_PERFIL, asignar_perfil, comparables
from tendencia import cargar_tendencias, tendencia_distrital
from recomendador import AVISO as AVISO_RECOMENDADOR, HOGARES, NOMBRES_PRIORIDAD, explicar, recomendar, validar_perfil

verificar_modelo_congelado()
MODELO_PRECIO = joblib.load(ROOT / "models/modelo_docente.joblib")
MODELO_PERFIL = joblib.load(ARCHIVO_PERFIL)
DEMOS = json.loads((ROOT / "data/demo_casos.json").read_text(encoding="utf-8"))
MERCADO = construir_mercado(MODELO_PRECIO, MODELO_PERFIL)
# De qué captura diaria viene el mercado de la app (preparar_mercado.py).
MERCADO_INFO = json.loads((ROOT / "data/mercado.json").read_text(encoding="utf-8"))
# Validación del modelo congelado con anuncios posteriores (validar_octubre.py): la de la captura más reciente
# entre resultados/validacion_*/metricas.json, si ya se corrió alguna.
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_VALIDACIONES = [json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "resultados").glob("validacion_*/metricas.json")]
VALIDACION = max(_VALIDACIONES, key=lambda v: v["captura"]) if _VALIDACIONES else None
MES_VALIDACION = MESES[int(VALIDACION["captura"][5:7]) - 1] if VALIDACION else "octubre"
# Enlace al anuncio original, solo para la ficha de los anuncios de mercado (decisión del equipo).
PORTALES = {"www.adondevivir.com": "Adondevivir", "adondevivir.com": "Adondevivir", "urbania.pe": "Urbania", "www.urbania.pe": "Urbania"}
FRONTEND = ROOT / "frontend"
ORDENES_RECOMENDACION = ("afinidad", "precio", "precio_desc", "paradero")
# Evaluación del recomendador (semana 12), si el repositorio la incluye.
_EVAL_RECOMENDADOR = ROOT.parent / "week12/resultados/recomendador_evaluacion.json"

app = FastAPI(title="DepaRent API", version="0.10")
app.add_middleware(CORSMiddleware, allow_origins=os.environ.get("DEPARENT_ORIGENES", "*").split(","),
                   allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["*"])


@app.exception_handler(cuentas.DatosInvalidos)
@app.exception_handler(ValueError)
def _datos_invalidos(_: Request, exc: Exception):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(cuentas.NoAutorizado)
def _no_autorizado(_: Request, exc: Exception):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(BusquedaNoDisponible)
def _busqueda_no_disponible(_: Request, exc: Exception):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(cuentas.SinPermiso)
def _sin_permiso(_: Request, exc: Exception):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(cuentas.NoEncontrado)
def _no_encontrado(_: Request, exc: Exception):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


class Vivienda(BaseModel):
    distrito_norm: str
    area_total: float
    dormitorios: int
    banos: int
    estacionamientos: Optional[int] = None
    antiguedad: Optional[float] = None
    mantenimiento: Optional[float] = None
    ascensor: Optional[int] = None
    balcon: Optional[int] = None
    terraza: Optional[int] = None
    piscina: Optional[int] = None
    gimnasio: Optional[int] = None
    pet_friendly: Optional[int] = None


class Ubicacion(BaseModel):
    latitud: float
    longitud: float


class PerfilBusqueda(BaseModel):
    hogar: str
    presupuesto_max: Optional[float] = None
    distritos: List[str] = []
    dormitorios_min: Optional[int] = None
    prioridades: List[str] = []
    lugar: Optional[Ubicacion] = None
    lugar_nombre: Optional[str] = Field(None, max_length=200)
    # Cómo prefiere ver las recomendaciones; solo lo usa la app para ordenar la lista.
    orden: Optional[str] = None


class PerfilInquilino(PerfilBusqueda):
    limite: int = Field(12, ge=1, le=30)


class Analisis(BaseModel):
    vivienda: Vivienda
    ubicacion: Optional[Ubicacion] = None


class Comparacion(BaseModel):
    vivienda: Vivienda
    cambios: dict


class Registro(BaseModel):
    nombre: str
    email: str
    password: str


class Ingreso(BaseModel):
    email: str
    password: str


class Departamento(BaseModel):
    nombre: str
    vivienda: Vivienda
    ubicacion: Optional[Ubicacion] = None


class Publicacion(BaseModel):
    precio_soles: float
    escenario: Optional[str] = None


class Interes(BaseModel):
    nombre: str
    email: str
    mensaje: str


class Filtros(BaseModel):
    distritos: List[str] = []
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None
    area_min: Optional[float] = None
    area_max: Optional[float] = None
    dormitorios_min: Optional[int] = None
    banos_min: Optional[int] = None
    paradero_max_m: Optional[float] = None
    amenidades: List[str] = []
    valoracion: Optional[str] = None
    orden: str = "precio"
    limite: int = Field(24, ge=1, le=60)


def limpiar(valor):
    """JSON estricto: NaN pasa a null y los escalares de numpy a tipos de Python."""
    if isinstance(valor, dict):
        return {str(k): limpiar(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [limpiar(v) for v in valor]
    if isinstance(valor, np.generic):
        valor = valor.item()
    if isinstance(valor, float) and not math.isfinite(valor):
        return None
    return valor


def _vivienda(v):
    datos = v.model_dump()
    # Se envían enteros cuando el valor es entero, igual que el formulario de la app del profesor.
    return {k: int(x) if isinstance(x, float) and x.is_integer() else x for k, x in datos.items()}


def _ubicacion(u):
    return u.model_dump() if u is not None else None


def _accesibilidad(distrito, ubicacion):
    if ubicacion is not None:
        return {"origen": "coordenadas ingresadas", **accesibilidad(ubicacion["latitud"], ubicacion["longitud"])}
    centro = centro_distrito(distrito) or (-12.0464, -77.0428)
    return {"origen": "centro aproximado del distrito", **accesibilidad(*centro)}


def analisis_completo(vivienda, ubicacion):
    precio = predecir(vivienda, MODELO_PRECIO)
    competencia = comparables(vivienda, MODELO_PERFIL)
    tendencia = tendencia_distrital(vivienda["distrito_norm"])
    return {
        "vivienda": vivienda, "ubicacion": ubicacion,
        "precio": precio,
        "evidencia_distrital": evidencia_distrital(vivienda["distrito_norm"]),
        "avisos": precio["advertencias"] + avisos_coherencia(vivienda),
        "perfil": competencia,
        "accesibilidad": _accesibilidad(vivienda["distrito_norm"], ubicacion),
        "tendencia": tendencia,
        "publicacion": escenarios_publicacion(precio, competencia, tendencia),
    }


def resumen_analisis(analisis):
    """Lo que se guarda con cada departamento para mostrarlo en la lista sin recalcular."""
    sugerido = next(e for e in analisis["publicacion"]["escenarios"] if e["sugerido"])
    return {"precio_estimado_soles": analisis["precio"]["precio_estimado_soles"],
            "perfil": analisis["perfil"]["perfil"]["perfil"], "accesibilidad": analisis["accesibilidad"]["nivel"],
            "tendencia": analisis["tendencia"]["tendencia"], "escenario_sugerido": sugerido["escenario"],
            "precio_sugerido_soles": sugerido["precio_soles"]}


def base_datos():
    conexion = cuentas.conectar()
    try:
        yield conexion
    finally:
        conexion.close()


def _token(authorization):
    return authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else None


def usuario_actual(authorization: Optional[str] = Header(None), conexion=Depends(base_datos)):
    return cuentas.usuario_de_token(conexion, _token(authorization))


def usuario_opcional(authorization: Optional[str] = Header(None), conexion=Depends(base_datos)):
    """La cuenta si hay una sesión válida; None si no. Para pantallas públicas que cambian un poco con sesión."""
    try:
        return cuentas.usuario_de_token(conexion, _token(authorization))
    except cuentas.NoAutorizado:
        return None


def analista_actual(usuario=Depends(usuario_actual)):
    if usuario.get("rol") != "analista":
        raise cuentas.SinPermiso("Esta sección es solo para el equipo de análisis.")
    return usuario


def tabla_publicados(conexion):
    """Departamentos publicados en DepaRent con las mismas columnas que los anuncios de mercado."""
    filas = []
    for d in cuentas.publicados(conexion):
        vivienda = d["vivienda"]
        X = preparar(pd.DataFrame([vivienda]))
        acceso = _accesibilidad(vivienda["distrito_norm"], d["ubicacion"])
        filas.append({**X.iloc[0].to_dict(), "id": f"d{d['id']}", "origen": "Publicado en DepaRent", "nombre": d["nombre"],
                      "precio_soles": d["publicacion"]["precio_soles"],
                      "dist_paradero_min_m": acceso["dist_paradero_min_m"], "paraderos_500m": acceso["paraderos_500m"],
                      "perfil": asignar_perfil(vivienda, MODELO_PERFIL)["perfil"],
                      "precio_estimado": float(MODELO_PRECIO["pipeline"].predict(X)[0]),
                      "url": None, "fuente": "deparent", "fecha_scraping": None})
    return pd.DataFrame(filas, columns=MERCADO.columns)


# ---------- Análisis ----------

@app.get("/api/salud")
def salud():
    return {"estado": "ok"}


@app.get("/api/opciones")
def opciones():
    tendencias = cargar_tendencias()
    return limpiar({
        "distritos": MODELO_PRECIO["distritos"], "limites": LIMITS, "binarias": BINARY, "etiquetas": ETIQUETAS,
        "cambiables": sorted(CAMBIABLES), "demos": DEMOS,
        "centros": {d: centro_distrito(d) for d in MODELO_PRECIO["distritos"]},
        "metricas": {"precio": MODELO_PRECIO["metricas"]["metricas_prueba"], "intervalo": MODELO_PRECIO["metricas"]["intervalo"],
                     "particiones": MODELO_PRECIO["metricas"]["particiones"],
                     "perfil": {k: MODELO_PERFIL["metricas"][k] for k in ("k", "silhouette", "ari_medio_semillas", "filas")},
                     "tendencia": {k: tendencias[k] for k in ("metodo", "validacion", "regla_tendencia", "limites")}},
        "mercado": {"anuncios": int(len(MERCADO)), "distritos": int(MERCADO["distrito_norm"].nunique()),
                    "captura": MERCADO_INFO["captura"], "captura_texto": MERCADO_INFO["captura_texto"]},
        "recomendador": {"hogares": {k: v["nombre"] for k, v in HOGARES.items()}, "prioridades": NOMBRES_PRIORIDAD},
        "validacion": None if VALIDACION is None else {
            "captura": VALIDACION["captura"], "mes": MES_VALIDACION, "evaluados": VALIDACION["flujo"]["evaluados"],
            "mae_soles": VALIDACION["metricas_octubre"]["HistGradientBoosting"]["MAE_soles"],
            "cobertura": VALIDACION["intervalo"]["cobertura_octubre"]},
    })


@app.get("/api/ubicaciones")
def ubicaciones(q: str):
    """Direcciones de Lima que coinciden con lo escrito, para elegir la ubicación del departamento."""
    resultados = buscar_direccion(q)
    for r in resultados:
        r["distrito"] = distrito_de(r.pop("direccion"), MODELO_PRECIO["distritos"])
    return resultados


@app.post("/api/estimar")
def estimar(vivienda: Vivienda):
    """Solo el precio del modelo 3: lo usa el estimador en vivo de la página de inicio."""
    return limpiar(predecir(_vivienda(vivienda), MODELO_PRECIO))


@app.post("/api/analizar")
def analizar(consulta: Analisis):
    return limpiar(analisis_completo(_vivienda(consulta.vivienda), _ubicacion(consulta.ubicacion)))


@app.post("/api/accesibilidad")
def accesibilidad_punto(ubicacion: Ubicacion):
    return limpiar(_accesibilidad(None, _ubicacion(ubicacion)))


@app.post("/api/comparar")
def comparar_escenario(consulta: Comparacion):
    resultado = comparar(_vivienda(consulta.vivienda), consulta.cambios, MODELO_PRECIO)
    return limpiar({**resultado, "advertencia": ADVERTENCIA})


@app.post("/api/area")
def explorar(vivienda: Vivienda):
    return limpiar({**explorar_area(_vivienda(vivienda), MODELO_PRECIO), "aviso": AVISO_AREA})


# ---------- Cuentas (una sola para inquilinos y propietarios) ----------

@app.post("/api/cuentas/registro")
def registro(datos: Registro, conexion=Depends(base_datos)):
    usuario = cuentas.registrar(conexion, datos.nombre, datos.email, datos.password)
    return {"token": cuentas.crear_sesion(conexion, usuario["id"]), "usuario": usuario}


@app.post("/api/cuentas/ingreso")
def ingreso(datos: Ingreso, conexion=Depends(base_datos)):
    usuario = cuentas.ingresar(conexion, datos.email, datos.password)
    return {"token": cuentas.crear_sesion(conexion, usuario["id"]), "usuario": usuario}


@app.post("/api/cuentas/salida")
def salida(authorization: Optional[str] = Header(None), conexion=Depends(base_datos)):
    cuentas.cerrar_sesion(conexion, _token(authorization))
    return {"estado": "ok"}


@app.get("/api/cuentas/yo")
def yo(usuario=Depends(usuario_actual)):
    return usuario


# ---------- Inquilino: perfil de búsqueda y guardados ----------

@app.get("/api/perfil")
def mi_perfil(usuario=Depends(usuario_actual), conexion=Depends(base_datos)):
    return {"usuario": usuario, "perfil": limpiar(cuentas.obtener_perfil(conexion, usuario["id"]))}


@app.put("/api/perfil")
def guardar_mi_perfil(perfil: PerfilBusqueda, usuario=Depends(usuario_actual), conexion=Depends(base_datos)):
    datos = {**_perfil_valido(perfil), "lugar_nombre": (perfil.lugar_nombre or "").strip() or None}
    return {"usuario": usuario, "perfil": limpiar(cuentas.guardar_perfil(conexion, usuario["id"], datos))}


@app.get("/api/guardados")
def mis_guardados(usuario=Depends(usuario_actual), conexion=Depends(base_datos)):
    return limpiar(cuentas.listar_guardados(conexion, usuario["id"]))


@app.post("/api/guardados/{anuncio_id}")
def guardar(anuncio_id: str, usuario=Depends(usuario_actual), conexion=Depends(base_datos)):
    """Guarda el anuncio con la misma explicación que le dio el recomendador al perfil del usuario."""
    fila = ubicar(MERCADO, tabla_publicados(conexion), anuncio_id)
    if fila is None:
        raise HTTPException(404, "Ese anuncio ya no está en el mercado actual.")
    perfil = cuentas.obtener_perfil(conexion, usuario["id"])
    if perfil:
        perfil = {k: v for k, v in perfil.items() if k not in ("actualizado", "lugar_nombre")}
        datos = explicar(fila, perfil, cargar_red()["centros"], formatear=formatear)
    else:
        datos = {**formatear(fila), "motivos": [], "faltas": [], "amenidades_extra": []}
    return limpiar(cuentas.guardar_anuncio(conexion, usuario["id"], anuncio_id, limpiar(datos)))


@app.delete("/api/guardados/{anuncio_id}")
def quitar(anuncio_id: str, usuario=Depends(usuario_actual), conexion=Depends(base_datos)):
    return limpiar(cuentas.quitar_guardado(conexion, usuario["id"], anuncio_id))


# ---------- Departamentos del propietario ----------

@app.get("/api/departamentos")
def mis_departamentos(usuario=Depends(usuario_actual), conexion=Depends(base_datos)):
    return limpiar(cuentas.listar_departamentos(conexion, usuario["id"]))


@app.post("/api/departamentos")
def crear_departamento(datos: Departamento, usuario=Depends(usuario_actual), conexion=Depends(base_datos)):
    vivienda, ubicacion = _vivienda(datos.vivienda), _ubicacion(datos.ubicacion)
    analisis = analisis_completo(vivienda, ubicacion)
    departamento = cuentas.guardar_departamento(conexion, usuario["id"], datos.nombre, vivienda, ubicacion, resumen_analisis(analisis))
    return limpiar({"departamento": departamento, "analisis": analisis})


@app.get("/api/departamentos/{departamento_id}")
def ver_departamento(departamento_id: int, usuario=Depends(usuario_actual), conexion=Depends(base_datos)):
    departamento = cuentas.obtener_departamento(conexion, usuario["id"], departamento_id)
    departamento["interesados"] = cuentas.listar_interesados(conexion, usuario["id"], departamento_id)
    return limpiar({"departamento": departamento, "analisis": analisis_completo(departamento["vivienda"], departamento["ubicacion"])})


@app.put("/api/departamentos/{departamento_id}")
def editar_departamento(departamento_id: int, datos: Departamento, usuario=Depends(usuario_actual), conexion=Depends(base_datos)):
    vivienda, ubicacion = _vivienda(datos.vivienda), _ubicacion(datos.ubicacion)
    analisis = analisis_completo(vivienda, ubicacion)
    departamento = cuentas.guardar_departamento(conexion, usuario["id"], datos.nombre, vivienda, ubicacion,
                                                resumen_analisis(analisis), departamento_id)
    return limpiar({"departamento": departamento, "analisis": analisis})


@app.delete("/api/departamentos/{departamento_id}")
def borrar_departamento(departamento_id: int, usuario=Depends(usuario_actual), conexion=Depends(base_datos)):
    cuentas.eliminar_departamento(conexion, usuario["id"], departamento_id)
    return {"estado": "ok"}


@app.post("/api/departamentos/{departamento_id}/publicacion")
def publicar(departamento_id: int, datos: Publicacion, usuario=Depends(usuario_actual), conexion=Depends(base_datos)):
    return limpiar(cuentas.publicar(conexion, usuario["id"], departamento_id, datos.precio_soles, datos.escenario))


@app.delete("/api/departamentos/{departamento_id}/publicacion")
def retirar_publicacion(departamento_id: int, usuario=Depends(usuario_actual), conexion=Depends(base_datos)):
    return limpiar(cuentas.publicar(conexion, usuario["id"], departamento_id, None, None))


# ---------- Búsqueda para inquilinos ----------

def _perfil_valido(perfil):
    """Perfil del cuestionario con la ubicación validada; lugar_nombre solo se guarda para mostrarlo."""
    datos = {k: v for k, v in perfil.model_dump().items() if k not in ("limite", "lugar_nombre")}
    if datos.get("orden") not in (None, *ORDENES_RECOMENDACION):
        raise ValueError(f"Orden no válido. Opciones: {', '.join(ORDENES_RECOMENDACION)}.")
    if datos["lugar"]:
        lugar = datos["lugar"]
        datos["lugar"] = dict(zip(("latitud", "longitud"), validar_coordenadas(lugar["latitud"], lugar["longitud"])))
    return validar_perfil(datos)


@app.post("/api/recomendar")
def recomendar_departamentos(perfil: PerfilInquilino, conexion=Depends(base_datos)):
    """Modelo 7: departamentos recomendados según el perfil del inquilino, con sus motivos."""
    limite = perfil.limite
    datos = _perfil_valido(perfil)
    propios = tabla_publicados(conexion)
    tabla = pd.concat([propios, MERCADO], ignore_index=True) if len(propios) else MERCADO
    resultado = recomendar(tabla, datos, cargar_red()["centros"], limite=limite, formatear=formatear)
    return limpiar({**resultado, "aviso": AVISO_RECOMENDADOR.format(captura=MERCADO_INFO["captura_texto"])})

@app.post("/api/buscar")
def buscar_departamentos(filtros: Filtros, conexion=Depends(base_datos)):
    datos = filtros.model_dump()
    return limpiar(buscar(MERCADO, tabla_publicados(conexion), datos, limite=datos.pop("limite"), captura=MERCADO_INFO["captura_texto"], mes_validacion=MES_VALIDACION))


# ---------- Ficha de un anuncio para inquilinos ----------

@app.get("/api/anuncios/{anuncio_id}")
def ver_anuncio(anuncio_id: str, usuario=Depends(usuario_opcional), conexion=Depends(base_datos)):
    fila = ubicar(MERCADO, tabla_publicados(conexion), anuncio_id) if re.fullmatch(r"[md]\d+", anuncio_id) else None
    if fila is None:
        raise cuentas.NoEncontrado("No encontramos ese anuncio. Puede que ya no esté publicado.")
    vivienda = vivienda_de(fila)
    propio = anuncio_id.startswith("d")
    # Un anuncio de mercado no se compara consigo mismo ni con sus duplicados de otros portales.
    competencia = comparables(vivienda, MODELO_PERFIL, excluir=None if propio else anuncio_id)
    red = cargar_red()
    distancia = float(fila["dist_paradero_min_m"])
    mas_lejos = 100 * (1 - np.searchsorted(red["ref_distancia"], distancia, side="right") / len(red["ref_distancia"]))
    tendencia = tendencia_distrital(vivienda["distrito_norm"])
    publicacion, original = None, None
    if not propio:
        enlace = urlparse(str(fila["url"]))
        # Solo enlaces https a los portales de origen; cualquier otro valor no se muestra.
        if enlace.scheme == "https" and enlace.netloc in PORTALES:
            original = {"url": enlace.geturl(), "portal": PORTALES[enlace.netloc], "capturado": str(fila["fecha_scraping"])[:10]}
    if propio:
        d = cuentas.publicado(conexion, int(anuncio_id[1:]))
        publicacion = {"propietario": d["propietario"], "escenario": d["publicacion"]["escenario"], "desde": d["publicacion"]["desde"],
                       # Quien mira su propio anuncio no ve el formulario de contacto (no se escribe a sí mismo).
                       "es_mio": bool(usuario and usuario["id"] == d["usuario_id"]),
                       "departamento_id": d["id"] if usuario and usuario["id"] == d["usuario_id"] else None}
    return limpiar({
        "anuncio": formatear(fila), "vivienda": vivienda, "publicacion": publicacion, "original": original,
        "precio": predecir(vivienda, MODELO_PRECIO), "perfil": competencia,
        # Sin nombres de paraderos ni mapa: revelarían la ubicación del anuncio original.
        "acceso": {"dist_paradero_min_m": distancia, "paraderos_500m": int(fila["paraderos_500m"]),
                   "nivel": nivel_accesibilidad(distancia, fila["paraderos_500m"], red["ref_500m_mediana"]),
                   "porcentaje_anuncios_mas_lejos": round(float(mas_lejos), 1)},
        "tendencia": {k: tendencia[k] for k in ("distrito", "serie_propia", "tendencia", "cambio_porcentaje")},
        "aviso": AVISO_MERCADO.format(captura=MERCADO_INFO["captura_texto"], mes_validacion=MES_VALIDACION),
    })


@app.post("/api/anuncios/{anuncio_id}/interes")
def registrar_interes(anuncio_id: str, datos: Interes, usuario=Depends(usuario_opcional), conexion=Depends(base_datos)):
    if not re.fullmatch(r"d\d+", anuncio_id):
        raise cuentas.DatosInvalidos("Este anuncio viene de un portal externo; DepaRent no tiene el contacto de su propietario.")
    cuentas.registrar_interes(conexion, int(anuncio_id[1:]), datos.nombre, datos.email, datos.mensaje,
                              usuario["id"] if usuario else None)
    return {"estado": "ok"}

# ---------- KPIs del producto de datos (solo analistas) ----------

def _metricas(m):
    return {"mae_soles": round(m["MAE_soles"], 1), "mape_porcentaje": round(m["MAPE_porcentaje"], 1), "r2": round(m["R2"], 3)}


def _kpis_modelo():
    entrenamiento = json.loads((ROOT / "resultados/metricas.json").read_text(encoding="utf-8"))
    prueba = entrenamiento["metricas_prueba"]
    modelo = {"entrenado_con": "captura del 14-sep-2026", "version": entrenamiento.get("version"),
              "prueba": {"modelo": _metricas(prueba["HistGradientBoosting"]), "baseline_distrital": _metricas(prueba["mediana_distrital"]),
                         "baseline_global": _metricas(prueba["mediana_global"])},
              "validaciones": []}
    for v in sorted(_VALIDACIONES, key=lambda v: v["captura"]):
        m = v["metricas_octubre"]
        modelo["validaciones"].append({
            "captura": v["captura"], "evaluados": v["flujo"]["evaluados"],
            "modelo": _metricas(m["HistGradientBoosting"]), "baseline_distrital": _metricas(m["mediana_distrital"]),
            "cobertura_rango_porcentaje": round(100 * v["intervalo"]["cobertura_octubre"], 1),
            "cobertura_objetivo_porcentaje": round(100 * v["intervalo"]["nivel_nominal"], 1),
            "cambio_mae_porcentaje": round(v["cambio_MAE_porcentaje"], 1),
            "porcentaje_por_encima_del_estimado": round(v["sesgo"]["porcentaje_por_encima_del_estimado"], 1)})
    return modelo


def _kpis_datos():
    from datetime import date
    captura = date.fromisoformat(MERCADO_INFO["captura"])
    distritos = MERCADO["distrito_norm"].value_counts()
    return {"captura": MERCADO_INFO["captura"], "captura_texto": MERCADO_INFO["captura_texto"],
            "dias_desde_captura": (date.today() - captura).days,
            "anuncios_en_captura": MERCADO_INFO["anuncios_en_captura"], "validos": MERCADO_INFO["validos"],
            "unicos": MERCADO_INFO["unicos"], "en_la_app": int(len(MERCADO)),
            "porcentaje_validos": round(100 * MERCADO_INFO["validos"] / MERCADO_INFO["anuncios_en_captura"], 1),
            "distritos": int(distritos.size),
            "anuncios_por_distrito": [{"distrito": d, "anuncios": int(n)} for d, n in distritos.head(12).items()],
            "precio_mediano_soles": round(float(MERCADO["precio_soles"].median()), 0)}


def _kpis_recomendador():
    if not _EVAL_RECOMENDADOR.exists():
        return None
    e = json.loads(_EVAL_RECOMENDADOR.read_text(encoding="utf-8"))
    r = e["resumen"]
    return {"perfiles_evaluados": e["perfiles_evaluados"], "k": e["K"],
            "recomendador": r["recomendador"], "mejor_alternativa": max(
                ((k, v) for k, v in r.items() if k != "recomendador"), key=lambda kv: kv[1]["precision"])}


@app.get("/api/kpis")
def kpis(_=Depends(analista_actual), conexion=Depends(base_datos)):
    return limpiar({"producto": cuentas.kpis_producto(conexion), "modelo": _kpis_modelo(),
                    "datos": _kpis_datos(), "recomendador": _kpis_recomendador()})


if FRONTEND.exists():
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
