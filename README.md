# DepaRent

**Plataforma de apoyo a la decisión para alquilar departamentos en Lima Metropolitana y Callao.**
Ayuda al **propietario** a decidir a cuánto publicar su departamento y al **inquilino** a encontrar uno a su medida.

| | |
|---|---|
| **App desplegada** | https://deparent.onrender.com (plan gratuito: la primera visita tarda 30–60 s en despertar) |
| **Repositorio** | https://github.com/Luciana-y/DepaRent |
| **Guía para el profesor** | [`README_PROFESOR.md`](README_PROFESOR.md) |
| **Estado del proyecto (documento breve)** | [`deliveries/week15/EstadoProyecto.md`](deliveries/week15/EstadoProyecto.md) |
| **Curso** | DS3022 Desarrollo de Producto de Datos · UTEC · 2026-2 |
| **Equipo** | Adrian Urbina Mendoza · Armando Martinez Palomino · Breysi Salazar Medina · Luciana Yangali Cáceres |

DepaRent no es una tasación oficial: da un precio esperado con su rango, anuncios comparables, contexto del
distrito y escenarios de publicación para reducir la incertidumbre.

---

## 1. Guía para el profesor

Lo que pidió el profesor para la revisión (código, base de datos, notebooks, modelo, interfaz, documentos,
instrucciones y enlaces), con la ubicación de cada cosa, está en **[`README_PROFESOR.md`](README_PROFESOR.md)**.
El documento breve del estado del proyecto está en [`deliveries/week15/EstadoProyecto.md`](deliveries/week15/EstadoProyecto.md).

---

## 2. Qué hace el producto

| Recorrido | Qué hace |
|---|---|
| **Propietario** | Crea cuenta, registra sus departamentos (con ubicación en el mapa) y recibe el análisis completo; publica al precio que elija y ve a los interesados |
| **Inquilino** | Busca con filtros (distrito, presupuesto, dormitorios, amenidades, cercanía a paraderos) sobre ~3,000 anuncios reales; ve si cada precio está por debajo, en línea o por encima del estimado; o responde un cuestionario y recibe recomendaciones personalizadas |
| **Prueba rápida** | El análisis completo sin crear cuenta (`#/probar`) |
| **Analista** | Panel de KPIs (uso, modelo, datos y recomendador), solo para correos autorizados |

### Componentes analíticos

| # | Componente | Método | Archivo (`deliveries/week10/code/`) |
|:-:|---|---|---|
| 1 | Perfil competitivo y comparables | K-Means (k=4, sin precio) + vecinos cercanos | `perfil_competitivo.py` |
| 2 | Accesibilidad a transporte | Paraderos ATU con `cKDTree` | `accesibilidad.py` |
| 3 | Precio esperado y rango | HistGradientBoosting + rango calibrado al 90% | `modelo.py` |
| 4 | Tendencia distrital | SARIMA sobre series trimestrales del BCRP | `tendencia.py` |
| 5 | Escenarios de precio de publicación | Reglas sobre 1 + 3 + 4 | `escenarios_precio.py` |
| 6 | Simulador de mejoras | Uso contrafactual del modelo 3 | `escenarios.py`, `laboratorio_area.py` |
| 7 | Recomendador para inquilinos | Puntaje por contenido según el perfil del hogar | `recomendador.py` |

### Fuentes de datos
- **Anuncios** de Adondevivir y Urbania: captura base del 14-sep-2026 (3,128 anuncios válidos) + capturas diarias (`scraper/`).
- **BCRP**: series trimestrales de precios inmobiliarios por distrito (tendencia).
- **ATU**: paraderos de transporte público georreferenciados (accesibilidad).

---

## 3. Estructura del repositorio

```text
DepaRent/
├── README.md                      ← este archivo
├── requirements.txt               dependencias de los notebooks (semanas 6–7)
├── render.yaml                    despliegue en Render
├── .github/workflows/             actualización diaria del mercado (GitHub Actions)
├── scraper/                       descarga diaria de anuncios (Adondevivir, Urbania)
└── deliveries/
    ├── week04/   adquisición de datos: datos crudos, diccionario, calidad de datos
    ├── week05/   propuesta, Data Product Canvas, requisitos, presentación
    ├── week06/   análisis exploratorio, selección de modelos, notebook EDA, presentación
    ├── week07/   Entrega 1: informe, arquitectura, bocetos/wireframes, datos procesados, notebook, plan
    ├── week08/   estado del proyecto para revisión del profesor, presentación
    ├── week10/   PROTOTIPO: código (API + modelos), frontend, modelos .joblib, datos, resultados, capturas
    ├── week12/   evaluación, casos de estudio, guion de pruebas con usuarios, plan final
    └── week15/   Entrega final: informe, requisitos, contribución, reflexión, diagramas, índices
```

### Documentos y presentaciones por semana

