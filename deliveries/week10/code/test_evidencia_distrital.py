"""Comprueba que el dato local visible es agregado y corresponde a la prueba."""
import csv
import unittest
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory

from streamlit.testing.v1 import AppTest

from evidencia_distrital import evidencia_distrital
from modelo import ROOT


class EvidenciaDistritalTest(unittest.TestCase):
    def test_aggregate_matches_held_out_rows(self):
        grouped = defaultdict(list)
        with (ROOT / "resultados/predicciones_prueba.csv").open(encoding="utf-8", newline="") as source:
            for row in csv.DictReader(source):
                grouped[row["distrito"]].append(abs(float(row["real_soles"]) - float(row["prediccion_soles"])))
        self.assertEqual(sum(map(len, grouped.values())), 629)
        for district, errors in grouped.items():
            with self.subTest(district=district):
                visible = evidencia_distrital(district)
                self.assertEqual(visible["anuncios_prueba"], len(errors))
                self.assertAlmostEqual(visible["error_absoluto_medio_soles"], sum(errors) / len(errors), places=8)
                self.assertEqual(visible["muestra_pequena"], len(errors) < 20)

    def test_missing_district_and_bad_numbers(self):
        self.assertIsNone(evidencia_distrital("distrito inexistente"))
        with TemporaryDirectory() as folder:
            source = Path(folder) / "resumen.csv"
            source.write_text("distrito,n,MAE_soles,MAPE_porcentaje\nlince,0,123,4\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                evidencia_distrital("lince", source)
            source.write_text("distrito,n,MAE_soles,MAPE_porcentaje\nlince,20,nan,4\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                evidencia_distrital("lince", source)

    def test_interface_uses_saved_estimate_and_warns_for_small_sample(self):
        app = AppTest.from_file(str(ROOT / "code/app.py"), default_timeout=30).run()
        self.assertFalse(app.exception, str(app.exception))
        first = app.selectbox[0].value
        next(button for button in app.button if button.label == "Estimar alquiler").click().run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertTrue(any("25 anuncios reservados de Lince" in item.value for item in app.markdown))
        app.selectbox(key=first + "district").select("ate")
        next(button for button in app.button if button.label == "Estimar alquiler").click().run()
        self.assertFalse(app.exception, str(app.exception))
        self.assertTrue(any("3 anuncios reservados de Ate" in item.value for item in app.markdown))
        self.assertTrue(any("menos de 20 anuncios de prueba" in item.value for item in app.warning))


if __name__ == "__main__":
    unittest.main(verbosity=2)
