"""Pruebas de cuentas de propietarios, sus departamentos y la búsqueda para inquilinos.

Usan una base SQLite temporal: no tocan data/deparent.sqlite.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd

_TEMPORAL = tempfile.TemporaryDirectory()
os.environ["DEPARENT_DB"] = str(Path(_TEMPORAL.name) / "prueba.sqlite")

import cuentas  # noqa: E402  (después de fijar DEPARENT_DB)
from fastapi.testclient import TestClient  # noqa: E402

from api import MERCADO, app  # noqa: E402
from busqueda import valoracion  # noqa: E402
from modelo import ROOT  # noqa: E402

DEMOS = json.loads((ROOT / "data/demo_casos.json").read_text(encoding="utf-8"))


def _registrar(cliente, email, password="clave-de-prueba-1"):
    r = cliente.post("/api/cuentas/registro", json={"nombre": "Propietaria Prueba", "email": email, "password": password})
    return {"Authorization": "Bearer " + r.json()["token"]}


class CuentasTest(unittest.TestCase):
    def setUp(self):
        self.cliente = TestClient(app)

    def test_password_se_guarda_con_hash_y_sal(self):
        _registrar(self.cliente, "hash@deparent.test", "una-clave-larga")
        conexion = cuentas.conectar()
        fila = conexion.execute("SELECT * FROM usuarios WHERE email = 'hash@deparent.test'").fetchone()
        sesiones = [s["token_hash"] for s in conexion.execute("SELECT token_hash FROM sesiones")]
        conexion.close()
        self.assertNotIn(b"una-clave-larga", fila["hash"])
        self.assertEqual(len(fila["sal"]), 16)
        self.assertTrue(all(len(s) == 64 for s in sesiones))

    def test_validaciones_de_registro_e_ingreso(self):
        malo = lambda **d: self.cliente.post("/api/cuentas/registro", json={"nombre": "Ana", "email": "a@deparent.test", "password": "12345678", **d})
        self.assertEqual(malo(password="corta").status_code, 422)
        self.assertEqual(malo(email="sin-arroba").status_code, 422)
        _registrar(self.cliente, "Duplicado@deparent.test")
        self.assertEqual(self.cliente.post("/api/cuentas/registro", json={"nombre": "Otra", "email": "duplicado@deparent.test",
                                                                          "password": "otra-clave-1"}).status_code, 422)
        self.assertEqual(self.cliente.post("/api/cuentas/ingreso", json={"email": "duplicado@deparent.test", "password": "mala-clave"}).status_code, 401)
        self.assertEqual(self.cliente.post("/api/cuentas/ingreso", json={"email": "DUPLICADO@deparent.test",
                                                                         "password": "clave-de-prueba-1"}).status_code, 200)

    def test_rutas_privadas_exigen_sesion_y_salida_la_invalida(self):
        self.assertEqual(self.cliente.get("/api/departamentos").status_code, 401)
        token = _registrar(self.cliente, "salida@deparent.test")
        self.assertEqual(self.cliente.get("/api/cuentas/yo", headers=token).json()["email"], "salida@deparent.test")
        self.cliente.post("/api/cuentas/salida", headers=token)
        self.assertEqual(self.cliente.get("/api/cuentas/yo", headers=token).status_code, 401)


class DepartamentosTest(unittest.TestCase):
    def setUp(self):
        self.cliente = TestClient(app)

    def test_ciclo_completo_y_aislamiento_entre_propietarios(self):
        dueno = _registrar(self.cliente, "dueno@deparent.test")
        otro = _registrar(self.cliente, "otro@deparent.test")
        self.assertEqual(self.cliente.get("/api/departamentos", headers=dueno).json(), [])
        creado = self.cliente.post("/api/departamentos", headers=dueno, json={"nombre": "Depa Lince", "vivienda": DEMOS[0]["entrada"]}).json()
        depto_id = creado["departamento"]["id"]
        self.assertEqual(creado["departamento"]["resumen"]["precio_estimado_soles"], creado["analisis"]["precio"]["precio_estimado_soles"])
        self.assertEqual(self.cliente.get(f"/api/departamentos/{depto_id}", headers=otro).status_code, 404)
        self.assertEqual(self.cliente.delete(f"/api/departamentos/{depto_id}", headers=otro).status_code, 404)

        publicado = self.cliente.post(f"/api/departamentos/{depto_id}/publicacion", headers=dueno,
                                      json={"precio_soles": 2420, "escenario": "Renta superior"}).json()
        self.assertEqual(publicado["publicacion"]["precio_soles"], 2420)
        busqueda = self.cliente.post("/api/buscar", json={"distritos": ["lince"], "limite": 5}).json()
        self.assertEqual(busqueda["resultados"][0]["origen"], "Publicado en DepaRent")
        self.assertEqual(busqueda["resultados"][0]["nombre"], "Depa Lince")
        self.assertNotIn("email", json.dumps(busqueda))

        # Cambiar las características retira la publicación; cambiar solo el nombre no.
        editado = self.cliente.put(f"/api/departamentos/{depto_id}", headers=dueno,
                                   json={"nombre": "Depa Lince 2", "vivienda": DEMOS[0]["entrada"]}).json()
        self.assertIsNotNone(editado["departamento"]["publicacion"])
        editado = self.cliente.put(f"/api/departamentos/{depto_id}", headers=dueno,
                                   json={"nombre": "Depa Lince 2", "vivienda": {**DEMOS[0]["entrada"], "area_total": 55}}).json()
        self.assertIsNone(editado["departamento"]["publicacion"])

        self.assertEqual(self.cliente.delete(f"/api/departamentos/{depto_id}", headers=dueno).status_code, 200)
        self.assertEqual(self.cliente.get("/api/departamentos", headers=dueno).json(), [])

    def test_entradas_invalidas_no_se_guardan(self):
        dueno = _registrar(self.cliente, "invalido@deparent.test")
        r = self.cliente.post("/api/departamentos", headers=dueno, json={"nombre": "X", "vivienda": DEMOS[0]["entrada"]})
        self.assertEqual(r.status_code, 422)
        r = self.cliente.post("/api/departamentos", headers=dueno, json={"nombre": "Depa", "vivienda": {**DEMOS[0]["entrada"], "area_total": 5}})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.cliente.get("/api/departamentos", headers=dueno).json(), [])


class BusquedaTest(unittest.TestCase):
    def setUp(self):
        self.cliente = TestClient(app)

    def test_filtros_se_cumplen_en_todos_los_resultados(self):
        filtros = {"distritos": ["miraflores", "barranco"], "precio_max": 4000, "dormitorios_min": 2, "banos_min": 2,
                   "area_min": 60, "paradero_max_m": 500, "amenidades": ["ascensor", "balcon"], "limite": 60}
        r = self.cliente.post("/api/buscar", json=filtros).json()
        self.assertGreater(r["total"], 0)
        for x in r["resultados"]:
            self.assertIn(x["distrito"], {"miraflores", "barranco"})
            self.assertLessEqual(x["precio_soles"], 4000)
            self.assertGreaterEqual(x["dormitorios"], 2)
            self.assertGreaterEqual(x["area_total"], 60)
            self.assertLessEqual(x["dist_paradero_min_m"], 500)
            self.assertTrue({"ascensor", "balcon"} <= set(x["amenidades"]))

    def test_orden_y_sin_datos_personales(self):
        mercado = self.cliente.post("/api/buscar", json={"distritos": ["surco"], "orden": "precio", "limite": 30}).json()["resultados"]
        precios = [x["precio_soles"] for x in mercado if x["origen"] != "Publicado en DepaRent"]
        self.assertEqual(precios, sorted(precios))
        self.assertFalse({"direccion", "url", "descripcion", "latitud", "longitud"} & set(mercado[0]))

    def test_errores_y_valoracion(self):
        self.assertEqual(self.cliente.post("/api/buscar", json={"orden": "inventado"}).status_code, 422)
        self.assertEqual(self.cliente.post("/api/buscar", json={"amenidades": ["jacuzzi"]}).status_code, 422)
        self.assertEqual(self.cliente.post("/api/buscar", json={"precio_max": 100}).json()["total"], 0)
        self.assertEqual(valoracion(0.85), "Por debajo del estimado")
        self.assertEqual(valoracion(1.0), "En línea con el estimado")
        self.assertEqual(valoracion(1.2), "Por encima del estimado")

    def test_conteos_por_valoracion_filtran_y_suman(self):
        todos = self.cliente.post("/api/buscar", json={"distritos": ["lince"], "limite": 60}).json()
        self.assertEqual(sum(todos["conteos"].values()), todos["total"])
        debajo = self.cliente.post("/api/buscar", json={"distritos": ["lince"], "valoracion": "por_debajo", "limite": 60}).json()
        self.assertEqual(debajo["total"], todos["conteos"]["por_debajo"])
        self.assertTrue(all(x["valoracion"] == "Por debajo del estimado" for x in debajo["resultados"]))
        self.assertEqual(debajo["conteos"], todos["conteos"])
        self.assertEqual(self.cliente.post("/api/buscar", json={"valoracion": "barato"}).status_code, 422)

    def test_mercado_actual_coherente_y_sin_columnas_privadas(self):
        info = json.loads((ROOT / "data/mercado.json").read_text(encoding="utf-8"))
        self.assertEqual(len(MERCADO), info["unicos"])
        self.assertTrue(MERCADO["id"].is_unique)
        self.assertTrue(MERCADO["id"].str.fullmatch(r"m\d+").all())
        self.assertTrue(MERCADO["perfil"].notna().all())
        columnas = set(pd.read_csv(ROOT / "data/mercado.csv", nrows=1).columns)
        self.assertFalse({"direccion", "latitud", "longitud", "descripcion", "titulo", "texto_amenidades_crudo"} & columnas)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class FichaAnuncioTest(unittest.TestCase):
    def setUp(self):
        self.cliente = TestClient(app)

    def test_ficha_de_mercado_sin_datos_privados_ni_contacto(self):
        anuncio_id = MERCADO.iloc[100]["id"]
        r = self.cliente.get(f"/api/anuncios/{anuncio_id}")
        self.assertEqual(r.status_code, 200)
        f = r.json()
        self.assertEqual(f["anuncio"]["id"], anuncio_id)
        self.assertIsNone(f["publicacion"])
        self.assertEqual(f["precio"]["precio_estimado_soles"], f["anuncio"]["precio_estimado_soles"])
        self.assertEqual(len(f["perfil"]["comparables"]), 8)
        # El enlace al original va solo en "original"; dirección, coordenadas y texto del anuncio nunca.
        texto = json.dumps({k: v for k, v in f.items() if k != "original"})
        for privado in ("direccion", "latitud", "longitud", "url", "descripcion", "paradero_cercano_nombre"):
            self.assertNotIn(privado, texto)
        self.assertEqual(set(f["original"]), {"url", "portal", "capturado"})
        self.assertEqual(self.cliente.post(f"/api/anuncios/{anuncio_id}/interes",
                                           json={"nombre": "Ana", "email": "ana@deparent.test", "mensaje": "Me interesa"}).status_code, 422)

    def test_comparables_llevan_a_su_ficha_y_el_original_solo_va_a_los_portales(self):
        f = self.cliente.get(f"/api/anuncios/{MERCADO.iloc[100]['id']}").json()
        self.assertIn(f["original"]["portal"], {"Adondevivir", "Urbania"})
        self.assertTrue(f["original"]["url"].startswith(("https://www.adondevivir.com/", "https://urbania.pe/")))
        for c in f["perfil"]["comparables"]:
            self.assertEqual(self.cliente.get(f"/api/anuncios/{c['anuncio_id']}").status_code, 200, c["anuncio_id"])
        analisis = self.cliente.post("/api/analizar", json={"vivienda": DEMOS[1]["entrada"]}).json()
        ids = [c["anuncio_id"] for c in analisis["perfil"]["comparables"]]
        self.assertEqual(len(set(ids)), 8)
        self.assertTrue(set(ids) <= set(MERCADO["id"]))

    def test_ids_invalidos_o_inexistentes_dan_404(self):
        for anuncio_id in ("m99999999", "x1", "d99999", "1"):
            self.assertEqual(self.cliente.get(f"/api/anuncios/{anuncio_id}").status_code, 404, anuncio_id)

    def test_interes_llega_solo_al_propietario_y_solo_si_esta_publicado(self):
        dueno = _registrar(self.cliente, "ficha.dueno@deparent.test")
        otro = _registrar(self.cliente, "ficha.otro@deparent.test")
        creado = self.cliente.post("/api/departamentos", headers=dueno, json={"nombre": "Depa Surquillo", "vivienda": {**DEMOS[0]["entrada"], "distrito_norm": "surquillo"}}).json()
        depto_id = creado["departamento"]["id"]
        mensaje = {"nombre": "Inquilina Prueba", "email": "inquilina@deparent.test", "mensaje": "Hola, ¿sigue disponible?"}
        # Borrador: no tiene ficha pública ni recibe mensajes.
        self.assertEqual(self.cliente.get(f"/api/anuncios/d{depto_id}").status_code, 404)
        self.assertEqual(self.cliente.post(f"/api/anuncios/d{depto_id}/interes", json=mensaje).status_code, 404)
        self.cliente.post(f"/api/departamentos/{depto_id}/publicacion", headers=dueno, json={"precio_soles": 2100, "escenario": "Equilibrado"})
        ficha = self.cliente.get(f"/api/anuncios/d{depto_id}").json()
        self.assertEqual(ficha["publicacion"]["propietario"], "Propietaria")
        self.assertIsNone(ficha["original"])
        self.assertNotIn("ficha.dueno@deparent.test", json.dumps(ficha))
        self.assertEqual(self.cliente.post(f"/api/anuncios/d{depto_id}/interes", json={**mensaje, "email": "sin-arroba"}).status_code, 422)
        self.assertEqual(self.cliente.post(f"/api/anuncios/d{depto_id}/interes", json=mensaje).status_code, 200)
        visto = self.cliente.get(f"/api/departamentos/{depto_id}", headers=dueno).json()["departamento"]["interesados"]
        self.assertEqual([(i["nombre"], i["email"]) for i in visto], [("Inquilina Prueba", "inquilina@deparent.test")])
        self.assertEqual(self.cliente.get(f"/api/departamentos/{depto_id}", headers=otro).status_code, 404)
