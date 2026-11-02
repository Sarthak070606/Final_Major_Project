"""About the Project page."""

from __future__ import annotations

import streamlit as st


def render():
    st.markdown('<div class="page-title">About the Project</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">AI-Enabled Groundwater Monitoring, Prediction and Well Suitability Assessment</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        ### Problem statement
        Groundwater is a critical resource for Madhya Pradesh.  
        This project builds a decision-support system that helps users explore
        CGWB telemetry data, understand historical and seasonal patterns,
        and obtain preliminary forecasts and suitability context.

        ### Objectives
        1. Clean and process CGWB 6-hourly groundwater telemetry for Madhya Pradesh.
        2. Provide transparent data-quality reporting.
        3. Forecast the next groundwater-level observation at existing stations.
        4. Compare historical (2021–2025) and recent (2026) conditions.
        5. Analyse quarterly / seasonal patterns.
        6. Offer a preliminary well-suitability evidence summary (with clear limitations).
        7. Present everything through a professional interactive dashboard.

        ### Data source
        Central Ground Water Board (CGWB) groundwater-level telemetry  
        (India-WRIS / NWIC). Signed readings are preserved exactly as published.

        ### Methodology summary
        - **Phase 1** – Chunked ingestion, cleaning, station-wise feature engineering.
        - **Phase 2** – Chronological splits, multi-model training, honest evaluation.
        - **Phase 3** – Historical, yearly, quarterly and district analytics.
        - **Dashboard** – Streamlit + Plotly interactive application.

        ### Important limitations
        - Soil, geology and laboratory water-quality modules require verified external datasets that are not yet integrated.
        - Predictions are for monitoring support only and do **not** authorise drilling.
        - Measurement convention of signed telemetry values should be verified against official CGWB documentation.
        - Missing data is never fabricated.

        ### Technologies
        Python · Pandas · PyArrow · Scikit-learn · XGBoost / CatBoost / LightGBM (optional)  
        Streamlit · Plotly · FastAPI (backend)

        ### Future scope
        - Integration of official NAQUIM / GSI soil and lithology layers.
        - Laboratory water-quality records.
        - Calibrated prediction intervals.
        - JAL-GPT grounded chatbot.
        - Deployment on Streamlit Cloud / container hosting.
        """
    )
