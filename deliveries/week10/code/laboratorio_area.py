"""Tres consultas de sensibilidad al área; no entrena ni modifica el modelo."""
import copy
import csv
import io
import math
from modelo import FEATURES, predecir

AVISO = ("Solo cambia el área; las demás entradas permanecen iguales. Son perfiles hipotéticos, "
         "no anuncios nuevos ni efectos causales. Los rangos son individuales: no son un intervalo "
         "de confianza para las diferencias. Más área no garantiza una estimación mayor.")


def resumen_sensibilidad(points):
    """Describe las salidas observadas del modelo; nunca corrige sus predicciones."""
    if len(points) != 3:
        raise ValueError("El resumen requiere exactamente tres áreas.")
    base, mayor = points[1], points[2]
    precio_base = base["resultado"]["precio_estimado_soles"]
    precio_mayor = mayor["resultado"]["precio_estimado_soles"]
    diferencia = round(precio_mayor - precio_base, 2)
    precios = [point["resultado"]["precio_estimado_soles"] for point in points]
    return {
        "area_base_m2": base["entrada"]["area_total"],
        "area_mayor_m2": mayor["entrada"]["area_total"],
        "diferencia_base_a_mayor_soles": diferencia,
        "variacion_base_a_mayor_porcentaje": round(100 * diferencia / precio_base, 2) if precio_base else None,
        "hay_descenso_al_aumentar_area": any(despues < antes for antes, despues in zip(precios, precios[1:])),
    }


def explorar_area(base, artifact):
    """Rechaza la consulta completa si alguna de las tres áreas no es válida."""
    try:
        area = float(base.get("area_total"))
    except (TypeError, ValueError):
        raise ValueError("El área base debe ser un número entero válido.")
    if isinstance(base.get("area_total"), bool) or not math.isfinite(area) or not area.is_integer():
        raise ValueError("El área base debe ser un número entero válido.")
    points = []
    for factor in (0.8, 1.0, 1.2):
        entry = copy.deepcopy(base)
        entry["area_total"] = round(area * factor)
        try:
            result = predecir(entry, artifact)
        except ValueError as exc:
            raise ValueError(f"No se pueden mostrar las tres áreas: {entry['area_total']} m². {exc}") from exc
        points.append({"factor_area": factor, "entrada": entry, "resultado": result})
    return {"naturaleza": "SENSIBILIDAD_MODELO_ENTRADAS_HIPOTETICAS", "solo_cambia": "area_total",
            "entrada_base": copy.deepcopy(base), "puntos": points, "resumen": resumen_sensibilidad(points),
            "advertencia": AVISO}


def tabla_area(lab):
    return [{"Área (m²)": point["entrada"]["area_total"],
             "Estimación (S/)": point["resultado"]["precio_estimado_soles"],
             "Límite inferior (S/)": point["resultado"]["limite_inferior_soles"],
             "Límite superior (S/)": point["resultado"]["limite_superior_soles"]}
            for point in lab["puntos"]]


def csv_area(lab):
    stream = io.StringIO(newline="")
    fields = ["factor_area"] + FEATURES + ["precio_estimado_soles", "limite_inferior_soles",
        "limite_superior_soles", "naturaleza", "advertencias", "interpretacion"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for point in lab["puntos"]:
        result = point["resultado"]
        writer.writerow({"factor_area": point["factor_area"], **{k: point["entrada"].get(k) for k in FEATURES},
            **{k: result[k] for k in ("precio_estimado_soles", "limite_inferior_soles", "limite_superior_soles")},
            "naturaleza": lab["naturaleza"], "advertencias": " | ".join(result["advertencias"]),
            "interpretacion": AVISO})
    return "\ufeff" + stream.getvalue()
