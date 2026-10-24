"""Modelo 5: tres precios de publicación a partir de los modelos 1, 3 y 4.

No es un modelo de aprendizaje automático. Son reglas explícitas:
- Equilibrado: el precio esperado del modelo 3.
- Competitivo: el punto medio entre el precio esperado y el percentil 25 de los comparables,
  y como máximo 5% por debajo del esperado.
- Renta superior: el punto medio entre el precio esperado y el percentil 75 de los comparables,
  y como mínimo 5% por encima del esperado.
Los tres quedan dentro del rango calibrado del modelo 3 y se redondean a S/ 10.
La tendencia del modelo 4 solo cambia qué escenario se sugiere, no los montos.
"""
import numpy as np

AJUSTE_MINIMO = 0.05
REDONDEO = 10
AVISO = ("Reglas de apoyo a la decisión con precios pedidos en anuncios. No son tasaciones, no garantizan el tiempo "
         "de alquiler y no se validaron con contratos cerrados.")


def _redondear(valor):
    return float(REDONDEO * round(valor / REDONDEO))


def _posicion(precio, precios_comparables):
    """Porcentaje de comparables que piden menos que este precio."""
    return round(100 * float(np.mean(np.asarray(precios_comparables, float) < precio)), 1)


def sugerir_escenario(tendencia):
    if not tendencia.get("serie_propia"):
        return "Equilibrado", "El distrito no tiene serie propia en el BCRP; sin una señal local se sugiere el escenario equilibrado."
    if tendencia["tendencia"] == "Al alza":
        return "Renta superior", "La serie del distrito proyecta alza; hay margen para publicar por encima del esperado y ajustar si no hay interesados."
    if tendencia["tendencia"] == "A la baja":
        return "Competitivo", "La serie del distrito proyecta baja; un precio competitivo reduce el riesgo de que el anuncio quede sin interesados."
    return "Equilibrado", "La serie del distrito se mantiene estable; el precio esperado es el punto de partida razonable."


def escenarios_publicacion(precio, competencia, tendencia):
    """precio: salida de modelo.predecir; competencia: de perfil_competitivo.comparables; tendencia: de tendencia.tendencia_distrital."""
    esperado = precio["precio_estimado_soles"]
    inferior, superior = precio["limite_inferior_soles"], precio["limite_superior_soles"]
    p25, p75 = competencia["precio_p25_soles"], competencia["precio_p75_soles"]
    precios = [c["Precio pedido (S/)"] for c in competencia["comparables"]]
    montos = {
        "Competitivo": min((esperado + p25) / 2, esperado * (1 - AJUSTE_MINIMO)),
        "Equilibrado": esperado,
        "Renta superior": max((esperado + p75) / 2, esperado * (1 + AJUSTE_MINIMO)),
    }
    descripciones = {
        "Competitivo": "Prioriza alquilar rápido: se acerca a los comparables más baratos.",
        "Equilibrado": "El precio esperado por el modelo para estas características.",
        "Renta superior": "Prioriza el ingreso mensual: se acerca a los comparables más caros y puede tardar más.",
    }
    sugerido, motivo = sugerir_escenario(tendencia)
    escenarios = []
    for nombre, monto in montos.items():
        valor = _redondear(float(np.clip(monto, inferior, superior)))
        escenarios.append({"escenario": nombre, "precio_soles": valor,
                           "diferencia_vs_esperado_porcentaje": round(100 * (valor - esperado) / esperado, 2),
                           "comparables_mas_baratos_porcentaje": _posicion(valor, precios),
                           "descripcion": descripciones[nombre], "sugerido": nombre == sugerido})
    return {"escenarios": escenarios, "sugerido": sugerido, "motivo": motivo,
            "reglas": __doc__.split("\n\n", 1)[1].strip(), "aviso": AVISO}
