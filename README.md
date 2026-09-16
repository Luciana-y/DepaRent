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
        ├── PresentationWeek07.pdf
        ├── DataProductCanvas.pdf
        ├── Requirements.pdf
        ├── data_dictionary.csv
        │
        ├── architecture/
        │   ├── system_architecture.png
        │   └── product_workflow.png
        │
        ├── design/
        │   ├── README.md
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
        │   └── processed/
        │
        ├── code/
        │
        └── planning/
            ├── implementation_plan.md
            └── team_responsibilities.md
