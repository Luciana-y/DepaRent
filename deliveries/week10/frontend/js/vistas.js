import { llamar, obtenerOpciones, guardarSesion, sesion } from "./api.js";
import { mostrarAnalisis } from "./analisis.js";
import { formularioVivienda } from "./formulario.js";
import { $, esc, num, pct, soles, titulo, conBoton, mensaje, ETIQUETAS_AMENIDAD } from "./util.js";

const irA = (ruta) => { location.hash = ruta; };

/* ---------- Ingreso y registro ---------- */

export function vistaIngresar(main, params) {
  if (sesion()) return irA("#/mis-departamentos");
  const modo = params.get("modo") === "registro" ? "registro" : "ingreso";
  main.innerHTML = `
    <section class="container auth">
      <div class="auth-side">
        <p class="eyebrow light">Para propietarios</p>
        <h1>Tu cartera de departamentos, con precio respaldado por datos</h1>
        <ul class="checks">
          <li>Guarda tus departamentos y vuelve a su análisis cuando quieras.</li>
          <li>Compara con anuncios parecidos y revisa la tendencia de tu distrito.</li>
          <li>Publica con un precio competitivo, equilibrado o de renta superior.</li>
        </ul>
      </div>
      <div class="card auth-card">
        <nav class="tabs">
          <a class="tab ${modo === "ingreso" ? "active" : ""}" href="#/ingresar">Ingresar</a>
          <a class="tab ${modo === "registro" ? "active" : ""}" href="#/ingresar?modo=registro">Crear cuenta</a>
        </nav>
        <form class="auth-form" novalidate>
          ${modo === "registro" ? '<label class="field"><span>Nombre</span><input name="nombre" autocomplete="name" required></label>' : ""}
          <label class="field"><span>Correo</span><input name="email" type="email" autocomplete="email" required></label>
          <label class="field"><span>Contraseña</span><input name="password" type="password" minlength="8"
            autocomplete="${modo === "registro" ? "new-password" : "current-password"}" required></label>
          ${modo === "registro" ? '<p class="hint">Mínimo 8 caracteres. Es un prototipo académico: no reutilices una contraseña importante.</p>' : ""}
          <button class="btn primary block" type="submit">${modo === "registro" ? "Crear cuenta" : "Ingresar"}</button>
          <div class="form-msg"></div>
        </form>
      </div>
    </section>`;
  const form = $(".auth-form", main);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const datos = Object.fromEntries(new FormData(form));
    try {
      const r = await conBoton($("button", form), "Un momento…", () =>
        llamar(modo === "registro" ? "/api/cuentas/registro" : "/api/cuentas/ingreso", { cuerpo: datos }));
      guardarSesion({ token: r.token, usuario: r.usuario });
      irA(params.get("siguiente") || "#/mis-departamentos");
    } catch (err) {
      mensaje($(".form-msg", form), err.message);
    }
  });
}

export async function cerrarSesion() {
  await llamar("/api/cuentas/salida", { cuerpo: {} }).catch(() => null);
  guardarSesion(null);
  irA("#/");
}

/* ---------- Propietario ---------- */

function encabezado(tituloTexto, subtitulo, acciones = "") {
  return `<div class="page-head"><div><h1>${tituloTexto}</h1>${subtitulo ? `<p class="muted">${subtitulo}</p>` : ""}</div>${acciones}</div>`;
}

