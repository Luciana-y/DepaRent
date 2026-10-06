# Week 08 – Estado del proyecto DepaRent

**Curso:** DS3022 – Desarrollo de Producto de Datos
**Equipo:** Adrian Urbina Mendoza · Armando Martinez Palomino · Breysi Salazar Medina · Luciana Yangali Cáceres
**Fecha:** octubre 2026 (posterior a Delivery 1, previo al prototipo funcional de Week 10)

Este documento responde, punto por punto, a la solicitud de revisión de avance. Para no duplicar archivos, cada punto enlaza a su ubicación en el repositorio.

---

## Índice de materiales

| Material solicitado | Ubicación |
|---|---|
| Presentación actualizada | [`PresentationWeek08.pptx`](PresentationWeek08.pptx) · [`PresentationWeek08.pdf`](PresentationWeek08.pdf) |
| Notebook (.ipynb) y código | [`../week07/code/EDA_week07.ipynb`](../week07/code/EDA_week07.ipynb) |
| Datos originales | [`../week04/data/`](../week04/data/) |
| Datos procesados | [`../week07/data/`](../week07/data/) |
| Diccionario de datos | [`../week07/data_dictionary.csv`](../week07/data_dictionary.csv) |
| Dependencias | [`../../requirements.txt`](../../requirements.txt) |
| Reporte de Delivery 1 | [`../week07/Delivery1Report.pdf`](../week07/Delivery1Report.pdf) |
| Arquitectura y wireframes | [`../week07/architecture/`](../week07/architecture/) · [`../week07/design/`](../week07/design/) |
| Plan de implementación | [`../week07/planning/Implementation_Plan.md`](../week07/planning/Implementation_Plan.md) |

---

## 1. Problema, usuario objetivo y solución propuesta

**Problema.** Los propietarios fijan el precio de alquiler comparando manualmente anuncios de portales inmobiliarios. Esos anuncios no siempre son comparables: hay diferencias de ubicación, área, amenidades, accesibilidad y contexto del distrito.

**Usuario objetivo.** Propietario de uno o varios departamentos en alquiler en Lima Metropolitana y Callao. Como usuario secundario está la persona que busca alquilar y explora los anuncios publicados.

**Solución.** DepaRent es una plataforma web de apoyo a la decisión que, a partir de las características del inmueble:

- **R1 – Analiza y valora el inmueble:** perfil competitivo y comparables, accesibilidad a transporte público, precio esperado y tendencia del distrito.
- **R2 – Recomienda una estrategia de publicación:** escenarios de precio (competitivo, equilibrado, renta superior) y simulación de mejoras.

DepaRent no realiza tasaciones oficiales ni garantiza el precio final de alquiler.

## 2. Datos: fuente y naturaleza

| Dataset | Fuente | Tipo | Tamaño | Corte temporal |
|---|---|---|---|---|
| `departamentos_alquiler_lima.csv` | Anuncios de Adondevivir (3,113) y Urbania (709), obtenidos por web scraping | **Real**, de anuncios públicos (no sintético) | 3,822 anuncios × 43 columnas | 14-sep-2026 |
| `dataset_alquileres_trimestre_bcrp.csv` | API oficial de estadísticas del BCRP (PER, precio de venta US$/m², tipo de cambio) | **Real, público y oficial** | 663 obs. (13 series × 51 trimestres) | 2013-T3 a 2026-T1 |
| `paraderos.csv` | Inventario de paraderos de la ATU, recuperado del espejo de datos abiertos `jmcastagnetto/lima-atu-covid19-paraderos` | **Real y público** (copia de un archivo oficial) | 3,233 paraderos × 10 columnas | mayo 2021 |

Notas:
- La columna `Alquiler_Mensual_Soles` del BCRP es **derivada** (precio de venta × tipo de cambio ÷ PER ÷ 12); no es un alquiler observado.
- Los anuncios provienen de portales comerciales y pueden estar sujetos a sus términos de uso. Se usan solo con fines académicos.
- El procedimiento de adquisición está en [`../week04/acquisition.md`](../week04/acquisition.md) y la calidad de datos en [`../week04/data_quality.md`](../week04/data_quality.md).

