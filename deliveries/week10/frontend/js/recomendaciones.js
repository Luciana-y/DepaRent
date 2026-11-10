import { llamar, obtenerOpciones } from "./api.js";
import { cerrarSesion } from "./vistas.js";
import { $, $$, esc, num, soles, titulo, conBoton, mensaje, ETIQUETAS_AMENIDAD } from "./util.js";

/* ---------- Inquilino (modelo 7): cuestionario → mi perfil → recomendaciones → guardados ----------
   El perfil y los guardados viven en la cuenta (API), así se ven desde cualquier dispositivo. */

const DESCRIPCION_HOGAR = {
  familia: "Pesan 3 dormitorios, área, juegos infantiles, áreas verdes, seguridad y cochera.",
  pareja: "Pesan 1 o 2 dormitorios, balcón o terraza, gimnasio y parrilla.",
  estudiante: "Pesan el paradero cercano, el tamaño justo y el coworking.",
  mascota: "Solo departamentos que admiten mascotas; pesan terraza y áreas verdes.",
  mayor: "Pesan el ascensor, el paradero cercano y la seguridad.",
};

const irA = (ruta) => { location.hash = ruta; };
const filaTitulo = (h1, sub, acciones = "") =>
  `<div class="title-row"><div><h1>${h1}</h1>${sub ? `<p class="sub">${sub}</p>` : ""}</div>${acciones ? `<div class="title-actions">${acciones}</div>` : ""}</div>`;

// El perfil que se envía al recomendador: sin los campos que solo sirven para mostrarlo u ordenar.
const paraRecomendar = ({ actualizado, lugar_nombre, orden, ...perfil }) => perfil;

// Cómo ordenar la lista de recomendados (se elige en el cuestionario y se puede cambiar en la lista).
const ORDENES = [
  ["afinidad", "Los que mejor me calzan"],
  ["precio", "Precio: del más barato al más caro"],
  ["precio_desc", "Precio: del más caro al más barato"],
  ["paradero", "Más cerca de un paradero"],
];
const NOMBRE_ORDEN = Object.fromEntries(ORDENES);
function ordenar(lista, orden) {
  const copia = [...lista];
  const valor = (x, k) => (x[k] == null ? Infinity : Number(x[k]));
  if (orden === "precio") copia.sort((a, b) => valor(a, "precio_soles") - valor(b, "precio_soles"));
  if (orden === "precio_desc") copia.sort((a, b) => valor(b, "precio_soles") - valor(a, "precio_soles"));
  if (orden === "paradero") copia.sort((a, b) => valor(a, "dist_paradero_min_m") - valor(b, "dist_paradero_min_m"));
  return copia;
}

/* ---------- 1. Cuestionario ---------- */

