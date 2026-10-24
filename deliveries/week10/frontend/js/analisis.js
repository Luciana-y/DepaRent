import { llamar } from "./api.js";
import { $, $$, esc, num, pct, soles, tabla, titulo, conBoton, mensaje } from "./util.js";

/**
 * Dibuja el análisis completo de un departamento (respuesta de /api/analizar).
 * acciones.alMoverUbicacion(lat, lon): clic en el mapa · acciones.alPublicar(escenario): botón de publicar (opcional)
 * acciones.publicacion: publicación vigente del departamento, si existe.
 */
export function mostrarAnalisis(contenedor, a, opciones, acciones = {}) {
  contenedor.innerHTML = `
    <div class="analysis">
      <section class="card hero-card">
        <div class="hero-price">
          <p class="eyebrow">Precio mensual esperado · modelo 3</p>
          <p class="big">${soles(a.precio.precio_estimado_soles)}</p>
          <div class="range" aria-hidden="true">
            <div class="range-track"><span class="range-marker" style="left:${marcador(a.precio)}%"></span></div>
            <div class="range-labels"><span>${soles(a.precio.limite_inferior_soles)}</span><span>${soles(a.precio.limite_superior_soles)}</span></div>
          </div>
          <p class="hint">Rango calibrado: buscó cubrir 9 de cada 10 precios de prueba. No asegura el precio de esta vivienda.</p>
        </div>
        <div class="kpis">
          ${kpi("Mediana del distrito", soles(a.precio.baseline_distrital_soles))}
          ${kpi("Perfil competitivo", esc(a.perfil.perfil.perfil))}
          ${kpi("Accesibilidad", esc(a.accesibilidad.nivel))}
          ${kpi("Tendencia del distrito", esc(a.tendencia.tendencia))}
        </div>
        <p class="note">${evidencia(a.evidencia_distrital)}</p>
        ${avisos(a)}
      </section>

      <section class="card">
        <header class="card-head">
          <div><p class="eyebrow">Modelo 5 · reglas sobre los modelos 1, 3 y 4</p><h2>¿A qué precio publicar?</h2></div>
        </header>
        ${acciones.publicacion ? `<div class="banner ok">Publicado a <b>${soles(acciones.publicacion.precio_soles)}</b> (${esc(acciones.publicacion.escenario)}). Los inquilinos lo ven en la búsqueda.
          <button class="btn small ghost" data-retirar>Retirar publicación</button></div>` : ""}
        <div class="scenarios">${a.publicacion.escenarios.map((s) => escenario(s, acciones)).join("")}</div>
        <p class="note">${esc(a.publicacion.motivo)} ${esc(a.publicacion.aviso)}</p>
        <details class="more"><summary>¿Cómo se calculan los tres precios?</summary><pre>${esc(a.publicacion.reglas)}</pre></details>
        <div class="pub-msg"></div>
      </section>

      <section class="card tabs-card">
        <nav class="tabs" role="tablist">
          ${[["comparables", "Comparables"], ["acceso", "Accesibilidad"], ["tendencia", "Tendencia"], ["simulador", "Simular mejoras"]]
            .map(([id, texto], i) => `<button role="tab" class="tab ${i ? "" : "active"}" data-tab="${id}" aria-selected="${!i}">${texto}</button>`).join("")}
        </nav>
        <div class="tab-panel" data-panel="comparables">${panelComparables(a.perfil)}</div>
        <div class="tab-panel" data-panel="acceso" hidden>${panelAcceso(a.accesibilidad)}</div>
        <div class="tab-panel" data-panel="tendencia" hidden>${panelTendencia(a.tendencia)}</div>
        <div class="tab-panel" data-panel="simulador" hidden>${panelSimulador(a.vivienda)}</div>
      </section>
    </div>`;

  let mapa = null;
  $$(".tab", contenedor).forEach((boton) => boton.addEventListener("click", () => {
    $$(".tab", contenedor).forEach((b) => { b.classList.toggle("active", b === boton); b.setAttribute("aria-selected", b === boton); });
    $$(".tab-panel", contenedor).forEach((p) => { p.hidden = p.dataset.panel !== boton.dataset.tab; });
    if (boton.dataset.tab === "acceso") mapa = dibujarMapa($(".map", contenedor), a.accesibilidad, mapa, moverUbicacion);
  }));

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
  $("[data-retirar]", contenedor)?.addEventListener("click", (e) =>
    conBoton(e.currentTarget, "Retirando…", () => acciones.alRetirar()).catch((err) => mensaje($(".pub-msg", contenedor), err.message)));

  activarSimulador(contenedor, a.vivienda, opciones);
}

const kpi = (etiqueta, valor) => `<div class="kpi"><span>${etiqueta}</span><b>${valor}</b></div>`;
const marcador = (p) => 100 * (p.precio_estimado_soles - p.limite_inferior_soles) / (p.limite_superior_soles - p.limite_inferior_soles);

