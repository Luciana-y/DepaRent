"""Pruebas de los modelos 4 (tendencia) y 5 (escenarios de publicación) y de la API web."""
import copy
import json
import unittest

import joblib
import pandas as pd
from fastapi.testclient import TestClient

from api import app
from escenarios import comparar
from escenarios_precio import escenarios_publicacion, sugerir_escenario
from modelo import ROOT, normalizar, predecir
from perfil_competitivo import ARCHIVO, comparables
from tendencia import HORIZONTE, cargar_tendencias, clasificar_tendencia, tendencia_distrital

SERIES = ROOT.parent / "week07/data/bcrp_serie_completa.csv"


class TendenciaTest(unittest.TestCase):
    def test_una_serie_por_distrito_del_bcrp_con_pronostico(self):
        datos = cargar_tendencias()
        esperados = {normalizar(d) for d in pd.read_csv(SERIES)["Distrito"].unique()}
        self.assertEqual(set(datos["series"]), esperados)
        for serie in datos["series"].values():
            self.assertEqual(len(serie["pronostico"]), HORIZONTE)
            self.assertEqual(serie["pronostico"][0]["trimestre"], "2026-T2")
            for punto in serie["pronostico"]:
                self.assertLessEqual(punto["inferior_80"], punto["valor"])
                self.assertLessEqual(punto["valor"], punto["superior_80"])
            self.assertEqual(len(serie["validacion"]["trimestres"]), 4)
            self.assertIn(serie["tendencia"], {"Al alza", "A la baja", "Estable"})

    def test_etiqueta_respeta_la_regla_de_dos_por_ciento(self):
        self.assertEqual(clasificar_tendencia([10] * 4, [10.3] * 4)["tendencia"], "Al alza")
        self.assertEqual(clasificar_tendencia([10] * 4, [9.7] * 4)["tendencia"], "A la baja")
        self.assertEqual(clasificar_tendencia([10] * 4, [10.1] * 4)["tendencia"], "Estable")

    def test_distrito_sin_serie_usa_promedio_y_lo_indica(self):
        self.assertTrue(tendencia_distrital("Lince")["serie_propia"])
        sin_serie = tendencia_distrital("ate")
        self.assertFalse(sin_serie["serie_propia"])
        self.assertEqual(normalizar(sin_serie["distrito"]), "promedio")


class EscenariosPublicacionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.precio = joblib.load(ROOT / "models/modelo_docente.joblib")
        cls.perfil = joblib.load(ARCHIVO)
        cls.demos = json.loads((ROOT / "data/demo_casos.json").read_text(encoding="utf-8"))

    def test_orden_rango_y_redondeo(self):
        for demo in self.demos:
            entrada = demo["entrada"]
            precio = predecir(entrada, self.precio)
            resultado = escenarios_publicacion(precio, comparables(entrada, self.perfil), tendencia_distrital(entrada["distrito_norm"]))
            montos = [e["precio_soles"] for e in resultado["escenarios"]]
            self.assertEqual([e["escenario"] for e in resultado["escenarios"]], ["Competitivo", "Equilibrado", "Renta superior"])
            self.assertLess(montos[0], montos[1])
            self.assertLess(montos[1], montos[2])
            for monto in montos:
                self.assertEqual(monto % 10, 0)
                self.assertGreaterEqual(monto, precio["limite_inferior_soles"] - 5)
                self.assertLessEqual(monto, precio["limite_superior_soles"] + 5)
            self.assertEqual(sum(e["sugerido"] for e in resultado["escenarios"]), 1)

    def test_sugerencia_segun_tendencia(self):
        self.assertEqual(sugerir_escenario({"serie_propia": True, "tendencia": "Al alza"})[0], "Renta superior")
        self.assertEqual(sugerir_escenario({"serie_propia": True, "tendencia": "A la baja"})[0], "Competitivo")
        self.assertEqual(sugerir_escenario({"serie_propia": True, "tendencia": "Estable"})[0], "Equilibrado")
        self.assertEqual(sugerir_escenario({"serie_propia": False, "tendencia": "Al alza"})[0], "Equilibrado")


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cliente = TestClient(app)
        cls.precio = joblib.load(ROOT / "models/modelo_docente.joblib")
        cls.demos = json.loads((ROOT / "data/demo_casos.json").read_text(encoding="utf-8"))

    def test_analizar_devuelve_los_seis_componentes_en_json_estricto(self):
        for demo in self.demos:
            respuesta = self.cliente.post("/api/analizar", json={"vivienda": demo["entrada"]})
            self.assertEqual(respuesta.status_code, 200, respuesta.text)
            datos = json.loads(respuesta.text, parse_constant=lambda c: self.fail(f"Valor no JSON: {c}"))
            self.assertEqual(set(datos), {"vivienda", "ubicacion", "precio", "evidencia_distrital", "avisos", "perfil",
                                          "accesibilidad", "tendencia", "publicacion"})
            self.assertEqual(datos["precio"], predecir(demo["entrada"], self.precio))

    def test_errores_de_entrada_son_422_con_mensaje(self):
        mala = {**self.demos[0]["entrada"], "area_total": 5}
        respuesta = self.cliente.post("/api/analizar", json={"vivienda": mala})
        self.assertEqual(respuesta.status_code, 422)
        self.assertIn("area_total", respuesta.json()["detail"])
        fuera = self.cliente.post("/api/accesibilidad", json={"latitud": -13.0, "longitud": -77.0})
        self.assertEqual(fuera.status_code, 422)

    def test_comparar_y_area_coinciden_con_los_modulos_del_profesor(self):
        base = copy.deepcopy(self.demos[1]["entrada"])
        respuesta = self.cliente.post("/api/comparar", json={"vivienda": base, "cambios": {"area_total": 108}}).json()
        self.assertEqual(respuesta["diferencia_soles"], comparar(base, {"area_total": 108}, self.precio)["diferencia_soles"])
        area = self.cliente.post("/api/area", json=self.demos[2]["entrada"]).json()
        self.assertEqual(area["puntos"][2]["resultado"]["precio_estimado_soles"], 7077.25)

    def test_sirve_el_frontend(self):
        self.assertEqual(self.cliente.get("/").status_code, 200)
        self.assertEqual(self.cliente.get("/js/main.js").status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