export async function vistaMisDepartamentos(main) {
  const usuario = sesion().usuario;
  main.innerHTML = `<section class="container page">${encabezado(`Hola, ${esc(usuario.nombre.split(" ")[0])}`, "Tus departamentos registrados en DepaRent",
    '<a class="btn primary" href="#/mis-departamentos/nuevo">+ Agregar departamento</a>')}<div class="lista-deptos"><p class="muted">Cargando…</p></div></section>`;
  const lista = $(".lista-deptos", main);
  const deptos = await llamar("/api/departamentos");
  if (!deptos.length) {
    lista.innerHTML = `<div class="card empty-state">
      <div class="empty-icon" aria-hidden="true">🏠</div>
      <h2>Todavía no registras departamentos</h2>
      <p>Agrega el primero: con sus características calculamos el precio esperado, sus comparables y tres precios de publicación.</p>
      <a class="btn primary" href="#/mis-departamentos/nuevo">Agregar mi primer departamento</a></div>`;
    return;
  }
  const publicados = deptos.filter((d) => d.publicacion).length;
  lista.innerHTML = `<div class="summary-bar"><span><b>${deptos.length}</b> departamento${deptos.length > 1 ? "s" : ""}</span>
      <span><b>${publicados}</b> publicado${publicados === 1 ? "" : "s"}</span></div>
    <div class="cards-grid">${deptos.map(tarjetaDepartamento).join("")}</div>`;
}

function tarjetaDepartamento(d) {
  const v = d.vivienda, r = d.resumen || {};
  return `<a class="card depto-card" href="#/mis-departamentos/${d.id}">
    <div class="row-between"><h3>${esc(d.nombre)}</h3>
      <span class="status ${d.publicacion ? "on" : ""}">${d.publicacion ? "Publicado" : "Borrador"}</span></div>
    <p class="muted">${esc(titulo(v.distrito_norm))} · ${num(v.area_total)} m² · ${v.dormitorios} dorm. · ${v.banos} baños</p>
    <div class="kpis two">
      <div class="kpi"><span>Precio esperado</span><b>${soles(r.precio_estimado_soles)}</b></div>
      <div class="kpi"><span>${d.publicacion ? "Publicado a" : "Sugerido (" + esc(r.escenario_sugerido || "—") + ")"}</span>
        <b>${soles(d.publicacion ? d.publicacion.precio_soles : r.precio_sugerido_soles)}</b></div>
    </div>
    <p class="hint">${esc(r.perfil || "")} · accesibilidad ${esc((r.accesibilidad || "").toLowerCase())} · tendencia ${esc((r.tendencia || "").toLowerCase())}</p>
  </a>`;
}

export async function vistaNuevoDepartamento(main) {
  const op = await obtenerOpciones();
  main.innerHTML = `<section class="container page">${encabezado("Agregar departamento", "Completa sus características; puedes empezar desde un ejemplo y editarlo.")}
    <div class="work-grid"><aside class="card form-card"></aside>
      <div class="card info-card"><h2>Qué vas a obtener</h2><ol class="steps">
        <li><b>Precio esperado</b> con un rango de incertidumbre.</li>
        <li><b>Tres precios de publicación</b> y uno sugerido.</li>
        <li><b>8 anuncios comparables</b> y tu perfil competitivo.</li>
        <li><b>Accesibilidad</b> a paraderos y <b>tendencia</b> del distrito.</li>
        <li><b>Simulador</b> de mejoras.</li></ol>
        <p class="hint">Guardamos el departamento en tu cuenta. Solo se muestra a inquilinos si decides publicarlo.</p></div></div></section>`;
  const f = formularioVivienda($(".form-card", main), op, { conNombre: true, conDemos: true, textoBoton: "Guardar y analizar" });
  f.form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const { nombre, vivienda, ubicacion } = f.leer();
      const r = await conBoton(f.boton, "Analizando…", () => llamar("/api/departamentos", { cuerpo: { nombre, vivienda, ubicacion } }));
      irA(`#/mis-departamentos/${r.departamento.id}`);
    } catch (err) {
      mensaje(f.mensaje, err.message);
    }
  });
}

