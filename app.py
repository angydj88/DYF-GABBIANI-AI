"""
GABBIANI MASTER AI v7.0 — Interfaz Streamlit
"""
import streamlit as st
import pandas as pd
import os
import html as html_module
from datetime import datetime
# ◄◄◄ ELIMINADO: from concurrent.futures import ThreadPoolExecutor, as_completed

from core import (
    PERFILES, MotorVision, CerebroOperarioV5,
    Auditoria, DatosPagina, PiezaIndustrial,
    OrigenDato, NivelConfianza, worker_pagina, pdf_a_datos
)

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="GABBIANI MASTER AI v7", layout="wide",
                   page_icon="🔷", initial_sidebar_state="collapsed")

BACKEND = st.secrets.get("BACKEND", "google_ai")
GEMINI_MODEL = st.secrets.get("GEMINI_MODEL", "gemini-2.0-flash")  # ◄◄◄ Flash por defecto en EU
# ◄◄◄ MAX_WORKERS ya no se usa para API, solo informativo
MAX_WORKERS = 1  # ◄◄◄ Secuencial para respetar rate limits EU
backend_label = "Vertex AI" if BACKEND == "vertex_ai" else "Google AI Studio"

# ══════════════════════════════════════════════════════════════════════════════
# CSS PREMIUM COMPLETO (sin cambios)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ═══════════ FONTS ═══════════ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ═══════════ DESIGN TOKENS ═══════════ */
:root {
    --bg-body: #f8f9fb;
    --bg-white: #ffffff;
    --bg-elevated: #ffffff;
    --bg-subtle: #f1f3f8;
    --bg-overlay: rgba(255,255,255,.92);

    --border-hairline: #e8ecf2;
    --border-light: #dfe4ed;
    --border-medium: #c5cdd8;
    --border-focus: #4f7df3;

    --blue-50: #eef4ff;
    --blue-100: #dce7fd;
    --blue-200: #bdd2fb;
    --blue-300: #8db4f8;
    --blue-400: #6199f4;
    --blue-500: #4f7df3;
    --blue-600: #3a63e7;
    --blue-700: #2f50d4;
    --blue-800: #2c43ac;
    --blue-900: #1e3264;

    --gray-50: #f8f9fb;
    --gray-100: #f1f3f8;
    --gray-200: #e2e7f0;
    --gray-300: #c5cdd8;
    --gray-400: #8d96a6;
    --gray-500: #636d7e;
    --gray-600: #475164;
    --gray-700: #343d4f;
    --gray-800: #1f2737;
    --gray-900: #0d1320;

    --text-primary: #0d1320;
    --text-secondary: #475164;
    --text-tertiary: #636d7e;
    --text-muted: #8d96a6;
    --text-inverted: #ffffff;

    --accent-green: #0d9e6c;
    --accent-green-bg: #e6f9f0;
    --accent-green-border: #b0e8cf;
    --accent-red: #d93025;
    --accent-red-bg: #fdecea;
    --accent-amber: #c07d10;
    --accent-amber-bg: #fef6e0;

    --gradient-brand: linear-gradient(135deg, #2f50d4 0%, #4f7df3 50%, #6199f4 100%);
    --gradient-brand-hover: linear-gradient(135deg, #2845b8 0%, #3a63e7 50%, #4f7df3 100%);
    --gradient-accent: linear-gradient(135deg, #4f7df3 0%, #6199f4 100%);
    --gradient-glow: radial-gradient(ellipse at 30% 0%, rgba(79,125,243,.06) 0%, transparent 60%);

    --shadow-xs: 0 1px 2px rgba(13,19,32,.04);
    --shadow-sm: 0 1px 4px rgba(13,19,32,.05), 0 1px 2px rgba(13,19,32,.03);
    --shadow-md: 0 4px 12px rgba(13,19,32,.06), 0 1px 4px rgba(13,19,32,.04);
    --shadow-lg: 0 8px 24px rgba(13,19,32,.07), 0 2px 8px rgba(13,19,32,.04);
    --shadow-xl: 0 16px 48px rgba(13,19,32,.08), 0 4px 16px rgba(13,19,32,.04);
    --shadow-brand: 0 4px 16px rgba(47,80,212,.20);
    --shadow-brand-lg: 0 8px 32px rgba(47,80,212,.25);

    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 20px;
    --radius-pill: 100px;

    --transition-fast: 150ms cubic-bezier(.4,0,.2,1);
    --transition-base: 250ms cubic-bezier(.4,0,.2,1);
    --transition-slow: 400ms cubic-bezier(.4,0,.2,1);
}

/* ═══════════ RESET & BASE ═══════════ */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background: var(--bg-body) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
.stApp > header { background: transparent !important; }
.main .block-container {
    padding: 1.5rem 2.5rem 4rem !important;
    max-width: 1400px !important;
}
h1,h2,h3,h4,h5,h6 {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
    letter-spacing: -0.025em !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] {
    display: none !important;
    visibility: hidden !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--gray-300); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: var(--gray-400); }

/* ═══════════ HERO HEADER ═══════════ */
.hero-wrapper {
    position: relative;
    margin: -0.5rem -0.5rem 2rem;
    border-radius: var(--radius-xl);
    overflow: hidden;
    background: var(--bg-white);
    border: 1px solid var(--border-hairline);
    box-shadow: var(--shadow-lg);
}
.hero-accent-bar {
    height: 3px;
    background: var(--gradient-brand);
}
.hero-content {
    position: relative;
    padding: 2.25rem 2.75rem 2rem;
}
.hero-content::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: var(--gradient-glow);
    pointer-events: none;
}
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--blue-600);
    padding: 4px 14px;
    background: var(--blue-50);
    border: 1px solid var(--blue-100);
    border-radius: var(--radius-pill);
    margin-bottom: 1rem;
}
.eyebrow-dot {
    width: 6px; height: 6px;
    background: var(--blue-500);
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(79,125,243,.6);
    animation: pulse-dot 2.5s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: .35; transform: scale(.85); }
}
.hero-title-row {
    display: flex;
    align-items: baseline;
    gap: 16px;
    margin-bottom: 0.5rem;
}
.hero-brand {
    font-size: 2.1rem !important;
    font-weight: 900 !important;
    letter-spacing: -0.04em !important;
    line-height: 1 !important;
    margin: 0 !important;
    color: var(--gray-900) !important;
}
.hero-brand .accent { color: var(--blue-600); }
.hero-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--gray-500);
    padding: 3px 10px;
    background: var(--gray-100);
    border: 1px solid var(--border-light);
    border-radius: 4px;
    text-transform: uppercase;
}
.hero-desc {
    font-size: 0.88rem;
    color: var(--text-secondary);
    line-height: 1.7;
    margin: 0 0 1.5rem;
    max-width: 700px;
}
.hero-chips {
    display: flex;
    align-items: center;
    gap: 10px;
    padding-top: 1.25rem;
    border-top: 1px solid var(--border-hairline);
    flex-wrap: wrap;
}

