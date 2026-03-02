"""
GABBIANI MASTER AI v7.0 — Interfaz Streamlit
"""
import streamlit as st
import pandas as pd
import os
import html as html_module
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import html


# ── Import del core (único import necesario) ──
from core import (
    PERFILES, MotorVision, CerebroOperarioV5, ExtractorVectorial,
    ValidadorFisico, Auditoria, DatosPagina, PiezaIndustrial,
    OrigenDato, NivelConfianza, worker_pagina, pdf_a_datos
)

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="GABBIANI MASTER AI v7", layout="wide",
                   page_icon="🔷", initial_sidebar_state="collapsed")

BACKEND = st.secrets.get("BACKEND", "google_ai")
GEMINI_MODEL = st.secrets.get("GEMINI_MODEL", "gemini-2.5-pro-preview-06-05")
MAX_WORKERS = int(st.secrets.get("MAX_WORKERS", 5))
backend_label = "Vertex AI" if BACKEND == "vertex_ai" else "Google AI Studio"

# ══════════════════════════════════════════════════════════════════════════════
# CSS (cargado desde archivo externo si existe, sino inline)
# ══════════════════════════════════════════════════════════════════════════════
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    # Fallback: CSS inline (el mismo bloque largo que ya tenías)
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    /* ... (aquí va todo el CSS, lo omito por brevedad pero es el mismo) ... */
    </style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# AUTENTICACIÓN
# ══════════════════════════════════════════════════════════════════════════════
try:
    if BACKEND == "vertex_ai":
        _secrets = {
            "gcp_service_account": dict(st.secrets["gcp_service_account"]),
            "GCP_PROJECT": st.secrets["GCP_PROJECT"],
            "GCP_LOCATION": st.secrets.get("GCP_LOCATION", "europe-west1"),
        }
    else:
        _secrets = {"GEMINI_API_KEY": st.secrets["GEMINI_API_KEY"]}
except Exception as e:
    st.error(f"⛔ Error de Configuración: {e}")
    st.stop()

@st.cache_resource
def get_motor():
    return MotorVision(backend=BACKEND, model_name=GEMINI_MODEL,
                       secrets_dict=_secrets)

# ══════════════════════════════════════════════════════════════════════════════
# HERO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="hero-wrapper">
    <div class="hero-blue-line"></div>
    <div class="hero-content">
        <div class="hero-mono-tag"><span class="tag-dot"></span>
            SISTEMA EXPERTO DE CORTE INDUSTRIAL · v7.0 ENTERPRISE</div>
        <div class="hero-title-line">
            <h1 class="hero-brand">GABBIANI <span class="blue">MASTER AI</span></h1>
            <span class="hero-edition">ENTERPRISE</span>
        </div>
        <p class="hero-desc">
            Pipeline dual {MAX_WORKERS}x: vectorial + Gemini 2.5 Pro híbrido.
            {backend_label} · HDR6,90 nativo · Trazabilidad · Auditoría.
        </p>
        <div class="hero-status-row">
            <div class="status-chip chip-online"><span class="chip-dot green"></span>Operativo</div>
            <div class="status-chip chip-blue"><span class="chip-dot blue"></span>{GEMINI_MODEL}</div>
            <div class="status-chip chip-blue"><span class="chip-dot blue"></span>{backend_label}</div>
            <div class="status-chip chip-neutral">🚀 {MAX_WORKERS}x hilos</div>
            <div class="status-chip chip-neutral">🕐 {datetime.now().strftime("%d/%m/%Y · %H:%M")}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="trust-bar">
    <div class="trust-item"><span class="t-icon">🛡️</span> Procesamiento seguro</div>
    <div class="trust-item"><span class="t-icon">🔒</span> Datos no almacenados</div>
    <div class="trust-item"><span class="t-icon">✅</span> Validación por reglas</div>
    <div class="trust-item"><span class="t-icon">📐</span> Precisión híbrida</div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ Configuración Industrial")
    perfil_sel = st.selectbox("Perfil de Cliente", list(PERFILES.keys()),
                               format_func=lambda x: PERFILES[x]["display"])
    pf = PERFILES[perfil_sel]
    st.markdown("---")
    extras = []
    if pf.get("regla_puertas_16"): extras.append("16mm:    SÍ (Gradeles)")
    st.code(f"Pinza:     {pf['ancho_pinza']}mm\n"
            f"Saneado:   {pf['margen_sandwich']}mm\n"
            f"Kerf:      {pf['kerf_mm']}mm\n"
            f"Canteado:  {'SÍ' if pf['canteado_auto'] else 'NO'}\n"
            f"Cajones:   {'QUBE' if pf['cajon_qube'] else 'NO'}\n"
            + ("\n".join(extras) + "\n" if extras else "") +
            f"Backend:   {backend_label}\n"
            f"Modelo:    {GEMINI_MODEL}\n"
            f"Workers:   {MAX_WORKERS}")
    st.markdown("---")
    dpi_sel = st.select_slider("Resolución DPI", [150,200,250,300], value=300)
    mostrar_debug = st.checkbox("Mostrar trazabilidad", value=True)

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
if 'datos_pdf' not in st.session_state:
    st.session_state['datos_pdf'] = []

