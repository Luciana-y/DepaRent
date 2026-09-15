# Semana 05 – Propuesta de Proyecto, Requisitos y Definición del Producto de Datos

## Miembros del Equipo

- Adrian Urbina Mendoza — Líder de Equipo / Adquisición y Preprocesamiento de Datos
- Armando Martinez Palomino — Ingeniería de Datos e Integración de Datos Externos
- Breysi Salazar Medina — Ingeniera de Machine Learning
- Luciana Yangali Cáceres — Aplicación / Visualización

---

## Nombre del Producto en Desarrollo

**DepaRent – Plataforma inteligente para propietarios de departamentos en alquiler**

---

## Descripción General del Proyecto

DepaRent es una plataforma web de apoyo a la decisión dirigida principalmente a propietarios que desean publicar uno o varios departamentos en alquiler en Lima Metropolitana y Callao.

El problema que aborda no se limita a publicar un anuncio. El propietario debe decidir contra qué inmuebles debería comparar su departamento, cuánto podría pedir por el alquiler, cómo se comporta el mercado de su distrito y qué estrategia de publicación resulta más adecuada.

Actualmente, estas decisiones suelen realizarse mediante comparaciones manuales entre anuncios que no necesariamente corresponden a propiedades equivalentes.

DepaRent busca reducir esta incertidumbre mediante la integración de datos inmobiliarios y fuentes oficiales de contexto territorial, utilizando técnicas descriptivas, predictivas y prescriptivas para transformar los datos en información útil para la toma de decisiones.

El sistema no pretende realizar una tasación oficial ni garantizar que una propiedad será alquilada a un determinado precio. Sus resultados serán presentados como estimaciones y escenarios de apoyo a la decisión.

---

## Objetivo General

Desarrollar una plataforma web de apoyo a la decisión para propietarios de departamentos en alquiler en Lima Metropolitana y Callao, que integre datos inmobiliarios y territoriales con técnicas descriptivas, predictivas y prescriptivas para analizar el posicionamiento del inmueble, estimar su precio esperado y generar escenarios que apoyen la definición de una estrategia de publicación.

---

## Dominio Objetivo

Mercado inmobiliario de departamentos en alquiler en **Lima Metropolitana y Callao**.

---

## Usuarios Objetivo

### Usuario Principal

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

### Usuario Secundario

La plataforma también contará con una interfaz pública para personas que buscan alquilar un departamento.

Estos usuarios podrán:

- explorar propiedades publicadas;
- consultar las características del inmueble;
- revisar información disponible;
- contactar al propietario.

En la primera versión no será obligatorio que el usuario que busca alquilar cree una cuenta.

### Otros Interesados (*Stakeholders*)

- Agentes inmobiliarios e inmobiliarias.
- Equipo de desarrollo.
- Equipo de Machine Learning / Datos.
- Administrador de la plataforma.
- Proveedores externos de datos: ATU y BCRP.

---

## Requerimientos Principales

Para organizar las funcionalidades principales del producto se definieron dos requerimientos generales.

### Requerimiento 1 – Analizar y Valorizar el Inmueble

El sistema deberá permitir al propietario registrar las características de su inmueble y obtener un análisis integral que identifique su segmento competitivo, propiedades comparables, nivel de accesibilidad, precio esperado de alquiler y tendencia inmobiliaria del distrito.

Este requerimiento integra cuatro funcionalidades:

1. **Perfil Competitivo de la Propiedad**
   - Identifica el segmento al que pertenece el inmueble mediante técnicas de *clustering*.
   - Recupera propiedades realmente comparables.

2. **Perfil de Accesibilidad de la Propiedad**
   - Caracteriza la conectividad del inmueble utilizando información de transporte público oficial de la ATU.

3. **Predicción del Precio Esperado de Alquiler**
   - Estima el precio esperado de alquiler mediante modelos supervisados de regresión.

4. **Pronóstico de Tendencia Distrital de Alquiler**
   - Analiza series históricas del BCRP para estimar si el mercado del distrito presenta una tendencia creciente, estable o decreciente.

---

### Requerimiento 2 – Recomendar una Estrategia de Publicación

El sistema deberá utilizar los resultados del análisis del inmueble y los objetivos indicados por el propietario para generar escenarios de precio de publicación y permitir la simulación de características modificables antes de tomar una decisión.

Este requerimiento integra dos funcionalidades:

