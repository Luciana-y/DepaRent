# Product

<!-- impeccable:product-schema 1 -->

## Platform

web (escritorio y móvil). Frontend estático en `frontend/` (HTML, CSS y JS en módulos, sin framework) servido por la API FastAPI en local; Netlify más una API en Render cuando se despliegue.

## Users

- **Propietario** de uno o varios departamentos en alquiler en Lima Metropolitana y Callao. Antes de publicar un anuncio quiere saber a qué precio ponerlo. Hoy compara a mano con anuncios de portales que no siempre son comparables.
- **Inquilino** que busca un departamento por distrito, presupuesto y características, y quiere saber si un precio es razonable. No necesita cuenta.
- **Docente y compañeros del curso** DS3022 (UTEC) que evalúan el prototipo en una demo.

## Product Purpose

Reducir la incertidumbre del propietario antes de publicar: precio esperado con su rango de error, anuncios realmente parecidos, accesibilidad a transporte, tendencia del distrito y tres precios de publicación (competitivo, equilibrado, renta superior). Éxito: el propietario elige un precio de publicación y entiende por qué; el inquilino encuentra opciones y sabe si su precio está en línea con el mercado.

## Positioning

Combina seis componentes con datos reales de Lima que un portal de anuncios no muestra juntos: modelo de precio entrenado con 3,128 anuncios (septiembre de 2026), perfiles K-Means sin precio, 3,233 paraderos ATU, series trimestrales del BCRP con SARIMA, reglas de publicación y simulador de mejoras. Dice siempre sus límites.

## Evidence

- Modelo de precio: MAE S/ 553.18, MAPE 18.85%, R² 0.7622 en 629 anuncios de prueba; rango calibrado al 90% con cobertura observada de 92.2%.
- Perfiles: k=4, silhouette 0.2075. Tendencia: SARIMA supera al naive estacional en 10 de 13 series y al naive en 7 de 13.
- No hay clientes, testimonios, logos de prensa ni cifras de negocio: no se inventan.

## Constraints

- Son precios pedidos en anuncios de una sola captura, no contratos ni tasaciones; la interfaz lo dice donde muestra precios.
- Nunca mostrar dirección, coordenadas exactas, URL ni texto de los anuncios originales.
- Español de Perú, soles con formato `S/ 3,656`.
- Las vistas y rutas existentes se conservan: inicio, ingreso y registro, mis departamentos, detalle con análisis y publicación, búsqueda, prueba sin cuenta.

## Brand

- Nombre: DepaRent. Sin logo definido.
- Identidad visual: **decisión abierta**. El verde actual no es un compromiso de marca confirmado.

## Accessibility

Contraste AA, foco visible, navegación por teclado, `prefers-reduced-motion`, funcional a 390 px de ancho.
