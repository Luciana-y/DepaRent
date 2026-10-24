"""Descarga diaria de anuncios de alquiler de departamentos en Lima (Adondevivir y Urbania).

Mismo método que la Semana 4 (ver deliveries/week04/acquisition.md): se lee el JSON
`window.__PRELOADED_STATE__` de cada página del catálogo y se mapean los campos CFT.

Cada ejecución guarda en data_diaria/:
  snapshots/AAAA-MM-DD.csv.gz  foto del día, mismas columnas que departamentos_alquiler_lima.csv
  historial_precios.csv        una fila por anuncio y día (para ver cambios de precio)
  anuncios.csv                 una fila por anuncio: primera/última vez visto, precio inicial/actual
  descargas_log.csv            resumen de cada ejecución

Solo usa la librería estándar. Uso:  py -3 scraper/descarga_diaria.py [--max-paginas N]
"""
import argparse
import csv
import gzip
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data_diaria"
SNAP_DIR = OUT_DIR / "snapshots"

PORTALES = {
    "adondevivir": {
        "base": "https://www.adondevivir.com",
        "pagina": lambda n: "/departamentos-en-alquiler-en-lima.html" if n == 1
        else f"/departamentos-en-alquiler-en-lima-pagina-{n}.html",
    },
    "urbania": {
        "base": "https://urbania.pe",
        "pagina": lambda n: "/buscar/alquiler-de-departamentos-en-lima" if n == 1
        else f"/buscar/alquiler-de-departamentos-en-lima?page={n}",
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept-Language": "es-PE,es;q=0.9",
}
TIPO_CAMBIO = 3.75  # PEN por USD, misma tasa de referencia que la Semana 4
MAX_PAGINAS = 200   # tope de seguridad por portal

# Columnas idénticas a deliveries/week04/data/departamentos_alquiler_lima.csv
COLUMNAS = [
    "id_anuncio", "fuente", "tipo_operacion", "url", "fecha_scraping", "titulo", "precio", "moneda",
    "precio_soles", "area_total", "area_construida", "precio_m2", "distrito", "direccion",
    "dormitorios", "banos", "medios_banos", "estacionamientos", "piso", "antiguedad", "mantenimiento",
    "estado_inmueble", "caracteristicas", "nombre_proyecto", "inmobiliaria", "descripcion",
    "latitud", "longitud", "texto_amenidades_crudo", "ascensor", "balcon", "terraza", "piscina",
    "gimnasio", "cochera", "deposito", "vista_al_mar", "parrilla", "areas_verdes", "seguridad_24_7",
    "coworking", "juegos_infantiles", "pet_friendly",
]
COLUMNAS_EXTRA = ["estado_portal", "fecha_modificacion_portal"]

RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
RE_TELEFONO = re.compile(r"(?<!\d)(?:\+?51[\s.-]?)?\d(?:[\s.-]?\d){6,}(?!\d)")


def anonimizar(texto):
    if not texto:
        return ""
    texto = RE_EMAIL.sub("[correo]", texto)
    return RE_TELEFONO.sub("[telefono]", texto)


def descargar(url, intentos=4):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            espera = 2 ** (i + 1)
            print(f"  error {e} en {url}; reintento en {espera}s", flush=True)
            time.sleep(espera)
    return None


def leer_estado(html):
    marca = "window.__PRELOADED_STATE__"
    i = html.find(marca)
    if i < 0:
        return None
    resto = html[i + len(marca):]
    resto = resto[resto.index("=") + 1:].lstrip()
    estado, _ = json.JSONDecoder().raw_decode(resto)
    return estado.get("listStore")


def numero(valor):
    try:
        return float(str(valor).replace(",", ""))
    except (TypeError, ValueError):
        return None


def distrito_de(location):
    nodo = location
    while nodo:
        if nodo.get("label") == "ZONA":
            return nodo.get("name")
        nodo = nodo.get("parent")
    return (location or {}).get("name")


def mapear(p, fuente, base, fecha):
    precio, moneda = None, None
    for op in p.get("priceOperationTypes") or []:
        if op.get("operationType", {}).get("name") != "Alquiler":
            continue
        precios = op.get("prices") or []
        pen = next((x for x in precios if x.get("currency") == "S/"), None)
        elegido = pen or (precios[0] if precios else None)
        if elegido:
            precio = numero(elegido.get("amount"))
            moneda = "PEN" if elegido.get("currency") == "S/" else elegido.get("currency")
    precio_soles = precio if moneda == "PEN" else (precio * TIPO_CAMBIO if precio and moneda == "USD" else None)

    cft = {k: v.get("value") for k, v in (p.get("mainFeatures") or {}).items()}
    area_total = numero(cft.get("CFT100"))
    gasto = p.get("expenses") or {}
    # amount 0 sin formattedAmount = el anunciante no llenó el campo (vacío, como en la Semana 4)
    mantenimiento = numero(gasto.get("amount")) if gasto.get("formattedAmount") else None
    if mantenimiento and gasto.get("currency") == "USD":
        mantenimiento *= TIPO_CAMBIO

    ubic = p.get("postingLocation") or {}
    geo = (ubic.get("postingGeolocation") or {}).get("geolocation") or {}
    generales = [f.get("label") for grupo in (p.get("generalFeatures") or {}).values()
                 for f in (grupo.values() if isinstance(grupo, dict) else []) if isinstance(f, dict)]
    caracteristicas = ", ".join(x for x in generales if x)
    titulo = p.get("title") or p.get("generatedTitle") or ""
    descripcion = anonimizar(p.get("descriptionNormalized"))

    fila = dict.fromkeys(COLUMNAS + COLUMNAS_EXTRA, "")
    fila.update({
        "id_anuncio": p.get("postingId"),
        "fuente": fuente,
        "tipo_operacion": "alquiler",
        "url": base + (p.get("url") or ""),
        "fecha_scraping": fecha,
        "titulo": anonimizar(titulo),
        "precio": precio,
        "moneda": moneda,
        "precio_soles": precio_soles,
        "area_total": area_total,
        "area_construida": numero(cft.get("CFT101")),
        "precio_m2": round(precio_soles / area_total, 2) if precio_soles and area_total else None,
        "distrito": distrito_de(ubic.get("location")),
        "direccion": (ubic.get("address") or {}).get("name"),
        "dormitorios": numero(cft.get("CFT2")),
        "banos": numero(cft.get("CFT3")),
        "medios_banos": numero(cft.get("CFT4")),
        "estacionamientos": numero(cft.get("CFT7")),
        "antiguedad": numero(cft.get("CFT5")) if cft.get("CFT5") is not None else numero(p.get("antiquity")),
        "mantenimiento": mantenimiento,
        "caracteristicas": caracteristicas,
        "descripcion": descripcion,
        "latitud": geo.get("latitude"),
        "longitud": geo.get("longitude"),
        "texto_amenidades_crudo": " | ".join(x for x in (anonimizar(titulo), descripcion, caracteristicas) if x),
        "estado_portal": p.get("status"),
        "fecha_modificacion_portal": p.get("modified_date"),
    })
    return fila


def recorrer_portal(fuente, conf, fecha, max_paginas):
    filas, descartados, paginas, errores = [], 0, 0, 0
    total_paginas = max_paginas
    n = 1
    while n <= min(total_paginas, max_paginas):
        html = descargar(conf["base"] + conf["pagina"](n))
        store = leer_estado(html) if html else None
        if store is None:
            errores += 1
            print(f"  {fuente} página {n}: sin datos", flush=True)
            if errores >= 3:
                break
            n += 1
            continue
        paging = store.get("paging") or {}
        total_paginas = paging.get("totalPages") or total_paginas
        if n > 1 and paging.get("currentPage") not in (None, n):
            print(f"  {fuente}: la página {n} devolvió la {paging.get('currentPage')}; se detiene", flush=True)
            break
        postings = store.get("listPostings") or []
        if not postings:
            break
        for p in postings:
            if (p.get("realEstateType") or {}).get("name") != "Departamentos":
                descartados += 1
                continue
            filas.append(mapear(p, fuente, conf["base"], fecha))
        paginas += 1
        if n % 10 == 0:
            print(f"  {fuente}: página {n}/{total_paginas}, {len(filas)} anuncios", flush=True)
        n += 1
        time.sleep(random.uniform(1.0, 1.3))
    return filas, {"paginas": paginas, "descartados_no_depa": descartados, "errores": errores}


def escribir_csv(ruta, filas, columnas, comprimido=False):
    abrir = gzip.open if comprimido else open
    with abrir(ruta, "wt", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)


def leer_csv(ruta):
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def actualizar_historial(dia, filas):
    """Reemplaza las filas del día (si se corre dos veces) y reconstruye anuncios.csv."""
    ruta = OUT_DIR / "historial_precios.csv"
    cols = ["fecha", "id_anuncio", "fuente", "distrito", "precio", "moneda", "precio_soles"]
    historial = [h for h in leer_csv(ruta) if h["fecha"] != dia]
    historial += [{"fecha": dia, **{c: f[c] for c in cols[1:]}} for f in filas]
    historial.sort(key=lambda h: (h["fecha"], h["id_anuncio"]))
    escribir_csv(ruta, historial, cols)

    ultimo_dia = max(h["fecha"] for h in historial)
    anuncios = {}
    for h in historial:
        a = anuncios.get(h["id_anuncio"])
        if a is None:
            a = anuncios[h["id_anuncio"]] = {
                "id_anuncio": h["id_anuncio"], "fuente": h["fuente"], "distrito": h["distrito"],
                "primera_vez_visto": h["fecha"], "precio_inicial_soles": h["precio_soles"],
                "dias_visto": 0, "n_cambios_precio": 0,
            }
        elif h["precio_soles"] != a["precio_actual_soles"]:
            a["n_cambios_precio"] += 1
        a["ultima_vez_visto"] = h["fecha"]
        a["precio_actual_soles"] = h["precio_soles"]
        a["dias_visto"] += 1
    for a in anuncios.values():
        a["activo"] = int(a["ultima_vez_visto"] == ultimo_dia)
        a["dias_publicado"] = (datetime.fromisoformat(a["ultima_vez_visto"])
                               - datetime.fromisoformat(a["primera_vez_visto"])).days + 1
    cols_a = ["id_anuncio", "fuente", "distrito", "primera_vez_visto", "ultima_vez_visto", "dias_visto",
              "dias_publicado", "activo", "precio_inicial_soles", "precio_actual_soles", "n_cambios_precio"]
    escribir_csv(OUT_DIR / "anuncios.csv", list(anuncios.values()), cols_a)
    return len(anuncios), sum(a["activo"] for a in anuncios.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--max-paginas", type=int, default=MAX_PAGINAS,
                        help="páginas por portal (para pruebas rápidas)")
    parser.add_argument("--sin-historial", action="store_true",
                        help="guardar solo el snapshot, sin tocar historial ni anuncios (pruebas)")
    args = parser.parse_args()

    inicio = time.time()
    ahora = datetime.now()
    dia, fecha = ahora.strftime("%Y-%m-%d"), ahora.strftime("%Y-%m-%d %H:%M:%S")
    SNAP_DIR.mkdir(parents=True, exist_ok=True)

    todas, vistos, resumen = [], set(), {}
    for fuente, conf in PORTALES.items():
        print(f"Descargando {fuente}...", flush=True)
        filas, stats = recorrer_portal(fuente, conf, fecha, args.max_paginas)
        # El orden del catálogo cambia mientras se pagina: un anuncio puede salir en dos páginas
        # del mismo portal, además de repetirse entre portales.
        nuevas = []
        for f in filas:
            if f["id_anuncio"] not in vistos:
                vistos.add(f["id_anuncio"])
                nuevas.append(f)
        stats.update(anuncios=len(filas), unicos_agregados=len(nuevas))
        resumen[fuente] = stats
        todas += nuevas
        print(f"  {fuente}: {stats}", flush=True)

    if not todas:
        print("No se descargó ningún anuncio; no se guarda nada.", file=sys.stderr)
        sys.exit(1)

    snap = SNAP_DIR / f"{dia}.csv.gz"
    escribir_csv(snap, todas, COLUMNAS + COLUMNAS_EXTRA, comprimido=True)
    total_ids, activos = (None, None) if args.sin_historial else actualizar_historial(dia, todas)

    log = OUT_DIR / "descargas_log.csv"
    cols_log = ["fecha", "anuncios_dia", "adondevivir", "urbania", "paginas", "errores",
                "anuncios_historicos", "duracion_min"]
    filas_log = leer_csv(log) + [{
        "fecha": fecha, "anuncios_dia": len(todas),
        "adondevivir": resumen["adondevivir"]["unicos_agregados"],
        "urbania": resumen["urbania"]["unicos_agregados"],
        "paginas": sum(s["paginas"] for s in resumen.values()),
        "errores": sum(s["errores"] for s in resumen.values()),
        "anuncios_historicos": total_ids, "duracion_min": round((time.time() - inicio) / 60, 1),
    }]
    escribir_csv(log, filas_log, cols_log)

    print(f"Listo: {len(todas)} anuncios únicos -> {snap}")
    if total_ids is not None:
        print(f"Historial: {total_ids} anuncios distintos, {activos} activos hoy.")


if __name__ == "__main__":
    main()
