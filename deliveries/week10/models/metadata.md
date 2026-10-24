# Modelos serializados

| Archivo | Modelo | Uso en el producto | Generado por |
|---|---|---|---|
| `modelo_docente.joblib` | HistGradientBoosting (Pipeline con imputación y one-hot de distrito) + radio de rango calibrado | Modelo 3: precio esperado y rango; también lo usan el simulador (modelo 6) y la exploración de área | `code/entrenar.py` (copia del profesor, revisión 20-oct-2026). **No reentrenar**: la app verifica su hash |
| `perfil_competitivo.joblib` | K-Means (k=4) con imputación + StandardScaler, aprendido con septiembre; tabla de referencia con el mercado actual (`data/mercado.csv`, 23-oct) asignado a esos perfiles | Modelo 1: perfil competitivo y anuncios comparables | `code/entrenar_perfil.py` |

Otros artefactos analíticos:
- **Modelo 2 (accesibilidad):** sin archivo serializado; se calcula al momento con `cKDTree` sobre
  `week07/data/paraderos_procesado.csv` (`code/accesibilidad.py`). Reproduce exactamente las 6 variables del notebook de la Semana 7.
- **Modelo 4 (tendencia):** `resultados/tendencia_distrital.json`, con los pronósticos SARIMA precalculados por
  `code/entrenar_tendencia.py`. Las series del BCRP solo cambian con una nueva publicación, así que la API consulta el archivo.
- **Modelo 5 (publicación):** reglas en `code/escenarios_precio.py`, sin entrenamiento.

## Versiones necesarias para cargarlos
Python 3.12 o 3.13 · scikit-learn 1.7.2 · numpy 2.3.5 · pandas 2.3.3 · joblib 1.5.2 (ver `code/requirements.txt`).
Con otra versión de scikit-learn, joblib puede fallar al cargar o advertir incompatibilidad.

## Cómo cargarlos (desde `code/`)
```python
import joblib
from modelo import ROOT, predecir
from perfil_competitivo import comparables
precio = joblib.load(ROOT / "models/modelo_docente.joblib")
perfil = joblib.load(ROOT / "models/perfil_competitivo.joblib")
casa = {"distrito_norm": "lince", "area_total": 50, "dormitorios": 1, "banos": 1, "estacionamientos": 0,
        "antiguedad": 5, "mantenimiento": 200, "ascensor": 1, "balcon": 0, "terraza": 0,
        "piscina": 0, "gimnasio": 0, "pet_friendly": 1}
predecir(casa, precio)      # precio_estimado_soles, limites del rango, referencia distrital
comparables(casa, perfil)   # perfil, 8 comparables, percentiles de precio
```

## Entradas y salidas
- **Entrada común:** `distrito_norm`, `area_total`, `dormitorios`, `banos`, `estacionamientos`, `antiguedad`,
  `mantenimiento` y las amenidades `ascensor`, `balcon`, `terraza`, `piscina`, `gimnasio`, `pet_friendly` (0, 1 o `None`).
  El modelo 1 no usa `estacionamientos` (nulos ambiguos) ni ningún precio.
- **Modelo 3:** alquiler mensual esperado en soles y rango calibrado.
- **Modelo 1:** número y nombre de perfil, 8 comparables (sin dirección, coordenadas ni URL) y percentiles 25/50/75 de su precio pedido.

## Métricas de referencia
**Modelo 3** (prueba agrupada de 629 anuncios, `resultados/metricas.json`):

| Método | MAE (S/) | MAPE | R² |
|---|---:|---:|---:|
| Mediana global | 1,215.82 | 37.84% | -0.0435 |
| Mediana distrital | 993.23 | 26.64% | 0.1332 |
| HistGradientBoosting | 553.18 | 18.85% | 0.7622 |

Rango calibrado: radio S/ 1,356.95, nivel nominal 90%, cobertura observada en prueba 92.21%.
Estas métricas usan una partición distinta de la del notebook de la Semana 7 (MAPE 15.77%) y no son comparables directamente.

**Modelo 1** (3,128 anuncios, `resultados/metricas_perfil.json`):

| k | Silhouette | ARI entre semillas |
|---:|---:|---:|
| 2 | 0.1824 | 0.997 |
| 3 | 0.2012 | 0.999 |
| **4** | **0.2075** | **1.000** |
| 5 | 0.1623 | 0.940 |
| 6 | 0.1612 | 0.625 |
| 7 | 0.1770 | 0.549 |

En la Semana 7 se usaba k=4 con precio por m² entre las variables (silhouette 0.1776). Se quitó el precio porque el
propietario no lo conoce antes de publicar.

**Modelo 4** (`resultados/tendencia_distrital.json`): SARIMA (p,1,q)(P,D,Q,4) con orden elegido por AIC y los
últimos 4 trimestres reservados. Supera al naive estacional en 10 de 13 series y al naive (último valor) en 7 de 13:
la ventaja sobre el baseline simple no es consistente, así que la tendencia se presenta como contexto, no como predicción precisa.

**Mercado de octubre en los perfiles.** Los perfiles se aprenden con septiembre y a ellos se asignan los 3,055 anuncios
de la captura del 23-oct: silhouette de octubre asignado 0.2063 (frente a 0.2075 en septiembre) y cada perfil conserva
el rasgo que le da nombre. Reentrenar con octubre dio silhouette 0.148 con k=4 y un grupo de "mascotas" que ya no existía.

**Modelo 3 frente a octubre** (`resultados/validacion_octubre/`): 1,712 anuncios nuevos, MAE S/ 512.29 (IC 95% 476–551),
MAPE 16.43%, R² 0.7852, cobertura del rango 93.5%. No se degradó: no se reentrena.
