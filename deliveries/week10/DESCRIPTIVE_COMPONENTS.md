# Componentes descriptivos — Week 10 (RF1 y RF2)

Alcance de Week 10: solo funcionalidades descriptivas. **No hay predicción de precio, BCRP, forecasting, escenarios ni simulador.**

Fuente canónica: `deliveries/week07/code/EDA_week07.ipynb` y `deliveries/week07/data/`.
Código: `code/src/`. Entrenamiento: `code/scripts/train_clustering.py`. Artefactos: `models/`.

## Procedencia de los datos

| Fuente | Qué es | Uso en Week 10 |
|---|---|---|
| Anuncios inmobiliarios (scraping) | 3,822 anuncios originales de departamentos en alquiler recopilados de **Adondevivir** (3,113) y **Urbania** (709), 43 atributos (`deliveries/week04/acquisition.md`, `data_quality.md`). Captura del 2026-09-14 (columna `fecha_scraping`, UTC-5). | Tras el procesamiento de Week 7 (filtros de coordenadas, precio, área y doble modalidad venta/alquiler) quedan **3,128 anuncios** en `deliveries/week07/data/departamentos_procesados.csv` (Adondevivir 2,657 y Urbania 471). Sobre ellos se construyen los perfiles, y los comparables son filas reales de este archivo. |
| ATU | Inventario georreferenciado de 3,233 paraderos de transporte público, fuente externa (`timestamp_oficial` 2021-05-24). | Indicadores de accesibilidad (RF2). |

- Los precios mostrados son **precios publicados de oferta (asking prices)**, no precios finales de transacción.
- Para cada comparable se conservan en el backend el portal (`fuente`), el identificador original (`id_anuncio`), la URL y `fecha_scraping`. La interfaz muestra solo el portal. No se consultan los portales en tiempo real ni se verifica si los anuncios siguen activos.
- **Ninguna funcionalidad predictiva o prescriptiva forma parte de Week 10.**

## Uso

```python
# desde deliveries/week10/code (o con esa carpeta en sys.path)
from src.descriptive_service import analyze_descriptive
from src.clustering import predict_cluster
from src.comparables import get_comparables
from src.accessibility import get_accessibility

analyze_descriptive({
    "distrito": "Lince", "area_total": 70, "dormitorios": 2, "banos": 2,
    "antiguedad": 8, "mantenimiento": 250, "amenidades": ["ascensor"],
    "latitud": -12.085, "longitud": -77.035,
})
```

Reentrenar y probar (entorno con `code/requirements.txt`):

```bash
python deliveries/week10/code/scripts/train_clustering.py          # solo evalúa k=2..6
python deliveries/week10/code/scripts/train_clustering.py --k 3    # entrena y guarda
cd deliveries/week10/code && python -m pytest tests
```

## Contrato de entrada

| USER INPUT | Tipo | Obligatorio | Rango / valores |
|---|---|---|---|
| `distrito` | texto | sí | uno de los 40 distritos presentes en los datos (sin distinguir tildes ni mayúsculas; acepta "Santiago de Surco", "Cercado de Lima", etc.) |
| `area_total` | número | sí | 25–450 m² |
| `dormitorios` | entero | sí | 1–10 |
| `banos` | entero | sí | 1–10 |
| `amenidades` | lista | sí (puede ser vacía) | subconjunto de: ascensor, balcon, terraza, piscina, gimnasio, deposito, vista_al_mar, parrilla, areas_verdes, seguridad_24_7, coworking, juegos_infantiles, pet_friendly |
| `antiguedad` | número | no | 0–100 años |
| `mantenimiento` | número | no | S/ 50–2,500 por mes |
| `latitud`, `longitud` | número | sí (RF2) | Lima/Callao: lat [-12.35, -11.75], lon [-77.20, -76.80] |
| `id_anuncio_origen` | entero | no | solo para **casos reales del dataset**: identificador del anuncio cargado. Los demás valores deben coincidir con su fila del CSV (si no, error) y el anuncio se excluye de sus propios comparables |