export async function vistaEditarPerfil(lienzo) {
  const [op, { perfil }] = await Promise.all([obtenerOpciones(), llamar("/api/perfil")]);
  const p = perfil || { hogar: "", prioridades: [], distritos: [] };
  const hogares = op.recomendador.hogares, prioridades = op.recomendador.prioridades;
  const distritos = op.distritos.filter((d) => d !== "otros");
  lienzo.innerHTML = `
    ${filaTitulo(perfil ? "Editar mi perfil" : "Cuéntanos qué buscas", "Con estas respuestas el sistema elige los departamentos del mercado que mejor te calzan.")}
    <form class="panel perfil-form" novalidate>
      <fieldset class="perfil-grupo"><legend>¿Para quién es el departamento?</legend>
        <div class="hogares">${Object.entries(hogares).map(([k, nombre]) => `
          <label class="hogar"><input type="radio" name="hogar" value="${k}" ${p.hogar === k ? "checked" : ""} required>
            <span><b>${esc(nombre)}</b><small>${esc(DESCRIPCION_HOGAR[k] || "")}</small></span></label>`).join("")}</div>
      </fieldset>
      <div class="fields">
        <div class="field"><label for="r-max">Presupuesto máximo (S/ al mes)</label>
          <input class="input num" id="r-max" name="presupuesto_max" type="number" min="300" max="50000" step="100" value="${p.presupuesto_max ?? ""}" placeholder="Por ejemplo 2500"></div>
        <div class="field optional"><label for="r-dorm">Dormitorios mínimos</label>
          <select class="input" id="r-dorm" name="dormitorios_min"><option value="">Según tu hogar</option>
          ${[1, 2, 3, 4].map((n) => `<option value="${n}" ${p.dormitorios_min === n ? "selected" : ""}>${n} o más</option>`).join("")}</select></div>
      </div>
      <fieldset class="perfil-grupo"><legend>¿Qué te importa más? <small>(hasta 3)</small></legend>
        <div class="chips">${Object.entries(prioridades).map(([k, nombre]) => `
          <label class="chip"><input type="checkbox" name="prioridades" value="${k}" ${p.prioridades?.includes(k) ? "checked" : ""}><span>${esc(nombre)}</span></label>`).join("")}</div>
      </fieldset>
      <fieldset class="perfil-grupo"><legend>Distritos que te interesan <small>(si no marcas ninguno, buscamos en todos)</small></legend>
        <div class="chips">${distritos.map((d) => `
          <label class="chip"><input type="checkbox" name="distritos" value="${esc(d)}" ${p.distritos?.includes(d) ? "checked" : ""}><span>${esc(titulo(d))}</span></label>`).join("")}</div>
      </fieldset>
      <fieldset class="perfil-grupo"><legend>¿Cómo quieres ver los resultados?</legend>
        <div class="chips">${ORDENES.map(([k, nombre]) => `
          <label class="chip"><input type="radio" name="orden" value="${k}" ${(p.orden || "afinidad") === k ? "checked" : ""}><span>${esc(nombre)}</span></label>`).join("")}</div>
      </fieldset>
      <fieldset class="perfil-grupo"><legend>¿Dónde trabajas o estudias? <small>(opcional: acerca las recomendaciones)</small></legend>
        <div class="search-row"><input class="input" id="r-lugar" placeholder="Por ejemplo: Av. Javier Prado Este 4600, Surco" value="${esc(p.lugar_nombre || "")}" autocomplete="off">
          <button class="btn" type="button" data-buscar-lugar>Buscar</button>
          ${p.lugar ? '<button class="btn ghost" type="button" data-quitar-lugar>Quitar</button>' : ""}</div>
        <ul class="dir-results" hidden></ul>
        <p class="hint" data-lugar-msg>${p.lugar ? `Marcado: ${esc(p.lugar_nombre || "ubicación elegida")}.` : "Escribe la dirección y elige el resultado."}</p>
      </fieldset>
      <div class="form-actions">${perfil ? '<a class="btn ghost" href="#/mi-perfil">Cancelar</a>' : ""}
        <button class="btn primary" type="submit">Guardar mi perfil</button></div>
      <div class="form-msg" role="alert"></div>
    </form>`;
  const form = $(".perfil-form", lienzo);
  let lugar = p.lugar || null, lugarNombre = p.lugar_nombre || "";
  const avisoLugar = $("[data-lugar-msg]", form), lista = $(".dir-results", form), entrada = $("#r-lugar", form);

  async function buscarLugar() {
    const texto = entrada.value.trim();
    lista.hidden = true;
    if (texto.length < 3) { avisoLugar.textContent = "Escribe la calle y el distrito."; return; }
    try {
      const resultados = await conBoton($("[data-buscar-lugar]", form), "Buscando…", () => llamar("/api/ubicaciones?q=" + encodeURIComponent(texto)));
      if (!resultados.length) { avisoLugar.textContent = "No encontramos esa dirección en Lima. Prueba con la avenida y el distrito."; return; }
      lista.innerHTML = resultados.map((r, i) => `<li><button type="button" data-i="${i}">${esc(r.nombre)}</button></li>`).join("");
      $$("button", lista).forEach((b) => b.addEventListener("click", () => {
        const r = resultados[Number(b.dataset.i)];
        lugar = { latitud: r.latitud, longitud: r.longitud };
        lugarNombre = r.nombre;
        entrada.value = r.nombre;
        lista.hidden = true;
        avisoLugar.textContent = `Marcado: ${r.nombre}.`;
      }));
      lista.hidden = false;
      avisoLugar.textContent = "Elige el resultado correcto.";
    } catch (err) {
      avisoLugar.textContent = err.message;
    }
  }
  $("[data-buscar-lugar]", form).addEventListener("click", buscarLugar);
  entrada.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); buscarLugar(); } });
  $("[data-quitar-lugar]", form)?.addEventListener("click", (e) => {
    lugar = null; lugarNombre = ""; entrada.value = ""; avisoLugar.textContent = "Sin lugar de trabajo o estudio."; e.currentTarget.remove();
  });
  $$('input[name="prioridades"]', form).forEach((c) => c.addEventListener("change", () => {
    if ($$('input[name="prioridades"]:checked', form).length > 3) {
      c.checked = false;
      mensaje($(".form-msg", form), "Elige como máximo 3 prioridades.");
    } else mensaje($(".form-msg", form), "");
  }));

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const hogar = $('input[name="hogar"]:checked', form)?.value;
    if (!hogar) return mensaje($(".form-msg", form), "Elige para quién es el departamento.");
    const max = $("#r-max", form).value, dorm = $("#r-dorm", form).value;
    const nuevo = {
      hogar, presupuesto_max: max === "" ? null : Number(max), dormitorios_min: dorm === "" ? null : Number(dorm),
      prioridades: $$('input[name="prioridades"]:checked', form).map((c) => c.value),
      distritos: $$('input[name="distritos"]:checked', form).map((c) => c.value),
      lugar, lugar_nombre: lugarNombre || null,
      orden: $('input[name="orden"]:checked', form)?.value || "afinidad",
    };
    if (nuevo.presupuesto_max != null && (nuevo.presupuesto_max < 300 || nuevo.presupuesto_max > 50000)) {
      return mensaje($(".form-msg", form), "El presupuesto debe estar entre S/ 300 y S/ 50,000.");
    }
    try {
      await conBoton($('button[type="submit"]', form), "Guardando…", () => llamar("/api/perfil", { metodo: "PUT", cuerpo: nuevo }));
      irA("#/mi-perfil");
    } catch (err) {
      mensaje($(".form-msg", form), err.message);
    }
  });
}

