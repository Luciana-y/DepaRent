import { llamar } from "./api.js";
import { $, $$, esc, num, pct, soles, titulo, conBoton, mensaje } from "./util.js";

const PESTANAS = [["resumen", "Resumen"], ["comparables", "Comparables"], ["acceso", "Accesibilidad"], ["tendencia", "Tendencia"], ["simulador", "Simular una mejora"]];

/**
 * Dibuja el análisis de un departamento (respuesta de /api/analizar) en pestañas.
 * acciones.alPublicar(escenario) y acciones.alRetirar(): publicación (solo propietario)
 * acciones.publicacion: publicación vigente · acciones.alMoverUbicacion(lat, lon): clic en el mapa
 * acciones.extras: [[id, etiqueta, dibujar(panel)], ...] pestañas propias de la vista (Características, Interesados).
 */
export function mostrarAnalisis(contenedor, a, opciones, acciones = {}) {
  const extras = acciones.extras || [];
  const pestanas = [...PESTANAS, ...extras.map((e) => e.slice(0, 2))];
  contenedor.innerHTML = `
    <nav class="tabs" role="tablist" aria-label="Secciones del análisis">
      ${pestanas.map(([id, texto], i) => `<button type="button" role="tab" id="tab-${id}" aria-controls="panel-${id}" aria-selected="${i === 0}" data-tab="${id}">${texto}</button>`).join("")}
    </nav>
    <div role="tabpanel" id="panel-resumen" aria-labelledby="tab-resumen" data-panel="resumen">${panelResumen(a, acciones)}</div>
    <div role="tabpanel" id="panel-comparables" aria-labelledby="tab-comparables" data-panel="comparables" hidden>${panelComparables(a.perfil)}</div>
    <div role="tabpanel" id="panel-acceso" aria-labelledby="tab-acceso" data-panel="acceso" hidden>${panelAcceso(a.accesibilidad)}</div>
    <div role="tabpanel" id="panel-tendencia" aria-labelledby="tab-tendencia" data-panel="tendencia" hidden>${panelTendencia(a.tendencia, true)}</div>
    <div role="tabpanel" id="panel-simulador" aria-labelledby="tab-simulador" data-panel="simulador" hidden>${panelSimulador(a.vivienda)}</div>
    ${extras.map(([id]) => `<div role="tabpanel" id="panel-${id}" aria-labelledby="tab-${id}" data-panel="${id}" hidden></div>`).join("")}`;
  extras.forEach(([id, , dibujar]) => dibujar($(`[data-panel="${id}"]`, contenedor)));

  let mapa = null;
  const abrir = (id) => {
    $$(".tabs [role=tab]", contenedor).forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === id)));
    $$("[data-panel]", contenedor).forEach((p) => { p.hidden = p.dataset.panel !== id; });
    if (id === "acceso") mapa = dibujarMapa($(".map", contenedor), a.accesibilidad, mapa, moverUbicacion);
  };
  $$(".tabs [role=tab]", contenedor).forEach((b) => b.addEventListener("click", () => abrir(b.dataset.tab)));
  $$("[data-ir]", contenedor).forEach((b) => b.addEventListener("click", () => abrir(b.dataset.ir)));

  async function moverUbicacion(lat, lon) {
    try {
      const nuevo = await llamar("/api/accesibilidad", { cuerpo: { latitud: lat, longitud: lon } });
      a.accesibilidad = nuevo;
      const panel = $('[data-panel="acceso"]', contenedor);
      panel.innerHTML = panelAcceso(nuevo);
      mapa = dibujarMapa($(".map", panel), nuevo, null, moverUbicacion);
      acciones.alMoverUbicacion?.(lat, lon);
    } catch (e) {
      mensaje($(".acceso-msg", contenedor), e.message);
    }
  }

  $$("[data-publicar]", contenedor).forEach((boton) => boton.addEventListener("click", () => {
    const s = a.publicacion.escenarios[Number(boton.dataset.publicar)];
    conBoton(boton, "Publicando…", () => acciones.alPublicar(s)).catch((e) => mensaje($(".pub-msg", contenedor), e.message));
  }));
  activarSimulador(contenedor, a.vivienda, opciones);
}

/* ---------- Resumen ---------- */

