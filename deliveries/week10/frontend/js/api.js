const BASE = (window.DEPARENT_API_URL || "").replace(/\/$/, "");
const CLAVE = "deparent.sesion";
let memoria = null;

// La sesión se recuerda en este navegador; si el almacenamiento está bloqueado, dura solo esta pestaña.
export function sesion() {
  try {
    return JSON.parse(localStorage.getItem(CLAVE)) || memoria;
  } catch {
    return memoria;
  }
}

export function guardarSesion(datos) {
  memoria = datos;
  try {
    if (datos) localStorage.setItem(CLAVE, JSON.stringify(datos));
    else localStorage.removeItem(CLAVE);
  } catch {
    /* sin almacenamiento persistente */
  }
}

export class ErrorApi extends Error {
  constructor(mensaje, estado) {
    super(mensaje);
    this.estado = estado;
  }
}

export async function llamar(ruta, { metodo, cuerpo } = {}) {
  const cabeceras = {};
  const actual = sesion();
  if (actual?.token) cabeceras.Authorization = "Bearer " + actual.token;
  if (cuerpo !== undefined) cabeceras["Content-Type"] = "application/json";
  let respuesta;
  try {
    respuesta = await fetch(BASE + ruta, {
      method: metodo || (cuerpo === undefined ? "GET" : "POST"), headers: cabeceras,
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    });
  } catch {
    throw new ErrorApi("No se pudo conectar con el servidor de DepaRent. Revisa que la API esté encendida.", 0);
  }
  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    if (respuesta.status === 401) guardarSesion(null);
    const detalle = Array.isArray(datos.detail) ? datos.detail.map((d) => d.msg).join(" ") : datos.detail;
    throw new ErrorApi(detalle || "No se pudo completar la consulta.", respuesta.status);
  }
  return datos;
}

let opciones = null;
export async function obtenerOpciones() {
  opciones = opciones || await llamar("/api/opciones");
  return opciones;
}
