"""Preliminary Well Suitability Assessment."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from dashboard.utils import data_loader as dl


def render():
    st.markdown('<div class="page-title">Well Suitability Assessment</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Preliminary decision-support only – not a drilling authorisation</div>',
        unsafe_allow_html=True,
    )

    st.warning(
        "This module provides a **preliminary evidence summary** only. "
        "It does **not** authorise well construction or guarantee yield, "
        "depth or water quality. Professional field investigation is required."
    )

    latest = dl.load_latest_readings()
    if latest is None:
        st.info("Station data not available.")
        return

    stations = sorted(latest["station"].dropna().unique())
    station = st.selectbox("Select station / location", stations)
    row = latest[latest["station"] == station].iloc[0]

    st.subheader("Available evidence")
    c1, c2, c3 = st.columns(3)
    c1.metric("Latest groundwater level (m)", f"{row['wl_raw']:.3f}" if "wl_raw" in row else "—")
    c2.metric("District", row.get("district", "—"))
    c3.metric("Coordinates", f"{row.get('latitude', '—')}, {row.get('longitude', '—')}")

    st.markdown("#### Evidence completeness")
    evidence = {
        "Groundwater-level telemetry": "Available",
        "Historical trend (2021–2025)": "Check Historical vs Recent page",
        "Soil / lithology": "Not yet integrated",
        "Aquifer type": "Not yet integrated",
        "Laboratory water quality": "Not yet integrated",
        "Existing well inventory": "Not yet integrated",
    }
    for k, v in evidence.items():
        st.write(f"- **{k}:** {v}")

    st.markdown("#### Preliminary assessment")
    st.info(
        "**Insufficient data for a reliable suitability assessment.**\n\n"
        "Only groundwater-level telemetry is currently available. "
        "Soil, geology, aquifer and water-quality evidence are required "
        "before any investigation-method recommendation can be made."
    )

    st.caption(
        "Possible future investigation methods (for reference only, not a recommendation): "
        "dug well, borewell, auger investigation, rotary drilling – "
        "selection depends on verified geological conditions."
    )
