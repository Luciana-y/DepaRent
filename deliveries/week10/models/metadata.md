# Modelos serializados

| Archivo | Modelo | Uso en el producto | Formato |
|---|---|---|---|
| `precio_model.joblib` | HistGradientBoosting (Pipeline con imputación) | Precio esperado de alquiler | joblib |
| `kmeans_cluster.joblib` | K-Means (k=4) + scaler | Perfil competitivo | joblib |

> Estado: pendiente de serializar. Completar esta tabla al agregar los archivos.

## Versiones necesarias para cargarlos
- Python: 3.10+
- scikit-learn: _(anotar la versión exacta usada al entrenar)_
- joblib / numpy / pandas: _(anotar)_

## Cómo cargarlos
```python
import joblib
model = joblib.load("models/precio_model.joblib")
pred = model.predict(X)  # X: DataFrame con las columnas de entrada documentadas abajo
```

## Entradas y salidas
- Entrada: _(listar columnas esperadas)_
- Salida: alquiler mensual esperado en soles (`precio_soles`)

## Métricas de referencia (split 80/20)
HistGradientBoosting: R² 0.8332 · MAE S/ 491.74 · RMSE S/ 830.11 · MAPE 15.77%
