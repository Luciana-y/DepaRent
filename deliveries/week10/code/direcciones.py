"""Búsqueda de direcciones de Lima con Nominatim (OpenStreetMap) para ubicar el departamento.

Se consulta desde el servidor, una vez por búsqueda (no al teclear), como pide la política de uso de Nominatim.
"""
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from accesibilidad import LIMITES
from modelo import normalizar

URL = "https://nominatim.openstreetmap.org/search"
AGENTE = "DepaRent/0.10 (https://deparent.onrender.com; proyecto DS3022 UTEC)"
# Campos de Nominatim que suelen traer el distrito, del más al menos específico. "city" no entra:
# en Lima casi siempre dice "Lima" y marcaría el Cercado para cualquier dirección.
CAMPOS_DISTRITO = ("city_district", "suburb", "town", "village", "municipality")
# Abreviaturas de las direcciones peruanas que Nominatim no reconoce ("Jr. Monte Rosa" no aparece; "Jirón Monte Rosa", sí).
ABREVIATURAS = {"av": "Avenida", "jr": "Jirón", "jir": "Jirón", "ca": "Calle", "cl": "Calle", "psje": "Pasaje", "pje": "Pasaje",
                "prol": "Prolongación", "mlc": "Malecón", "urb": "Urbanización"}
_CACHE = {}


def expandir(texto):
    return re.sub(r"\b([A-Za-z]+)\.?(?=\s)", lambda m: ABREVIATURAS.get(m.group(1).lower(), m.group(0)), texto)


class BusquedaNoDisponible(Exception):
    pass


def buscar_direccion(texto, limite=5):
    texto = re.sub(r"\s+", " ", str(texto or "")).strip()
    if len(texto) < 3:
        raise ValueError("Escribe al menos 3 caracteres de la dirección.")
    if len(texto) > 200:
        raise ValueError("La dirección es demasiado larga.")
    clave = texto.lower()
    if clave not in _CACHE:
        (lat_min, lat_max), (lon_min, lon_max) = LIMITES["latitud"], LIMITES["longitud"]
        parametros = urlencode({
            "q": expandir(texto), "format": "jsonv2", "addressdetails": 1, "limit": limite, "countrycodes": "pe",
            "viewbox": f"{lon_min},{lat_max},{lon_max},{lat_min}", "bounded": 1, "accept-language": "es",
        })
        try:
            with urlopen(Request(f"{URL}?{parametros}", headers={"User-Agent": AGENTE}), timeout=8) as respuesta:
                datos = json.load(respuesta)
        except Exception as exc:
            raise BusquedaNoDisponible("No se pudo buscar la dirección ahora. Marca el punto en el mapa o escribe las coordenadas.") from exc
        _CACHE[clave] = [{"nombre": d["display_name"], "latitud": round(float(d["lat"]), 6), "longitud": round(float(d["lon"]), 6),
                          "direccion": d.get("address", {})} for d in datos]
    # Copias: quien llama puede modificar los resultados sin tocar la caché.
    return [dict(r) for r in _CACHE[clave]]


def distrito_de(direccion, distritos):
    """Distrito del modelo que corresponde a la dirección, o None si no se reconoce."""
    candidatos = [d for d in distritos if d != "otros"]
    for campo in CAMPOS_DISTRITO:
        valor = f" {normalizar(direccion.get(campo))} "
        # El nombre más largo primero: "magdalena del mar" es magdalena; "santiago de surco" es surco.
        coincidencias = [d for d in candidatos if f" {normalizar(d)} " in valor]
        if coincidencias:
            return max(coincidencias, key=len)
    return None
