"""Data Quality and Monitoring page."""

from __future__ import annotations

import streamlit as st
import pandas as pd

from dashboard.utils import data_loader as dl


def render():
    st.markdown('<div class="page-title">Data Quality & Monitoring</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">File presence, coverage and known data-quality flags</div>',
        unsafe_allow_html=True,
    )

    status = dl.file_status()
    st.subheader("Key file status")
    rows = [{"File": k, "Present": "✅" if v else "❌"} for k, v in status.items()]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    summary = dl.load_phase3_summary()
    if summary:
        st.subheader("Phase-3 summary")
        st.json(summary)
    else:
        st.info("Phase-3 summary JSON not found.")

    st.markdown("---")
    st.markdown(
        """
        **Known data-quality practices applied in this project**

        - Duplicate station-timestamp records are resolved with a documented rule (keep first).
        - Extreme magnitude readings are **flagged**, not automatically deleted.
        - Signed groundwater readings are never converted with `abs()`.
        - Target alignment is recalculated after cleaning (`features_clean_v2.parquet`).
        - Missing months in quarterly analysis are left blank, never zero-filled.
        """
    )