/* ---------- 2. Mi perfil: datos de la cuenta y lo que el sistema entendió del cuestionario ---------- */

export async function vistaMiPerfil(lienzo) {
  const [op, { usuario, perfil }] = await Promise.all([obtenerOpciones(), llamar("/api/perfil")]);
  lienzo.innerHTML = `
    ${filaTitulo("Mi perfil", "Tus datos y lo que el sistema usa para recomendarte departamentos.")}
    <section class="panel perfil-card" aria-label="Cuenta">
      <h2>Cuenta</h2>
      <dl><div><dt>Nombre</dt><dd>${esc(usuario.nombre)}</dd></div><div><dt>Correo</dt><dd>${esc(usuario.email)}</dd></div></dl>
    </section>
    ${perfil ? `
    <section class="panel perfil-card" aria-label="Perfil de búsqueda">
      <div class="perfil-head"><h2>Lo que buscas</h2><a class="btn" href="#/mi-perfil/editar">Editar</a></div>
      <dl>${filasPerfil(op, perfil).map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("")}</dl>
    </section>
    <div class="perfil-actions"><a class="btn primary" href="#/para-ti">Ver mis recomendaciones</a>
      <a class="btn" href="#/para-ti?ver=guardados">Mis guardados</a></div>`
    : `<section class="panel"><div class="empty"><p>Todavía no nos cuentas qué buscas. Responde unas preguntas y te recomendamos departamentos.</p>
        <a class="btn primary" href="#/mi-perfil/editar">Empezar</a></div></section>`}
    <p class="perfil-foot">¿También alquilas un departamento? <a href="#/mis-departamentos">Mis departamentos</a> ·
      <button class="link-btn" type="button" data-salir>Cerrar sesión</button></p>`;
  $("[data-salir]", lienzo).addEventListener("click", cerrarSesion);
}

