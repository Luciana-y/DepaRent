# DataAnalysis — Semana 06

**Proyecto:** DepaRent — Plataforma inteligente para propietarios de departamentos en alquiler
**Curso:** DS3022 — Desarrollo de Producto de Datos

---

## 1. Datasets utilizados

| Dataset | Registros | Columnas | Descripción |
|---|:---:|:---:|---|
| **Departamentos (Scraping)** | 3,822 | 43 | Anuncios individuales de alquiler en Lima Metropolitana y Callao (Adondevivir + Urbania), incluyendo `medios_banos` y `texto_amenidades_crudo`. |
| **BCRP (Trimestral)** | 663 | 6 | Series trimestrales de PER, precio de venta por m² en USD y alquiler mensual en soles, por distrito (T3-2013 a T1-2026). |
| **Paraderos (ATU)** | 3,233 | 10 | Inventario oficial de paraderos del sistema de transporte metropolitano (Troncal BRT, Corredores y Transporte Regular), corte mayo 2021. |

---

## 2. Diagnóstico de nulos en el dataset crudo

En el archivo crudo existen **17 columnas con 100% de valores nulos**:

`ascensor, balcon, terraza, piscina, gimnasio, deposito, vista_al_mar, parrilla, areas_verdes, seguridad_24_7, coworking, juegos_infantiles, pet_friendly, piso, estado_inmueble, nombre_proyecto, caracteristicas`

**Esta condición es por diseño, no un error del scraper.** Se investigó directamente la estructura del JSON `__PRELOADED_STATE__` del portal Navent (Adondevivir/Urbania) y se confirmó que el backend **no expone estas amenidades ni el número de piso como campos estructurados** para anuncios individuales de alquiler — solo existen 7 códigos `CFT###` estructurados (área total, área techada, dormitorios, baños, medios baños, antigüedad, estacionamientos). Por diseño arquitectónico, el scraper separa adquisición de inferencia: preserva estos campos como `NaN` y concatena todo el texto libre en `texto_amenidades_crudo` para que la extracción se realice de forma trazable en esta etapa de EDA, evitando imputación oculta y fuga de información hacia el modelado.

Otras columnas con nulos relevantes en el dataset crudo:

| Columna | % Nulos |
|---|:---:|
| `medios_banos` | 76.32% |
| `estacionamientos` / `cochera` | 45.79% |
| `mantenimiento` | 26.19% |
| `antiguedad` | 23.00% |
| `latitud` / `longitud` | 8.77% |
| `area_construida` | 8.63% |
| `banos` | 0.55% |

---

## 3. Recuperación de información desde texto libre

Se aplicaron expresiones regulares sobre `texto_amenidades_crudo` para recuperar datos existentes en el texto pero no capturados en campos estructurados:

| Variable | Registros recuperados | Cobertura ganada | Nulos restantes | Criterio de extracción |
|---|:---:|:---:|:---:|---|
| `piso` | 2,098 | 54.89% | 1,724 | Patrones de nivel y número de piso (rango válido: 1 a 45). |
| `antiguedad` | 521 | 13.63% | 358 | Años declarados o mención explícita de "estreno" (antigüedad = 0). |
| `estacionamientos` | 197 | 5.15% | 1,553 | Cocheras identificadas explícitamente en texto. **Los nulos restantes no se reemplazan con 0** — ver nota metodológica más abajo. |
| `mantenimiento` | 43 | 1.13% | 958 | Cuotas mensuales en soles (rango admisible: S/ 50 a S/ 2,500). |

### 3.1 Extracción de las 14 amenidades desde texto

Prevalencia de amenidades tras la extracción por palabras clave:

- **Mayor prevalencia:** `cochera` (100% de los avisos con estacionamientos informados), `seguridad_24_7` (44.6%), `parrilla` (37.6%), `ascensor` (36.1%), `gimnasio` (33.0%), `balcon` (31.9%), `coworking` (30.3%), `terraza` (29.3%).
- **Presencia media:** `piscina` (27.2%), `pet_friendly` (26.7%), `vista_al_mar` (15.5%), `areas_verdes` (14.1%), `deposito` (12.0%).
- **Baja cobertura (<10%):** `juegos_infantiles` (8.7%), concentrada en condominios familiares de gran escala.

### Nota metodológica — ambigüedad de `estacionamientos`