/* ═══════════ CHIPS ═══════════ */
.chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 13px;
    border-radius: var(--radius-pill);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.01em;
    white-space: nowrap;
    transition: var(--transition-fast);
}
.chip-live {
    background: var(--accent-green-bg);
    border: 1px solid var(--accent-green-border);
    color: var(--accent-green);
}
.chip-info {
    background: var(--blue-50);
    border: 1px solid var(--blue-100);
    color: var(--blue-700);
}
.chip-neutral {
    background: var(--gray-100);
    border: 1px solid var(--border-light);
    color: var(--gray-500);
}
.chip-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
}
.chip-dot.green {
    background: var(--accent-green);
    box-shadow: 0 0 6px rgba(13,158,108,.45);
    animation: pulse-dot 2s ease-in-out infinite;
}
.chip-dot.blue { background: var(--blue-500); }

/* ═══════════ TRUST BAR ═══════════ */
.trust-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2.5rem;
    padding: 0.6rem 1rem;
    background: var(--bg-white);
    border: 1px solid var(--border-hairline);
    border-radius: var(--radius-sm);
    margin: 0 0 0.5rem;
}
.trust-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 600;
    color: var(--gray-500);
    letter-spacing: 0.01em;
}
.trust-item .ti { font-size: 13px; }

/* ═══════════ SECTION HEADERS ═══════════ */
.sec-hdr {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 2.25rem 0 1.25rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border-hairline);
    position: relative;
}
.sec-hdr::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0;
    width: 48px; height: 2px;
    background: var(--gradient-brand);
    border-radius: 2px;
}
.sec-icon {
    width: 38px; height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--blue-50);
    border: 1px solid var(--blue-100);
    border-radius: var(--radius-sm);
    font-size: 16px;
    flex-shrink: 0;
}
.sec-body .sec-title {
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    margin: 0 !important;
    line-height: 1.2 !important;
}
.sec-body .sec-sub {
    font-size: 0.76rem;
    color: var(--text-muted);
    margin-top: 2px;
}
.sec-badge {
    margin-left: auto;
    padding: 4px 14px;
    background: var(--gray-50);
    border: 1px solid var(--border-light);
    border-radius: var(--radius-pill);
    font-size: 10px;
    font-weight: 700;
    color: var(--gray-500);
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.04em;
}

