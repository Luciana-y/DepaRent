"""Contrato de entrada de una propiedad nueva: validación y normalización.

Las reglas replican el pipeline canónico (deliveries/week07/code/EDA_week07.ipynb):
- DISTRITO_MAP es el `distrito_map` de la celda In[12].
- AMENITIES son las 13 amenidades extraídas en In[5] (sin `cochera`, ver DESCRIPTIVE_COMPONENTS.md).
- LIMA_BBOX es el bounding box del filtro geográfico de In[9].
- Los rangos de área son los del filtro de In[9]; el de mantenimiento es el de In[4].
"""
import math
import unicodedata

AMENITIES = [
    "ascensor", "balcon", "terraza", "piscina", "gimnasio", "deposito", "vista_al_mar",
    "parrilla", "areas_verdes", "seguridad_24_7", "coworking", "juegos_infantiles", "pet_friendly",
]

DISTRITO_MAP = {
    "Santiago de Surco": "Surco",
    "Magdalena del Mar": "Magdalena",
    "Jesús María": "Jesus Maria",
    "Cercado de Lima": "Lima",
    "Barranca": "Barranco",
}

# Rangos plausibles (inclusive). Se usan igual en entrenamiento (valor fuera de rango -> NaN)
# y en inferencia (valor fuera de rango -> error), para que ambos lados sean coherentes.
RANGES = {
    "area_total": (25.0, 450.0),
    "dormitorios": (1, 10),
    "banos": (1, 10),
    "antiguedad": (0.0, 100.0),
    "mantenimiento": (50.0, 2500.0),
}
REQUIRED_FIELDS = ["distrito", "area_total", "dormitorios", "banos", "amenidades"]
OPTIONAL_FIELDS = ["antiguedad", "mantenimiento"]
INTEGER_FIELDS = {"dormitorios", "banos"}

LIMA_BBOX = {"lat": (-12.35, -11.75), "lon": (-77.20, -76.80)}


class InputValidationError(ValueError):
    """Entrada no procesable. `errors` contiene un mensaje por problema detectado."""

    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("Entrada inválida: " + "; ".join(self.errors))


def _key(text):
    """Clave de comparación: sin tildes, minúsculas y espacios colapsados."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(text.lower().split())


def normalize_district_name(raw):
    """Nombre crudo del anuncio -> nombre normalizado (mismo criterio que In[12])."""
    name = str(raw).strip()
    return DISTRITO_MAP.get(name, name)


def build_district_lookup(known_districts):
    """Alias aceptados (sin tildes/mayúsculas) -> nombre normalizado conocido."""
    lookup = {_key(d): d for d in known_districts}
    for alias, target in DISTRITO_MAP.items():
        if target in known_districts:
            lookup[_key(alias)] = target
    return lookup


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_number(name, value, errors, required):
    if value is None:
        if required:
            errors.append(f"'{name}' es obligatorio")
        return None
    if not _is_number(value):
        errors.append(f"'{name}' debe ser numérico (recibido {type(value).__name__})")
        return None
    if math.isnan(value) or math.isinf(value):
        errors.append(f"'{name}' no puede ser NaN ni infinito")
        return None
    if name in INTEGER_FIELDS and float(value) != int(value):
        errors.append(f"'{name}' debe ser un número entero (recibido {value})")
        return None
    lo, hi = RANGES[name]
    if not lo <= value <= hi:
        errors.append(f"'{name}'={value} fuera del rango soportado [{lo}, {hi}]")
        return None
    return int(value) if name in INTEGER_FIELDS else float(value)


def validate_property(data, known_districts):
    """Valida y normaliza las características físicas de la propiedad (RF1).

    Devuelve un diccionario normalizado o levanta InputValidationError con todos los
    problemas encontrados. `known_districts` son los distritos normalizados presentes
    en los datos de entrenamiento.
    """
    if not isinstance(data, dict):
        raise InputValidationError([f"se esperaba un diccionario, se recibió {type(data).__name__}"])
    errors = []
    out = {}

    distrito = data.get("distrito")
    if distrito is None or (isinstance(distrito, str) and not distrito.strip()):
        errors.append("'distrito' es obligatorio")
    elif not isinstance(distrito, str):
        errors.append("'distrito' debe ser texto")
    else:
        match = build_district_lookup(known_districts).get(_key(distrito))
        if match is None:
            errors.append(
                f"distrito '{distrito}' sin cobertura en los datos; distritos soportados: "
                + ", ".join(sorted(known_districts))
            )
        out["distrito"] = match

    for name in ["area_total", "dormitorios", "banos"]:
        out[name] = _check_number(name, data.get(name), errors, required=True)
    for name in OPTIONAL_FIELDS:
        out[name] = _check_number(name, data.get(name), errors, required=False)

    amen = data.get("amenidades")
    if amen is None:
        errors.append("'amenidades' es obligatorio (lista de amenidades presentes; puede ser vacía)")
    elif not isinstance(amen, (list, tuple, set)) or not all(isinstance(a, str) for a in amen):
        errors.append("'amenidades' debe ser una lista de nombres")
    else:
        unknown = sorted(set(amen) - set(AMENITIES))
        if unknown:
            errors.append(f"amenidades no reconocidas: {unknown}; válidas: {AMENITIES}")
        out["amenidades"] = {a: int(a in amen) for a in AMENITIES}

    if errors:
        raise InputValidationError(errors)
    return out


def validate_coordinates(lat, lon):
    """Valida coordenadas para RF2. Devuelve (lat, lon) como float o levanta InputValidationError."""
    errors = []
    values = {}
    for name, value, (lo, hi) in [("latitud", lat, LIMA_BBOX["lat"]), ("longitud", lon, LIMA_BBOX["lon"])]:
        if value is None:
            errors.append(f"'{name}' es obligatoria")
        elif not _is_number(value):
            errors.append(f"'{name}' debe ser numérica (recibido {type(value).__name__})")
        elif math.isnan(value) or math.isinf(value):
            errors.append(f"'{name}' no puede ser NaN ni infinita")
        elif not lo <= value <= hi:
            errors.append(f"'{name}'={value} fuera del área Lima Metropolitana/Callao [{lo}, {hi}]")
        else:
            values[name] = float(value)
    if errors:
        raise InputValidationError(errors)
    return values["latitud"], values["longitud"]