La validación cruzada contra el texto mostró que, de los 1,553 anuncios sin dato estructurado de `estacionamientos`, solo el **10.75%** menciona explícitamente tener cochera. El **89.25% restante es ambiguo**: podría representar "no tiene cochera" o simplemente "no se informó". Por este motivo, el dato faltante **no se imputa a 0** ni se asume ausencia — se preserva como `NaN` y se documenta mediante una columna indicadora (`estacionamientos_imputado`) para su tratamiento contextual en el modelado.

---

## 4. Flags de missingness

Para evitar imputar silenciosamente las variables numéricas, se crean indicadores binarios (`_imputado`) que documentan qué filas requirieron imputación posterior:

| Indicador | Registros nulos | % (sobre 3,822) |
|---|:---:|:---:|
| `estacionamientos_imputado` | 1,553 | 40.63% |
| `mantenimiento_imputado` | 958 | 25.07% |
| `antiguedad_imputado` | 358 | 9.37% |
| `area_construida_imputado` | 330 | 8.63% |
| `banos_imputado` | 21 | 0.55% |

Estas columnas se incorporan como features del Modelo #3, permitiendo que el modelo capture si la ausencia de un dato es en sí misma informativa (por ejemplo, anuncios menos detallados podrían correlacionar con ciertos segmentos de mercado).

---

## 5. Filtro geográfico, de outliers y de doble modalidad

Se descartaron **694 observaciones (18.16%)** del dataset original de 3,822 anuncios, por cuatro motivos:

1. **Coordenadas inválidas (335 filas):** sin coordenadas válidas o ubicadas fuera del cuadrante de Lima Metropolitana y Callao `[-12.35, -11.75] × [-77.20, -76.80]`.
2. **Precios atípicos (181 filas):** `precio_soles` fuera del rango [S/ 800, S/ 25,000], equivalente al **percentil 96.02** de la distribución observada.
3. **Área fuera de rango (51 filas):** `area_total` menor a 25 m² o mayor a 450 m².
4. **Doble modalidad venta/alquiler (127 filas):** anuncios identificados como "venta y alquiler" mediante palabras clave en el título (`venta`, `vendo`, `se vende`), donde el precio capturado corresponde a una operación de venta y no de alquiler.

### Hallazgo — por qué el filtro de precio por sí solo no bastaba

La inspección manual de los 15 casos con `precio_soles` más alto (hasta S/10,500,000) confirmó que la causa dominante **no era un segmento premium legítimo**, sino anuncios de doble modalidad donde el scraper capturó el precio de venta (ej. *"Vendo/alquilo Penthouse... S/10,500,000"*). Al verificar el resto de estos anuncios, se encontró que **40 de los 127 casos** tenían un precio de venta que coincidencialmente caía dentro del rango de alquiler plausible (≤ S/25,000) y **no habrían sido detectados únicamente con el filtro de precio**. Por eso se excluyen por título, no solo por monto — el campo `precio_soles` de estos anuncios no es confiable para el problema de alquiler, independientemente de su magnitud.

**El dataset depurado (`df_clean`) queda conformado por 3,128 departamentos (81.84% del original)**, listos para el análisis espacial y los modelos predictivos.

### 5.1 Corrección de typo verificado por geolocalización: "Barranca" → "Barranco"

Al listar las frecuencias de distrito en el dataset filtrado se detectó 1 anuncio (`id_anuncio 150601693`) clasificado con `distrito = "Barranca"`. *Barranco* es un distrito real de Lima; *Barranca* es una provincia a más de 180 km al norte, fuera del bounding box aplicado en la sección 5. Al inspeccionar sus coordenadas geográficas (`lat = -12.118873, lon = -77.033667`) se confirmó que el inmueble está situado en el malecón de Barranco, Lima Metropolitana — no en la provincia de Barranca. Como el anuncio ya había superado el filtro geográfico, sus coordenadas reales constituyen evidencia suficiente de que se trata de un error de tipeo del anunciante, no de un anuncio real de otra provincia. Se corrige con evidencia verificable: el conteo de Barranco pasa de 211 a **212** anuncios.

### 5.2 Agrupamiento de distritos con pocas observaciones

Los 19 distritos con menos de 20 anuncios en la muestra (*Punta Hermosa, San Juan de Lurigancho, Rímac, Santa Anita, San Juan de Miraflores, Magdalena Vieja, La Perla, Lurín, San Luis, Bellavista, Villa El Salvador, El Agustino, Carabayllo, Villa María del Triunfo, Ventanilla, Puente Piedra, Ancón, Pachacámac, Independencia*) se agrupan bajo la categoría `"Otros"` — **125 observaciones (4.00% del dataset limpio)**.

