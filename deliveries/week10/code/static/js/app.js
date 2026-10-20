// DepaRent Week 10 — interfaz del análisis descriptivo (RF1 + RF2), orientada al propietario.
// Los casos reales y todos los resultados provienen del backend; aquí solo se presentan.

const NUMERIC_FIELDS = ["area_total", "dormitorios", "banos", "antiguedad", "mantenimiento", "latitud", "longitud"];
const OPTIONAL_FIELDS = ["antiguedad", "mantenimiento"];
const NA = "No disponible";
const FEATURE_LABELS = {
  area_total: ["Área total", "m²"],
  dormitorios: ["Dormitorios", ""],
  banos: ["Baños", ""],
  antiguedad: ["Antigüedad", "años"],
  mantenimiento: ["Mantenimiento mensual", "S/"],
};

const AMENITY_LABELS = {};
document.querySelectorAll('input[name="amenidades"]').forEach((input) => {
  AMENITY_LABELS[input.value] = input.parentElement.textContent.trim();
});

const form = document.getElementById("property-form");
const submitBtn = document.getElementById("submit-btn");
const errorsBox = document.getElementById("errors");
const results = document.getElementById("results");
const sourceBadge = document.getElementById("input-source");
let loadedCase = null; // caso real cargado y sin modificar

function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined && text !== null) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function fmt(value, minDigits = 0, maxDigits = minDigits) {
  if (value === null || value === undefined || Number.isNaN(value)) return null;
  return Number(value).toLocaleString("es-PE", { minimumFractionDigits: minDigits, maximumFractionDigits: maxDigits });
}

function withUnit(value, unit, digits = [0, 1]) {
  const text = fmt(value, digits[0], digits[1]);
  if (text === null) return null;
  if (unit === "S/") return `S/ ${text}`;
  return unit ? `${text} ${unit}` : text;
}

function cell(value, digits = [0, 0], className = "num") {
  const td = el("td", null, className);
  const text = fmt(value, digits[0], digits[1]);
  if (text === null) {
    td.textContent = NA;
    td.classList.add("na");
  } else {
    td.textContent = text;
  }
  return td;
}

function amenityList(keys) {
  return keys.map((k) => AMENITY_LABELS[k] || k).join(", ");
}

// ---------- Casos reales del dataset ----------

function setSource(caseData) {
  loadedCase = caseData;
  if (caseData) {
    sourceBadge.textContent = `Caso real del dataset: anuncio ${caseData.id_anuncio} · ${caseData.fuente} · capturado ${String(caseData.fecha_scraping).slice(0, 10)}`;
    sourceBadge.classList.add("real");
  } else {
    sourceBadge.textContent = "Ingreso manual";
    sourceBadge.classList.remove("real");
  }
}

function fillCase(caseData) {
  form.reset();
  const p = caseData.property;
  for (const name of NUMERIC_FIELDS.concat(["distrito"])) {
    form.elements[name].value = p[name] === undefined ? "" : p[name];
  }
  form.querySelectorAll('input[name="amenidades"]').forEach((c) => { c.checked = p.amenidades.includes(c.value); });
  setSource(caseData);
}

async function loadCases() {
  const box = document.getElementById("example-cases");
  try {
    const resp = await fetch("/api/example-properties");
    if (!resp.ok) throw new Error(String(resp.status));
    const body = await resp.json();
    box.replaceChildren();
    body.cases.forEach((c, i) => {
      const btn = el("button", `Caso ${i + 1} · ${c.property.distrito} · ${fmt(c.property.area_total, 0, 1)} m²`, "case-btn");
      btn.type = "button";
      btn.title = `Anuncio ${c.id_anuncio} (${c.fuente})`;
      btn.addEventListener("click", () => fillCase(c));
      box.appendChild(btn);
    });
  } catch (err) {
    box.replaceChildren(el("span", "No se pudieron cargar los casos reales.", "na"));
  }
}

