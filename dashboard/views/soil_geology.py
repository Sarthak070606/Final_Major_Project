"""Soil and Geological Analysis – placeholder until verified datasets are integrated."""

from __future__ import annotations

import streamlit as st


def render():
    st.markdown('<div class="page-title">Soil and Geological Analysis</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Hydrogeological context for Madhya Pradesh</div>',
        unsafe_allow_html=True,
    )

    st.warning(
        "**Verified soil / geology datasets are not yet integrated.**\n\n"
        "This module will display official data from sources such as:\n"
        "- Central Ground Water Board (CGWB) / NAQUIM\n"
        "- Geological Survey of India (GSI)\n"
        "- Soil and Land Use Survey of India\n"
        "- India-WRIS\n\n"
        "Until those datasets are obtained and spatially joined to stations, "
        "no soil type, lithology or aquifer classification is shown."
    )

    st.info(
        "Do not invent soil or geological values from latitude/longitude alone. "
        "When data becomes available, each record will carry its source, "
        "resolution and last-update date."
    )
