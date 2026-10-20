# Modelos y artefactos — Week 10

> **Week 10 implementa únicamente los componentes descriptivos RF1 y RF2. El modelo predictivo de precio no forma parte de este prototipo.**

## Artefactos presentes

| Archivo | Contenido | Uso en el producto | Formato |
|---|---|---|---|
| `clustering_pipeline.joblib` | `Pipeline` de scikit-learn: `ClusteringPreprocessor` (imputación con parámetros aprendidos) → `StandardScaler` → `KMeans(k=3, n_init=10, random_state=42)` | RF1: perfil competitivo y espacio de similitud de comparables | joblib |
| `clustering_metadata.json` | Dataset fuente con SHA-256, fecha de entrenamiento, variables usadas y excluidas, imputación, escalado, evaluación k=2..6 (silhouette, tamaños y estabilidad), k seleccionado, perfiles por cluster y versiones | Trazabilidad; perfiles mostrados en la interfaz | JSON |
| `cluster_names.json` | Nombre descriptivo de cada `cluster_id`, con la evidencia estadística que lo respalda. Incluye `k` y `cluster_sizes`: si el modelo se reentrena y cambian, la carga falla hasta revisar los nombres | Etiqueta del perfil en la interfaz | JSON |

RF2 (accesibilidad ATU) no tiene artefacto serializado: el índice `cKDTree` se construye al iniciar la aplicación a partir de `deliveries/week07/data/paraderos_procesado.csv`.

## Generación

```bash
python deliveries/week10/code/scripts/train_clustering.py --k 3
```

- Dataset: `deliveries/week07/data/departamentos_procesados.csv` (3,128 anuncios). Al cargar el modelo se verifica su SHA-256 frente al registrado en `clustering_metadata.json`.
- Variables (18): `area_total`, `dormitorios`, `banos`, `antiguedad`, `mantenimiento` y 13 amenidades. No se usa ninguna variable de precio.
- Detalle metodológico y justificación de k=3: `../DESCRIPTIVE_COMPONENTS.md`.

## Versiones necesarias para cargarlos

Serializados con Python 3.13.2, numpy 2.2.6, pandas 2.3.3, scipy 1.15.3, scikit-learn 1.7.2 y joblib 1.6.0 (fijadas en `code/requirements.txt`). Cargarlos con otra versión de scikit-learn no está garantizado.

## Cómo cargarlos

No se cargan a mano: `src/clustering.py` (`ClusteringModel` / `get_model()`) carga los tres archivos, valida su coherencia y verifica el dataset. El pipeline contiene la clase `src.clustering.ClusteringPreprocessor`, por lo que `deliveries/week10/code` debe estar en `sys.path`.

```python
from src.clustering import predict_cluster
predict_cluster({"distrito": "Lince", "area_total": 70, "dormitorios": 2, "banos": 2, "amenidades": []})
```

## Referencia histórica (no implementada en Week 10)

En Week 7 se entrenó en memoria un HistGradientBoosting de precio dentro de `deliveries/week07/code/EDA_week07.ipynb` (split 80/20, `random_state=42`): R² 0.8332, MAE S/ 491.74, RMSE S/ 830.11, MAPE 15.77%. **Ese modelo no está serializado ni se usa en este prototipo**; queda para iteraciones posteriores.
