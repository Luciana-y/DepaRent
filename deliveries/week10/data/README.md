# Datos del prototipo

## Qué usa la app
| Archivo | Uso | Fecha |
|---|---|---|
| `mercado.csv` | Búsqueda, fichas, comparables y perfiles: 3,055 anuncios únicos | Captura diaria del 23-oct-2026 |
| `mercado.json` | De qué captura sale el mercado; la app muestra esa fecha en sus textos | — |
| `demo_casos.json` | Tres perfiles hipotéticos precargados (Lince, Miraflores, San Isidro) | Copia del profesor |
| `deparent.sqlite` | Cuentas, departamentos e interesados (se crea sola; **no se sube**) | En vivo |
| `../../week07/data/departamentos_procesados.csv` | Entrenamiento de los modelos de precio y de perfiles | 14-sep-2026 |
| `../../week07/data/paraderos_procesado.csv` | Accesibilidad (modelo 2) | ATU, mayo de 2021 |

El **modelo de precio** sigue siendo el de septiembre: se validó con 1,712 anuncios nuevos de octubre y no se degradó
(`../resultados/validacion_octubre/`). Los **perfiles** se aprendieron con septiembre y a ellos se asignan los anuncios
de octubre; reentrenarlos con octubre daba una segmentación peor.

`mercado.csv` no tiene dirección, coordenadas, título ni descripción. Sí guarda el enlace al anuncio original en
Adondevivir o Urbania, que solo se muestra en la ficha (ver `../PRODUCT.md`). Los valores imposibles (por ejemplo, un
mantenimiento de S/ 350,000) se guardan como no informados.

## Cómo se genera
Desde `deliveries/week10/code`:

```powershell
..\..\..\.venv\Scripts\python.exe preparar_mercado.py     # captura completa más reciente de data_diaria/
..\..\..\.venv\Scripts\python.exe entrenar_perfil.py      # reasigna los perfiles y los comparables
```

Después hay que reiniciar la API, que carga el mercado al arrancar.

## Actualización automática
Desde que `main` tenga el flujo `.github/workflows/actualizar-mercado.yml`, el mercado se actualiza solo cada día a las
07:00 de Lima en los servidores de GitHub: descarga → `preparar_mercado.py` → `entrenar_perfil.py` → pruebas → commit.
Render vuelve a desplegar con ese commit. No hay que subir datos a mano ni tener la PC encendida. Los pasos para
activarlo y sus límites están en `../deployed_url.txt`.

Respaldo si los portales bloquean la descarga desde la nube: la tarea programada local (`scraper/programar_tarea.ps1`)
seguida de los dos comandos de arriba y un `git push`.