5. **Precio de Publicación Recomendado**
   - Combina precio esperado, propiedades comparables y tendencia del distrito.
   - Genera escenarios de posicionamiento:
     - Competitivo (*Competitive*)
     - Equilibrado (*Balanced*)
     - Renta Superior (*Higher-rent*)

6. **Simulador de Mejoras del Inmueble**
   - Permite modificar virtualmente atributos seleccionados del inmueble.
   - Recalcula el precio esperado utilizando el mismo modelo predictivo.
   - Compara el escenario actual con el escenario simulado.

---

## Tareas Analíticas

El flujo de trabajo analítico sigue tres niveles metodológicos:

### 1. Analítica Descriptiva

**Segmentación de Propiedades y Comparables**

Se evaluarán técnicas de agrupamiento (*clustering*) como K-Means y DBSCAN para identificar grupos de propiedades homogéneas. Una vez identificado el segmento, se utilizarán medidas de similitud o métodos de vecinos más cercanos (*Nearest Neighbors*) para recuperar departamentos comparables.

**Caracterización de Accesibilidad Espacial**

La información geoespacial de paraderos de la ATU se integrará con la ubicación de los departamentos para generar indicadores de accesibilidad y cobertura de transporte público.

### 2. Analítica Predictiva

**Predicción del Precio de Alquiler**

Un modelo de regresión supervisada estimará el precio esperado de alquiler en función de variables como ubicación, área total, dormitorios, baños completos, medios baños, estacionamientos, antigüedad y variables derivadas de texto libre.

Se utilizará una regresión lineal hedónica como línea base (*baseline*) y se comparará contra modelos avanzados de ensamble:

- Random Forest
- Gradient Boosting
- XGBoost
- CatBoost
- LightGBM

El rendimiento se evaluará mediante métricas estándar de regresión: MAE, RMSE, MAPE y R².

**Pronóstico de Tendencia Distrital de Alquiler**

Se utilizarán las series temporales históricas del panel BCRP para construir una referencia trimestral de alquiler por distrito.

Se evaluarán enfoques de series temporales como líneas base temporales, modelos autorregresivos (ARIMA / SARIMA) y modelos de regresión con variables rezagadas.

### 3. Analítica Prescriptiva

**Escenarios de Precio de Publicación**

El precio esperado, las propiedades comparables y la tendencia distrital se combinarán vectorialmente para generar diferentes estrategias de fijación de precio de salida al mercado:

- **Estrategia Competitiva**: Orientada a minimizar el tiempo de vacancia.
- **Estrategia Equilibrada**: Punto medio óptimo entre renta y absorción de mercado.
- **Estrategia de Renta Superior**: Captura el percentil superior para inmuebles con atributos diferenciados.

**Simulación de Mejoras del Inmueble**

El modelo de predicción de precios se reutilizará para contrastar la propiedad actual frente a un escenario hipotético donde se modifica una característica (ej. añadir amoblado o remodelación).

La diferencia resultante se presentará estrictamente como una asociación estimada de mercado y no como un efecto causal garantizado.

---

## Datasets y Fuentes de Datos

DepaRent integra un dataset microinmobiliario primario con fuentes oficiales de datos públicos:

### 1. Dataset Microinmobiliario Principal

**Archivo:** `departamentos_alquiler_lima.csv`

**Fuentes:**
- Adondevivir (`https://www.adondevivir.com`)
- Urbania (`https://urbania.pe`)

**Contenido:**

El dataset contiene **3,822 anuncios de departamentos en alquiler** estructurados en **43 atributos**, incluyendo:

- precio de alquiler publicado y moneda;
- precio estandarizado en Soles (PEN) y precio por m²;
- distrito y dirección normalizada;
- área total y área construida saneadas;
- dormitorios, baños completos y medios baños (`CFT4`);
- estacionamientos y cochera;
- coordenadas GPS (latitud y longitud);
- características del portal y texto consolidado sin procesar (`texto_amenidades_crudo` para NLP);
- 13 variables de amenidades preservadas para extracción en EDA.

**Formato:** CSV (UTF-8 con BOM)

*Limitación:* La variable objetivo representa el **precio de oferta publicado (*asking price*)**, no necesariamente el precio final de cierre transaccional.

---

### 2. Banco Central de Reserva del Perú – BCRP

**Archivo:** `dataset_alquileres_trimestre_bcrp.csv`

