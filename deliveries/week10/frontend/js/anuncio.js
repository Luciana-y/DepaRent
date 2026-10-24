import { llamar } from "./api.js";
import { escala, panelComparables, ticks } from "./analisis.js";
import { $, esc, num, pct, soles, titulo, conBoton, mensaje, ETIQUETAS_AMENIDAD, enlazarFilas, copiarEnlace } from "./util.js";

const banos = (n) => `${num(n)} ${n === 1 ? "baño" : "baños"}`;
const fecha = (segundos) => new Date(segundos * 1000).toLocaleDateString("es-PE", { day: "numeric", month: "long", year: "numeric" });

/* ---------- Ficha de un anuncio: ¿vale lo que piden? ---------- */

export async function vistaAnuncio(lienzo, params, id) {
  lienzo.innerHTML = `<section class="panel object-head"><div class="cover" aria-hidden="true"></div><div><h1><span class="skeleton">Cargando anuncio</span></h1></div></section>`;
  const f = await llamar(`/api/anuncios/${id}`);
  const x = f.anuncio, v = f.vivienda, p = f.precio;
  const nombre = x.nombre || `${num(v.dormitorios)} dorm. · ${banos(v.banos)} en ${titulo(x.distrito)}`;
  const origen = f.publicacion
    ? `publicado en DepaRent por ${esc(f.publicacion.propietario)} el ${fecha(f.publicacion.desde)}`
    : `anuncio de ${f.original ? esc(f.original.portal) : "un portal"}${f.original ? `, captura del ${fecha(Date.parse(f.original.capturado + "T12:00:00") / 1000)}` : ""}`;
  const clasePill = x.valoracion.startsWith("Por debajo") ? "pos" : x.valoracion.startsWith("Por encima") ? "warn" : "";
  lienzo.innerHTML = `
    <p style="margin-bottom:12px"><a class="card-link" href="#/buscar">Buscar departamentos</a></p>
    <section class="panel object-head">
      <div class="cover" aria-hidden="true">${num(v.area_total)}<br>m²</div>
      <div><h1>${esc(nombre)}</h1><p class="meta">${esc(titulo(x.distrito))} · ${num(v.area_total)} m² · ${esc(x.perfil)} · ${origen}</p></div>
      <div class="title-actions">
        <button class="btn" type="button" data-copiar>Copiar enlace</button>
        ${f.original ? `<a class="btn primary" href="${esc(f.original.url)}" target="_blank" rel="noopener noreferrer nofollow">Ver el anuncio original en ${esc(f.original.portal)}</a>` : ""}
        ${f.publicacion ? '<a class="btn primary" href="#contacto" data-ir-contacto>Me interesa</a>' : ""}
      </div>
    </section>
    <div class="grid">
      <div class="kpis span-6">
        <div class="kpi"><p class="kpi-label">Precio pedido</p><p class="kpi-value is-main num">${soles(x.precio_soles)}<small>al mes</small></p>
          <p class="delta">${f.publicacion ? `Escenario ${esc(f.publicacion.escenario.toLowerCase())}` : "Precio pedido en el portal, no de contrato"}</p></div>
        <div class="kpi"><p class="kpi-label">Estimado por el modelo</p><p class="kpi-value num">${soles(p.precio_estimado_soles)}</p>
          <p class="delta">Rango probable: ${soles(p.limite_inferior_soles)} a ${soles(p.limite_superior_soles)}</p></div>
        <div class="kpi"><p class="kpi-label">Frente al estimado</p><p class="kpi-value num">${pct(x.diferencia_estimado_porcentaje)}</p>
          <p class="delta"><span class="pill ${clasePill}">${esc(x.valoracion)}</span></p></div>
      </div>

    </div>
    <div class="grid stretch" style="margin-top:var(--gap)">
      <section class="panel span-4 ruler" aria-labelledby="t-justo">
        <header><h2 id="t-justo">¿Es un buen precio?</h2><span class="meta">Frente a sus anuncios parecidos y al rango del modelo</span></header>
        ${reglaAnuncio(f)}
        <p class="panel-note">${lecturaPrecio(f)}</p>
      </section>

      <section class="panel span-2" aria-labelledby="t-carac">
        <header><h2 id="t-carac">Características</h2></header>
        <div class="rows kv">
          ${[["Área", `${num(v.area_total)} m²`], ["Dormitorios", num(v.dormitorios)], ["Baños", num(v.banos)],
            ["Estacionamientos", v.estacionamientos == null ? null : num(v.estacionamientos)],
            ["Antigüedad", v.antiguedad == null ? null : `${num(v.antiguedad)} años`],
            ["Mantenimiento", v.mantenimiento == null ? null : soles(v.mantenimiento)]]
            .map(([k, val]) => `<div class="row"><span>${k}</span>${val == null ? '<span class="dash">No informado</span>' : `<b class="num">${val}</b>`}</div>`).join("")}
        </div>
        <p class="panel-note">${x.amenidades.length ? "Tiene " + x.amenidades.map((a) => ETIQUETAS_AMENIDAD[a].toLowerCase()).join(", ") + "." : "El anuncio no menciona amenidades."}</p>
      </section>

    </div>
    <div class="grid stretch" style="margin-top:var(--gap)">
      <section class="panel span-3" aria-labelledby="t-transporte">
        <header><h2 id="t-transporte">Transporte</h2><span class="pill">${esc(f.acceso.nivel)}</span></header>
        <p class="big-figure num">${num(f.acceso.dist_paradero_min_m)} m</p>
        <p class="hint">al paradero de transporte público más cercano · ${f.acceso.paraderos_500m} paraderos a 500 m</p>
        <div class="bullet" role="img" aria-label="Más cerca que el ${num(f.acceso.porcentaje_anuncios_mas_lejos, 1)}% de los anuncios"><span style="width:${f.acceso.porcentaje_anuncios_mas_lejos}%"></span></div>
        <p class="hint">Más cerca de un paradero que el ${num(f.acceso.porcentaje_anuncios_mas_lejos, 1)}% de los anuncios.</p>
        <p class="hint" style="margin-top:8px">Nivel ${esc(f.acceso.nivel.toLowerCase())}: alta si hay un paradero a 300 m o menos y más paraderos a 500 m que la mitad de los anuncios; baja si el más cercano está a más de 500 m.</p>
        <p class="panel-note">No mostramos el nombre del paradero ni un mapa: revelarían la ubicación del departamento.</p>
      </section>

      <section class="panel span-3" aria-labelledby="t-distrito">
        <header><h2 id="t-distrito">${esc(titulo(x.distrito))}</h2><span class="pill ${f.tendencia.tendencia === "Al alza" ? "main" : ""}">${esc(f.tendencia.tendencia)} · ${pct(f.tendencia.cambio_porcentaje)}</span></header>
        <p>${f.tendencia.serie_propia ? "La serie del BCRP del distrito" : "La serie promedio de Lima del BCRP (el distrito no tiene serie propia)"}
          proyecta un cambio de ${pct(f.tendencia.cambio_porcentaje)} en los próximos cuatro trimestres.</p>
        <div class="rows kv" style="margin-top:10px">
          <div class="row"><span>Mediana de alquiler del distrito</span><b class="num">${soles(p.baseline_distrital_soles)}</b></div>
          <div class="row"><span>Anuncios del distrito en el modelo</span><b class="num">${num(p.anuncios_entrenamiento_distrito)}</b></div>
        </div>
        <p class="panel-note">Es contexto de mercado derivado del precio de venta, no un pronóstico de este alquiler.</p>
      </section>

      <div class="span-6">${panelComparables(f.perfil).replace("Los 8 anuncios más parecidos", "Anuncios parecidos")}</div>

      <section class="panel span-6" id="contacto" aria-labelledby="t-contacto">
        <header><h2 id="t-contacto">${f.publicacion ? `Escríbele a ${esc(f.publicacion.propietario)}` : "Contacto"}</h2></header>
        ${f.publicacion ? formularioInteres(f.publicacion.propietario)
          : f.original ? `<p>Este anuncio viene de ${esc(f.original.portal)} (captura del ${fecha(Date.parse(f.original.capturado + "T12:00:00") / 1000)}) y puede ya no estar disponible.
              La dirección y el contacto están en el anuncio original; DepaRent no los guarda ni los muestra.</p>
              <p style="margin-top:12px"><a class="btn" href="${esc(f.original.url)}" target="_blank" rel="noopener noreferrer nofollow">Ver el anuncio original en ${esc(f.original.portal)}</a></p>`
          : "<p>Este anuncio viene de un portal inmobiliario y DepaRent no guarda su dirección ni el contacto de su propietario.</p>"}
      </section>
    </div>
    <p class="panel-note">${esc(f.aviso)}</p>`;

  $("[data-copiar]", lienzo).addEventListener("click", (e) => copiarEnlace(e.currentTarget));
  enlazarFilas(lienzo);
  $("[data-ir-contacto]", lienzo)?.addEventListener("click", (e) => {
    e.preventDefault();
    $("#contacto", lienzo).scrollIntoView({ block: "start" });
    $("#i-nombre", lienzo)?.focus({ preventScroll: true });
  });
  const form = $(".interes-form", lienzo);
  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await conBoton($("button", form), "Enviando…", () => llamar(`/api/anuncios/${id}/interes`, { cuerpo: Object.fromEntries(new FormData(form)) }));
      form.outerHTML = `<p class="toast">Listo. ${esc(f.publicacion.propietario)} verá tu mensaje y tu correo en su cuenta de DepaRent para responderte.</p>`;
    } catch (err) {
      mensaje($(".form-msg", form), err.message);
    }
  });
}