Una entrada inválida levanta `InputValidationError`, cuyo atributo `.errors` reúne todos los problemas, incluidos los de RF1 y RF2. Nunca se sustituye un valor inválido en silencio.

| DERIVED FEATURES (backend) | Cómo se obtiene |
|---|---|
| `distrito` normalizado | `distrito_map` de Week 7 (In[12]) |
| grupo distrital | `distrito_norm` de Week 7: los distritos con menos de 20 anuncios forman "Otros" (In[13]) |
| `antiguedad` / `mantenimiento` faltantes | mediana del grupo distrital aprendida en entrenamiento; se informa en `warnings` y en `derived.imputed_for_profile` |
| vector estandarizado | `StandardScaler` aprendido en entrenamiento |
| `cluster_id` | K-Means persistido |
| `dist_paradero_min_m`, `paraderos_300m/500m/1000m`, `dist_troncal_brt_m`, `dist_corredor_m`, `paradero_cercano_tipo/afluencia/nombre` | índice ATU a partir de lat/lon |

## RF1 — Perfil competitivo

**Propósito.** Ubicar la propiedad en un segmento del mercado de anuncios usando solo características conocidas antes de fijar el precio.

**Dataset.** `week07/data/departamentos_procesados.csv` (3,128 anuncios con coordenadas validadas en Lima/Callao; SHA-256 en el metadata). No se usó `departamentos_sin_geo_para_clustering.csv`, la base del K-Means de Week 7, porque incluye 135 anuncios de otras ciudades (Arequipa, Chiclayo, Trujillo…) y 308 sin coordenadas.

**Variables (18).** `area_total`, `dormitorios`, `banos`, `antiguedad`, `mantenimiento` y las 13 amenidades. Es el conjunto de Week 7 sin `precio_m2_real`.

**Excluidas.**

| Variable | Motivo |
|---|---|
| `precio_soles`, `precio_m2_real`, `precio`, `precio_m2` | precio o transformación directa del precio (dependencia circular) |
| `cochera` | constante (=1) en todas las filas no nulas |
| `estacionamientos` | el 89% de los nulos es ambiguo (ya se excluía en Week 7) |
| `medios_banos`, `piso` | 78% y 43% de nulos; no forman parte del clustering canónico |
| banderas `*_imputado` | describen la calidad del anuncio, no el inmueble |
| BCRP, ATU | fuera del alcance de RF1 (ATU se reporta aparte, como RF2) |
| `distrito` | solo se usa para filtrar/priorizar comparables e imputar, no como distancia |

**Preprocesamiento.** Todos los parámetros se aprenden en entrenamiento y quedan guardados en `clustering_pipeline.joblib` (además de listarse en `clustering_metadata.json`).
- Limpieza: los valores fuera de los rangos del contrato pasan a NaN (1 en `banos`, 1 en `antiguedad`, 34 en `mantenimiento`). El rango 50–2,500 de mantenimiento es el que ya usaba In[4].
- Imputación (como en In[19]): mediana por grupo distrital para `antiguedad` y `mantenimiento`, con fallback a la mediana global; moda por dormitorios para `banos` (solo en entrenamiento, ya que en inferencia es obligatorio).
- Escalado: `StandardScaler`, también sobre las amenidades binarias, como en Week 7. No se aplica PCA.

**Selección de k.** K-Means con `n_init=10` y `random_state=42` sobre el espacio estandarizado.
- Estabilidad 1: ARI frente a las semillas 0, 1, 7, 123 y 2024.
- Estabilidad 2: ARI de 10 submuestras del 80% (el modelo se ajusta en la submuestra y se aplica a todo el dataset).

| k | silhouette | tamaños (%) | ARI semillas min | ARI submuestras min / media |
|---|---|---|---|---|
| 2 | 0.1674 | 37.7 / 62.3 | 0.995 | 0.968 / 0.982 |
| **3** | **0.1676** | **15.0 / 48.8 / 36.3** | **1.000** | **0.988 / 0.991** |
| 4 | 0.1751 | 48.0 / 28.8 / 8.7 / 14.4 | 0.987 | 0.981 / 0.986 |
| 5 | 0.1003 | 28.5 / 9.8 / 25.5 / 8.6 / 27.7 | 0.993 | 0.920 / 0.969 |
| 6 | 0.1034 | 7.8 / 8.4 / 25.0 / 23.9 / 8.1 / 26.7 | 0.953 | 0.715 / 0.821 |

