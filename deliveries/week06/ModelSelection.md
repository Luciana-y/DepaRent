# ModelSelection — Semana 06

**Proyecto:** DepaRent — Plataforma inteligente para propietarios de departamentos en alquiler
**Curso:** DS3022 — Desarrollo de Producto de Datos

Este documento justifica la selección del método analítico o de modelado para cada uno de los 6 componentes funcionales de DepaRent, con base en el análisis exploratorio documentado en `DataAnalysis.md` y en el dataset depurado `df_clean` (3,128 departamentos).

---

## Resumen ejecutivo

| # | Componente | Algoritmo seleccionado | Evidencia empírica |
|:-:|---|---|---|
| 1 | Perfil competitivo | **K-Means (k=2) sobre PCA** | Silhouette 0.274 — mejor entre 5 configuraciones evaluadas |
| 2 | Accesibilidad urbana | **Feature engineering (cKDTree)** | Distancia mediana 174.8 m y 71.6% de cobertura a <300 m, integradas como variables |
| 3 | Predicción de precio | **HistGradientBoosting Regressor** | MAPE = 15.93% (R² = 0.8236) vs. baseline MAPE = 36.59% |
| 4 | Forecasting distrital | **SARIMA (d=1, s=4)** | 69.2% de las series del BCRP no son estacionarias (ADF) |
| 5 | Recomendación de precio | **Motor de reglas sobre #1 + #3 + #4** | Combina predicción puntual, rango de comparables y tendencia distrital |
| 6 | Simulador de mejoras | **Inferencia contrafactual sobre #3** | Reutiliza el mismo pipeline de regresión, sin modelo adicional |

---

## Modelo #1 — Perfil competitivo (Clustering)

**Pregunta que responde:** ¿Contra qué propiedades debería compararse realmente un departamento?

### Proceso de selección

Se evaluaron diferentes configuraciones de clustering buscando obtener segmentos interpretables y suficientemente diferenciados. El análisis inicial mostró que la configuración de **9 features + PCA** mejoraba el silhouette respecto al modelo original, pasando de **0.237 a 0.274**.

Posteriormente, se amplió el análisis incorporando variables adicionales de características y amenidades de los inmuebles. Esta evaluación permitió identificar **4 segmentos con perfiles diferenciados**, que resultan más útiles para la caracterización del mercado inmobiliario.

| Configuración                                                   |                                                         Resultado | Decisión           |
| --------------------------------------------------------------- | ----------------------------------------------------------------: | ------------------ |
| 9 features, sin PCA                                             |                                                Silhouette = 0.237 | Punto de partida   |
| 9 features + PCA                                                |                                                Silhouette = 0.274 | Base metodológica  |
| Configuraciones con distrito, GMM y mayor cantidad de variables | Menor separación / problemas de dimensionalidad o datos faltantes | Descartadas        |
| **Configuración final de segmentación**                         |                         **4 clusters con perfiles diferenciados** | **Seleccionada** |

### Modelo final: K-Means (k=4)

El modelo final utiliza **K-Means con 4 clusters**, permitiendo identificar perfiles más específicos dentro del mercado inmobiliario.

El análisis de los clusters muestra que la segmentación está determinada principalmente por el **tamaño de la propiedad, antigüedad, precio por m² y presencia de amenidades**.

| Cluster | % propiedades | Perfil identificado                                                                                                                                     |
| ------- | ------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **0**   |    **49.01%** | **Estándar tradicional:** propiedades de tamaño medio, aproximadamente 2 dormitorios y baja presencia de amenidades.                                    |
| **1**   |    **14.54%** | **Propiedades amplias:** destaca por un área promedio de 188.82 m², mayor cantidad de dormitorios y baños y mayor mantenimiento.                        |
| **2**   |    **27.99%** | **Compacto con alta oferta de amenidades:** propiedades pequeñas y relativamente nuevas, con alta presencia de piscina, gimnasio, coworking y parrilla. |
| **3**   |     **8.46%** | **Residencial familiar:** propiedades relativamente nuevas con alta presencia de amenidades, destacando que el 100% presenta juegos infantiles.         |

### Interpretación

Los resultados muestran que las propiedades no se diferencian únicamente por su precio, sino por **perfiles residenciales distintos**. El paso de 2 a 4 clusters permite capturar esta heterogeneidad con mayor detalle y generar comparables más específicos para el sistema de recomendación.

Por ejemplo, dos departamentos con precios similares pueden pertenecer a segmentos diferentes si uno destaca por su gran superficie y número de habitaciones, mientras que otro presenta menor superficie pero una mayor cantidad de amenidades.

Por ello, el **cluster funciona como una primera etapa para determinar el grupo de propiedades comparables**, mientras que posteriormente variables como **distrito, ubicación y características específicas** pueden utilizarse para realizar una comparación más precisa dentro del segmento.

### Pendiente para Delivery 1

