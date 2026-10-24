"""Interfaz local: estimaciones guardadas y comparación explicada."""
import copy
import json
import joblib
import pandas as pd
import streamlit as st
from modelo import ROOT, BINARY, LIMITS, predecir
from escenarios import ADVERTENCIA, comparar, csv_comparacion, json_comparacion, verificar_modelo_congelado
from ayuda_interfaz import ETIQUETAS, avisos_coherencia, tabla_entrada, tabla_comparacion
from ayuda_interfaz import mostrar_valor
from laboratorio_area import AVISO, explorar_area, tabla_area, csv_area
from evidencia_distrital import evidencia_distrital
from perfil_competitivo import ARCHIVO as ARCHIVO_PERFIL, comparables
from accesibilidad import accesibilidad, centro_distrito

st.set_page_config(page_title="DepaRent | Explora un alquiler", page_icon="🏠", layout="centered")
st.title("DepaRent")
st.markdown("### Explora un alquiler. Entiende sus límites.")
st.caption("Describe un departamento, revisa una estimación mensual en soles y compara un escenario. Precios de anuncios, no contratos ni tasaciones.")

@st.cache_resource
def cargar():
    verificar_modelo_congelado()
    return joblib.load(ROOT / "models/modelo_docente.joblib")

if not (ROOT / "models/modelo_docente.joblib").exists():
    st.error("Falta el archivo del modelo. Extrae de nuevo la carpeta completa para abrir la aplicación.")
    st.stop()
artifact = cargar()

@st.cache_resource
def cargar_perfil():
    return joblib.load(ARCHIVO_PERFIL) if ARCHIVO_PERFIL.exists() else None

perfil_artifact = cargar_perfil()
demos =json.loads((ROOT / "data/demo_casos.json").read_text(encoding="utf-8"))

st.header("1. Describe el departamento")
selected = st.selectbox("Caso inicial", [d["nombre"] for d in demos])
default = next(d["entrada"] for d in demos if d["nombre"] == selected)
estimate_key = "estimacion_guardada_" + selected
initial = st.session_state.get(estimate_key, {}).get("entrada", default)
st.caption("Los perfiles son hipotéticos. Puedes editar sus características; solo se recalculan al pulsar Estimar alquiler.")
with st.form("vivienda"):
    values = {}
    values["distrito_norm"] = st.selectbox("Distrito", artifact["distritos"], index=artifact["distritos"].index(initial["distrito_norm"]), key=selected + "district")
    columns = st.columns(2)
    for i, (name, limits) in enumerate(LIMITS.items()):
        with columns[i % 2]:
            values[name] = st.number_input(ETIQUETAS[name], min_value=int(limits[0]), max_value=int(limits[1]), value=initial[name], step=1, key=selected + name)
    st.write("Amenidades")
    amenity_columns = st.columns(2)
    for i, name in enumerate(BINARY):
        with amenity_columns[i % 2]:
            value = st.selectbox(ETIQUETAS[name], ["No", "Sí", "Desconocido"], index={0: 0, 1: 1, None: 2}[initial[name]], key=selected + name)
            values[name] = {"No": 0, "Sí": 1, "Desconocido": None}[value]
    submitted = st.form_submit_button("Estimar alquiler", type="primary")
if submitted:
    try:
        result = predecir(values, artifact)
    except ValueError as exc:
        st.session_state.pop(estimate_key, None)
        st.error(str(exc))
    else:
        st.session_state[estimate_key] = {"entrada": copy.deepcopy(values), "resultado": result}

st.header("2. Revisa la estimación")
if estimate_key not in st.session_state:
    st.info("Completa el formulario y pulsa Estimar alquiler. Aquí aparecerán el precio, su rango y las entradas utilizadas.")
