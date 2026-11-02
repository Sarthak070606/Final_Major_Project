"""
MP Groundwater Intelligence – Streamlit Dashboard
Run from project root: streamlit run dashboard/app.py
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from dashboard.views import (
    overview, map_page, station_explorer, historical_recent, quarterly,
    prediction, soil_geology, water_quality, well_suitability, data_quality,
    model_performance, about, location_search,
)
from dashboard.utils.styles import inject_css
from dashboard.utils import config as cfg
from dashboard.utils.floating_chatbot import render_floating_chatbot

st.set_page_config(
    page_title=cfg.APP_TITLE,
    page_icon=cfg.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

PAGES = {
    "🏠  Overview": overview,
    "🗺️  Groundwater Map": map_page,
    "📍  Location Search": location_search,
    "📡  Station Explorer": station_explorer,
    "📈  Historical vs Recent": historical_recent,
    "📅  Quarterly Analysis": quarterly,
    "🤖  AI Prediction": prediction,
    "🪨  Soil & Geology": soil_geology,
    "🧪  Water Quality": water_quality,
    "💧  Well Suitability": well_suitability,
    "🛡️  Data Quality": data_quality,
    "🎯  Model Performance": model_performance,
    "ℹ️  About Project": about,
}

with st.sidebar:
    st.markdown(f"# {cfg.PAGE_ICON} MP Groundwater")
    st.caption("INTELLIGENCE & MONITORING PLATFORM")
    st.markdown("---")
    choice = st.radio("NAVIGATION", list(PAGES.keys()), label_visibility="visible")
    st.markdown("---")
    st.caption("Data source: CGWB telemetry")
    st.caption("Academic decision-support system")
    st.caption("Not a substitute for field investigation")

PAGES[choice].render()
render_floating_chatbot()

st.markdown(
    '<div class="footer">MP Groundwater Intelligence · B.Tech Major Project · '
    'CGWB telemetry · For research and decision support only</div>',
    unsafe_allow_html=True,
)
