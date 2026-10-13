# Modelos serializados — instrucciones

Coloca aquí los artefactos analíticos serializados (modelos entrenados, scalers, pipelines) usados por el prototipo.

Formato recomendado:
- joblib: `models/precio_model.joblib`
- pickle: `models/knn_comparables.pkl`
- ONNX: `models/precio_model.onnx` (si aplica)

Incluye además un archivo `models/metadata.md` que explique:
- formato del archivo
- versión de librerías necesarias para cargarlo (scikit-learn, xgboost, etc.)
- cómo cargar el modelo (snippet de código)
