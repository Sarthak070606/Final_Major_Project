"""Overview Dashboard page."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import base64
import plotly.express as px
import plotly.graph_objects as go

from dashboard.utils import data_loader as dl


def render():
    st.markdown('<div class="page-title">Overview Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Madhya Pradesh Groundwater Monitoring Summary</div>',
        unsafe_allow_html=True,
    )

    hero_path = dl.cfg.PROJECT_ROOT / "dashboard" / "assets" / "groundwater_hero.svg"
    if hero_path.exists():
        hero_b64 = base64.b64encode(hero_path.read_bytes()).decode("ascii")
        st.markdown(
            f'<img src="data:image/svg+xml;base64,{hero_b64}" '
            'style="width:100%;height:auto;border-radius:18px;margin:.2rem 0 1rem;" '
            'alt="MP Groundwater Intelligence banner">',
            unsafe_allow_html=True,
        )

    latest = dl.load_latest_readings()
    yearly = dl.load_yearly_summary()
    district = dl.load_district_summary()
    summary = dl.load_phase3_summary()

    # ---- KPI row ----
    c1, c2, c3, c4 = st.columns(4)

    n_stations = latest["station"].nunique() if latest is not None and "station" in latest.columns else "—"
    n_districts = (
        latest["district"].nunique()
        if latest is not None and "district" in latest.columns
        else "—"
    )
    n_obs = summary.get("n_observations", "—") if summary else "—"
    latest_date = summary.get("latest_date", "—") if summary else "—"

    if latest is not None and "datetime" in latest.columns:
        latest_date = str(pd.to_datetime(latest["datetime"]).max().date())

    c1.metric("Monitoring Stations", n_stations)
    c2.metric("Districts Covered", n_districts)
    c3.metric("Total Observations", n_obs if isinstance(n_obs, str) else f"{n_obs:,}")
    c4.metric("Latest Observation", latest_date)

    st.markdown("---")

    # ---- Latest groundwater statistics ----
    if latest is not None and "wl_raw" in latest.columns:
        st.subheader("Latest Groundwater-Level Statistics")
        wl = latest["wl_raw"].dropna()
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Median (m)", f"{wl.median():.2f}")
        k2.metric("Mean (m)", f"{wl.mean():.2f}")
        k3.metric("Min (m)", f"{wl.min():.2f}")
        k4.metric("Max (m)", f"{wl.max():.2f}")

        st.caption(
            "Values are the signed CGWB telemetry readings (metres). "
            "A high proportion of negative values is common in the published data; "
            "the measurement convention should be verified against official CGWB documentation."
        )
    else:
        st.info("Latest station readings file not found. Run Phase 3 analytics first.")

    # ---- Year-wise trend ----
    if yearly is not None and {"year", "wl_mean"}.issubset(yearly.columns):
        st.subheader("Year-wise Mean Groundwater Level")
        agg = yearly.groupby("year", as_index=False)["wl_mean"].mean()
        fig = px.line(
            agg, x="year", y="wl_mean",
            markers=True,
            labels={"wl_mean": "Mean wl_raw (m)", "year": "Year"},
            template="plotly",
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=30, b=40),
            height=360,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Yearly summary not available.")

    # ---- District distribution ----
    if latest is not None and "district" in latest.columns:
        st.subheader("Stations per District")
        counts = latest.groupby("district")["station"].nunique().sort_values(ascending=False).reset_index()
        counts.columns = ["District", "Stations"]
        top_counts = counts.head(20)

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=top_counts["District"],
            y=top_counts["Stations"],
            marker=dict(
                color=top_counts["Stations"],
                colorscale="Teal",
                showscale=True,
                colorbar=dict(title="Stations"),
            ),
            name="Stations",
        ))
        fig2.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=30, b=80),
            height=400,
            xaxis_tickangle=-40,
        )
        st.plotly_chart(fig2, use_container_width=True)
