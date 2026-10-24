import { sesion } from "./api.js";
import { vistaInicio } from "./inicio.js";
import { activarMovimiento } from "./movimiento.js";
import { $, $$, esc } from "./util.js";
import {
  cerrarSesion, vistaBuscar, vistaDetalleDepartamento, vistaError, vistaIngresar, vistaMisDepartamentos,
  vistaNoEncontrada, vistaNuevoDepartamento, vistaProbar,
} from "./vistas.js";

// [patrón, vista, requiere sesión, sección del menú]
const RUTAS = [
  [/^\/$/, vistaInicio, false, "inicio"],
  [/^\/buscar$/, vistaBuscar, false, "buscar"],
  [/^\/probar$/, vistaProbar, false, "probar"],
  [/^\/ingresar$/, vistaIngresar, false, "propietario"],
  [/^\/mis-departamentos$/, vistaMisDepartamentos, true, "propietario"],
  [/^\/mis-departamentos\/nuevo$/, vistaNuevoDepartamento, true, "propietario"],
  [/^\/mis-departamentos\/(\d+)$/, vistaDetalleDepartamento, true, "propietario"],
];

function menu(seccion) {
  const actual = sesion();
  $("#menu").innerHTML = `
    <div class="menu-links">
      <a href="#/buscar" data-s="buscar">Buscar</a>
      <a href="#/probar" data-s="probar">Probar</a>
      ${actual ? '<a href="#/mis-departamentos" data-s="propietario">Mis departamentos</a>' : '<a href="#/ingresar" data-s="propietario">Ingresar</a>'}
    </div>
    ${actual ? `<button class="menu-action" id="salir" title="${esc(actual.usuario.email)}">Salir</button>`
      : '<a class="menu-action" href="#/ingresar?modo=registro">Publicar mi depa</a>'}`;
  $$("#menu [data-s]").forEach((a) => a.classList.toggle("active", a.dataset.s === seccion));
  $("#salir")?.addEventListener("click", cerrarSesion);
}

async function navegar() {
  const [ruta, consulta = ""] = (location.hash.slice(1) || "/").split("?");
  const params = new URLSearchParams(consulta);
  const main = $("#vista");
  const encontrada = RUTAS.find(([patron]) => patron.test(ruta));
  $("#menu").classList.remove("open");
  $("#menu-toggle").setAttribute("aria-expanded", "false");
  if (!encontrada) {
    menu(null);
    return vistaNoEncontrada(main);
  }
  const [patron, vista, privada, seccion] = encontrada;
  if (privada && !sesion()) {
    location.hash = "#/ingresar?siguiente=" + encodeURIComponent("#" + ruta);
    return;
  }
  menu(seccion);
  document.body.dataset.vista = seccion;
  window.scrollTo(0, 0);
  try {
    await vista(main, params, ...(ruta.match(patron).slice(1)));
    activarMovimiento(main);
  } catch (error) {
    if (error.estado === 401) {
      menu(seccion);
      location.hash = "#/ingresar?siguiente=" + encodeURIComponent("#" + ruta);
      return;
    }
    vistaError(main, error);
  }
}

$("#menu-toggle").addEventListener("click", (e) => {
  const abierto = $("#menu").classList.toggle("open");
  e.currentTarget.setAttribute("aria-expanded", String(abierto));
});
window.addEventListener("hashchange", navegar);
navegar();