Evaluar si la segmentación de 4 clusters mejora la calidad de las recomendaciones frente a una comparación únicamente basada en características individuales y determinar cómo combinar el **cluster + ubicación + características del inmueble** en la búsqueda final de comparables.

---

## Modelo #2 — Perfil de accesibilidad

**Pregunta que responde:** ¿Qué tan bien conectado está un departamento mediante transporte público?

**No requiere un modelo de Machine Learning dedicado.** Se construyeron variables espaciales mediante indexación `cKDTree` sobre los 3,233 paraderos oficiales de la ATU:

- `dist_paradero_min_m` — distancia al paradero más cercano (mediana: 174.8 m)
- `paraderos_300m`, `paraderos_500m`, `paraderos_1000m` — conteo de paraderos en radios crecientes (promedio en 500m: 9.3)
- `dist_troncal_brt_m`, `dist_corredor_m` — distancia a infraestructura troncal/corredor

Estas variables ya demuestran aporte real como features del Modelo #3 (`dist_paradero_min_m` y `dist_troncal_brt_m` aparecen en el top 4 de importancia).

---

## Modelo #3 — Predicción del precio esperado de alquiler (núcleo ML)

**Pregunta que responde:** ¿Cuánto debería pedir un propietario por su departamento?

**Metodología:** split 80/20 (train/test) **antes** de cualquier imputación, con `SimpleImputer` dentro de un `ColumnTransformer`/`Pipeline` de scikit-learn, calculado únicamente sobre el set de entrenamiento — evitando *data leakage*.

**Benchmark de 6 algoritmos (conjunto de prueba, 20% holdout):**

| Modelo | R² | MAE (S/.) | RMSE (S/.) | MAPE (%) |
|---|:---:|:---:|:---:|:---:|
| **HistGradientBoosting** | **0.8236** | **501.48** | **853.70** | **15.93%** |
| Random Forest | 0.7889 | 500.87 | 933.92 | 16.05% |
| Gradient Boosting | 0.7882 | 518.86 | 935.53 | 16.37% |
| KNN | 0.7903 | 535.40 | 930.80 | 17.27% |
| Ridge | 0.7787 | 622.36 | 956.28 | 21.56% |
| Baseline Dummy (mediana) | -0.0689 | 1,213.26 | 2,101.61 | 36.59% |

**Modelo elegido: HistGradientBoosting.** Menor MAPE (15.93%) y mayor R² (0.8236) — una reducción del **56.5%** en el error relativo frente al baseline.

**Feature importance (Random Forest, top 5):** `area_total`, `mantenimiento`, `dist_paradero_min_m`, `dist_troncal_brt_m`, `banos`.

**Pendiente para Delivery 1:** tuning de hiperparámetros (actualmente valores por defecto razonables, no optimizados).

---

## Modelo #4 — Pronóstico del alquiler por distrito

**Pregunta que responde:** ¿El mercado de un distrito está subiendo, bajando o se mantiene estable?

**Test de estacionariedad (ADF)** sobre las 13 series distritales del BCRP: 4 de 13 (30.8%) estacionarias, 9 de 13 (69.2%) no estacionarias.

**Modelo elegido: SARIMA (d=1, componente estacional s=4).** La mayoría de series no son estacionarias, descartando ARIMA simple sin diferenciar; la componente estacional captura la oscilación trimestral visible en la serie histórica del BCRP.

**Baseline de comparación:** modelo naive estacional (mismo trimestre del año anterior).

**Pendiente para Delivery 1:** implementar `SARIMAX` real para los distritos de mayor volumen (Miraflores, San Isidro, Surco).

---

## Modelo #5 — Precio recomendado de publicación

**No es un modelo de ML nuevo.** Combina los outputs de los tres modelos anteriores: rango predictivo del Modelo #3, estadísticas del cluster de comparables del Modelo #1, y tendencia distrital del Modelo #4, para generar tres escenarios (competitivo, equilibrado, premium).

---

## Modelo #6 — Simulador de mejoras del inmueble

**Reutiliza el Modelo #3 en modo contrafactual.** Predicción con estado actual → modificación virtual de un atributo → nueva predicción manteniendo el resto constante. La diferencia se reporta como impacto estimado, con advertencia explícita de asociación (no causalidad).

---

## Limitaciones generales

Ver sección 9 de `DataAnalysis.md`. En síntesis: dependencia de extracción por texto para amenidades y piso, ambigüedad del 89.25% de nulos en `estacionamientos`, 16.3% de departamentos sin serie BCRP propia, y descarte del 18.16% del dataset original por filtros de calidad geográfica, de precio y de doble modalidad venta/alquiler.

---

## Pendientes técnicos antes de Delivery 1

1. **Modelo #1:** implementar la segunda etapa de comparables (k-NN dentro del cluster + mismo distrito), ya diseñada conceptualmente pero pendiente de integrar al pipeline final.
2. **Modelo #3:** tuning de hiperparámetros.
3. **Modelo #4:** implementación real de SARIMAX con métricas de validación temporal.
