"""Consultas de sensibilidad al modelo v1 congelado; sin entrenamiento."""
import copy
import csv
import hashlib
import io
import json
from modelo import ROOT, FEATURES, predecir, validar_entrada

HASHES_V1 = {
    "models/modelo_docente.joblib": "6dabe6d10d3751654dde1dbc8d3eccfc66eabd3462b768b747aafe02e8724760",
    "code/modelo.py": "2e543c5bd382bc2bec1a623c21bda751790c1c74418675691166c8c844060d1a",
    "code/entrenar.py": "dc103b95d3c0fcdff9beee43d49e8c0a11fa41319f5a66b70407f5349a76803a",
    "resultados/metricas.json": "fd25590bdeda1c4a0d9dd1c06e89e6e247c92b5b17b8f29b8ad381e1b9b7d0e4",
}
ADVERTENCIA = "Sensibilidad predictiva con entradas hipotéticas. No es un efecto causal, precio observado, rentabilidad ni recomendación de remodelación."
CAMBIABLES = {"area_total", "mantenimiento", "balcon", "gimnasio"}

def verificar_modelo_congelado():
    for relative, expected in HASHES_V1.items():
        data = (ROOT / relative).read_bytes()
        if not relative.endswith(".joblib"):
            data = data.replace(b"\r\n", b"\n")  # git puede convertir finales de línea al clonar
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise ValueError(f"Cambió un artefacto de v1: {relative}. Regenerar y documentar una nueva versión antes de simular.")

def comparar(base, cambios, artifact):
    if not isinstance(cambios, dict) or set(cambios) - CAMBIABLES:
        raise ValueError("Solo se comparan área, mantenimiento, balcón y gimnasio.")
    alternate = copy.deepcopy(base)
    alternate.update(cambios)
    validar_entrada(base, artifact)
    validar_entrada(alternate, artifact)
    before, after = predecir(base, artifact), predecir(alternate, artifact)
    difference = round(after["precio_estimado_soles"] - before["precio_estimado_soles"], 2)
    percentage = round(100 * difference / before["precio_estimado_soles"], 2) if before["precio_estimado_soles"] else None
    return {"tipo": "CONSULTA_MODELO_ENTRENADO_ENTRADAS_HIPOTETICAS", "base_entrada": copy.deepcopy(base),
            "alternativa_entrada": alternate, "base_resultado": before, "alternativa_resultado": after,
            "cambios": {key: {"base": base.get(key), "alternativa": alternate[key]} for key in sorted(cambios) if base.get(key) != alternate[key]},
            "diferencia_soles": difference, "diferencia_porcentaje": percentage,
            "advertencia": ADVERTENCIA,
            "interpretacion_intervalos": "Rangos de precio separados con radio global calibrado; no constituyen un intervalo estadístico para la diferencia.",
            "soporte": "El conteo distrital no prueba que la combinación concreta de atributos tenga soporte suficiente."}

def csv_comparacion(comparison):
    stream = io.StringIO(newline="")
    columns = ["escenario"] + FEATURES + ["precio_estimado_soles", "limite_inferior_soles", "limite_superior_soles", "baseline_distrital_soles", "anuncios_entrenamiento_distrito", "naturaleza", "advertencias"]
    writer = csv.DictWriter(stream, fieldnames=columns)
    writer.writeheader()
    for name, source, result in [("base", "base_entrada", "base_resultado"), ("alternativa", "alternativa_entrada", "alternativa_resultado")]:
        row = {"escenario": name, **comparison[source], **comparison[result], "naturaleza": "HIPOTETICO_PREDICCION_MODELO"}
        row["advertencias"] = " | ".join(row["advertencias"])
        writer.writerow(row)
    return stream.getvalue()

def json_comparacion(comparison):
    return json.dumps(comparison, ensure_ascii=False, indent=2, allow_nan=False)