**Preprocesamiento (resumen).** Recuperación de atributos desde el texto libre (piso, antigüedad, estacionamientos, mantenimiento y 13 amenidades). Filtros de precio (S/ 800–25,000), área (25–450 m²), coordenadas dentro de Lima y exclusión de anuncios de venta: quedan **3,128 departamentos** (se descarta el 18.16%). Se cruzan con el BCRP por distrito y con los paraderos de la ATU mediante `cKDTree`.

## 3. Variable objetivo

| Componente | Tipo de tarea | Variable |
|---|---|---|
| Precio esperado (núcleo ML) | **Regresión** | `precio_soles`: alquiler mensual en soles |
| Perfil competitivo | Segmentación (no supervisado) | Cluster de pertenencia (4 perfiles) |
| Tendencia distrital | Pronóstico de series de tiempo | `Alquiler_Mensual_Soles` trimestral por distrito (BCRP) |
| Escenarios y simulador | Prescriptivo (reglas y contrafactual) | Precio recomendado y Δ de precio por mejora |

## 4. Modelos probados, métricas y conclusiones

### Modelo 3 – Precio esperado (regresión)

Split 80/20 hecho **antes** de imputar. Toda la imputación ocurre dentro del `Pipeline`, así que no hay fuga de datos.

| Modelo | R² | MAE (S/) | RMSE (S/) | MAPE |
|---|---:|---:|---:|---:|
| **HistGradientBoosting** | **0.8332** | **491.74** | **830.11** | **15.77%** |
| Gradient Boosting | 0.8003 | 514.02 | 908.50 | 16.13% |
| Random Forest | 0.7863 | 503.50 | 939.60 | 16.05% |
| KNN (k=7) | 0.7920 | 534.78 | 927.06 | 16.95% |
| Ridge | 0.7786 | 621.74 | 956.53 | 21.51% |
| Baseline Dummy (mediana) | -0.0689 | 1,213.26 | 2,101.61 | 36.59% |

**Conclusión:** HistGradientBoosting reduce el MAPE en **56.9%** frente al baseline.
- **Robustez:** con validación cruzada agrupada (GroupKFold de 5 folds, que agrupa anuncios duplicados entre portales) el MAPE es **15.57% ± 0.40**. El resultado no depende de la partición ni de los duplicados.
- **Variables más influyentes:** `area_total`, `mantenimiento`, `dist_paradero_min_m`, `dist_troncal_brt_m` y `banos`.

### Modelo 1 – Perfil competitivo (clustering)

Configuraciones evaluadas: 9 variables + PCA (silhouette 0.274), GMM (0.196, descartado), one-hot de distrito (0.04–0.10, descartado). Se eligió **K-Means con k=4 sobre 19 variables, sin PCA (silhouette 0.1776)** porque cada amenidad sigue siendo interpretable para el propietario.
- **Estabilidad:** los clusters son estables entre semillas (ARI ≥ 0.999).
- **Perfiles:** estándar tradicional (49.3%), amplias (14.7%), compacto con amenidades (27.5%) y residencial familiar (8.5%).
- **Limitación:** el silhouette es bajo (< 0.25), así que los segmentos son una heurística útil, no grupos naturalmente separados.

### Modelo 2 – Accesibilidad

Ingeniería de variables espaciales, no es un modelo de ML. La distancia mediana al paradero más cercano es 174.8 m y el 71.6% de los departamentos está a menos de 300 m. Estas variables están entre las más importantes del modelo de precio.

### Modelo 4 – Tendencia distrital

El test ADF indica que **9 de 13 series (69.2%) no son estacionarias**, lo que justifica un **SARIMA (d=1, s=4)** frente a un baseline naive estacional. **El SARIMA todavía no está ajustado** (ver sección 5).

### Modelos 5 y 6 – Escenarios y simulador

Motor de reglas que combina los resultados de los modelos 1, 3 y 4, y uso contrafactual del modelo 3. Están diseñados, pero no implementados.

### Correcciones hechas en esta revisión (Week 8)

- **`coworking`:** la extracción desde texto se inflaba por la palabra clave `"sum"`, que coincidía con "consumo", "sumamente", etc. Se corrigió y la prevalencia pasó de 30.3% a 19.7%.
- **`pet_friendly`:** contaba como positivos los anuncios que prohíben mascotas ("no se aceptan mascotas"). Se corrigió y la prevalencia pasó de 26.7% a 13.4%.
- **Datos procesados:** los CSV de `week07/data/` no correspondían al notebook (3,165 filas en vez de 3,128). Se regeneraron.
- **Dependencias:** se agregó `requirements.txt` y se verificó que el notebook corre completo en un entorno limpio.

