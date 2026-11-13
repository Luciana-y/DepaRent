# DepaRent — Guía para el profesor

Este archivo responde punto por punto a lo que se pidió para la revisión. La descripción general del proyecto y
las instrucciones completas están en el [`README.md`](README.md).

| | |
|---|---|
| **App desplegada** | https://deparent.onrender.com (plan gratuito: la primera visita tarda 30–60 s en despertar) |
| **Repositorio** | https://github.com/Luciana-y/DepaRent |
| **Panel de KPIs** | Ingresar en la app con `analista@gmail.com` / contraseña `analista` (ver §2) |
| **Equipo** | Adrian Urbina Mendoza · Armando Martinez Palomino · Breysi Salazar Medina · Luciana Yangali Cáceres |

---

## 1. Lo que se pidió incluir y dónde está

| Pedido | Dónde está |
|---|---|
| **Código completo y actualizado** | Producto (API + modelos): [`deliveries/week10/code/`](deliveries/week10/code/) · Interfaz web: [`deliveries/week10/frontend/`](deliveries/week10/frontend/) · Descarga diaria de anuncios: [`scraper/`](scraper/) · Índice del código por etapa: [`deliveries/week15/code/README.md`](deliveries/week15/code/README.md) |
| **Base de datos utilizada** | Datos crudos (septiembre): [`deliveries/week04/data/`](deliveries/week04/data/) · Datos procesados: [`deliveries/week07/data/`](deliveries/week07/data/) · Mercado actual de la app (captura del 9-nov-2026): [`deliveries/week10/data/mercado.csv`](deliveries/week10/data/) · Diccionario de datos: [`deliveries/week07/data_dictionary.csv`](deliveries/week07/data_dictionary.csv) · Base de cuentas: Postgres (Neon) en producción y SQLite en local |
| **Notebooks o scripts de entrenamiento** | Notebooks de EDA y preprocesamiento: [`deliveries/week06/code/EDA_week06_v5.ipynb`](deliveries/week06/code/), [`deliveries/week07/code/EDA_week07.ipynb`](deliveries/week07/code/) · Notebook del profesor: [`deliveries/week10/code/Notebook_docente.ipynb`](deliveries/week10/code/) · Scripts: `entrenar.py` (precio), `entrenar_perfil.py` (K-Means) y `entrenar_tendencia.py` (SARIMA) en `deliveries/week10/code/` |
| **Modelo entrenado** | [`deliveries/week10/models/`](deliveries/week10/models/) (`modelo_docente.joblib`, `perfil_competitivo.joblib`) · Cómo cargarlos y sus métricas: [`deliveries/week10/models/metadata.md`](deliveries/week10/models/metadata.md) |
| **Interfaz o prototipo actual** | En línea: https://deparent.onrender.com · Código: [`deliveries/week10/frontend/`](deliveries/week10/frontend/) · Capturas: [`deliveries/week10/screenshots/`](deliveries/week10/screenshots/) · Bocetos y wireframes: [`deliveries/week07/design/`](deliveries/week07/design/) |
| **Documentos y presentaciones** | Tabla por semana en el [`README.md`](README.md) §3 · Evaluación: [`deliveries/week12/EvaluationReport.md`](deliveries/week12/EvaluationReport.md) · Última presentación: [`deliveries/week10/PresentationWeek10.pptx`](deliveries/week10/) |
| **Instrucciones para instalar y ejecutar** | [`README.md`](README.md) §4 |
| **Enlace de GitHub** | https://github.com/Luciana-y/DepaRent |
| **Ejercicio del profesor (n y MAE de un distrito)** | [`deliveries/week10/code/EJERCICIO_FINAL.py`](deliveries/week10/code/EJERCICIO_FINAL.py) |

## 2. Acceso al panel de KPIs

En https://deparent.onrender.com, entrar a **Ingresar** con esta cuenta de analista:

| Correo | Contraseña |
|---|---|
| `analista@gmail.com` | `analista` |

Al iniciar sesión se abre directamente el **Panel de análisis (KPIs)**: uso del producto (cuentas, perfiles,
departamentos, publicaciones, guardados y mensajes), métricas del modelo, estado de los datos y evaluación del
recomendador. El panel solo muestra conteos agregados, sin datos personales.

En una instalación local, la cuenta no existe todavía: hay que crearla desde **Ingresar** y arrancar la API con
`$env:DEPARENT_ANALISTAS = "analista@gmail.com"` antes del comando `uvicorn` de la §4.

## 3. Documento breve

Está en [`deliveries/week15/EstadoProyecto.md`](deliveries/week15/EstadoProyecto.md). Cada pregunta tiene su sección:

| Pregunta | Sección |
|---|---|
| Qué mejoras realizaron | §1 |
| Qué funciona actualmente | §2 |
| Qué modelo están utilizando y qué resultados obtuvieron | §3 |
| Cómo se conectan los datos, el modelo y la interfaz | §4 |
| Qué simulación pueden mostrar | §5 |
| Qué dificultades tienen actualmente | §6 |
| Qué les falta completar | §7 |
| Qué desean demostrar en la presentación | §8 |
| Qué parte está desarrollando cada integrante | §9 |

## 4. Ejecución rápida (Windows, desde la raíz del repositorio)

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r deliveries/week10/code/requirements.txt
cd deliveries/week10/code
..\..\..\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Abrir **http://127.0.0.1:8000**. No se necesitan credenciales para usarlo en local.
