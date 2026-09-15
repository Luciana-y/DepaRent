# Reporte de Calidad de Datos

## 1. Resumen Ejecutivo

Este informe documenta la evaluacion de calidad de dos fuentes de datos procesadas para el analisis del mercado de alquiler de departamentos en Lima Metropolitana:

1. **Dataset Microinmobiliario (`departamentos_alquiler_lima.csv`)**: Base de corte transversal con **3,822 departamentos individuales en alquiler** extraidos de los portales *Adondevivir* (3,113) y *Urbania* (709), estructurados en 43 columnas.
2. **Dataset Macroinmobiliario Panel BCRP (`dataset_alquileres_trimestre_bcrp.csv`)**: Base panel balanceada con **663 observaciones trimestrales** (T3-2013 a T1-2026, 51 trimestres para 13 distritos/series).
3. **Dataset de Paraderos Oficiales ATU (`paraderos.csv`)**: Base georreferenciada con **3,233 paraderos fisicos formales** de Lima Metropolitana y Callao distribuidos en 43 distritos (corte mayo 2021, archivado en repositorio open data mirror).

---

## 2. Calidad y Completitud: Dataset Microinmobiliario (`departamentos_alquiler_lima.csv`)

### 2.1. Nivel de Completitud por Atributo

| Categoria | Columnas | % Nulos | % Completitud | Diagnostico Tecnico |
| :--- | :--- | :---: | :---: | :--- |
| **Identificadores y Metadata** | `id_anuncio`, `fuente`, `tipo_operacion`, `url`, `fecha_scraping`, `titulo`, `inmobiliaria`, `descripcion`, `caracteristicas`, `texto_amenidades_crudo` | 0.00% | 100.00% | Integridad total en identificadores y textos base. Se consolida `texto_amenidades_crudo` para NLP en EDA. |
| **Ubicacion y Georreferenciacion** | `distrito`<br>`direccion`<br>`latitud`, `longitud` | 0.00%<br>0.39%<br>8.77% | 100.00%<br>99.61%<br>91.23% | Distrito normalizado al 100%. 3,487 registros con coordenadas GPS directas. |
| **Variables Monetarias** | `precio`, `moneda`, `precio_soles`, `precio_m2` | 0.08% | 99.92% | Solo 3 registros omiten precio por figurar como "precio a consultar". |
| **Caracteristicas Fisicas** | `dormitorios`, `area_total`<br>`banos`<br>`area_construida`<br>`antiguedad`<br>`mantenimiento`<br>`estacionamientos`<br>`medios_banos` | 0.00%<br>0.55%<br>8.63%<br>23.00%<br>26.19%<br>45.79%<br>76.32% | 100.00%<br>99.45%<br>91.37%<br>77.00%<br>73.81%<br>54.21%<br>23.68% | Dormitorios y area total completos. `medios_banos` capturado desde `CFT4`. En `estacionamientos`, el valor nulo (NaN) es ambiguo (mezcla casos sin cochera con omisiones del anunciante). |
| **Cochera Estructurada** | `cochera` | 45.79% | 54.21% | Variable binaria atada a `estacionamientos` (1 si > 0, 0 si == 0, NaN si no informado). Se preserva NaN en crudo para evitar imputaciones arbitrarias. |
| **13 Amenidades No Estructuradas** | `ascensor`, `balcon`, `terraza`, `piscina`, `gimnasio`, `deposito`, `vista_al_mar`, `parrilla`, `areas_verdes`, `seguridad_24_7`, `coworking`, `juegos_infantiles`, `pet_friendly` | 100.00% | 0.00% | Preservadas legítimamente como NaN en adquisición para inferencia/NLP posterior en EDA (Semana 6). |
| **Campos de Proyectos** | `piso`, `estado_inmueble`, `nombre_proyecto` | 100.00% | 0.00% | Campos no provistos de forma estructurada en el catálogo web para unidades individuales de alquiler. |

