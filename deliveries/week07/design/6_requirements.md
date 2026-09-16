# Documentación de Diseño – DepaRent

## Propósito

Esta carpeta contiene los bocetos de baja fidelidad y los wireframes desarrollados para los principales requerimientos funcionales de **DepaRent – Plataforma inteligente para propietarios de departamentos en alquiler**.

Con el fin de evitar ambigüedades en la interpretación de los archivos, los requerimientos del proyecto se organizan en tres niveles:

1. **Requerimientos generales del producto:** dos flujos principales que organizan el propósito central de la plataforma.
2. **Requerimientos funcionales:** seis funcionalidades específicas derivadas de los dos requerimientos generales.
3. **Requerimientos no funcionales:** características de calidad, usabilidad, confiabilidad, reproducibilidad, rendimiento y restricciones técnicas documentadas de manera transversal.

Los seis bocetos y los seis wireframes almacenados en esta carpeta corresponden a los **seis requerimientos funcionales**, y no a seis requerimientos generales independientes.

---

# 1. Requerimientos Generales del Producto

## Requerimiento General 1 – Analizar y Valorar el Inmueble

El sistema deberá permitir al propietario obtener un análisis integral de su departamento en alquiler con el objetivo de comprender su posicionamiento competitivo, accesibilidad urbana, precio esperado de alquiler y contexto del mercado distrital.

Este requerimiento general agrupa cuatro requerimientos funcionales:

- RF1 – Perfil competitivo y propiedades comparables
- RF2 – Perfil de accesibilidad
- RF3 – Predicción del precio esperado de alquiler
- RF4 – Pronóstico de tendencia distrital de alquiler

---

## Requerimiento General 2 – Recomendar una Estrategia de Publicación

El sistema deberá utilizar los resultados analíticos del inmueble y el objetivo del propietario para generar escenarios de precio de publicación y permitir la simulación de determinadas mejoras antes de tomar una decisión.

Este requerimiento general agrupa dos requerimientos funcionales:

- RF5 – Precio de publicación recomendado
- RF6 – Simulador de mejoras del inmueble

---

# 2. Requerimientos Funcionales y Archivos de Diseño

| ID | Requerimiento funcional | Requerimiento general | Boceto | Wireframe |
|---|---|---|---|---|
| **RF1** | Perfil competitivo y propiedades comparables | Requerimiento General 1 | `sketch_requirement_1.png` | `wireframe_requirement_1.png` |
| **RF2** | Perfil de accesibilidad | Requerimiento General 1 | `sketch_requirement_2.png` | `wireframe_requirement_2.png` |
| **RF3** | Predicción del precio esperado de alquiler | Requerimiento General 1 | `sketch_requirement_3.png` | `wireframe_requirement_3.png` |
| **RF4** | Pronóstico de tendencia distrital de alquiler | Requerimiento General 1 | `sketch_requirement_4.png` | `wireframe_requirement_4.png` |
| **RF5** | Precio de publicación recomendado | Requerimiento General 2 | `sketch_requirement_5.png` | `wireframe_requirement_5.png` |
| **RF6** | Simulador de mejoras del inmueble | Requerimiento General 2 | `sketch_requirement_6.png` | `wireframe_requirement_6.png` |

---

# 3. Descripción de Cada Requerimiento Funcional

## RF1 – Perfil Competitivo y Propiedades Comparables

**Objetivo:**  
Identificar el segmento competitivo al que pertenece el inmueble y mostrar departamentos con características suficientemente similares para proporcionar un contexto de mercado relevante.

**Componente analítico:**  
Segmentación mediante K-Means y posterior recuperación de propiedades comparables mediante técnicas de similitud o vecinos cercanos.

**Archivos de diseño:**

- `sketch_requirement_1.png`
- `wireframe_requirement_1.png`

---

## RF2 – Perfil de Accesibilidad

**Objetivo:**  
Proporcionar al propietario información sobre la accesibilidad de su inmueble respecto a la infraestructura de transporte público disponible.

**Componente analítico:**  
Ingeniería de características geoespaciales utilizando información de paraderos de la ATU y las coordenadas del inmueble.

Entre los indicadores considerados se encuentran la distancia al paradero más cercano y la disponibilidad de paraderos dentro de determinados radios de distancia.

**Archivos de diseño:**

