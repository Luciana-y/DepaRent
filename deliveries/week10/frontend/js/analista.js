import { llamar } from "./api.js";
import { esc, num, soles, titulo } from "./util.js";

/* Panel de análisis: KPIs del producto de datos. Solo lo ven las cuentas con rol "analista"
   (correos en DEPARENT_ANALISTAS); la API responde 403 a cualquier otra cuenta. */

const porcentaje = (v, dec = 1) => (v == null ? "—" : `${num(v, dec)}%`);
const kpi = (etiqueta, valor, nota, principal = false) => `<div class="kpi"><p class="kpi-label">${etiqueta}</p>
  <p class="kpi-value num ${principal ? "is-main" : ""}">${valor}</p>${nota ? `<p class="delta">${nota}</p>` : ""}</div>`;
const NOMBRES_ALTERNATIVA = { azar: "elegir al azar", buscador_area: "ordenar por área", buscador_oportunidad: "ordenar por oportunidad", buscador_precio: "ordenar por precio" };

export async function vistaAnalista(lienzo) {
  lienzo.innerHTML = `<div class="title-row"><div><h1>Panel de análisis</h1><p class="sub"><span class="skeleton">Cargando KPIs</span></p></div></div>`;
  let k;
  try {
    k = await llamar("/api/kpis");
  } catch (err) {
    if (err.estado !== 403) throw err;
    lienzo.innerHTML = `<div class="title-row"><div><h1>Panel de análisis</h1></div></div>
      <section class="panel"><div class="empty"><p>Esta sección es solo para el equipo de análisis de DepaRent.</p><a class="btn" href="#/">Volver al inicio</a></div></section>`;
    return;
  }
  const { producto: p, modelo: m, datos: d, recomendador: r } = k;
  const ultima = m.validaciones.at(-1);
  const mejora = ultima ? 100 * (1 - ultima.modelo.mae_soles / ultima.baseline_distrital.mae_soles) : null;
  const desactualizado = d.dias_desde_captura > 7;
  const maxDistrito = Math.max(...d.anuncios_por_distrito.map((x) => x.anuncios), 1);
  const maxMae = Math.max(...m.validaciones.map((v) => v.baseline_distrital.mae_soles), m.prueba.baseline_distrital.mae_soles);
  const filasValidacion = [{ captura: "Prueba (sep.)", evaluados: 629, modelo: m.prueba.modelo, baseline_distrital: m.prueba.baseline_distrital, cobertura_rango_porcentaje: 92 },
    ...m.validaciones];

  lienzo.innerHTML = `
    <div class="title-row"><div><h1>Panel de análisis</h1>
      <p class="sub">KPIs del producto de datos · mercado del ${esc(d.captura_texto)} · modelo entrenado con la ${esc(m.entrenado_con)}</p></div>
      <div class="title-actions"><span class="pill ${desactualizado ? "warn" : "pos"}">${desactualizado ? `Datos con ${num(d.dias_desde_captura)} días` : "Datos al día"}</span>
        <button class="btn" type="button" data-recargar>Actualizar</button></div></div>

    <h2 class="section-title">Uso del producto</h2>
    <div class="kpis kpis-wrap">
      ${kpi("Cuentas", num(p.usuarios), `${num(p.usuarios_nuevos_7_dias)} nuevas en 7 días`, true)}
      ${kpi("Completan el cuestionario", porcentaje(p.tasa_perfil_porcentaje), `${num(p.perfiles_completados)} perfiles de inquilino`)}
      ${kpi("Guardan algún departamento", porcentaje(p.tasa_perfil_a_guardado_porcentaje), `${num(p.usuarios_con_guardados)} de quienes tienen perfil · ${num(p.guardados)} guardados`)}
      ${kpi("Departamentos publicados", `${num(p.departamentos_publicados)} <small>de ${num(p.departamentos)}</small>`, `${porcentaje(p.tasa_publicacion_porcentaje)} de los registrados · ${num(p.propietarios)} propietarios`)}
    </div>
    <div class="kpis kpis-wrap" style="margin-top:var(--gap)">
      ${kpi("Mensajes a propietarios", num(p.mensajes_interesados), `${num(p.mensajes_7_dias)} en 7 días`)}
      ${kpi("Publicados que reciben mensajes", porcentaje(p.tasa_publicado_con_interes_porcentaje), `${num(p.publicados_con_interes)} departamentos`)}
      ${kpi("Publican a precio propio", num(p.publicados_a_precio_propio), "en vez de un precio sugerido")}
      ${kpi("Precio publicado vs. esperado", p.diferencia_media_publicado_vs_esperado_porcentaje == null ? "—" : `${p.diferencia_media_publicado_vs_esperado_porcentaje > 0 ? "+" : ""}${num(p.diferencia_media_publicado_vs_esperado_porcentaje, 1)}%`, "promedio de los publicados")}
    </div>

    <h2 class="section-title">Calidad del modelo de precio</h2>
    <div class="kpis kpis-wrap">
      ${kpi("Error medio (MAE)", ultima ? soles(ultima.modelo.mae_soles) : "—", ultima ? `Validación del ${esc(ultima.captura)} · ${num(ultima.evaluados)} anuncios` : "", true)}
      ${kpi("Mejor que el baseline", mejora == null ? "—" : `${num(mejora, 0)}%`, ultima ? `menos error que la mediana del distrito (${soles(ultima.baseline_distrital.mae_soles)})` : "")}
      ${kpi("Error porcentual (MAPE)", ultima ? porcentaje(ultima.modelo.mape_porcentaje) : "—", ultima ? `R² ${num(ultima.modelo.r2, 3)}` : "")}
      ${kpi("Cobertura del rango", ultima ? porcentaje(ultima.cobertura_rango_porcentaje) : "—", ultima ? `objetivo ${porcentaje(ultima.cobertura_objetivo_porcentaje, 0)} · MAE ${ultima.cambio_mae_porcentaje > 0 ? "+" : ""}${num(ultima.cambio_mae_porcentaje, 1)}% vs. septiembre` : "")}
    </div>
    <section class="panel" style="margin-top:var(--gap)" aria-labelledby="t-val">
      <header><h2 id="t-val">Error medio por evaluación</h2><span class="meta">Modelo frente a la mediana del distrito (baseline)</span></header>
      <div class="table-wrap"><table class="list-table">
        <thead><tr><th>Evaluación</th><th class="n">Anuncios</th><th>Modelo vs. baseline</th><th class="n">MAE modelo</th><th class="n">MAE baseline</th><th class="n">MAPE</th><th class="n">Cobertura</th></tr></thead>
        <tbody>${filasValidacion.map((v) => `<tr>
          <td>${esc(v.captura)}</td><td class="n">${num(v.evaluados)}</td>
          <td class="barras-celda"><div class="barra"><span style="width:${(100 * v.modelo.mae_soles) / maxMae}%"></span></div>
            <div class="barra base"><span style="width:${(100 * v.baseline_distrital.mae_soles) / maxMae}%"></span></div></td>
          <td class="n key"><b>${soles(v.modelo.mae_soles)}</b></td><td class="n">${soles(v.baseline_distrital.mae_soles)}</td>
          <td class="n">${porcentaje(v.modelo.mape_porcentaje)}</td><td class="n">${porcentaje(v.cobertura_rango_porcentaje)}</td></tr>`).join("")}</tbody>
      </table></div>
      <p class="panel-note"><span class="leyenda"><i></i>Modelo</span> <span class="leyenda base"><i></i>Baseline: mediana del distrito</span> · El modelo está congelado: cada fila lo prueba con anuncios que no vio al entrenar.</p>
    </section>

    <div class="grid" style="margin-top:var(--gap)">
      <section class="panel span-3" aria-labelledby="t-datos">
        <header><h2 id="t-datos">Datos del mercado</h2><span class="meta">Captura del ${esc(d.captura)}</span></header>
        <div class="rows kv">
          <div class="row"><span>Días desde la última captura</span><b class="num">${num(d.dias_desde_captura)}</b></div>
          <div class="row"><span>Anuncios descargados</span><b class="num">${num(d.anuncios_en_captura)}</b></div>
          <div class="row"><span>Válidos tras limpiar</span><b class="num">${num(d.validos)} <small class="hint">(${porcentaje(d.porcentaje_validos)})</small></b></div>
          <div class="row"><span>Únicos (sin duplicados)</span><b class="num">${num(d.unicos)}</b></div>
          <div class="row"><span>En la búsqueda de la app</span><b class="num">${num(d.en_la_app)}</b></div>
          <div class="row"><span>Distritos cubiertos</span><b class="num">${num(d.distritos)}</b></div>
          <div class="row"><span>Precio mediano pedido</span><b class="num">${soles(d.precio_mediano_soles)}</b></div>
        </div>
      </section>
      <section class="panel span-3" aria-labelledby="t-dist">
        <header><h2 id="t-dist">Anuncios por distrito</h2><span class="meta">Los ${d.anuncios_por_distrito.length} con más anuncios</span></header>
        <div class="rows kv">${d.anuncios_por_distrito.map((x) => `<div class="row dist-row"><span>${esc(titulo(x.distrito))}</span>
          <div class="barra"><span style="width:${(100 * x.anuncios) / maxDistrito}%"></span></div><b class="num">${num(x.anuncios)}</b></div>`).join("")}</div>
      </section>
    </div>

    ${r ? `<h2 class="section-title">Recomendador para inquilinos</h2>
    <div class="kpis kpis-wrap">
      ${kpi("Precisión en los 12 primeros", porcentaje(100 * r.recomendador.precision, 0), `vs. ${porcentaje(100 * r.mejor_alternativa[1].precision, 0)} al ${esc(NOMBRES_ALTERNATIVA[r.mejor_alternativa[0]] || r.mejor_alternativa[0])}`, true)}
      ${kpi("Cumplen lo pedido", porcentaje(100 * r.recomendador.cumplimiento, 0), "presupuesto, dormitorios y distritos")}
      ${kpi("Calidad del orden (nDCG)", num(r.recomendador.ndcg, 3), "1 es el orden ideal")}
      ${kpi("Perfiles con algún acierto", porcentaje(100 * r.recomendador.acierto, 0), `${num(r.perfiles_evaluados)} perfiles de prueba · ${num(r.recomendador.distritos, 1)} distritos por lista`)}
    </div>` : ""}
    <p class="panel-note">Los KPIs de uso salen de la base de cuentas y no incluyen nombres ni correos. Los del modelo y del recomendador salen de las evaluaciones guardadas en el repositorio (semanas 10 y 12).</p>`;
  lienzo.querySelector("[data-recargar]").addEventListener("click", () => vistaAnalista(lienzo));
}
