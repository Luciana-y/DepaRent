# Design

DepaRent tiene dos superficies con una misma tipografía y una misma raíz de color. Las decisiones salen de las
skills Taste (dirección y medición), Impeccable (contexto, base de calidad y auditoría) y Emil Kowalski (movimiento).
El contexto del producto está en `PRODUCT.md`.

## 1. Página de inicio: el cartel

**Idea.** El cartel "SE ALQUILA" que los propietarios pegan en las ventanas de Lima, con el espacio del precio en
blanco; el estimador en vivo llena ese espacio con el precio del modelo. Dirección de Taste `borrowed-category`
(semilla 1823295350), sector inmobiliario.

| Rol | Valor |
|---|---|
| Fondo | `--bg #ff7a1f` (naranja de cartel), cortes duros a `--paper #ffffff` |
| Tinta | `--ink #050f16` |
| Tinta secundaria sobre naranja y papel | `--brown #5a2306` |
| Campos de color | naranja, papel, tinta y marrón; vecinos con distinta luminosidad |
| Tipografía | Epilogue 900 (display, tracking -0.04em, interlineado 0.88) y 400/500 (texto) |
| Tamaños | cinco pasos: `--step-display`, `--step-head`, `--step-lead`, `--step-body`, `--step-small` |
| Esquinas | cuadradas; los objetos (fichas, tarjetas) se inclinan 1.5 a 4 grados |

Reglas: un `h1` (`Se alquila. / ¿A cuánto?`), títulos de dos líneas como máximo, ninguna etiqueta encima de un
título, sin degradados, sin sombras en reposo, sin líneas finas. Las imágenes son fragmentos reales de la
interfaz (`data-ui`, al menos 300 × 200 px); no hay fotografías por decisión (no se descargaron imágenes).

## 2. Pantallas de la app: el libro contable

Estilo de Taste `achromatic-ledger` (semilla 1913438529) sobre `assets/app.css`.

| Rol | Valor |
|---|---|
| Fondo | `--ground #f2f2f0`, el gris del cielo de Lima |
| Superficies | `--surface #ffffff`, borde `--border #e3e2de`, reglas `--rule #efeeeb` |
| Texto | `--text #111111`, `--muted #5d5f63`, `--faint #67696d` |
| Color de datos | `--accent #c2510a` (4.6:1 sobre blanco), solo en el precio del propio departamento y en lo seleccionado |
| Acción principal | casi negra `--primary #111111`, una por pantalla |
| Tamaños | título 24, sección 16, KPI 28, texto 14, secundario 13 |
| Radios | tarjetas 8, controles 6, píldoras completas |

Cada pantalla responde una pregunta: **Mis departamentos** (¿cuáles están publicados y a qué precio?), **Detalle**
(¿a cuánto lo publico?), **Buscar** (¿cuáles valen lo que piden?). Los KPI son una tira dividida, sin íconos. Las
tarjetas de conteo filtran la lista y sus cifras se calculan sobre la vista. Las tablas alinean cifras a la derecha
con números tabulares y en el teléfono pasan a filas de dos líneas. Los estados vacíos, de carga y de error viven
dentro de su bloque.

**Elemento propio:** la regla de precios (`reglaPrecios` en `js/analisis.js`), con los 8 comparables, el rango
calibrado y los tres precios de publicación en un mismo eje, y el precio esperado como única línea naranja.

## 3. Movimiento

| Dónde | Qué | Valores |
|---|---|---|
| Inicio | Titular enmascarado (gesto principal) | 900 ms, `--ease-expo`, segunda línea 110 ms después |
| Inicio | Cartel que sube al cargar; texto de apoyo | 1000 ms y 700 ms |
| Inicio | Revelado único al entrar en pantalla | 700 a 900 ms, escalonado de 70 ms |
| Inicio | Desplazamiento ligado al scroll del fragmento de precios | `animation-timeline: view()`, solo si se soporta |
| App | Presión de botones y tarjetas | `scale(0.97)` o `0.98`, 140 ms, `--ease-out` |
| App | Menú lateral en el teléfono | abre 280 ms con `--ease-drawer`, cierra 160 ms |
| App | Aviso de publicación | `@starting-style`, 220 ms |
| Todas | Hover | solo con `(hover: hover) and (pointer: fine)` |

Sin animación en pestañas, filtros ni en la cifra del estimador (acciones frecuentes). Todo estado oculto existe
solo con `.js` y `prefers-reduced-motion: no-preference`; con movimiento reducido la página ya está terminada.

## 4. Verificación

- Taste `inspect.mjs`: inicio 0 FAIL (WARN defendidos: sin fotografías ni video por decisión; margen derecho
  medido con la barra de desplazamiento); búsqueda y probar con `--app` 0 FAIL. `lint.mjs` sin patrones prohibidos.
- axe-core (WCAG 2 A y AA): inicio, búsqueda, probar e ingreso sin problemas.
- Pruebas de la API: 39. Recorrido completo del propietario en Chrome sin errores de consola ni desborde horizontal.
