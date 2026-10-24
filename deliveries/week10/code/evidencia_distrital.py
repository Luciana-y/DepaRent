"""Resumen agregado de la prueba reservada, sin mostrar anuncios individuales."""
import csv
import math

from modelo import ROOT, normalizar


ARCHIVO = ROOT / "resultados/error_por_distrito.csv"
MINIMO_ORIENTATIVO = 20


def evidencia_distrital(distrito, archivo=ARCHIVO):
    """Devuelve el error histórico del distrito o None si no hubo casos de prueba.

    El umbral de 20 solo sirve para advertir sobre muestras muy pequeñas;
    no convierte el MAE distrital en una garantía para una vivienda nueva.
    """
    buscado = normalizar(distrito)
    with archivo.open(encoding="utf-8-sig", newline="") as fuente:
        for fila in csv.DictReader(fuente):
            if normalizar(fila["distrito"]) != buscado:
                continue
            cantidad = int(fila["n"])
            mae = float(fila["MAE_soles"])
            if cantidad < 1 or not math.isfinite(mae) or mae < 0:
                raise ValueError("El resumen de prueba por distrito tiene valores inválidos.")
            return {
                "distrito": buscado,
                "anuncios_prueba": cantidad,
                "error_absoluto_medio_soles": mae,
                "muestra_pequena": cantidad < MINIMO_ORIENTATIVO,
            }
    return None
