# Semana 10 — Prototipo funcional (DepaRent)

DepaRent ayuda a un propietario a decidir el precio de alquiler de su departamento y a un inquilino a encontrar
uno a su medida. El prototipo web tiene tres recorridos:

| Recorrido | Ruta | Qué hace |
|---|---|---|
| Inicio | `#/` | Página informativa: problema, qué buscamos, cómo funciona, equipo y límites |
| Propietario | `#/ingresar` → `#/mis-departamentos` | Registro e inicio de sesión; lista de sus departamentos (o invitación a agregar el primero); análisis de cada uno con los 6 componentes; publicación con el precio elegido |
| Inquilino | `#/buscar` | Búsqueda por distrito, presupuesto, dormitorios, baños, área, amenidades y cercanía a paraderos, sobre 3,013 anuncios de mercado y los departamentos publicados en DepaRent; cada resultado indica si su precio está por debajo, en línea o por encima del estimado y abre su ficha (`#/anuncio/:id`, con «Copiar enlace»): precio frente al estimado, anuncios parecidos (cada uno abre su ficha), transporte y, según el origen, el enlace al anuncio original en Adondevivir o Urbania o un formulario «Me interesa» que llega al propietario |
| Prueba rápida | `#/probar` | El análisis completo sin crear cuenta |

Los seis componentes analíticos:

| # | Componente | Método | Archivo |
|:-:|---|---|---|
| 1 | Perfil competitivo y comparables | K-Means (k=4, sin precio) + vecinos cercanos | `code/perfil_competitivo.py` |
| 2 | Accesibilidad a transporte | Paraderos ATU con `cKDTree` | `code/accesibilidad.py` |
| 3 | Precio esperado y rango | HistGradientBoosting + rango calibrado (copia del profesor, 20-oct-2026) | `code/modelo.py` |
| 4 | Tendencia distrital | SARIMA sobre series trimestrales del BCRP | `code/tendencia.py` |
| 5 | Precio de publicación | Reglas sobre 1 + 3 + 4 (competitivo, equilibrado, renta superior) | `code/escenarios_precio.py` |
| 6 | Simulador de mejoras | Uso contrafactual del modelo 3 (del profesor) | `code/escenarios.py` |