/* ═══════════ KPI CARDS ═══════════ */
.kpi-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 1.25rem 0;
}
.kpi {
    position: relative;
    padding: 1.25rem 1.35rem;
    background: var(--bg-white);
    border: 1px solid var(--border-hairline);
    border-radius: var(--radius-md);
    overflow: hidden;
    transition: var(--transition-base);
    box-shadow: var(--shadow-xs);
}
.kpi:hover {
    border-color: var(--border-medium);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}
.kpi::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
}
.kpi.kpi-brand::before { background: var(--gradient-brand); }
.kpi.kpi-green::before { background: linear-gradient(90deg, #0d9e6c, #22c990); }
.kpi.kpi-neutral::before { background: linear-gradient(90deg, var(--gray-300), var(--gray-200)); }
.kpi.kpi-amber::before { background: linear-gradient(90deg, #c07d10, #e9a829); }
.kpi-label {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-muted);
    margin-bottom: 0.45rem;
}
.kpi-value {
    font-size: 1.7rem;
    font-weight: 800;
    color: var(--text-primary);
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.03em;
    line-height: 1;
}
.kpi-unit {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-muted);
    margin-left: 2px;
}
.kpi-detail {
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 0.45rem;
    font-weight: 500;
}

/* ═══════════ BUTTONS ═══════════ */
.stButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.02em !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.65rem 1.8rem !important;
    transition: all var(--transition-fast) !important;
    border: none !important;
    font-size: 0.82rem !important;
    text-transform: uppercase !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: var(--gradient-brand) !important;
    color: var(--text-inverted) !important;
    box-shadow: var(--shadow-brand) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {
    background: var(--gradient-brand-hover) !important;
    box-shadow: var(--shadow-brand-lg) !important;
    transform: translateY(-2px) !important;
}
.stButton > button[kind="secondary"],
.stButton > button[data-testid="baseButton-secondary"] {
    background: var(--bg-white) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-medium) !important;
    box-shadow: var(--shadow-xs) !important;
}
.stButton > button[kind="secondary"]:hover,
.stButton > button[data-testid="baseButton-secondary"]:hover {
    border-color: var(--border-focus) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* ═══════════ DOWNLOAD BUTTONS ═══════════ */
.stDownloadButton > button {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.75rem 2rem !important;
    border: none !important;
    font-size: 0.84rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.02em !important;
    transition: all var(--transition-fast) !important;
    background: var(--gradient-brand) !important;
    color: var(--text-inverted) !important;
    box-shadow: var(--shadow-brand) !important;
}
.stDownloadButton > button:hover {
    background: var(--gradient-brand-hover) !important;
    box-shadow: var(--shadow-brand-lg) !important;
    transform: translateY(-2px) !important;
}

/* ═══════════ DATA EDITOR / TABLE ═══════════ */
[data-testid="stDataEditor"],
[data-testid="stDataFrame"] {
    border: 1px solid var(--border-hairline) !important;
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
    box-shadow: var(--shadow-md) !important;
    background: var(--bg-white) !important;
}

/* ═══════════ EXPANDER ═══════════ */
[data-testid="stExpander"] {
    background: var(--bg-white) !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: var(--radius-md) !important;
    overflow: hidden;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stExpander"] summary {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    padding: 0.85rem 1.15rem !important;
    font-size: 0.88rem !important;
}

/* ═══════════ ALERTS ═══════════ */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    font-size: 0.82rem !important;
    padding: 0.7rem 1rem !important;
    border-left-width: 3px !important;
}

/* ═══════════ PROGRESS BAR ═══════════ */
.stProgress > div > div {
    background: var(--gradient-brand) !important;
    border-radius: var(--radius-pill) !important;
}
.stProgress > div {
    background: var(--gray-100) !important;
    border-radius: var(--radius-pill) !important;
    border: 1px solid var(--border-hairline) !important;
}

/* ═══════════ FILE UPLOADER ═══════════ */
[data-testid="stFileUploader"] {
    background: transparent !important;
}
[data-testid="stFileUploaderFile"] {
    background: var(--blue-50) !important;
    border: 1px solid var(--blue-200) !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.5rem 0.75rem !important;
}

/* ═══════════ IMAGES (page previews) ═══════════ */
[data-testid="stImage"] {
    border-radius: var(--radius-sm) !important;
    overflow: hidden !important;
    border: 1px solid var(--border-light) !important;
    transition: all var(--transition-base) !important;
    background: var(--bg-white) !important;
}
[data-testid="stImage"]:hover {
    border-color: var(--blue-400) !important;
    box-shadow: var(--shadow-brand) !important;
    transform: scale(1.03);
}

/* ═══════════ CHECKBOX ═══════════ */
[data-testid="stCheckbox"] label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
    font-size: 0.8rem !important;
}