// Cualquier edición convierte el análisis en ingreso manual.
["input", "change"].forEach((evt) => form.addEventListener(evt, () => { if (loadedCase) setSource(null); }));

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
  if (loadedCase) payload.id_anuncio_origen = loadedCase.id_anuncio;
  return payload;
}

// ---------- Resultados ----------

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

function renderProfile(cp, dataset) {
  const p = cp.cluster_profile;
  const head = el("p", cp.cluster_name, "profile-name");
  const id = el("p", `Segmento ${cp.cluster_id} · ${fmt(p.n)} anuncios (${fmt(p.pct, 1, 1)}% de los ${fmt(dataset.properties_reference_count)} anuncios de referencia)`, "profile-id");
  const intro = el("p", "Tu inmueble se aproxima a un segmento caracterizado por:");
  const ul = el("ul", null, "profile-stats");
  ul.appendChild(el("li", `área mediana: ${fmt(p.area_total.mediana, 0, 1)} m² (rango intercuartílico ${fmt(p.area_total.p25, 0, 1)}–${fmt(p.area_total.p75, 0, 1)} m²);`));
  ul.appendChild(el("li", `dormitorios (mediana): ${fmt(p.dormitorios.mediana)}; baños (mediana): ${fmt(p.banos.mediana)};`));
  ul.appendChild(el("li", `antigüedad mediana: ${fmt(p.antiguedad.mediana, 0, 1)} años;`));
  ul.appendChild(el("li", `mantenimiento mediano: S/ ${fmt(p.mantenimiento.mediana)} por mes;`));
  const top = Object.entries(p.amenidades_pct).sort((a, b) => b[1] - a[1]).slice(0, 4)
    .map(([k, v]) => `${AMENITY_LABELS[k] || k} (${fmt(v, 1, 1)}%)`).join(", ");
  ul.appendChild(el("li", `amenidades con mayor prevalencia en el segmento: ${top}.`));
  document.getElementById("profile").replaceChildren(head, id, intro, ul);
}

function renderSegmentComparison(sc) {
  const body = document.getElementById("segment-body");
  body.replaceChildren();
  sc.numericas.forEach((row) => {
    const [label, unit] = FEATURE_LABELS[row.variable];
    const tr = document.createElement("tr");
    tr.appendChild(el("td", label));
    let own = withUnit(row.inmueble, unit);
    let ownClass = "num";
    if (own === null) {
      own = row.imputado_para_perfil === null ? "No informado"
        : `No informado (para el perfil se usó ${withUnit(row.imputado_para_perfil, unit)})`;
      ownClass = "num na";
    }
    tr.appendChild(el("td", own, ownClass));
    tr.appendChild(el("td", withUnit(row.mediana_segmento, unit) ?? NA, "num"));
    const iqr = row.p25_segmento === null ? NA : `${withUnit(row.p25_segmento, unit)} – ${withUnit(row.p75_segmento, unit)}`;
    tr.appendChild(el("td", iqr, "num"));
    body.appendChild(tr);
  });
  const present = sc.amenidades.filter((a) => a.presente_en_inmueble);
  document.getElementById("segment-amenities").textContent = present.length === 0
    ? "El inmueble no registra amenidades."
    : "Amenidades del inmueble y su presencia en el segmento: "
      + present.map((a) => `${AMENITY_LABELS[a.amenidad] || a.amenidad} (${fmt(a.prevalencia_segmento_pct, 1, 1)}% de los anuncios del segmento)`).join(", ") + ".";
}

