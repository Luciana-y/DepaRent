import { llamar, obtenerOpciones, guardarSesion, sesion } from "./api.js";
import { mostrarAnalisis } from "./analisis.js";
import { formularioVivienda } from "./formulario.js";
import { $, $$, esc, num, pct, soles, titulo, conBoton, mensaje, ETIQUETAS_AMENIDAD } from "./util.js";

const irA = (ruta) => { location.hash = ruta; };
const banos = (n) => `${num(n)} ${n === 1 ? "baño" : "baños"}`;
const dorms = (n) => `${num(n)} dorm.`;
const filaTitulo = (h1, sub, acciones = "") =>
  `<div class="title-row"><div><h1>${h1}</h1>${sub ? `<p class="sub">${sub}</p>` : ""}</div>${acciones ? `<div class="title-actions">${acciones}</div>` : ""}</div>`;

/* ---------- Ingreso y registro ---------- */

export function vistaIngresar(lienzo, params) {
  if (sesion()) return irA("#/mis-departamentos");
  const registro = params.get("modo") === "registro";
  const siguiente = params.get("siguiente");
  const enlace = (modo) => `#/ingresar${modo ? "?modo=registro" : ""}${siguiente ? `${modo ? "&" : "?"}siguiente=${encodeURIComponent(siguiente)}` : ""}`;
  lienzo.innerHTML = `
    ${filaTitulo(registro ? "Crear cuenta" : "Ingresar", "Guarda tus departamentos, revisa su análisis y publícalos con el precio que elijas.")}
    <section class="panel auth-panel">
      <nav class="tabs" aria-label="Ingreso o registro">
        <a href="${enlace(false)}" ${registro ? "" : 'aria-current="page"'}>Ingresar</a>
        <a href="${enlace(true)}" ${registro ? 'aria-current="page"' : ""}>Crear cuenta</a>
      </nav>
      <form class="auth-form" novalidate>
        ${registro ? '<div class="field"><label for="a-nombre">Nombre</label><input class="input" id="a-nombre" name="nombre" autocomplete="name" required></div>' : ""}
        <div class="field"><label for="a-email">Correo</label><input class="input" id="a-email" name="email" type="email" autocomplete="email" required></div>
        <div class="field"><label for="a-pass">Contraseña</label><input class="input" id="a-pass" name="password" type="password" minlength="8"
          autocomplete="${registro ? "new-password" : "current-password"}" required>
          ${registro ? '<p class="hint">Mínimo 8 caracteres. Es un prototipo académico: no reutilices una contraseña importante.</p>' : ""}</div>
        <button class="btn primary block" type="submit">${registro ? "Crear cuenta" : "Ingresar"}</button>
        <div class="form-msg" role="alert"></div>
      </form>
    </section>`;
  const form = $(".auth-form", lienzo);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const r = await conBoton($("button", form), "Un momento…", () =>
        llamar(registro ? "/api/cuentas/registro" : "/api/cuentas/ingreso", { cuerpo: Object.fromEntries(new FormData(form)) }));
      guardarSesion({ token: r.token, usuario: r.usuario });
      irA(siguiente || "#/mis-departamentos");
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

/* ---------- Mis departamentos: ¿cuáles están publicados y a qué precio? ---------- */

export async function vistaMisDepartamentos(lienzo) {
  const accion = '<a class="btn primary" href="#/mis-departamentos/nuevo">Agregar departamento</a>';
  lienzo.innerHTML = filaTitulo("Mis departamentos", '<span class="skeleton">Cargando tus departamentos</span>', accion) + '<div data-lista></div>';
  const deptos = await llamar("/api/departamentos");
  const publicados = deptos.filter((d) => d.publicacion);
  const sub = deptos.length
    ? `${deptos.length} departamento${deptos.length > 1 ? "s" : ""} · ${publicados.length ? `${publicados.length} publicado${publicados.length > 1 ? "s" : ""} por ${soles(publicados.reduce((t, d) => t + d.publicacion.precio_soles, 0))} al mes en total` : "ninguno publicado todavía"}`
    : "Agrega el primero para ver su precio esperado y a cuánto publicarlo.";
  $(".title-row .sub", lienzo).textContent = sub;
  const grupos = { todos: deptos, publicados, borradores: deptos.filter((d) => !d.publicacion) };
  let filtro = "todos";
  const destino = $("[data-lista]", lienzo);
  function dibujar() {
    const filas = grupos[filtro];
    destino.innerHTML = `
      <div class="counts" role="group" aria-label="Filtrar por estado">
        ${[["todos", "Todos"], ["publicados", "Publicados"], ["borradores", "Borradores"]].map(([k, t]) =>
          `<button class="count" type="button" data-filtro="${k}" aria-pressed="${k === filtro}"><span>${t}</span><b>${grupos[k].length}</b></button>`).join("")}
      </div>
      <section class="panel" aria-label="Lista de departamentos">
        ${filas.length ? `<div class="table-wrap"><table class="list-table">
          <thead><tr><th>Departamento</th><th class="n">Precio esperado</th><th class="n">Sugerido</th><th>Estado</th><th class="n">Publicado a</th></tr></thead>
          <tbody>${filas.map(filaDepartamento).join("")}</tbody></table></div>`
          : `<div class="empty">${deptos.length ? `<p>${filtro === "publicados" ? "Ningún departamento publicado todavía. Ábrelo y elige un precio de publicación." : "No hay borradores: todos están publicados."}</p>`
            : '<p>Todavía no registras departamentos.</p><a class="btn primary" href="#/mis-departamentos/nuevo">Agregar mi primer departamento</a>'}</div>`}
      </section>`;
    $$("[data-filtro]", destino).forEach((b) => b.addEventListener("click", () => { filtro = b.dataset.filtro; dibujar(); }));
    $$("tr[data-href]", destino).forEach((tr) => tr.addEventListener("click", (e) => { if (!e.target.closest("a")) irA(tr.dataset.href); }));
  }
  dibujar();
}

function filaDepartamento(d) {
  const v = d.vivienda, r = d.resumen || {};
  return `<tr data-href="#/mis-departamentos/${d.id}">
    <td><a class="id" href="#/mis-departamentos/${d.id}">${esc(d.nombre)}</a>
      <span class="sub">${esc(titulo(v.distrito_norm))} · ${num(v.area_total)} m² · ${dorms(v.dormitorios)} · ${banos(v.banos)}</span></td>
    <td class="n more" data-label="Esperado">${soles(r.precio_estimado_soles)}</td>
    <td class="n more" data-label="Sugerido">${soles(r.precio_sugerido_soles)}<span class="sub">${esc(r.escenario_sugerido || "")}</span></td>
    <td class="more hide-phone"><span class="pill ${d.publicacion ? "pos" : ""}">${d.publicacion ? "Publicado" : "Borrador"}</span></td>
    <td class="n key">${d.publicacion ? `<b>${soles(d.publicacion.precio_soles)}</b>` : '<span class="dash">Sin publicar</span>'}</td>
  </tr>`;
}

/* ---------- Agregar departamento ---------- */

export async function vistaNuevoDepartamento(lienzo) {
  const op = await obtenerOpciones();
  lienzo.innerHTML = filaTitulo("Agregar departamento", "Con sus características calculamos el precio esperado, sus comparables y tres precios de publicación. Solo lo ven los inquilinos si lo publicas.")
    + '<section class="panel" data-form></section>';
  const f = formularioVivienda($("[data-form]", lienzo), op, { conNombre: true, conDemos: true, textoBoton: "Guardar y analizar",
    secundario: '<a class="btn" href="#/mis-departamentos">Cancelar</a>' });
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

/* ---------- Detalle: ¿a cuánto lo publico? ---------- */

function cabeceraObjeto(nombre, v, acciones, extra = "") {
  return `<section class="panel object-head">
    <div class="cover" aria-hidden="true">${num(v.area_total)}<br>m²</div>
    <div><h1>${esc(nombre)}</h1><p class="meta">${esc(titulo(v.distrito_norm))} · ${num(v.area_total)} m² · ${dorms(v.dormitorios)} · ${banos(v.banos)}${extra}</p></div>
    ${acciones ? `<div class="title-actions">${acciones}</div>` : ""}
  </section>`;
}

export async function vistaDetalleDepartamento(lienzo, params, id) {
  const op = await obtenerOpciones();
  lienzo.innerHTML = `<section class="panel object-head"><div class="cover" aria-hidden="true"></div><div><h1><span class="skeleton">Cargando departamento</span></h1></div></section>`;
  const { departamento: d, analisis: a } = await llamar(`/api/departamentos/${id}`);
  const sugerido = a.publicacion.escenarios.find((s) => s.sugerido);
  const acciones = d.publicacion
    ? `<span class="pill pos">Publicado a ${soles(d.publicacion.precio_soles)}</span><button class="btn" type="button" data-retirar>Retirar publicación</button>`
    : `<button class="btn primary" type="button" data-publicar-sugerido>Publicar a ${soles(sugerido.precio_soles)}</button>`;
  lienzo.innerHTML = `<p style="margin-bottom:12px"><a class="card-link" href="#/mis-departamentos">Mis departamentos</a></p>`
    + cabeceraObjeto(d.nombre, d.vivienda, acciones, d.publicacion ? ` · ${esc(d.publicacion.escenario)}` : " · borrador, no visible para inquilinos")
    + '<div class="pub-msg"></div><div data-analisis></div>';
  const recargar = () => vistaDetalleDepartamento(lienzo, params, id);
  const publicar = async (s) => {
    await llamar(`/api/departamentos/${id}/publicacion`, { cuerpo: { precio_soles: s.precio_soles, escenario: s.escenario } });
    await recargar();
  };
  let formulario = null;
  mostrarAnalisis($("[data-analisis]", lienzo), a, op, {
    publicacion: d.publicacion,
    alPublicar: publicar,
    alMoverUbicacion: (lat, lon) => formulario?.fijarUbicacion(lat, lon),
    extras: [["caracteristicas", "Características", (panel) => {
      panel.innerHTML = `<section class="panel" data-form></section>
        <div class="danger-zone"><p class="hint">Eliminar borra el departamento y su publicación.</p>
          <div class="confirm"><button class="btn danger" type="button" data-borrar>Eliminar departamento</button></div></div>`;
      formulario = formularioVivienda($("[data-form]", panel), op, { conNombre: true, textoBoton: "Guardar y recalcular" });
      formulario.cargar(d.vivienda, d.ubicacion, d.nombre);
      if (d.publicacion) formulario.mensaje.innerHTML = '<p class="hint">Si cambias las características, la publicación se retira porque su precio ya no aplica.</p>';
      formulario.form.addEventListener("submit", async (e) => {
        e.preventDefault();
        try {
          const { nombre, vivienda, ubicacion } = formulario.leer();
          await conBoton(formulario.boton, "Recalculando…", () => llamar(`/api/departamentos/${id}`, { metodo: "PUT", cuerpo: { nombre, vivienda, ubicacion } }));
          await recargar();
        } catch (err) {
          mensaje(formulario.mensaje, err.message);
        }
      });
      const zona = $(".confirm", panel);
      $("[data-borrar]", panel).addEventListener("click", () => {
        zona.innerHTML = `<span>¿Eliminar «${esc(d.nombre)}»? No se puede deshacer.</span>
          <button class="btn danger" type="button" data-confirmar>Sí, eliminar</button><button class="btn ghost" type="button" data-cancelar>Cancelar</button>`;
        $("[data-cancelar]", zona).addEventListener("click", () => recargar());
        $("[data-confirmar]", zona).addEventListener("click", async (e) => {
          await conBoton(e.currentTarget, "Eliminando…", () => llamar(`/api/departamentos/${id}`, { metodo: "DELETE" }));
          irA("#/mis-departamentos");
        });
      });
    }], ["interesados", `Interesados (${d.interesados.length})`, (panel) => {
      panel.innerHTML = `<section class="panel" aria-labelledby="t-int"><header><h2 id="t-int">Personas interesadas</h2>
        <span class="meta">${d.publicacion ? `Escriben desde la ficha pública: <a class="card-link" href="#/anuncio/d${d.id}">ver cómo la ven</a>` : "Publica el departamento para recibir mensajes"}</span></header>
        ${d.interesados.length ? `<div class="rows">${d.interesados.map((i) => `<div class="row" style="align-items:flex-start">
            <span>${esc(i.nombre)} · <a href="mailto:${esc(i.email)}">${esc(i.email)}</a><span class="sub">${esc(i.mensaje)}</span></span>
            <span class="hint num">${new Date(i.creado * 1000).toLocaleDateString("es-PE")}</span></div>`).join("")}</div>`
          : `<div class="empty"><p>${d.publicacion ? "Todavía nadie escribió. Los inquilinos te encuentran en la búsqueda." : "Aún no está publicado: nadie puede verlo ni escribirte."}</p></div>`}
      </section>`;
    }]],
  });
  $("[data-publicar-sugerido]", lienzo)?.addEventListener("click", (e) =>
    conBoton(e.currentTarget, "Publicando…", () => publicar(sugerido)).catch((err) => mensaje($(".pub-msg", lienzo), err.message)));
  $("[data-retirar]", lienzo)?.addEventListener("click", (e) =>
    conBoton(e.currentTarget, "Retirando…", async () => { await llamar(`/api/departamentos/${id}/publicacion`, { metodo: "DELETE" }); await recargar(); })
      .catch((err) => mensaje($(".pub-msg", lienzo), err.message)));
}

/* ---------- Probar sin cuenta ---------- */

export async function vistaProbar(lienzo) {
  const op = await obtenerOpciones();
  lienzo.innerHTML = filaTitulo("Probar el análisis", "Sin cuenta: elige un ejemplo o describe un departamento. Los resultados no se guardan.",
    sesion() ? "" : '<a class="btn" href="#/ingresar?modo=registro">Crear cuenta para guardar</a>')
    + '<section class="panel" data-form></section><div data-resultado style="margin-top:24px"></div>';
  const f = formularioVivienda($("[data-form]", lienzo), op, { conDemos: true, textoBoton: "Analizar" });
  const destino = $("[data-resultado]", lienzo);
  f.form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const { vivienda, ubicacion } = f.leer();
      const a = await conBoton(f.boton, "Analizando…", () => llamar("/api/analizar", { cuerpo: { vivienda, ubicacion } }));
      destino.innerHTML = cabeceraObjeto("Departamento de prueba", a.vivienda, "") + "<div data-analisis></div>";
      mostrarAnalisis($("[data-analisis]", destino), a, op, { alMoverUbicacion: (lat, lon) => f.fijarUbicacion(lat, lon) });
      destino.scrollIntoView({ block: "start" });
    } catch (err) {
      mensaje(f.mensaje, err.message);
    }
  });
}

