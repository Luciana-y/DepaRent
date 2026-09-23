# DepaRent

## Plataforma inteligente para propietarios de departamentos en alquiler

**DepaRent** es un producto de datos diseñado para apoyar a propietarios de departamentos en alquiler en Lima Metropolitana y Callao en la toma de decisiones antes de publicar sus inmuebles.

La plataforma integra información inmobiliaria, territorial y de mercado para proporcionar analítica descriptiva, predictiva y prescriptiva.

DepaRent no busca realizar una tasación oficial ni garantizar un precio final de alquiler. Su propósito es proporcionar estimaciones, contexto de mercado, propiedades comparables y escenarios de publicación que reduzcan la incertidumbre del propietario.

---

# 1. Problema

Los propietarios suelen determinar el precio de alquiler de sus departamentos mediante comparaciones manuales con anuncios publicados en portales inmobiliarios.

Sin embargo, las propiedades seleccionadas no siempre son realmente comparables y existen diferencias importantes relacionadas con ubicación, área, características del inmueble, accesibilidad y contexto del mercado.

DepaRent busca reducir esta incertidumbre mediante la integración de múltiples fuentes de información y técnicas analíticas dentro de una única plataforma de apoyo a la decisión.

---

# 2. Usuarios Objetivo

## Usuario Principal

El usuario principal es el **propietario de uno o varios departamentos en alquiler** ubicados en Lima Metropolitana o Callao.

El propietario podrá:

- registrar y administrar propiedades;
- analizar su posicionamiento competitivo;
- identificar propiedades comparables;
- consultar indicadores de accesibilidad;
- obtener una estimación del precio esperado de alquiler;
- revisar la tendencia del mercado distrital;
- comparar estrategias de precio de publicación;
- simular determinadas mejoras del inmueble;
- preparar el inmueble para su publicación.

## Usuario Secundario

Los potenciales inquilinos podrán explorar las propiedades publicadas y consultar información relevante sin necesidad de registrarse durante la primera versión del producto.

---

# 3. Requerimientos Principales del Producto

DepaRent se organiza en torno a dos requerimientos generales.

## Requerimiento General 1 – Analizar y Valorar el Inmueble

El sistema proporciona un análisis integral compuesto por:

1. Perfil competitivo y propiedades comparables.
2. Perfil de accesibilidad.
3. Predicción del precio esperado de alquiler.
4. Pronóstico de tendencia distrital.

## Requerimiento General 2 – Recomendar una Estrategia de Publicación

A partir de los resultados del análisis anterior, la plataforma proporciona:

5. Escenarios de precio de publicación.
6. Simulación de mejoras del inmueble.

Estas seis funcionalidades corresponden a los principales requerimientos funcionales documentados en la especificación del proyecto.

---

# 4. Componentes Analíticos

| Componente | Método |
|---|---|
| Perfil competitivo | Clustering mediante K-Means |
| Propiedades comparables | Análisis de similitud / vecinos cercanos |
| Perfil de accesibilidad | Ingeniería de características geoespaciales con datos de ATU |
| Precio esperado de alquiler | Regresión con HistGradientBoosting |
| Tendencia distrital | Pronóstico de series temporales con SARIMA |
| Escenarios de publicación | Motor prescriptivo basado en reglas |
| Simulador de mejoras | Reutilización contrafactual del modelo de precio |

---

# 5. Fuentes de Datos

DepaRent integra actualmente tres fuentes principales de información.

## Dataset Inmobiliario

Anuncios de departamentos en alquiler obtenidos de:

- Adondevivir
- Urbania

El dataset original contiene aproximadamente **3,822 anuncios** y **43 variables**, incluyendo información sobre:

- precio;
- área;
- dormitorios;
- baños;
- estacionamientos;
- antigüedad;
- mantenimiento;
- distrito;
- coordenadas geográficas;
- amenidades;
- información textual del anuncio.

---

## Banco Central de Reserva del Perú – BCRP

Se utilizan series trimestrales de indicadores inmobiliarios distritales para proporcionar contexto histórico del mercado y apoyar el pronóstico de tendencias.

---

## Autoridad de Transporte Urbano – ATU

Se utiliza información georreferenciada de paraderos de transporte público para generar indicadores de accesibilidad asociados a cada inmueble.

---

# 6. Integrantes del Equipo y Responsabilidades