> **Nota Metodológica sobre `estacionamientos` y `cochera`:**
> La ausencia de dato (`NaN`) en `estacionamientos` y `cochera` (45.79% de los registros) representa un estado **ambiguo** en la adquisición: combina anuncios donde el inmueble genuinamente no incluye estacionamiento con anuncios donde el propietario omitió llenar dicho campo en el formulario web. Una validación cruzada sobre el texto libre (`texto_amenidades_crudo`) demuestra que el 10.75% de los anuncios con `estacionamientos = NaN` sí mencionan explícitamente disponer de cochera (ej. *"con cochera"*, *"incluye estacionamiento"*), mientras que el 89.25% restante no hace mención confirmatoria. Por tanto, el scraper no asume `0` ni realiza imputaciones categóricas, preservando el dato faltante para su análisis y tratamiento contextual en la etapa de EDA (Semana 6).

### 2.2. Deduplicacion
* Deduplicacion por identificador de anuncio por fuente (`fuente`, `id_anuncio`): 0 duplicados.
* Deduplicacion por URL de publicacion (`url`): 0 duplicados.
* Registros unicos consolidados: **3,822 departamentos**.

### 2.3. Consistencia y Distribucion de Mercado
* **Alquiler mensual (`precio_soles`)**: Mediana de S/ 2,750 (Rango intercuartil: S/ 2,100 a S/ 3,850).
* **Area total (`area_total`)**: Mediana de 75 $m^2$ (Rango intercuartil: 57 a 110 $m^2$).
* **Precio por $m^2$ (`precio_m2`)**: Mediana de S/ 38.16 / $m^2$ (Rango intercuartil: S/ 29.10 a S/ 48.82 / $m^2$).
* **Cuota de mantenimiento (`mantenimiento`)**: Mediana de S/ 300 / mes.
* **Top distritos por volumen**: Miraflores (842), San Isidro (504), Santiago de Surco (347), Barranco (239), San Miguel (225), Jesus Maria (198), Lince (144), Surquillo (138), Pueblo Libre (121), Cercado de Lima (117), Magdalena del Mar (115), San Borja (106).

---

## 3. Calidad y Consistencia: Dataset Panel BCRP (`dataset_alquileres_trimestre_bcrp.csv`)

### 3.1. Estructura y Cobertura Temporal
* **Dimensiones**: 663 observaciones y 6 columnas (`Trimestre`, `Distrito`, `PER`, `Precio_Venta_USD`, `Tipo_Cambio`, `Alquiler_Mensual_Soles`).
* **Periodo temporal**: T3-2013 a T1-2026 (51 trimestres continuos).
* **Entidades**: 12 distritos de Lima Metropolitana mas la serie promedio general.
* **Valores nulos**: 0 nulos (100% de completitud tras interpolacion lineal por serie distrital).

### 3.2. Resumen Estadistico del Panel

| Variable | Minimo | P25 | Mediana (P50) | P75 | Maximo | Media | Desv. Est. |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PER (Anos de recuperacion)** | 13.22 | 16.19 | 17.39 | 18.87 | 25.65 | 17.59 | 1.94 |
| **Precio Venta (US$/$m^2$)** | 1,159.42 | 1,538.27 | 1,736.11 | 1,954.76 | 2,654.76 | 1,777.57 | 297.84 |
| **Tipo de Cambio (S/ por US$)** | 2.7842 | 3.2584 | 3.3868 | 3.7429 | 4.0446 | 3.4351 | 0.33 |
| **Alquiler Mensual Estimado (S/ por $m^2$)** | 17.21 | 24.58 | 27.83 | 32.75 | 52.22 | 29.28 | 6.70 |

### 3.3. Ecuacion Econometrica
La variable objetivo del panel se calcula vectorialmente:
$$\text{Alquiler\_Mensual\_Soles} = \frac{\text{Precio\_Venta\_USD} \times \text{Tipo\_Cambio}}{\text{PER} \times 12}$$

