"""Professional blue-and-white styling for the MP Groundwater dashboard."""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

:root {
  --navy:#102a43; --blue:#1769aa; --cyan:#16a6b6;
  --ink:#183247; --muted:#627d98; --line:#d9e5ef; --surface:#ffffff;
}
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:#f4f8fc; color:var(--ink); }
.block-container { padding-top:1.7rem; padding-bottom:3rem; max-width:1500px; }
section[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#102a43 0%,#163f5f 100%);
  border-right:1px solid #244e6b;
}
section[data-testid="stSidebar"] * { color:#edf6fc !important; }
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  padding:.48rem .65rem; border-radius:9px; margin:.12rem 0;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
  background:rgba(255,255,255,.12);
}
h1,h2,h3 { color:#15344b !important; font-weight:750 !important; letter-spacing:-.02em; }
p,li { color:#334e68; }
.page-title { font-size:2rem; font-weight:800; color:#123b5d; margin:0 0 .25rem; letter-spacing:-.04em; }
.page-subtitle { color:#627d98; font-size:1rem; margin-bottom:1.45rem; }
div[data-testid="stMetric"] {
  background:#fff; border:1px solid #dbe7f0; border-radius:15px;
  padding:17px 18px; box-shadow:0 5px 18px rgba(16,42,67,.055);
}
div[data-testid="stMetric"] label { color:#627d98 !important; font-weight:600; }
div[data-testid="stMetric"] [data-testid="stMetricValue"] { color:#1769aa !important; font-weight:800 !important; }
div[data-testid="stMetricDelta"] { font-size:.8rem; }
.stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] button {
  border-radius:10px; border:0; background:linear-gradient(100deg,#1769aa,#16a6b6);
  color:#fff; font-weight:700; padding:.55rem 1rem;
}
.stButton > button:hover, .stDownloadButton > button:hover { color:#fff; border:0; filter:brightness(1.06); }
div[data-testid="stAlert"] { border-radius:12px; }
div[data-testid="stExpander"] { background:#fff; border:1px solid #dbe7f0; border-radius:12px; }
.stDataFrame { border:1px solid #dbe7f0; border-radius:12px; overflow:hidden; }
div[data-testid="stTabs"] button { font-weight:650; }
hr { border-color:#dbe7f0; }
.hero-panel {
  background:linear-gradient(115deg,#102a43 0%,#1769aa 58%,#16a6b6 100%);
  color:white; border-radius:20px; padding:25px 28px; margin:.2rem 0 1.3rem;
  box-shadow:0 12px 28px rgba(23,105,170,.16);
}
.hero-panel h2 { color:white !important; margin:0 0 .35rem; }
.hero-panel p { color:#e4f4fb; margin:0; }
.section-kicker { color:#16a6b6; font-size:.76rem; font-weight:800; letter-spacing:.1em; text-transform:uppercase; }
.footer { text-align:center; color:#829ab1; font-size:.8rem; padding:1.4rem 0 .5rem; border-top:1px solid #dbe7f0; margin-top:2rem; }
[data-testid="stPopover"] > button { border-radius:999px !important; }
</style>
"""

def inject_css():
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
