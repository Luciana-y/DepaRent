# Reporte de Calidad de Datos

## 1. Resumen Ejecutivo

Este informe documenta la evaluacion de calidad de dos fuentes de datos procesadas para el analisis del mercado de alquiler de departamentos en Lima Metropolitana:

1. **Dataset Microinmobiliario (`departamentos_alquiler_lima.csv`)**: Base de corte transversal con **3,801 departamentos individuales en alquiler** extraidos de los portales *Adondevivir* (3,055) y *Urbania* (746).
2. **Dataset Macroinmobiliario Panel BCRP (`dataset_alquileres_trimestre_bcrp.csv`)**: Base panel balanceada con **663 observaciones trimestrales** (T3-2013 a T1-2026, 51 trimestres para 13 distritos/series).

---

## 2. Calidad y Completitud: Dataset Microinmobiliario (`departamentos_alquiler_lima.csv`)

### 2.1. Nivel de Completitud por Atributo

| Categoria | Columnas | % Nulos | % Completitud | Diagnostico Tecnico |
| :--- | :--- | :---: | :---: | :--- |
| **Identificadores y Metadata** | `id_anuncio`, `fuente`, `tipo_operacion`, `url`, `fecha_scraping`, `titulo`, `inmobiliaria`, `descripcion` | 0.00% | 100.00% | Integridad total en identificadores y textos base. |
| **Ubicacion y Georreferenciacion** | `distrito`<br>`direccion`<br>`latitud`, `longitud` | 0.00%<br>0.39%<br>8.73% | 100.00%<br>99.61%<br>91.27% | Distrito normalizado al 100%. 3,469 registros con coordenadas GPS directas. |
| **Variables Monetarias** | `precio`, `moneda`, `precio_soles`, `precio_m2` | 0.16% | 99.84% | Solo 6 registros omiten precio por figurar como "precio a consultar". |
| **Caracteristicas Fisicas** | `dormitorios`, `area_total`<br>`banos`<br>`area_construida`<br>`antiguedad`<br>`mantenimiento`<br>`estacionamientos` | 0.00%<br>0.45%<br>8.10%<br>22.97%<br>26.07%<br>44.70% | 100.00%<br>99.55%<br>91.90%<br>77.03%<br>73.93%<br>55.30% | Dormitorios y area total completos. Estacionamiento omitido cuando el departamento no incluye cochera. |
| **14 Amenidades Binarias** | `ascensor`, `balcon`, `terraza`, `piscina`, `gimnasio`, `cochera`, `deposito`, `vista_al_mar`, `parrilla`, `areas_verdes`, `seguridad_24_7`, `coworking`, `juegos_infantiles`, `pet_friendly` | 0.00% | 100.00% | Variables binarias (0 o 1). 1 indica presencia confirmada de la amenidad. |
| **Campos de Proyectos** | `piso`, `estado_inmueble`, `nombre_proyecto`, `caracteristicas` | 100.00% | 0.00% | Campos no provistos por el catalogo web para unidades individuales de alquiler. |

### 2.2. Deduplicacion
* Deduplicacion por identificador de anuncio por fuente (`fuente`, `id_anuncio`): 0 duplicados.
* Deduplicacion por URL de publicacion (`url`): 0 duplicados.
* Registros unicos consolidados: **3,801 departamentos**.

### 2.3. Consistencia y Distribucion de Mercado
* **Alquiler mensual (`precio_soles`)**: Mediana de S/ 2,750 (Rango intercuartil: S/ 2,100 a S/ 3,910).
* **Area total (`area_total`)**: Mediana de 75 $m^2$ (Rango intercuartil: 57 a 111 $m^2$).
* **Precio por $m^2$ (`precio_m2`)**: Mediana de S/ 38.46 / $m^2$ (Rango intercuartil: S/ 28.99 a S/ 48.57 / $m^2$).
* **Cuota de mantenimiento (`mantenimiento`)**: Mediana de S/ 300 / mes.
* **Top distritos por volumen**: Miraflores (825), San Isidro (513), Santiago de Surco (329), Barranco (249), San Miguel (225), Jesus Maria (202), Surquillo (145), Lince (134), Magdalena del Mar (118), Pueblo Libre (117).

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
