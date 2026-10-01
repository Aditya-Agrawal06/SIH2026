import pandas as pd
import streamlit as st


def render_whatif_tab() -> None:
    st.markdown("#### Digital Twin · 'What-If' Disaster Simulation")
    st.caption(
        "Heuristic hydrology model driven by rainfall intensity, pump capacity and drain "
        "blockage — powered by DEM slope and municipal drain rules (mock values for the demo)."
    )

    col_ctrl, col_out = st.columns([1, 2], gap="large")

    with col_ctrl:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        sim_rain = st.slider(
            "Predicted rainfall (mm/hr)",
            min_value=0,
            max_value=200,
            step=10,
            key="sim_rain_mm",
            help="Feeds the flood-zone size on the Live Impact Map (Tab 2) whenever radar is armed.",
        )
        sim_pumps = st.slider(
            "Municipal drain pump capacity (%)",
            min_value=0,
            max_value=100,
            value=40,
            step=10,
            key="sim_pump_pct",
        )
        sim_blockage = st.select_slider(
            "Stormwater drain blockage",
            options=["Low (10%)", "Medium (50%)", "Severe (90%)"],
            value="Medium (50%)",
            key="sim_blockage",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    blockage_dict = {"Low (10%)": 0.1, "Medium (50%)": 0.5, "Severe (90%)": 0.9}
    b_factor = blockage_dict[sim_blockage]
    effective_drainage = (sim_pumps / 100.0) * (1.0 - b_factor)
    sim_depth = max(0.0, round((sim_rain / 100.0) * (1.5 - effective_drainage), 2))

    with col_out:
        st.markdown("**Predicted inundation curve · next 6 hours**")
        hours = [f"T+{h}h" for h in range(1, 7)]
        depth_curve = [round(sim_depth * (1 + 0.1 * h - 0.02 * h**2), 2) for h in range(1, 7)]
        chart_data = pd.DataFrame({"Time": hours, "Predicted Water Depth (m)": depth_curve})
        st.area_chart(chart_data.set_index("Time"))

        m1, m2 = st.columns(2)
        m1.metric("Peak predicted depth", f"{max(depth_curve)} m")
        m2.metric("Estimated clearance time", f"{int(max(depth_curve) * 4 + 2)} h")

        if max(depth_curve) > 1.0:
            st.error("ACTION REQUIRED: critical inundation predicted. Deploy NDRF pumps immediately.")
        elif max(depth_curve) > 0.5:
            st.warning("WARNING: moderate waterlogging expected. Issue a traffic diversion advisory.")
        else:
            st.success("LOW RISK: drainage capacity sufficient for this scenario.")

        if sim_rain > 100:
            st.info(
                "Rainfall exceeds 100 mm/hr — switch to Tab 2 with radar armed to see the "
                "flood polygon scale up 1.5× to reflect this forecast."
            )