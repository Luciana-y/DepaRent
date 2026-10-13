# Código del prototipo - Flask

Este directorio contiene un prototipo mínimo en Flask que utiliza el dataset procesado `departamentos_procesados.csv` ubicado en `deliveries/week07/data/`.

Archivos:
- app.py: aplicación Flask con dos rutas (`/` y `/predict`).
- inference.py: clase `Estimator` que carga el dataset y calcula la mediana de renta por distrito.
- templates/index.html: interfaz web simple para probar el endpoint /predict.
- requirements.txt: dependencias necesarias.

Ejecución (desde la raíz del repositorio):

```bash
# crear entorno y activar
python -m venv venv
# Windows
# venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# instalar dependencias
pip install -r deliveries/week10/code/requirements.txt

# ejecutar la app
python deliveries/week10/code/app.py
```

Notas:
- La app busca el dataset en `deliveries/week07/data/departamentos_procesados.csv`.
- Si el dataset no está en el repositorio o es muy grande, puedes crear un CSV de ejemplo con las columnas `distrito` y `precio` y colocarlo en la ruta indicada.
