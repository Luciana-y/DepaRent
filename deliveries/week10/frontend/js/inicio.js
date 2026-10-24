import { llamar, obtenerOpciones, sesion } from "./api.js";
import { $, esc, num, pct, soles, titulo } from "./util.js";

// Caso de ejemplo de la portada: el mismo perfil precargado de Miraflores que usa el profesor.
const EJEMPLO = {
  distrito_norm: "miraflores", area_total: 90, dormitorios: 3, banos: 2, estacionamientos: 1, antiguedad: 8,
  mantenimiento: 400, ascensor: 1, balcon: 1, terraza: 0, piscina: 0, gimnasio: 0, pet_friendly: 1,
};
const DISTRITOS_CARTA = ["miraflores", "lince", "san miguel"];
const LETRAS = ["D", "e", "p", "a", "R", "e", "n", "t"];

export async function vistaInicio(main) {
  const opciones = await obtenerOpciones().catch(() => null);
  // Mercado: la captura que muestra la app. Modelo: entrenado con septiembre y validado con octubre.
  const anuncios = opciones ? num(opciones.mercado.anuncios) : "miles de";
  const captura = opciones?.mercado.captura_texto || "la última captura";
  const val = opciones?.validacion;
  const errorTexto = val ? `Error medio en ${num(val.evaluados)} anuncios nuevos de octubre: <b>${soles(val.mae_soles)} al mes</b>.`
    : "Error medio medido en 629 anuncios de prueba: <b>S/ 553 al mes</b>.";
  const conCuenta = Boolean(sesion());
  main.innerHTML = `
    <div class="home">
      <section class="home-hero">
        <h1 class="lines home-title">
          <span class="line"><span data-line style="--i:0">Se alquila.</span></span>
          <span class="line"><span data-line style="--i:1">¿A cuánto?</span></span>
        </h1>
        <p class="home-lead">DepaRent estima el alquiler de tu departamento, lo compara con ${anuncios} anuncios de Lima y te dice a qué precio publicarlo.</p>
        <p class="home-fact">${errorTexto}</p>
        <div class="hero-stage">
        <img class="hero-foto" src="assets/balcon-en-calle-jiron-ancash-lima-peru.jpg" width="1280" height="1983" fetchpriority="high"
          alt="Balcón de madera sobre un muro rojo en el Jirón Áncash, centro de Lima">
        <form class="cartel" data-ui aria-label="Estimador de alquiler" novalidate>
          <p class="cartel-kind">Departamento en</p>
          <label class="cartel-district"><span class="sr-only">Distrito</span>
            <select name="distrito_norm">${(opciones?.distritos || ["miraflores"]).filter((d) => d !== "otros")
              .map((d) => `<option value="${esc(d)}" ${d === EJEMPLO.distrito_norm ? "selected" : ""}>${esc(titulo(d))}</option>`).join("")}</select>
          </label>
          <div class="cartel-fields">
            <label><input name="area_total" type="number" inputmode="numeric" min="25" max="450" value="${EJEMPLO.area_total}"><span>m²</span></label>
            <label><input name="dormitorios" type="number" inputmode="numeric" min="0" max="10" value="${EJEMPLO.dormitorios}"><span>dorm.</span></label>
            <label><input name="banos" type="number" inputmode="numeric" min="0" max="10" value="${EJEMPLO.banos}"><span>baños</span></label>
          </div>
          <output class="cartel-price" aria-live="polite"><span data-precio><span class="moneda">S/</span>…</span><small>al mes</small></output>
          <p class="cartel-range" data-rango>Calculando con el modelo…</p>
          <a class="cartel-link" href="#/probar">Ver el análisis completo</a>
          <p class="cartel-foot">Informes: modelo DepaRent, entrenado con anuncios de septiembre y validado con los de octubre</p>
        </form>
        </div>
      </section>

      <section class="home-prices" aria-labelledby="titulo-precios">
        <div class="stack">
          <span class="stack-line stack-deco" data-palabra="Competitivo." aria-hidden="true"></span>
          <h2 id="titulo-precios" class="stack-line stack-strong">Tres precios.</h2>
          <span class="stack-line stack-deco" data-palabra="Renta superior." aria-hidden="true"></span>
        </div>
        <div class="prices-row">
        <figure class="price-object" data-ui data-reveal style="--i:1">
          <figcaption>Departamento de 90 m² en Miraflores</figcaption>
          <ol class="price-object-list" data-escenarios>
            <li><span>Competitivo</span><b>S/ —</b></li><li><span>Equilibrado</span><b>S/ —</b></li><li><span>Renta superior</span><b>S/ —</b></li>
          </ol>
        </figure>
        <div class="price-facts" data-reveal style="--i:3">
          <p>No te damos un solo número. El precio equilibrado es lo que estima el modelo; el competitivo se acerca a los anuncios parecidos más baratos para alquilar rápido; el de renta superior se acerca a los más caros.</p>
          <p data-motivo>La tendencia del distrito decide cuál sugerimos: si la serie del BCRP proyecta alza, hay margen para pedir más.</p>
        </div>
        </div>
      </section>

      <section class="home-steps" aria-labelledby="titulo-pasos">
        ${["describes", "comparamos", "ubicamos", "publicas"].map((paso, i) => `
          <div class="step-field step-${paso}">
            ${i === 0 ? '<h2 id="titulo-pasos" class="step-title">Así funciona</h2>' : ""}
            <article class="ficha" data-ui data-paso="${paso}" data-reveal style="--i:${i}">
              <p class="ficha-name">Depa familiar en Miraflores</p>
              <p class="ficha-row">90 m² · 3 dorm. · 2 baños</p>
            </article>
            <p class="step-clause">${["Primero lo describes: área, dormitorios y amenidades.", "Luego lo comparamos con sus anuncios más parecidos.",
              "Después lo ubicamos frente al transporte y su distrito.", "Al final, lo publicas al precio que elijas."][i]}</p>
          </div>`).join("")}
      </section>

      <section class="home-proof" aria-labelledby="titulo-medimos">
        <div class="proof-card" data-reveal>
          <h2 id="titulo-medimos">Lo que medimos</h2>
          <img class="proof-foto" src="assets/buildings-in-miraflores-district-lima-peru.jpg" width="1920" height="1440" loading="lazy" decoding="async"
            alt="Edificios de departamentos sobre el acantilado de Miraflores, bajo el cielo gris de Lima">
          <p>Modelo entrenado con 3,128 anuncios de septiembre&nbsp;·&nbsp;${val ? `probado con ${num(val.evaluados)} anuncios nuevos de octubre&nbsp;·&nbsp;` : ""}3,233 paraderos de la ATU&nbsp;·&nbsp;13 series del BCRP</p>
          <p>Error medio de S/ 553 en septiembre${val ? ` y de ${soles(val.mae_soles)} en octubre` : ""}&nbsp;·&nbsp;el rango cubrió ${val ? Math.round(val.cobertura * 100) : 92} de cada 100 precios${val ? " de octubre" : " de prueba"}&nbsp;·&nbsp;8 comparables por departamento</p>
          <h3>Y lo que no</h3>
          <p>Son precios pedidos, no contratos&nbsp;·&nbsp;la búsqueda es una foto del mercado del ${captura}&nbsp;·&nbsp;paraderos del inventario de 2021&nbsp;·&nbsp;no es una tasación</p>
        </div>
      </section>

      <section class="home-carta" aria-labelledby="titulo-carta">
        <img class="carta-fondo" src="assets/lima-peru-apartments.jpg" width="1630" height="1225" loading="lazy" decoding="async"
          alt="Edificios de departamentos con balcones en Lima">
        <div class="carta" data-reveal>
          <h2 id="titulo-carta">La carta de alquileres</h2>
          <p class="carta-note">Para quien busca: los dos dormitorios más económicos por distrito, comparados con el precio del modelo.</p>
          <div class="carta-groups" data-carta>${DISTRITOS_CARTA.map((d) => `<section class="carta-group"><h3>${esc(titulo(d))}</h3><p class="carta-wait">Cargando…</p></section>`).join("")}</div>
          <p class="carta-close">Anuncios del ${captura}<br><a href="#/buscar">Buscar con tus propios filtros</a></p>
        </div>
      </section>

      <section class="home-about" aria-labelledby="titulo-equipo">
        <h2 id="titulo-equipo" class="about-title">Quiénes somos</h2>
        <p class="about-text" data-reveal style="--i:1"><b>DepaRent</b> es el proyecto de cuatro estudiantes de Ciencia de Datos de
          <mark class="hl-a">UTEC</mark> para el curso <mark class="hl-b">DS3022 Desarrollo de Producto de Datos</mark>, en el ciclo 2026-2.
          <mark class="hl-c">Adrian Urbina Mendoza</mark> coordina el equipo y la calidad de los datos; <mark class="hl-a">Armando Martinez Palomino</mark> integra
          las fuentes de la ATU y del BCRP; <mark class="hl-b">Breysi Salazar Medina</mark> entrena los modelos; <mark class="hl-c">Luciana Yangali Cáceres</mark>
          diseña la aplicación. Partimos de una pregunta que se hace cualquier propietario antes de pegar el cartel en la ventana: ¿a cuánto lo alquilo?
          Reunimos miles de anuncios, paraderos y trece series de precios, y construimos un modelo que estima el alquiler y dice cuánto se equivoca.
          No reemplaza a una tasación: es una segunda opinión con datos.
          <a class="about-link" href="#/probar">Pruébalo con tu departamento.</a></p>
      </section>

      <section class="home-reply" aria-labelledby="titulo-respuesta">
        <img class="reply-fondo" src="assets/malecon-de-miraflores-lima.jpg" width="1920" height="1440" loading="lazy" decoding="async"
          alt="El malecón de Miraflores y el mar bajo el cielo nublado">
        <p class="reply-aside" data-reveal>¿Buscas dónde vivir? No necesitas cuenta: filtra por distrito y presupuesto, y mira si cada precio está por debajo o por encima de lo que estima el modelo. <a href="#/buscar">Buscar departamentos</a></p>
        <div class="reply-card" data-reveal style="--i:1">
          <h2 id="titulo-respuesta">Publica a tu precio</h2>
          <p>Guarda tus departamentos, revisa su análisis cuando quieras y publícalos con el precio que elijas.</p>
          <a class="reply-action" href="${conCuenta ? "#/mis-departamentos" : "#/ingresar?modo=registro"}">${conCuenta ? "Ir a mis departamentos" : "Crear mi cuenta"}</a>
        </div>
      </section>

      <footer class="home-footer">
        <p class="blocks" role="img" aria-label="DepaRent">${LETRAS.map((l, i) => `<span class="bloque bloque-${i % 4}" style="--h:${[100, 72, 86, 64, 96, 70, 82, 90][i]}%" aria-hidden="true">${l}</span>`).join("")}</p>
        <nav class="footer-cols" aria-label="Pie de página">
          <div><h3>Propietarios</h3><a href="#/ingresar?modo=registro">Crear cuenta</a><a href="#/ingresar">Ingresar</a><a href="#/probar">Probar sin cuenta</a></div>
          <div><h3>Inquilinos</h3><a href="#/buscar">Buscar departamentos</a></div>
          <div><h3>Datos</h3><p>Anuncios de Adondevivir y Urbania: modelo con septiembre de 2026, búsqueda con el ${captura}</p><p>Paraderos ATU, mayo de 2021</p><p>Series BCRP, 2013 a 2026</p></div>
          <div><h3>Curso</h3><p>DS3022 Desarrollo de Producto de Datos</p><p>UTEC, Lima · 2026-2</p></div>
        </nav>
        <p class="credits">Fotos de Wikimedia Commons:
          <a href="https://commons.wikimedia.org/wiki/File:Balc%C3%B3n_en_calle_Jir%C3%B3n_Ancash,_Lima,_Per%C3%BA,_2015-07-28,_DD_82.JPG">«Balcón en calle Jirón Ancash»</a> de Diego Delso, <a href="https://creativecommons.org/licenses/by-sa/4.0">CC BY-SA 4.0</a>;
          <a href="https://commons.wikimedia.org/wiki/File:Buildings_in_Miraflores_district,_Lima,_Peru.jpg">«Buildings in Miraflores district»</a> de Ianyou78, <a href="https://creativecommons.org/licenses/by-sa/3.0">CC BY-SA 3.0</a>;
          <a href="https://commons.wikimedia.org/wiki/File:Lima,_Peru_Apartments.jpg">«Lima, Peru Apartments»</a> de Quado678, <a href="https://creativecommons.org/licenses/by-sa/3.0">CC BY-SA 3.0</a>;
          <a href="https://commons.wikimedia.org/wiki/File:Malec%C3%B3n_de_Miraflores_-_Lima.jpg">«Malecón de Miraflores»</a> de Angela Vanessa Ortiz, <a href="https://creativecommons.org/licenses/by-sa/4.0">CC BY-SA 4.0</a>.
          Muestran Lima, no los departamentos de los anuncios.</p>
        <div class="footer-last"><p>Prototipo académico. Precios pedidos en anuncios, no contratos ni tasaciones.</p><a class="footer-top" href="#/">Volver arriba</a></div>
      </footer>
    </div>`;

  activarEstimador($(".cartel", main));
  cargarEjemplo(main);
  cargarCarta($("[data-carta]", main));
  $(".footer-top", main).addEventListener("click", (e) => { e.preventDefault(); window.scrollTo({ top: 0 }); });
}

