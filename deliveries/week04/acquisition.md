# Protocolo y Metodologia de Adquisicion de Datos

## 1. Resumen y Fuentes de Informacion

Este documento describe los procesos de adquisicion y procesamiento de datos para la construccion de dos fuentes principales:

1. **Dataset Microinmobiliario de Alquileres (`departamentos_alquiler_lima.csv`)**: Recopila anuncios de departamentos en modalidad exclusiva de **Alquiler** en Lima Metropolitana.
   * **Adondevivir** (`https://www.adondevivir.com`)
   * **Urbania Peru** (`https://urbania.pe`)
   * Total consolidado: **3,801 departamentos unicos**.

2. **Dataset Macroinmobiliario Panel BCRP (`dataset_alquileres_trimestre_bcrp.csv`)**: Series temporales macroeconomicas e inmobiliarias trimestrales (T3-2013 a T1-2026) obtenidas de la API oficial del **Banco Central de Reserva del Peru (BCRP)**.
   * Total consolidado: **663 observaciones** (51 trimestres por 13 distritos/categorias).

---

## 2. Adquisicion de Datos de Portales Inmobiliarios

### 2.1. Arquitectura de Scraping
Ambos portales operan sobre la infraestructura de Navent, la cual incluye el estado inicial de la aplicacion en el HTML renderizado en servidor (*Server-Side Rendering*) dentro de la variable global `window.__PRELOADED_STATE__`.

```mermaid
flowchart TD
    A["Peticion HTTP GET (Catalogo de Alquiler)"] --> B["Respuesta HTML con __PRELOADED_STATE__"]
    B --> C["Extraccion de listStore.listPostings (JSON)"]
    C --> D["Mapeo de Campos Estructurados y Caracteristicas (CFT)"]
    D --> E["Normalizacion de Moneda (PEN/USD a Soles) y Unidades"]
    E --> F["Deduplicacion Multi-Nivel"]
    F --> G["Exportacion a data/departamentos_alquiler_lima.csv"]
```

### 2.2. Mapeo de Campos Estructurados (CFT)
La extraccion prioriza los campos nativos de la base de datos JSON del portal:
* `CFT100`: Area total ($m^2$) $\rightarrow$ `area_total`
* `CFT101`: Area construida ($m^2$) $\rightarrow$ `area_construida`
* `CFT2`: Dormitorios $\rightarrow$ `dormitorios`
* `CFT3`: Banos $\rightarrow$ `banos`
* `CFT7`: Estacionamientos $\rightarrow$ `estacionamientos`
* `CFT5`: Antiguedad en anos $\rightarrow$ `antiguedad`
* Precios, expensas de mantenimiento, ubicacion, coordenadas geograficas y 14 amenidades binarias.

### 2.3. Control de Tasa y Resiliencia
* Encabezados de navegacion estandarizados (*User-Agent*).
* Pausas de 1.0 a 1.3 segundos entre solicitudes.
* Reintentos automaticos con backoff exponencial ante respuestas HTTP no exitosas.

---

## 3. Adquisicion de Series Temporales desde la API del BCRP

### 3.1. Consulta a la API JSON
Se consume el endpoint oficial sin requerir web scraping:
`https://estadisticas.bcrp.gob.pe/estadisticas/series/api/[codigos_serie]/json/[periodo_inicio]/[periodo_fin]`

### 3.2. Series Consultadas (T3-2013 a T1-2026)
1. **Indicador PER (Precio de Venta / Alquiler Anual) — 13 series trimestrales**:
   * Barranco (`PD41940PQ`), Jesus Maria (`PD41941PQ`), La Molina (`PD41942PQ`), Lince (`PD41943PQ`), Magdalena (`PD41944PQ`), Miraflores (`PD41945PQ`), Pueblo Libre (`PD41946PQ`), San Borja (`PD41947PQ`), San Isidro (`PD41948PQ`), San Miguel (`PD41949PQ`), Surco (`PD41950PQ`), Surquillo (`PD41951PQ`), Promedio (`PD41952PQ`).
2. **Precio de Venta de Departamentos (US$ corrientes por $m^2$) — 13 series trimestrales**:
   * Barranco (`PD37957PQ`), Jesus Maria (`PD17464PQ`), La Molina (`PD17459PQ`), Lince (`PD17465PQ`), Magdalena (`PD17466PQ`), Miraflores (`PD17460PQ`), Pueblo Libre (`PD17467PQ`), San Borja (`PD17461PQ`), San Isidro (`PD17462PQ`), San Miguel (`PD17468PQ`), Surco (`PD17463PQ`), Surquillo (`PD37958PQ`), Promedio (`PD37944PQ`).
3. **Tipo de Cambio Nominal Promedio (`PN01246PM`) — Serie mensual**:
   * Descarga mensual agregada a nivel trimestral mediante promedio aritmetico de los meses de cada trimestre calendario.

### 3.3. Estandarizacion Temporal y Estructura Panel
* Conversion de identificadores temporales (`T3.13` $\rightarrow$ `2013-T3`).
* Cruce por llaves `(Trimestre, Distrito)` para conformar una estructura panel balanceada.
* Imputacion de valores faltantes puntuales mediante interpolacion lineal dentro de cada serie distrital.