/* ---------- Búsqueda para inquilinos: ¿cuáles valen lo que piden? ---------- */

export async function vistaBuscar(lienzo) {
  const op = await obtenerOpciones();
  const opcionesMin = Array.from({ length: 4 }, (_, i) => `<option value="${i + 1}">${i + 1} o más</option>`).join("");
  lienzo.innerHTML = `
    ${filaTitulo("Buscar departamentos", '<span data-hallazgo>Anuncios de septiembre de 2026 y departamentos publicados en DepaRent.</span>')}
    <form class="filters" novalidate>
      <div class="field"><label for="b-distrito">Distrito</label><select class="input" id="b-distrito" name="distrito"><option value="">Todos</option>
        ${op.distritos.filter((d) => d !== "otros").map((d) => `<option value="${esc(d)}">${esc(titulo(d))}</option>`).join("")}</select></div>
      <div class="field optional"><label for="b-max">Presupuesto máximo (S/)</label><input class="input num" id="b-max" name="precio_max" type="number" min="0" step="100" placeholder="Sin límite"></div>
      <div class="field optional"><label for="b-dorm">Dormitorios</label><select class="input" id="b-dorm" name="dormitorios_min"><option value="">Cualquiera</option>${opcionesMin}</select></div>
      <div class="field optional"><label for="b-orden">Ordenar</label><select class="input" id="b-orden" name="orden">
        <option value="precio">Precio: menor primero</option><option value="precio_desc">Precio: mayor primero</option>
        <option value="oportunidad">Más barato que el estimado</option><option value="area">Mayor área</option><option value="paradero">Más cerca de un paradero</option></select></div>
      <button class="btn" type="button" data-mas-filtros aria-expanded="false" aria-controls="mas-filtros">Más filtros</button>
      <span class="spacer"></span>
      <button class="btn primary" type="submit">Buscar</button>
    </form>
    <section class="panel" id="mas-filtros" hidden style="margin-bottom:16px">
      <div class="fields">
        <div class="field"><label for="b-min">Presupuesto mínimo (S/)</label><input class="input num" id="b-min" name="precio_min" type="number" min="0" step="100"></div>
        <div class="field"><label for="b-banos">Baños</label><select class="input" id="b-banos" name="banos_min"><option value="">Cualquiera</option>${opcionesMin}</select></div>
        <div class="field"><label for="b-amin">Área mínima (m²)</label><input class="input num" id="b-amin" name="area_min" type="number" min="0" step="5"></div>
        <div class="field"><label for="b-amax">Área máxima (m²)</label><input class="input num" id="b-amax" name="area_max" type="number" min="0" step="5"></div>
        <div class="field"><label for="b-par">Paradero de transporte</label><select class="input" id="b-par" name="paradero_max_m"><option value="">Sin preferencia</option>
          <option value="300">A 300 m o menos</option><option value="500">A 500 m o menos</option><option value="1000">A 1 km o menos</option></select></div>
        <fieldset class="field wide" style="border:0;padding:0;margin:0"><legend class="hint" style="margin-bottom:6px">Debe tener</legend>
          <div style="display:flex;flex-wrap:wrap;gap:14px">${op.binarias.map((b) => `<label style="display:flex;gap:6px;align-items:center;font-weight:400"><input type="checkbox" name="amenidades" value="${b}">${esc(ETIQUETAS_AMENIDAD[b])}</label>`).join("")}</div>
        </fieldset>
      </div>
    </section>
    <div data-resultados></div>`;
  const form = $(".filters", lienzo), extra = $("#mas-filtros", lienzo), destino = $("[data-resultados]", lienzo);
  let limite = 24, valoracion = null;
  $("[data-mas-filtros]", lienzo).addEventListener("click", (e) => {
    extra.hidden = !extra.hidden;
    form.classList.toggle("expand", !extra.hidden);
    e.currentTarget.setAttribute("aria-expanded", String(!extra.hidden));
  });

  function filtros() {
    const valor = (sel) => $(sel, lienzo).value;
    const numero = (sel) => (valor(sel) === "" ? null : Number(valor(sel)));
    return {
      distritos: valor("#b-distrito") ? [valor("#b-distrito")] : [], orden: valor("#b-orden"), limite, valoracion,
      precio_max: numero("#b-max"), precio_min: numero("#b-min"), dormitorios_min: numero("#b-dorm"), banos_min: numero("#b-banos"),
      area_min: numero("#b-amin"), area_max: numero("#b-amax"), paradero_max_m: numero("#b-par"),
      amenidades: $$('#mas-filtros input[name="amenidades"]:checked', lienzo).map((c) => c.value),
    };
  }

  async function ejecutar() {
    destino.setAttribute("aria-busy", "true");
    try {
      const r = await llamar("/api/buscar", { cuerpo: filtros() });
      destino.innerHTML = resultadosBusqueda(r, valoracion);
      const total = Object.values(r.conteos).reduce((a, b) => a + b, 0);
      $("[data-hallazgo]", lienzo).textContent = total
        ? `${num(total)} departamentos con estos filtros · ${num(r.conteos.por_debajo)} piden menos de lo que estima el modelo.`
        : "Ningún departamento con estos filtros.";
      $$("[data-valoracion]", destino).forEach((b) => b.addEventListener("click", () => {
        valoracion = b.dataset.valoracion || null; limite = 24; ejecutar();
      }));
      $("[data-mas]", destino)?.addEventListener("click", () => { limite = Math.min(60, limite + 24); ejecutar(); });
      $$("tr[data-href]", destino).forEach((tr) => tr.addEventListener("click", (e) => { if (!e.target.closest("a")) irA(tr.dataset.href); }));
    } catch (err) {
      destino.innerHTML = `<section class="panel"><div class="empty"><p>No pudimos cargar la búsqueda. ${esc(err.message)}</p><button class="btn" type="button" data-reintentar>Reintentar</button></div></section>`;
      $("[data-reintentar]", destino).addEventListener("click", ejecutar);
    } finally {
      destino.removeAttribute("aria-busy");
    }
  }
  form.addEventListener("submit", (e) => { e.preventDefault(); limite = 24; ejecutar(); });
  extra.addEventListener("change", () => { limite = 24; ejecutar(); });
  ejecutar();
}

