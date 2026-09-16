# ModelSelection — Semana 06

**Proyecto:** DepaRent — Plataforma inteligente para propietarios de departamentos en alquiler
**Curso:** DS3022 — Desarrollo de Producto de Datos

Este documento justifica la selección del método analítico o de modelado para cada uno de los 6 componentes funcionales de DepaRent, con base en el análisis exploratorio documentado en `DataAnalysis.md` y en el dataset depurado `df_clean` (3,128 departamentos).

---

## Resumen ejecutivo

| # | Componente | Algoritmo seleccionado | Evidencia empírica |
|:-:|---|---|---|
| 1 | Perfil competitivo | **K-Means (k=4) sobre 19 features (sin PCA)** | Silhouette = 0.1647 — priorizado por interpretabilidad de negocio sobre la alternativa de mejor silhouette (9 features + PCA, k=2, silhouette = 0.274) |
| 2 | Accesibilidad urbana | **Feature engineering (cKDTree)** | Distancia mediana 174.8 m y 71.6% de cobertura a <300 m, integradas como variables |
| 3 | Predicción de precio | **HistGradientBoosting Regressor** | MAPE = 15.93% (R² = 0.8236) vs. baseline MAPE = 36.59% |
| 4 | Forecasting distrital | **SARIMA (d=1, s=4)** | 69.2% de las series del BCRP no son estacionarias (ADF) |
| 5 | Recomendación de precio | **Motor de reglas sobre #1 + #3 + #4** | Combina predicción puntual, rango de comparables y tendencia distrital |
| 6 | Simulador de mejoras | **Inferencia contrafactual sobre #3** | Reutiliza el mismo pipeline de regresión, sin modelo adicional |

---

## Modelo #1 — Perfil competitivo (Clustering)

**Pregunta que responde:** ¿Contra qué propiedades debería compararse realmente un departamento?

### Proceso de selección

Se evaluaron diferentes configuraciones de clustering buscando obtener segmentos interpretables y suficientemente diferenciados.

| Configuración | Resultado | Decisión |
|---|---:|---|
| 9 features, sin PCA | Silhouette = 0.237 | Punto de partida |
| 9 features + PCA (6 componentes) | Silhouette = 0.274 | Mejor resultado estadístico de todas las configuraciones probadas |
| Distrito vía one-hot (9 features + ~20 dummies) | Silhouette = 0.041–0.105 | Descartada — dimensionalidad dispersa degrada la distancia |
| Gaussian Mixture Model | Silhouette = 0.196 | Descartada — BIC monotónicamente decreciente indica degeneración del modelo (variables binarias violan el supuesto gaussiano) |
| 20 features (incluye `cochera`) | Silhouette = 0.150, con 47% de la muestra perdida por nulos | Descartada — pérdida masiva de datos |
| 19 features (sin `cochera`/`estacionamientos`) + PCA, k=4 | Silhouette = 0.178 (calculado sobre el espacio reducido por PCA) | Referencia intermedia |
| **19 features (sin `cochera`/`estacionamientos`), sin PCA, k=4** | **Silhouette = 0.1647 (verificado sobre el modelo final real)** | **Seleccionada** |

**Nota de transparencia metodológica:** el modelo final se ajusta sobre el espacio estandarizado de 19 features **sin** reducción por PCA (a diferencia del experimento intermedio de la fila anterior, que sí aplicaba PCA). El silhouette de 0.1647 fue calculado directamente sobre este fit final (`silhouette_score(X_scaled_19features, labels_kmeans_k4)`), no reutilizado de un experimento con distinta transformación de datos. Es, en términos puramente estadísticos, la configuración con menor silhouette entre las evaluadas — significativamente por debajo de la alternativa de 9 features + PCA (0.274). Se prioriza sobre esa alternativa por la razón que se explica a continuación.

### Modelo final: K-Means (k=4), 19 features estandarizadas, sin PCA

**Features utilizadas:** `area_total`, `dormitorios`, `banos` (imputado por moda según dormitorios), `precio_m2_real`, `antiguedad` (imputada por mediana de distrito), `mantenimiento` (imputado por mediana de distrito), y las 13 amenidades binarias completas (`piscina`, `gimnasio`, `seguridad_24_7`, `coworking`, `balcon`, `terraza`, `vista_al_mar`, `parrilla`, `areas_verdes`, `juegos_infantiles`, `pet_friendly`, `deposito`, `ascensor`). Se excluyen `cochera` y `estacionamientos` por la ambigüedad de sus nulos (ver `data_quality.md`: solo 10.75% de los nulos son confirmables por texto).