function filasPerfil(op, perfil) {
  return [
    ["Hogar", `${op.recomendador.hogares[perfil.hogar] || ""}. ${DESCRIPCION_HOGAR[perfil.hogar] || ""}`],
    ["Presupuesto", perfil.presupuesto_max ? `hasta ${soles(perfil.presupuesto_max)} al mes` : "sin tope"],
    ["Dormitorios", perfil.dormitorios_min ? `${perfil.dormitorios_min} o más` : "según tu hogar"],
    ["Te importa", perfil.prioridades?.length ? perfil.prioridades.map((k) => op.recomendador.prioridades[k]).join(", ") : "sin prioridades marcadas"],
    ["Distritos", perfil.distritos?.length ? perfil.distritos.map(titulo).join(", ") : "todos"],
    ["Trabajo o estudio", perfil.lugar ? (perfil.lugar_nombre || "ubicación marcada") : "no indicado"],
    ["Orden de resultados", NOMBRE_ORDEN[perfil.orden || "afinidad"]],
  ];
}

/* ---------- 3. Recomendaciones y 4. Guardados ---------- */

export async function vistaRecomendaciones(lienzo, params) {
  const [{ perfil }, guardados] = await Promise.all([llamar("/api/perfil"), llamar("/api/guardados")]);
  if (!perfil) return irA("#/mi-perfil/editar");
  const pestana = params.get("ver") === "guardados" ? "guardados" : "recomendados";
  lienzo.innerHTML = `
    ${filaTitulo("Recomendados para ti", "Elegidos según tu perfil. Guarda los que te gusten para compararlos después.",
      '<a class="btn" href="#/mi-perfil">Mi perfil</a>')}
    <nav class="tabs reco-tabs" aria-label="Recomendados o guardados">
      <a href="#/para-ti" ${pestana === "recomendados" ? 'aria-current="page"' : ""}>Recomendados</a>
      <a href="#/para-ti?ver=guardados" ${pestana === "guardados" ? 'aria-current="page"' : ""}>Guardados <span data-n-guardados>(${guardados.length})</span></a>
    </nav>
    ${pestana === "recomendados" ? `<div class="orden-row"><label for="r-orden">Ordenar</label>
      <select class="input" id="r-orden">${ORDENES.map(([k, nombre]) => `<option value="${k}" ${(perfil.orden || "afinidad") === k ? "selected" : ""}>${esc(nombre)}</option>`).join("")}</select></div>` : ""}
    <div data-recos aria-busy="true"><section class="panel"><p class="skeleton">Buscando los departamentos que mejor te calzan…</p></section></div>`;
  const destino = $("[data-recos]", lienzo);
  const estado = { ids: new Set(guardados.map((g) => g.id)) };
  try {
    if (pestana === "guardados") {
      pintarGuardados(destino, lienzo, guardados, estado);
    } else {
      const r = await llamar("/api/recomendar", { cuerpo: { ...paraRecomendar(perfil), limite: 12 } });
      const pintar = (orden) => {
        destino.innerHTML = r.recomendaciones.length ? `
          <ol class="reco-list">${ordenar(r.recomendaciones, orden).map((x, i) => tarjeta(x, i, estado)).join("")}</ol>
          <p class="panel-note">${esc(r.aviso)} Elegimos estos ${r.recomendaciones.length} según lo que suele necesitar tu tipo de hogar, tus prioridades,
            la cercanía a tu trabajo o estudio y si el precio es bueno para lo que ofrece; luego los ordenamos como prefieras. El esquema de cada tarjeta es referencial:
            se dibuja con los dormitorios, baños y metros del anuncio, no es su plano real.</p>`
          : `<section class="panel"><div class="empty"><p>Ningún departamento cumple tu presupuesto y tus filtros. Prueba subir el presupuesto, quitar distritos o bajar el mínimo de dormitorios.</p>
              <a class="btn primary" href="#/mi-perfil/editar">Editar mi perfil</a></div></section>`;
        activarGuardar(destino, lienzo, estado);
      };
      pintar(perfil.orden || "afinidad");
      $("#r-orden", lienzo)?.addEventListener("change", (e) => {
        const orden = e.currentTarget.value;
        pintar(orden);
        // Se recuerda en el perfil para la próxima visita; si falla, la lista ya quedó ordenada igual.
        perfil.orden = orden;
        llamar("/api/perfil", { metodo: "PUT", cuerpo: perfil }).catch(() => null);
      });
    }
  } catch (err) {
    destino.innerHTML = `<section class="panel"><div class="empty"><p>No pudimos cargar esta sección. ${esc(err.message)}</p>
      <a class="btn" href="#/mi-perfil">Revisar mi perfil</a></div></section>`;
  } finally {
    destino.removeAttribute("aria-busy");
  }
}

