
"""Quarterly / representative-month groundwater analysis."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from dashboard.utils import data_loader as dl


MONTHS = {
    3: "March",
    6: "June",
    9: "September",
    12: "December",
}

MONTH_ORDER = ["March", "June", "September", "December"]


def normalize_month(value):
    """Convert numeric or text month representations to month numbers."""

    if pd.isna(value):
        return None

    text = str(value).strip().lower()

    month_names = {
        "march": 3,
        "mar": 3,
        "june": 6,
        "jun": 6,
        "september": 9,
        "sep": 9,
        "sept": 9,
        "december": 12,
        "dec": 12,
    }

    if text in month_names:
        return month_names[text]

    try:
        number = int(float(text))
        return number if number in MONTHS else None
    except (ValueError, TypeError):
        return None


def render():

    st.markdown(
        '<div class="page-title">Quarterly Groundwater Analysis</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="page-subtitle">'
        'Representative months: March · June · September · December'
        '</div>',
        unsafe_allow_html=True,
    )

    qdf = dl.load_quarterly_summary()

    if qdf is None or qdf.empty:
        st.warning("Representative-month summary is unavailable.")
        st.info(
            "Run Phase 3 analytics to generate "
            "representative_month_summary.csv."
        )
        return

    qdf = qdf.copy()

    # Normalize column names
    qdf.columns = [str(c).strip().lower() for c in qdf.columns]

    # Identify month column
    month_col = next(
        (
            col for col in ["representative_month", "month"]
            if col in qdf.columns
        ),
        None,
    )

    if month_col is None:
        st.error("Month column not found in quarterly summary.")
        st.write("Available columns:", list(qdf.columns))
        return

    # Identify groundwater value column
    value_col = next(
        (
            col for col in [
                "wl_mean",
                "average_wl",
                "mean_wl",
                "wl_raw_mean",
                "avg_wl",
            ]
            if col in qdf.columns
        ),
        None,
    )

    if value_col is None:
        st.error("Groundwater-level column not found.")
        st.write("Available columns:", list(qdf.columns))
        return

    required_columns = {"station", "year"}

    if not required_columns.issubset(qdf.columns):
        st.error("Station or year column is missing.")
        st.write("Available columns:", list(qdf.columns))
        return

    # Normalize month, year and groundwater values
    qdf["month_number"] = qdf[month_col].apply(normalize_month)
    qdf["month_name"] = qdf["month_number"].map(MONTHS)

    qdf["year"] = pd.to_numeric(qdf["year"], errors="coerce")
    qdf[value_col] = pd.to_numeric(qdf[value_col], errors="coerce")

    qdf = qdf.dropna(
        subset=["station", "year", "month_number", value_col]
    ).copy()

    qdf["year"] = qdf["year"].astype(int)
    qdf["station"] = qdf["station"].astype(str)

    if qdf.empty:
        st.warning("No valid quarterly observations found.")
        return

    # District filter
    if "district" in qdf.columns:
        districts = sorted(qdf["district"].dropna().astype(str).unique())

        selected_district = st.selectbox(
            "District",
            ["All"] + districts,
            key="quarterly_district",
        )

        if selected_district != "All":
            qdf = qdf[
                qdf["district"].astype(str) == selected_district
            ]

    if qdf.empty:
        st.info("No observations available for this district.")
        return

    # Station filter
    stations = sorted(qdf["station"].unique())

    selected_station = st.selectbox(
        "Station",
        ["All"] + stations,
        key="quarterly_station",
    )

    if selected_station != "All":
        qdf = qdf[qdf["station"] == selected_station]

    # Year filter
    years = sorted(qdf["year"].unique())

    if not years:
        st.warning("No valid years found.")
        return

    selected_year = st.selectbox(
        "Year",
        years,
        index=len(years) - 1,
        key="quarterly_year",
    )

    plot_df = qdf[qdf["year"] == selected_year].copy()

    if plot_df.empty:
        st.info("No quarterly observations for the selected year.")
        return

    st.caption(
        "Values are averages of available observations in the "
        "representative months. Missing months are not treated as zero."
    )

    # Aggregate across stations when All is selected
    if selected_station == "All":
        chart_df = (
            plot_df.groupby(
                ["month_number", "month_name"],
                as_index=False,
            )[value_col]
            .mean()
        )
    else:
        chart_df = plot_df.copy()

    chart_df = chart_df.sort_values("month_number")

    # Chart
    st.subheader("Quarterly Groundwater Trend")

    fig = px.bar(
        chart_df,
        x="month_name",
        y=value_col,
        category_orders={"month_name": MONTH_ORDER},
        labels={
            "month_name": "Representative month",
            value_col: "Average groundwater level (m)",
        },
        title=f"Groundwater levels - {selected_year}",
        template="plotly_white",
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        xaxis_title="Month",
        yaxis_title="Average groundwater level (m)",
    )

    st.plotly_chart(fig, use_container_width=True)

    # Quarterly table
    st.subheader("Quarterly Readings")

    table_df = (
        plot_df.pivot_table(
            index="year",
            columns="month_name",
            values=value_col,
            aggfunc="mean",
        )
        .reindex(columns=MONTH_ORDER)
    )

    table_df.columns.name = None

    st.dataframe(
        table_df.style.format("{:.3f}", na_rep="Unavailable"),
        use_container_width=True,
    )

    # Station-level records
    if selected_station == "All":
        st.subheader("Station-wise Quarterly Records")
        display_df = plot_df.copy()
    else:
        st.subheader("Selected Station Records")
        display_df = plot_df.copy()

    display_columns = [
        col for col in [
            "station",
            "district",
            "year",
            "month_name",
            value_col,
        ]
        if col in display_df.columns
    ]

    st.dataframe(
        display_df[display_columns].sort_values(
            ["year", "month_name"]
        ),
        use_container_width=True,
        hide_index=True,
    )

    # Download
    st.download_button(
        "Download quarterly data",
        data=plot_df.to_csv(index=False).encode("utf-8"),
        file_name=f"quarterly_groundwater_{selected_year}.csv",
        mime="text/csv",
    )

    st.info(
        "Quarterly values represent available observations in March, "
        "June, September and December. Missing observations remain "
        "unavailable and are never interpreted as zero."
    )

    st.warning(
        "Groundwater level alone cannot establish drinking-water quality, "
        "well yield, drilling depth or well-construction suitability. "
        "These assessments require verified geological, field and "
        "laboratory information."
    )