**Se seleccionó k = 3.** k=3 fue seleccionado como compromiso entre estabilidad, interpretabilidad y utilidad para el producto. Aunque k=4 presenta un silhouette ligeramente mayor (0.1751 frente a 0.1676), incorpora un cluster pequeño fuertemente dominado por la amenidad `juegos_infantiles`, mientras que k=3 presenta mayor estabilidad y perfiles más generales para el objetivo descriptivo del prototipo.

- *Estabilidad.* k=3 obtiene ARI 1.000 entre semillas y 0.988 como mínimo entre submuestras, los valores más altos de los k evaluados.
- *Cluster dominado por una amenidad en k=4.* El cluster de 273 anuncios (8.7%) tiene `juegos_infantiles` = 100% frente a 0–3% en los demás, y reúne el 95% de los 286 anuncios con esa mención.
- *Tamaños.* En k=3 el cluster más pequeño reúne 468 anuncios (15%).
- *k=5 y k=6.* El silhouette cae a ≈0.10 y la estabilidad en submuestras baja (mínimo 0.92 y 0.71).

**Advertencia.** Todos los silhouette están por debajo de 0.25, es decir, la estructura global es débil. Los perfiles deben describirse siempre como una segmentación descriptiva exploratoria y no como grupos naturales del mercado.

**Perfiles (valores observados; medianas).** Los nombres son etiquetas separadas de `cluster_id` y están en `models/cluster_names.json`.

| id | nombre | n (%) | área | dorm | baños | antigüedad | mantenimiento | amenidades destacadas |
|---|---|---|---|---|---|---|---|---|
| 0 | Amplio con mantenimiento alto | 468 (15.0%) | 180 | 3 | 3 | 10 | S/ 650 | ascensor 59.4%, terraza 57.5%, depósito 37.2% |
| 1 | Tamaño medio con pocas amenidades | 1,526 (48.8%) | 75 | 2 | 2 | 10 | S/ 250 | la prevalencia más baja de las 13 amenidades (piscina 1.8%, gimnasio 3.6%) |
| 2 | Compacto y reciente con amenidades de condominio | 1,134 (36.3%) | 60 | 2 | 2 | 2 | S/ 250 | parrilla 86.1%, gimnasio 82.5%, piscina 65.5%, coworking 55.0% |

Como comprobación posterior (el precio no se usó en el entrenamiento), la mediana del precio publicado es S/ 6,100, S/ 2,400 y S/ 2,600, respectivamente.

**Estadísticas del segmento.** Se generan en `scripts/train_clustering.py` (`build_cluster_profiles`) a partir de los 3,128 anuncios y se guardan en `models/clustering_metadata.json`: n, %, mediana, media y p25/p75 de cada variable numérica (valores observados, sin imputar), prevalencia de cada amenidad y distritos principales. El frontend no contiene estadísticas fijas. `tests/test_real_cases.py` las recalcula desde el dataset.

**Posición frente al segmento.** `segment_comparison` compara cada variable numérica del inmueble con la mediana y el rango intercuartílico de su segmento, e indica para cada amenidad su prevalencia en el segmento. Es solo una comparación descriptiva: sin puntajes ni calificaciones.

## RF1 — Propiedades comparables

- **Espacio:** el mismo vector estandarizado de 18 variables del clustering; distancia euclidiana. No se usan precio, identificadores, URL ni texto.
- **Estrategia:**
  1. candidatos del mismo cluster;
  2. si hay al menos N del mismo distrito, se eligen solo entre ellos (`mismo_cluster_mismo_distrito`);
  3. si no, se toman todos los del mismo distrito y se completa con los más cercanos del mismo cluster en otros distritos (`mismo_cluster_ampliado_a_otros_distritos`); cada resultado lleva `mismo_distrito`;
  4. dentro de cada grupo se ordena por distancia, con desempate por `id_anuncio`.
