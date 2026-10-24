"""Prepara el mercado que muestra la app a partir de la captura diaria más reciente.

La app (búsqueda, fichas, comparables y perfiles) usa data/mercado.csv. El modelo de precio no cambia:
sigue siendo el congelado de septiembre, validado con octubre en resultados/validacion_octubre/.

1. Toma la captura completa más reciente de data_diaria/snapshots (o la fecha pedida).
2. La procesa con las reglas de la Semana 7 y los distritos con que se entrenó el modelo de precio.
3. Deja un anuncio por posible inmueble (misma heurística de duplicados del entrenamiento).
4. Calcula su accesibilidad (paraderos ATU) y guarda solo lo que la app necesita:
   sin dirección, coordenadas, título ni descripción. El enlace al portal sí se guarda (decisión del equipo).

Uso, desde deliveries/week10/code:
    python preparar_mercado.py [--captura AAAA-MM-DD]
    python entrenar_perfil.py          # reentrena los perfiles y los comparables con el mercado nuevo
"""
import argparse
import json
from datetime import datetime

import joblib
import pandas as pd

from accesibilidad import variables_lote
from modelo import LIMITS, ROOT, grupos_inmueble
from preprocesar import AMENITY_KEYWORDS, elegir_captura, procesar

ARCHIVO = ROOT / "data/mercado.csv"
METADATOS = ROOT / "data/mercado.json"
COLUMNAS = ["id_anuncio", "fuente", "url", "fecha_scraping", "distrito_norm", "precio_soles", "area_total", "dormitorios",
            "banos", "estacionamientos", "antiguedad", "mantenimiento", *AMENITY_KEYWORDS, "precio_m2_real",
            "dist_paradero_min_m", "paraderos_500m"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def preparar(archivo_captura):
    distritos = joblib.load(ROOT / "models/modelo_docente.joblib")["distritos"]
    crudo = pd.read_csv(archivo_captura, low_memory=False)
    limpio = procesar(crudo, distritos_conocidos=distritos, alias_portal=True)
    # Un anuncio por posible inmueble: el mismo departamento aparece en Adondevivir y en Urbania.
    limpio["_grupo"] = grupos_inmueble(limpio)
    unicos = limpio.drop_duplicates("_grupo").reset_index(drop=True)
    unicos["dist_paradero_min_m"], unicos["paraderos_500m"] = variables_lote(unicos["latitud"], unicos["longitud"])
    unicos["distrito_norm"] = unicos["distrito_norm"].str.strip()
    # Valores imposibles (un mantenimiento de S/ 350,000, 402 años de antigüedad): fuera de los límites que acepta el
    # formulario, el dato se toma como no informado; el anuncio se conserva.
    corregidos = {}
    for col, (minimo, maximo) in LIMITS.items():
        fuera = (unicos[col] < minimo) | (unicos[col] > maximo)
        if fuera.any():
            unicos.loc[fuera, col] = float("nan")
            corregidos[col] = int(fuera.sum())
    fecha = archivo_captura.name.replace(".csv.gz", "")
    dia = datetime.strptime(fecha, "%Y-%m-%d")
    metadatos = {"captura": fecha, "captura_texto": f"{dia.day} de {MESES[dia.month - 1]} de {dia.year}",
                 "anuncios_en_captura": len(crudo), "validos": len(limpio), "unicos": len(unicos),
                 "valores_fuera_de_limites_como_no_informados": corregidos,
                 "generado": datetime.now().isoformat(timespec="seconds"),
                 "nota": "Mercado de la app. El modelo de precio sigue entrenado con la captura del 14-sep-2026."}
    return unicos[COLUMNAS], metadatos


def main():
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--captura", help="fecha AAAA-MM-DD; por defecto la captura completa más reciente")
    archivo = elegir_captura(argumentos.parse_args().captura)
    mercado, metadatos = preparar(archivo)
    mercado.to_csv(ARCHIVO, index=False)
    METADATOS.write_text(json.dumps(metadatos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadatos, ensure_ascii=False, indent=2))
    print(mercado["distrito_norm"].value_counts().to_string())


if __name__ == "__main__":
    main()
