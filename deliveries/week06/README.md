# Semana 06 — Análisis Exploratorio de Datos (EDA) y Selección de Modelos

**Curso:** DS3022 — Desarrollo de Producto de Datos (2026)  
**Proyecto:** **DepaRent** — Plataforma inteligente para propietarios de departamentos en alquiler  

---

## Miembros del Equipo

- **Adrian Urbina Mendoza** — Líder de Equipo / Adquisición y Preprocesamiento de Datos
- **Armando Martinez Palomino** — Ingeniería de Datos e Integración de Datos Externos
- **Breysi Salazar Medina** — Ingeniera de Machine Learning
- **Luciana Yangali Cáceres** — Aplicación / Visualización

---

## Estructura del Entregable de la Semana 06

El directorio `deliveries/week06/` contiene todos los artefactos requeridos para la entrega:

```text
deliveries/week06/
├── README.md               # Instrucciones de reproducibilidad, resumen y estructura
├── DataAnalysis.md         # Documento de comprensión de datos, preprocesamiento, EDA, hallazgos y limitaciones
├── ModelSelection.md       # Documento de justificación técnica, alternativas baseline, métricas y suite de modelos
├── data_dictionary.csv     # Diccionario de datos estructurado y actualizado
├── data/
│   └── processed/          # Datasets transformados y procesados generados por el pipeline
│       ├── departamentos_procesados.csv
│       ├── departamentos_sin_geo_para_clustering.csv
│       ├── bcrp_procesado.csv
│       ├── bcrp_serie_completa.csv
│       └── paraderos_procesado.csv
└── code/
    └── EDA_week06_v5.ipynb # Notebook ejecutable con el flujo completo de EDA, ingeniería de features y benchmark
```

---

## Mapa de Entregables

| Entregable | Archivo | Descripción |
| :--- | :--- | :--- |
| **Análisis de Datos** | [`DataAnalysis.md`](DataAnalysis.md) | Detalla la estructura y calidad de los datos, decisiones de preprocesamiento, diagnóstico de nulos, reducción de asimetría, correlaciones, integración macroeconómica BCRP, accesibilidad ATU y limitaciones. |
| **Selección de Modelos** | [`ModelSelection.md`](ModelSelection.md) | Justifica empíricamente los 6 componentes analíticos de DepaRent (Clustering K-Means $k=2$, Accesibilidad `cKDTree`, Regresión HistGradientBoosting, Forecasting SARIMA, Motor de Reglas y Simulador de Mejoras). |
| **Diccionario de Datos** | [`data_dictionary.csv`](data_dictionary.csv) | Catálogo completo con descripción, tipo de dato, formato, valores posibles y tratamiento de nulos para todas las variables crudas y derivadas. |
| **Datos Procesados** | [`data/processed/`](data/processed/) | Archivos CSV limpios y estandarizados resultantes del pipeline de ingeniería de características. |
| **Código y Pipeline** | [`code/EDA_week06_v5.ipynb`](code/EDA_week06_v5.ipynb) | Notebook integral con todas las celdas ejecutadas, gráficos generados y validación sin data leakage. |

---

## Resumen del Diccionario de Datos

El catálogo actualizado ([`data_dictionary.csv`](data_dictionary.csv)) documenta las variables correspondientes a las tres fuentes de datos:

1. **Catálogo Inmobiliario Scraping (3,822 registros crudos $\rightarrow$ 3,128 en `df_clean`):**
   - Atributos físicos: `area_total`, `area_construida`, `dormitorios`, `banos`, `medios_banos`, `estacionamientos`, `antiguedad`, `piso`, `mantenimiento`.
   - Atributos geográficos y de ubicación: `distrito`, `distrito_norm`, `direccion`, `latitud`, `longitud`.
   - Variables de amenidades extraídas (14 binarias): `ascensor`, `balcon`, `terraza`, `piscina`, `gimnasio`, `cochera`, `deposito`, `vista_al_mar`, `parrilla`, `areas_verdes`, `seguridad_24_7`, `coworking`, `juegos_infantiles`, `pet_friendly`.
   - Missingness flags: `estacionamientos_imputado`, `mantenimiento_imputado`, `antiguedad_imputado`, `area_construida_imputado`, `banos_imputado`.
2. **Series Macroeconómicas BCRP (663 registros trimestrales, 2004–2026):**
   - Variables: `Trimestre`, `Distrito`, `PER`, `Precio_Venta_USD`, `Tipo_Cambio`, `Alquiler_Mensual_Soles`, `bcrp_es_promedio_general`.
3. **Red de Paraderos ATU (3,233 paraderos de transporte metropolitano):**
   - Variables: `paradero_id`, `nombre_paradero`, `distrito`, `corredor_vial`, `latitud`, `longitud`, `tipo_transporte`, `nivel_afluencia_cod`.
   - Features espaciales calculadas: `dist_paradero_min_m`, `paraderos_300m`, `paraderos_500m`, `paraderos_1000m`, `dist_troncal_brt_m`.

---

## Instrucciones de Reproducibilidad

### 1. Requisitos del Entorno

- **Python:** 3.10, 3.11, 3.12 o 3.13.
- **Librerías principales requeridas:**
  ```bash
  pip install numpy pandas scipy scikit-learn statsmodels matplotlib seaborn jupyter nbformat nbclient
  ```

### 2. Fuentes de Datos Crudos Requeridas

El pipeline consume los datos crudos ubicados en `deliveries/week04/data/`:
- `departamentos_alquiler_lima.csv` (3,822 filas)
- `dataset_alquileres_trimestre_bcrp.csv` (663 filas)
- `paraderos.csv` (3,233 filas)

### 3. Ejecución del Pipeline (Notebook)

El notebook puede ejecutarse tanto en entorno local como en Google Colab:

#### Opción A: Ejecución Local
```bash
cd deliveries/week06/code
jupyter notebook EDA_week06_v5.ipynb
```
O ejecutando el notebook mediante `nbclient` / `jupyter execute`:
```bash
python -m jupyter nbconvert --to notebook --execute EDA_week06_v5.ipynb --inplace
```

#### Opción B: Ejecución en Google Colab
1. Cargar el notebook `deliveries/week06/code/EDA_week06_v5.ipynb` en Google Colab.
2. Al ejecutar la celda 4, cargar los 3 archivos CSV crudos (`departamentos_alquiler_lima.csv`, `dataset_alquileres_trimestre_bcrp.csv`, `paraderos.csv`).
3. Ejecutar todas las celdas en orden secuencial (`Runtime -> Run all`).

### 4. Generación de Artefactos Procesados

Al completar la ejecución de la Sección 9 del notebook, se exportan automáticamente los datasets depurados a la carpeta `deliveries/week06/data/processed/`:
- `departamentos_procesados.csv`: Catálogo depurado con 3,128 filas, variables extraídas y métricas de accesibilidad.
- `departamentos_sin_geo_para_clustering.csv`: Catálogo para clustering (3,610 filas) preservando anuncios sin geolocalización.
- `bcrp_procesado.csv`: Snapshot del trimestre más reciente del BCRP (2026-T1) con indicador de promedio general.
- `bcrp_serie_completa.csv`: Serie temporal completa normalizada del BCRP para proyecciones SARIMA.
- `paraderos_procesado.csv`: Inventario depurado de paraderos de la ATU en Lima Metropolitana y Callao.
