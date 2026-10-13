import os
import pandas as pd

class Estimator:
    def __init__(self, data_path=None):
        if data_path is None:
            data_path = os.path.join(os.getcwd(), 'deliveries', 'week07', 'data', 'departamentos_procesados.csv')
        self.data_path = data_path
        self.medians = None
        self.default = None
        self._load()

    def _load(self):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError(f"Dataset not found at {self.data_path}. Ensure deliveries/week07/data/departamentos_procesados.csv exists")
        df = pd.read_csv(self.data_path, low_memory=False)
        # Detect probable column names
        price_col = next((c for c in df.columns if 'precio' in c.lower()), None)
        distrito_col = next((c for c in df.columns if 'distrito' in c.lower()), None)
        if price_col is None or distrito_col is None:
            raise ValueError(f"No se encontraron las columnas de precio/distrito en {self.data_path}. Columnas disponibles: {df.columns.tolist()}")
        df = df[[distrito_col, price_col]].dropna()
        self.medians = df.groupby(distrito_col)[price_col].median().to_dict()
        self.default = float(df[price_col].median())

    def predict(self, distrito):
        if self.medians is None:
            self._load()
        if distrito is None:
            return self.default
        return float(self.medians.get(distrito, self.default))