export async function vistaDetalleDepartamento(main, params, id) {
  const op = await obtenerOpciones();
  main.innerHTML = `<section class="container page"><p class="muted">Cargando análisis…</p></section>`;
  const { departamento: d, analisis } = await llamar(`/api/departamentos/${id}`);
  main.innerHTML = `<section class="container page">
    <a class="back" href="#/mis-departamentos">← Mis departamentos</a>
    ${encabezado(esc(d.nombre), `${esc(titulo(d.vivienda.distrito_norm))} · ${num(d.vivienda.area_total)} m² · ${d.publicacion ? "publicado" : "borrador, no visible para inquilinos"}`)}
    <div class="work-grid">
      <aside class="card form-card">
        <h2>Características</h2><div class="form-slot"></div>
        <div class="danger-zone"><button class="btn small ghost danger" data-borrar>Eliminar departamento</button><div class="confirm" hidden>
          <p>¿Eliminar «${esc(d.nombre)}»? No se puede deshacer.</p>
          <button class="btn small danger-solid" data-confirmar>Sí, eliminar</button> <button class="btn small ghost" data-cancelar>Cancelar</button></div></div>
      </aside>
      <div class="analysis-slot"></div>
    </div></section>`;
  const f = formularioVivienda($(".form-slot", main), op, { conNombre: true, textoBoton: "Guardar y recalcular" });
  f.cargar(d.vivienda, d.ubicacion, d.nombre);
  if (d.publicacion) f.mensaje.innerHTML = '<p class="hint">Si cambias las características, la publicación se retira porque su precio ya no aplica.</p>';
  const recargar = () => vistaDetalleDepartamento(main, params, id);
  mostrarAnalisis($(".analysis-slot", main), analisis, op, {
    publicacion: d.publicacion,
    alMoverUbicacion: (lat, lon) => f.fijarUbicacion(lat, lon),
    alPublicar: async (s) => { await llamar(`/api/departamentos/${id}/publicacion`, { cuerpo: { precio_soles: s.precio_soles, escenario: s.escenario } }); await recargar(); },
    alRetirar: async () => { await llamar(`/api/departamentos/${id}/publicacion`, { metodo: "DELETE" }); await recargar(); },
  });
  f.form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const { nombre, vivienda, ubicacion } = f.leer();
      await conBoton(f.boton, "Recalculando…", () => llamar(`/api/departamentos/${id}`, { metodo: "PUT", cuerpo: { nombre, vivienda, ubicacion } }));
      await recargar();
    } catch (err) {
      mensaje(f.mensaje, err.message);
    }
  });
  const confirmar = $(".confirm", main);
  $("[data-borrar]", main).addEventListener("click", () => { confirmar.hidden = false; });
  $("[data-cancelar]", main).addEventListener("click", () => { confirmar.hidden = true; });
  $("[data-confirmar]", main).addEventListener("click", async (e) => {
    await conBoton(e.currentTarget, "Eliminando…", () => llamar(`/api/departamentos/${id}`, { metodo: "DELETE" }));
    irA("#/mis-departamentos");
  });
}

/* ---------- Probar sin cuenta ---------- */

export async function vistaProbar(main) {
  const op = await obtenerOpciones();
  main.innerHTML = `<section class="container page">${encabezado("Prueba el análisis", "Sin cuenta: los resultados no se guardan.",
    sesion() ? "" : '<a class="btn" href="#/ingresar?modo=registro">Crear cuenta para guardar</a>')}
    <div class="work-grid"><aside class="card form-card"></aside>
      <div class="analysis-slot"><div class="card empty-state small"><h2>Elige un caso o describe un departamento</h2>
        <p>Pulsa «Analizar» para ver el precio esperado, los precios de publicación, comparables, accesibilidad y tendencia.</p></div></div></div></section>`;
  const f = formularioVivienda($(".form-card", main), op, { conDemos: true, textoBoton: "Analizar" });
  const destino = $(".analysis-slot", main);
  f.form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const { vivienda, ubicacion } = f.leer();
      const a = await conBoton(f.boton, "Analizando…", () => llamar("/api/analizar", { cuerpo: { vivienda, ubicacion } }));
      mostrarAnalisis(destino, a, op, { alMoverUbicacion: (lat, lon) => f.fijarUbicacion(lat, lon) });
    } catch (err) {
      mensaje(f.mensaje, err.message);
    }
  });
}