Las cifras de este documento son las de después de estas correcciones. Las del Delivery 1 eran: MAPE 15.93%, R² 0.8236 y silhouette 0.1647.

## 5. Qué funciona y qué falta

| Componente | Estado |
|---|---|
| Adquisición y limpieza de las 3 fuentes | ✅ Funciona y es reproducible |
| Variables de accesibilidad (ATU) | ✅ Funciona |
| Modelo de precio (HistGradientBoosting) | ✅ Entrenado y evaluado. ⏳ Falta tuning e intervalos de predicción |
| Perfil competitivo (K-Means k=4) | ✅ Entrenado y validado en estabilidad. ⏳ Falta la búsqueda de comparables (k-NN dentro del cluster + ubicación) |
| Tendencia distrital (SARIMA) | ⚠️ Solo justificado con ADF. ❌ Falta ajustar el modelo y validarlo temporalmente |
| Escenarios de precio | ❌ Diseñado, no implementado |
| Simulador de mejoras | ❌ Diseñado, no implementado |
| Modelos serializados (.joblib) | ❌ Pendiente (Week 10) |
| Aplicación web (frontend y backend) | ❌ Solo hay wireframes; el desarrollo empieza para Week 10 |

**Problema de diseño identificado:** el clustering usa `precio_m2_real` como variable. En el producto, el propietario todavía no conoce su precio, así que para asignarle un cluster hay que quitar esa variable o reemplazarla por el precio que predice el modelo 3. Se resolverá antes de Week 10.

## 6. Resultado que queremos demostrar en la presentación final

Un flujo completo para un propietario real: ingresa su departamento (por ejemplo, 70 m², 2 dormitorios, 2 baños, en Lince) y la plataforma devuelve:

1. Su perfil competitivo y 5–10 departamentos comparables.
2. Su accesibilidad a transporte público.
3. Un precio esperado con un rango de error (MAPE de alrededor de 16%).
4. La tendencia del alquiler en su distrito.
5. Tres escenarios de precio de publicación.
6. El impacto estimado de una mejora (por ejemplo, agregar cochera), con advertencia de que es una asociación y no causalidad.

## 7. Instrucciones de ejecución

```bash
git clone https://github.com/Luciana-y/DepaRent.git
cd DepaRent
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1   |   Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
jupyter notebook deliveries/week07/code/EDA_week07.ipynb
```

Ejecutar **Run All**. El notebook encuentra solo los datos crudos en `deliveries/week04/data/` y escribe los procesados en `deliveries/week07/code/processed/`. No requiere credenciales ni variables de entorno. Tarda unos minutos, sobre todo por t-SNE y UMAP.

## 8. Limitaciones conocidas

- **Precios publicados, no cerrados:** los anuncios reflejan el precio pedido, no el contrato final.
- **Captura única:** es un solo scraping (14-sep-2026); no hay historia propia de anuncios.
- **Paraderos desactualizados:** el inventario de la ATU es de mayo de 2021 y puede no reflejar la red actual.
- **Cobertura del BCRP:** solo cubre 12 distritos. El 16.3% de los departamentos usa el promedio general.
- **Extracción desde texto:** las amenidades, el piso y la antigüedad dependen de reglas sobre el texto libre y pueden tener errores residuales. Por ejemplo, `seguridad_24_7` usa palabras clave amplias.
- **Estacionamientos:** el 89.25% de los nulos es ambiguo, así que se excluyen del clustering.
- **Clustering débil:** el silhouette es bajo (0.1776).

## 9. Próximos pasos y qué necesitamos

| Semana | Entregable |
|---|---|
| Week 9 | Pipeline como módulos `.py`, comparables k-NN, clustering sin precio |
| Week 10 | Modelo de precio serializado, endpoint de inferencia y primer prototipo web |
| Week 11 | SARIMA ajustado y validado; respuesta analítica integrada |
| Week 12 | Escenarios de precio, simulador, evaluación y caso de estudio |
| Week 13–15 | Integración, pruebas con usuarios, despliegue y Delivery 2 |

**Lo que necesitamos:**
- Retroalimentación sobre si priorizar el prototipo web completo o la profundidad de los modelos (SARIMA, comparables) para Week 10.
- Validar si el uso académico de los datos obtenidos por scraping es aceptable en un repositorio público, o si conviene publicar solo una muestra.
