"""Ayudas de presentación. No alteran entradas ni predicciones del modelo."""
import math

ETIQUETAS = {
    "distrito_norm": "Distrito", "area_total": "Área total (m²)", "dormitorios": "Dormitorios",
    "banos": "Baños", "estacionamientos": "Estacionamientos", "antiguedad": "Antigüedad (años)",
    "mantenimiento": "Mantenimiento mensual (S/)", "ascensor": "Ascensor", "balcon": "Balcón",
    "terraza": "Terraza", "piscina": "Piscina", "gimnasio": "Gimnasio", "pet_friendly": "Admite mascotas",
}
BINARIAS = {"ascensor", "balcon", "terraza", "piscina", "gimnasio", "pet_friendly"}

def mostrar_valor(campo, valor):
    if valor is None:
        return "Desconocido"
    if campo in BINARIAS:
        return "Sí" if valor == 1 else "No"
    return str(valor)

def tabla_entrada(entrada):
    return [{"Entrada utilizada": etiqueta, "Valor": mostrar_valor(campo, entrada.get(campo))}
            for campo, etiqueta in ETIQUETAS.items()]

def tabla_comparacion(base, alternativa):
    return [{"Entrada utilizada": etiqueta, "Base": mostrar_valor(campo, base.get(campo)),
             "Alternativa": mostrar_valor(campo, alternativa.get(campo)),
             "Cambió": "Sí" if base.get(campo) != alternativa.get(campo) else "—"}
            for campo, etiqueta in ETIQUETAS.items()]

def avisos_coherencia(entrada):
    """Umbral elegido para revisar casos extremos; no es norma ni dato aprendido."""
    try:
        area = float(entrada.get("area_total"))
        cantidades = [float(entrada.get(c, 0) or 0) for c in ("dormitorios", "banos", "estacionamientos")]
    except (TypeError, ValueError):
        return []
    if all(math.isfinite(v) for v in [area] + cantidades) and area <= 30 and any(v >= 6 for v in cantidades):
        return ["Revisa esta combinación: 30 m² o menos con 6 o más dormitorios, baños o estacionamientos. "
                "Es una regla heurística de apoyo para esta demostración, no una norma de vivienda ni un límite aprendido del mercado. "
                "Verifica las unidades y características antes de interpretar el resultado; la regla no cambia la predicción."]
    return []