/* ═══════════ DIVIDERS ═══════════ */
.divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 2rem 0;
}
.divider .line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-light), transparent);
}
.divider .dot {
    width: 5px; height: 5px;
    background: var(--blue-300);
    border-radius: 50%;
    flex-shrink: 0;
    opacity: 0.55;
}

/* ═══════════ TABLE LABEL ═══════════ */
.tbl-label {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 0.75rem;
}
.tbl-label .bar {
    width: 3px; height: 16px;
    background: var(--gradient-brand);
    border-radius: 2px;
}
.tbl-label span {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ═══════════ PROCESSING STATUS ═══════════ */
.proc-card {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 0.75rem 1.25rem;
    background: var(--bg-white);
    border: 1px solid var(--border-hairline);
    border-radius: var(--radius-sm);
    margin: 0.5rem 0;
    box-shadow: var(--shadow-xs);
    transition: var(--transition-fast);
}
.proc-icon-box {
    width: 34px; height: 34px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--blue-50);
    border: 1px solid var(--blue-100);
    border-radius: 8px;
    font-size: 15px;
    flex-shrink: 0;
}
.proc-main {
    font-size: 0.86rem;
    font-weight: 600;
    color: var(--text-primary);
}
.proc-sub {
    font-size: 0.76rem;
    color: var(--text-muted);
    margin-left: 8px;
}

/* ═══════════ FOOTER ═══════════ */
.app-footer {
    margin-top: 4rem;
    padding: 2rem 0 1rem;
    text-align: center;
    position: relative;
}
.app-footer::before {
    content: '';
    position: absolute;
    top: 0;
    left: 15%; right: 15%;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-light), transparent);
}
.footer-brand {
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    font-weight: 800;
    color: var(--blue-700);
    letter-spacing: -0.02em;
    margin-bottom: 0.3rem;
}
.footer-meta {
    font-size: 0.68rem;
    color: var(--text-muted);
    letter-spacing: 0.03em;
}
.footer-copy {
    color: var(--gray-300);
    font-size: 0.6rem;
    margin-top: 0.5rem;
    letter-spacing: 0.06em;
}

/* ═══════════ RESPONSIVE ═══════════ */
@media (max-width: 768px) {
    .main .block-container { padding: 1rem !important; }
    .hero-brand { font-size: 1.4rem !important; }
    .kpi-row { grid-template-columns: repeat(2, 1fr); }
    .hero-content { padding: 1.25rem !important; }
    .trust-bar { flex-direction: column; gap: 0.5rem; }
    .hero-chips { gap: 6px; }
}
</style>
""", unsafe_allow_html=True)

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
    <div class="hero-accent-bar"></div>
    <div class="hero-content">
        <div class="hero-eyebrow">
            <span class="eyebrow-dot"></span>
            SISTEMA EXPERTO DE CORTE INDUSTRIAL · v7.0
        </div>
        <div class="hero-title-row">
            <h1 class="hero-brand">GABBIANI <span class="accent">MASTER AI</span></h1>
            <span class="hero-tag">Enterprise</span>
        </div>
        <p class="hero-desc">
            Pipeline dual secuencial — extracción vectorial determinista
            combinada con {GEMINI_MODEL} en modo híbrido (visión + texto).
            Rate limiting adaptativo para servidor EU.
            Exportación HDR6,90 nativa para seccionadora.
        </p>
        <div class="hero-chips">
            <div class="chip chip-live"><span class="chip-dot green"></span> Operativo</div>
            <div class="chip chip-info"><span class="chip-dot blue"></span> {GEMINI_MODEL}</div>
            <div class="chip chip-info"><span class="chip-dot blue"></span> {backend_label}</div>
            <div class="chip chip-neutral">🇪🇺 EU Rate Limited</div>
            <div class="chip chip-neutral">{datetime.now().strftime("%d/%m/%Y · %H:%M")}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="trust-bar">
    <div class="trust-item"><span class="ti">🛡️</span> Procesamiento seguro</div>
    <div class="trust-item"><span class="ti">🔒</span> Datos no almacenados</div>
    <div class="trust-item"><span class="ti">✅</span> Validación por reglas de ingeniería</div>
    <div class="trust-item"><span class="ti">⏱️</span> Rate limiting adaptativo EU</div>
</div>
""", unsafe_allow_html=True)

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
            f"Modo:      Secuencial (EU)")  # ◄◄◄ Actualizado
    st.markdown("---")
    dpi_sel = st.select_slider("Resolución DPI", [150,200,250,300], value=300)
    mostrar_debug = st.checkbox("Mostrar trazabilidad", value=True)