function formularioInteres(propietario) {
  return `<p class="hint" style="margin-bottom:14px">${esc(propietario)} verá tu nombre, tu correo y tu mensaje en su cuenta. No compartimos tu correo con nadie más.</p>
    <form class="interes-form fields" novalidate>
      <div class="field"><label for="i-nombre">Tu nombre</label><input class="input" id="i-nombre" name="nombre" autocomplete="name" required></div>
      <div class="field"><label for="i-email">Tu correo</label><input class="input" id="i-email" name="email" type="email" autocomplete="email" required></div>
      <div class="field wide"><label for="i-mensaje">Mensaje</label>
        <textarea class="input" id="i-mensaje" name="mensaje" rows="3" maxlength="600" required style="height:auto;padding:10px 12px">Hola, me interesa el departamento. ¿Sigue disponible?</textarea></div>
      <div class="field wide"><div style="display:flex;justify-content:flex-end"><button class="btn primary" type="submit">Enviar mensaje</button></div></div>
      <div class="form-msg wide" role="alert"></div>
    </form>`;
}

function lecturaPrecio(f) {
  const x = f.anuncio, c = f.perfil;
  const baratos = c.comparables.filter((k) => k["Precio pedido (S/)"] < x.precio_soles).length;
  return `Pide ${soles(x.precio_soles)}: ${baratos} de sus ${c.comparables.length} anuncios más parecidos piden menos, y el modelo estima ${soles(f.precio.precio_estimado_soles)}. `
    + "Muchos anuncios de mercado se usaron para entrenar el modelo, así que la comparación es orientativa.";
}

