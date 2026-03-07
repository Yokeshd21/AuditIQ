import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import re
import json

from utils import (
    load_css,
    extract_text,
    calculate_performance,
    create_excel_download,
    create_pdf_download,
    apply_color_coding,
)
from ai_wrapper import get_groq_client, evaluate_performance, re_evaluate_with_trace

st.set_page_config(
    page_title="Streamlit",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS matching the target exactly
st.markdown(
    """
<style>
    /* Global Font */
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;600;700;800&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Source Sans Pro', sans-serif;
    }

    /* Hide standard header */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Main Background - pure white 'Paper' aesthetic */
    .stApp {
        background: #ffffff !important;
        color: #1e293b !important; /* Deep Charcoal */
    }

    /* Center container restriction to match visual flow */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 5rem !important;
        max-width: 960px !important;
    }

    /* Sidebar Background & Text colors */
    [data-testid="stSidebar"] {
        background-color: #3b82f6 !important; /* Material Blue */
        border-right: none !important;
    }

    /* Sidebar Text overriding */
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    /* Hide specific selectbox labels completely */
    .stSelectbox label {
        display: none !important;
    }

    /* Sidebar Selectbox Customization */
    [data-testid="stSidebar"] div[data-baseweb="select"] {
        cursor: pointer;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: #f4f6f8 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 4px;
        min-height: 48px;
    }
    /* Set selectbox text to dark gray inside the sidebar select container */
    [data-testid="stSidebar"] div[data-baseweb="select"] span {
        color: #333333 !important;
        font-size: 15px !important;
        font-weight: 400 !important;
    }
    [data-testid="stSidebar"] div[data-baseweb="select"] svg {
        fill: #333 !important;
        color: #333 !important;
    }
    /* Fix the specific text node Streamlit generates so it isn't white */
    .stSelectbox div[data-baseweb="select"] * {
        color: #333333 !important;
    }

    /* Global Override for sidebar text exceptions */
    [data-testid="stSidebar"] [data-baseweb="select"] * {
        color: #333333 !important;
    }

    /* Sidebar Green Clear/Reset Button */
    [data-testid="stSidebar"] .stButton {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        margin: 0 auto !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #34A853 0%, #2c9347 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 10px 32px !important;
        box-shadow: 0 4px 12px rgba(52, 168, 83, 0.3);
        transition: all 0.3s ease-in-out !important;
        font-size: 14px !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #2c9347 0%, #1a7a3a 100%) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 16px rgba(52, 168, 83, 0.4) !important;
    }
    [data-testid="stSidebar"] .stButton > button:active {
        transform: translateY(-1px) !important;
    }

    /* Main Area Selectbox customization */
    div[data-baseweb="select"] > div {
        background-color: #e5e7eb !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        min-height: 48px;
    }
    div[data-baseweb="select"] span {
        color: #111827 !important;
        font-size: 15px !important;
    }
    div[data-baseweb="select"] svg {
        fill: #000 !important;
    }

    /* Horizontal rule styling */
    hr {
        border: 0;
        border-top: 2px solid #555555;
        margin: 1.5rem 0 3.5rem 0 !important;
    }

    /* ═══════════════════════════════════════════════
       PREMIUM FILE UPLOADER — Animated Drop Zone
    ═══════════════════════════════════════════════ */

    /* Keyframes */
    @keyframes dashedSpin {
        0%   { stroke-dashoffset: 0; }
        100% { stroke-dashoffset: 60; }
    }
    @keyframes pulseGlow {
        0%, 100% { box-shadow: 0 0 0 0 rgba(59,130,246,0.0),  0 4px 24px rgba(59,130,246,0.06); }
        50%       { box-shadow: 0 0 0 6px rgba(59,130,246,0.08), 0 8px 32px rgba(59,130,246,0.16); }
    }
    @keyframes floatIcon {
        0%, 100% { transform: translateY(0px) scale(1);    }
        50%       { transform: translateY(-8px) scale(1.05); }
    }
    @keyframes browseShine {
        0%   { left: -100%; }
        55%  { left: 220%; }
        100% { left: 220%; }
    }
    @keyframes fadeSlideIn {
        from { opacity: 0; transform: translateY(10px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Drop Zone Container */
    [data-testid="stFileUploadDropzone"] {
        position: relative !important;
        background: linear-gradient(135deg, #f8faff 0%, #eef4ff 50%, #f0f9ff 100%) !important;
        border: 2px dashed #93c5fd !important;
        border-radius: 20px !important;
        padding: 3.5rem 2.5rem !important;
        text-align: center !important;
        cursor: pointer !important;
        transition: all 0.45s cubic-bezier(0.23, 1, 0.32, 1) !important;
        animation: pulseGlow 3s ease-in-out infinite, fadeSlideIn 0.5s ease !important;
        overflow: hidden !important;
    }

    /* Radial spotlight overlay (decorative) */
    [data-testid="stFileUploadDropzone"]::before {
        content: '' !important;
        position: absolute !important;
        inset: 0 !important;
        background: radial-gradient(ellipse at 50% 30%, rgba(59,130,246,0.07) 0%, transparent 70%) !important;
        pointer-events: none !important;
        border-radius: inherit !important;
    }

    /* Hover State */
    [data-testid="stFileUploadDropzone"]:hover {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 50%, #e0f2fe 100%) !important;
        border-color: #3b82f6 !important;
        border-style: solid !important;
        transform: translateY(-3px) scale(1.01) !important;
        box-shadow: 0 12px 40px rgba(59,130,246,0.18), 0 4px 16px rgba(59,130,246,0.10) !important;
        animation: none !important;
    }

    /* Active / Drag-over */
    [data-testid="stFileUploadDropzone"]:active,
    [data-testid="stFileUploadDropzone"][data-dragging="true"] {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%) !important;
        border-color: #2563eb !important;
        transform: scale(1.02) !important;
        box-shadow: 0 16px 48px rgba(59,130,246,0.25) !important;
    }

    /* Upload SVG Icon — floating animation */
    [data-testid="stFileUploadDropzone"] svg {
        fill: #3b82f6 !important;
        color: #3b82f6 !important;
        filter: drop-shadow(0 4px 8px rgba(59,130,246,0.30)) !important;
        animation: floatIcon 2.8s ease-in-out infinite !important;
    }

    /* Drag & drop main label */
    [data-testid="stFileUploadDropzone"] p {
        color: #1e3a5f !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: 0.2px !important;
        margin-top: 12px !important;
    }

    /* Hint text "Limit … per file" — NOT in button */
    [data-testid="stFileUploadDropzone"] span:not(button span):not(button *) {
        color: #64748b !important;
        font-size: 12.5px !important;
        font-weight: 500 !important;
        letter-spacing: 0.1px !important;
    }

    /* ── Browse Files Button ── */
    [data-testid="stFileUploadDropzone"] button {
        position: relative !important;
        overflow: hidden !important;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 60%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 11px 32px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 5px 18px rgba(59,130,246,0.45), 0 2px 6px rgba(37,99,235,0.3) !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease, background 0.3s ease !important;
        cursor: pointer !important;
        margin-top: 8px !important;
    }

    /* Shimmer sweep on button */
    [data-testid="stFileUploadDropzone"] button::after {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 60% !important;
        height: 100% !important;
        background: linear-gradient(to right,
            rgba(255,255,255,0)   0%,
            rgba(255,255,255,0.35) 50%,
            rgba(255,255,255,0)   100%) !important;
        transform: skewX(-18deg) !important;
        animation: browseShine 2.8s ease-in-out infinite !important;
    }

    /* Button text — force white at all times */
    [data-testid="stFileUploadDropzone"] button span,
    [data-testid="stFileUploadDropzone"] button * {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* Button hover */
    [data-testid="stFileUploadDropzone"] button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        transform: translateY(-3px) scale(1.04) !important;
        box-shadow: 0 10px 28px rgba(59,130,246,0.55) !important;
    }

    /* Button press */
    [data-testid="stFileUploadDropzone"] button:active {
        transform: translateY(-1px) scale(0.97) !important;
        box-shadow: 0 4px 12px rgba(59,130,246,0.35) !important;
    }

    /* Uploaded file info chips */
    [data-testid="stFileUploaderFileName"],
    [data-testid="stFileUploaderFileSize"],
    .stFileUploaderFileData,
    [data-testid="stUploadedFileName"],
    .uploadedFileName,
    .uploadedFileSize {
        color: #1e293b !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }


    /* Loading Spinner Text Color */
    .stSpinner > div > div {
        color: #111827 !important; /* Black/Dark Gray text for visibility on white background */
        font-weight: 600 !important;
    }

    /* Typography Overrides */
    .title-text {
        text-align: center;
        font-size: 34px;
        font-weight: 800;
        color: #000000;
        margin-bottom: 2px;
        letter-spacing: -0.5px;
    }

    .section-left-title {
        font-size: 28px;
        font-weight: 800;
        color: #000000;
        line-height: 1.3;
        margin-top: 15px;
    }

    .mouse-icon-container {
        text-align: left;
        padding-left: 20px;
        margin-top: 10px;
    }

    /* Upload labels styling hack -> overriding streamlit label */
    .stFileUploader label {
        display: block !important;
        color: #333333 !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        margin-bottom: 5px !important;
    }

    /* Reusing some logic styles */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 22px 18px;
        text-align: center;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        border-color: #3b82f6;
    }
    .metric-card .label { font-size: 0.72rem; font-weight: 700; color: #6b7280; text-transform: uppercase; margin-bottom: 8px; }
    .metric-card .value { font-size: 2.2rem; font-weight: 900; line-height: 1; color: #111827; }
    .metric-card .value.good { color: #10b981; }
    .metric-card .value.warn { color: #f59e0b; }
    .metric-card .value.bad { color: #ef4444; }

    /* Result section headers */
    .sec-head {
        font-size: 1.25rem;
        font-weight: 800;
        color: #111827;
        margin: 2.5rem 0 1rem 0;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.5rem;
    }

    /* Logic Table headers fix */
    div[data-testid="stDataFrame"] {
        background: #ffffff !important;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
        overflow: hidden;
        border: 1px solid #d1d5db !important;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* Prevent empty space in table container */
    [data-testid="stDataFrame"] {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Enhanced Table Styling */
    [data-testid="stDataFrame"] table {
        width: 100% !important;
        border-collapse: collapse !important;
        background: #ffffff !important;
        border-spacing: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    [data-testid="stDataFrame"] thead {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    }

    [data-testid="stDataFrame"] th {
        background: inherit !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        padding: 14px 12px !important;
        border: 1px solid #1d4ed8 !important;
        text-align: left !important;
        font-size: 13px !important;
        letter-spacing: 0.3px !important;
    }

    [data-testid="stDataFrame"] td {
        padding: 12px !important;
        border: 1px solid #d1d5db !important;
        color: #111827 !important;
        background: #ffffff !important;
        font-size: 13px !important;
    }

    [data-testid="stDataFrame"] tbody {
        margin: 0 !important;
        padding: 0 !important;
    }

    [data-testid="stDataFrame"] tbody tr {
        background: #ffffff !important;
        transition: background-color 0.2s ease;
        border-bottom: 1px solid #d1d5db !important;
    }

    [data-testid="stDataFrame"] tbody tr:hover {
        background: #f3f4f6 !important;
    }

    [data-testid="stDataFrame"] tbody tr:nth-child(odd) {
        background: #fafafa !important;
    }

    [data-testid="stDataFrame"] tbody tr:nth-child(odd):hover {
        background: #f0f0f0 !important;
    }

    /* Remove scrollbar padding */
    [data-testid="stDataFrame"] .stTable {
        padding: 0 !important;
    }

    /* Clean, Animated Execute Button */
    @keyframes subtlePulse {
        0% { box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2); }
        50% { box-shadow: 0 4px 25px rgba(59, 130, 246, 0.4); }
        100% { box-shadow: 0 4px 15px rgba(59, 130, 246, 0.2); }
    }

    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important;
        font-family: 'Inter', 'Roboto', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 16px 32px !important;
        font-size: 16px !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        animation: subtlePulse 3s infinite;
        position: relative;
        overflow: hidden;
    }

    .stButton > button::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 50%;
        height: 100%;
        background: linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0) 100%);
        transform: skewX(-25deg);
        transition: all 0.7s ease;
    }

    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.5) !important;
    }

    .stButton > button:hover::after {
        left: 200%;
    }

    .stButton > button:active {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
    }

    /* ── Download Buttons ── */
    @keyframes downloadShine {
        0%   { left: -100%; }
        60%  { left: 200%; }
        100% { left: 200%; }
    }

    [data-testid="stDownloadButton"] > button {
        position: relative !important;
        overflow: hidden !important;
        color: #ffffff !important;
        font-family: 'Inter', 'Source Sans Pro', sans-serif !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        letter-spacing: 0.4px !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 28px !important;
        width: 100% !important;
        cursor: pointer !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
    }

    /* Excel button — green gradient */
    [data-testid="stDownloadButton"]:nth-of-type(1) > button {
        background: linear-gradient(135deg, #059669 0%, #10b981 50%, #34d399 100%) !important;
        box-shadow: 0 4px 18px rgba(16, 185, 129, 0.35) !important;
    }

    /* PDF button — indigo/purple gradient */
    [data-testid="stDownloadButton"]:nth-of-type(2) > button {
        background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 50%, #8b5cf6 100%) !important;
        box-shadow: 0 4px 18px rgba(109, 40, 217, 0.35) !important;
    }

    /* Shine sweep on both */
    [data-testid="stDownloadButton"] > button::after {
        content: '';
        position: absolute !important;
        top: 0 !important;
        left: -100% !important;
        width: 55% !important;
        height: 100% !important;
        background: linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.28) 50%, rgba(255,255,255,0) 100%) !important;
        transform: skewX(-20deg) !important;
        animation: downloadShine 2.8s infinite !important;
    }

    /* Hover lift + stronger glow */
    [data-testid="stDownloadButton"]:nth-of-type(1) > button:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 0 10px 28px rgba(16, 185, 129, 0.55) !important;
    }
    [data-testid="stDownloadButton"]:nth-of-type(2) > button:hover {
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 0 10px 28px rgba(109, 40, 217, 0.55) !important;
    }

    /* Active press */
    [data-testid="stDownloadButton"] > button:active {
        transform: translateY(-1px) scale(0.99) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<h2 style='text-align: center; font-weight: 400; font-size: 26px; margin-top: 10px; margin-bottom: 30px;'>Solutions Scope</h2>",
        unsafe_allow_html=True,
    )

    # Placeholders matching screenshot exactly
    sidebar_app = st.selectbox("Application", ["Select Application", "LLMatScale.ai"])
    st.selectbox("Application", ["Select LLM model", "Groq"])
    st.selectbox("Specifications 2", ["LLM Framework"])
    st.selectbox("Specifications 3", ["GCP Services Used"])

    # Adding spacing
    st.markdown("<div style='height: 30px;justify-content: center;'></div>", unsafe_allow_html=True)
    clear_btn = st.button("Clear/Reset", key="clear_btn")

    st.markdown(
        """
        <div style='text-align: center; margin-top: 4rem;'>
            <p style='font-size: 16px; font-weight: 600; margin-bottom: 20px;'>Build & Deployed on</p>
            <div style='display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-top: 15px;'>
                <div style='width: 30px; height: 70px; border-radius: 8px; display: flex; align-items: center; justify-content: center;'>
                    <img src='https://i.im.ge/2026/03/04/eYH8HT.image.png' width='30' style='object-fit: contain;'>
                </div>
                <div style='width: 30px; height: 70px; border-radius: 8px; display: flex; align-items: center; justify-content: center;'>
                    <img src='https://i.im.ge/2026/03/04/eYHgy0.oie-png.png' width='30' style='object-fit: contain;'>
                </div>
                <div style='width: 30px; height: 70px; border-radius: 8px; display: flex; align-items: center; justify-content: center;'>
                    <img src='https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Amazon_Web_Services_Logo.svg/1280px-Amazon_Web_Services_Logo.svg.png' width='30' style='object-fit: contain;'>
                </div>
                <div style='width: 30px; height: 70px; border-radius: 8px; display: flex; align-items: center; justify-content: center;'>
                    <img src='https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Microsoft_Azure.svg/1200px-Microsoft_Azure.svg.png' width='30' style='object-fit: contain;'>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if clear_btn:
        st.session_state.history = []
        st.session_state.current_evaluation = None
        st.rerun()

# ─── MAIN CONTENT ─────────────────────────────────────────────────────────────

# --- Top Logo (Circular Hero Logo) ---
st.markdown(
    """
<div style="display: flex; justify-content: center; align-items: center; margin-bottom: 5px; margin-top: -50px;">
    <img src="https://i.im.ge/2026/03/04/eYH8HT.image.png" width="180">
</div>
""",
    unsafe_allow_html=True,
)

# --- Main Title ---
st.markdown("<div class='title-text' style='margin-bottom: 25px;'>Agentic AI Learning Program – Foundational Learning</div>", unsafe_allow_html=True)
st.markdown("<hr style='margin-bottom: 30px;'>", unsafe_allow_html=True)

# --- Row 1: Select Application ---
c1, c2 = st.columns([1.0, 1.0])
with c1:
    st.markdown("<div class='section-left-title' style='margin-top: 0;'>Select Application</div>", unsafe_allow_html=True)
with c2:
    if sidebar_app == "Select Application":
        st.markdown("<div style='margin-top: 15px; font-size: 16px; color: #666; font-weight: 600;'>Please select the application in the left sidebar.</div>", unsafe_allow_html=True)
        selected_app = "None"
    else:
        selected_app = st.selectbox("app_selector_main", ["Select an application", "CUCP Re-Evaluations", "Personal Narrative"], key="app_selector_main")

st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)

# --- Initialize File Variables ---
narrative_file = None
rubric_file = None
personal_narrative_file = None

# --- Conditional Upload Sections Based on Application ---
if selected_app == "Select an application":
    # Show empty space when no application selected
    st.markdown("<div style='height: 300px;'></div>", unsafe_allow_html=True)

elif selected_app == "CUCP Re-Evaluations":
    # --- Row 2: Upload Narrative ---
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.markdown("<div class='section-left-title'>Upload the<br>Narrative (PDF)</div>", unsafe_allow_html=True)
    with c2:
        narrative_file = st.file_uploader("Upload CUCP Narrative", type=["pdf", "docx", "txt"], key="cucp_narrative")

    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

    # --- Row 3: Upload Rubric ---
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.markdown("<div class='section-left-title'>Upload the<br>Rubric (PDF)</div>", unsafe_allow_html=True)
    with c2:
        rubric_file = st.file_uploader("Upload CUCP Rubric", type=["pdf", "docx", "txt"], key="cucp_rubric")

elif selected_app == "Personal Narrative":
    # --- Row 2: Upload Personal Narrative ---
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.markdown("<div class='section-left-title'>Upload Personal<br>Narrative (PDF)</div>", unsafe_allow_html=True)
    with c2:
        personal_narrative_file = st.file_uploader("Upload Personal Narrative", type=["pdf", "docx", "txt"], key="personal_narrative")

    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

    # --- Row 3: Upload Rubric ---
    c1, c2 = st.columns([1, 1.4])
    with c1:
        st.markdown("<div class='section-left-title'>Upload the<br>Rubric (PDF)</div>", unsafe_allow_html=True)
    with c2:
        rubric_file = st.file_uploader("Upload Rubric", type=["pdf", "docx", "txt"], key="personal_rubric")

st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

# ─── APP LOGIC (EVALUATION EXECUTION) ─────────────────────────────────────────
analyze_btn = st.button("🚀 Execute Operational Audit", use_container_width=True)

if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_evaluation' not in st.session_state:
    st.session_state.current_evaluation = None
if 'editable_data' not in st.session_state:
    st.session_state.editable_data = None
if 'refinement_mode' not in st.session_state:
    st.session_state.refinement_mode = False
if 'edited_trace' not in st.session_state:
    st.session_state.edited_trace = ""
if 'edited_narrative' not in st.session_state:
    st.session_state.edited_narrative = ""
# Store rubric & narrative text for trace-guided re-evaluation
if 'rubric_text_stored' not in st.session_state:
    st.session_state.rubric_text_stored = ""
if 'narrative_text_stored' not in st.session_state:
    st.session_state.narrative_text_stored = ""

if analyze_btn:
    if not rubric_file or (selected_app == "CUCP Re-Evaluations" and not narrative_file) or (selected_app == "Personal Narrative" and not personal_narrative_file):
        st.error("⚠️  Please upload both the Rubric and Narrative documents.")
    else:
        client = get_groq_client()
        if not client:
            st.error("🔑  Groq API Key missing. Set the `GROQ_API_KEY` environment variable.")
        else:
            with st.spinner("🤖  AI Auditor analysing operational data…"):
                rubric_text = extract_text(rubric_file)

                if selected_app == "CUCP Re-Evaluations":
                    narrative_text = extract_text(narrative_file)
                else:  # Personal Narrative
                    narrative_text = extract_text(personal_narrative_file)

                # Store for trace-guided re-evaluation later
                st.session_state.rubric_text_stored  = rubric_text
                st.session_state.narrative_text_stored = narrative_text

                result_text = evaluate_performance(
                    client=client,
                    rubric_text=rubric_text,
                    narrative_text=narrative_text,
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                )

                if result_text:
                    st.session_state.current_evaluation = result_text
                    
                    # Parse results for interactivity
                    trace_match = re.search(r'<trace>(.*?)</trace>', result_text, re.DOTALL)
                    st.session_state.edited_trace = trace_match.group(1).strip() if trace_match else "Processing thoughts..."
                    
                    json_match = re.search(r'<json>(.*?)</json>', result_text, re.DOTALL)
                    if json_match:
                        try:
                            st.session_state.editable_data = json.loads(json_match.group(1).strip())
                        except:
                            st.session_state.editable_data = None
                    
                    main_text = re.sub(r'<trace>.*?</trace>', '', result_text, flags=re.DOTALL)
                    main_text = re.sub(r'<json>.*?</json>', '', main_text, flags=re.DOTALL).strip()
                    st.session_state.edited_narrative = main_text

                    st.session_state.history.append(
                        {
                            "timestamp": time.time(),
                            "score": 100, # Legacy metric
                            "data": result_text,
                        }
                    )
                    st.success("✅  Narrative Architect Complete!")

if st.session_state.current_evaluation:
    # Use session state for all rendering to ensure edits are reflected
    data = st.session_state.editable_data
    if not isinstance(data, dict):
        # Fallback parsing if state is empty
        json_match = re.search(r'<json>(.*?)</json>', st.session_state.current_evaluation, re.DOTALL)
        try:
            data = json.loads(json_match.group(1).strip()) if json_match else {}
        except:
            data = {}
    
    # Ensure data is a dictionary for the rest of the logic
    data = dict(data) if data else {}
    
    trace_content = st.session_state.edited_trace
    main_text = st.session_state.edited_narrative
    
    # ─── A. TRACING PHASE ───
    if st.session_state.refinement_mode:
        st.markdown("<div class='sec-head'>⚙️ Refine Trace (Internal Reasoning)</div>", unsafe_allow_html=True)
        st.session_state.edited_trace = st.text_area("Edit Trace Content", value=st.session_state.edited_trace, height=200, label_visibility="collapsed")
    else:
        formatted_trace = trace_content.replace("\n", "<br>")
        st.markdown(f"""
        <div id="tracing-container" class="glass-card" style="margin-bottom: 2rem; border-left: 4px solid #3b82f6; padding: 1.5rem;">
            <h4 style="margin-top:0; color:#3b82f6; display:flex; align-items:center;">
                <svg style="width:20px;height:20px;margin-right:8px;fill:#3b82f6;" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/></svg>
                Tracing Phase (Internal Reasoning)
            </h4>
            <div id="tracing-content" style="display:none; color:#64748b; font-style:italic; line-height: 1.6; margin-top: 15px; border-top: 1px solid #e2e8f0; padding-top: 15px;">
                {formatted_trace}
            </div>
            <button 
                onclick="document.getElementById('tracing-content').style.display='block'; this.style.display='none'; document.getElementById('tracing-container').classList.remove('shimmer');" 
                style="margin-top:15px; padding:8px 20px; border-radius:6px; border:1px solid #3b82f6; background:transparent; color:#3b82f6; font-weight:600; cursor:pointer; transition: all 0.3s ease;">
                View Trace
            </button>
        </div>
        """, unsafe_allow_html=True)

    # ─── B. METRICS DASHBOARD (Restored) ───
    if data:
        score, band, risk, supervision, badge_html = calculate_performance(data)
        meets = all(str(i.get("Status", "")).strip().upper() == "YES" for i in data.get("Evaluation", []))

        def color_class(val, good, bad):
            v = str(val).strip().upper()
            if v in bad: return "bad"
            if v in good: return "good"
            return "warn"

        sc = "good" if score >= 75 else "warn" if score >= 50 else "bad"
        rc = color_class(risk, {"LOW"}, {"HIGH", "CRITICAL"})
        vc = color_class(supervision, {"MINIMAL", "STANDARD"}, {"DIRECT"})
        mc = "good" if meets else "bad"

        st.markdown("<div class='sec-head'>📊  Performance Overview</div>", unsafe_allow_html=True)
        metrics_cols = st.columns(4, gap="medium")
        metrics = [
            (metrics_cols[0], "Performance Score", f"{score}%", sc, badge_html),
            (metrics_cols[1], "Compliance Risk", risk, rc, ""),
            (metrics_cols[2], "Supervision Level", supervision, vc, ""),
            (metrics_cols[3], "Meets Standards", "PASS" if meets else "FAIL", mc, ""),
        ]
        for col, label, value, cls, extra in metrics:
            with col:
                extra_html = f"<div style='margin-top:8px;'>{extra}</div>" if extra else ""
                st.markdown(f"""<div class='metric-card'><div class='label'>{label}</div><div class='value {cls}'>{value}</div>{extra_html}</div>""", unsafe_allow_html=True)

        st.markdown("<div class='sec-head'>🗂  Operational Audit Matrix</div>", unsafe_allow_html=True)
        if "Evaluation" in data:
            eval_list = data.get("Evaluation", [])
            df = pd.DataFrame(eval_list)

            if st.session_state.refinement_mode:
                # EDITABLE MODE
                try:
                    edited_df = st.data_editor(
                        df, 
                        use_container_width=True, 
                        hide_index=True, 
                        key="data_editor_main",
                        column_config={
                            "Status": st.column_config.SelectboxColumn(
                                "Status",
                                options=["YES", "NO"],
                                required=True,
                            )
                        }
                    )
                    st.session_state.editable_data["Evaluation"] = edited_df.to_dict('records')
                except Exception as e:
                    st.error(f"Editor error: {e}")
            else:
                # ─── STATIC MODE: Full HTML Table (no truncation) ───
                # Build a clean HTML table so every cell (including Corrective Action) is fully visible.
                # Only the Status column gets color; all other text is plain black.
                columns = list(df.columns)
                
                html_table = """
                <div style="width:100%; overflow-x:auto; border:1px solid #d1d5db; border-radius:12px; box-shadow:0 4px 6px rgba(0,0,0,0.08); margin-bottom:1rem;">
                <table style="width:100%; border-collapse:collapse; background:#ffffff; font-family:'Source Sans Pro','Inter',sans-serif; font-size:13px;">
                <thead>
                <tr>
                """
                for col in columns:
                    html_table += f'<th style="background:linear-gradient(135deg,#3b82f6 0%,#2563eb 100%); color:#ffffff; font-weight:700; padding:14px 12px; border:1px solid #1d4ed8; text-align:left; font-size:13px; letter-spacing:0.3px; white-space:nowrap;">{col}</th>\n'
                html_table += "</tr>\n</thead>\n<tbody>\n"
                
                for idx, row in df.iterrows():
                    bg = "#ffffff" if idx % 2 == 0 else "#fafafa"
                    html_table += f'<tr style="background:{bg};">\n'
                    for col in columns:
                        try:
                            v = row[col]
                            cell_val = "" if v is None or (not isinstance(v, (list, dict)) and pd.isna(v)) else str(v)
                        except (TypeError, ValueError):
                            cell_val = str(row[col]) if row[col] is not None else ""

                        # ── Clean up Python list-string formatting ──
                        # e.g. "['Provide documented evidence...', 'item2']" → "Provide documented evidence... • item2"
                        import ast
                        stripped = cell_val.strip()
                        if stripped.startswith("[") and stripped.endswith("]"):
                            try:
                                parsed = ast.literal_eval(stripped)
                                if isinstance(parsed, list):
                                    cell_val = " • ".join(str(item).strip(" '\"") for item in parsed if str(item).strip(" '\""))
                            except Exception:
                                # Fallback: manually strip outer brackets and quotes
                                cell_val = stripped[1:-1].strip().strip("'\"")
                        # Also strip stray leading/trailing quotes and brackets
                        cell_val = cell_val.strip("'\"[]")

                        # Only Status column gets color — everything else is plain black text
                        if col == "Status":
                            s_upper = cell_val.strip().upper()
                            if s_upper == "YES":
                                cell_style = "background-color:#ecfdf5; color:#059669; font-weight:700;"
                            elif s_upper == "NO":
                                cell_style = "background-color:#fef2f2; color:#dc2626; font-weight:700;"
                            else:
                                cell_style = "color:#111827; font-weight:500;"
                        else:
                            cell_style = "color:#111827; font-weight:500;"
                        
                        html_table += f'<td style="padding:12px; border:1px solid #d1d5db; {cell_style} word-wrap:break-word; max-width:300px;">{cell_val}</td>\n'
                    html_table += "</tr>\n"
                
                html_table += "</tbody>\n</table>\n</div>"
                st.markdown(html_table, unsafe_allow_html=True)


        st.markdown("<div class='sec-head'>📡  Criteria Radar — Compliance Coverage</div>", unsafe_allow_html=True)
        evals = data.get("Evaluation", [])
        if evals:
            criteria = [i.get("Criterion", "?") for i in evals]
            status_r = [1.0 if str(i.get("Status", "")).strip().upper() == "YES" else 0.15 for i in evals]
            ev_map = {"STRONG": 1.0, "MODERATE": 0.65, "WEAK": 0.35, "NONE": 0.1}
            evi_r = [ev_map.get(str(i.get("Evidence Strength", "")).strip().upper(), 0.1) for i in evals]

            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=[*status_r, status_r[0]], 
                theta=[*criteria, criteria[0]], 
                fill="toself", 
                fillcolor="rgba(16, 185, 129, 0.25)", 
                line={"color": "#10b981", "width": 3}, 
                name="Compliance Status"
            ))
            fig.add_trace(go.Scatterpolar(
                r=[*evi_r, evi_r[0]], 
                theta=[*criteria, criteria[0]], 
                fill="toself", 
                fillcolor="rgba(59, 130, 246, 0.2)", 
                line={"color": "#3b82f6", "width": 2.2, "dash": "dot"}, 
                name="Evidence Strength"
            ))
            fig.update_layout(
                polar={
                    "bgcolor": "rgba(255,255,255,0.8)", 
                    "radialaxis": {
                        "visible": True, 
                        "range": [0, 1.05], 
                        "tickvals": [0, 0.25, 0.5, 0.75, 1.0], 
                        "ticktext": ["0%", "25%", "50%", "75%", "100%"],
                        "tickfont": {"color": "black"}
                    },
                    "angularaxis": {
                        "tickfont": {"color": "black", "size": 12, "weight": "bold"}
                    }
                }, 
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)", 
                height=450, 
                margin={"l": 80, "r": 80, "t": 40, "b": 40}
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("<div class='sec-head'>📋  Executive Operational Summary</div>", unsafe_allow_html=True)
        st.markdown("<div style='background: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        if "Executive Summary" in data:
            for k, v in data["Executive Summary"].items():
                st.markdown(f"""<div style='margin-bottom: 15px;'><div style='font-size: 0.8rem; font-weight: 700; color: #64748b; text-transform: uppercase;'>{k}</div><div style='font-size: 1rem; color: #1e293b; line-height: 1.5;'>{v}</div></div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ─── D. HUMAN-IN-THE-LOOP (Buttons) ───
    st.markdown("<h3 style='color:#1f2937; margin-bottom: 20px;'>🔄 Human-in-the-Loop Approval</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2, gap="large")
    with col1:
        if st.session_state.refinement_mode:
            if st.button("💾 Save & Update View", use_container_width=True):
                # ── TRACE-GUIDED LLM RE-EVALUATION ──
                user_trace = st.session_state.edited_trace.strip()
                rubric_stored   = st.session_state.get("rubric_text_stored", "")
                narrative_stored = st.session_state.get("narrative_text_stored", "")

                if user_trace and rubric_stored and narrative_stored:
                    client = get_groq_client()
                    if client:
                        with st.spinner("🤖  Re-evaluating based on your trace instructions…"):
                            result_text = re_evaluate_with_trace(
                                client=client,
                                rubric_text=rubric_stored,
                                narrative_text=narrative_stored,
                                user_trace_instructions=user_trace,
                                model="llama-3.3-70b-versatile",
                                temperature=0.5,
                            )
                        if result_text:
                            st.session_state.current_evaluation = result_text
                            trace_match = re.search(r'<trace>(.*?)</trace>', result_text, re.DOTALL)
                            st.session_state.edited_trace = trace_match.group(1).strip() if trace_match else user_trace
                            json_match = re.search(r'<json>(.*?)</json>', result_text, re.DOTALL)
                            if json_match:
                                try:
                                    st.session_state.editable_data = json.loads(json_match.group(1).strip())
                                except:
                                    pass
                            main_text = re.sub(r'<trace>.*?</trace>', '', result_text, flags=re.DOTALL)
                            main_text = re.sub(r'<json>.*?</json>', '', main_text, flags=re.DOTALL).strip()
                            st.session_state.edited_narrative = main_text
                            st.success("✅  Re-evaluation complete based on your trace instructions!")
                    else:
                        st.error("🔑  Groq API Key missing.")
                else:
                    st.info("ℹ️  No trace instructions found — just saving current view.")

                st.session_state.refinement_mode = False
                st.rerun()
        else:
            if st.button("✅ Confirm & Save to Timeline", use_container_width=True):
                st.session_state.confirmed = True # Set a confirmation flag
                st.success("Draft Saved Successfully!")
    with col2:
        if st.session_state.refinement_mode:
            if st.button("❌ Cancel Refinement", use_container_width=True):
                st.session_state.refinement_mode = False
                st.rerun()
        else:
            if st.button("✍️ Refine & Edit Trace", use_container_width=True):
                st.session_state.refinement_mode = True
                st.rerun()

    # ─── C. NARRATIVE DRAFT (Contextual Visibility) ───
    if st.session_state.refinement_mode:
        st.markdown("<div class='sec-head'>🖋️ Narrative Architect Draft (Refining)</div>", unsafe_allow_html=True)
        st.session_state.edited_narrative = st.text_area("Edit Narrative Draft", value=st.session_state.edited_narrative, height=400, label_visibility="collapsed")
    elif getattr(st.session_state, 'confirmed', False):
        st.markdown("<div class='sec-head'>🖋️ Final Narrative Draft</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass-card" style="padding: 2rem; border-left: 4px solid #3b82f6; font-family: 'Inter', sans-serif; color: #1e293b; line-height: 1.7; font-size: 1.1rem;">
            {st.session_state.edited_narrative}
        </div>
        """, unsafe_allow_html=True)
    # Draft is hidden in 'Normal' mode before confirmation to match "before make it non vivble"


    # ─── E. EXPORT ───
    if data:
        st.markdown("<div class='sec-head'>💾  Export Intelligence</div>", unsafe_allow_html=True)
        st.markdown("""
        <p style="color:#111827; font-size:15px; font-weight:500; margin-bottom:16px;">
            Download the full audit report in your preferred format.
        </p>
        """, unsafe_allow_html=True)
        export_df = pd.DataFrame(data.get("Evaluation", []))
        excel_data = create_excel_download(export_df)
        pdf_data = create_pdf_download(data)
        dl1, dl2 = st.columns([1, 1], gap="medium")
        with dl1:
            st.download_button("📥 Export as Excel", data=excel_data, file_name="audit_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with dl2:
            st.download_button("📄 Export as PDF", data=pdf_data, file_name="audit_report.pdf", mime="application/pdf", use_container_width=True)


# ─── FLOATING CHATBOT ────────────────────────────────────────────────────────
st.markdown(
    """
<style>
#chatbot-fab {
    position: fixed;
    bottom: 32px;
    right: 32px;
    z-index: 9999;
    width: 64px;
    height: 64px;
    background: #3b82f6;
    border-radius: 50%;
    box-shadow: 0 4px 20px rgba(59, 130, 246, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
}
#chatbot-fab svg { width: 36px; height: 36px; fill: #fff; }

#chatbot-window {
    position: fixed;
    bottom: 110px;
    right: 32px;
    width: 340px;
    max-width: 95vw;
    background: #fff;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    z-index: 10000;
    display: none;
    flex-direction: column;
    overflow: hidden;
}
#chatbot-window.active { display: flex; }
#chatbot-header {
    background: #ffffff;
    color: #3b82f6;
    font-weight: 700;
    padding: 16px;
    font-size: 1rem;
    border-bottom: 2px solid #f8fafc;
    text-align: center;
}
#chatbot-messages { flex: 1; padding: 16px; overflow-y: auto; background: #ffffff; font-size: 0.95rem; }
#chatbot-input-row { display: flex; border-top: 1px solid #e2e8f0; background: #fff; }
#chatbot-input { flex: 1; border: none; padding: 12px; font-size: 0.95rem; outline: none; background: #fff; color: #1e293b; }
#chatbot-send { background: none; border: none; color: #3b82f6; font-size: 1.2rem; padding: 0 16px; cursor: pointer; font-weight: 700; }
</style>

<div id="chatbot-fab" onclick="document.getElementById('chatbot-window').classList.toggle('active')">
    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" opacity="0.15"/><path d="M12 2C6.48 2 2 6.48 2 12c0 4.41 3.59 8 8 8 1.85 0 3.55-.63 4.9-1.69l3.7 1.01a1 1 0 0 0 1.22-1.22l-1.01-3.7A7.963 7.963 0 0 0 22 12c0-5.52-4.48-10-10-10zm-2 13h4v2h-4v-2zm6.31-2.9l-1.41 1.41C14.53 13.53 13.3 14 12 14s-2.53-.47-3.9-1.49l-1.41-1.41A5.978 5.978 0 0 1 6 12c0-3.31 2.69-6 6-6s6 2.69 6 6c0 .34-.03.67-.09.99z"/></svg>
</div>

<div id="chatbot-window">
    <div id="chatbot-header">namma llm.ai bot</div>
    <div id="chatbot-messages"></div>
    <div id="chatbot-input-row">
        <input id="chatbot-input" type="text" maxlength="200" placeholder="Ask about this app..." onkeydown="if(event.key==='Enter'){window.sendChatbotMsg()}" />
        <button id="chatbot-send" onclick="window.sendChatbotMsg()">➤</button>
    </div>
</div>

<script>
window.sendChatbotMsg = function() {
    var input = document.getElementById('chatbot-input');
    var msg = input.value.trim();
    if(!msg) return;
    var messages = document.getElementById('chatbot-messages');
    var userMsg = document.createElement('div');
    userMsg.style.margin = '8px 0';
    userMsg.style.textAlign = 'right';
    userMsg.innerHTML = '<span style="background:#2563eb;color:#fff;padding:7px 14px;border-radius:16px 16px 2px 16px;display:inline-block;max-width:80%">'+msg+'</span>';
    messages.appendChild(userMsg);
    input.value = '';
    messages.scrollTop = messages.scrollHeight;
    // Simulate bot reply (content-restricted)
    setTimeout(function(){
        var botMsg = document.createElement('div');
        botMsg.style.margin = '8px 0';
        botMsg.style.textAlign = 'left';
        botMsg.innerHTML = '<span style="background:#f3f4f6;color:#111;padding:7px 14px;border-radius:16px 16px 16px 2px;display:inline-block;max-width:80%">'+window.getBotReply(msg)+'</span>';
        messages.appendChild(botMsg);
        messages.scrollTop = messages.scrollHeight;
    }, 700);
}

window.getBotReply = function(msg) {
    msg = msg.toLowerCase();
    if(msg.includes('criteria')||msg.includes('status')||msg.includes('evidence')||msg.includes('rubric')||msg.includes('narrative')||msg.includes('table')||msg.includes('score')){
        return 'This bot can help you with content and features of this evaluation app. Please ask about rubrics, narratives, scoring, or table details.';
    }
    if(msg.includes('hello')||msg.includes('hi')){
        return 'Hello! I am namma llm.ai bot. Ask me about this app.';
    }
    if(msg.includes('llm')||msg.includes('ai')){
        return 'This app uses LLMs for evaluation. Ask about how it works!';
    }
    if(msg.includes('reset')||msg.includes('clear')){
        return 'Use the Clear/Reset button in the sidebar to reset the app.';
    }
    if(msg.length < 8){
        return 'Please ask a content-related question about this app.';
    }
    return 'Sorry, I can only answer questions about the content and features of this app.';
}
</script>
""",
    unsafe_allow_html=True,
)