st.markdown("""
<div class="sec-header"><div class="sec-icon">📁</div>
<div class="sec-text"><div class="sec-title">Importar Proyecto</div>
<div class="sec-sub">PDF técnico · Extracción dual</div>
</div></div>""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Selecciona PDF", type=["pdf"])

if uploaded_file:
    nombre_base = os.path.splitext(uploaded_file.name)[0]
    safe_name = html_module.escape(uploaded_file.name)

    if st.session_state.get('_last_file') != uploaded_file.name:
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"): del st.session_state[key]
        with st.spinner(f"Extrayendo capas del PDF a {dpi_sel} DPI..."):
            st.session_state['datos_pdf'] = pdf_a_datos(uploaded_file, dpi=dpi_sel)
            st.session_state['_last_file'] = uploaded_file.name
            for k in ['df_final','alertas_final','piezas_obj','meta_pags']:
                st.session_state.pop(k, None)

    datos_pdf = st.session_state['datos_pdf']
    tp = len(datos_pdf)
    pags_texto = sum(1 for d in datos_pdf if d.tiene_texto)
    pags_tablas = sum(1 for d in datos_pdf if d.tiene_tablas)

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card blue">
            <div class="kpi-label">Documento</div>
            <div class="kpi-value" style="font-size:.92rem;word-break:break-all;font-weight:600">{safe_name}</div>
            <div class="kpi-sub">Perfil: {html_module.escape(pf['display'])}</div>
        </div>
        <div class="kpi-card blue">
            <div class="kpi-label">Páginas</div>
            <div class="kpi-value">{tp}</div>
            <div class="kpi-sub">{pags_texto} con texto · {pags_tablas} con tablas</div>
        </div>
        <div class="kpi-card emerald">
            <div class="kpi-label">Texto Vectorial</div>
            <div class="kpi-value">{pags_texto}<span class="kpi-unit">/ {tp}</span></div>
            <div class="kpi-sub">Páginas con datos digitales</div>
        </div>
        <div class="kpi-card blue">
            <div class="kpi-label">Motor</div>
            <div class="kpi-value" style="font-size:.72rem">{GEMINI_MODEL.replace('-preview-06-05','')}</div>
            <div class="kpi-sub">{backend_label} · {MAX_WORKERS}x</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Selección de páginas ──
    st.markdown(f"""
    <div class="sec-header"><div class="sec-icon">📑</div>
    <div class="sec-text"><div class="sec-title">Selección de Páginas</div>
    <div class="sec-sub">📝 texto · 🖼️ imagen</div></div>
    <div class="sec-badge">{tp} PÁG</div></div>""", unsafe_allow_html=True)

    for i in range(tp):
        if f"chk_{i}" not in st.session_state:
            st.session_state[f"chk_{i}"] = True

    act = sum(1 for i in range(tp) if st.session_state.get(f"chk_{i}",True))
    todas = act==tp
    c1,c2 = st.columns([5,1])
    with c1: st.markdown(f"**{act}** de **{tp}** seleccionadas")
    with c2:
        if st.button("☐ Ninguna" if todas else "☑ Todas", use_container_width=True):
            for i in range(tp): st.session_state[f"chk_{i}"] = not todas
            st.rerun()

    seleccionadas = []
    cols = st.columns(6)
    for i, dp in enumerate(datos_pdf):
        with cols[i%6]:
            icono = "📝" if dp.tiene_texto else "🖼️"
            tab_tag = " 📊" if dp.tiene_tablas else ""
            m = st.checkbox(f"{icono} Pág {i+1:02d}{tab_tag}", key=f"chk_{i}")
            st.image(dp.imagen, use_container_width=True)
            if m: seleccionadas.append(dp)

    st.markdown("""<div class="section-divider"><div class="line"></div>
    <div class="dot"></div><div class="line"></div></div>""", unsafe_allow_html=True)

    n_sel = len(seleccionadas)
    tiempo_est = max(3, (n_sel*9)//MAX_WORKERS)
    cb,_,ci = st.columns([2,1,3])
    with cb:
        procesar = st.button(f"▶  ANALIZAR  ·  {n_sel} PÁGINAS",
                             type="primary", use_container_width=True, disabled=(n_sel==0))
    with ci:
        st.caption(f"~{tiempo_est}s · {MAX_WORKERS} hilos · Pipeline dual")

    # ══════════════════════════════════════════════════════════════════════
    # PROCESAMIENTO
    # ══════════════════════════════════════════════════════════════════════
    if procesar and n_sel > 0:
        motor = get_motor()
        cerebro = CerebroOperarioV5(perfil_sel)
        piezas_total, alertas_total, meta_pags = [], [], []

        st.markdown("""
        <div class="sec-header"><div class="sec-icon">🔬</div>
        <div class="sec-text"><div class="sec-title">Pipeline Dual</div>
        <div class="sec-sub">Vectorial → Gemini → Reglas → Validación</div>
        </div></div>""", unsafe_allow_html=True)

        barra = st.progress(0)
        status = st.empty()
        status.markdown("""<div class="proc-status"><div class="proc-icon">🔄</div>
        <div><span class="proc-text-main">Lanzando análisis...</span></div></div>""",
        unsafe_allow_html=True)
        barra.progress(5)

        resultados_raw = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futuros = {
                executor.submit(worker_pagina, dp, motor): dp.num
                for dp in seleccionadas
            }
            completados = 0
            for futuro in as_completed(futuros):
                completados += 1
                try:
                    resultado = futuro.result()
                    resultados_raw.append(resultado)
                    num_pag, _, _, estrategia = resultado
                    status.markdown(f"""<div class="proc-status">
                    <div class="proc-icon">⚡</div>
                    <div><span class="proc-text-main">Página {num_pag}</span>
                    <span class="proc-text-sub">({completados}/{n_sel}) · {estrategia}</span></div>
                    </div>""", unsafe_allow_html=True)
                except Exception as e:
                    alertas_total.append(f"❌ Worker error: {e}")
                barra.progress(max(5, int((completados/n_sel)*100)))

        resultados_raw.sort(key=lambda r: r[0])

        for num_pag, datos_raw, origen, estrategia in resultados_raw:
            meta_pags.append(estrategia)
            if isinstance(datos_raw, list) and datos_raw:
                if isinstance(datos_raw[0], dict) and "error" in datos_raw[0]:
                    alertas_total.append(f"❌ Pág {num_pag}: {datos_raw[0]['error']}")
                else:
                    pzs, als = cerebro.procesar(datos_raw, num_pag, origen)
                    piezas_total.extend(pzs)
                    alertas_total.extend(als)

        status.markdown("""<div class="proc-status" style="border-color:#a7f3d0;background:#ecfdf5">
        <div class="proc-icon" style="background:#d1fae5;border-color:#a7f3d0">✅</div>
        <div><span class="proc-text-main" style="color:#065f46">Completado</span></div></div>""",
        unsafe_allow_html=True)
        barra.progress(100)

        piezas_total.sort(key=lambda p: p.id)

        if piezas_total:
            rows = [p.to_row_debug() for p in piezas_total] if mostrar_debug else [p.to_display_row() for p in piezas_total]
            st.session_state['df_final'] = pd.DataFrame(rows)
            st.session_state['alertas_final'] = alertas_total
            st.session_state['piezas_obj'] = piezas_total
            st.session_state['meta_pags'] = meta_pags
            st.session_state['nombre_base'] = nombre_base
        else:
            st.session_state['df_final'] = pd.DataFrame()
            st.session_state['alertas_final'] = alertas_total
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# RESULTADOS
# ══════════════════════════════════════════════════════════════════════════════
if 'df_final' in st.session_state:
    df = st.session_state['df_final']
    al = st.session_state.get('alertas_final',[])
    po = st.session_state.get('piezas_obj',[])
    nb = st.session_state.get('nombre_base','proyecto')
    meta = st.session_state.get('meta_pags',[])

    if df.empty:
        st.warning("No se extrajeron piezas válidas.")
    else:
        st.markdown("""<div class="section-divider"><div class="line"></div>
        <div class="dot"></div><div class="dot" style="margin:0 -4px"></div>
        <div class="dot"></div><div class="line"></div></div>""", unsafe_allow_html=True)

        tpz = int(df['Cantidad'].sum()) if 'Cantidad' in df.columns else len(df)
        tl = len(df)
        mu = df['Material'].nunique() if 'Material' in df.columns else 0
        pv = sum(1 for m in meta if "VECTORIAL" in m)
        pi = sum(1 for m in meta if "GEMINI" in m)

        st.markdown(f"""
        <div class="sec-header"><div class="sec-icon">📋</div>
        <div class="sec-text"><div class="sec-title">Lista de Corte</div>
        <div class="sec-sub">{pv} vectoriales + {pi} Gemini · HDR6,90</div></div>
        <div class="sec-badge" style="color:#059669;border-color:#a7f3d0;background:#ecfdf5">✓ LISTO</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card emerald"><div class="kpi-label">Líneas</div>
            <div class="kpi-value">{tl}</div><div class="kpi-sub">{pv} det. + {pi} IA</div></div>
            <div class="kpi-card blue"><div class="kpi-label">Piezas</div>
            <div class="kpi-value">{tpz}</div><div class="kpi-sub">Con cantidades</div></div>
            <div class="kpi-card blue"><div class="kpi-label">Materiales</div>
            <div class="kpi-value">{mu}</div><div class="kpi-sub">Tipos</div></div>
            <div class="kpi-card amber"><div class="kpi-label">Alertas</div>
            <div class="kpi-value">{len(al)}</div><div class="kpi-sub">Revisar</div></div>
        </div>""", unsafe_allow_html=True)

        if al:
            with st.expander(f"⚠️ {len(al)} alertas", expanded=True):
                for a in al:
                    if any(k in a for k in ["🚫","🚨","METAL","KRION","❌"]): st.error(a)
                    elif any(k in a for k in ["🔄","⚠️","sospechoso"]): st.warning(a)
                    else: st.info(a)

        st.markdown("""<div class="table-label"><div class="bar"></div>
        <span>Tabla editable · Doble clic para modificar</span></div>""", unsafe_allow_html=True)

        if mostrar_debug and 'Largo_IA' in df.columns:
            cc = {
                "ID": st.column_config.TextColumn("ID",width="small"),
                "Nombre": st.column_config.TextColumn("Nombre",width="medium"),
                "Largo_IA": st.column_config.NumberColumn("L (IA)",format="%.1f",width="small"),
                "Largo_Corte": st.column_config.NumberColumn("L CORTE",format="%.1f",width="small"),
                "Ancho_IA": st.column_config.NumberColumn("A (IA)",format="%.1f",width="small"),
                "Ancho_Corte": st.column_config.NumberColumn("A CORTE",format="%.1f",width="small"),
                "Espesor": st.column_config.NumberColumn("Esp",format="%.0f",width="small"),
                "Material": st.column_config.TextColumn("Material",width="medium"),
                "Cantidad": st.column_config.NumberColumn("Cant",format="%d",width="small"),
                "Confianza": st.column_config.TextColumn("🔒",width="small"),
                "Regla": st.column_config.TextColumn("Regla",width="large"),
                "Notas": st.column_config.TextColumn("Notas",width="medium"),
            }
        else:
            cc = {
                "Nombre": st.column_config.TextColumn("Nombre",width="medium"),
                "Largo": st.column_config.NumberColumn("Largo",format="%.1f mm",width="small"),
                "Ancho": st.column_config.NumberColumn("Ancho",format="%.1f mm",width="small"),
                "Espesor": st.column_config.NumberColumn("Esp",format="%.0f mm",width="small"),
                "Material": st.column_config.TextColumn("Material",width="medium"),
                "Cantidad": st.column_config.NumberColumn("Cant",format="%d",width="small"),
                "Notas": st.column_config.TextColumn("Notas",width="large"),
            }

        df_ed = st.data_editor(df, num_rows="dynamic", use_container_width=True,
                               height=600, column_config=cc)

        st.markdown("""<div class="section-divider"><div class="line"></div>
        <div class="dot"></div><div class="line"></div></div>""", unsafe_allow_html=True)

        # ── EXPORTACIÓN ──
        csv_l = pd.DataFrame([p.to_csv_row() for p in po]) if po else df_ed
        csv_b = csv_l.to_csv(index=False, sep=";").encode('utf-8')

        txt_body = csv_l.to_csv(index=False, header=False, sep=",")
        txt_body = txt_body.replace("\r\n", "\n").rstrip("\n")
        txt_final = f"HDR6,90\n{txt_body}\n".encode('utf-8')

        c_csv, c_txt, c_aud = st.columns([1, 1, 2])
        with c_csv:
            st.download_button("📊 CSV (Revisión)", data=csv_b,
                               file_name=f"{nb}_revision.csv", mime="text/csv",
                               use_container_width=True)
        with c_txt:
            st.download_button("🤖 TXT GABBIANI", data=txt_final,
                               file_name=f"{nb}_GABBIANI.txt", mime="text/plain",
                               type="primary", use_container_width=True)
        with c_aud:
            inf = Auditoria.generar(po, al, perfil_sel,
                                    st.session_state.get('_last_file','N/A'),
                                    backend=BACKEND, model=GEMINI_MODEL,
                                    workers=MAX_WORKERS)
            st.download_button("📄 AUDITORÍA", data=inf.encode('utf-8'),
                               file_name=f"{nb}_auditoria.txt", mime="text/plain",
                               use_container_width=True)

        st.caption("🤖 TXT GABBIANI = formato HDR6,90 nativo para USB seccionadora · "
                   "📊 CSV = revisión humana en Excel (;)")

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="corp-footer">
    <div class="footer-logo-text">GABBIANI MASTER AI</div>
    <div class="footer-sub">v7.0 Enterprise · {GEMINI_MODEL} · {backend_label} · HDR6,90 · {MAX_WORKERS}x</div>
    <div class="footer-copy">© 2026 · SISTEMA EXPERTO DE OPTIMIZACIÓN DE CORTE INDUSTRIAL</div>
</div>""", unsafe_allow_html=True)
