"""AI Groundwater Prediction page."""

import streamlit as st
import pandas as pd
import requests
from urllib.parse import quote

from dashboard.utils import data_loader as dl
from dashboard.utils import config as cfg


def render():
    st.markdown(
        '<div class="page-title">AI Groundwater Prediction</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="page-subtitle">Prediction of the next available observation</div>',
        unsafe_allow_html=True
    )

    st.info(
        "Forecast horizon: next available observation. "
        "It is not guaranteed to be exactly six hours ahead."
    )

    latest = dl.load_latest_readings()

    if latest is None or latest.empty:
        st.warning("Latest station readings are unavailable.")
        return

    stations = sorted(latest["station"].dropna().astype(str).unique())

    if not stations:
        st.warning("No stations available.")
        return

    station = st.selectbox("Select monitoring station", stations)
    row = latest[latest["station"].astype(str) == station].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Latest groundwater reading", f"{row['wl_raw']:.3f} m")
    c2.metric("District", str(row.get("district", "Unavailable")))
    c3.metric("Observation date", str(row.get("datetime", "Unavailable")))

    if st.button("Run prediction", type="primary"):
        result = None

        try:
            url = f"{cfg.API_BASE}/api/predict/{quote(station, safe='')}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            result = response.json()
        except requests.RequestException as exc:
            st.warning(f"Prediction API unavailable: {exc}")

        if result is not None:
            st.success("Prediction received from the trained backend.")

            predicted = result.get("predicted_next_available_observation")
            if predicted is not None:
                st.metric("Predicted next observation", f"{predicted:.3f} m")

            st.write("**Prediction method:**", result.get("prediction_method", "Unavailable"))
            st.write("**Last observed value:**", result.get("last_observed_level", "Unavailable"))
            st.write("**Last observation time:**", result.get("last_observation_time", "Unavailable"))
            st.caption(result.get("forecast_horizon", "Horizon unavailable"))
            st.warning(result.get("warning", "Prediction is not a measured reading."))
            st.json(result)

        else:
            st.warning("Showing persistence baseline only; the trained API prediction was not obtained.")
            st.metric("Persistence estimate", f"{float(row['wl_raw']):.3f} m")
            st.caption(
                "This estimate assumes the next value equals the latest reading. "
                "It is not a Random Forest prediction."
            )

    st.markdown("---")
    st.caption(
        "Predictions support monitoring and research. They do not establish "
        "drinking-water safety or authorise well drilling."
    )
