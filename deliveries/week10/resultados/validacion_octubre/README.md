# Validación temporal: el modelo de septiembre frente a anuncios de octubre

El modelo de precio (`models/modelo_docente.joblib`, congelado y sin reentrenar) se entrenó con la captura del
14 de septiembre de 2026. Su limitación declarada era que no se había validado en períodos posteriores. Aquí se
mide sobre la captura diaria del **23 de octubre de 2026**, cinco semanas y media después.

Reproducir, desde `deliveries/week10/code` (requiere `data_diaria/`, que no se sube a GitHub):

```powershell
..\..\..\.venv\Scripts\python.exe validar_octubre.py            # la captura completa más reciente
..\..\..\.venv\Scripts\python.exe validar_octubre.py --captura 2026-10-23
```

## Cómo se armó la muestra
| Paso | Anuncios |
|---|---:|
| Captura del 23-oct (Adondevivir y Urbania) | 6,166 |
| Válidos tras el preprocesamiento de la Semana 7 (`preprocesar.py`) | 5,335 |
| Fuera: ya estaban en septiembre (mismo id) | −1,077 |
| Fuera: posibles duplicados de anuncios de septiembre (heurística de grupos) | −1,387 |
| Fuera: duplicados dentro de octubre (un anuncio por posible inmueble) | −1,159 |
| **Evaluados** | **1,712** |

`preprocesar.py` reproduce exactamente `week07/data/departamentos_procesados.csv` a partir de la captura cruda de
septiembre: mismas 3,128 filas, mismas columnas y mismas predicciones (`test_preprocesar.py`). Con capturas nuevas,
los distritos que no estaban en el entrenamiento van a "Otros", y se corrigen tres nombres que los portales usan en
octubre: "Lima Cercado" → Lima, "Ate Vitarte" → Ate y "Magdalena Vieja" (nombre antiguo de Pueblo Libre) → Pueblo Libre.
La captura del 22-oct se descarta (falló: 30 anuncios).

## Resultados
| Métrica | Prueba de septiembre (629) | Octubre (1,712) |
|---|---:|---:|
| MAE | S/ 553.18 | **S/ 512.29** (IC 95% bootstrap: 476 a 551) |
| RMSE | S/ 1,075.56 | **S/ 971.73** |
| MAPE | 18.85% | **16.43%** |
| R² | 0.7622 | **0.7852** |
| Cobertura del rango de 90% (radio S/ 1,356.95) | 92.2% | **93.5%** |
| Baseline mediana distrital, MAE | S/ 993.23 | S/ 948.07 |
| Baseline mediana global, MAE | S/ 1,215.82 | S/ 1,121.09 |

**Sensibilidad.** Si se excluye solo por id, sin la heurística de duplicados (que puede unir departamentos
distintos de un mismo edificio), se evalúan 2,845 anuncios: MAE S/ 533.96, MAPE 16.00%, R² 0.7831 y cobertura 93.0%.
La conclusión no cambia.

**Sesgo.** La mediana de (precio pedido − estimado) es −S/ 65 y el 44.5% de los anuncios pide más que el estimado:
en octubre se pide un poco menos de lo que el modelo aprendió en septiembre. Coincide con el historial de la descarga
diaria: de los 1,292 anuncios que siguen publicados desde septiembre, 416 cambiaron de precio, con una baja mediana de 6.7%.

## Por distrito (`error_por_distrito.csv`)
Con 20 o más anuncios en ambas muestras, el error se mantiene o baja en Miraflores, Surco, San Miguel, Jesús María,
Barranco, Lince, Surquillo y Pueblo Libre. **Sube en San Isidro (S/ 643 → S/ 814) y Magdalena (S/ 239 → S/ 457)**:
son los dos distritos a vigilar. Lima, San Borja, "Otros", Chorrillos, La Victoria, La Molina, Ate, Los Olivos,
Breña, Comas, San Martín de Porres y Callao tienen menos de 20 anuncios en alguna de las dos muestras: su error no es estable.

## Lectura
En un horizonte de cinco semanas el modelo de septiembre **no se degradó**: el error en anuncios nuevos queda dentro
o por debajo del de la prueba original, el rango calibrado conserva su cobertura y sigue muy por delante de los
baselines. **No hace falta reentrenar por ahora.** Por eso la app usa el mercado de octubre (`data/mercado.csv`) con
el modelo de septiembre. Conviene repetir la validación con capturas posteriores y vigilar San Isidro y Magdalena.

## Límites
- Precios pedidos en anuncios, no de contrato.
- Un solo corte de octubre: mide un desfase corto, no estacionalidad ni cambios de mercado de meses.
- La heurística de duplicados puede omitir republicaciones con otro texto o unir viviendas distintas (por eso la sensibilidad).
- La captura tuvo bloqueos puntuales de Urbania (error 403): faltan algunas páginas.
- En el entrenamiento, 10 anuncios de "Magdalena Vieja" quedaron en "Otros"; no se corrige para no alterar el modelo congelado.
- `predicciones.csv` guarda solo distrito y precios; no incluye ids, direcciones ni textos de los anuncios.
