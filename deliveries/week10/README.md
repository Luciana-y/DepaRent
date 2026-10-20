# Semana 10 — Prototipo funcional descriptivo (DepaRent)

## 1. Objetivo del prototipo

El prototipo está orientado al **propietario del inmueble**; la experiencia del usuario que busca alquilar no forma parte de Week 10.

Demostrar un flujo web funcional y reproducible en el que un propietario ingresa las características de su departamento y recibe un **análisis descriptivo**: a qué segmento del mercado de anuncios se parece, cuáles son los anuncios más similares y qué accesibilidad tiene al transporte público según la ATU.

## 2. Funcionalidades implementadas

| Requerimiento | Funcionalidad | Implementación |
|---|---|---|
| RF1 | Perfil competitivo | K-Means (k=3) sobre 18 características sin precio (`code/src/clustering.py`), con estadísticas reales del segmento y comparación del inmueble frente a su segmento |
| RF1 | Propiedades comparables (en la interfaz: "Comparables de mercado") | 5 anuncios reales más similares del mismo perfil, con prioridad al mismo distrito, más un resumen descriptivo de sus precios publicados (`code/src/comparables.py`); sin enlaces externos en la interfaz |
| RF2 | Perfil de accesibilidad | Indicadores ATU con `cKDTree` (`code/src/accessibility.py`) |
| — | Dos formas de análisis | Ingreso manual de una propiedad nueva, o carga de un **caso real del dataset** (`GET /api/example-properties`, `code/src/examples.py`) |
| — | Interfaz web | Flask + HTML/CSS/JS locales (`code/app.py`, `code/templates/`, `code/static/`) |

### Procedencia de los datos

- **Base inmobiliaria:** anuncios de departamentos en alquiler obtenidos por scraping de Adondevivir y Urbania. Fueron 3,822 anuncios originales (`deliveries/week04/`), capturados el 2026-09-14 según la columna `fecha_scraping`. Tras el procesamiento de Week 7 quedan **3,128 anuncios** (`deliveries/week07/data/departamentos_procesados.csv`).
- **Uso en el prototipo:** los perfiles se construyen sobre esos 3,128 anuncios, y los comparables y los casos de demostración son observaciones reales de ese archivo.
- **Precios:** son precios publicados de oferta (asking prices), no precios finales de transacción.
- **Accesibilidad:** proviene de una fuente externa georreferenciada, el inventario de 3,233 paraderos de la ATU (corte 2021-05-24).
- **Alcance:** ninguna funcionalidad predictiva o prescriptiva forma parte de Week 10.

## 3. Fuera del alcance de Week 10

No están implementados ni simulados: predicción de precio (HistGradientBoosting), BCRP como funcionalidad, tendencia distrital (SARIMA), recomendación de precio, escenarios de publicación, simulador de mejoras, login, base de datos de usuarios, publicación de inmuebles y mensajería.

El estimador anterior por mediana distrital (`code/inference.py`, endpoint `/predict`) se **eliminó**. Devolvía la mediana global cuando el distrito era desconocido y no correspondía a ningún componente validado. Su versión anterior queda en el historial de git.

## 4. Estructura

```text
deliveries/week10/
├── README.md                    # este archivo
├── PrototypeReport.md           # reporte del prototipo
├── DESCRIPTIVE_COMPONENTS.md    # metodología de RF1 y RF2
├── code/
│   ├── app.py                   # Flask: GET /, GET /health, POST /analyze
│   ├── config.py                # rutas (independientes del directorio de ejecución)
│   ├── requirements.txt         # dependencias con versiones fijadas
│   ├── src/                     # input_validation, clustering, comparables, accessibility, examples, descriptive_service
│   ├── scripts/train_clustering.py
│   ├── templates/index.html
│   ├── static/css/styles.css, static/js/app.js
│   └── tests/                   # pytest (componentes + Flask)
├── models/                      # clustering_pipeline.joblib, clustering_metadata.json, cluster_names.json, metadata.md
├── data/                        # sin archivos nuevos: se usan los procesados de ../week07/data/
├── screenshots/
└── deployed_url.txt
```

## 5. Requisitos

