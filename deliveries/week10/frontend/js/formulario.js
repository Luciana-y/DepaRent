import { $, esc, titulo } from "./util.js";

/**
 * Formulario de características del departamento.
 * opciones: datos de /api/opciones · conNombre: pide un nombre (propietario) · conDemos: muestra casos de ejemplo.
 * Devuelve { leer, cargar } para leer los valores o rellenarlos.
 */
export function formularioVivienda(contenedor, opciones, { conNombre = false, conDemos = false, textoBoton = "Analizar" } = {}) {
  const numericos = Object.entries(opciones.limites).map(([campo, [min, max]]) => `
    <label class="field"><span>${esc(opciones.etiquetas[campo])}</span>
      <input name="${campo}" type="number" min="${min}" max="${max}" step="1" ${["area_total", "dormitorios", "banos"].includes(campo) ? "required" : ""}></label>`).join("");
  const amenidades = opciones.binarias.map((campo) => `
    <label class="field"><span>${esc(opciones.etiquetas[campo])}</span>
      <select name="${campo}"><option value="0">No</option><option value="1">Sí</option><option value="">No sé</option></select></label>`).join("");
  contenedor.innerHTML = `
    <form class="vivienda-form" novalidate>
      ${conNombre ? '<label class="field"><span>Nombre del departamento</span><input name="nombre" maxlength="80" placeholder="Ej.: Depa de Lince, piso 5" required></label>' : ""}
      ${conDemos ? `<label class="field"><span>Caso de ejemplo</span><select name="demo">${opciones.demos.map((d, i) => `<option value="${i}">${esc(d.nombre)}</option>`).join("")}</select></label>` : ""}
      <label class="field"><span>Distrito</span><select name="distrito_norm" required>
        ${opciones.distritos.map((d) => `<option value="${esc(d)}">${esc(titulo(d))}</option>`).join("")}</select></label>
      <div class="grid-2">${numericos}</div>
      <fieldset><legend>Amenidades</legend><div class="grid-2">${amenidades}</div></fieldset>
      <details class="ubicacion">
        <summary>Ubicación exacta (opcional)</summary>
        <p class="hint">Sin coordenadas usamos el centro aproximado del distrito. También puedes hacer clic en el mapa de accesibilidad.</p>
        <div class="grid-2">
          <label class="field"><span>Latitud</span><input name="latitud" type="number" step="0.000001" placeholder="-12.088"></label>
          <label class="field"><span>Longitud</span><input name="longitud" type="number" step="0.000001" placeholder="-77.034"></label>
        </div>
      </details>
      <button type="submit" class="btn primary block">${esc(textoBoton)}</button>
      <div class="form-msg"></div>
    </form>`;
  const form = $("form", contenedor);
  const campo = (nombre) => form.elements.namedItem(nombre);

  function cargar(vivienda, ubicacion = null, nombre = null) {
    for (const [clave, valor] of Object.entries(vivienda)) {
      if (campo(clave)) campo(clave).value = valor == null ? "" : valor;
    }
    campo("latitud").value = ubicacion?.latitud ?? "";
    campo("longitud").value = ubicacion?.longitud ?? "";
    if (conNombre && nombre != null) campo("nombre").value = nombre;
  }

  function leer() {
    const vivienda = { distrito_norm: campo("distrito_norm").value };
    for (const clave of Object.keys(opciones.limites)) {
      const texto = campo(clave).value.trim();
      vivienda[clave] = texto === "" ? null : Number(texto);
    }
    for (const clave of opciones.binarias) vivienda[clave] = campo(clave).value === "" ? null : Number(campo(clave).value);
    for (const clave of ["area_total", "dormitorios", "banos"]) {
      if (vivienda[clave] == null) throw new Error(`Completa: ${opciones.etiquetas[clave]}.`);
    }
    const lat = campo("latitud").value.trim(), lon = campo("longitud").value.trim();
    if ((lat === "") !== (lon === "")) throw new Error("Ingresa latitud y longitud, o deja ambas vacías.");
    const ubicacion = lat === "" ? null : { latitud: Number(lat), longitud: Number(lon) };
    return { vivienda, ubicacion, nombre: conNombre ? campo("nombre").value.trim() : null };
  }

  function fijarUbicacion(lat, lon) {
    campo("latitud").value = lat.toFixed(6);
    campo("longitud").value = lon.toFixed(6);
  }

  if (conDemos) {
    campo("demo").addEventListener("change", () => cargar(opciones.demos[Number(campo("demo").value)].entrada));
    cargar(opciones.demos[0].entrada);
  }
  return { form, leer, cargar, fijarUbicacion, mensaje: $(".form-msg", form), boton: $("button[type=submit]", form) };
}