| Semana | Documentos | Presentación |
|---|---|---|
| 04 | `README.md`, `acquisition.md`, `data_quality.md`, `data_dictionary.csv`, `DepaRent.pdf` | — |
| 05 | `ProjectProposal.pdf/.docx`, `DataProductCanvas.pdf`, `Requirements.pdf` | `PresentationWeek05.pdf` |
| 06 | `DataAnalysis.md`, `ModelSelection.md` | `PresentationWeek06.pdf` |
| 07 | `Delivery1Report.pdf/.docx`, `Requirements.pdf`, `DataProductCanvas.pdf`, `architecture/`, `design/`, `planning/` | `PresentationWeek07.pptx` |
| 08 | `README.md` (estado para el profesor) | `PresentationWeek08.pptx/.pdf` |
| 10 | `PrototypeReport.md`, `PRODUCT.md`, `DESIGN.md`, `models/metadata.md`, `deployed_url.txt` | `PresentationWeek10.pptx/.pdf` |
| 12 | `EvaluationReport.md`, `GuionPruebasUsuarios.md`, `PlanFinal.md`, `architecture/` | — |
| 15 | `EstadoProyecto.md`, `FinalReport.md` (en redacción), `Requirements.md`, `ContributionStatement.md`, `Reflection.md`, `architecture/` | `presentation/` (pendiente) |

> El código del producto se quedó en `deliveries/week10/` porque Render despliega desde esas rutas; las
> mejoras de las semanas 12 y 15 se hicieron sobre esa misma carpeta.

---

## 4. Instalación y ejecución

### Requisitos
- **Python 3.12 o 3.13** y conexión a internet (instalar dependencias y cargar el mapa de OpenStreetMap).
- Git.

### App web (API + interfaz) — Windows PowerShell, desde la raíz del repo

```powershell
git clone https://github.com/Luciana-y/DepaRent.git
cd DepaRent
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r deliveries/week10/code/requirements.txt
cd deliveries/week10/code
..\..\..\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Abrir **http://127.0.0.1:8000**. Documentación de la API: http://127.0.0.1:8000/docs.

En Linux/macOS: `python3 -m venv .venv`, `.venv/bin/python -m pip install ...` y `../../../.venv/bin/python -m uvicorn api:app --port 8000`.

### Pruebas automáticas (desde `deliveries/week10/code`)

```powershell
..\..\..\.venv\Scripts\python.exe -m unittest discover -p "test_*.py"   # 70 pruebas, todas pasan (13-nov-2026)
```

### Reproducir la evaluación

```powershell
cd deliveries\week12\code
..\..\..\.venv\Scripts\python.exe evaluar_producto.py       # error por rango de precio + coherencia de punta a punta
..\..\..\.venv\Scripts\python.exe casos_estudio.py          # casos de estudio
..\..\..\.venv\Scripts\python.exe evaluar_recomendador.py   # recomendador frente al buscador y al azar
```

### Reentrenar (opcional)
Desde `deliveries/week10/code`: `entrenar_perfil.py` (modelo 1) y `entrenar_tendencia.py` (modelo 4).
El modelo de precio (`entrenar.py`) **no se reentrena**: es la versión revisada por el profesor y la app verifica su hash.

### Notebooks (semanas 6–7)

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m notebook
```
Abrir `deliveries/week07/code/EDA_week07.ipynb` y ejecutar todo; lee los crudos de `deliveries/week04/data/`.

### Variables de entorno (todas opcionales en local)

| Variable | Uso |
|---|---|
| `DATABASE_URL` | Postgres (Neon) en producción. Sin ella se usa SQLite en `deliveries/week10/data/deparent.sqlite` (se crea sola, no se sube) |
| `DEPARENT_DB` | Otra ruta para la base SQLite |
| `DEPARENT_ANALISTAS` | Correos (separados por comas) que ven el panel de KPIs |
| `DEPARENT_ORIGENES` | Dominios permitidos si el frontend se sirve aparte |

### Despliegue
Render con `render.yaml` (un solo servicio que sirve API y frontend). El mercado se actualiza con
`.github/workflows/actualizar-mercado.yml` o, si los portales bloquean la nube, con `scraper/programar_tarea.ps1`
en local. Detalle en [`deliveries/week10/deployed_url.txt`](deliveries/week10/deployed_url.txt).

---

## 5. Equipo y roles

| Integrante | Rol principal |
|---|---|
| **Adrian Urbina Mendoza** | Líder · adquisición y preprocesamiento de datos |
| **Armando Martinez Palomino** | Ingeniería de datos · integración de fuentes externas (ATU, BCRP) |
| **Breysi Salazar Medina** | Machine learning · modelos y evaluación |
| **Luciana Yangali Cáceres** | Aplicación y visualización · interfaz web |

Detalle: [`deliveries/week07/planning/team_responsibilities.md`](deliveries/week07/planning/team_responsibilities.md) y
[`deliveries/week15/ContributionStatement.md`](deliveries/week15/ContributionStatement.md).

---

## 6. Limitaciones principales
- El modelo aprende **precios pedidos** en anuncios, no precios de contrato.
- El rango de precio tiene radio fijo (S/ 1,357): bien calibrado en promedio, menos en departamentos de lujo.
- Distritos con pocos anuncios tienen error inestable.
- Los portales bloquean a veces la descarga automática (error 403); la app usa la última captura completa.
- Render gratuito se duerme tras 15 min sin visitas.

Más detalle en [`deliveries/week12/EvaluationReport.md`](deliveries/week12/EvaluationReport.md) §8.