- Python 3.10 o superior. Los artefactos se generaron y probaron con **Python 3.13.2**.
- Dependencias con versiones exactas en `code/requirements.txt`: numpy 2.2.6, pandas 2.3.3, scipy 1.15.3, scikit-learn 1.7.2, joblib 1.6.0, Flask 3.1.3 y pytest 8.4.2. El modelo serializado requiere esa versión de scikit-learn.
- Datos: `deliveries/week07/data/departamentos_procesados.csv` y `paraderos_procesado.csv` (incluidos en el repositorio).
- No se requieren variables de entorno ni credenciales.

## 6–8. Entorno, instalación y ejecución

Desde la raíz de un clon limpio:

```bash
git clone https://github.com/Luciana-y/DepaRent.git
cd DepaRent
python -m venv .venv
# Windows (PowerShell):  .\.venv\Scripts\Activate.ps1
# Linux / macOS:         source .venv/bin/activate
pip install -r deliveries/week10/code/requirements.txt
python deliveries/week10/code/app.py
```

## 9. URL local

Abrir **http://127.0.0.1:5000**. Para verificar que la aplicación está activa: http://127.0.0.1:5000/health → `{"status": "ok"}`.

La sección **Casos reales del dataset** carga desde `GET /api/example-properties` tres anuncios reales de `departamentos_procesados.csv`, uno por cluster. Se eligen con una regla determinista: el anuncio con datos completos más cercano al centroide. Solo rellenan el formulario con los valores del CSV, incluidas sus coordenadas reales. Al pulsar **Analizar inmueble**, el backend ejecuta el flujo completo, verifica que los valores coincidan con el anuncio de origen y lo excluye de sus propios comparables. Si se edita cualquier campo, el análisis pasa a ser un ingreso manual.

El modo debug de Flask está desactivado por defecto. Para desarrollo: `DEPARENT_DEBUG=1 python deliveries/week10/code/app.py` (PowerShell: `$env:DEPARENT_DEBUG="1"`).

## 10. Tests

```bash
cd deliveries/week10/code
python -m pytest tests
```

Reentrenar el clustering (no es necesario para ejecutar la aplicación):

```bash
python deliveries/week10/code/scripts/train_clustering.py          # solo evalúa k=2..6
python deliveries/week10/code/scripts/train_clustering.py --k 3    # reentrena y guarda en models/
```

## 11. Flujo

Formulario → `POST /analyze` (JSON) → `analyze_descriptive()`:

1. validación de la entrada (si hay errores responde HTTP 400 con `{"error": "validation_error", "details": [...]}`);
2. normalización del distrito e imputación con parámetros de entrenamiento;
3. perfil competitivo y posición del inmueble frente a su segmento;
4. 5 comparables y resumen de sus precios publicados;
5. accesibilidad ATU.

La respuesta incluye además `input_source` (manual o caso real, con su `id_anuncio`) y `meta`: alcance "descriptive", número de anuncios de referencia, portales y fecha de captura.

La interfaz muestra los tres bloques y las advertencias de imputación o de fallback de comparables.

Endpoints:
- `GET /` interfaz;
- `GET /health`;
- `GET /api/example-properties` casos reales;
- `POST /analyze` análisis.

## 12. Limitaciones conocidas

- Datos de anuncios (precios de oferta, no de cierre), en una única captura (14-sep-2026). Las publicaciones originales de los comparables pueden haber finalizado después.
- Inventario ATU de mayo de 2021.
- Los perfiles son una segmentación descriptiva exploratoria de estructura débil (silhouette 0.1676), no grupos naturales del mercado.
- La similitud usa 18 dimensiones, 13 de ellas amenidades binarias, que pueden pesar mucho en la selección de comparables.
- Las amenidades provienen de palabras clave en el texto de los anuncios.
- Solo se aceptan los 40 distritos presentes en los datos. Las coordenadas se ingresan manualmente (temporal) y no se verifica que correspondan al distrito.
- Sin predicción de precio, forecasting ni recomendación en Week 10.
- Servidor de desarrollo de Flask; el despliegue está pendiente (`deployed_url.txt`).

Detalle completo en `DESCRIPTIVE_COMPONENTS.md` y `PrototypeReport.md`.