function pintarGuardados(destino, lienzo, lista, estado) {
  destino.dataset.vista = "guardados";
  destino.innerHTML = lista.length
    ? `<ol class="reco-list">${lista.map((x, i) => tarjeta(x, i, estado)).join("")}</ol>
       <p class="panel-note">Cada tarjeta muestra cómo estaba el anuncio cuando lo guardaste.</p>`
    : `<section class="panel"><div class="empty"><p>Todavía no guardas ningún departamento. En Recomendados, usa "Guardar" en los que te gusten.</p>
        <a class="btn primary" href="#/para-ti">Ver recomendados</a></div></section>`;
  activarGuardar(destino, lienzo, estado);
}

function activarGuardar(destino, lienzo, estado) {
  $$("[data-guardar]", destino).forEach((boton) => boton.addEventListener("click", async () => {
    const id = boton.dataset.guardar, ya = estado.ids.has(id);
    try {
      const lista = await conBoton(boton, ya ? "Quitando…" : "Guardando…",
        () => llamar(`/api/guardados/${encodeURIComponent(id)}`, { metodo: ya ? "DELETE" : "POST" }));
      estado.ids = new Set(lista.map((g) => g.id));
      const n = $("[data-n-guardados]", lienzo);
      if (n) n.textContent = `(${lista.length})`;
      if (destino.dataset.vista === "guardados") return pintarGuardados(destino, lienzo, lista, estado);
      boton.setAttribute("aria-pressed", String(!ya));
      boton.textContent = ya ? "Guardar" : "Guardado";
    } catch (err) {
      boton.textContent = "No se pudo";
      boton.title = err.message;
    }
  }));
}

function yaDicha(amenidad, dichos) {
  const a = amenidad.toLowerCase();
  return dichos.includes(a) || ((a === "balcón" || a === "terraza") && dichos.includes("balcón o terraza"));
}

