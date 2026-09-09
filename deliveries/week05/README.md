# Week 05 – Project Proposal, Requirements and Data Product Definition

## Team Members

- Adrian Urbina Mendoza — Team Leader / Data Acquisition & Preprocessing
- Armando Martinez Palomino — Data Engineering & External Data Integration
- Breysi Salazar Medina — Machine Learning Engineer
- Luciana Yangali Cáceres — Application / Visualization

---

## Working Product Name

**DepaRent – Plataforma inteligente para propietarios de departamentos en alquiler**

---

## Project Overview

DepaRent es una plataforma web de apoyo a la decisión dirigida principalmente a propietarios que desean publicar uno o varios departamentos en alquiler en Lima Metropolitana y Callao.

El problema que aborda no se limita a publicar un anuncio. El propietario debe decidir contra qué inmuebles debería comparar su departamento, cuánto podría pedir por el alquiler, cómo se comporta el mercado de su distrito y qué estrategia de publicación resulta más adecuada.

Actualmente, estas decisiones suelen realizarse mediante comparaciones manuales entre anuncios que no necesariamente corresponden a propiedades equivalentes.

DepaRent busca reducir esta incertidumbre mediante la integración de datos inmobiliarios y fuentes oficiales de contexto territorial, utilizando técnicas descriptivas, predictivas y prescriptivas para transformar los datos en información útil para la toma de decisiones.

El sistema no pretende realizar una tasación oficial ni garantizar que una propiedad será alquilada a un determinado precio. Sus resultados serán presentados como estimaciones y escenarios de apoyo a la decisión.

---

## General Objective

Desarrollar una plataforma web de apoyo a la decisión para propietarios de departamentos en alquiler en Lima Metropolitana y Callao, que integre datos inmobiliarios y territoriales con técnicas descriptivas, predictivas y prescriptivas para analizar el posicionamiento del inmueble, estimar su precio esperado y generar escenarios que apoyen la definición de una estrategia de publicación.

---

## Target Domain

Mercado inmobiliario de departamentos en alquiler en **Lima Metropolitana y Callao**.

---

## Target Users

### Primary User

El usuario principal es el **propietario de uno o varios departamentos en alquiler**.

El propietario deberá registrarse e iniciar sesión para:

- registrar múltiples propiedades;
- consultar análisis individuales;
- obtener estimaciones de precio;
- revisar propiedades comparables;
- analizar el entorno del inmueble;
- evaluar escenarios de publicación;
- simular posibles mejoras;
- administrar sus publicaciones.

### Secondary User

La plataforma también contará con una interfaz pública para personas que buscan alquilar un departamento.

Estos usuarios podrán:

- explorar propiedades publicadas;
- consultar las características del inmueble;
- revisar información disponible;
- contactar al propietario.

En la primera versión no será obligatorio que el usuario que busca alquilar cree una cuenta.

### Other Stakeholders

- Agentes inmobiliarios e inmobiliarias.
- Equipo de desarrollo.
- Equipo de Machine Learning / Data.
- Administrador de la plataforma.
- Proveedores externos de datos: ATU, BCRP y SUSALUD / RENIPRESS.

---

## Main Requirements

Para organizar las funcionalidades principales del producto se definieron dos requerimientos generales.

### Requirement 1 – Analyze and Value the Property

El sistema deberá permitir al propietario registrar las características de su inmueble y obtener un análisis integral que identifique su segmento competitivo, propiedades comparables, nivel de accesibilidad, precio esperado de alquiler y tendencia inmobiliaria del distrito.

Este requerimiento integra cuatro funcionalidades:

1. **Competitive Property Profile**
   - Identifica el segmento al que pertenece el inmueble mediante clustering.
   - Recupera propiedades realmente comparables.

2. **Property Accessibility Profile**
   - Caracteriza la conectividad del inmueble utilizando información de transporte público de ATU.

3. **Expected Rental Price Prediction**
   - Estima el precio esperado de alquiler mediante modelos supervisados de regresión.

4. **District Rental Forecast**
   - Analiza series históricas del BCRP para estimar si el mercado del distrito presenta una tendencia creciente, estable o decreciente.

---

### Requirement 2 – Recommend a Publication Strategy

El sistema deberá utilizar los resultados del análisis del inmueble y los objetivos indicados por el propietario para generar escenarios de precio de publicación y permitir la simulación de características modificables antes de tomar una decisión.

Este requerimiento integra dos funcionalidades:

5. **Recommended Publication Price**
   - Combina precio esperado, propiedades comparables y tendencia del distrito.
   - Genera escenarios de posicionamiento:
     - Competitive
     - Balanced
     - Higher-rent

6. **Property Improvement Simulator**
   - Permite modificar virtualmente atributos seleccionados del inmueble.
   - Recalcula el precio esperado utilizando el mismo modelo predictivo.
   - Compara el escenario actual con el escenario simulado.

---

## Analytical Tasks

The analytical workflow follows three levels:

### Descriptive Analytics

**Property Segmentation and Comparables**

Clustering techniques such as K-Means and DBSCAN will be evaluated to identify groups of similar properties. Once the segment is identified, similarity measures or nearest-neighbor methods will be used to retrieve comparable apartments.

**Accessibility Characterization**

Geospatial information from ATU will be integrated with property locations to generate accessibility indicators related to public transportation.

### Predictive Analytics

**Rental Price Prediction**

A supervised regression model will estimate the expected rental price based on variables such as location, area, bedrooms, bathrooms, parking spaces, amenities and other available characteristics.

