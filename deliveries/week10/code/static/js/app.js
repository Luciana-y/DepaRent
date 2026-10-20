// DepaRent Week 10 — interfaz del análisis descriptivo (RF1 + RF2).
// Los resultados provienen siempre de POST /analyze; aquí solo se presentan.

// Ejemplos de entrada (no de resultados), derivados de anuncios reales del dataset con
// pequeñas modificaciones, uno por perfil competitivo (cluster 0, 1 y 2).
const EXAMPLES = {
  A: { distrito: "Miraflores", area_total: 165, dormitorios: 3, banos: 3, antiguedad: 15, mantenimiento: 550,
       amenidades: ["ascensor", "terraza"], latitud: -12.1183, longitud: -77.0402 },
  B: { distrito: "Jesus Maria", area_total: 72, dormitorios: 2, banos: 2, antiguedad: 10,
       amenidades: [], latitud: -12.073, longitud: -77.0503 },
  C: { distrito: "Magdalena", area_total: 65, dormitorios: 2, banos: 2, antiguedad: 1, mantenimiento: 260,
       amenidades: ["balcon", "piscina", "gimnasio", "parrilla", "seguridad_24_7", "coworking"],
       latitud: -12.0931, longitud: -77.06 },
};

const NUMERIC_FIELDS = ["area_total", "dormitorios", "banos", "antiguedad", "mantenimiento", "latitud", "longitud"];
const OPTIONAL_FIELDS = ["antiguedad", "mantenimiento"];
const NA = "No disponible";

const AMENITY_LABELS = {};
document.querySelectorAll('input[name="amenidades"]').forEach((el) => {
  AMENITY_LABELS[el.value] = el.parentElement.textContent.trim();
});