- **N = 5** por defecto. `exclude_ids` permite excluir la propia propiedad cuando proviene del dataset.
- **Salida:** distrito, área, dormitorios, baños, antigüedad, mantenimiento (los valores observados; `null` si el anuncio no los informa), amenidades, `precio_soles_observado`, `precio_m2_real_observado`, `distancia_similitud`, `id_anuncio`, `fuente`, `url` y `fecha_scraping`. El precio es solo informativo.
- **Resumen de los comparables** (`comparables_summary`): mediana, mínimo y máximo del precio publicado, y mediana del precio publicado por m², calculados solo sobre los comparables devueltos. Estas estadísticas resumen únicamente los precios publicados de los anuncios comparables recuperados y no constituyen una estimación del precio del inmueble analizado. No existe "precio sugerido".

## Casos reales del dataset

`GET /api/example-properties` devuelve 3 anuncios reales de `departamentos_procesados.csv`, uno por cluster. Para cada uno entrega solo las características del formulario, más `id_anuncio`, `fuente` y `fecha_scraping`.
- **Regla determinista** (`src/examples.py`): por cada cluster, el anuncio más cercano al centroide en el espacio estandarizado, entre los que tienen baños, antigüedad y mantenimiento informados. Los empates se resuelven por el menor `id_anuncio`.
- **Sin resultados precalculados:** al analizar, el backend ejecuta el flujo completo. El caso usa sus coordenadas reales para RF2 y se excluye de sus propios comparables.

## RF2 — Perfil de accesibilidad

- **Metodología:** la de Week 7 (In[17]) sin cambios: proyección equirectangular centrada en lat −12.05 y `cKDTree` sobre los 3,233 paraderos de `week07/data/paraderos_procesado.csv`, con árboles separados para Troncal y Corredor. Los árboles se construyen una vez y se reutilizan.
- **Indicadores:** `dist_paradero_min_m`, `paraderos_300m`, `paraderos_500m`, `paraderos_1000m`, `dist_troncal_brt_m`, `dist_corredor_m`, `paradero_cercano_tipo`, `paradero_cercano_afluencia` (nivel de afluencia que reporta la ATU) y `paradero_cercano_nombre`. No se calculan tiempos, frecuencias, puntajes ni índices.
- **Verificación:** recalcularlos para los 3,128 anuncios reproduce exactamente las columnas de Week 7 (`tests/test_accessibility.py`).

## Limitaciones

- Los datos son anuncios (precios de oferta), no transacciones cerradas.
- Es una sola captura del mercado (scraping del 14-sep-2026).
- El inventario ATU es de mayo de 2021 (`timestamp_oficial` 2021-05-24) y puede no reflejar la red actual.
- El clustering es una segmentación descriptiva exploratoria de estructura débil (silhouette 0.1676), no una clasificación verdadera ni un conjunto de grupos naturales del mercado.
- Las amenidades provienen de palabras clave en texto libre: un 0 significa "no mencionado", no "no existe".
- La antigüedad y el mantenimiento faltantes se imputan con medianas distritales, tanto para la propiedad consultada como para los anuncios del dataset. Esto influye en el cluster y en la distancia.
- La similitud utiliza actualmente 18 dimensiones, de las cuales 13 corresponden a amenidades binarias. Por ello, las amenidades pueden tener un peso importante en la selección de comparables. La ponderación de características será objeto de evaluación posterior.
- Los comparables dependen de la cobertura del dataset: los distritos con pocos anuncios recurren al fallback, y solo se aceptan los 40 distritos presentes.
- Similitud estadística no implica equivalencia inmobiliaria. Hay posibles duplicados entre portales.
- No se verifica que las coordenadas correspondan al distrito declarado.
- En Week 10 todavía no hay predicción de precio, forecasting ni recomendación prescriptiva.