function panelResumen(a, acciones) {
  const p = a.precio, ev = a.evidencia_distrital;
  const avisos = [...a.avisos];
  if (ev?.muestra_pequena) avisos.unshift(`En ${titulo(ev.distrito)} hubo menos de 20 anuncios de prueba: su error local es inestable.`);
  return `
    ${avisos.length ? `<div style="margin-bottom:16px">${avisos.map((t) => `<p class="notice">${esc(t)}</p>`).join("")}</div>` : ""}
    <div class="grid">
      <div class="kpis span-6">
        <div class="kpi"><p class="kpi-label">Precio esperado</p><p class="kpi-value is-main num">${soles(p.precio_estimado_soles)}<small>al mes</small></p>
          <p class="delta">Mediana del distrito: ${soles(p.baseline_distrital_soles)}</p></div>
        <div class="kpi"><p class="kpi-label">Rango probable</p><p class="kpi-value num">${soles(p.limite_inferior_soles)} <small>a</small> ${soles(p.limite_superior_soles)}</p>
          <p class="delta">Cubrió 92 de cada 100 precios de prueba</p></div>
        <div class="kpi"><p class="kpi-label">Error medio en el distrito</p>
          <p class="kpi-value num">${ev ? soles(ev.error_absoluto_medio_soles) : '<span class="dash">—</span>'}</p>
          <p class="delta">${ev ? `${ev.anuncios_prueba} anuncios de prueba de ${esc(titulo(ev.distrito))}` : "Sin anuncios de prueba en este distrito"}</p></div>
      </div>

      <section class="panel span-4 ruler" aria-labelledby="t-regla">
        <header><h2 id="t-regla">¿A cuánto publicar?</h2><span class="meta">Comparables, rango del modelo y los tres precios</span></header>
        ${reglaPrecios(a)}
        <p class="panel-note">La línea naranja es el precio esperado. Cada punto es uno de los 8 anuncios más parecidos; la barra gris, el rango probable del modelo.</p>
      </section>

      <section class="panel span-2" aria-labelledby="t-publicar">
        <header><h2 id="t-publicar">Precio de publicación</h2></header>
        ${acciones.publicacion ? `<p class="toast">Publicado a ${soles(acciones.publicacion.precio_soles)} (${esc(acciones.publicacion.escenario)}). Ya aparece en la búsqueda.</p>` : ""}
        <div class="rows">
          ${a.publicacion.escenarios.map((s, i) => `
            <div class="row scenario-row">
              <span>${esc(s.escenario)}${s.sugerido ? '<span class="pill main">Sugerido</span>' : ""}
                <span class="sub">${pct(s.diferencia_vs_esperado_porcentaje)} frente al esperado</span></span>
              <span style="text-align:right"><b class="num">${soles(s.precio_soles)}</b>
                ${acciones.alPublicar ? `<button class="card-link" type="button" data-publicar="${i}">Publicar</button>` : ""}</span>
            </div>`).join("")}
        </div>
        <p class="panel-note">${esc(a.publicacion.motivo)}</p>
        <div class="pub-msg"></div>
      </section>

      <section class="panel span-3" aria-labelledby="t-acceso">
        <header><h2 id="t-acceso">Accesibilidad</h2><span class="pill">${esc(a.accesibilidad.nivel)}</span></header>
        <p class="big-figure num">${num(a.accesibilidad.dist_paradero_min_m)} m</p>
        <p class="hint">al paradero ${esc(a.accesibilidad.paradero_cercano_nombre)} (${esc(a.accesibilidad.paradero_cercano_tipo)})</p>
        <div class="bullet" role="img" aria-label="Más cerca que el ${num(a.accesibilidad.porcentaje_anuncios_mas_lejos, 1)}% de los anuncios"><span style="width:${a.accesibilidad.porcentaje_anuncios_mas_lejos}%"></span></div>
        <p class="hint">Más cerca de un paradero que el ${num(a.accesibilidad.porcentaje_anuncios_mas_lejos, 1)}% de los anuncios · ${a.accesibilidad.paraderos_500m} paraderos a 500 m</p>
        <p style="margin-top:12px"><button class="card-link" type="button" data-ir="acceso">Ver el mapa</button></p>
      </section>

      <section class="panel span-3" aria-labelledby="t-perfil">
        <header><h2 id="t-perfil">Perfil competitivo</h2><span class="meta">K-Means sin precio</span></header>
        <p class="big-figure">${esc(a.perfil.perfil.perfil)}</p>
        <p class="hint" style="margin-top:6px">${num(a.perfil.perfil.anuncios_en_perfil)} anuncios en este perfil; la mitad central pide ${soles(a.perfil.perfil.precio_p25_perfil_soles)} a ${soles(a.perfil.perfil.precio_p75_perfil_soles)}.
          Sus 8 más parecidos (${a.perfil.en_mismo_distrito} del mismo distrito) piden ${soles(a.perfil.precio_p25_soles)} a ${soles(a.perfil.precio_p75_soles)}.</p>
        <p style="margin-top:12px"><button class="card-link" type="button" data-ir="comparables">Ver los 8 comparables</button></p>
      </section>

      <section class="panel span-6" aria-labelledby="t-tend">${panelTendencia(a.tendencia, false)}</section>
    </div>`;
}

