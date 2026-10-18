"""Estimador mínimo: mediana de alquiler (precio_soles) por distrito.

Es un placeholder del prototipo. Se reemplazará por el modelo HistGradientBoosting
serializado en models/ cuando esté disponible.
"""
import pandas as pd

from config import find_data_file

PRICE_COL = "precio_soles"  # alquiler mensual en soles (precio y moneda originales se mezclan)
DISTRICT_COL = "distrito"


class Estimator:
    def __init__(self, data_path=None):
        self.data_path = data_path or find_data_file("departamentos_procesados.csv")
        self.medians = {}
        self.default = None
        self._load()

    def _load(self):
        df = pd.read_csv(self.data_path, low_memory=False)
        missing = [c for c in (PRICE_COL, DISTRICT_COL) if c not in df.columns]
        if missing:
            raise ValueError(f"Faltan columnas {missing} en {self.data_path}")
        df = df[[DISTRICT_COL, PRICE_COL]].dropna()
        self.medians = df.groupby(DISTRICT_COL)[PRICE_COL].median().to_dict()
        self.default = float(df[PRICE_COL].median())

    def predict(self, distrito):
        if not distrito:
            return self.default
        key = str(distrito).strip()
        lookup = {k.lower(): v for k, v in self.medians.items()}
        return float(lookup.get(key.lower(), self.default))