## Arquitectura
```
Navegador ──► frontend/ (HTML + CSS + JS en módulos, Leaflet)  ──fetch──►  code/api.py (FastAPI)
                                                                              ├─ modelos 1–6 (code/*.py)
                                                                              ├─ cuentas.py ─► Postgres (Neon) en producción · data/deparent.sqlite en local
                                                                              ├─ busqueda.py (anuncios de mercado + publicados)
                                                                              ├─ models/*.joblib
                                                                              ├─ resultados/ (métricas, pronósticos SARIMA)
                                                                              └─ ../week07/data/ (anuncios y paraderos procesados)
```
Cuentas: contraseñas con PBKDF2-SHA256 y sal propia; tokens de sesión guardados solo como hash, con vencimiento de 7 días.
En local la base `data/deparent.sqlite` se crea sola y no se sube a GitHub (`.gitignore`); en producción, con
`DATABASE_URL`, se usa Postgres en Neon y las tablas también se crean solas. Es un prototipo académico: no tiene
recuperación de contraseña ni verificación de correo.
La API también sirve el frontend, en local y en Render (https://deparent.onrender.com, ver `deployed_url.txt`). `code/app.py` (Streamlit) se conserva como versión del profesor y respaldo.

## Contenido
| Elemento | Ubicación |
|---|---|
| Frontend web | `frontend/` (`index.html`, `styles.css`, `inicio.css`, `js/`); diseño en `DESIGN.md` y contexto en `PRODUCT.md` |
| API y modelos | `code/` |
| Datos | `data/` (ver su README; los procesados base están en `../week07/data/`) |
| Modelos serializados | `models/` (ver `metadata.md`) |
| Métricas y resultados | `resultados/` |
| Ejercicio del profesor (n y MAE de un distrito) | `code/EJERCICIO_FINAL.py` |
| Reporte del prototipo | `PrototypeReport.md` |
| Presentación | `PresentationWeek10.pptx` / `.pdf` |
| Capturas / demo | `screenshots/` |
| URL desplegada | https://deparent.onrender.com (`deployed_url.txt`) |

### Archivos de `code/`
| Archivo | Función |
|---|---|
| `api.py` | API web; en local también sirve el frontend |
| `cuentas.py`, `busqueda.py` | Cuentas de propietarios y sus departamentos; búsqueda para inquilinos |
| `modelo.py`, `entrenar.py` | Modelo 3 (del profesor). No reentrenar: la app verifica sus hashes |
| `perfil_competitivo.py`, `entrenar_perfil.py` | Modelo 1 |
| `accesibilidad.py` | Modelo 2 |
| `tendencia.py`, `entrenar_tendencia.py` | Modelo 4 |
| `escenarios_precio.py` | Modelo 5 |
| `escenarios.py`, `laboratorio_area.py` | Modelo 6 y exploración del área (del profesor) |
| `evidencia_distrital.py`, `ayuda_interfaz.py` | Error por distrito y textos (del profesor) |
| `app.py` | Versión Streamlit del profesor, como respaldo |
| `preprocesar.py` | Preprocesamiento de la Semana 7 como módulo (reproduce exactamente los datos procesados) |
| `preparar_mercado.py` | Convierte la captura diaria más reciente en el mercado de la app (`data/mercado.csv`) |
| `validar_octubre.py` | Validación temporal del modelo congelado con la descarga diaria de octubre (`resultados/validacion_octubre/`) |
| `test_*.py` | Pruebas (47) |

## Requisitos
- Python 3.12 o 3.13 y conexión a internet la primera vez (para instalar dependencias; el mapa usa teselas de OpenStreetMap).
- Dependencias exactas en `code/requirements.txt`. Para usar Postgres en local (opcional) instalar también `psycopg[binary]`.

## Instalación y ejecución local (Windows, desde la raíz del repositorio)
```powershell
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r deliveries/week10/code/requirements.txt
cd deliveries/week10/code
..\..\..\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```
Abrir **http://127.0.0.1:8000**. En Linux/macOS usar `python3 -m venv .venv` y `.venv/bin/python`.

Endpoints principales: `GET /api/opciones`, `POST /api/analizar`, `POST /api/accesibilidad`, `POST /api/comparar`,
`POST /api/area`, `POST /api/cuentas/registro|ingreso|salida`, `GET|POST /api/departamentos`,
`GET|PUT|DELETE /api/departamentos/{id}`, `POST|DELETE /api/departamentos/{id}/publicacion`, `POST /api/buscar`,
`GET /api/anuncios/{id}` y `POST /api/anuncios/{id}/interes`.
Documentación interactiva en http://127.0.0.1:8000/docs.

Versión Streamlit del profesor (opcional): `..\..\..\.venv\Scripts\python.exe -m streamlit run app.py`.

## Pruebas y ejercicio (desde `deliveries/week10/code`)
```powershell
..\..\..\.venv\Scripts\python.exe -m unittest test_cuentas_busqueda test_tendencia_escenarios_api test_modelos_perfil_accesibilidad test_evidencia_distrital test_laboratorio_area
..\..\..\.venv\Scripts\python.exe EJERCICIO_FINAL.py
```

## Reentrenar (opcional)
- Modelo 1: `python entrenar_perfil.py` → `models/perfil_competitivo.joblib`, `resultados/metricas_perfil.json`.
- Modelo 4: `python entrenar_tendencia.py` → `resultados/tendencia_distrital.json`.
- Modelo 3: **no reentrenar**. Es la versión del profesor y la app verifica sus hashes.

## Despliegue
Publicado en **https://deparent.onrender.com**. Configurado para Render con `render.yaml` (raíz del repo): un solo servicio que sirve la API y el frontend, con
`code/requirements-deploy.txt`. El mercado se actualiza solo cada día con GitHub Actions
(`.github/workflows/actualizar-mercado.yml`). Pasos y límites del plan gratuito en `deployed_url.txt`.

## Credenciales y datos
No se requieren variables de entorno ni credenciales para el uso local. Variables opcionales: `DEPARENT_DB` (ruta de
la base SQLite), `DATABASE_URL` (cadena de conexión de Postgres; en Render apunta a Neon y se configura en el panel,
nunca en el repositorio) y `DEPARENT_ORIGENES` (dominios que pueden llamar a la API, solo si el frontend va aparte). Ninguna pantalla muestra dirección, coordenadas ni descripción de los anuncios; solo la ficha de un anuncio de mercado enlaza a su original en Adondevivir o Urbania (ver `PRODUCT.md`).
