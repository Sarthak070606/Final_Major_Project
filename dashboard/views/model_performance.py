"""Model Performance page."""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from dashboard.utils import data_loader as dl


def render():
    st.markdown('<div class="page-title">Model Performance</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Validation and test metrics for groundwater-level forecasting</div>',
        unsafe_allow_html=True,
    )

    st.info(
        "Metrics below are loaded from saved reports. "
        "They are only valid if Phase 2 training was run on the corrected "
        "`features_clean_v2.parquet` dataset. Do not treat previously quoted "
        "figures as final until they are regenerated."
    )

    comparison = dl.load_model_comparison()
    if comparison is None:
        st.warning(
            "Model comparison CSV not found. "
            "Run Phase 2 training to generate `reports/phase2/model_comparison.csv`."
        )
        return

    st.subheader("Model comparison (sorted by validation MAE)")
    st.dataframe(comparison, use_container_width=True)

    # Bar chart of validation MAE
    mae_col = None
    for c in ["val_mae", "validation_mae", "mae"]:
        if c in comparison.columns:
            mae_col = c
            break
    name_col = "model" if "model" in comparison.columns else comparison.columns[0]

    if mae_col:
        fig = px.bar(
            comparison.sort_values(mae_col),
            x=name_col, y=mae_col,
            template="plotly_white",
            color=mae_col,
            color_continuous_scale="Teal",
            title="Validation MAE by model",
            labels={mae_col: "Validation MAE (m)"},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=400,
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Lower MAE is better. Always compare against the persistence baseline. "
        "R² can be high even when absolute errors remain meaningful for decision support."
    )
