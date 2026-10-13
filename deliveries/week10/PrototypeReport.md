# Prototype Report — Semana 10

## 1. Resumen ejecutivo

(Describe en 2-4 párrafos el prototipo, su propósito, y la demostración que se entregará.)

## 2. Funcionalidades implementadas

- [ ] Listar las funciones concretas implementadas en el prototipo (por ejemplo: carga de datos, preprocesamiento, inferencia del modelo X, dashboard con filtros, exportar resultados).

Ejemplo:
- Carga de dataset `departamentos_procesados.csv` desde `data/`.
- Preprocesamiento y generación de features X, Y, Z.
- Inferencia de precio esperado usando `models/precio_model.joblib`.
- Visualización web mínima con Flask/Streamlit en `code/app.py`.

## 3. Arquitectura del sistema

- Diagrama: (adjuntar imagen en `architecture/` y referenciarla aquí).
- Componentes:
  - Frontend: (tecnología, rutas, pantallas principales)
  - Backend: (API / scripts de inferencia)
  - Almacenamiento: (carpeta `data/`, `models/`)
  - Orquestación: (notebooks que generan `data/`)

## 4. Artefactos incluidos

- Código: carpeta `code/` (especificar entrypoints y comandos para ejecutar).
- Datos procesados: `data/` (lista de archivos incluida y una breve descripción).
- Modelos serializados: `models/` (formato y cómo cargarlos).
- Presentación: `PresentationWeek10.*`.
- Capturas / video: `screenshots/` o `demo/`.
- URL deploy (si aplica): contenido de `deployed_url.txt`.

## 5. Resultados y ejemplos de uso

(Pegar ejemplos de comandos y capturas de salida de inferencia o pantallas.)

## 6. Limitaciones conocidas

- Datos: tamaño, sesgos, calidad.
- Modelos: rango de valores válidos, advertencias de uso.
- Performance: tiempos de inferencia, requisitos de memoria.

## 7. Desafíos técnicos encontrados

- Describir problemas relevantes (p.ej., integración de ATU, inconsistencias geocodificación, tiempo de entrenamiento).

## 8. Trabajo pendiente

- Lista priorizada de tareas para completar el prototipo (p.ej., serializar modelos, mejorar UI, pruebas E2E, despliegue).

## 9. Anexos

- Incluir enlaces a notebooks relevantes en `deliveries/week06/` y `deliveries/week07/`.