function evidencia(ev) {
  if (!ev) return "No hubo anuncios de este distrito en la muestra de prueba; no podemos mostrar un error local.";
  return `En ${ev.anuncios_prueba} anuncios de prueba de ${esc(titulo(ev.distrito))} el error absoluto medio fue <b>${soles(ev.error_absoluto_medio_soles, 2)}</b>. ` +
    "Es un promedio de septiembre de 2026, no el error garantizado para esta vivienda.";
}

function avisos(a) {
  const lista = [...a.avisos];
  if (a.evidencia_distrital?.muestra_pequena) lista.unshift("Hay menos de 20 anuncios de prueba en este distrito: el error local es inestable.");
  return lista.map((t) => `<div class="banner warn">${esc(t)}</div>`).join("");
}

function escenario(s, acciones) {
  const indice = ["Competitivo", "Equilibrado", "Renta superior"].indexOf(s.escenario);
  return `<article class="scenario ${s.sugerido ? "sugerido" : ""}">
    ${s.sugerido ? '<span class="tag">Sugerido</span>' : ""}
    <h3>${esc(s.escenario)}</h3>
    <p class="price">${soles(s.precio_soles)}</p>
    <p class="delta ${s.diferencia_vs_esperado_porcentaje >= 0 ? "up" : "down"}">${pct(s.diferencia_vs_esperado_porcentaje)} vs. esperado</p>
    <p>${esc(s.descripcion)}</p>
    <p class="hint">Más caro que el ${num(s.comparables_mas_baratos_porcentaje)}% de los comparables.</p>
    ${acciones.alPublicar ? `<button class="btn small ${s.sugerido ? "primary" : ""}" data-publicar="${indice}">Publicar a ${soles(s.precio_soles)}</button>` : ""}
  </article>`;
}

function panelComparables(c) {
  const p = c.perfil;
  return `<p>Tu departamento se parece al perfil <b>${esc(p.perfil)}</b> (${num(p.anuncios_en_perfil)} anuncios), cuya mitad central pide entre
    <b>${soles(p.precio_p25_perfil_soles)} y ${soles(p.precio_p75_perfil_soles)}</b>. Sus ${c.comparables.length} anuncios más parecidos
    (${c.en_mismo_distrito} en el mismo distrito) piden entre ${soles(c.precio_p25_soles)} y ${soles(c.precio_p75_soles)}, con mediana ${soles(c.precio_mediana_soles)}.</p>
    ${tabla(c.comparables)}
    <p class="note">Modelo 1 · K-Means sin precio + vecinos cercanos. ${esc(c.aviso)} Las celdas con — son datos que el anuncio no informaba.</p>`;
}

