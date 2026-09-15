# ModelSelection — Semana 06

**Proyecto:** DepaRent — Plataforma inteligente para propietarios de departamentos en alquiler
**Curso:** DS3022 — Desarrollo de Producto de Datos

Este documento justifica la selección del método analítico o de modelado para cada uno de los 6 componentes funcionales de DepaRent, con base en el análisis exploratorio documentado en `DataAnalysis.md` y en el dataset depurado `df_clean` (3,128 departamentos).

---

## Resumen ejecutivo

| # | Componente | Algoritmo seleccionado | Evidencia empírica |
|:-:|---|---|---|
| 1 | Perfil competitivo | **K-Means (k=2)** | Silhouette 0.237 vs. DBSCAN descartado por 40.6% de ruido |
| 2 | Accesibilidad urbana | **Feature engineering (cKDTree)** | Distancia mediana 174.8 m y 71.6% de cobertura a <300 m, integradas como variables |
| 3 | Predicción de precio | **HistGradientBoosting Regressor** | MAPE = 15.93% (R² = 0.8236) vs. baseline MAPE = 36.59% |
| 4 | Forecasting distrital | **SARIMA (d=1, s=4)** | 69.2% de las series del BCRP no son estacionarias (ADF) |
| 5 | Recomendación de precio | **Motor de reglas sobre #1 + #3 + #4** | Combina predicción puntual, rango de comparables y tendencia distrital |
| 6 | Simulador de mejoras | **Inferencia contrafactual sobre #3** | Reutiliza el mismo pipeline de regresión, sin modelo adicional |

---

## Modelo #1 — Perfil competitivo (Clustering)

**Pregunta que responde:** ¿Contra qué propiedades debería compararse realmente un departamento?

**Features utilizadas:** `area_total`, `dormitorios`, `banos`, `precio_m2_real`, `piscina`, `gimnasio`, `cochera`, `seguridad_24_7`, `coworking` (estandarizadas). Se usó `df_clean_sin_geo` (3,610 filas) en lugar de `df_clean`, para no perder observaciones sin coordenadas válidas en un componente que no depende de geolocalización.

**Comparación de algoritmos:**

| k (K-Means) | Silhouette |
|:---:|:---:|
| 2 | **0.237** |
| 3 | 0.209 |
| 4 | 0.191 |
| 5 | 0.209 |
| 6 | 0.201 |

**DBSCAN** (eps calculado por vecino más cercano, min_samples=5): 71 clusters, silhouette=0.462, pero con **40.6% de los puntos clasificados como ruido** — se descarta porque casi la mitad del dataset quedaría fuera de cualquier segmento, lo cual no es útil para un producto que debe ofrecer comparables a la mayoría de propietarios.

**Modelo elegido: K-Means, k=2.** Silhouette más alto entre los valores evaluados (0.237), sin descartar observaciones.

**Perfiles resultantes:**

| Cluster | Área media | Dormitorios | Baños | Precio/m² | Piscina | Gimnasio | Coworking |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0 — Tradicional/Amplio | 101.1 m² | 2.3 | 1.9 | S/ 34.19 | 3% | 7% | 15% |
| 1 — Moderno/Alta amenidad | 66.6 m² | 1.8 | 1.6 | S/ 47.95 | 72% | 86% | 65% |

**Pendiente para Delivery 1:** evaluar si un k mayor con una selección de features distinta (o un preprocesamiento robusto a outliers) revela subsegmentos adicionales dentro de cada cluster.

---

## Modelo #2 — Perfil de accesibilidad

**Pregunta que responde:** ¿Qué tan bien conectado está un departamento mediante transporte público?

**No requiere un modelo de Machine Learning dedicado.** Se construyeron variables espaciales mediante indexación `cKDTree` sobre los 3,233 paraderos oficiales de la ATU:

- `dist_paradero_min_m` — distancia al paradero más cercano (mediana: 174.8 m)
- `paraderos_300m`, `paraderos_500m`, `paraderos_1000m` — conteo de paraderos en radios crecientes (promedio en 500m: 9.3)
- `dist_troncal_brt_m`, `dist_corredor_m` — distancia a infraestructura troncal/corredor

**Justificación de no usar clustering aquí:** el proposal original contemplaba K-Means sobre variables de accesibilidad solo si había "suficiente variedad de indicadores". Con 6 variables numéricas ya interpretables por sí mismas, un perfil directo (percentiles de distancia) es más simple y transparente que un cluster adicional, y estas variables ya demuestran aporte real como features del Modelo #3 (`dist_paradero_min_m` y `dist_troncal_brt_m` aparecen en el top 4 de importancia — ver Modelo #3).

---

## Modelo #3 — Predicción del precio esperado de alquiler (núcleo ML)

**Pregunta que responde:** ¿Cuánto debería pedir un propietario por su departamento?

