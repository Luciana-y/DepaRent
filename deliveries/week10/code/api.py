"""API del prototipo: componentes analíticos, cuentas de propietarios y búsqueda para inquilinos.

Local (desde deliveries/week10/code):
    python -m uvicorn api:app --port 8000
y abrir http://127.0.0.1:8000 (la API también sirve ../frontend).
En despliegue, DEPARENT_ORIGENES limita qué dominios pueden llamar a la API (por ejemplo, el de Netlify).
"""
import json
import math
import os
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
from accesibilidad import accesibilidad, centro_distrito
from ayuda_interfaz import ETIQUETAS, avisos_coherencia
from busqueda import buscar, construir_mercado
from escenarios import ADVERTENCIA, CAMBIABLES, comparar, verificar_modelo_congelado
from escenarios_precio import escenarios_publicacion
from evidencia_distrital import evidencia_distrital
from laboratorio_area import AVISO as AVISO_AREA, explorar_area
from modelo import BINARY, LIMITS, ROOT, predecir, preparar
from perfil_competitivo import ARCHIVO as ARCHIVO_PERFIL, asignar_perfil, comparables
from tendencia import cargar_tendencias, tendencia_distrital

verificar_modelo_congelado()
MODELO_PRECIO = joblib.load(ROOT / "models/modelo_docente.joblib")
MODELO_PERFIL = joblib.load(ARCHIVO_PERFIL)
DEMOS = json.loads((ROOT / "data/demo_casos.json").read_text(encoding="utf-8"))
MERCADO = construir_mercado(MODELO_PRECIO, MODELO_PERFIL)
FRONTEND = ROOT / "frontend"

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
                      "precio_estimado": float(MODELO_PRECIO["pipeline"].predict(X)[0])})
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
        "metricas": {"precio": MODELO_PRECIO["metricas"]["metricas_prueba"], "intervalo": MODELO_PRECIO["metricas"]["intervalo"],
                     "particiones": MODELO_PRECIO["metricas"]["particiones"],
                     "perfil": {k: MODELO_PERFIL["metricas"][k] for k in ("k", "silhouette", "ari_medio_semillas", "filas")},
                     "tendencia": {k: tendencias[k] for k in ("metodo", "validacion", "regla_tendencia", "limites")}},
        "mercado": {"anuncios": int(len(MERCADO)), "distritos": int(MERCADO["distrito_norm"].nunique())},
    })


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


# ---------- Cuentas de propietarios ----------

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

@app.post("/api/buscar")
def buscar_departamentos(filtros: Filtros, conexion=Depends(base_datos)):
    datos = filtros.model_dump()
    return limpiar(buscar(MERCADO, tabla_publicados(conexion), datos, limite=datos.pop("limite")))


if FRONTEND.exists():
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
