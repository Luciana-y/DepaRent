# Datos procesados — instrucciones

Coloca aquí los datasets procesados que el prototipo necesita. Formatos admitidos: `.csv`, `.parquet`, `.json`.

Nombres sugeridos y su descripción:
- departamentos_procesados.csv — dataset inmobiliario limpio con coordenadas e imputación básica.
- departamentos_sin_geo_para_clustering.csv — versión para clustering sin variables geoespaciales.
- paraderos_procesado.csv — paraderos ATU procesados.
- bcrp_procesado.csv — indicadores distritales por trimestre.

Nota: los archivos de datos pueden ser grandes; si no puedes subirlos al repositorio público, coloca una versión muestreada (`_sample.csv`) y explica cómo regenerar los archivos completos desde los notebooks en `deliveries/week06/` y `deliveries/week07/`.