**Motivo:** sin este agrupamiento, la codificación one-hot genera columnas de 1 a 19 casos que el Random Forest puede usar para sobreajustar. Se verificó empíricamente: antes de este ajuste, `distrito_norm_Punta Hermosa` (con solo 19 filas) aparecía en el top 3 de variables más influyentes del Modelo #3 — un artefacto de sobreajuste sobre una categoría casi vacía, no un patrón de mercado real. Tras agrupar, el feature importance queda dominado por variables con soporte estadístico real.

---

## 6. EDA univariado y bivariado

**Efecto del filtro de outliers sobre la distribución de precio:** el filtrado redujo la asimetría (*skewness*) de `precio_soles` de **14.07 a 3.24**, estabilizando la distribución para el entrenamiento de modelos.

**Correlación con `precio_soles`:**

| Variable | Correlación (r) |
|---|:---:|
| `mantenimiento` | 0.79 |
| `area_total` | 0.77 |
| `banos` | 0.50 |
| `dormitorios` | 0.39 |
| `medios_banos` | 0.10 |
| `estacionamientos` | 0.09 |
| `antiguedad` | 0.08 |

`mantenimiento` presenta la correlación más fuerte, seguida de cerca por `area_total`. Existe correlación relevante entre `area_total` y `mantenimiento` (r=0.70) y entre `area_total` y `banos` (r=0.69), consistente con la estructura física y de costos de los departamentos — se documenta como riesgo de colinealidad a vigilar en modelos lineales (Ridge), aunque no afecta a los modelos de árboles utilizados en el Modelo #3.

---

## 7. Integración con el BCRP (contexto macroeconómico)

Se toma como referencia el trimestre más reciente disponible (**2026-T1**). El **83.7%** de los departamentos se enlaza directamente a su serie distrital específica (PER, precio de venta USD/m², alquiler mensual implícito), mientras que el **16.3%** restante (distritos sin serie propia en el BCRP) recibe el valor "Promedio general" metropolitano, marcado explícitamente con la variable indicadora `bcrp_es_promedio_general = 1`.

**Nota conceptual:** el cruce con el BCRP es, en su mayoría, integración de datos (no imputación) — se está agregando información real de otra fuente. La única excepción es el 16.3% que recibe el "Promedio general": ahí sí se sustituye un valor real distrital por uno agregado, razón por la cual se documenta y marca explícitamente con su propio flag.

---

## 8. Integración con Paraderos ATU (accesibilidad)

Mediante indexación espacial (`cKDTree`) sobre las coordenadas de los 3,233 paraderos oficiales, se determinó:

- Distancia mediana al paradero más cercano: **174.8 metros**.
- **71.6%** de los departamentos tiene al menos un paradero a menos de 300 metros.
- Promedio de **9.3 paraderos** en un radio caminable de 500 metros.
- Distancia mediana a la troncal del Metropolitano (BRT): **1,767.8 metros**.

Estas variables espaciales (`dist_paradero_min_m`, `paraderos_300m`, `paraderos_500m`, `paraderos_1000m`, `dist_troncal_brt_m`, `dist_corredor_m`) se incorporan directamente como features del Modelo #3, sin requerir un modelo de Machine Learning dedicado para el componente de accesibilidad (Modelo #2).

---

## 9. Limitaciones documentadas

1. Las 14 amenidades y el `piso` dependen de extracción por palabras clave sobre texto libre; su cobertura está limitada por los sinónimos contemplados en el diccionario `AMENITY_KEYWORDS`.
2. El nulo en `estacionamientos` es ambiguo (solo 10.75% confirmado por texto); no se trata como ausencia categórica de cochera.
3. El 16.3% de los departamentos usa el "Promedio general" del BCRP en lugar de una serie distrital propia, por lo que su contexto macroeconómico es menos preciso.
4. El filtro geográfico y de outliers descarta el 18.16% del dataset original; los rangos de precio y área se basan en percentiles observados y verificación manual de casos extremos, no en un criterio puramente estadístico.
5. El dataset de paraderos ATU tiene corte a mayo de 2021; se asume estabilidad razonable de la infraestructura de transporte troncal desde entonces.

---

*Datasets procesados exportados a `data/processed/`: `departamentos_procesados.csv`, `bcrp_procesado.csv`, `bcrp_serie_completa.csv`, `paraderos_procesado.csv`, `departamentos_sin_geo_para_clustering.csv`.*
