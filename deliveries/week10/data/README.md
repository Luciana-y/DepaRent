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

## Duda abierta: que la app use la descarga diaria sola
Hoy el mercado se actualiza a mano con los dos comandos de arriba. Para que sea automático hay tres piezas que decidir:

1. **Encadenar los pasos.** La tarea programada (`scraper/programar_tarea.ps1`) descarga a las 07:00. Se le pueden
   sumar `preparar_mercado.py` y `entrenar_perfil.py`, y que la API recargue el mercado sin reiniciarse (un endpoint
   de recarga protegido o una relectura periódica de `mercado.json`).
2. **Dónde corre.** En local funciona porque `data_diaria/` está en la misma PC. En un despliegue (Render), el
   servidor no ve esa carpeta: o se sube cada día `mercado.csv` al repositorio (y el servidor se vuelve a desplegar),
   o el scraper corre en el propio servidor con un disco persistente.
3. **Controles.** Cada actualización debería rechazar capturas fallidas (como la del 22-oct, con 30 anuncios),
   repetir `validar_octubre.py` para vigilar si el modelo se degrada y avisar antes de publicar un mercado con
   menos anuncios de lo normal. Scrapear a diario también depende de los términos de uso de los portales.