else:
    saved = st.session_state[estimate_key]
    used, result = saved["entrada"], saved["resultado"]
    if values != used:
        st.warning("Hay cambios en el formulario sin calcular. El resultado y la descarga conservan las entradas guardadas que se muestran abajo; pulsa Estimar alquiler para actualizarlos.")
    with st.container(border=True):
        st.caption("ÚLTIMA ESTIMACIÓN GUARDADA · " + selected)
        st.metric("Precio mensual estimado", f"S/ {result['precio_estimado_soles']:,.2f}")
        st.write(f"Rango calibrado: **S/ {result['limite_inferior_soles']:,.2f} a S/ {result['limite_superior_soles']:,.2f}**")
        st.caption("El número central es una estimación, no una oferta garantizada. El rango comunica incertidumbre: es amplio y no asegura el precio de esta vivienda.")
        reference, support = st.columns(2)
        reference.metric("Referencia del distrito", f"S/ {result['baseline_distrital_soles']:,.0f}")
        support.metric("Anuncios de entrenamiento en el distrito", result["anuncios_entrenamiento_distrito"])
        st.caption("La referencia es una mediana aprendida con entrenamiento. El conteo no demuestra que exista una vivienda comparable con esta combinación exacta.")
        district_evidence = evidencia_distrital(used["distrito_norm"])
        st.markdown("**Lo que pasó en la prueba de este distrito**")
        if district_evidence is None:
            st.caption("No hubo anuncios de este distrito en la muestra reservada para prueba; no podemos mostrar un error local.")
        else:
            n = district_evidence["anuncios_prueba"]
            mae = district_evidence["error_absoluto_medio_soles"]
            st.write(f"En {n} anuncios reservados de {used['distrito_norm'].title()}, el error absoluto medio observado fue S/ {mae:,.2f}.")
            if district_evidence["muestra_pequena"]:
                st.warning("Hay menos de 20 anuncios de prueba en este distrito. La cifra es inestable; no la usen para afirmar precisión local.")
            st.caption("Son anuncios de septiembre de 2026. Este promedio histórico no es el error esperado ni un margen garantizado para esta vivienda; la prueba no mide meses futuros.")
        for warning in result["advertencias"] + avisos_coherencia(used):
            st.warning(warning)
        st.markdown("**Entradas usadas para este resultado**")
        st.caption("Editar el formulario no cambia esta tabla ni la descarga hasta volver a estimar.")
        st.dataframe(pd.DataFrame(tabla_entrada(used)), hide_index=True, width="stretch", height=495)
        st.download_button("Descargar resultado", json.dumps(saved, ensure_ascii=False, indent=2, allow_nan=False), "estimacion_deparent.json", "application/json", key="descarga_estimacion_" + selected)

with st.expander("¿Qué significan la muestra, el error y el rango?"):
    st.write("Se reservaron 629 anuncios para probar el modelo. Esos anuncios no se usaron para ajustar el modelo ni calibrar su rango. Otros 500 se usaron para calibración y 1,999 para entrenamiento.")
    scores = artifact["metricas"]["metricas_prueba"]
    st.dataframe(pd.DataFrame(scores).T.round(2), width="stretch")
    st.caption("MAE es el promedio del error absoluto en soles; MAPE es el error porcentual medio. No garantizan el error de un caso individual.")
    interval = artifact["metricas"]["intervalo"]
    st.write(f"El rango buscó un nivel nominal de 90%. En prueba cubrió el precio anunciado en {interval['cobertura_observada_prueba']:.2%} de los casos. No garantiza esa cobertura en el futuro ni en cada distrito.")
    st.caption("Anuncios capturados en septiembre de 2026. Se agruparon posibles duplicados; la revisión de datos y de valores extremos sigue siendo necesaria.")

st.divider()
st.header("3. Perfil competitivo y comparables")
if perfil_artifact is None:
    st.warning("Falta models/perfil_competitivo.joblib. Ejecuta python entrenar_perfil.py desde la carpeta code.")
elif estimate_key not in st.session_state:
    st.info("Estima el alquiler en el paso 1 para ubicar el departamento en un perfil del mercado y ver anuncios parecidos.")
else:
    used = st.session_state[estimate_key]["entrada"]
    competencia = comparables(used, perfil_artifact)
    perfil = competencia["perfil"]
    with st.container(border=True):
        st.caption("PERFIL COMPETITIVO · usa las entradas de la última estimación guardada")
        st.metric("Perfil del departamento", perfil["perfil"])
        st.write(f"En este perfil hay {perfil['anuncios_en_perfil']:,} anuncios. La mitad central pide entre "
                 f"**S/ {perfil['precio_p25_perfil_soles']:,.0f} y S/ {perfil['precio_p75_perfil_soles']:,.0f}** "
                 f"(mediana S/ {perfil['precio_mediana_perfil_soles']:,.0f}).")
        st.markdown(f"**Los {len(competencia['comparables'])} anuncios más parecidos** "
                    f"({competencia['en_mismo_distrito']} en el mismo distrito)")
        st.dataframe(pd.DataFrame(competencia["comparables"]), hide_index=True, width="stretch")
        st.write(f"Precio pedido de estos comparables: S/ {competencia['precio_p25_soles']:,.0f} a "
                 f"S/ {competencia['precio_p75_soles']:,.0f} (percentiles 25 y 75), mediana S/ {competencia['precio_mediana_soles']:,.0f}.")
        st.caption(competencia["aviso"] + " Las celdas vacías son datos que el anuncio no informaba.")