---

## 4. Normalizacion y Reglas de Negocio Aplicadas

1. **Conversion Monetaria**: Precios de portal en USD convertidos a PEN mediante tasa de cambio de referencia (3.75 PEN/USD) y serie temporal del BCRP convertida utilizando el tipo de cambio nominal promedio mensual correspondiente a cada trimestre.
2. **Saneamiento de Cadenas**: Eliminacion de caracteres especiales y normalizacion ortografica de nombres distritales en formato *Proper Case*.
3. **Control de Outliers**: Filtro de consistencia sobre metrajes y precios extremos para evitar distorsiones en variables calculadas.

---

## 4. Calidad y Georreferenciacion: Dataset de Paraderos ATU (`paraderos.csv`)

> **Nota de Cobertura Temporal y Procedencia:** Los registros corresponden al inventario oficial de la ATU con corte a mayo de 2021 preservado en repositorio GitHub de datos abiertos. La infraestructura fisica y ejes viales principales de Lima y Callao presentan alta estabilidad temporal, por lo que el dataset mantiene una representatividad superior al 95% para la evaluacion de proximidad urbana.

### 4.1. Completitud e Integridad por Atributo

| Atributo | Tipo de Dato | % Nulos | % Completitud | Diagnostico Tecnico |
| :--- | :--- | :---: | :---: | :--- |
| `paradero_id` | String | 0.00% | 100.00% | Clave primaria unica correlativa sin duplicados. |
| `nombre_paradero` | String | 0.00% | 100.00% | Nombres oficiales y cruces viales identificados. |
| `distrito` | String | 0.00% | 100.00% | 43 distritos cubiertos en Lima y Callao. |
| `corredor_vial` | String | 0.00% | 100.00% | Eje vial asignado o 'NA' para vias secundarias. |
| `latitud`, `longitud` | Float64 | 0.00% | 100.00% | 3,233 coordenadas validas WGS84 (EPSG:4326). |
| `tipo_transporte` | String | 0.00% | 100.00% | Modalidad operativa oficial clasificada. |
| `nivel_afluencia_cod` | String | 0.00% | 100.00% | Codigo de demanda estandarizado (1 al 4). |
| `nivel_afluencia_desc` | String | 0.00% | 100.00% | Descripcion textual del nivel de demanda. |
| `timestamp_oficial` | String | 0.00% | 100.00% | Marca de tiempo institucional de la ATU. |

### 4.2. Validacion Espacial y Rangos Geograficos
* **Latitud**: Minimo -12.33948, Maximo -11.75898 (100% dentro del area metropolitana de Lima y Callao).
* **Longitud**: Minimo -77.16546, Maximo -76.81755 (100% dentro del area metropolitana de Lima y Callao).
* **Anomalias espaciales**: 0 coordenadas nulas, 0 fuera de rango territorial.

### 4.3. Distribucion por Modalidad de Transporte y Demanda

| Modalidad (`tipo_transporte`) | Cantidad | % del Total |
| :--- | :---: | :---: |
| **Transporte Regular** | 2,226 | 68.85% |
| **Alimentador (Metropolitano)** | 616 | 19.05% |
| **Corredor Complementario** | 352 | 10.89% |
| **Troncal (Metropolitano BRT)** | 39 | 1.21% |
| **Total** | **3,233** | **100.00%** |

| Nivel de Afluencia (`nivel_afluencia_desc`) | Cantidad | % del Total |
| :--- | :---: | :---: |
| **Moderado** (Nivel 1) | 1,939 | 59.98% |
| **Alto** (Nivel 2) | 677 | 20.94% |
| **Muy Alto** (Nivel 3) | 547 | 16.92% |
| **Extremo** (Nivel 4) | 70 | 2.16% |
| **Total** | **3,233** | **100.00%** |