function tarjeta(x, i, estado) {
  const dorm = `${num(x.dormitorios)} ${x.dormitorios === 1 ? "dormitorio" : "dormitorios"}`;
  const banos = `${num(x.banos)} ${x.banos === 1 ? "baño" : "baños"}`;
  const guardado = estado.ids.has(x.id);
  // Todas las amenidades del anuncio, sin repetir las que ya están en "Tiene".
  const dichos = (x.motivos || []).join(" ").toLowerCase();
  const amenidades = [...(x.amenidades || []).map((a) => ETIQUETAS_AMENIDAD[a].toLowerCase()), ...(x.amenidades_extra || [])]
    .filter((a) => !yaDicha(a, dichos));
  return `<li class="reco-card">
    <a class="reco-link" href="#/anuncio/${esc(x.id)}" aria-label="Ver ficha: ${esc(dorm)} en ${esc(titulo(x.distrito))}">
      <span class="reco-rank" aria-label="Recomendación ${i + 1}">${i + 1}</span>
      <figure class="reco-plano">${plano(x.dormitorios, x.banos, x.area_total)}
        <figcaption>${num(x.area_total)} m² · referencial</figcaption></figure>
      <div class="reco-body">
        <p class="reco-title"><b>${esc(titulo(x.distrito))}</b> · ${esc(dorm)} · ${esc(banos)} · ${num(x.area_total)} m²</p>
        <p class="reco-price"><b>${soles(x.precio_soles)}</b> al mes · debería costar ${soles(x.precio_estimado_soles)}${x.dist_paradero_min_m != null ? ` · paradero a ${num(x.dist_paradero_min_m)} m` : ""}</p>
        ${x.motivos?.length ? `<p class="reco-why"><span>Tiene:</span> ${x.motivos.map(esc).join(" · ")}</p>` : ""}
        ${amenidades.length ? `<p class="reco-extra"><span>Amenidades:</span> ${amenidades.map(esc).join(" · ")}</p>` : ""}
        ${x.faltas?.length ? `<p class="reco-miss"><span>Ten en cuenta:</span> ${x.faltas.map(esc).join(" · ")}</p>` : ""}
      </div>
    </a>
    <button class="btn reco-save" type="button" data-guardar="${esc(x.id)}" aria-pressed="${guardado}">${guardado ? "Guardado" : "Guardar"}</button></li>`;
}

/* Esquema de distribución dibujado con los datos del anuncio (no es el plano real).
   El tamaño del contorno crece con los m², para comparar de un vistazo; dormitorios a la derecha,
   baños abajo a la izquierda y el resto como sala-cocina. */
function plano(dormitorios, banos, area) {
  const W = 120, H = 90;
  const d = Math.max(0, Math.round(dormitorios || 0)), b = Math.max(0, Math.round(banos || 0));
  const escala = 0.62 + 0.38 * Math.min(Math.max(((area || 40) - 30) / 150, 0), 1);
  const w = W * escala, h = H * escala, x0 = (W - w) / 2, y0 = (H - h) / 2;
  const dDib = Math.min(d, 4), bDib = Math.min(b, 3);
  const anchoDorm = dDib ? w * 0.42 : 0, anchoResto = w - anchoDorm;
  const altoBano = bDib ? h * 0.34 : 0;
  const letra = Math.max(6, Math.min(8.5, 7 * escala + 1));
  const piezas = [];
  const cuarto = (x, y, ancho, alto, texto, clase) => {
    piezas.push(`<rect class="${clase}" x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${ancho.toFixed(1)}" height="${alto.toFixed(1)}"/>`);
    if (texto && ancho > 14 && alto > 10) {
      piezas.push(`<text x="${(x + ancho / 2).toFixed(1)}" y="${(y + alto / 2 + letra / 3).toFixed(1)}" font-size="${letra.toFixed(1)}">${texto}</text>`);
    }
  };
  cuarto(x0, y0, anchoResto, h - altoBano, d ? "Sala · cocina" : "Ambiente", "p-sala");
  for (let i = 0; i < bDib; i += 1) {
    cuarto(x0 + (anchoResto / bDib) * i, y0 + h - altoBano, anchoResto / bDib, altoBano, i === bDib - 1 && b > bDib ? `${b - bDib + 1} baños` : "Baño", "p-bano");
  }
  for (let i = 0; i < dDib; i += 1) {
    cuarto(x0 + anchoResto, y0 + (h / dDib) * i, anchoDorm, h / dDib, i === dDib - 1 && d > dDib ? `${d - dDib + 1} dorm.` : "Dorm.", "p-dorm");
  }
  piezas.push(`<rect class="p-muro" x="${x0.toFixed(1)}" y="${y0.toFixed(1)}" width="${w.toFixed(1)}" height="${h.toFixed(1)}"/>`);
  const etiqueta = `Esquema referencial: ${d} ${d === 1 ? "dormitorio" : "dormitorios"}, ${b} ${b === 1 ? "baño" : "baños"}, ${num(area)} metros cuadrados`;
  return `<svg class="plano" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(etiqueta)}">${piezas.join("")}</svg>`;
}
