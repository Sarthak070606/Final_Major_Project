"""Station Explorer page."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from dashboard.utils import data_loader as dl


def render():
    st.markdown('<div class="page-title">Station Explorer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Search stations and inspect latest & historical readings</div>',
        unsafe_allow_html=True,
    )

    latest = dl.load_latest_readings()
    yearly = dl.load_yearly_summary()

    if latest is None:
        st.warning("Latest station readings not found. Run Phase 3 analytics first.")
        return

    # Filters
    districts = sorted(latest["district"].dropna().unique()) if "district" in latest.columns else []
    col1, col2 = st.columns(2)
    with col1:
        district = st.selectbox("District", ["All"] + districts)
    filtered = latest if district == "All" else latest[latest["district"] == district]

    stations = sorted(filtered["station"].dropna().unique())
    with col2:
        station = st.selectbox("Station", stations)

    row = filtered[filtered["station"] == station].iloc[0] if station else None
    if row is None:
        st.info("Select a station.")
        return

    # Metadata cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Station", station)
    c2.metric("District", row.get("district", "—"))
    c3.metric("Latitude", f"{row['latitude']:.4f}" if pd.notna(row.get("latitude")) else "—")
    c4.metric("Longitude", f"{row['longitude']:.4f}" if pd.notna(row.get("longitude")) else "—")

    if "wl_raw" in row.index:
        st.metric("Latest Groundwater Level (m)", f"{row['wl_raw']:.3f}")
    if "datetime" in row.index:
        st.caption(f"Observation time: {row['datetime']}")

    # Yearly history for this station
    if yearly is not None and "station" in yearly.columns:
        hist = yearly[yearly["station"] == station].sort_values("year")
        if not hist.empty and "wl_mean" in hist.columns:
            st.subheader("Yearly Mean Groundwater Level")
            fig = px.bar(
                hist, x="year", y="wl_mean",
                labels={"wl_mean": "Mean wl_raw (m)", "year": "Year"},
                template="plotly_white",
                color="wl_mean",
                color_continuous_scale="Teal",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=360,
                margin=dict(t=30, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(hist.reset_index(drop=True), use_container_width=True)
        else:
            st.info("No yearly summary available for this station.")
    else:
        st.info("Yearly summary file not found.")