| Integrante | Rol principal | Responsabilidades |
|---|---|---|
| **Adrian Urbina Mendoza** | Líder de Equipo / Adquisición y Preprocesamiento de Datos | Coordinación general del proyecto, adquisición de datos, preprocesamiento, calidad de datos y apoyo en el análisis competitivo. |
| **Armando Martinez Palomino** | Ingeniería de Datos e Integración de Datos Externos | Integración de fuentes externas, preparación de datos de ATU y BCRP, ingeniería de características espaciales y temporales e integración técnica. |
| **Breysi Salazar Medina** | Ingeniera de Machine Learning | Clustering, predicción del precio de alquiler, forecasting, evaluación de modelos, motor de recomendación y simulador de mejoras. |
| **Luciana Yangali Cáceres** | Aplicación y Visualización | Desarrollo de la aplicación web, dashboards, visualización de resultados, flujo de usuario e integración de la interfaz. |

Todos los integrantes participan adicionalmente en:

- validación;
- pruebas;
- documentación;
- preparación de presentaciones;
- revisión del repositorio;
- integración final del producto.

La distribución detallada de responsabilidades se encuentra en:

`deliveries/week07/planning/team_responsibilities.md`

---

# 7. Estructura del Repositorio

```text
DepaRent/
│
├── README.md
│
└── deliveries/
    │
    ├── week04/
    │   ├── README.md
    │   ├── data/
    │   ├── data_dictionary.csv
    │   └── acquisition.md
    │
    ├── week05/
    │   ├── ProjectProposal.pdf
    │   ├── DataProductCanvas.pdf
    │   ├── Requirements.pdf
    │   └── PresentationWeek05.pdf
    │
    ├── week06/
    │   ├── DataAnalysis.md
    │   ├── ModelSelection.md
    │   ├── PresentationWeek06.pdf
    │   ├── data/
    │   │   └── processed/
    │   └── code/
    │
    └── week07/
        ├── Delivery1Report.pdf
        ├── Delivery1Report.docx
        ├── PresentationWeek07.pptx
        ├── DataProductCanvas.pdf
        ├── Requirements.pdf
        ├── data_dictionary.csv
        │
        ├── architecture/
        │   ├── product_workflow.png
        │   └── system_architecture.png
        │
        ├── design/
        │   ├── sketch_requirement_1.png
        │   ├── sketch_requirement_2.png
        │   ├── sketch_requirement_3.png
        │   ├── sketch_requirement_4.png
        │   ├── sketch_requirement_5.png
        │   ├── sketch_requirement_6.png
        │   ├── wireframe_requirement_1.png
        │   ├── wireframe_requirement_2.png
        │   ├── wireframe_requirement_3.png
        │   ├── wireframe_requirement_4.png
        │   ├── wireframe_requirement_5.png
        │   └── wireframe_requirement_6.png
        │
        ├── data/
        │   ├── bcrp_procesado.csv
        │   ├── bcrp_serie_completa.csv
        │   ├── departamentos_procesados.csv
        │   ├── departamentos_sin_geo_para_clustering.csv
        │   └── paraderos_procesado.csv
        │
        ├── code/
        │   └── EDA_week07.ipynb
        │
        └── planning/
            ├── Implementation_Plan.md
            └── team_responsibilities.md
```

---

# 8. Instrucciones de Ejecución

## Requisitos Previos

- **Python**: Se recomienda utilizar **Python 3.10** o superior (probado con Python 3.10 / 3.11).
- **Dependencias y librerías**: Actualmente el repositorio no cuenta con un archivo `requirements.txt` o `environment.yml` formalizado. A partir de los módulos importados en los notebooks de análisis y modelado (`deliveries/week06/code/EDA_week06_v5.ipynb` y `deliveries/week07/code/EDA_week07.ipynb`), se requiere la instalación de los siguientes paquetes:
  - `numpy`
  - `pandas`
  - `scipy`
  - `scikit-learn`
  - `statsmodels`
  - `matplotlib`
  - `seaborn`
  - `umap-learn`
  - `notebook` / `jupyter` (para la ejecución de los cuadernos de trabajo)

> [!TIP]
> Se sugiere crear a corto plazo un archivo `requirements.txt` o `environment.yml` en la raíz del repositorio para congelar las versiones de las librerías y garantizar reproducibilidad automatizada.

