"""Pruebas de la sección de analista: rol por correo, KPIs protegidos, precio propio y orden del perfil.

Usan una base SQLite temporal: no tocan data/deparent.sqlite.
"""
import os
import tempfile
import unittest
import uuid
from pathlib import Path

_TEMPORAL = tempfile.TemporaryDirectory()
os.environ.setdefault("DEPARENT_DB", str(Path(_TEMPORAL.name) / "prueba.sqlite"))

from fastapi.testclient import TestClient  # noqa: E402

from api import app  # noqa: E402

VIVIENDA = {"distrito_norm": "lince", "area_total": 70, "dormitorios": 2, "banos": 2}


def _cuenta(cliente, prefijo="usuario"):
    email = f"{prefijo}-{uuid.uuid4().hex[:8]}@ejemplo.com"
    r = cliente.post("/api/cuentas/registro", json={"nombre": "Prueba", "email": email, "password": "clave-de-prueba-1"})
    return email, r.json(), {"Authorization": "Bearer " + r.json()["token"]}


class KpisAnalista(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cliente = TestClient(app)
        cls.email_analista = f"analista-{uuid.uuid4().hex[:8]}@ejemplo.com"
        os.environ["DEPARENT_ANALISTAS"] = f"otra@ejemplo.com, {cls.email_analista.upper()}"

    @classmethod
    def tearDownClass(cls):
        os.environ.pop("DEPARENT_ANALISTAS", None)

    def _analista(self):
        r = self.cliente.post("/api/cuentas/registro", json={"nombre": "Analista", "email": self.email_analista, "password": "clave-de-prueba-1"})
        if r.status_code != 200:
            r = self.cliente.post("/api/cuentas/ingreso", json={"email": self.email_analista, "password": "clave-de-prueba-1"})
        return r.json(), {"Authorization": "Bearer " + r.json()["token"]}

    def test_kpis_exigen_sesion_y_rol(self):
        self.assertEqual(self.cliente.get("/api/kpis").status_code, 401)
        _, cuerpo, cabecera = _cuenta(self.cliente)
        self.assertEqual(cuerpo["usuario"]["rol"], "usuario")
        self.assertEqual(self.cliente.get("/api/kpis", headers=cabecera).status_code, 403)

    def test_analista_ve_los_kpis(self):
        cuerpo, cabecera = self._analista()
        self.assertEqual(cuerpo["usuario"]["rol"], "analista")
        self.assertEqual(self.cliente.get("/api/cuentas/yo", headers=cabecera).json()["rol"], "analista")
        r = self.cliente.get("/api/kpis", headers=cabecera)
        self.assertEqual(r.status_code, 200)
        k = r.json()
        self.assertGreaterEqual(k["producto"]["usuarios"], 1)
        self.assertLess(k["modelo"]["prueba"]["modelo"]["mae_soles"], k["modelo"]["prueba"]["baseline_distrital"]["mae_soles"])
        self.assertTrue(k["modelo"]["validaciones"])
        self.assertGreater(k["datos"]["en_la_app"], 0)
        # Sin datos personales en los KPIs.
        self.assertNotIn("@", r.text)

    def test_publicar_a_precio_propio_y_cambiarlo(self):
        _, _, cabecera = _cuenta(self.cliente, "propietario")
        d = self.cliente.post("/api/departamentos", headers=cabecera, json={"nombre": "Depa prueba", "vivienda": VIVIENDA}).json()["departamento"]
        url = f"/api/departamentos/{d['id']}/publicacion"
        r = self.cliente.post(url, headers=cabecera, json={"precio_soles": 2345, "escenario": "Personalizado"})
        self.assertEqual(r.json()["publicacion"]["precio_soles"], 2345)
        r = self.cliente.post(url, headers=cabecera, json={"precio_soles": 2400, "escenario": "Personalizado"})
        self.assertEqual(r.json()["publicacion"]["precio_soles"], 2400)
        self.assertEqual(self.cliente.post(url, headers=cabecera, json={"precio_soles": 50}).status_code, 422)

    def test_orden_del_perfil_se_guarda_y_se_valida(self):
        _, _, cabecera = _cuenta(self.cliente, "inquilino")
        perfil = {"hogar": "pareja", "presupuesto_max": 3000, "orden": "precio"}
        r = self.cliente.put("/api/perfil", headers=cabecera, json=perfil)
        self.assertEqual(r.json()["perfil"]["orden"], "precio")
        self.assertEqual(self.cliente.put("/api/perfil", headers=cabecera, json={**perfil, "orden": "otro"}).status_code, 422)
        self.assertEqual(self.cliente.post("/api/recomendar", json={**perfil, "limite": 5}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