st.divider()
st.header("4. Accesibilidad a transporte público")
if estimate_key not in st.session_state:
    st.info("Estima el alquiler en el paso 1 para revisar los paraderos cercanos al departamento.")
else:
    distrito = st.session_state[estimate_key]["entrada"]["distrito_norm"]
    centro = centro_distrito(distrito) or (-12.0464, -77.0428)
    st.caption("Sin dirección exacta se usa el centro aproximado del distrito (mediana de las coordenadas de sus anuncios). "
               "Puedes reemplazarlo con las coordenadas del departamento, por ejemplo copiándolas de un mapa.")
    with st.form("ubicacion"):
        location_columns = st.columns(2)
        lat = location_columns[0].number_input("Latitud", min_value=-12.35, max_value=-11.75, value=centro[0], step=0.0005, format="%.6f", key=f"lat_{selected}_{distrito}")
        lon = location_columns[1].number_input("Longitud", min_value=-77.20, max_value=-76.80, value=centro[1], step=0.0005, format="%.6f", key=f"lon_{selected}_{distrito}")
        located = st.form_submit_button("Calcular accesibilidad")
    access_key = "accesibilidad_" + selected
    if located:
        try:
            st.session_state[access_key] = {"distrito": distrito, "origen": "coordenadas ingresadas", "resultado": accesibilidad(lat, lon)}
        except ValueError as exc:
            st.error(str(exc))
    saved_access = st.session_state.get(access_key)
    if saved_access is None or saved_access["distrito"] != distrito:
        saved_access = {"distrito": distrito, "origen": "centro aproximado del distrito", "resultado": accesibilidad(*centro)}
    acceso = saved_access["resultado"]
    with st.container(border=True):
        st.caption(f"ACCESIBILIDAD · {saved_access['origen']} ({acceso['latitud']:.5f}, {acceso['longitud']:.5f})")
        first, second, third = st.columns(3)
        first.metric("Nivel de accesibilidad", acceso["nivel"])
        second.metric("Paradero más cercano", f"{acceso['dist_paradero_min_m']:,.0f} m")
        third.metric("Paraderos a 500 m", acceso["paraderos_500m"])
        st.write(f"El paradero más cercano es **{acceso['paradero_cercano_nombre']}** ({acceso['paradero_cercano_tipo']}, afluencia {acceso['paradero_cercano_afluencia'].lower()}). "
                 f"El {acceso['porcentaje_anuncios_mas_lejos']:.1f}% de los anuncios tiene su paradero más cercano a mayor distancia. "
                 f"Metropolitano a {acceso['dist_troncal_brt_m']:,.0f} m · corredor complementario a {acceso['dist_corredor_m']:,.0f} m · "
                 f"{acceso['paraderos_300m']} paraderos a 300 m y {acceso['paraderos_1000m']} a 1 km.")
        points = pd.DataFrame([{"latitud": acceso["latitud"], "longitud": acceso["longitud"], "color": "#176552", "tamano": 60}] +
                              [{"latitud": p["latitud"], "longitud": p["longitud"], "color": "#d9822b", "tamano": 25} for p in acceso["cercanos"]])
        st.map(points, latitude="latitud", longitude="longitud", color="color", size="tamano", zoom=14)
        st.caption("Verde: departamento. Naranja: los paraderos más cercanos.")
        st.dataframe(pd.DataFrame(acceso["cercanos"]).drop(columns=["latitud", "longitud"]), hide_index=True, width="stretch")
        st.caption(acceso["aviso"] + " Nivel: Alta si hay un paradero a 300 m o menos y al menos la mediana de paraderos a 500 m; Baja si el más cercano está a más de 500 m.")