**Metodología:** split 80/20 (train/test) **antes** de cualquier imputación, con `SimpleImputer` dentro de un `ColumnTransformer`/`Pipeline` de scikit-learn, calculado únicamente sobre el set de entrenamiento. Esto evita *data leakage* — un riesgo detectado y corregido explícitamente durante el desarrollo del pipeline, dado que una primera versión del notebook del equipo imputaba antes del split.

**Features:** variables físicas (`area_total`, `dormitorios`, `banos`, `estacionamientos`, `antiguedad`, `mantenimiento`), variables de accesibilidad (Modelo #2), variables de contexto BCRP (Modelo #4 — snapshot más reciente), las 14 amenidades extraídas por texto, los flags de missingness (`_imputado`), y `distrito_norm` (con categorías raras agrupadas en "Otros").

**Benchmark de 6 algoritmos (conjunto de prueba, 20% holdout):**

| Modelo | R² | MAE (S/.) | RMSE (S/.) | MAPE (%) |
|---|:---:|:---:|:---:|:---:|
| **HistGradientBoosting** | **0.8236** | **501.48** | **853.70** | **15.93%** |
| Random Forest | 0.7889 | 500.87 | 933.92 | 16.05% |
| Gradient Boosting | 0.7882 | 518.86 | 935.53 | 16.37% |
| KNN | 0.7903 | 535.40 | 930.80 | 17.27% |
| Ridge | 0.7787 | 622.36 | 956.28 | 21.56% |
| Baseline Dummy (mediana) | -0.0689 | 1,213.26 | 2,101.61 | 36.59% |

**Modelo elegido: HistGradientBoosting.** Menor MAPE (15.93%) y mayor R² (0.8236) de todos los algoritmos evaluados — una reducción del **56.5%** en el error relativo frente al baseline de la mediana. Se prioriza MAPE sobre R² porque el error relativo es la métrica más interpretable para comunicar al propietario (ej. "el precio estimado tiene un margen de error típico de ~16%").

**Feature importance (Random Forest, top 5):** `area_total`, `mantenimiento`, `dist_paradero_min_m`, `dist_troncal_brt_m`, `banos`. Las variables de accesibilidad calculadas en el Modelo #2 confirman aporte real al modelo de precio.

**Pendiente para Delivery 1:** tuning de hiperparámetros (actualmente se usan valores por defecto razonables, no optimizados vía GridSearch/RandomizedSearch).

---

## Modelo #4 — Pronóstico del alquiler por distrito

**Pregunta que responde:** ¿El mercado de un distrito está subiendo, bajando o se mantiene estable?

**Test de estacionariedad (Dickey-Fuller Aumentado, ADF)** sobre las 13 series distritales del BCRP:

- Series estacionarias (p < 0.05): **4 de 13 (30.8%)**
- Series NO estacionarias: **9 de 13 (69.2%)**

**Modelo elegido: SARIMA (d=1, componente estacional s=4).** La mayoría de las series (69.2%) no son estacionarias, lo que descarta un ARIMA simple sin diferenciar. La componente estacional (s=4) se incluye porque las series muestran oscilación trimestral regular superpuesta a la tendencia de largo plazo, visible en el gráfico de la serie completa del BCRP (2013-2026).

**Baseline de comparación:** modelo naive estacional (repetir el valor del mismo trimestre del año anterior).

**Pendiente para Delivery 1:** implementar el SARIMA real (`statsmodels.tsa.statespace.SARIMAX`) para al menos los distritos de mayor volumen en el dataset (Miraflores, San Isidro, Surco), y comparar contra el baseline naive con métricas de error de pronóstico (MAE/RMSE sobre ventana de validación temporal).

---

## Modelo #5 — Precio recomendado de publicación

**No es un modelo de ML nuevo.** Combina los outputs de los tres modelos anteriores:

- Rango predictivo del Modelo #3 (HistGradientBoosting) como referencia central.
- Estadísticas del cluster de comparables (Modelo #1) para contextualizar el segmento del propietario.
- Tendencia distrital del Modelo #4 (SARIMA) para ajustar según la dirección reciente del mercado.

Se generan tres escenarios (competitivo, equilibrado, premium) como posicionamiento relativo dentro del rango estimado, no como una predicción exacta de tiempo de alquiler.

---

## Modelo #6 — Simulador de mejoras del inmueble

**Reutiliza el Modelo #3 en modo contrafactual.** Se calcula la predicción con el estado actual del inmueble, se modifica virtualmente un atributo (ej. condición de amoblado), y se vuelve a predecir manteniendo las demás variables constantes. La diferencia entre ambas predicciones se reporta como el impacto estimado de la mejora, con la advertencia explícita de que refleja asociación observada en el mercado, no causalidad.

---

## Limitaciones generales que afectan a los 6 modelos

Ver sección 9 de `DataAnalysis.md` para el detalle completo. En síntesis: dependencia de extracción por texto para amenidades y piso, ambigüedad del 89.25% de nulos en `estacionamientos`, 16.3% de departamentos sin serie BCRP propia, y descarte del 18.16% del dataset original por filtros de calidad geográfica, de precio y de doble modalidad venta/alquiler.
