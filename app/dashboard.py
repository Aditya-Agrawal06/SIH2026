import streamlit as st

from theme import inject_styles
from rainfall_tab import render_rainfall_tab
from live_map_tab import sidebar_roi, render_live_map_tab
from cctv_sensor import render_cctv_tab
from whatif_tab import render_whatif_tab


def main() -> None:
    st.set_page_config(
        page_title="Rainfall & Inundation Early Warning",
        page_icon="🛰️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()

    if "radar_toggle" not in st.session_state:
        st.session_state.radar_toggle = False
    if "sim_rain_mm" not in st.session_state:
        st.session_state.sim_rain_mm = 110

    if st.sidebar.button("🚨 Trigger Flood Alert (Demo)", use_container_width=True, type="primary"):
        st.session_state.radar_toggle = True
    if st.sidebar.button("🟢 Clear Alert (Demo)", use_container_width=True):
        st.session_state.radar_toggle = False
    st.sidebar.markdown("---")

    radar_on = st.session_state.radar_toggle
    chip_class = "status-chip alert" if radar_on else "status-chip"
    chip_text = "IMPACT SCENARIO ARMED" if radar_on else "SYSTEM NOMINAL · WATCH"

    st.markdown(
        f"""
        <div class="cmd-banner">
            <div>
                <div class="cmd-kicker">SIH 2026 · AI/ML HEAVY RAINFALL EARLY WARNING AND INUNDATION PREDICTION</div>
                <p class="cmd-title">Rainfall and Inundation Early Warning System</p>
                <p class="cmd-sub">Real ML rainfall prediction (Periyar Basin, Kerala) + downstream impact demo (Andheri Subway, Mumbai)</p>
            </div>
            <div class="{chip_class}">{chip_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")

    sidebar_roi(radar_on)

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Tab 1 · Rainfall Prediction Engine",
            "Tab 2 · Live Impact Map",
            "Tab 3 · CCTV Virtual Sensor",
            "Tab 4 · What-If Sim",
        ]
    )

    with tab1:
        render_rainfall_tab()

    with tab2:
        st.markdown("#### Sensor ingest")
        radar_on = st.toggle(
            "Ingest Real-Time Radar Data",
            help="Simulates IMD/NDEM radar fusion over the Andheri subway bowl.",
            key="radar_toggle",
        )
        sim_rain = st.session_state.get("sim_rain_mm", 0)
        scale_factor = 1.5 if (radar_on and sim_rain > 100) else 1.0
        render_live_map_tab(radar_on, scale_factor)

    with tab3:
        render_cctv_tab()

    with tab4:
        render_whatif_tab()


if __name__ == "__main__":
    main()