function renderComparables(items, method) {
  const body = document.getElementById("comparables-body");
  body.replaceChildren();
  items.forEach((c) => {
    const tr = document.createElement("tr");
    const td = el("td", c.distrito);
    if (!c.mismo_distrito) td.appendChild(el("span", "otro distrito", "tag"));
    tr.appendChild(td);
    tr.appendChild(cell(c.area_total, [0, 1]));
    tr.appendChild(cell(c.dormitorios));
    tr.appendChild(cell(c.banos));
    tr.appendChild(cell(c.antiguedad, [0, 1]));
    tr.appendChild(cell(c.mantenimiento));
    tr.appendChild(el("td", c.amenidades.length ? amenityList(c.amenidades) : "Ninguna mencionada", c.amenidades.length ? "wrap" : "wrap na"));
    tr.appendChild(cell(c.precio_soles_observado));
    tr.appendChild(cell(c.precio_m2_real_observado, [2, 2]));
    tr.appendChild(cell(c.distancia_similitud, [2, 2]));
    tr.appendChild(el("td", c.fuente || NA));
    body.appendChild(tr);
  });
  const desc = document.getElementById("comparables-method");
  if (method.strategy === "mismo_cluster_mismo_distrito") {
    desc.textContent = `${items.length} anuncios del mismo segmento y del mismo distrito (${method.distrito_consultado}), ordenados por similitud en características físicas y amenidades.`;
  } else {
    desc.textContent = `Solo hay ${method.candidatos_mismo_distrito} anuncios del mismo segmento en ${method.distrito_consultado}; se completó con los más similares del mismo segmento en otros distritos (marcados como "otro distrito").`;
  }
}

function renderMetrics(target, metrics) {
  const dl = document.getElementById(target);
  dl.replaceChildren();
  metrics.forEach(([label, text]) => {
    const wrap = document.createElement("div");
    wrap.appendChild(el("dt", label));
    wrap.appendChild(el("dd", text === null || text === undefined ? NA : text, text === null || text === undefined ? "na" : ""));
    dl.appendChild(wrap);
  });
}

function renderSummary(s) {
  const range = s.minimo_precio_publicado === null ? null
    : `${withUnit(s.minimo_precio_publicado, "S/")} – ${withUnit(s.maximo_precio_publicado, "S/")}`;
  renderMetrics("comparables-summary", [
    ["Mediana de precio publicado", withUnit(s.mediana_precio_publicado, "S/")],
    ["Rango observado", range],
    ["Mediana de precio publicado por m²", withUnit(s.mediana_precio_publicado_m2, "S/", [2, 2])],
    ["Comparables con precio publicado", `${s.n_con_precio_publicado} de ${s.n_comparables}`],
  ]);
}

function renderAccessibility(a) {
  const m = (v) => withUnit(v, "m", [1, 1]);
  renderMetrics("accessibility", [
    ["Distancia al paradero más cercano", m(a.dist_paradero_min_m)],
    ["Paradero más cercano", a.paradero_cercano_nombre || null],
    ["Tipo del paradero más cercano", a.paradero_cercano_tipo || null],
    ["Paraderos a 300 m o menos", fmt(a.paraderos_300m)],
    ["Paraderos a 500 m o menos", fmt(a.paraderos_500m)],
    ["Paraderos a 1,000 m o menos", fmt(a.paraderos_1000m)],
    ["Distancia a la troncal BRT (Metropolitano)", m(a.dist_troncal_brt_m)],
    ["Distancia al paradero de corredor más cercano", m(a.dist_corredor_m)],
  ]);
  const src = a.fuente || {};
  document.getElementById("accessibility-detail").textContent = src.n_paraderos
    ? ` ${fmt(src.n_paraderos)} paraderos, corte ${(src.corte_datos || []).map((d) => d.slice(0, 10)).join(", ")}.`
    : "";
}

function renderDataset(ds) {
  document.getElementById("dataset-detail").textContent =
    ` Base de referencia: ${fmt(ds.properties_reference_count)} anuncios procesados (captura ${ds.capture_dates.join(", ")}).`;
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
    renderProfile(body.competitive_profile, body.meta.dataset);
    renderSegmentComparison(body.segment_comparison);
    renderDataset(body.meta.dataset);
    renderComparables(body.comparables, body.comparables_method);
    renderSummary(body.comparables_summary);
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

loadCases();