st.divider()
st.header("5. Compara un escenario")
st.warning("El modelo no garantiza que más área o más amenidades aumenten el precio. Son consultas de sensibilidad, no efectos causales ni ganancias garantizadas.")
st.caption("Esta comparación usa el perfil precargado seleccionado como base, no las ediciones del formulario anterior. Cambia un atributo a la vez para explicar la diferencia.")
st.write(f"Base: **{selected}** · {default['area_total']} m² · mantenimiento S/ {default['mantenimiento']}.")
with st.form("comparacion"):
    alt_columns = st.columns(2)
    with alt_columns[0]:
        alt_area = st.number_input("Área alternativa (m²)", min_value=25, max_value=450, value=round(default["area_total"] * 1.2), key="alt_area_" + selected)
        alt_balcon = st.selectbox("Balcón en la alternativa", ["No", "Sí"], index=default["balcon"], key="alt_balcon_" + selected)
    with alt_columns[1]:
        alt_mant = st.number_input("Mantenimiento alternativo (S/)", min_value=0, max_value=5000, value=default["mantenimiento"], key="alt_mant_" + selected)
        alt_gym = st.selectbox("Gimnasio en la alternativa", ["No", "Sí"], index=default["gimnasio"], key="alt_gym_" + selected)
    compared = st.form_submit_button("Comparar dos escenarios")
comparison_key = "comparacion_guardada_" + selected
changes_input = {"area_total": alt_area, "mantenimiento": alt_mant, "balcon": int(alt_balcon == "Sí"), "gimnasio": int(alt_gym == "Sí")}
if compared:
    try:
        st.session_state[comparison_key] = comparar(default, changes_input, artifact)
    except ValueError as exc:
        st.session_state.pop(comparison_key, None)
        st.error(str(exc))
if comparison_key in st.session_state:
    comparison = st.session_state[comparison_key]
    if any(comparison["alternativa_entrada"][k] != v for k, v in changes_input.items()):
        st.warning("La comparación guardada corresponde a las entradas de la tabla, no a cambios pendientes. Pulsa Comparar dos escenarios para actualizarla.")
    with st.container(border=True):
        output_columns = st.columns(2)
        for column, title, side in zip(output_columns, ("Base precargada", "Alternativa"), ("base", "alternativa")):
            prediction = comparison[side + "_resultado"]
            with column:
                st.metric(title, f"S/ {prediction['precio_estimado_soles']:,.2f}")
                st.caption(f"Rango: S/ {prediction['limite_inferior_soles']:,.2f} – S/ {prediction['limite_superior_soles']:,.2f}")
            for warning in prediction["advertencias"] + avisos_coherencia(comparison[side + "_entrada"]):
                st.warning(warning)
        st.write(f"Diferencia estimada: **S/ {comparison['diferencia_soles']:+,.2f} ({comparison['diferencia_porcentaje']:+.2f}%)**.")
        st.info(ADVERTENCIA)
        st.caption(comparison["interpretacion_intervalos"] + " " + comparison["soporte"])
        st.markdown("**Entradas utilizadas en la comparación guardada**")
        st.dataframe(pd.DataFrame(tabla_comparacion(comparison["base_entrada"], comparison["alternativa_entrada"])), hide_index=True, width="stretch", height=495)
        st.download_button("Descargar comparación JSON", json_comparacion(comparison), "comparacion_deparent.json", "application/json")
        st.download_button("Descargar comparación CSV", csv_comparacion(comparison), "comparacion_deparent.csv", "text/csv")
else:
    st.info("Pulsa Comparar dos escenarios para ver ambos resultados y descargar sus entradas.")

st.divider()
st.header("6. Explora el área")
st.caption("Consulta −20%, el área base y +20%, redondeados a m² enteros; solo cambia el área. Si editaste el formulario, pulsa Estimar alquiler antes de usar esa estimación aquí.")
area_source = "Perfil precargado"
if estimate_key in st.session_state:
    area_source = st.radio("Base para explorar", ["Perfil precargado", "Última estimación guardada"], horizontal=True, key="fuente_area_" + selected)
else:
    st.caption("Para explorar un caso editado, primero calcula y guarda su estimación en el paso 1.")
lab_base = st.session_state[estimate_key]["entrada"] if area_source == "Última estimación guardada" else default
st.caption(f"Base elegida: {area_source.lower()} · {lab_base['area_total']} m² · mantenimiento S/ {lab_base['mantenimiento']}.")
st.info(AVISO)
st.caption("Contraejemplo visible: en el perfil de San Isidro, 160 → 192 m² produce S/ 7,386.28 → S/ 7,077.25. El descenso no demuestra que ampliar una vivienda reduzca su valor.")
lab_key = "laboratorio_area_" + selected + ("_estimacion" if area_source == "Última estimación guardada" else "")
if lab_key in st.session_state and st.session_state[lab_key]["entrada_base"] != lab_base:
    st.session_state.pop(lab_key)
