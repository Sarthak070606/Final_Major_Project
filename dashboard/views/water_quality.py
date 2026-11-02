"""Groundwater Quality – placeholder until laboratory data is integrated."""

from __future__ import annotations

import streamlit as st


def render():
    st.markdown('<div class="page-title">Groundwater Quality</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Laboratory measurements and drinking-water standards</div>',
        unsafe_allow_html=True,
    )

    st.warning(
        "**Actual laboratory water-quality data is not yet integrated.**\n\n"
        "This module will display measured parameters such as pH, TDS, EC, "
        "Fluoride, Nitrate, Iron and Chloride when official CGWB / state "
        "laboratory records are available."
    )

    st.info(
        "Groundwater-level telemetry **cannot** be used to infer drinking-water safety. "
        "Missing laboratory values will never be replaced by model predictions."
    )
