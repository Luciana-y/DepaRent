# Descarga diaria de anuncios

Repite cada día la adquisición de la Semana 4 (`deliveries/week04/acquisition.md`) en Adondevivir y
Urbania, para tener varias capturas en el tiempo y poder validar el modelo con anuncios posteriores.

## Ejecutar a mano
```powershell
py -3 scraper\descarga_diaria.py                     # descarga completa (~6-8 min)
py -3 scraper\descarga_diaria.py --max-paginas 2 --sin-historial   # prueba rápida
```
No requiere instalar librerías (solo Python 3 estándar).

## Programarla todos los días
```powershell
powershell -ExecutionPolicy Bypass -File scraper\programar_tarea.ps1            # 07:00 por defecto
powershell -ExecutionPolicy Bypass -File scraper\programar_tarea.ps1 -Hora 06:30
```
Si la PC está apagada a esa hora, la descarga corre apenas se encienda. Para quitarla:
`Unregister-ScheduledTask -TaskName "DepaRent descarga diaria" -Confirm:$false`

## Qué se guarda (`data_diaria/`, fuera de git)
| Archivo | Contenido |
|---|---|
| `snapshots/AAAA-MM-DD.csv.gz` | Foto del día con las mismas 43 columnas de `departamentos_alquiler_lima.csv`, más `estado_portal` y `fecha_modificacion_portal` |
| `historial_precios.csv` | Una fila por anuncio y día: `fecha, id_anuncio, fuente, distrito, precio, moneda, precio_soles` |
| `anuncios.csv` | Una fila por anuncio: primera y última vez visto, días publicado, si sigue activo, precio inicial/actual y número de cambios de precio |
| `descargas_log.csv` | Resumen de cada ejecución (anuncios, páginas, errores, duración) |
| `ultima_ejecucion.log` | Salida de la última ejecución programada |

Leer un snapshot: `pd.read_csv("data_diaria/snapshots/2026-10-21.csv.gz")`.

## Decisiones
- Solo inmuebles tipo **Departamentos** (se descartan edificios y proyectos sin características).
- Deduplicación por `id_anuncio` entre portales (comparten IDs); se conserva el primero (Adondevivir).
- USD a soles con 3.75, la misma tasa de referencia de la Semana 4.
- Las amenidades quedan vacías, igual que en la Semana 4; se derivan en el EDA desde `texto_amenidades_crudo`.
- Teléfonos y correos del texto se reemplazan por `[telefono]` y `[correo]`; no se guarda el anunciante.
  El texto puede seguir teniendo nombres y las direcciones se conservan: por eso `data_diaria/` no se sube.
- Que un anuncio deje de aparecer (`activo = 0`) no confirma que se alquiló; puede haberse retirado o republicado.
- Correr dos veces el mismo día reemplaza los datos de ese día, no los duplica.