A linear regression model will be used as a baseline and will be compared with models such as:

- Random Forest
- Gradient Boosting
- XGBoost
- CatBoost

Performance will be evaluated using metrics such as MAE, RMSE, MAPE and R².

**District Rental Forecasting**

Historical BCRP real-estate series will be used to build a quarterly rental reference by district.

Forecasting approaches such as temporal baselines, ARIMA and regression models with lagged variables will be evaluated depending on the amount of historical information available.

### Prescriptive Analytics

**Publication Price Scenarios**

The expected rental price, comparable properties and district trend will be combined to generate different publication strategies:

- Competitive
- Balanced
- Higher-rent

**Property Improvement Simulation**

The rental-price model will be reused to compare the current property with a hypothetical scenario in which a modifiable characteristic is changed.

The resulting difference will be presented as an estimated association and not as a causal effect.

---

## Datasets and Data Sources

DepaRent integrates a primary real-estate dataset with external official data sources.

### 1. Main Real-Estate Dataset

**File:** `departamentos_alquiler_lima.csv`

**Sources:**
- Adondevivir
- Urbania

**Content:**

The dataset contains **3,801 rental apartment listings** with **41 attributes**, including variables related to:

- published rental price;
- district and location;
- area;
- bedrooms;
- bathrooms;
- parking spaces;
- geographic coordinates;
- property characteristics;
- amenities.

**Format:** CSV

The main limitation is that the target variable represents the **published asking price**, not necessarily the final rental price agreed in a contract.

---

### 2. Banco Central de Reserva del Perú – BCRP

**File:** `dataset_alquileres_trimestre_bcrp.csv`

**Source:** Official BCRP real-estate statistics.

**Content:**

The current dataset contains **663 quarterly observations**, covering the period from **Q3-2013 to Q1-2026**, with district-level series such as:

- Sale Price in US$/m²;
- Price-to-Rent Ratio (PER);
- nominal exchange rate;
- estimated monthly rental reference in S/ per m².

**Main use in DepaRent:**

District rental forecasting and market-trend analysis.

**Format:** CSV

---

### 3. Autoridad de Transporte Urbano para Lima y Callao – ATU

**Source:** Official ATU Open Data Portal.

**Main use in DepaRent:**

Generate spatial accessibility indicators related to public transportation, depending on the geographic coverage and variables available in the selected official datasets.

Potential derived variables include:

- proximity to public transport infrastructure;
- number of nearby transport options;
- relative accessibility indicators.

The final variables will depend on the georeferenced information available in the selected ATU files.

---

### 4. SUSALUD – RENIPRESS

**Source:** Registro Nacional de Instituciones Prestadoras de Servicios de Salud (RENIPRESS).

The official dataset contains information such as:

- district;
- UBIGEO;
- address;
- health-establishment category;
- longitude;
- latitude.

**Main use in DepaRent:**

Generate contextual variables such as proximity to health establishments or number of facilities located around the property.

These variables will only be incorporated into predictive models if they show sufficient coverage and predictive value during validation.

---

## Data Preparation

Before modeling, the datasets will go through a preprocessing pipeline that includes:

- duplicate detection;
- missing-value analysis;
- normalization of categorical variables;
- data-type validation;
- outlier analysis;
- geographic consistency checks;
- integration of external data sources;
- feature engineering.

The acquisition process is documented in `acquisition.md`, data-quality observations in `data_quality.md`, and attribute definitions in `data_dictionary.csv`.

---

## User Requirement Representations

The requirements were documented using four complementary representation methods:

1. **Use Cases**
2. **Wireframes**
3. **Storyboards**
4. **User Stories**

For the Week 05 presentation, the six analytical functionalities are grouped into two main user journeys:

### User Journey 1

**Understand and value the property**

The owner registers the property and obtains:

Property Profile  
→ Competitive Segment  
→ Comparable Properties  
→ Accessibility Profile  
→ Expected Rental Price  
→ District Market Trend

### User Journey 2

**Decide how to publish**

Using the previous analysis:

Expected Price + Comparables + District Trend  
→ Publication Price Scenarios  
→ Improvement Simulation  
→ Owner Decision  
→ Property Publication

---

## Initial Scope

The first version of DepaRent will focus exclusively on:

- rental apartments;
- Lima Metropolitana and Callao;
- owners as the primary user;
- management of multiple properties;
- descriptive, predictive and prescriptive analytics;
- a public inventory for potential tenants.

The following elements are outside the initial scope:

- purchase or sale of properties;
- official property appraisal;
- guaranteed rental prices;
- exact prediction of time-to-rent;
- models that depend on clicks or contact history generated by the platform.

---

## Week 05 Deliverables

The Week 05 delivery includes:

- `ProjectProposal.pdf`
- Editable source of the Project Proposal
- `DataProductCanvas.pdf`
- `Requirements.pdf`
- `PresentationWeek05.pptx` or PDF
- Updated `README.md`

---

## Repository Structure

```text
DepaRent/
│
├── README.md
│
└── deliveries/
    │
    ├── week04/
    │   ├── README.md
    │   ├── acquisition.md
    │   ├── data_quality.md
    │   ├── data_dictionary.csv
    │   └── data/
    │
    └── week05/
        ├── README.md
        ├── ProjectProposal.pdf
        ├── Requirements.pdf
        ├── DataProductCanvas.pdf
        └── PresentationWeek05.pptx