if st.button("Explorar tres áreas", key="explorar_area_" + selected):
    try:
        st.session_state[lab_key] = explorar_area(lab_base, artifact)
    except ValueError as exc:
        st.session_state.pop(lab_key, None)
        st.error(str(exc))
if lab_key in st.session_state:
    lab = st.session_state[lab_key]
    rows = tabla_area(lab)
    summary = lab["resumen"]
    st.write(f"**{selected}** · {area_source.lower()} · mantenimiento S/ {lab['entrada_base']['mantenimiento']}.")
    difference = summary["diferencia_base_a_mayor_soles"]
    percentage = summary["variacion_base_a_mayor_porcentaje"]
    if difference:
        direction = "baja" if difference < 0 else "sube"
        percent_text = f" ({abs(percentage):.2f}%)" if percentage is not None else ""
        st.write(f"Al pasar de {summary['area_base_m2']} a {summary['area_mayor_m2']} m², la estimación {direction} S/ {abs(difference):,.2f}{percent_text}.")
    else:
        st.write(f"Al pasar de {summary['area_base_m2']} a {summary['area_mayor_m2']} m², la estimación no cambia.")
    if summary["hay_descenso_al_aumentar_area"]:
        st.warning("Al menos una de las tres consultas baja al aumentar el área. No cambiamos la predicción para ocultarlo: revisen datos comparables y errores del modelo antes de usar esta salida para decidir.")
    st.vega_lite_chart(pd.DataFrame(rows), {
        "height": 300,
        "encoding": {"x": {"field": "Área (m²)", "type": "quantitative", "scale": {"zero": False}, "axis": {"values": [r["Área (m²)"] for r in rows]}}},
        "layer": [
            {"mark": {"type": "rule", "color": "#75ac99", "strokeWidth": 7},
             "encoding": {"y": {"field": "Límite inferior (S/)", "type": "quantitative", "title": "Alquiler mensual (S/)", "scale": {"zero": True}}, "y2": {"field": "Límite superior (S/)"}}},
            {"mark": {"type": "point", "filled": True, "size": 120, "color": "#176552"},
             "encoding": {"y": {"field": "Estimación (S/)", "type": "quantitative"}, "tooltip": [{"field": k, "type": "quantitative"} for k in rows[0]]}},
            {"mark": {"type": "text", "dy": -14, "color": "#143e45", "fontSize": 12},
             "encoding": {"y": {"field": "Estimación (S/)", "type": "quantitative"}, "text": {"field": "Estimación (S/)", "type": "quantitative", "format": ",.2f"}}}
        ]}, use_container_width=True)
    st.caption("Puntos: estimaciones. Barras verticales: rangos individuales. No se interpolan valores entre las tres áreas.")
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    for point in lab["puntos"]:
        for warning in point["resultado"]["advertencias"] + avisos_coherencia(point["entrada"]):
            st.warning(f"{point['entrada']['area_total']} m²: {warning}")
    with st.expander("Entradas utilizadas en las tres consultas"):
        st.dataframe(pd.DataFrame([{"Entrada": label, **{str(point["entrada"]["area_total"]) + " m²": mostrar_valor(field, point["entrada"].get(field)) for point in lab["puntos"]}} for field, label in ETIQUETAS.items()]), hide_index=True, width="stretch")
    lab_csv_payload = csv_area(lab)
    lab_json_payload = json.dumps(lab, ensure_ascii=False, indent=2, allow_nan=False)
    st.download_button("Descargar laboratorio CSV", lab_csv_payload, "deparent_areas.csv", "text/csv", key="lab_csv_" + selected, on_click="ignore")
    st.download_button("Descargar laboratorio JSON", lab_json_payload, "deparent_areas.json", "application/json", key="lab_json_" + selected, on_click="ignore")
    with st.expander("Ver datos para copiar"):
        st.caption("Si el navegador no inicia la descarga, copia estos datos y guárdalos como .csv o .json")
        st.code(lab_csv_payload, language="csv")
        st.code(lab_json_payload, language="json")
else:
    st.info("Pulsa Explorar tres áreas para ver el gráfico y su tabla. No se reentrena el modelo.")
