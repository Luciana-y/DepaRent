"""Pruebas del laboratorio sin navegador, servidores ni reentrenamiento."""
import copy
import csv
import io
import json
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
import joblib
from streamlit.testing.v1 import AppTest
from streamlit.runtime.memory_media_file_storage import MemoryMediaFileStorage
from modelo import ROOT, predecir
from laboratorio_area import explorar_area, tabla_area, csv_area
from escenarios import verificar_modelo_congelado


class LaboratorioAreaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        verificar_modelo_congelado()
        cls.model = joblib.load(ROOT / "models/modelo_docente.joblib")
        cls.profiles = json.loads((ROOT / "data/demo_casos.json").read_text(encoding="utf-8"))
        cls.catalog = json.loads((ROOT / "resultados/simulacion_v2/consultas_54.json").read_text(encoding="utf-8"))["consultas"]

    def test_tres_areas_solo_cambia_area_y_no_muta_base(self):
        for profile in self.profiles:
            base = copy.deepcopy(profile["entrada"])
            before = copy.deepcopy(base)
            lab = explorar_area(base, self.model)
            self.assertEqual(base, before)
            self.assertEqual([p["factor_area"] for p in lab["puntos"]], [0.8, 1.0, 1.2])
            for point in lab["puntos"]:
                self.assertEqual({k: v for k, v in point["entrada"].items() if k != "area_total"},
                                 {k: v for k, v in base.items() if k != "area_total"})
                self.assertEqual(point["resultado"], predecir(point["entrada"], self.model))
            self.assertEqual(lab["puntos"][1]["entrada"], base)

    def test_concordancia_con_nueve_consultas_guardadas(self):
        for profile in self.profiles:
            lab = explorar_area(profile["entrada"], self.model)
            for point in lab["puntos"]:
                stored = [c for c in self.catalog if c["perfil"] == profile["nombre"]
                          and c["alternativa_entrada"] == point["entrada"]]
                self.assertEqual(len(stored), 1)
                self.assertEqual(point["resultado"], stored[0]["alternativa_resultado"])

    def test_validacion_no_recorta_ni_oculta_area_invalida(self):
        for area in (25, 450, 0, -1, 90.5, float("nan"), float("inf"), True, None, "abc"):
            with self.subTest(area=area):
                base = {**self.profiles[0]["entrada"], "area_total": area}
                with self.assertRaises(ValueError):
                    explorar_area(base, self.model)
        for changes in ({"distrito_norm": "otro"}, {"banos": 100}, {"balcon": 3}):
            with self.assertRaises(ValueError):
                explorar_area({**self.profiles[0]["entrada"], **changes}, self.model)

    def test_tabla_y_exportacion_completa(self):
        lab = explorar_area(self.profiles[1]["entrada"], self.model)
        rows = list(csv.DictReader(io.StringIO(csv_area(lab).lstrip("\ufeff"))))
        self.assertEqual(len(rows), 3)
        self.assertEqual(len(tabla_area(lab)), 3)
        for row, point in zip(rows, lab["puntos"]):
            self.assertEqual(float(row["area_total"]), point["entrada"]["area_total"])
            self.assertEqual(float(row["precio_estimado_soles"]), point["resultado"]["precio_estimado_soles"])
            self.assertEqual(float(row["limite_inferior_soles"]), point["resultado"]["limite_inferior_soles"])
            self.assertEqual(float(row["limite_superior_soles"]), point["resultado"]["limite_superior_soles"])
            self.assertEqual(float(row["mantenimiento"]), 400)
            self.assertIn("no anuncios nuevos", row["interpretacion"])
        self.assertEqual(json.loads(json.dumps(lab, allow_nan=False)), lab)

    def test_san_isidro_muestra_descenso_real(self):
        lab = explorar_area(self.profiles[2]["entrada"], self.model)
        self.assertEqual(lab["puntos"][1]["resultado"]["precio_estimado_soles"], 7386.28)
        self.assertEqual(lab["puntos"][2]["resultado"]["precio_estimado_soles"], 7077.25)
        self.assertLess(lab["puntos"][2]["resultado"]["precio_estimado_soles"], lab["puntos"][1]["resultado"]["precio_estimado_soles"])
        self.assertEqual(lab["resumen"]["diferencia_base_a_mayor_soles"], -309.03)
        self.assertEqual(lab["resumen"]["variacion_base_a_mayor_porcentaje"], -4.18)
        self.assertTrue(lab["resumen"]["hay_descenso_al_aumentar_area"])
        verificar_modelo_congelado()

    def test_apptest_area_de_ultima_estimacion_y_resultado_obsoleto(self):
        app = AppTest.from_file(str(ROOT / "code/app.py"), default_timeout=30).run()
        name = self.profiles[0]["nombre"]
        app.number_input(key=name + "area_total").set_value(60)
        next(b for b in app.button if b.label == "Estimar alquiler").click().run()
        self.assertFalse(app.exception, str(app.exception))
        app.radio(key="fuente_area_" + name).set_value("Última estimación guardada").run()
        next(b for b in app.button if b.label == "Explorar tres áreas").click().run()
        self.assertFalse(app.exception, str(app.exception))
        lab_key = "laboratorio_area_" + name + "_estimacion"
        self.assertEqual(app.session_state[lab_key]["entrada_base"]["area_total"], 60)
        self.assertEqual(app.session_state[lab_key]["puntos"][1]["resultado"],
                         predecir(app.session_state[lab_key]["entrada_base"], self.model))
        self.assertTrue(any("Al pasar de 60 a 72 m²" in e.value for e in app.markdown))
        app.number_input(key=name + "area_total").set_value(70).run()
        self.assertEqual(app.session_state[lab_key]["entrada_base"]["area_total"], 60)
        next(b for b in app.button if b.label == "Estimar alquiler").click().run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertNotIn(lab_key, app.session_state)
        next(b for b in app.button if b.label == "Explorar tres áreas").click().run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertEqual(app.session_state[lab_key]["entrada_base"]["area_total"], 70)
        self.assertEqual([point["entrada"]["area_total"] for point in app.session_state[lab_key]["puntos"]], [56, 70, 84])

    def test_apptest_grafico_tabla_descarga_persistencia_y_caso(self):
        app = AppTest.from_file(str(ROOT / "code/app.py"), default_timeout=30).run()
        self.assertFalse(app.exception)
        for profile in self.profiles:
            name = profile["nombre"]
            app.selectbox[0].select(name).run()
            next(b for b in app.button if b.label == "Explorar tres áreas").click().run()
            self.assertFalse(app.exception, str(app.exception))
            lab = app.session_state["laboratorio_area_" + name]
            self.assertEqual(lab, explorar_area(profile["entrada"], self.model))
            self.assertTrue(app.get("arrow_vega_lite_chart"))
            tables = [e.value for e in app.dataframe if list(e.value.columns) == list(tabla_area(lab)[0])]
            self.assertEqual(len(tables), 1)
            self.assertEqual(tables[0].to_dict("records"), tabla_area(lab))
            downloads = [e.proto.label for e in app.get("download_button")]
            self.assertIn("Descargar laboratorio CSV", downloads)
            self.assertIn("Descargar laboratorio JSON", downloads)
            app.run()
            self.assertEqual(app.session_state["laboratorio_area_" + name], lab)
        first = self.profiles[0]["nombre"]
        app.selectbox[0].select(first).run()
        self.assertEqual(app.session_state["laboratorio_area_" + first]["entrada_base"], self.profiles[0]["entrada"])
        next(b for b in app.button if b.label == "Estimar alquiler").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any(e.label == "Precio mensual estimado" for e in app.metric))
        self.assertTrue(app.get("arrow_vega_lite_chart"))

    def test_descarga_url_bytes_csv_json_sin_rerun(self):
        # Conserva el almacenamiento REAL usado por AppTest. No sustituye sus bytes ni su URL.
        registered = {}
        original_load = MemoryMediaFileStorage.load_and_get_id
        def capture(storage, path_or_data, mimetype, kind, filename=None):
            file_id = original_load(storage, path_or_data, mimetype, kind, filename)
            registered[file_id] = storage
            return file_id
        with patch.object(MemoryMediaFileStorage, "load_and_get_id", new=capture):
            app = AppTest.from_file(str(ROOT / "code/app.py"), default_timeout=30).run()
            for profile in self.profiles:
                name = profile["nombre"]
                app.selectbox[0].select(name).run()
                next(b for b in app.button if b.label == "Explorar tres áreas").click().run()
                self.assertFalse(app.exception)
                lab = app.session_state["laboratorio_area_" + name]
                before = {}
                for extension, mime in (("CSV", "text/csv"), ("JSON", "application/json")):
                    button = next(e.proto for e in app.get("download_button") if e.proto.label == "Descargar laboratorio " + extension)
                    self.assertTrue(button.ignore_rerun)
                    self.assertTrue(button.url, "La descarga debe tener una URL de medios")
                    filename = urlsplit(button.url).path.rsplit("/", 1)[-1]
                    file_id = filename.rsplit(".", 1)[0]
                    self.assertIn(file_id, registered)
                    media = registered[file_id].get_file(filename)
                    self.assertEqual(media.filename, "deparent_areas." + extension.lower())
                    self.assertEqual(media.mimetype, mime)
                    self.assertIsInstance(media.content, bytes)
                    if extension == "CSV":
                        self.assertEqual(media.content, csv_area(lab).encode("utf-8"))
                        self.assertTrue(media.content.startswith(b"\xef\xbb\xbf"))
                        rows = list(csv.DictReader(io.StringIO(media.content.decode("utf-8-sig"))))
                        self.assertEqual(len(rows), 3)
                        self.assertEqual([float(r["precio_estimado_soles"]) for r in rows], [p["resultado"]["precio_estimado_soles"] for p in lab["puntos"]])
                    else:
                        self.assertEqual(json.loads(media.content.decode("utf-8")), lab)
                    before[extension] = (button.url, media.content)
                app.run()
                self.assertFalse(app.exception)
                for extension in ("CSV", "JSON"):
                    button = next(e.proto for e in app.get("download_button") if e.proto.label == "Descargar laboratorio " + extension)
                    self.assertEqual(button.url, before[extension][0])
                    filename = urlsplit(button.url).path.rsplit("/", 1)[-1]
                    media = registered[filename.rsplit(".", 1)[0]].get_file(filename)
                    self.assertEqual(media.content, before[extension][1])

    def test_respaldo_para_copiar_coincide_con_payload(self):
        registered = {}
        original_load = MemoryMediaFileStorage.load_and_get_id
        def capture(storage, path_or_data, mimetype, kind, filename=None):
            file_id = original_load(storage, path_or_data, mimetype, kind, filename)
            registered[file_id] = storage
            return file_id
        with patch.object(MemoryMediaFileStorage, "load_and_get_id", new=capture):
            app = AppTest.from_file(str(ROOT / "code/app.py"), default_timeout=30).run()
            for profile in self.profiles:
                app.selectbox[0].select(profile["nombre"]).run()
                next(b for b in app.button if b.label == "Explorar tres áreas").click().run()
                self.assertFalse(app.exception)
                self.assertTrue(any(e.label == "Ver datos para copiar" for e in app.expander))
                self.assertTrue(any("Si el navegador no inicia la descarga" in e.value for e in app.caption))
                blocks = {e.proto.language: e.proto.code_text for e in app.get("code")}
                self.assertEqual(set(blocks), {"csv", "json"})
                for language in ("csv", "json"):
                    button = next(e.proto for e in app.get("download_button") if e.proto.label == "Descargar laboratorio " + language.upper())
                    filename = urlsplit(button.url).path.rsplit("/", 1)[-1]
                    payload = registered[filename.rsplit(".", 1)[0]].get_file(filename).content.decode("utf-8")
                    # st.code elimina un LF final al serializar; no cambia los campos del archivo.
                    self.assertEqual(blocks[language], payload.removesuffix("\n"))
                    if language == "csv":
                        visible = list(csv.DictReader(io.StringIO(blocks[language].lstrip("\ufeff"))))
                        stored = list(csv.DictReader(io.StringIO(payload.lstrip("\ufeff"))))
                        self.assertEqual(visible, stored)
                        self.assertEqual(len(visible), 3)
                    else:
                        self.assertEqual(json.loads(blocks[language]), json.loads(payload))


if __name__ == "__main__":
    unittest.main(verbosity=2)
