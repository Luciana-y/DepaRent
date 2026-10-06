# Week 08 – Estado del proyecto DepaRent

**Curso:** DS3022 – Desarrollo de Producto de Datos
**Equipo:** Adrian Urbina Mendoza · Armando Martinez Palomino · Breysi Salazar Medina · Luciana Yangali Cáceres
**Fecha:** octubre 2026 (posterior a Delivery 1, previo al prototipo funcional de Week 10)


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

## 4. Los 6 modelos de DepaRent y su avance

DepaRent se compone de seis componentes analíticos. Los cuatro primeros responden al requerimiento R1 (analizar y valorar el inmueble) y los dos últimos al R2 (recomendar una estrategia de publicación). A continuación se explica brevemente cada uno, en orden, junto con su avance actual.

**Resumen del avance**

| # | Modelo | Método | Avance |
|:-:|---|---|---|
| 1 | Perfil competitivo | K-Means (k=4) | Entrenado y validado; falta la búsqueda de comparables |
| 2 | Perfil de accesibilidad | Variables espaciales con cKDTree | Implementado |
| 3 | Precio esperado | HistGradientBoosting | Entrenado y evaluado; falta tuning e intervalos |
| 4 | Tendencia distrital | SARIMA (d=1, s=4) | Justificado con ADF; falta ajustar el modelo |
| 5 | Escenarios de precio | Motor de reglas sobre 1 + 3 + 4 | Diseñado; no implementado |
| 6 | Simulador de mejoras | Uso contrafactual del modelo 3 | Diseñado; no implementado |

### Modelo 1 – Perfil competitivo (clustering)

**Qué hace.** Agrupa los departamentos en segmentos de mercado según área, dormitorios, baños, precio por m², antigüedad, mantenimiento y 13 amenidades. Así el propietario se compara solo contra inmuebles realmente parecidos al suyo y no contra todo el mercado.

**Método.** K-Means con k=4 sobre 19 variables estandarizadas, sin PCA. Antes se probaron otras configuraciones:
- 9 variables + PCA: silhouette 0.274.
- Gaussian Mixture Model: silhouette 0.196. Se descartó.
- Distrito en one-hot: silhouette entre 0.04 y 0.10. Se descartó.

Se eligió la configuración actual porque cada amenidad sigue siendo interpretable para el propietario.

**Avance.**
- Entrenado, con silhouette de **0.1776**.
- Los clusters son estables ante distintas semillas aleatorias (ARI ≥ 0.999).
- Identifica cuatro perfiles: estándar tradicional (49.3%), propiedades amplias (14.7%), compacto con amenidades (27.5%) y residencial familiar (8.5%).

**Pendiente.**
- Implementar la segunda etapa: buscar los k vecinos más cercanos dentro del cluster, considerando también la ubicación.
- Quitar la variable de precio del clustering. El propietario todavía no conoce su precio, así que para asignarle un cluster hay que usar el precio predicho por el modelo 3 o no usar precio.
- El silhouette es bajo (< 0.25): los segmentos son una heurística útil, no grupos naturalmente separados.

### Modelo 2 – Perfil de accesibilidad

**Qué hace.** Mide qué tan bien conectado está el departamento con el transporte público, a partir de los 3,233 paraderos georreferenciados de la ATU.

**Método.** No es un modelo de machine learning: es ingeniería de variables espaciales con un índice `cKDTree`. Calcula:
- la distancia al paradero más cercano;
- el número de paraderos a 300 m, 500 m y 1,000 m;
- la distancia al Metropolitano y a los corredores.

**Avance.**
- Implementado.
- La distancia mediana al paradero más cercano es de 174.8 m, y el 71.6% de los departamentos tiene un paradero a menos de 300 m.
- Estas variables aportan al modelo de precio: la distancia al paradero y la distancia al Metropolitano están entre las cinco más importantes.

**Pendiente.** Empaquetarlo como función reutilizable para el prototipo. Hay que considerar que el inventario de paraderos es de 2021.

### Modelo 3 – Precio esperado de alquiler (regresión)

**Qué hace.** Estima el alquiler mensual esperado (`precio_soles`) a partir de las características del inmueble, su accesibilidad y el contexto del distrito según el BCRP. Es el núcleo del producto.

**Método.** Se compararon seis algoritmos con un split 80/20, hecho antes de imputar. La imputación ocurre dentro del `Pipeline`, así que no hay fuga de datos.

| Modelo | R² | MAE (S/) | RMSE (S/) | MAPE |
|---|---:|---:|---:|---:|
| **HistGradientBoosting** | **0.8332** | **491.74** | **830.11** | **15.77%** |
| Gradient Boosting | 0.8003 | 514.02 | 908.50 | 16.13% |
| Random Forest | 0.7863 | 503.50 | 939.60 | 16.05% |
| KNN (k=7) | 0.7920 | 534.78 | 927.06 | 16.95% |
| Ridge | 0.7786 | 621.74 | 956.53 | 21.51% |
| Baseline Dummy (mediana) | -0.0689 | 1,213.26 | 2,101.61 | 36.59% |

**Avance.**
- Entrenado y evaluado. HistGradientBoosting reduce el error en **56.9%** frente al baseline.
- Con validación cruzada agrupada (GroupKFold de 5 folds, que agrupa anuncios duplicados entre portales) el MAPE es **15.57% ± 0.40**. El resultado es robusto a la partición y a los duplicados.
- Las variables más influyentes son `area_total`, `mantenimiento`, `dist_paradero_min_m`, `dist_troncal_brt_m` y `banos`.

