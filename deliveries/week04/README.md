# Week 04 – Topic, Team and Dataset Selection

## Team Members

- Adrian Urbina Mendoza — Team Leader / Data Acquisition & Preprocessing
- Armando Martinez Palomino — NLP & Data Engineering
- Breysi Salazar Medina — Machine Learning Engineer
- Luciana Yangali Cáceres — Application / Visualization & Recommendation System
  
## Working Product Name

DepaRent – Plataforma inteligente para propietarios de departamentos en alquiler.

## Initial Problem / Opportunity

Los propietarios que desean alquilar un departamento deben determinar un precio de publicacion y posicionar su inmueble frente a otras propiedades del mercado. Actualmente, esta decision suele realizarse mediante comparacion manual de anuncios similares, sin integrar de manera sistematica las caracteristicas del inmueble, su ubicacion y el comportamiento historico y macroeconomico del mercado. El proyecto propone desarrollar un producto de datos web que utilice informacion inmobiliaria de corte transversal y series temporales para caracterizar propiedades, estimar valores de alquiler por metro cuadrado y apoyar decisiones relacionadas con la estrategia de publicacion y fijacion de precios.

## Target Domain

Mercado inmobiliario de alquiler de departamentos en Lima Metropolitana.

## Target Users

El usuario principal sera el propietario de uno o varios departamentos que desea publicarlos en alquiler y tomar decisiones basadas en datos sobre su posicionamiento en el mercado. Como usuario secundario, la plataforma podra ser utilizada por inversionistas y personas que buscan departamentos disponibles para alquilar.

## Datasets

El producto integra dos fuentes de datos complementarias:

1. **Dataset Microinmobiliario (`departamentos_alquiler_lima.csv`)**:
   * **Fuente**: Adondevivir (`https://www.adondevivir.com`) y Urbania (`https://urbania.pe`).
   * **Contenido**: 3,801 anuncios individuales de departamentos en alquiler con 41 atributos (precios, metrajes, distribucion, coordenadas GPS y 14 amenidades binarias).
   * **Formato**: CSV.

2. **Dataset Macroinmobiliario Panel (`dataset_alquileres_trimestre_bcrp.csv`)**:
   * **Fuente**: API oficial del Banco Central de Reserva del Peru (BCRP).
   * **Contenido**: 663 observaciones trimestrales (T3-2013 a T1-2026) con series de PER, Precio de Venta en US$/m², Tipo de Cambio nominal y Alquiler Mensual estimado en S/ por m² para 13 series distritales.
   * **Formato**: CSV.

El procedimiento de adquisicion se documenta en `acquisition.md`, la evaluacion de calidad en `data_quality.md` y la definicion de atributos en `data_dictionary.csv`.
