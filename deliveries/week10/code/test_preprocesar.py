"""El preprocesamiento en módulo reproduce exactamente los datos procesados de la Semana 7.

Es la garantía de que una captura nueva (por ejemplo, la de octubre) se procesa igual que la de entrenamiento.
"""
import unittest

import joblib
import numpy as np
import pandas as pd

from modelo import ROOT, SOURCE, preparar
from preprocesar import procesar

COLUMNAS = ["precio_soles", "area_total", "dormitorios", "banos", "estacionamientos", "antiguedad", "mantenimiento",
            "ascensor", "balcon", "terraza", "piscina", "gimnasio", "pet_friendly", "piso", "precio_m2_real"]


class PreprocesarTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.crudo = pd.read_csv(ROOT.parent / "week04/data/departamentos_alquiler_lima.csv")
        cls.referencia = pd.read_csv(SOURCE, low_memory=False)
        cls.artefacto = joblib.load(ROOT / "models/modelo_docente.joblib")

    def _comparar(self, nuevo):
        self.assertEqual(list(nuevo["id_anuncio"].astype(str)), list(self.referencia["id_anuncio"].astype(str)))
        for col in COLUMNAS:
            self.assertTrue(np.allclose(nuevo[col].astype(float), self.referencia[col].astype(float), equal_nan=True), col)
        self.assertTrue((nuevo["distrito_norm"].str.lower() == self.referencia["distrito_norm"].str.lower()).all())
        self.assertTrue(np.allclose(self.artefacto["pipeline"].predict(preparar(nuevo)),
                                    self.artefacto["pipeline"].predict(preparar(self.referencia))))

    def test_reproduce_septiembre_con_el_umbral_de_otros(self):
        self._comparar(procesar(self.crudo))

    def test_reproduce_septiembre_con_los_distritos_del_modelo(self):
        # El modo que se usa con capturas nuevas: los distritos fuera del entrenamiento van a "Otros".
        self._comparar(procesar(self.crudo, distritos_conocidos=self.artefacto["distritos"]))

    def test_un_distrito_desconocido_va_a_otros(self):
        fila = self.crudo.iloc[[0]].copy()
        fila["distrito"] = "Pachacámac"
        fila[["precio_soles", "area_total", "latitud", "longitud"]] = [2000, 60, -12.1, -77.0]
        procesado = procesar(fila, distritos_conocidos=self.artefacto["distritos"])
        self.assertEqual(procesado.loc[0, "distrito_norm"], "Otros")


if __name__ == "__main__":
    unittest.main(verbosity=2)