**Pendiente.**
- Ajuste de hiperparámetros.
- Intervalos de predicción, para mostrar un rango y no solo un valor.
- Importancia de variables calculada sobre el propio HistGradientBoosting; hoy se reporta la del Random Forest.
- Guardar el modelo entrenado (`.joblib`) para el prototipo.

### Modelo 4 – Tendencia distrital (series de tiempo)

**Qué hace.** Indica si el alquiler en el distrito del inmueble tiende a subir, bajar o mantenerse, usando las series trimestrales del BCRP (2013-T3 a 2026-T1, 12 distritos más el promedio).

**Método.** SARIMA con diferenciación de primer orden y estacionalidad trimestral (d=1, s=4). El baseline de comparación es un naive estacional: el mismo trimestre del año anterior.

**Avance.** Solo está la justificación del modelo. La prueba ADF muestra que **9 de las 13 series (69.2%) no son estacionarias**, lo que descarta un ARIMA sin diferenciar.

**Pendiente.**
- Ajustar el SARIMA. Todavía no está implementado.
- Validarlo con un esquema temporal (entrenar con trimestres pasados y evaluar en los últimos) contra el baseline naive.
- Definir qué se muestra en los distritos que no tienen serie propia en el BCRP. Esto afecta al 16.3% de los departamentos, que hoy usan el promedio general.

### Modelo 5 – Escenarios de precio de publicación

**Qué hace.** Propone tres precios de publicación según el objetivo del propietario: competitivo (alquilar rápido), equilibrado y renta superior.

**Método.** No es un modelo de machine learning nuevo. Es un motor de reglas que combina:
- el precio esperado del modelo 3;
- el rango de precios de los comparables del modelo 1;
- la tendencia del distrito del modelo 4.

**Avance.** Diseñado y con wireframe, pero no implementado.

**Pendiente.** Implementarlo cuando los modelos 1, 3 y 4 estén listos (previsto para Week 12) y definir las reglas exactas de cada escenario.

### Modelo 6 – Simulador de mejoras

**Qué hace.** Estima cuánto cambiaría el precio esperado si el propietario hiciera una mejora, por ejemplo agregar cochera o terraza.

**Método.** Reutiliza el modelo 3 de forma contrafactual:
1. Predice el precio con el estado actual del inmueble.
2. Cambia virtualmente un atributo.
3. Vuelve a predecir manteniendo el resto igual.

La diferencia se presenta como una asociación, no como un efecto causal.

**Avance.** Diseñado y con wireframe, pero no implementado.

**Pendiente.** Implementarlo cuando el modelo 3 esté guardado (previsto para Week 12) y limitar los atributos que se pueden modificar a los que el propietario realmente puede cambiar.

### Correcciones hechas en esta revisión (Week 8)

- **`coworking`:** la extracción desde texto se inflaba por la palabra clave `"sum"`, que coincidía con "consumo", "sumamente", etc. Se corrigió y la prevalencia pasó de 30.3% a 19.7%.
- **`pet_friendly`:** contaba como positivos los anuncios que prohíben mascotas ("no se aceptan mascotas"). Se corrigió y la prevalencia pasó de 26.7% a 13.4%.
- **Datos procesados:** los CSV de `week07/data/` no correspondían al notebook (3,165 filas en vez de 3,128). Se regeneraron.
- **Dependencias:** se agregó `requirements.txt` y se verificó que el notebook corre completo en un entorno limpio.

Las cifras de este documento son las de después de estas correcciones. Las del Delivery 1 eran: MAPE 15.93%, R² 0.8236 y silhouette 0.1647.

## 5. Estado del producto fuera de los modelos

| Elemento | Estado |
|---|---|
| Adquisición y limpieza de las 3 fuentes | Funciona y es reproducible desde el notebook |
| Datos procesados y diccionario de datos | Disponibles en `week07/data/` |
| Modelos guardados (`.joblib`) | Pendiente (Week 10) |
| Pipeline como módulos `.py` reutilizables | Pendiente (Week 9) |
| Aplicación web (frontend y backend) | Solo wireframes y arquitectura; el desarrollo empieza para Week 10 |
| Despliegue | Pendiente (Week 14–15) |

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

### Nuestras dudas

**Sobre el producto y su alcance**

- **Alcance.** ¿Seis funcionalidades son demasiadas para el tiempo que queda? Si conviene reducir el alcance, ¿cuáles priorizaría para que el producto final sea sólido?
- **Prioridad para Week 10.** ¿Qué espera ver en el prototipo funcional: un flujo completo aunque sea sencillo, o menos funcionalidades pero más trabajadas?

**Sobre los usuarios y la validación**
- **Validación con usuarios.** ¿Cómo podríamos validar el producto con propietarios reales? Nos ayudaría saber si conoce contactos (por ejemplo, administradores de edificios o personas del sector inmobiliario) dispuestos a probarlo o darnos su opinión.
- **Caso de estudio.** Para el caso de estudio de Week 12, ¿es suficiente un propietario representativo con datos reales del mercado, o se espera que sea una persona real usando la plataforma?

**Sobre los datos y el despliegue**
- **Datos de transporte.** El inventario de paraderos de la ATU es de 2021. ¿Conoce alguna fuente más actual o algún contacto en una entidad pública que pueda facilitarla?
- **Despliegue.** ¿El curso ofrece o recomienda alguna plataforma para publicar el prototipo, o lo decidimos nosotros?
