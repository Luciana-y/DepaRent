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

### Proceso de selección — 5 configuraciones evaluadas

Se realizó una comparación sistemática y rigurosa antes de fijar la configuración final, dado que el silhouette inicial (9 features, sin reducción) resultaba moderado (0.237):

| # | Configuración | Features | Filas (n) | Mejor k | Silhouette | Resultado |
|:-:|---|:---:|:---:|:---:|:---:|---|
| 1 | Original (sin PCA) | 9 | 3,128 | 2 | 0.237 | Punto de partida |
| 2 | Distrito vía one-hot | 9 + ~20 dummies | 3,128 | 7 | 0.041–0.105 | ❌ Descartado — dimensionalidad dispersa diluye la distancia |
| 3 | Gaussian Mixture Model | 9 | 3,128 | 7 | 0.196 | ❌ Descartado — BIC monotónicamente decreciente indica degeneración del modelo (variables binarias violan el supuesto gaussiano) |
| 4 | 20 features (con `cochera`) | 20 | 1,894 (47% perdido) | 2 | 0.150 | ❌ Descartado — pérdida masiva de muestra por ambigüedad de nulos en `cochera`/`estacionamientos` |
| 5 | 19 features (sin `cochera`/`estacionamientos`) + imputación por distrito | 19 | 3,548 (99.4%) | 4 | 0.178 | ❌ Descartado — resultado estable ante distinto método de imputación, pero amenidades de baja prevalencia diluyen la señal |
| **6** | **9 features + PCA (6 componentes, 90% varianza)** | **9** | **3,128** | **2** | **0.274** | ✅ **Seleccionado** |

**Features finales (9):** `area_total`, `dormitorios`, `banos`, `precio_m2_real`, `piscina`, `gimnasio`, `cochera`, `seguridad_24_7`, `coworking`.

**Por qué se descartó `distrito`, `estacionamientos` y las 9 amenidades de menor prevalencia:**
- `distrito`: aunque es información valiosa para el negocio, su codificación one-hot genera ~20 columnas dispersas que degradan la distancia euclidiana en K-Means. Se traslada a una **segunda etapa** de búsqueda de comparables (k-NN dentro del cluster y filtrado por distrito), consistente con el diseño original del proposal.
- `estacionamientos`/`cochera`: 41-47% de nulos ambiguos (solo 10.75% confirmable por texto, ver `data_quality.md`); imputar o incluir con `dropna()` degrada la muestra o el resultado. Se preservan como features del **Modelo #3**, donde su tratamiento vía flag de missingness es más apropiado.
- Amenidades de baja prevalencia (`balcon`, `terraza`, `vista_al_mar`, `parrilla`, `areas_verdes`, `juegos_infantiles`, `pet_friendly`, `deposito`, `ascensor`): agregarlas (con o sin imputación de variables numéricas asociadas) produjo consistentemente peor silhouette (0.178) que la versión de 9 features, confirmado con dos métodos de imputación distintos — la parsimonia gana sobre la exhaustividad en este caso.

### Modelo final: K-Means (k=2) sobre componentes PCA

**Preprocesamiento:** estandarización (`StandardScaler`) → PCA (6 componentes, 90% de varianza explicada) → K-Means.

**Perfiles resultantes** (K-Means final sobre componentes PCA, calculados sobre las 9 variables originales para mantener interpretabilidad):

| Cluster | Área media | Precio/m² | Piscina | Gimnasio | Coworking | Seguridad 24/7 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| 0 — Tradicional/Amplio | 102.6 m² | S/ 34.30 | 3% | 5% | 14% | 39% |
| 1 — Moderno/Alta amenidad | 70.2 m² | S/ 46.50 | 67% | 81% | 60% | 55% |

*Verificado: el perfil de negocio es equivalente al obtenido con K-Means sin PCA (diferencias de 1-5 puntos porcentuales en cada variable), confirmando que la reducción de dimensionalidad mejora el silhouette (0.237 → 0.274) sin alterar la interpretación de los segmentos.*

**Pendiente para Delivery 1:** evaluar si un k mayor, o un clustering *dentro* de cada distrito por separado, revela subsegmentos adicionales útiles para el propietario.

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