**Fuente:** Estadísticas macroinmobiliarias oficiales de la API del BCRP.

**Contenido:**

El dataset contiene **663 observaciones trimestrales**, cubriendo el período de **T3-2013 a T1-2026** (51 trimestres) para 13 series distritales:

- Precio de Venta en US$/m²;
- Ratio Precio de Venta / Alquiler Anual (PER);
- Tipo de cambio nominal promedio;
- Alquiler mensual estimado de referencia en S/ por m².

**Uso principal en DepaRent:**

Pronóstico de tendencias inmobiliarias distritales y contextualización macro del mercado.

**Formato:** CSV

---

### 3. Autoridad de Transporte Urbano para Lima y Callao – ATU

**Archivo:** `paraderos.csv`

**Fuente:** Inventario institucional georreferenciado oficial de la ATU (preservado en repositorio de respaldo de datos abiertos).

**Contenido:**

Inventario georreferenciado de **3,233 paraderos formales** en 43 distritos de Lima Metropolitana y Callao con atributos de ubicación (coordenadas WGS84), corredor vial, modalidad de servicio y nivel de afluencia.

**Uso principal en DepaRent:**

Generación de indicadores de accesibilidad espacial y conectividad urbana hacia el transporte público.

**Formato:** CSV

---

## Preparación y Calidad de Datos

Antes de ingresar a los modelos analíticos, los datos atraviesan un pipeline riguroso de preprocesamiento:

- detección y eliminación de duplicados por identificador, URL y combinación de atributos;
- análisis de completitud y trazabilidad de valores faltantes (sin imputaciones prematuras);
- normalización ortográfica y estandarización categórica de nombres distritales;
- validación de consistencia de tipos de datos numéricos y coordenadas GPS;
- control y saneamiento de errores de captura en áreas y precios extremos;
- integración geoespacial con capas de transporte oficial;
- ingeniería de características y minería de texto sobre `texto_amenidades_crudo`.

El proceso de adquisición se detalla en `acquisition.md`, las métricas de calidad en `data_quality.md` y la especificación de atributos en `data_dictionary.csv`.

---

## Representación de Requisitos de Usuario

Los requisitos se documentaron mediante cuatro técnicas complementarias:

1. **Casos de Uso**
2. **Wireframes**
3. **Storyboards**
4. **Historias de Usuario**

Para la presentación de la Semana 05, las seis funcionalidades analíticas se agrupan en dos flujos principales de usuario (*User Journeys*):

### Flujo de Usuario 1: Entender y Valorizar la Propiedad

El propietario registra las características de su inmueble y obtiene:

Perfil del Inmueble  
→ Segmento Competitivo  
→ Propiedades Comparables  
→ Perfil de Accesibilidad Urbana  
→ Precio Esperado de Alquiler  
→ Tendencia del Mercado Distrital  

### Flujo de Usuario 2: Decidir la Estrategia de Publicación

Utilizando el diagnóstico previo:

Precio Esperado + Comparables + Tendencia Distrital  
→ Escenarios de Precio de Salida  
→ Simulación de Mejoras  
→ Decisión Informada del Propietario  
→ Publicación Optimizada del Inmueble  

---

## Alcance Inicial del Producto

La primera versión de DepaRent se focaliza exclusivamente en:

- departamentos en modalidad exclusiva de alquiler;
- ámbito geográfico de Lima Metropolitana y Callao;
- propietarios como usuario principal de la plataforma;
- gestión de múltiples propiedades por cuenta de usuario;
- analítica descriptiva, predictiva y prescriptiva integrada;
- catálogo público para consulta de inquilinos potenciales.

Quedan explícitamente fuera del alcance inicial:

- compra y venta de inmuebles comerciales o residenciales;
- emisión de tasaciones arancelarias u oficiales con fines legales/periciales;
- garantía contractual sobre el precio de alquiler final;
- predicción determinística del tiempo exacto de colocación (*time-to-rent*);
- modelos dependientes de históricos de clics o interacciones internas de la plataforma.

---

## Entregables de la Semana 05

El paquete de entrega de la Semana 05 incluye:

- `ProjectProposal.pdf`
- Fuente editable de la Propuesta de Proyecto
- `DataProductCanvas.pdf`
- `Requirements.pdf`
- `PresentationWeek05.pptx` / PDF
- `README.md` actualizado

---

## Estructura del Repositorio

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
```
