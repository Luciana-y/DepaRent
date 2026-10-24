import { $, esc, titulo } from "./util.js";

const GRUPOS = [
  ["Tamaño", "Lo que más pesa en el precio.", ["area_total", "dormitorios", "banos", "estacionamientos"]],
  ["Edificio", "Si no lo sabes, déjalo vacío: el modelo usa la mediana de los anuncios.", ["antiguedad", "mantenimiento"]],
];

/**
 * Formulario de características del departamento, con la forma de una pantalla de ajustes.
 * opciones: datos de /api/opciones · conNombre: pide un nombre (propietario) · conDemos: casos de ejemplo
 * compacto: etiquetas sobre los campos (para paneles angostos). Devuelve { leer, cargar, ... }.
 */
export function formularioVivienda(contenedor, opciones, { conNombre = false, conDemos = false, compacto = false, textoBoton = "Analizar", secundario = "" } = {}) {
  const numerico = (campo) => {
    const [min, max] = opciones.limites[campo];
    const obligatorio = ["area_total", "dormitorios", "banos"].includes(campo);
    return `<div class="field"><label for="f-${campo}">${esc(opciones.etiquetas[campo])}</label>
      <input class="input num" id="f-${campo}" name="${campo}" type="number" inputmode="numeric" min="${min}" max="${max}" step="1" ${obligatorio ? "required" : 'placeholder="No sé"'}></div>`;
  };
  const amenidad = (campo) => `<div class="field"><label for="f-${campo}">${esc(opciones.etiquetas[campo])}</label>
    <select class="input" id="f-${campo}" name="${campo}"><option value="0">No</option><option value="1">Sí</option><option value="">No sé</option></select></div>`;
  const grupo = (nombre, ayuda, cuerpo) => `<section class="form-group"><div><h2>${nombre}</h2>${ayuda ? `<p class="hint">${ayuda}</p>` : ""}</div><div class="fields">${cuerpo}</div></section>`;
  contenedor.innerHTML = `
    <form class="vivienda-form ${compacto ? "compact" : ""}" novalidate>
      <div class="form-groups">
        ${grupo("Departamento", conDemos ? "Empieza desde un ejemplo y cámbialo." : "", `
          ${conDemos ? `<div class="field wide"><label for="f-demo">Caso de ejemplo</label><select class="input" id="f-demo" name="demo">${opciones.demos.map((d, i) => `<option value="${i}">${esc(d.nombre)}</option>`).join("")}</select></div>` : ""}
          ${conNombre ? '<div class="field wide"><label for="f-nombre">Nombre</label><input class="input" id="f-nombre" name="nombre" maxlength="80" placeholder="Depa de Lince, piso 5" required></div>' : ""}
          <div class="field wide"><label for="f-distrito">Distrito</label><select class="input" id="f-distrito" name="distrito_norm" required>
            ${opciones.distritos.map((d) => `<option value="${esc(d)}">${esc(titulo(d))}</option>`).join("")}</select></div>`)}
        ${GRUPOS.map(([nombre, ayuda, campos]) => grupo(nombre, ayuda, campos.map(numerico).join(""))).join("")}
        ${grupo("Amenidades", "Las que el anuncio diría.", opciones.binarias.map(amenidad).join(""))}
        ${grupo("Ubicación", "Opcional. Sin coordenadas usamos el centro del distrito; también puedes hacer clic en el mapa.", `
          <div class="field"><label for="f-latitud">Latitud</label><input class="input num" id="f-latitud" name="latitud" type="number" step="0.000001" placeholder="-12.088"></div>
          <div class="field"><label for="f-longitud">Longitud</label><input class="input num" id="f-longitud" name="longitud" type="number" step="0.000001" placeholder="-77.034"></div>`)}
      </div>
      <div class="form-actions">${secundario}<button type="submit" class="btn primary">${esc(textoBoton)}</button></div>
      <div class="form-msg" role="alert"></div>
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