function activarEstimador(form) {
  const precio = $("[data-precio]", form), rango = $("[data-rango]", form);
  let espera = null, turno = 0;
  async function calcular() {
    const datos = new FormData(form);
    const vivienda = { distrito_norm: datos.get("distrito_norm") };
    for (const campo of ["area_total", "dormitorios", "banos"]) vivienda[campo] = Number(datos.get(campo));
    const actual = ++turno;
    try {
      const r = await llamar("/api/estimar", { cuerpo: vivienda });
      if (actual !== turno) return;
      precio.innerHTML = `<span class="moneda">S/</span>${num(r.precio_estimado_soles)}`;
      rango.textContent = `Rango probable: ${soles(r.limite_inferior_soles)} a ${soles(r.limite_superior_soles)}`;
      form.classList.remove("is-error");
    } catch (e) {
      if (actual !== turno) return;
      precio.innerHTML = '<span class="moneda">S/</span>…';
      rango.textContent = e.estado === 422 ? e.message : "No pudimos calcular ahora. Intenta en unos segundos.";
      form.classList.add("is-error");
    }
  }
  // Sin animación en la cifra: cambia cada vez que el visitante escribe.
  form.addEventListener("input", () => { clearTimeout(espera); espera = setTimeout(calcular, 250); });
  form.addEventListener("submit", (e) => { e.preventDefault(); calcular(); });
  calcular();
}

