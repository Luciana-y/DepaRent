"""Prototipo web DepaRent Week 10: RF1 (perfil competitivo + comparables) y RF2 (accesibilidad ATU).

Todos los resultados analíticos provienen de src.descriptive_service.analyze_descriptive.
No hay predicción de precio ni recomendaciones en este prototipo.

Ejecutar:  python deliveries/week10/code/app.py   (DEPARENT_DEBUG=1 activa el modo debug de Flask)
"""
import logging
import os

from flask import Flask, jsonify, render_template, request

from src import accessibility, comparables
from src.descriptive_service import analyze_descriptive
from src.input_validation import AMENITIES, LIMA_BBOX, RANGES, InputValidationError

AMENITY_LABELS = {
    "ascensor": "Ascensor", "balcon": "Balcón", "terraza": "Terraza", "piscina": "Piscina",
    "gimnasio": "Gimnasio", "deposito": "Depósito", "vista_al_mar": "Vista al mar",
    "parrilla": "Parrilla", "areas_verdes": "Áreas verdes", "seguridad_24_7": "Seguridad 24/7",
    "coworking": "Coworking", "juegos_infantiles": "Juegos infantiles", "pet_friendly": "Pet friendly",
}

logger = logging.getLogger("deparent")


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    # Carga única de modelo, dataset de referencia e índice ATU (falla al iniciar si falta un artefacto).
    comp_index = comparables.get_index()
    accessibility.get_index()
    districts = comp_index.model.known_districts

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            districts=districts,
            amenities=[(a, AMENITY_LABELS[a]) for a in AMENITIES],
            ranges=RANGES,
            bbox=LIMA_BBOX,
        )

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/analyze")
    def analyze():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "validation_error",
                            "details": ["El cuerpo de la solicitud debe ser un objeto JSON."]}), 400
        try:
            result = analyze_descriptive(data)
        except InputValidationError as e:
            return jsonify({"error": "validation_error", "details": e.errors}), 400
        except Exception:
            logger.exception("Error inesperado en /analyze")
            return jsonify({"error": "internal_error",
                            "details": ["Error interno al analizar el inmueble. Intente nuevamente."]}), 500
        return jsonify(result)

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_app().run(host="127.0.0.1", port=5000, debug=os.environ.get("DEPARENT_DEBUG") == "1")
