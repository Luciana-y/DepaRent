# Week 04 – Topic, Team and Dataset Selection

## Team Members

- Adrian Urbina Mendoza — Team Leader / Data Acquisition & Preprocessing
- Armando Martinez Palomino — NLP & Data Engineering
- Breysi Salazar Medina — Machine Learning Engineer
- Luciana Yangali Cáceres — Application / Visualization & Recommendation System
  
## Working Product Name

DepaRent – Plataforma inteligente para propietarios de departamentos en alquiler.

## Initial Problem / Opportunity

Los propietarios que desean alquilar un departamento deben determinar un precio de publicación y posicionar su inmueble frente a otras propiedades del mercado. Actualmente, esta decisión suele realizarse mediante comparación manual de anuncios similares, sin integrar de manera sistemática las características del inmueble, su ubicación y el comportamiento del mercado. El proyecto propone desarrollar un producto de datos web que utilice información inmobiliaria para caracterizar propiedades, estimar valores de alquiler y apoyar posteriormente decisiones relacionadas con la estrategia de publicación.

## Target Domain

Mercado inmobiliario de alquiler de departamentos en Lima Metropolitana y Callao.

## Target Users

El usuario principal será el propietario de uno o varios departamentos que desea publicarlos en alquiler y tomar decisiones basadas en datos sobre su posicionamiento en el mercado. Como usuario secundario, la plataforma podrá ser utilizada por personas que buscan departamentos disponibles para alquilar.

## Dataset

El producto requiere un **dataset inmobiliario** donde cada registro represente una propiedad. El dataset principal contiene anuncios inmobiliarios de departamentos en Lima Metropolitana y Callao. 

Incluye atributos relacionados con:
- precio;
- distrito;
- superficie;
- dormitorios;
- baños;
- cochera;
- características y amenidades del inmueble;
- descripción del anuncio;
- otras variables inmobiliarias disponibles.

El procedimiento de adquisición y las restricciones correspondientes se documentan en `acquisition.md`.

El dataset principal seleccionado para el proyecto es:

**Dataset:** depatamentos_lima.csv
**Fuente:** `https://www.adondevivir.com` y `https://urbania.pe`
**Formato:** CSV
**Cobertura geográfica:** Lima Metropolitana