export function escala(min, max, x0, x1) {
  return (v) => x0 + ((v - min) / (max - min)) * (x1 - x0);
}

export function ticks(min, max, n = 4) {
  // El paso "redondo" más grande que deja al menos tres marcas dentro del rango.
  const base = Math.pow(10, Math.floor(Math.log10(max - min)));
  for (const paso of [base, base / 2, base / 4, base / 5, base / 10, base / 20]) {
    const salida = [];
    for (let v = Math.ceil(min / paso) * paso; v <= max; v += paso) salida.push(+v.toFixed(6));
    if (salida.length >= Math.min(3, n)) return salida.length > n + 1 ? salida.filter((_, i) => i % 2 === 0) : salida;
  }
  return [min, (min + max) / 2, max];
}

// El elemento propio de DepaRent: comparables, rango calibrado y precios de publicación en un mismo eje.
// Se dibuja al ancho del dispositivo para que el texto del SVG no se encoja en el teléfono.
function reglaPrecios(a) {
  const p = a.precio, comps = a.perfil.comparables.map((c) => c["Precio pedido (S/)"]).filter((v) => v != null);
  const escenarios = a.publicacion.escenarios;
  const todos = [...comps, p.limite_inferior_soles, p.limite_superior_soles, ...escenarios.map((s) => s.precio_soles)];
  const min = Math.min(...todos) * 0.94, max = Math.max(...todos) * 1.04;
  const compacto = window.innerWidth < 700;
  const W = compacto ? 360 : 640, L = compacto ? 8 : 132, R = W - 16;
  // En el teléfono la etiqueta de cada fila va encima de la fila; en escritorio, a la izquierda.
  const fila = compacto ? { comparables: 62, rango: 116, publicacion: 170 } : { comparables: 66, rango: 112, publicacion: 158 };
  const ejeY = fila.publicacion + 52, H = ejeY + 8;
  const x = escala(min, max, L, R);
  const etiquetaFila = (texto, y) => compacto
    ? `<text class="lbl" x="0" y="${y - 16}">${texto}</text>` : `<text class="lbl" x="0" y="${y + 4}">${texto}</text>`;
  // Competitivo a la izquierda de su marca, equilibrado encima, renta superior a la derecha.
  const etiqueta = (s) => {
    const xs = x(s.precio_soles), negrita = s.sugerido ? 'class="lbl" font-weight="700"' : "";
    if (s.escenario === "Competitivo") return `<text x="${xs - 6}" y="${fila.publicacion + 26}" text-anchor="end" ${negrita}>${esc(s.escenario)}</text>`;
    if (s.escenario === "Renta superior") return `<text x="${xs + 6}" y="${fila.publicacion + 26}" text-anchor="start" ${negrita}>${esc(s.escenario)}</text>`;
    // Equilibrado suele caer sobre la línea del esperado: su etiqueta va a la derecha de esa línea.
    return `<text x="${Math.max(xs, x(p.precio_estimado_soles)) + 8}" y="${fila.publicacion - 14}" text-anchor="start" ${negrita}>${esc(s.escenario)}</text>`;
  };
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Precio esperado ${soles(p.precio_estimado_soles)} frente a comparables, rango y precios de publicación">
    ${ticks(min, max, compacto ? 3 : 4).map((v) => `<line x1="${x(v)}" x2="${x(v)}" y1="40" y2="${ejeY - 18}" stroke="#e7e6e2" stroke-dasharray="2 3"/><text x="${x(v)}" y="${ejeY}" text-anchor="middle">${soles(v)}</text>`).join("")}
    ${etiquetaFila("8 comparables", fila.comparables)}${etiquetaFila("Rango del modelo", fila.rango)}${etiquetaFila("Publicación", fila.publicacion)}
    ${comps.map((v) => `<circle cx="${x(v)}" cy="${fila.comparables}" r="5" fill="#111" fill-opacity="0.28"><title>${soles(v)}</title></circle>`).join("")}
    <rect x="${x(p.limite_inferior_soles)}" y="${fila.rango - 4}" width="${x(p.limite_superior_soles) - x(p.limite_inferior_soles)}" height="8" rx="4" fill="#d9d7d2"/>
    ${escenarios.map((s) => `<line x1="${x(s.precio_soles)}" x2="${x(s.precio_soles)}" y1="${fila.publicacion - 9}" y2="${fila.publicacion + 9}" stroke="#111" stroke-width="${s.sugerido ? 3 : 1.5}"/>${etiqueta(s)}`).join("")}
    <line x1="${x(p.precio_estimado_soles)}" x2="${x(p.precio_estimado_soles)}" y1="34" y2="${fila.publicacion + 12}" stroke="var(--accent)" stroke-width="2"/>
    <text class="main-lbl" x="${Math.min(Math.max(x(p.precio_estimado_soles), L + 60), R - 60)}" y="24" text-anchor="middle">Esperado ${soles(p.precio_estimado_soles)}</text>
  </svg>`;
}

/* ---------- Comparables ---------- */

export function panelComparables(c) {
  return `<section class="panel" aria-labelledby="t-comp">
    <header><h2 id="t-comp">Los 8 anuncios más parecidos</h2><span class="meta">Perfil ${esc(c.perfil.perfil)} · ${c.en_mismo_distrito} del mismo distrito</span></header>
    <div class="table-wrap"><table class="list-table">
      <thead><tr><th>Anuncio</th><th class="n">Área</th><th class="n">Dorm.</th><th class="n">Baños</th><th class="n">Antigüedad</th><th class="n">Mantenimiento</th><th class="n">S/ por m²</th><th class="n">Precio pedido</th></tr></thead>
      <tbody>${c.comparables.map((x) => `<tr>
        <td><span class="id">${esc(x.Distrito)}</span><span class="sub">${esc(x.Perfil)}</span></td>
        <td class="n more" data-label="Área">${num(x["Área (m²)"])} m²</td>
        <td class="n more" data-label="Dorm.">${num(x.Dormitorios)}</td>
        <td class="n more" data-label="Baños">${num(x["Baños"])}</td>
        <td class="n more ${x["Antigüedad"] == null ? "dash" : ""}" data-label="Antigüedad">${x["Antigüedad"] == null ? "—" : num(x["Antigüedad"]) + " años"}</td>
        <td class="n more ${x["Mantenimiento (S/)"] == null ? "dash" : ""}" data-label="Mant.">${x["Mantenimiento (S/)"] == null ? "—" : soles(x["Mantenimiento (S/)"])}</td>
        <td class="n more" data-label="S/ por m²">${soles(x["S/ por m²"], 2)}</td>
        <td class="n key"><b>${soles(x["Precio pedido (S/)"])}</b></td></tr>`).join("")}</tbody>
    </table></div>
    <p class="list-foot"><span>Mediana ${soles(c.precio_mediana_soles)} · percentiles 25 y 75: ${soles(c.precio_p25_soles)} y ${soles(c.precio_p75_soles)}</span></p>
    <p class="panel-note">${esc(c.aviso)} Un guion es un dato que el anuncio no informaba.</p>
  </section>`;
}

/* ---------- Accesibilidad ---------- */

function panelAcceso(a) {
  return `<div class="grid">
    <div class="kpis span-6">
      <div class="kpi"><p class="kpi-label">Paradero más cercano</p><p class="kpi-value is-main num">${num(a.dist_paradero_min_m)}<small>m</small></p><p class="delta">${esc(a.paradero_cercano_nombre)}</p></div>
      <div class="kpi"><p class="kpi-label">Paraderos a 500 m</p><p class="kpi-value num">${num(a.paraderos_500m)}</p><p class="delta">${a.paraderos_300m} a 300 m · ${a.paraderos_1000m} a 1 km</p></div>
      <div class="kpi"><p class="kpi-label">Metropolitano</p><p class="kpi-value num">${num(a.dist_troncal_brt_m)}<small>m</small></p><p class="delta">Corredor complementario a ${num(a.dist_corredor_m)} m</p></div>
    </div>
    <section class="panel span-4" aria-labelledby="t-mapa">
      <header><h2 id="t-mapa">Mapa</h2><span class="meta">${esc(a.origen)}</span></header>
      <div class="map" role="img" aria-label="Mapa del departamento y paraderos cercanos"></div>
      <p class="panel-note">Haz clic en el mapa para mover la ubicación del departamento.</p>
      <div class="acceso-msg"></div>
    </section>
    <section class="panel span-2" aria-labelledby="t-paraderos">
      <header><h2 id="t-paraderos">Paraderos cercanos</h2></header>
      <div class="rows">${a.cercanos.map((p) => `<div class="row"><span>${esc(p.Paradero)}<span class="sub">${esc(p.Tipo)}</span></span><b class="num">${num(p["Distancia (m)"])} m</b></div>`).join("")}</div>
      <p class="panel-note">${esc(a.aviso)}</p>
    </section>
  </div>`;
}

function dibujarMapa(elemento, a, mapaAnterior, alClic) {
  if (!window.L) {
    elemento.textContent = "No se pudo cargar el mapa (requiere conexión a internet).";
    return null;
  }
  try {
    mapaAnterior?.remove();
    const centro = L.latLng(a.latitud, a.longitud);
    const mapa = L.map(elemento, { scrollWheelZoom: false }).setView(centro, 15);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap" }).addTo(mapa);
    L.circle(centro, { radius: 500, color: "#111", weight: 1, fillOpacity: 0.03 }).addTo(mapa);
    a.cercanos.forEach((p) => L.circleMarker([p.latitud, p.longitud], { radius: 6, color: "#111", weight: 1.5, fillColor: "#fff", fillOpacity: 1 })
      .bindTooltip(`${esc(p.Paradero)} · ${num(p["Distancia (m)"])} m`).addTo(mapa));
    L.circleMarker(centro, { radius: 9, color: "#fff", weight: 2, fillColor: "#c2510a", fillOpacity: 1 }).bindTooltip("Departamento").addTo(mapa);
    mapa.fitBounds(centro.toBounds(1000), { padding: [10, 10] });
    mapa.on("click", (e) => alClic(e.latlng.lat, e.latlng.lng));
    setTimeout(() => mapa.invalidateSize(), 0);
    return mapa;
  } catch (e) {
    // El mapa es complementario: si falla, el resto del análisis se sigue mostrando.
    console.error("Mapa:", e);
    return null;
  }
}

/* ---------- Tendencia ---------- */

function panelTendencia(t, completo) {
  const nombre = t.serie_propia ? titulo(t.distrito) : "Lima, promedio del BCRP";
  const v = t.validacion;
  const cabecera = `<header><h2 ${completo ? "" : 'id="t-tend"'}>Tendencia del distrito</h2><span class="pill ${t.tendencia === "Al alza" ? "main" : ""}">${esc(t.tendencia)} · ${pct(t.cambio_porcentaje)}</span></header>
    <div class="chart-head"><p class="hint">Serie ${esc(nombre)}${t.serie_propia ? "" : " (el distrito no tiene serie propia)"}, S/ por m² al mes. El promedio de los próximos 4 trimestres frente a los últimos 4.</p>
      <div class="legend"><span><i style="color:#111"></i>Observado</span><span><i style="color:#8a8a8a"></i>Pronóstico SARIMA</span><span><i style="color:#dedcd7;height:8px"></i>Intervalo de 80%</span></div></div>
    <div class="chart">${graficoSerie(t.historia.slice(-20), t.pronostico)}</div>`;
  if (!completo) return cabecera;
  return `<section class="panel" aria-labelledby="t-tend-c">${cabecera.replace("<h2 >", '<h2 id="t-tend-c">')}
    <div class="table-wrap" style="margin-top:16px"><table>
      <thead><tr><th>Método, validado en ${esc(v.trimestres[0])} a ${esc(v.trimestres.at(-1))}</th><th class="n">Error medio</th></tr></thead>
      <tbody>
        <tr><td>SARIMA ${esc(`(${t.orden.join(",")})(${t.orden_estacional.join(",")})`)}</td><td class="n">${num(v.SARIMA.MAPE_porcentaje, 1)}%</td></tr>
        <tr><td>Mismo trimestre del año anterior</td><td class="n">${num(v.naive_estacional.MAPE_porcentaje, 1)}%</td></tr>
        <tr><td>Repetir el último valor</td><td class="n">${num(v.naive.MAPE_porcentaje, 1)}%</td></tr>
      </tbody></table></div>
    <p class="panel-note">${esc(t.aviso)}</p></section>`;
}

function graficoSerie(historia, pronostico) {
  const W = window.innerWidth < 700 ? 360 : 1100, H = window.innerWidth < 700 ? 220 : 240, m = { t: 12, r: 12, b: 30, l: 44 };
  const todos = [...historia.map((h) => h.valor), ...pronostico.flatMap((p) => [p.inferior_80, p.superior_80])];
  const min = Math.min(...todos) * 0.97, max = Math.max(...todos) * 1.03;
  const n = historia.length + pronostico.length;
  const x = (i) => m.l + (i / (n - 1)) * (W - m.l - m.r);
  const y = (v) => H - m.b - ((v - min) / (max - min)) * (H - m.t - m.b);
  const punto = (i, v) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`;
  const base = historia.length - 1, ultimo = historia[base].valor;
  const hist = "M" + historia.map((h, i) => punto(i, h.valor)).join("L");
  const fut = "M" + [punto(base, ultimo), ...pronostico.map((p, i) => punto(base + 1 + i, p.valor))].join("L");
  const banda = "M" + [punto(base, ultimo), ...pronostico.map((p, i) => punto(base + 1 + i, p.superior_80)),
    ...pronostico.map((p, i) => punto(base + 1 + i, p.inferior_80)).reverse()].join("L") + "Z";
  const cada = W < 700 ? 8 : 4;
  const etiquetas = [...historia, ...pronostico].map((p, i) => ({ i, t: p.trimestre })).filter((e) => e.i % cada === 0);
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Serie trimestral y pronóstico">
    <g class="axis">${ticks(min, max, 3).map((v) => `<line x1="${m.l}" x2="${W - m.r}" y1="${y(v)}" y2="${y(v)}" stroke="#ecebe8"/><text x="${m.l - 8}" y="${y(v) + 4}" text-anchor="end">${num(v, 0)}</text>`).join("")}
    ${etiquetas.map((e) => `<text x="${x(e.i)}" y="${H - 8}" text-anchor="middle">${esc(e.t)}</text>`).join("")}</g>
    <path d="${banda}" fill="#dedcd7" fill-opacity="0.7"/>
    <path d="${hist}" fill="none" stroke="#111" stroke-width="2"/>
    <path d="${fut}" fill="none" stroke="#8a8a8a" stroke-width="2" stroke-dasharray="5 4"/>
    ${pronostico.map((p, i) => `<circle cx="${x(base + 1 + i)}" cy="${y(p.valor)}" r="3" fill="#8a8a8a"><title>${esc(p.trimestre)}: ${num(p.valor, 2)}</title></circle>`).join("")}
  </svg>`;
}

/* ---------- Simular ---------- */

function panelSimulador(v) {
  return `<div class="grid">
    <section class="panel span-4" aria-labelledby="t-sim">
      <header><h2 id="t-sim">¿Cuánto cambia el precio con una mejora?</h2><span class="meta">Uso contrafactual del modelo de precio</span></header>
      <form class="sim-form fields" novalidate>
        <div class="field"><label for="s-area">Área (m²)</label><input class="input num" id="s-area" name="area_total" type="number" min="25" max="450" step="1" value="${Math.min(450, Math.round(v.area_total * 1.2))}"></div>
        <div class="field"><label for="s-mant">Mantenimiento (S/)</label><input class="input num" id="s-mant" name="mantenimiento" type="number" min="0" max="5000" step="1" value="${v.mantenimiento ?? 0}"></div>
        <div class="field"><label for="s-balcon">Balcón</label><select class="input" id="s-balcon" name="balcon"><option value="0">No</option><option value="1" ${v.balcon === 1 ? "selected" : ""}>Sí</option></select></div>
        <div class="field"><label for="s-gym">Gimnasio</label><select class="input" id="s-gym" name="gimnasio"><option value="0">No</option><option value="1" ${v.gimnasio === 1 ? "selected" : ""}>Sí</option></select></div>
        <div class="field wide"><button class="btn primary" type="submit">Comparar</button></div>
      </form>
      <div class="sim-out" style="margin-top:16px"></div>
    </section>
    <section class="panel span-2" aria-labelledby="t-area">
      <header><h2 id="t-area">Explora el área</h2></header>
      <p class="hint">La estimación con 20% menos, el área actual y 20% más, sin cambiar nada más.</p>
      <p style="margin-top:12px"><button class="btn" type="button" data-area>Calcular tres áreas</button></p>
      <div class="area-out" style="margin-top:12px"></div>
    </section>
  </div>`;
}

function activarSimulador(contenedor, vivienda, opciones) {
  const form = $(".sim-form", contenedor);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const cambios = Object.fromEntries(["area_total", "mantenimiento", "balcon", "gimnasio"].map((k) => [k, Number(form.elements[k].value)]));
    const salida = $(".sim-out", contenedor);
    try {
      const r = await conBoton($("button", form), "Calculando…", () => llamar("/api/comparar", { cuerpo: { vivienda, cambios } }));
      const lista = Object.entries(r.cambios).map(([k, c]) => `${esc(opciones.etiquetas[k])}: ${esc(c.base ?? "—")} → ${esc(c.alternativa)}`).join(" · ");
      salida.innerHTML = `<div class="kpis">
          <div class="kpi"><p class="kpi-label">Hoy</p><p class="kpi-value num">${soles(r.base_resultado.precio_estimado_soles, 2)}</p></div>
          <div class="kpi"><p class="kpi-label">Con el cambio</p><p class="kpi-value is-main num">${soles(r.alternativa_resultado.precio_estimado_soles, 2)}</p></div>
          <div class="kpi"><p class="kpi-label">Diferencia</p><p class="kpi-value num">${r.diferencia_soles >= 0 ? "+" : "−"}${soles(Math.abs(r.diferencia_soles), 2)}</p><p class="delta">${pct(r.diferencia_porcentaje)} frente a hoy</p></div>
        </div><p class="panel-note">Cambios: ${lista || "ninguno"}. ${esc(r.advertencia)}</p>`;
    } catch (err) {
      mensaje(salida, err.message);
    }
  });
  const boton = $("[data-area]", contenedor);
  boton.addEventListener("click", async () => {
    const salida = $(".area-out", contenedor);
    try {
      const r = await conBoton(boton, "Calculando…", () => llamar("/api/area", { cuerpo: vivienda }));
      const s = r.resumen;
      salida.innerHTML = `<div class="rows">${r.puntos.map((p) => `<div class="row"><span>${num(p.entrada.area_total)} m²${p.factor_area === 1 ? '<span class="sub">actual</span>' : ""}</span><b class="num">${soles(p.resultado.precio_estimado_soles)}</b></div>`).join("")}</div>
        <p class="panel-note">De ${s.area_base_m2} a ${s.area_mayor_m2} m² la estimación ${s.diferencia_base_a_mayor_soles < 0 ? "baja" : "sube"} ${soles(Math.abs(s.diferencia_base_a_mayor_soles), 2)}.
          ${s.hay_descenso_al_aumentar_area ? "Baja al aumentar el área: el modelo no garantiza que más área suba el precio, y no lo corregimos para ocultarlo." : ""}</p>`;
    } catch (err) {
      mensaje(salida, err.message);
    }
  });
}