function resultadosBusqueda(r, valoracion) {
  const total = Object.values(r.conteos).reduce((a, b) => a + b, 0);
  const tarjetas = [["", "Todos", total], ["por_debajo", "Por debajo del estimado", r.conteos.por_debajo],
    ["en_linea", "En línea con el estimado", r.conteos.en_linea], ["por_encima", "Por encima del estimado", r.conteos.por_encima]];
  const pill = (x) => (x.valoracion.startsWith("Por debajo") ? "pos" : x.valoracion.startsWith("Por encima") ? "warn" : "");
  return `
    <div class="counts" role="group" aria-label="Filtrar por precio frente al estimado">
      ${tarjetas.map(([k, t, n]) => `<button class="count" type="button" data-valoracion="${k}" aria-pressed="${(valoracion || "") === k}"><span>${t}</span><b>${num(n)}</b></button>`).join("")}
    </div>
    <section class="panel" aria-label="Resultados">
      ${r.total ? `<div class="table-wrap"><table class="list-table">
        <thead><tr><th>Departamento</th><th class="n">Área</th><th class="n">Paradero</th><th class="n">Estimado</th><th class="n">Frente al estimado</th><th class="n">Precio</th></tr></thead>
        <tbody>${r.resultados.map((x) => `<tr data-href="#/anuncio/${x.id}">
          <td><a class="id" href="#/anuncio/${x.id}">${x.nombre ? esc(x.nombre) : `${dorms(x.dormitorios)} · ${banos(x.banos)}`}</a>
            <span class="sub">${esc(titulo(x.distrito))} · ${esc(x.perfil)}${x.origen === "Publicado en DepaRent" ? " · publicado en DepaRent" : ""}${x.amenidades.length ? " · " + x.amenidades.map((a) => ETIQUETAS_AMENIDAD[a].toLowerCase()).join(", ") : ""}</span></td>
          <td class="n more" data-label="Área">${num(x.area_total)} m²</td>
          <td class="n more" data-label="Paradero a">${num(x.dist_paradero_min_m)} m</td>
          <td class="n more" data-label="Estimado">${soles(x.precio_estimado_soles)}</td>
          <td class="n more" data-label="Frente al estimado"><span class="pill ${pill(x)}">${pct(x.diferencia_estimado_porcentaje)}</span></td>
          <td class="n key"><b>${soles(x.precio_soles)}</b></td></tr>`).join("")}</tbody>
      </table></div>
      <div class="list-foot"><span>1 a ${r.resultados.length} de ${num(r.total)}</span>
        ${r.resultados.length < Math.min(r.total, 60) ? `<button class="btn" type="button" data-mas>Mostrar ${Math.min(24, Math.min(r.total, 60) - r.resultados.length)} más</button>` : ""}</div>`
      : '<div class="empty"><p>Ningún departamento con estos filtros. Prueba ampliar el presupuesto, quitar amenidades o cambiar el distrito.</p></div>'}
      <p class="panel-note">${esc(r.aviso)} El porcentaje compara el precio pedido con el que estima el modelo para esas características.</p>
    </section>`;
}

/* ---------- Errores ---------- */

export function vistaNoEncontrada(lienzo) {
  lienzo.innerHTML = filaTitulo("Página no encontrada", "La dirección no corresponde a ninguna pantalla de DepaRent.")
    + '<section class="panel"><div class="empty"><a class="btn primary" href="#/">Volver al inicio</a></div></section>';
}

export function vistaError(lienzo, error) {
  lienzo.innerHTML = filaTitulo("No pudimos cargar esta pantalla", esc(error.message))
    + `<section class="panel"><div class="empty"><p>Si trabajas en local, inicia la API con <code>python -m uvicorn api:app --port 8000</code> desde <code>deliveries/week10/code</code>.</p>
      <button class="btn" type="button" data-recargar>Reintentar</button></div></section>`;
  $("[data-recargar]", lienzo).addEventListener("click", () => location.reload());
}
