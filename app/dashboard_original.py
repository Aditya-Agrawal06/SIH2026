import requests
import streamlit as st

st.set_page_config(page_title="Heavy Rainfall Early Warning", layout="wide")

st.title("🌧️ Heavy Rainfall Early Warning & Inundation Prediction")
st.caption("Prototype — Periyar Basin, Kerala | Ministry of Earth Sciences / IMD problem statement")

API_URL = "http://127.0.0.1:8000"

rainfall_mm = st.slider("Simulated rainfall today (mm)", min_value=0.0, max_value=200.0, value=50.0, step=5.0)

col1, col2 = st.columns([1, 2])

with col1:
    response = requests.post(f"{API_URL}/predict", json={"rainfall_mm": rainfall_mm})
    result = response.json()

    imd_color = result["imd_alert_color"]
st.markdown(
    f"""
    <div style="background-color:{imd_color}; padding:20px; border-radius:10px; text-align:center;">
        <h2 style="color:white; margin:0;">{result['imd_alert_level']} Alert</h2>
        <p style="color:white; margin:0;">{result['imd_alert_label']}</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.metric("ML Risk Score", f"{result['ml_risk_score']:.3f}")

with col2:
    map_response = requests.get(f"{API_URL}/predict/map", params={"rainfall_mm": rainfall_mm})
    st.image(map_response.content, caption="Inundation Risk Map", use_container_width=True)

st.subheader("Quick Scenarios")
col_a, col_b, col_c = st.columns(3)
with col_a:
    if st.button("☀️ Normal Day (5mm)"):
        st.session_state.rainfall_mm = 5.0
with col_b:
    if st.button("🌧️ Heavy Rain (90mm)"):
        st.session_state.rainfall_mm = 90.0
with col_c:
    if st.button("🌊 Aug 2018 Kerala Flood (>250mm)"):
        st.session_state.rainfall_mm = 260.0

if "rainfall_mm" not in st.session_state:
    st.session_state.rainfall_mm = 50.0


with st.expander("📊 Model Validation (Persistence vs LightGBM)"):
    import pandas as pd
    comparison = pd.DataFrame({
        "Model": ["Persistence (baseline)", "LightGBM"],
        "CSI": [0.273, 0.143],
        "Precision": [0.429, 0.176],
        "Recall": [0.429, 0.429],
    })
    st.dataframe(comparison, use_container_width=True)
    st.caption(
        "Tested on 2022-2023 held-out data (7 heavy-rain events). "
        "Persistence outperforms LightGBM due to limited positive examples "
        "(36 heavy-rain days across 9 years) — the deployed system uses "
        "persistence as the primary alert with LightGBM risk score as a "
        "supporting signal."
    )