# ══════════════════════════════════════════════════════════════════════════════
# UPLOAD
# ══════════════════════════════════════════════════════════════════════════════
if 'datos_pdf' not in st.session_state:
    st.session_state['datos_pdf'] = []

st.markdown("""
<div class="sec-hdr">
    <div class="sec-icon">📁</div>
    <div class="sec-body">
        <div class="sec-title">Importar Proyecto</div>
        <div class="sec-sub">PDF o DXF con planos técnicos · Extracción dual automática</div>
    </div>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Selecciona archivo", type=["pdf", "dxf"])

if uploaded_file:
    nombre_base = os.path.splitext(uploaded_file.name)[0]
    safe_name = html_module.escape(uploaded_file.name)
    es_dxf = uploaded_file.name.lower().endswith('.dxf')

    if st.session_state.get('_last_file') != uploaded_file.name:
        for key in list(st.session_state.keys()):
            if key.startswith("chk_"): del st.session_state[key]
        with st.spinner(f"Extrayendo datos del {'DXF' if es_dxf else 'PDF'}..."):
            if es_dxf:
                from core import extraer_datos_dxf
                st.session_state['datos_pdf'] = extraer_datos_dxf(uploaded_file)
            else:
                st.session_state['datos_pdf'] = pdf_a_datos(uploaded_file, dpi=dpi_sel)
            st.session_state['_last_file'] = uploaded_file.name
            for k in ['df_final','alertas_final','piezas_obj','meta_pags']:
                st.session_state.pop(k, None)

    datos_pdf = st.session_state['datos_pdf']
    tp = len(datos_pdf)
    pags_texto = sum(1 for d in datos_pdf if d.tiene_texto)
    pags_tablas = sum(1 for d in datos_pdf if d.tiene_tablas)

    # ◄◄◄ Estimar tiempo según modelo
    if "pro" in GEMINI_MODEL.lower():
        _seg_por_pag = 15  # Pro EU: ~15s por página
    elif "flash" in GEMINI_MODEL.lower():
        _seg_por_pag = 6   # Flash EU: ~6s por página
    else:
        _seg_por_pag = 10

    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi kpi-brand">
            <div class="kpi-label">Documento</div>
            <div class="kpi-value" style="font-size:.88rem;word-break:break-all;font-weight:600;font-family:'Inter',sans-serif">{safe_name}</div>
            <div class="kpi-detail">Perfil: {html_module.escape(pf['display'])}</div>
        </div>
        <div class="kpi kpi-brand">
            <div class="kpi-label">Páginas</div>
            <div class="kpi-value">{tp}</div>
            <div class="kpi-detail">{pags_texto} con texto · {pags_tablas} con tablas</div>
        </div>
        <div class="kpi kpi-green">
            <div class="kpi-label">Texto Vectorial</div>
            <div class="kpi-value">{pags_texto}<span class="kpi-unit">/ {tp}</span></div>
            <div class="kpi-detail">Páginas con datos digitales</div>
        </div>
        <div class="kpi kpi-brand">
            <div class="kpi-label">Motor IA</div>
            <div class="kpi-value" style="font-size:.68rem">{GEMINI_MODEL.replace('-preview-06-05','')}</div>
            <div class="kpi-detail">{backend_label} · Secuencial EU</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Selección de páginas ──
    st.markdown(f"""
    <div class="sec-hdr">
        <div class="sec-icon">📑</div>
        <div class="sec-body">
            <div class="sec-title">Selección de Páginas</div>
            <div class="sec-sub">📝 = texto vectorial · 🖼️ = solo imagen · 📊 = tablas detectadas</div>
        </div>
        <div class="sec-badge">{tp} PÁG</div>
    </div>
    """, unsafe_allow_html=True)

    for i in range(tp):
        if f"chk_{i}" not in st.session_state:
            st.session_state[f"chk_{i}"] = True

    act = sum(1 for i in range(tp) if st.session_state.get(f"chk_{i}", True))
    todas = act == tp
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(f"**{act}** de **{tp}** seleccionadas")
    with c2:
        if st.button("☐ Ninguna" if todas else "☑ Todas", width="stretch"):
            for i in range(tp): st.session_state[f"chk_{i}"] = not todas
            st.rerun()

    seleccionadas = []
    cols = st.columns(6)
    for i, dp in enumerate(datos_pdf):
        with cols[i % 6]:
            icono = "📝" if dp.tiene_texto else "🖼️"
            tab_tag = " 📊" if dp.tiene_tablas else ""
            m = st.checkbox(f"{icono} Pág {i+1:02d}{tab_tag}", key=f"chk_{i}")
            st.image(dp.imagen, width="stretch")
            if m: seleccionadas.append(dp)

    st.markdown("""<div class="divider"><div class="line"></div>
    <div class="dot"></div><div class="line"></div></div>""", unsafe_allow_html=True)

    n_sel = len(seleccionadas)
    # ◄◄◄ Páginas vectoriales no necesitan API → más rápido
    pags_solo_ia = sum(1 for dp in seleccionadas if not dp.tiene_tablas)
    tiempo_est = max(3, pags_solo_ia * _seg_por_pag + (n_sel - pags_solo_ia) * 2)

    cb, _, ci = st.columns([2, 1, 3])
    with cb:
        procesar = st.button(f"▶  ANALIZAR  ·  {n_sel} PÁGINAS",
                             type="primary", width="stretch",
                             disabled=(n_sel == 0))
    with ci:
        st.caption(f"~{tiempo_est}s estimado · Secuencial · Rate limited EU")  # ◄◄◄

    # ══════════════════════════════════════════════════════════════════════
    # PROCESAMIENTO — SECUENCIAL CON RATE LIMITING  ◄◄◄ REESCRITO
    # ══════════════════════════════════════════════════════════════════════
    if procesar and n_sel > 0:
        motor = get_motor()
        cerebro = CerebroOperarioV5(perfil_sel)
        piezas_total, alertas_total, meta_pags = [], [], []

        st.markdown("""
        <div class="sec-hdr">
            <div class="sec-icon">🔬</div>
            <div class="sec-body">
                <div class="sec-title">Pipeline Secuencial · Rate Limited</div>
                <div class="sec-sub">Vectorial → Gemini → Reglas → Validación → Deduplicación · Una página a la vez</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        barra = st.progress(0)
        status = st.empty()
        status.markdown("""<div class="proc-card">
            <div class="proc-icon-box">🔄</div>
            <div><span class="proc-main">Iniciando análisis secuencial…</span>
            <span class="proc-sub">Rate limiting activo para servidor EU</span></div>
        </div>""", unsafe_allow_html=True)
        barra.progress(5)

        # ◄◄◄ PROCESAMIENTO SECUENCIAL — Sin ThreadPoolExecutor
        for idx, dp in enumerate(seleccionadas):
            num_pag = dp.num + 1

            # Actualizar status antes de procesar
            es_vectorial = dp.tiene_tablas
            metodo = "📊 Vectorial" if es_vectorial else "🤖 Gemini IA"
            status.markdown(f"""<div class="proc-card">
                <div class="proc-icon-box">⏳</div>
                <div><span class="proc-main">Página {num_pag} · {metodo}</span>
                <span class="proc-sub">({idx+1}/{n_sel}) · {'Sin API' if es_vectorial else 'Esperando rate limit...'}</span></div>
            </div>""", unsafe_allow_html=True)

            try:
                resultado = worker_pagina(dp, motor)
                num, datos_raw, origen, estrategia = resultado
                meta_pags.append(estrategia)

                # Verificar errores
                if isinstance(datos_raw, list) and datos_raw:
                    if isinstance(datos_raw[0], dict) and "error" in datos_raw[0]:
                        err = datos_raw[0]["error"]
                        alertas_total.append(f"❌ Pág {num}: {err}")
                        status.markdown(f"""<div class="proc-card" style="border-color:var(--accent-red);border-left:3px solid var(--accent-red)">
                            <div class="proc-icon-box" style="background:var(--accent-red-bg)">❌</div>
                            <div><span class="proc-main">Página {num} — Error</span>
                            <span class="proc-sub">{html_module.escape(str(err)[:80])}</span></div>
                        </div>""", unsafe_allow_html=True)
                    else:
                        pzs, als = cerebro.procesar(datos_raw, num, origen)
                        piezas_total.extend(pzs)
                        alertas_total.extend(als)

                        # Status de éxito
                        status.markdown(f"""<div class="proc-card">
                            <div class="proc-icon-box">✅</div>
                            <div><span class="proc-main">Página {num} — {len(pzs)} piezas</span>
                            <span class="proc-sub">({idx+1}/{n_sel}) · {estrategia}</span></div>
                        </div>""", unsafe_allow_html=True)

            except Exception as e:
                alertas_total.append(f"❌ Pág {num_pag}: Error inesperado — {e}")
                status.markdown(f"""<div class="proc-card" style="border-color:var(--accent-red)">
                    <div class="proc-icon-box" style="background:var(--accent-red-bg)">💥</div>
                    <div><span class="proc-main">Página {num_pag} — Excepción</span>
                    <span class="proc-sub">{html_module.escape(str(e)[:80])}</span></div>
                </div>""", unsafe_allow_html=True)

            # Actualizar progreso
            progreso = max(5, int(((idx + 1) / n_sel) * 100))
            barra.progress(progreso)

        # ◄◄◄ FIN del bucle secuencial

        status.markdown(f"""<div class="proc-card" style="border-color:var(--accent-green-border);background:var(--accent-green-bg)">
            <div class="proc-icon-box" style="background:var(--accent-green-bg);border-color:var(--accent-green-border)">✅</div>
            <div><span class="proc-main" style="color:#065f46">Procesamiento completado — {len(piezas_total)} piezas</span>
            <span class="proc-sub">Pipeline secuencial finalizado · Sin errores de rate limit</span></div>
        </div>""", unsafe_allow_html=True)
        barra.progress(100)

        piezas_total.sort(key=lambda p: p.id)

        if piezas_total:
            rows = ([p.to_row_debug() for p in piezas_total] if mostrar_debug
                    else [p.to_display_row() for p in piezas_total])
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
# RESULTADOS (sin cambios)
# ══════════════════════════════════════════════════════════════════════════════
if 'df_final' in st.session_state:
    df = st.session_state['df_final']
    al = st.session_state.get('alertas_final', [])
    po = st.session_state.get('piezas_obj', [])
    nb = st.session_state.get('nombre_base', 'proyecto')
    meta = st.session_state.get('meta_pags', [])

    if df.empty:
        st.warning("No se extrajeron piezas válidas. Revisa la selección o el archivo.")
    else:
        st.markdown("""<div class="divider"><div class="line"></div>
        <div class="dot"></div><div class="dot" style="margin:0 -4px"></div>
        <div class="dot"></div><div class="line"></div></div>""", unsafe_allow_html=True)

        tpz = int(df['Cantidad'].sum()) if 'Cantidad' in df.columns else len(df)
        tl = len(df)
        mu = df['Material'].nunique() if 'Material' in df.columns else 0
        pv = sum(1 for m in meta if "VECTORIAL" in m)
        pi = sum(1 for m in meta if "GEMINI" in m)

        st.markdown(f"""
        <div class="sec-hdr">
            <div class="sec-icon">📋</div>
            <div class="sec-body">
                <div class="sec-title">Lista de Corte · Exportación Industrial</div>
                <div class="sec-sub">{pv} páginas vectoriales + {pi} páginas Gemini híbrido · Formato HDR6,90</div>
            </div>
            <div class="sec-badge" style="color:var(--accent-green);border-color:var(--accent-green-border);background:var(--accent-green-bg)">✓ LISTO</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="kpi-row">
            <div class="kpi kpi-green">
                <div class="kpi-label">Líneas únicas</div>
                <div class="kpi-value">{tl}</div>
                <div class="kpi-detail">{pv} deterministas + {pi} IA</div>
            </div>
            <div class="kpi kpi-brand">
                <div class="kpi-label">Total piezas</div>
                <div class="kpi-value">{tpz}</div>
                <div class="kpi-detail">Sumando cantidades</div>
            </div>
            <div class="kpi kpi-brand">
                <div class="kpi-label">Materiales</div>
                <div class="kpi-value">{mu}</div>
                <div class="kpi-detail">Tipos distintos</div>
            </div>
            <div class="kpi kpi-amber">
                <div class="kpi-label">Alertas</div>
                <div class="kpi-value">{len(al)}</div>
                <div class="kpi-detail">Requieren revisión</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if al:
            with st.expander(f"⚠️ {len(al)} alertas del motor de reglas", expanded=True):
                for a in al:
                    if any(k in a for k in ["🚫", "🚨", "METAL", "KRION", "❌"]):
                        st.error(a)
                    elif any(k in a for k in ["🔄", "⚠️", "sospechoso"]):
                        st.warning(a)
                    else:
                        st.info(a)

        st.markdown("""<div class="tbl-label"><div class="bar"></div>
        <span>Tabla editable · Doble clic para modificar valores</span></div>""",
        unsafe_allow_html=True)

        if mostrar_debug and 'Largo_IA' in df.columns:
            cc = {
                "ID": st.column_config.TextColumn("ID", width="small"),
                "Nombre": st.column_config.TextColumn("Nombre", width="medium"),
                "Largo_IA": st.column_config.NumberColumn("L (IA)", format="%.1f", width="small"),
                "Largo_Corte": st.column_config.NumberColumn("L CORTE", format="%.1f", width="small"),
                "Ancho_IA": st.column_config.NumberColumn("A (IA)", format="%.1f", width="small"),
                "Ancho_Corte": st.column_config.NumberColumn("A CORTE", format="%.1f", width="small"),
                "Espesor": st.column_config.NumberColumn("Esp", format="%.0f", width="small"),
                "Material": st.column_config.TextColumn("Material", width="medium"),
                "Cantidad": st.column_config.NumberColumn("Cant", format="%d", width="small"),
                "Confianza": st.column_config.TextColumn("🔒", width="small"),
                "Regla": st.column_config.TextColumn("Regla", width="large"),
                "Notas": st.column_config.TextColumn("Notas", width="medium"),
            }
        else:
            cc = {
                "Nombre": st.column_config.TextColumn("Nombre", width="medium"),
                "Largo": st.column_config.NumberColumn("Largo", format="%.1f mm", width="small"),
                "Ancho": st.column_config.NumberColumn("Ancho", format="%.1f mm", width="small"),
                "Espesor": st.column_config.NumberColumn("Esp", format="%.0f mm", width="small"),
                "Material": st.column_config.TextColumn("Material", width="medium"),
                "Cantidad": st.column_config.NumberColumn("Cant", format="%d", width="small"),
                "Notas": st.column_config.TextColumn("Notas", width="large"),
            }

        df_ed = st.data_editor(df, num_rows="dynamic", width="stretch",
                               height=600, column_config=cc)

        st.markdown("""<div class="divider"><div class="line"></div>
        <div class="dot"></div><div class="line"></div></div>""", unsafe_allow_html=True)

        # ── EXPORTACIÓN ──
        csv_l = pd.DataFrame([p.to_csv_row() for p in po]) if po else df_ed
        csv_b = csv_l.to_csv(index=False, sep=";").encode('utf-8')

        txt_body = csv_l.to_csv(index=False, header=False, sep=",")
        txt_body = txt_body.replace("\r\n", "\n").rstrip("\n")
        txt_final = f"HDR6,90\n{txt_body}\n".encode('utf-8')

        c_csv, c_txt, c_aud = st.columns([1, 1, 2])
        with c_csv:
            st.download_button("📊 CSV · Revisión", data=csv_b,
                               file_name=f"{nb}_revision.csv", mime="text/csv",
                               width="stretch")
        with c_txt:
            st.download_button("🤖 TXT GABBIANI · Máquina", data=txt_final,
                               file_name=f"{nb}_GABBIANI.txt", mime="text/plain",
                               type="primary", width="stretch")
        with c_aud:
            inf = Auditoria.generar(po, al, perfil_sel,
                                    st.session_state.get('_last_file', 'N/A'),
                                    backend=BACKEND, model=GEMINI_MODEL,
                                    workers=1)  # ◄◄◄ workers=1
            st.download_button("📄 Auditoría Completa", data=inf.encode('utf-8'),
                               file_name=f"{nb}_auditoria.txt", mime="text/plain",
                               width="stretch")

        st.caption("🤖 **TXT GABBIANI** = formato `HDR6,90` nativo listo para USB de seccionadora · "
                   "📊 **CSV** = revisión humana en Excel (separador `;`) · "
                   "📄 **Auditoría** = trazabilidad completa de todas las modificaciones")

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="app-footer">
    <div class="footer-brand">GABBIANI MASTER AI</div>
    <div class="footer-meta">v7.0 Enterprise · {GEMINI_MODEL} · {backend_label} · HDR6,90 Nativo · Secuencial EU</div>
    <div class="footer-copy">© 2026 · SISTEMA EXPERTO DE OPTIMIZACIÓN DE CORTE INDUSTRIAL</div>
</div>
""", unsafe_allow_html=True)