/* ---------- Búsqueda para inquilinos ---------- */

export async function vistaBuscar(main) {
  const op = await obtenerOpciones();
  const opcionesMin = (etiqueta) => `<option value="">${etiqueta}</option>` + [1, 2, 3, 4].map((n) => `<option value="${n}">${n} o más</option>`).join("");
  main.innerHTML = `<section class="container page">
    ${encabezado("Busca tu próximo departamento", "Filtra por lo que necesitas y compara cada precio con lo que estima nuestro modelo.")}
    <div class="work-grid">
      <aside class="card form-card">
        <form class="filtros" novalidate>
          <fieldset><legend>Distritos</legend><div class="chips-scroll">
            ${op.distritos.filter((d) => d !== "otros").map((d) => `<label class="chip"><input type="checkbox" name="distritos" value="${esc(d)}"><span>${esc(titulo(d))}</span></label>`).join("")}
          </div><p class="hint">Sin selección se busca en todos.</p></fieldset>
          <div class="grid-2">
            <label class="field"><span>Presupuesto mínimo (S/)</span><input name="precio_min" type="number" min="0" step="50"></label>
            <label class="field"><span>Presupuesto máximo (S/)</span><input name="precio_max" type="number" min="0" step="50" placeholder="Ej.: 3000"></label>
            <label class="field"><span>Dormitorios</span><select name="dormitorios_min">${opcionesMin("Cualquiera")}</select></label>
            <label class="field"><span>Baños</span><select name="banos_min">${opcionesMin("Cualquiera")}</select></label>
            <label class="field"><span>Área mínima (m²)</span><input name="area_min" type="number" min="0" step="5"></label>
            <label class="field"><span>Área máxima (m²)</span><input name="area_max" type="number" min="0" step="5"></label>
          </div>
          <label class="field"><span>Paradero de transporte</span><select name="paradero_max_m">
            <option value="">Sin preferencia</option><option value="300">A 300 m o menos</option><option value="500">A 500 m o menos</option><option value="1000">A 1 km o menos</option></select></label>
          <fieldset><legend>Debe tener</legend><div class="chips">
            ${op.binarias.map((b) => `<label class="chip"><input type="checkbox" name="amenidades" value="${b}"><span>${esc(ETIQUETAS_AMENIDAD[b])}</span></label>`).join("")}
          </div></fieldset>
          <label class="field"><span>Ordenar por</span><select name="orden">
            <option value="precio">Precio: menor a mayor</option><option value="precio_desc">Precio: mayor a menor</option>
            <option value="oportunidad">Mejor precio frente al estimado</option><option value="area">Mayor área</option><option value="paradero">Más cerca de un paradero</option></select></label>
          <button class="btn primary block" type="submit">Buscar</button>
          <button class="btn ghost block" type="reset">Limpiar filtros</button>
        </form>
      </aside>
      <div class="resultados-busqueda"></div>
    </div></section>`;
  const form = $(".filtros", main), destino = $(".resultados-busqueda", main);
  let limite = 24;

  function filtros() {
    const datos = new FormData(form);
    const numero = (k) => (datos.get(k) === "" || datos.get(k) == null ? null : Number(datos.get(k)));
    return { distritos: datos.getAll("distritos"), amenidades: datos.getAll("amenidades"), orden: datos.get("orden"), limite,
      ...Object.fromEntries(["precio_min", "precio_max", "area_min", "area_max", "dormitorios_min", "banos_min", "paradero_max_m"].map((k) => [k, numero(k)])) };
  }

  async function ejecutar() {
    destino.innerHTML = '<p class="muted">Buscando…</p>';
    try {
      const r = await llamar("/api/buscar", { cuerpo: filtros() });
      destino.innerHTML = resultadosBusqueda(r);
      $("[data-mas]", destino)?.addEventListener("click", () => { limite = Math.min(60, limite + 24); ejecutar(); });
    } catch (err) {
      mensaje(destino, err.message);
    }
  }
  form.addEventListener("submit", (e) => { e.preventDefault(); limite = 24; ejecutar(); });
  form.addEventListener("reset", () => setTimeout(() => { limite = 24; ejecutar(); }, 0));
  ejecutar();
}

