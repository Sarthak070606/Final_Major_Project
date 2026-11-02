"""Historical (2021–2025) vs Recent (2026) comparison."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from dashboard.utils import data_loader as dl


def render():
    st.markdown('<div class="page-title">Historical vs Recent Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Compare 2021–2025 averages with available 2026 observations</div>',
        unsafe_allow_html=True,
    )

    yearly = dl.load_yearly_summary()
    latest = dl.load_latest_readings()

    if yearly is None:
        st.warning(
            "Yearly station summary not found. "
            "Run Phase 3 analytics to generate `yearly_station_summary.csv`."
        )
        return

    # Build historical (2021-2025) and recent (2026) averages per station
    if "year" not in yearly.columns or "wl_mean" not in yearly.columns:
        st.error("Yearly summary is missing required columns (`year`, `wl_mean`).")
        return

    hist = yearly[yearly["year"].between(2021, 2025)]
    recent = yearly[yearly["year"] == 2026]

    hist_avg = (
        hist.groupby("station", as_index=False)
        .agg(hist_mean=("wl_mean", "mean"), hist_n=("wl_mean", "count"),
             district=("district", "first") if "district" in hist.columns else ("station", "first"))
    )
    recent_avg = (
        recent.groupby("station", as_index=False)
        .agg(recent_mean=("wl_mean", "mean"), recent_n=("wl_mean", "count"))
    )

    merged = hist_avg.merge(recent_avg, on="station", how="outer")
    merged["abs_variation"] = merged["recent_mean"] - merged["hist_mean"]
    # Safe percentage variation
    merged["pct_variation"] = merged.apply(
        lambda r: (
            (r["abs_variation"] / abs(r["hist_mean"]) * 100)
            if pd.notna(r["hist_mean"]) and abs(r["hist_mean"]) > 1e-6
            else None
        ),
        axis=1,
    )

    st.info(
        "Historical period = 2021–2025 (based on available records). "
        "Recent period = 2026 (only stations with 2026 observations). "
        "Averages use the mean of yearly station means. "
        "Signed CGWB telemetry values are used as-is; interpretation of "
        "‘improvement’ or ‘decline’ depends on the official measurement convention."
    )

    # Filters
    if "district" in merged.columns:
        districts = sorted(merged["district"].dropna().unique())
        sel = st.multiselect("Filter districts", districts, default=districts[:5] if len(districts) > 5 else districts)
        if sel:
            merged = merged[merged["district"].isin(sel)]

    # KPI
    both = merged.dropna(subset=["hist_mean", "recent_mean"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Stations with both periods", len(both))
    c2.metric("Median abs. variation (m)", f"{both['abs_variation'].median():.3f}" if len(both) else "—")
    c3.metric("Median % variation", f"{both['pct_variation'].median():.1f}%" if len(both) and both["pct_variation"].notna().any() else "—")

    # Chart
    if not both.empty:
        fig = px.scatter(
            both,
            x="hist_mean",
            y="recent_mean",
            hover_data=["station", "abs_variation", "pct_variation"],
            labels={"hist_mean": "Historical mean (2021–2025)", "recent_mean": "Recent mean (2026)"},
            template="plotly_white",
            title="Historical vs Recent Mean Groundwater Level",
        )
        # 1:1 line
        lims = [
            min(both["hist_mean"].min(), both["recent_mean"].min()),
            max(both["hist_mean"].max(), both["recent_mean"].max()),
        ]
        fig.add_shape(
            type="line", x0=lims[0], y0=lims[0], x1=lims[1], y1=lims[1],
            line=dict(color="#64748b", dash="dash"),
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Comparison table")
    show = merged.sort_values("abs_variation", key=lambda s: s.abs(), ascending=False)
    st.dataframe(show.reset_index(drop=True), use_container_width=True)

    csv = show.to_csv(index=False).encode("utf-8")
    st.download_button("Download comparison CSV", csv, "historical_vs_recent.csv", "text/csv")
