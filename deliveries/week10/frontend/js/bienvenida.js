import { llamar, sesion } from "./api.js";
import { esc, num, soles } from "./util.js";

/* Ventana de bienvenida que aparece una vez después de ingresar o crear la cuenta.
   Toma el foco (dialog modal), se cierra con Esc, con "Ahora no" o al elegir un camino. */

const CLAVE = "deparent.bienvenida";
let pendiente = false;

export function marcarBienvenida() {
  pendiente = true;
  try { sessionStorage.setItem(CLAVE, "1"); } catch { /* sin almacenamiento: basta la variable */ }
}

function tomarPendiente() {
  let hay = pendiente;
  try { hay = hay || sessionStorage.getItem(CLAVE) === "1"; sessionStorage.removeItem(CLAVE); } catch { /* idem */ }
  pendiente = false;
  return hay;
}

export async function mostrarBienvenida() {
  const actual = sesion();
  if (!tomarPendiente() || !actual || typeof HTMLDialogElement === "undefined") return;
  let perfil = null, deptos = [];
  try {
    [{ perfil }, deptos] = await Promise.all([llamar("/api/perfil"), llamar("/api/departamentos")]);
  } catch {
    return; // Si no carga, no interrumpimos: la persona ya está en la app.
  }
  const nombre = (actual.usuario?.nombre || "").trim().split(/\s+/)[0];
  const publicados = deptos.filter((d) => d.publicacion).length;

  const buscar = perfil
    ? { titulo: "Seguir buscando departamento",
        texto: `Ya sabemos lo que buscas${perfil.presupuesto_max ? ` (hasta ${soles(perfil.presupuesto_max)} al mes)` : ""}. Te mostramos los que mejor te calzan y puedes ordenarlos del más barato al más caro.`,
        boton: "Ver mis recomendados", href: "#/para-ti", extra: '<a class="link-btn" href="#/mi-perfil/editar">Cambiar lo que busco</a>' }
    : { titulo: "Busco un departamento",
        texto: "Respóndenos unas preguntas rápidas: para quién es, tu presupuesto y qué te importa. Con eso elegimos los departamentos que mejor te calzan.",
        boton: "Empezar a buscar", href: "#/mi-perfil/editar", extra: "" };
  const alquilar = deptos.length
    ? { titulo: "Mis departamentos",
        texto: `Tienes ${num(deptos.length)} ${deptos.length === 1 ? "departamento" : "departamentos"}${publicados ? `, ${num(publicados)} publicado${publicados > 1 ? "s" : ""}` : ", ninguno publicado"}. Revisa su precio, edítalos o publícalos.`,
        boton: "Ir a mis departamentos", href: "#/mis-departamentos" }
    : { titulo: "Quiero alquilar mi departamento",
        texto: "Te decimos cuánto debería costar según departamentos parecidos, y lo publicas al precio que elijas.",
        boton: "Agregar mi departamento", href: "#/mis-departamentos/nuevo" };

  const dialogo = document.createElement("dialog");
  dialogo.className = "bienvenida";
  dialogo.setAttribute("aria-labelledby", "bv-titulo");
  dialogo.setAttribute("aria-describedby", "bv-sub");
  dialogo.innerHTML = `
    <h2 id="bv-titulo">${nombre ? `Hola, ${esc(nombre)}` : "Hola"}. ¿Qué quieres hacer hoy?</h2>
    <p id="bv-sub" class="hint">Elige un camino; puedes cambiar cuando quieras desde el menú.</p>
    <div class="bv-opciones">
      ${[buscar, alquilar].map((o, i) => `<section class="bv-opcion">
        <h3>${esc(o.titulo)}</h3><p>${esc(o.texto)}</p>
        <div class="bv-acciones"><a class="btn ${i === 0 ? "primary" : ""}" href="${o.href}" data-ir>${esc(o.boton)}</a>${o.extra || ""}</div>
      </section>`).join("")}
    </div>
    <div class="bv-pie"><button class="btn ghost" type="button" data-cerrar>Ahora no</button></div>`;
  document.body.append(dialogo);
  const cerrar = () => dialogo.close();
  dialogo.addEventListener("close", () => dialogo.remove());
  dialogo.querySelector("[data-cerrar]").addEventListener("click", cerrar);
  dialogo.querySelectorAll("a").forEach((a) => a.addEventListener("click", cerrar));
  // Clic en el fondo oscurecido: cierra, igual que Esc.
  dialogo.addEventListener("click", (e) => { if (e.target === dialogo) cerrar(); });
  dialogo.showModal();
  dialogo.querySelector("[data-ir]").focus();
}
