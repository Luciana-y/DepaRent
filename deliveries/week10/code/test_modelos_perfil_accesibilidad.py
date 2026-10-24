"""Pruebas de los modelos 1 (perfil competitivo) y 2 (accesibilidad), sin reentrenar."""
import copy
import json
import unittest

import joblib
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from accesibilidad import accesibilidad, cargar_red, centro_distrito
from modelo import ROOT, SOURCE
from perfil_competitivo import ARCHIVO, VARIABLES, comparables
from escenarios import verificar_modelo_congelado

COLUMNAS_ACCESO = ["dist_paradero_min_m", "paraderos_300m", "paraderos_500m", "paraderos_1000m",
                   "dist_troncal_brt_m", "dist_corredor_m"]


class AccesibilidadTest(unittest.TestCase):
    def test_reproduce_variables_del_notebook(self):
        anuncios = pd.read_csv(SOURCE, low_memory=False).sample(300, random_state=0)
        red = cargar_red()
        for fila in anuncios.itertuples():
            resultado = accesibilidad(fila.latitud, fila.longitud, red)
            for columna in COLUMNAS_ACCESO:
                self.assertAlmostEqual(resultado[columna], getattr(fila, columna), places=1, msg=columna)
            self.assertEqual(resultado["paradero_cercano_tipo"], fila.paradero_cercano_tipo)

    def test_rechaza_coordenadas_fuera_de_lima_o_no_numericas(self):
        for lat, lon in ((-13.5, -77.0), (-12.0, -76.0), ("abc", -77.0), (float("nan"), -77.0)):
            with self.assertRaises(ValueError):
                accesibilidad(lat, lon)

    def test_centro_de_distrito_y_cercanos_ordenados(self):
        self.assertIsNotNone(centro_distrito("Lince"))
        self.assertIsNone(centro_distrito("distrito inexistente"))
        resultado = accesibilidad(*centro_distrito("lince"))
        distancias = [p["Distancia (m)"] for p in resultado["cercanos"]]
        self.assertEqual(distancias, sorted(distancias))
        self.assertEqual(distancias[0], resultado["dist_paradero_min_m"])
        self.assertIn(resultado["nivel"], {"Alta", "Media", "Baja"})


class PerfilCompetitivoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = joblib.load(ARCHIVO)
        cls.profiles = json.loads((ROOT / "data/demo_casos.json").read_text(encoding="utf-8"))

    def test_no_usa_precio_para_agrupar(self):
        self.assertFalse({"precio_soles", "precio_m2", "precio_m2_real"} & set(VARIABLES))
        self.assertEqual(self.artifact["metricas"]["variables"], VARIABLES)

    def test_cuatro_perfiles_con_nombres_distintos(self):
        self.assertEqual(sorted(self.artifact["nombres"]), [0, 1, 2, 3])
        self.assertEqual(len(set(self.artifact["nombres"].values())), 4)

    def test_comparables_sin_duplicados_ni_datos_personales(self):
        for profile in self.profiles:
            base = copy.deepcopy(profile["entrada"])
            resultado = comparables(base, self.artifact)
            self.assertEqual(base, profile["entrada"])
            self.assertEqual(len(resultado["comparables"]), 8)
            self.assertEqual(resultado["en_mismo_distrito"], 8)
            columnas = set(resultado["comparables"][0])
            self.assertFalse({"direccion", "url", "descripcion", "latitud", "longitud", "titulo"} & columnas)
            self.assertLessEqual(resultado["precio_p25_soles"], resultado["precio_mediana_soles"])
            self.assertLessEqual(resultado["precio_mediana_soles"], resultado["precio_p75_soles"])
        referencia = self.artifact["referencia"]
        self.assertFalse({"direccion", "url", "descripcion", "latitud", "longitud"} & set(referencia.columns))

    def test_amenidad_desconocida_se_imputa(self):
        base = {**self.profiles[0]["entrada"], "piscina": None, "antiguedad": None}
        self.assertIn(comparables(base, self.artifact)["perfil"]["cluster"], range(4))

    def test_apptest_muestra_perfil_y_accesibilidad(self):
        verificar_modelo_congelado()
        app = AppTest.from_file(str(ROOT / "code/app.py"), default_timeout=60).run()
        self.assertFalse(app.exception, str(app.exception))
        next(b for b in app.button if b.label == "Estimar alquiler").click().run()
        self.assertFalse(app.exception, str(app.exception))
        labels = {m.label for m in app.metric}
        self.assertIn("Perfil del departamento", labels)
        self.assertIn("Nivel de accesibilidad", labels)
        name = self.profiles[0]["nombre"]
        app.number_input(key=f"lat_{name}_lince").set_value(-12.0846)
        app.number_input(key=f"lon_{name}_lince").set_value(-77.0350)
        next(b for b in app.button if b.label == "Calcular accesibilidad").click().run()
        self.assertFalse(app.exception, str(app.exception))
        guardado = app.session_state["accesibilidad_" + name]
        self.assertEqual(guardado["origen"], "coordenadas ingresadas")
        self.assertEqual(guardado["resultado"], accesibilidad(-12.0846, -77.0350))


if __name__ == "__main__":
    unittest.main(verbosity=2)