- `sketch_requirement_2.png`
- `wireframe_requirement_2.png`

---

## RF3 – Predicción del Precio Esperado de Alquiler

**Objetivo:**  
Estimar el precio mensual esperado de publicación del departamento a partir de sus características y del contexto disponible en los datos de mercado.

**Componente analítico:**  
Modelo supervisado de regresión utilizando el modelo seleccionado para la predicción de precios de alquiler.

El resultado corresponde a una estimación del precio de oferta esperado y no debe interpretarse como una tasación oficial ni como un precio final de transacción garantizado.

**Archivos de diseño:**

- `sketch_requirement_3.png`
- `wireframe_requirement_3.png`

---

## RF4 – Pronóstico de Tendencia Distrital de Alquiler

**Objetivo:**  
Proporcionar información contextual sobre la evolución reciente y la tendencia esperada del mercado inmobiliario del distrito cuando exista suficiente información histórica disponible.

**Componente analítico:**  
Análisis de series temporales trimestrales utilizando información del BCRP y modelos SARIMA.

**Archivos de diseño:**

- `sketch_requirement_4.png`
- `wireframe_requirement_4.png`

---

## RF5 – Precio de Publicación Recomendado

**Objetivo:**  
Generar diferentes escenarios de precio de publicación según el análisis del inmueble y la estrategia seleccionada por el propietario.

El sistema considera tres escenarios principales:

- Competitivo
- Equilibrado
- Renta superior

**Componente analítico:**  
Motor prescriptivo basado en reglas que combina información del precio esperado, propiedades comparables y tendencia distrital.

**Archivos de diseño:**

- `sketch_requirement_5.png`
- `wireframe_requirement_5.png`

---

## RF6 – Simulador de Mejoras del Inmueble

**Objetivo:**  
Permitir al propietario modificar virtualmente determinados atributos del inmueble y comparar la estimación del precio de alquiler antes y después del cambio simulado.

**Componente analítico:**  
Uso contrafactual del modelo de predicción de precios.

La diferencia entre la estimación original y la simulada representa una asociación estimada a partir de los datos disponibles y no debe interpretarse como un efecto causal garantizado.

**Archivos de diseño:**

- `sketch_requirement_6.png`
- `wireframe_requirement_6.png`

---

# 4. Relación Entre los Requerimientos

El flujo funcional de DepaRent puede resumirse de la siguiente manera:

**Registro de propiedad**

→ **RF1 Perfil competitivo y comparables**

→ **RF2 Perfil de accesibilidad**

→ **RF3 Precio esperado de alquiler**

→ **RF4 Tendencia distrital**

→ **Análisis integral del inmueble**

→ **RF5 Escenarios de precio de publicación**

→ **RF6 Simulación de mejoras**

→ **Decisión de publicación del propietario**

Los primeros cuatro requerimientos funcionales proporcionan la base analítica del **Requerimiento General 1**.

Los dos últimos requerimientos utilizan dichos resultados para apoyar el **Requerimiento General 2**.

---

# 5. Requerimientos No Funcionales

Los requerimientos no funcionales no cuentan con bocetos o wireframes independientes, ya que describen características transversales del sistema y no funcionalidades aisladas.

Entre ellos se consideran aspectos como:

- usabilidad;
- interpretabilidad de los resultados analíticos;
- reproducibilidad de los datos y modelos;
- confiabilidad;
- consistencia de las respuestas;
- mantenibilidad;
- privacidad y manejo adecuado de la información;
- transparencia sobre las limitaciones de los modelos.

La especificación completa de requerimientos funcionales y no funcionales se encuentra en el archivo `Requirements.pdf` o `Requirements.md` correspondiente a la entrega.

---

# 6. Convención de Nombres de Archivos

La numeración utilizada en esta carpeta corresponde a los requerimientos funcionales:

- `requirement_1` → RF1 – Perfil competitivo y propiedades comparables
- `requirement_2` → RF2 – Perfil de accesibilidad
- `requirement_3` → RF3 – Predicción del precio esperado de alquiler
- `requirement_4` → RF4 – Pronóstico de tendencia distrital
- `requirement_5` → RF5 – Precio de publicación recomendado
- `requirement_6` → RF6 – Simulador de mejoras del inmueble

Esta misma convención se utiliza tanto para los bocetos como para los wireframes.