function panelAcceso(a) {
  return `<div class="kpis three">
      ${kpi("Paradero más cercano", num(a.dist_paradero_min_m) + " m")}
      ${kpi("Paraderos a 500 m", num(a.paraderos_500m))}
      ${kpi("Metropolitano", num(a.dist_troncal_brt_m) + " m")}
    </div>
    <p>Ubicación: ${esc(a.origen)}. El paradero más cercano es <b>${esc(a.paradero_cercano_nombre)}</b> (${esc(a.paradero_cercano_tipo)},
      afluencia ${esc(String(a.paradero_cercano_afluencia).toLowerCase())}). El ${num(a.porcentaje_anuncios_mas_lejos, 1)}% de los anuncios
      tiene su paradero más cercano a mayor distancia.</p>
    <div class="map" role="img" aria-label="Mapa del departamento y paraderos cercanos"></div>
    <p class="hint">Haz clic en el mapa para mover la ubicación del departamento.</p>
    <div class="acceso-msg"></div>
    ${tabla(a.cercanos.map(({ latitud, longitud, ...resto }) => resto))}
    <p class="note">Modelo 2 · paraderos ATU con cKDTree. ${esc(a.aviso)}</p>`;
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
    L.circle(centro, { radius: 500, color: "#176552", weight: 1, fillOpacity: .05 }).addTo(mapa);
    a.cercanos.forEach((p) => L.circleMarker([p.latitud, p.longitud], { radius: 6, color: "#d9822b", fillOpacity: .85 })
      .bindTooltip(`${esc(p.Paradero)} · ${num(p["Distancia (m)"])} m`).addTo(mapa));
    L.circleMarker(centro, { radius: 10, color: "#176552", fillColor: "#176552", fillOpacity: .9 }).bindTooltip("Departamento").addTo(mapa);
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

function panelTendencia(t) {
  const nombre = t.serie_propia ? titulo(t.distrito) : "Lima (promedio del BCRP)";
  const v = t.validacion;
  return `<p>Serie: <b>${esc(nombre)}</b>${t.serie_propia ? "" : " (el distrito no tiene serie propia)"}. El promedio pronosticado de los próximos
    4 trimestres cambia <b>${pct(t.cambio_porcentaje)}</b> frente a los últimos 4 observados: <b>${esc(t.tendencia.toLowerCase())}</b>.</p>
    <div class="chart">${graficoSerie(t.historia.slice(-20), t.pronostico)}</div>
    <p class="note">Modelo 4 · SARIMA. En validación (${esc(v.trimestres[0])} a ${esc(v.trimestres.at(-1))}) el error medio fue
      ${num(v.SARIMA.MAPE_porcentaje, 1)}% con SARIMA, ${num(v.naive_estacional.MAPE_porcentaje, 1)}% con naive estacional y
      ${num(v.naive.MAPE_porcentaje, 1)}% repitiendo el último valor. ${esc(t.aviso)}</p>`;
}

function graficoSerie(historia, pronostico) {
  const W = 760, H = 260, m = { t: 16, r: 16, b: 34, l: 48 };
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
  const etiquetas = [...historia, ...pronostico].map((p, i) => ({ i, t: p.trimestre })).filter((e) => e.i % 4 === 0 || e.i === n - 1);
  const ticks = [0, 0.5, 1].map((f) => min + f * (max - min));
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Serie trimestral y pronóstico">
    <g class="axis">${ticks.map((v) => `<line x1="${m.l}" x2="${W - m.r}" y1="${y(v)}" y2="${y(v)}" stroke="#dde5e2"/><text x="${m.l - 6}" y="${y(v) + 4}" text-anchor="end">${num(v, 1)}</text>`).join("")}
    ${etiquetas.map((e) => `<text x="${x(e.i)}" y="${H - 12}" text-anchor="middle">${esc(e.t)}</text>`).join("")}</g>
    <path d="${banda}" fill="#fbeedf"/>
    <path d="${hist}" fill="none" stroke="#176552" stroke-width="2.5"/>
    <path d="${fut}" fill="none" stroke="#d9822b" stroke-width="2.5" stroke-dasharray="6 4"/>
    ${pronostico.map((p, i) => `<circle cx="${x(base + 1 + i)}" cy="${y(p.valor)}" r="3.5" fill="#d9822b"><title>${esc(p.trimestre)}: ${num(p.valor, 2)}</title></circle>`).join("")}
  </svg>
  <div class="legend"><span><i style="background:#176552"></i>Observado (S/ por m² al mes)</span><span><i style="background:#d9822b"></i>Pronóstico SARIMA</span><span><i class="band"></i>Intervalo de 80%</span></div>`;
}

function panelSimulador(v) {
  return `<p>Cambia una característica y mira cuánto cambia el precio estimado. Solo se modifica lo que elijas; el resto queda igual.</p>
    <form class="sim-form grid-4">
      <label class="field"><span>Área (m²)</span><input name="area_total" type="number" min="25" max="450" step="1" value="${Math.min(450, Math.round(v.area_total * 1.2))}"></label>
      <label class="field"><span>Mantenimiento (S/)</span><input name="mantenimiento" type="number" min="0" max="5000" step="1" value="${v.mantenimiento ?? 0}"></label>
      <label class="field"><span>Balcón</span><select name="balcon"><option value="0">No</option><option value="1" ${v.balcon === 1 ? "selected" : ""}>Sí</option></select></label>
      <label class="field"><span>Gimnasio</span><select name="gimnasio"><option value="0">No</option><option value="1" ${v.gimnasio === 1 ? "selected" : ""}>Sí</option></select></label>
      <button class="btn" type="submit">Comparar</button>
    </form>
    <div class="sim-out"></div>
    <hr>
    <div class="row-between"><p><b>Explora el área:</b> estimación con −20%, el área actual y +20%.</p><button class="btn" type="button" data-area>Explorar área</button></div>
    <div class="area-out"></div>`;
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
      salida.innerHTML = `<div class="kpis three">
          ${kpi("Actual", soles(r.base_resultado.precio_estimado_soles, 2))}
          ${kpi("Con el cambio", soles(r.alternativa_resultado.precio_estimado_soles, 2))}
          ${kpi("Diferencia", `<span class="${r.diferencia_soles >= 0 ? "up" : "down"}">${r.diferencia_soles >= 0 ? "+" : ""}${soles(r.diferencia_soles, 2)} (${pct(r.diferencia_porcentaje)})</span>`)}
        </div><p class="note">Cambios: ${lista || "ninguno"}. Modelo 6 · uso contrafactual del modelo 3.</p><div class="banner warn">${esc(r.advertencia)}</div>`;
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
      salida.innerHTML = `<p>De ${s.area_base_m2} a ${s.area_mayor_m2} m² la estimación ${s.diferencia_base_a_mayor_soles < 0 ? "baja" : "sube"}
        <b>${soles(Math.abs(s.diferencia_base_a_mayor_soles), 2)}</b> (${pct(s.variacion_base_a_mayor_porcentaje)}).</p>
        ${s.hay_descenso_al_aumentar_area ? '<div class="banner warn">Al menos una estimación baja al aumentar el área. No se corrige para ocultarlo: el modelo no garantiza que más área suba el precio.</div>' : ""}
        ${tabla(r.puntos.map((p) => ({ "Área (m²)": p.entrada.area_total, "Estimación (S/)": p.resultado.precio_estimado_soles,
          "Límite inferior (S/)": p.resultado.limite_inferior_soles, "Límite superior (S/)": p.resultado.limite_superior_soles })))}
        <p class="note">${esc(r.aviso)}</p>`;
    } catch (err) {
      mensaje(salida, err.message);
    }
  });
}