function resultadosBusqueda(r) {
  if (!r.total) {
    return `<div class="card empty-state small"><h2>No encontramos departamentos con esos filtros</h2><p>Prueba ampliar el presupuesto, quitar amenidades o sumar distritos.</p></div>`;
  }
  const s = r.resumen;
  return `<div class="summary-bar">
      <span><b>${num(r.total)}</b> departamentos</span>
      <span>Precio mediano <b>${soles(s.precio_mediana_soles)}</b></span>
      <span>La mitad central entre <b>${soles(s.precio_p25_soles)}</b> y <b>${soles(s.precio_p75_soles)}</b></span>
      <span><b>${num(s.por_debajo_del_estimado)}</b> por debajo del estimado</span>
    </div>
    <div class="cards-grid results-grid">${r.resultados.map(tarjetaResultado).join("")}</div>
    ${r.resultados.length < Math.min(r.total, 60) ? `<button class="btn block" data-mas>Ver más resultados</button>` : ""}
    <p class="note">${esc(r.aviso)}</p>`;
}

function tarjetaResultado(x) {
  const clase = x.valoracion.startsWith("Por debajo") ? "good" : x.valoracion.startsWith("Por encima") ? "high" : "fair";
  const propio = x.origen === "Publicado en DepaRent";
  return `<article class="card result-card ${propio ? "own" : ""}">
    <div class="row-between"><span class="origin ${propio ? "own" : ""}">${esc(x.origen)}</span><span class="valor ${clase}">${esc(x.valoracion)}</span></div>
    <h3>${x.nombre ? esc(x.nombre) : `${num(x.dormitorios)} dorm. · ${num(x.area_total)} m²`}</h3>
    <p class="muted">${esc(titulo(x.distrito))} · ${esc(x.perfil)}</p>
    <p class="price">${soles(x.precio_soles)}<small> /mes</small></p>
    <p class="hint">Estimado por el modelo: ${soles(x.precio_estimado_soles)} (${pct(x.diferencia_estimado_porcentaje)})</p>
    <ul class="facts">
      <li>${num(x.area_total)} m²</li><li>${num(x.dormitorios)} dorm.</li><li>${num(x.banos)} baños</li>
      ${x.antiguedad != null ? `<li>${num(x.antiguedad)} años</li>` : ""}
      ${x.mantenimiento != null ? `<li>Mant. ${soles(x.mantenimiento)}</li>` : ""}
      <li>Paradero a ${num(x.dist_paradero_min_m)} m</li>
    </ul>
    <div class="chips small">${x.amenidades.map((a) => `<span class="chip static">${esc(ETIQUETAS_AMENIDAD[a])}</span>`).join("")}</div>
  </article>`;
}

export function vistaNoEncontrada(main) {
  main.innerHTML = `<section class="container page"><div class="card empty-state"><h2>No encontramos esta página</h2><a class="btn primary" href="#/">Volver al inicio</a></div></section>`;
}

export function vistaError(main, error) {
  main.innerHTML = `<section class="container page"><div class="card empty-state"><h2>Algo salió mal</h2><p class="error">${esc(error.message)}</p>
    <p class="hint">Si trabajas en local, inicia la API con <code>python -m uvicorn api:app --port 8000</code> desde <code>deliveries/week10/code</code>.</p>
    <a class="btn" href="#/">Volver al inicio</a></div></section>`;
}