const form = document.getElementById("property-form");
const submitBtn = document.getElementById("submit-btn");
const errorsBox = document.getElementById("errors");
const results = document.getElementById("results");

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function fmt(value, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return null;
  return Number(value).toLocaleString("es-PE", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function cell(value, digits = 0) {
  const td = document.createElement("td");
  const text = fmt(value, digits);
  td.className = "num";
  if (text === null) {
    td.textContent = NA;
    td.classList.add("na");
  } else {
    td.textContent = text;
  }
  return td;
}

function collectPayload() {
  const data = new FormData(form);
  const payload = { distrito: data.get("distrito") || null, amenidades: data.getAll("amenidades") };
  for (const name of NUMERIC_FIELDS) {
    const raw = (data.get(name) || "").trim();
    if (raw === "") {
      if (!OPTIONAL_FIELDS.includes(name)) payload[name] = null;
      continue;
    }
    payload[name] = Number(raw);
  }
  return payload;
}

function fillExample(key) {
  const ex = EXAMPLES[key];
  form.reset();
  for (const [name, value] of Object.entries(ex)) {
    if (name === "amenidades") continue;
    form.elements[name].value = value;
  }
  form.querySelectorAll('input[name="amenidades"]').forEach((c) => { c.checked = ex.amenidades.includes(c.value); });
}

function showErrors(details) {
  errorsBox.replaceChildren(el("strong", "No se pudo analizar el inmueble:"));
  const ul = el("ul");
  details.forEach((d) => ul.appendChild(el("li", d)));
  errorsBox.appendChild(ul);
  errorsBox.hidden = false;
}

function renderWarnings(warnings) {
  const box = document.getElementById("warnings");
  if (!warnings || warnings.length === 0) { box.hidden = true; return; }
  box.replaceChildren(el("strong", "Notas sobre los datos utilizados:"));
  const ul = el("ul");
  warnings.forEach((w) => ul.appendChild(el("li", w)));
  box.appendChild(ul);
  box.hidden = false;
}

function renderProfile(cp) {
  const box = document.getElementById("profile");
  const p = cp.cluster_profile;
  const head = el("p", cp.cluster_name, "profile-name");
  const id = el("p", `Segmento ${cp.cluster_id} · ${fmt(p.n)} anuncios (${fmt(p.pct, 1)}% del dataset)`, "profile-id");
  const intro = el("p", "Tu inmueble se aproxima a un segmento caracterizado por:");
  const ul = el("ul", null, "profile-stats");
  ul.appendChild(el("li", `área mediana: ${fmt(p.area_total.mediana)} m² (rango intercuartil ${fmt(p.area_total.p25)}–${fmt(p.area_total.p75)} m²);`));
  ul.appendChild(el("li", `dormitorios típicos (mediana): ${fmt(p.dormitorios.mediana)}; baños típicos (mediana): ${fmt(p.banos.mediana)};`));
  ul.appendChild(el("li", `antigüedad mediana: ${fmt(p.antiguedad.mediana)} años;`));
  ul.appendChild(el("li", `mantenimiento mediano: S/ ${fmt(p.mantenimiento.mediana)} por mes;`));
  const top = Object.entries(p.amenidades_pct).sort((a, b) => b[1] - a[1]).slice(0, 4)
    .map(([k, v]) => `${AMENITY_LABELS[k] || k} (${fmt(v, 1)}%)`).join(", ");
  ul.appendChild(el("li", `amenidades más frecuentes en el segmento: ${top}.`));
  box.replaceChildren(head, id, intro, ul);
}

function renderComparables(items, method) {
  const body = document.getElementById("comparables-body");
  body.replaceChildren();
  items.forEach((c) => {
    const tr = document.createElement("tr");
    const td = el("td", c.distrito);
    if (!c.mismo_distrito) td.appendChild(el("span", "otro distrito", "tag"));
    tr.appendChild(td);
    tr.appendChild(cell(c.area_total, 0));
    tr.appendChild(cell(c.dormitorios));
    tr.appendChild(cell(c.banos));
    tr.appendChild(cell(c.antiguedad));
    tr.appendChild(cell(c.mantenimiento));
    tr.appendChild(cell(c.precio_soles_observado));
    tr.appendChild(cell(c.distancia_similitud, 2));
    body.appendChild(tr);
  });
  const desc = document.getElementById("comparables-method");
  if (method.strategy === "mismo_cluster_mismo_distrito") {
    desc.textContent = `${items.length} anuncios del mismo segmento y del mismo distrito (${method.distrito_consultado}), ordenados por similitud en características físicas y amenidades.`;
  } else {
    desc.textContent = `Solo hay ${method.candidatos_mismo_distrito} anuncios del mismo segmento en ${method.distrito_consultado}; se completó con los más similares del mismo segmento en otros distritos (marcados como "otro distrito").`;
  }
}

function renderAccessibility(a) {
  const metrics = [
    ["Distancia al paradero más cercano", a.dist_paradero_min_m, (v) => `${fmt(v, 1)} m`],
    ["Tipo del paradero más cercano", a.paradero_cercano_tipo, (v) => v],
    ["Paradero más cercano", a.paradero_cercano_nombre, (v) => v],
    ["Paraderos a menos de 300 m", a.paraderos_300m, (v) => fmt(v)],
    ["Paraderos a menos de 500 m", a.paraderos_500m, (v) => fmt(v)],
    ["Paraderos a menos de 1,000 m", a.paraderos_1000m, (v) => fmt(v)],
    ["Distancia a la troncal BRT (Metropolitano)", a.dist_troncal_brt_m, (v) => `${fmt(v, 1)} m`],
    ["Distancia al paradero de corredor más cercano", a.dist_corredor_m, (v) => `${fmt(v, 1)} m`],
  ];
  const dl = document.getElementById("accessibility");
  dl.replaceChildren();
  metrics.forEach(([label, value, format]) => {
    const wrap = document.createElement("div");
    wrap.appendChild(el("dt", label));
    const available = value !== null && value !== undefined && value !== "";
    wrap.appendChild(el("dd", available ? format(value) : NA, available ? "" : "na"));
    dl.appendChild(wrap);
  });
  if (a.fuente && a.fuente.corte_datos) {
    document.getElementById("accessibility-note").textContent =
      `Indicadores calculados a partir del inventario georreferenciado ATU utilizado en el proyecto (${fmt(a.fuente.n_paraderos)} paraderos, corte ${a.fuente.corte_datos.map((d) => d.slice(0, 10)).join(", ")}).`;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorsBox.hidden = true;
  if (!form.reportValidity()) return;
  submitBtn.disabled = true;
  submitBtn.textContent = "Analizando…";
  try {
    const resp = await fetch("/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectPayload()),
    });
    let body;
    try { body = await resp.json(); } catch { body = null; }
    if (!resp.ok) {
      results.hidden = true;
      showErrors((body && body.details) || [`Error ${resp.status} del servidor.`]);
      return;
    }
    renderWarnings(body.warnings);
    renderProfile(body.competitive_profile);
    renderComparables(body.comparables, body.comparables_method);
    renderAccessibility(body.accessibility);
    results.hidden = false;
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    results.hidden = true;
    showErrors(["No se pudo conectar con el servidor."]);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Analizar inmueble";
  }
});

document.querySelectorAll("[data-example]").forEach((btn) => {
  btn.addEventListener("click", () => fillExample(btn.dataset.example));
});
