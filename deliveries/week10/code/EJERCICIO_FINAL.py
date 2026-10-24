"""Actividad breve: comprueba el error de prueba de un distrito.

Trabaja con predicciones ya reservadas. No entrena ni guarda archivos.
Ejecuta este archivo desde version_docente después de instalar requirements.txt.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent  # deliveries/week10


DISTRITO = "lince"  # Puedes cambiarlo por otro distrito con 20 o más casos de prueba.


def main():
    archivo = ROOT / "resultados/predicciones_prueba.csv"
    prueba = pd.read_csv(archivo)
    columnas = {"distrito", "real_soles", "prediccion_soles"}
    if not columnas.issubset(prueba.columns):
        raise ValueError("Faltan columnas necesarias en predicciones_prueba.csv.")
    if DISTRITO not in set(prueba["distrito"]):
        raise ValueError("El distrito elegido no figura en la muestra de prueba.")

    print(f"Muestra de prueba cargada. Distrito elegido: {DISTRITO}.")

    # 1. Filas de prueba del distrito y su cantidad.
    filas = prueba[prueba["distrito"] == DISTRITO]
    n = len(filas)
    if n < 20:
        raise ValueError(f"{DISTRITO} tiene {n} casos de prueba; elige un distrito con 20 o más.")

    # 2. Error absoluto de cada anuncio y su promedio (MAE en soles).
    errores = (filas["real_soles"] - filas["prediccion_soles"]).abs()
    mae = errores.mean()

    # 3. Resultado y contraste con la aplicación (resultados/error_por_distrito.csv).
    resumen = pd.read_csv(ROOT / "resultados/error_por_distrito.csv").set_index("distrito")
    app_n, app_mae = int(resumen.loc[DISTRITO, "n"]), float(resumen.loc[DISTRITO, "MAE_soles"])
    print()
    print(pd.DataFrame([{"Distrito": DISTRITO.title(), "n (prueba)": n, "MAE calculado (S/)": round(mae, 2),
                         "n en la app": app_n, "MAE en la app (S/)": round(app_mae, 2)}]).to_string(index=False))
    print()
    print("Coincide con la aplicación." if n == app_n and abs(mae - app_mae) < 0.005
          else "No coincide: revisar el filtro y el redondeo antes de cambiar el modelo.")
    print(f"Error individual: mediana S/ {errores.median():,.2f}, mínimo S/ {errores.min():,.2f}, máximo S/ {errores.max():,.2f}.")
    print("El MAE es un promedio de anuncios de septiembre de 2026: no es el error de otra vivienda ni de meses posteriores.")


if __name__ == "__main__":
    main()
