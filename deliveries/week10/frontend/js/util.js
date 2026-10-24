export const $ = (selector, raiz = document) => raiz.querySelector(selector);
export const $$ = (selector, raiz = document) => [...raiz.querySelectorAll(selector)];

export const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
export const num = (v, dec = 0) => v == null ? "—" : Number(v).toLocaleString("es-PE", { maximumFractionDigits: dec });
export const soles = (v, dec = 0) => v == null ? "—" :
  "S/ " + Number(v).toLocaleString("es-PE", { minimumFractionDigits: dec, maximumFractionDigits: dec });
export const pct = (v) => (v > 0 ? "+" : "") + num(v, 1) + "%";
export const titulo = (t) => String(t ?? "").replace(/\b\p{L}/gu, (c) => c.toUpperCase());

export const ETIQUETAS_AMENIDAD = {
  ascensor: "Ascensor", balcon: "Balcón", terraza: "Terraza", piscina: "Piscina", gimnasio: "Gimnasio", pet_friendly: "Admite mascotas",
};

export function html(cadena) {
  const plantilla = document.createElement("template");
  plantilla.innerHTML = cadena.trim();
  return plantilla.content;
}

export function tabla(filas, columnas) {
  columnas = columnas || Object.keys(filas[0] || {});
  const celda = (v) => esc(typeof v === "number" ? num(v, 2) : v ?? "—");
  return `<div class="table-wrap"><table><thead><tr>${columnas.map((c) => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>` +
    filas.map((f) => "<tr>" + columnas.map((c) => `<td>${celda(f[c])}</td>`).join("") + "</tr>").join("") +
    "</tbody></table></div>";
}

export function mensaje(contenedor, texto, tipo = "error") {
  contenedor.innerHTML = texto ? `<p class="${tipo}" role="alert">${esc(texto)}</p>` : "";
}

export async function conBoton(boton, textoOcupado, tarea) {
  const original = boton.textContent;
  boton.disabled = true;
  boton.textContent = textoOcupado;
  try {
    return await tarea();
  } finally {
    boton.disabled = false;
    boton.textContent = original;
  }
}