## Clonación del Repositorio y Preparación del Entorno

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/Luciana-y/DepaRent.git
   cd DepaRent
   ```

2. **Crear y activar un entorno virtual:**

   - En Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - En Linux / macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Instalar dependencias necesarias:**

   ```bash
   pip install numpy pandas scipy scikit-learn statsmodels matplotlib seaborn umap-learn notebook
   ```

## Ejecución del Pipeline de Datos, EDA y Modelado

El procesamiento de datos, análisis exploratorio y entrenamiento de los modelos analíticos preliminares están centralizados en cuadernos de Jupyter:

- **Pipeline y EDA de Semana 06:**
  ```text
  deliveries/week06/code/EDA_week06_v5.ipynb
  ```
- **Pipeline y EDA consolidado de Semana 07 (Delivery 1):**
  ```text
  deliveries/week07/code/EDA_week07.ipynb
  ```

Para ejecutarlos:

1. Iniciar Jupyter Notebook o JupyterLab:
   ```bash
   jupyter notebook
   ```
2. Abrir cualquiera de los notebooks mencionados (`deliveries/week06/code/EDA_week06_v5.ipynb` o `deliveries/week07/code/EDA_week07.ipynb`).
3. Ejecutar las celdas secuencialmente (*Run All*). Los notebooks están configurados para detectar automáticamente los datasets crudos ubicados en `deliveries/week04/data/`:
   - `departamentos_alquiler_lima.csv`
   - `dataset_alquileres_trimestre_bcrp.csv`
   - `paraderos.csv`

## Ubicación de Outputs y Artefactos

- **Datasets Procesados:**
  Al ejecutarse el pipeline en los notebooks, el código (`to_csv`) genera y escribe los archivos procesados en una subcarpeta relativa `processed/` en el directorio de trabajo del notebook en ejecución (por ejemplo, `deliveries/week06/code/processed/` o `deliveries/week07/code/processed/`).
  
  Por otro lado, los datasets procesados oficiales y versionados en el repositorio correspondientes a la Semana 07 se encuentran almacenados directamente en:
  `deliveries/week07/data/`

  Archivos generados:
  - `departamentos_procesados.csv`: dataset inmobiliario limpio con coordenadas e imputación básica.
  - `departamentos_sin_geo_para_clustering.csv`: versión estructurada para segmentación y clustering sin variables geoespaciales.
  - `paraderos_procesado.csv`: paraderos de transporte público de la ATU procesados para cálculo de accesibilidad.
  - `bcrp_procesado.csv`: corte más reciente de estadísticas distritales del BCRP.
  - `bcrp_serie_completa.csv`: serie histórica trimestral para pronóstico y análisis temporal.

- **Modelos Serializados:**
  Actualmente **no existen modelos serializados** (`.joblib` o `.pkl`) almacenados en el repositorio. La serialización y guardado de los artefactos entrenados (clustering K-Means y regresión HistGradientBoosting) está planificada como parte del prototipo funcional en la **Week 10**.

## Variables de Entorno y Credenciales

- **No se requieren variables de entorno ni credenciales externas** (API keys, tokens o contraseñas) para la ejecución actual. Todos los datos necesarios provienen de archivos locales contenidos dentro del repositorio.

---

# 9. Cronograma del Proyecto

| Semana | Prioridad | Trabajo principal | Resultado esperado |
|---|---|---|---|
| Week 7 | Alta | Consolidar definición integrada, arquitectura, requirements, datos y plan de implementación. | Delivery 1 completo y repositorio reorganizado. |
| Week 8 | Alta | Estabilizar pipeline de datos, esquemas y artefactos procesados; pruebas de reproducibilidad. | Pipeline reproducible y datasets versionados. |
| Week 9 | Alta | Validar estabilidad de K-Means k=4 e implementar segunda etapa de comparables (k-NN dentro de cluster + ubicación). | Perfil competitivo utilizable en producto. |
| Week 10 | Alta | Tuning y análisis de error del HistGradientBoosting; definición de contrato de inferencia. | Modelo de precio versionado y endpoint/prototipo de inferencia. |
| Week 11 | Media-Alta | Implementar/validar SARIMA temporal y consolidar módulo de accesibilidad. | Tendencia distrital y accesibilidad integrables. |
| Week 12 | Alta | Construir motor de escenarios de precio y simulador contrafactual con advertencias de uso. | Módulos prescriptivos funcionales. |
| Week 13 | Alta | Integrar frontend, backend, persistencia y modelos; flujo propietario de extremo a extremo. | Prototipo integrado. |
| Week 14 | Alta | Pruebas con usuarios, criterios de aceptación, QA, rendimiento, revisión de explicabilidad y limitaciones. | Versión candidata final con hallazgos de validación. |
| Week 15 | Alta | Evaluación final, documentación, limpieza de repositorio, presentación y entrega. | Prototipo final y Delivery 2. |