**Justificación de la elección sobre la alternativa de mejor silhouette:** se prioriza esta configuración porque preserva la interpretabilidad directa de cada amenidad individual (sin pasar por componentes de PCA no interpretables) y porque el propósito del Modelo #1 es generar un perfil descriptivo accionable para el propietario, donde la riqueza de atributos visibles importa tanto como la pureza estadística del agrupamiento. Esta es una decisión consciente de priorizar valor de negocio sobre optimización pura de la métrica, y se documenta explícitamente como tal — el silhouette de 0.1647 indica una estructura de cluster débil según la escala convencional (Kaufman & Rousseeuw: <0.25 = sin estructura sustancial), por lo que los 4 segmentos deben interpretarse como una heurística útil de agrupación, no como grupos naturalmente separados con alta confianza estadística.

**Perfiles resultantes:**

| Cluster | % propiedades | Perfil identificado |
|---|---:|---|
| **0** | **49.01%** | **Estándar tradicional:** tamaño medio (80.95 m² promedio), ~2 dormitorios, baja presencia de amenidades (piscina 1.4%, gimnasio 3.0%). |
| **1** | **14.54%** | **Propiedades amplias:** área promedio 188.82 m², mayor número de dormitorios (3.06) y baños (2.91), mayor mantenimiento (S/ 669.90), mayor presencia de terraza (58.3%), ascensor (59.9%) y depósito (38.6%). |
| **2** | **27.99%** | **Compacto con alta oferta de amenidades:** propiedades pequeñas (61.22 m²) y relativamente nuevas (antigüedad media 3.72 años), con alta presencia de piscina (67.1%), gimnasio (81.7%), coworking (61.5%) y parrilla (84.5%). |
| **3** | **8.46%** | **Residencial familiar:** propiedades relativamente nuevas (antigüedad media 4.92 años) con alta presencia de amenidades; 100% presenta juegos infantiles (variable distintiva de este segmento). |

### Interpretación

Los resultados muestran que las propiedades no se diferencian únicamente por su precio, sino por **perfiles residenciales distintos**. El paso de 2 a 4 clusters permite capturar esta heterogeneidad con mayor detalle y generar comparables más específicos para el sistema de recomendación, a costa de una segmentación estadísticamente menos nítida (silhouette 0.1647 vs. 0.274 de la alternativa más simple).

Por ejemplo, dos departamentos con precios similares pueden pertenecer a segmentos diferentes si uno destaca por su gran superficie y número de habitaciones (Cluster 1), mientras que otro presenta menor superficie pero mayor cantidad de amenidades (Cluster 2).

El **cluster funciona como una primera etapa** para determinar el grupo de propiedades comparables, mientras que posteriormente variables como **distrito, ubicación y características específicas** pueden utilizarse para realizar una comparación más precisa dentro del segmento (ver Modelo #5).

### Pendiente para Delivery 1

1. Evaluar si la segmentación de 4 clusters mejora la calidad de las recomendaciones frente a una comparación únicamente basada en características individuales, dado el silhouette débil (0.1647).
2. Determinar cómo combinar **cluster + ubicación + características del inmueble** en la búsqueda final de comparables.
3. Considerar validar la estabilidad de los 4 clusters (ej. con bootstrap o distintas semillas aleatorias), dado que un silhouette bajo puede indicar sensibilidad a la inicialización.

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

**Limitación adicional del Modelo #1:** la imputación de `antiguedad`/`mantenimiento` por mediana de distrito puede fallar en distritos con muestra muy pequeña o sin ningún valor no-nulo disponible (observado como `RuntimeWarning: Mean of empty slice` durante la ejecución) — estas filas se excluyen del clustering final (23 de 3,571, ~0.6%).

---

## Pendientes técnicos antes de Delivery 1

1. **Modelo #1:** implementar la segunda etapa de comparables (k-NN dentro del cluster + mismo distrito), ya diseñada conceptualmente pero pendiente de integrar al pipeline final.
2. **Modelo #1:** validar estabilidad de los 4 clusters ante distintas semillas aleatorias, dado el silhouette bajo (0.1647).
3. **Modelo #3:** tuning de hiperparámetros.
4. **Modelo #4:** implementación real de SARIMAX con métricas de validación temporal.