async function cargarEjemplo(main) {
  let a;
  try {
    a = await llamar("/api/analizar", { cuerpo: { vivienda: EJEMPLO } });
  } catch {
    return;
  }
  $("[data-escenarios]", main).innerHTML = a.publicacion.escenarios.map((s) =>
    `<li class="${s.sugerido ? "is-sugerido" : ""}"><span>${esc(s.escenario)}${s.sugerido ? " · sugerido" : ""}</span><b>${soles(s.precio_soles)}</b></li>`).join("");
  $("[data-motivo]", main).textContent = a.publicacion.motivo;
  const sugerido = a.publicacion.escenarios.find((s) => s.sugerido);
  const c = a.perfil, acc = a.accesibilidad, t = a.tendencia;
  const filas = {
    comparamos: [`Perfil: ${c.perfil.perfil}`, `8 parecidos piden ${soles(c.precio_p25_soles)} a ${soles(c.precio_p75_soles)}`],
    ubicamos: [`Perfil: ${c.perfil.perfil}`, `Paradero a ${num(acc.dist_paradero_min_m)} m · acceso ${acc.nivel.toLowerCase()}`,
      `Distrito ${t.tendencia.toLowerCase()} (${pct(t.cambio_porcentaje)})`],
    publicas: [`Paradero a ${num(acc.dist_paradero_min_m)} m · tendencia ${t.tendencia.toLowerCase()}`,
      `Publicado a ${soles(sugerido.precio_soles)}`, `${sugerido.escenario}, ${pct(sugerido.diferencia_vs_esperado_porcentaje)} sobre lo esperado`],
  };
  for (const [paso, lineas] of Object.entries(filas)) {
    const ficha = $(`[data-paso="${paso}"]`, main);
    ficha.insertAdjacentHTML("beforeend", lineas.map((l, i) => `<p class="ficha-row ${paso === "publicas" && i === 1 ? "ficha-strong" : ""}">${esc(l)}</p>`).join(""));
  }
}

async function cargarCarta(contenedor) {
  const grupos = await Promise.all(DISTRITOS_CARTA.map((d) =>
    llamar("/api/buscar", { cuerpo: { distritos: [d], dormitorios_min: 2, area_min: 45, orden: "precio", limite: 4 } }).catch(() => null)));
  contenedor.innerHTML = DISTRITOS_CARTA.map((d, i) => {
    const r = grupos[i];
    const items = r?.resultados?.length ? r.resultados.map((x) => `
      <li><span class="carta-item">${num(x.dormitorios)} dorm. · ${num(x.area_total)} m²${x.nombre ? ` · ${esc(x.nombre)}` : ""}</span>
        <span class="carta-price">${soles(x.precio_soles)}</span>
        <span class="carta-desc">${esc(x.valoracion)} (${pct(x.diferencia_estimado_porcentaje)}) · paradero a ${num(x.dist_paradero_min_m)} m</span></li>`).join("")
      : '<li class="carta-wait">Sin datos por ahora.</li>';
    return `<section class="carta-group"><h3>${esc(titulo(d))}</h3><ul>${items}</ul></section>`;
  }).join("");
}