// La regla de precios del inquilino: el precio pedido (único dato en naranja) frente a los parecidos y al modelo.
function reglaAnuncio(f) {
  const x = f.anuncio, p = f.precio;
  const comps = f.perfil.comparables.map((c) => c["Precio pedido (S/)"]).filter((v) => v != null);
  const todos = [...comps, p.limite_inferior_soles, p.limite_superior_soles, x.precio_soles];
  const min = Math.min(...todos) * 0.94, max = Math.max(...todos) * 1.04;
  const compacto = window.innerWidth < 700;
  const W = compacto ? 360 : 640, L = compacto ? 8 : 132, R = W - 16, ex = escala(min, max, L, R);
  const fila = compacto ? { comparables: 62, rango: 116 } : { comparables: 66, rango: 112 };
  const ejeY = fila.rango + 52, H = ejeY + 8;
  const etiqueta = (texto, y) => compacto ? `<text class="lbl" x="0" y="${y - 16}">${texto}</text>` : `<text class="lbl" x="0" y="${y + 4}">${texto}</text>`;
  const xPedido = ex(x.precio_soles), xEstimado = ex(p.precio_estimado_soles);
  const anclaPedido = xPedido > (L + R) / 2 ? "end" : "start", dxPedido = anclaPedido === "end" ? -6 : 6;
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Precio pedido ${soles(x.precio_soles)} frente a ${comps.length} anuncios parecidos y al rango del modelo">
    ${ticks(min, max, compacto ? 3 : 4).map((v) => `<line x1="${ex(v)}" x2="${ex(v)}" y1="40" y2="${ejeY - 18}" stroke="#e7e6e2" stroke-dasharray="2 3"/><text x="${ex(v)}" y="${ejeY}" text-anchor="middle">${soles(v)}</text>`).join("")}
    ${etiqueta(`${comps.length} parecidos`, fila.comparables)}${etiqueta("Rango del modelo", fila.rango)}
    ${comps.map((v) => `<circle cx="${ex(v)}" cy="${fila.comparables}" r="5" fill="#111" fill-opacity="0.28"><title>${soles(v)}</title></circle>`).join("")}
    <rect x="${ex(p.limite_inferior_soles)}" y="${fila.rango - 4}" width="${ex(p.limite_superior_soles) - ex(p.limite_inferior_soles)}" height="8" rx="4" fill="#d9d7d2"/>
    <line x1="${xEstimado}" x2="${xEstimado}" y1="${fila.rango - 12}" y2="${fila.rango + 12}" stroke="#111" stroke-width="2"/>
    <text x="${xEstimado}" y="${fila.rango + 28}" text-anchor="middle">Estimado</text>
    <line x1="${xPedido}" x2="${xPedido}" y1="34" y2="${fila.rango + 12}" stroke="var(--accent)" stroke-width="2"/>
    <text class="main-lbl" x="${xPedido + dxPedido}" y="24" text-anchor="${anclaPedido}">Pide ${soles(x.precio_soles)}</text>
  </svg>`;
}
