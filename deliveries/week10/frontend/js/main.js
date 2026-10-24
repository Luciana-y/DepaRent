import { sesion } from "./api.js";
import { vistaAnuncio } from "./anuncio.js";
import { vistaInicio } from "./inicio.js";
import { activarMovimiento } from "./movimiento.js";
import { $, esc } from "./util.js";
import {
  cerrarSesion, vistaBuscar, vistaDetalleDepartamento, vistaError, vistaIngresar, vistaMisDepartamentos,
  vistaNoEncontrada, vistaNuevoDepartamento, vistaProbar,
} from "./vistas.js";

// [patrón, vista, requiere sesión, sección, título en la barra del teléfono]
const RUTAS = [
  [/^\/$/, vistaInicio, false, "inicio", ""],
  [/^\/buscar$/, vistaBuscar, false, "buscar", "Buscar departamentos"],
  [/^\/anuncio\/([md]\d+)$/, vistaAnuncio, false, "buscar", "Anuncio"],
  [/^\/probar$/, vistaProbar, false, "probar", "Probar el análisis"],
  [/^\/ingresar$/, vistaIngresar, false, "ingresar", "Ingresar"],
  [/^\/mis-departamentos$/, vistaMisDepartamentos, true, "propietario", "Mis departamentos"],
  [/^\/mis-departamentos\/nuevo$/, vistaNuevoDepartamento, true, "nuevo", "Agregar departamento"],
  [/^\/mis-departamentos\/(\d+)$/, vistaDetalleDepartamento, true, "propietario", "Departamento"],
];

// Menú de la página de inicio: marca, tres enlaces y una acción.
function menuInicio() {
  const actual = sesion();
  $("#menu").innerHTML = `
    <div class="menu-links">
      <a href="#/buscar">Buscar</a>
      <a href="#/probar">Probar</a>
      ${actual ? '<a href="#/mis-departamentos">Mis departamentos</a>' : '<a href="#/ingresar">Ingresar</a>'}
    </div>
    ${actual ? '<a class="menu-action" href="#/mis-departamentos/nuevo">Agregar departamento</a>'
      : '<a class="menu-action" href="#/ingresar?modo=registro">Publicar mi depa</a>'}`;
}

// Marco de las pantallas de la app: barra lateral con etiquetas y lienzo.
function marco(main, seccion, titulo) {
  const actual = sesion();
  const item = (href, s, texto) => `<a class="nav-item" href="${href}" ${s === seccion ? 'aria-current="page"' : ""}>${texto}</a>`;
  main.innerHTML = `
    <div class="app">
      <aside class="sidebar" id="sidebar" aria-label="Navegación">
        <button class="btn ghost sidebar-close" type="button" data-cerrar-menu>Cerrar</button>
        <a class="app-brand" href="#/"><span class="app-mark" aria-hidden="true">D</span>
          <span><b>DepaRent</b><span>Lima · anuncios de sep. 2026</span></span></a>
        <p class="group-label">Explorar</p>
        ${item("#/buscar", "buscar", "Buscar departamentos")}
        ${item("#/probar", "probar", "Probar el análisis")}
        ${item("#/", "inicio", "Inicio")}
        <p class="group-label">Propietario</p>
        ${actual ? item("#/mis-departamentos", "propietario", "Mis departamentos") + item("#/mis-departamentos/nuevo", "nuevo", "Agregar departamento")
          : item("#/ingresar", "ingresar", "Ingresar o crear cuenta")}
        <div class="bottom">
          ${actual ? `<div class="user-row"><b>${esc(actual.usuario.nombre)}</b><span>${esc(actual.usuario.email)}</span></div>
            <button class="btn" type="button" id="salir">Salir</button>`
            : '<p class="hint">Sin cuenta puedes buscar y probar el análisis.</p>'}
        </div>
      </aside>
      <div class="canvas">
        <div class="phone-bar"><button class="btn" type="button" data-abrir-menu aria-controls="sidebar" aria-expanded="false">Menú</button><b>${esc(titulo)}</b></div>
        <div id="lienzo"></div>
      </div>
    </div>`;
  const lateral = $("#sidebar", main), abrir = $("[data-abrir-menu]", main);
  abrir.addEventListener("click", () => { lateral.classList.add("open"); abrir.setAttribute("aria-expanded", "true"); });
  $("[data-cerrar-menu]", main).addEventListener("click", () => { lateral.classList.remove("open"); abrir.setAttribute("aria-expanded", "false"); });
  $("#salir", main)?.addEventListener("click", cerrarSesion);
  return $("#lienzo", main);
}

async function navegar() {
  const [ruta, consulta = ""] = (location.hash.slice(1) || "/").split("?");
  const params = new URLSearchParams(consulta);
  const main = $("#vista");
  const encontrada = RUTAS.find(([patron]) => patron.test(ruta));
  $("#menu").classList.remove("open");
  $("#menu-toggle").setAttribute("aria-expanded", "false");
  if (!encontrada) {
    document.body.dataset.vista = "otra";
    return vistaNoEncontrada(marco(main, null, "Página no encontrada"));
  }
  const [patron, vista, privada, seccion, titulo] = encontrada;
  if (privada && !sesion()) {
    location.hash = "#/ingresar?siguiente=" + encodeURIComponent("#" + ruta);
    return;
  }
  document.body.dataset.vista = seccion;
  window.scrollTo(0, 0);
  const destino = seccion === "inicio" ? (menuInicio(), main) : marco(main, seccion, titulo);
  try {
    await vista(destino, params, ...(ruta.match(patron).slice(1)));
    activarMovimiento(main);
  } catch (error) {
    if (error.estado === 401) {
      location.hash = "#/ingresar?siguiente=" + encodeURIComponent("#" + ruta);
      return;
    }
    vistaError(destino, error);
  }
}

$("#menu-toggle").addEventListener("click", (e) => {
  const abierto = $("#menu").classList.toggle("open");
  e.currentTarget.setAttribute("aria-expanded", String(abierto));
});
window.addEventListener("hashchange", navegar);
navegar();

