import base64
from io import BytesIO

import folium
import numpy as np
import streamlit as st
from PIL import Image
from streamlit_folium import st_folium

from rainfall_warning.risk_model import (
    load_artifacts,
    predict_inundation_risk,
    get_imd_alert_level,
)

# Decimates the ~3600x4320 susceptibility grid before drawing it as a map
# overlay, so re-rendering on every slider tick stays responsive. Lower this
# (e.g. 5 or 3) for more visual detail if your machine renders it fast enough;
# raise it (e.g. 10+) if the map feels sluggish.
DOWNSAMPLE_STEP = 8


@st.cache_resource(show_spinner="Loading rainfall model…")
def _load():
    # Model + susceptibility array are static — loading them once and caching
    # across reruns avoids re-reading the .pkl/.npy on every slider tick.
    return load_artifacts()


def _array_to_data_url(rgba_uint8: np.ndarray) -> str:
    img = Image.fromarray(rgba_uint8, mode="RGBA")
    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _build_risk_map(inundation_map: np.ndarray, grid_meta: dict):
    """Colour the inundation-risk raster and drape it over a real OpenStreetMap
    basemap, zoomed to the Periyar Basin model grid (Google Earth isn't usable
    here without a paid Maps API key, so OSM — the alternative you named — is
    what's actually embeddable for free)."""
    import matplotlib.pyplot as plt

    min_lon, min_lat, max_lon, max_lat = grid_meta["bbox"]

    small = inundation_map[::DOWNSAMPLE_STEP, ::DOWNSAMPLE_STEP]
    peak = float(small.max())
    vmax = max(peak, 0.05)  # floor so a near-zero scenario still shows terrain texture

    norm = np.clip(small / vmax, 0.0, 1.0)
    cmap = plt.get_cmap("YlOrRd")
    rgba = cmap(norm)
    rgba[..., 3] = norm * 0.8  # up to 80% opacity at peak risk, transparent at zero
    rgba_uint8 = (np.clip(rgba, 0.0, 1.0) * 255).astype(np.uint8)

    # NOTE: this assumes row 0 of the array is the NORTH edge of the grid —
    # the standard rasterio/GDAL convention, and consistent with how the old
    # matplotlib view rendered it without anyone flagging it as flipped. If
    # this overlay looks upside-down against real Periyar geography, add
    # `rgba_uint8 = np.flipud(rgba_uint8)` right above the line below.
    data_url = _array_to_data_url(rgba_uint8)

    center_lat, center_lon = (min_lat + max_lat) / 2, (min_lon + max_lon) / 2
    m = folium.Map(location=[center_lat, center_lon], tiles="OpenStreetMap", control_scale=True)
    m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])

    folium.Rectangle(
        bounds=[[min_lat, min_lon], [max_lat, max_lon]],
        color="#7dd3fc",
        weight=1,
        fill=False,
        tooltip="Model grid extent",
    ).add_to(m)

    folium.raster_layers.ImageOverlay(
        image=data_url,
        bounds=[[min_lat, min_lon], [max_lat, max_lon]],
        opacity=1.0,  # per-pixel alpha is already baked into the PNG
        interactive=False,
        cross_origin=False,
    ).add_to(m)

    return m, peak


def render_rainfall_tab() -> None:
    st.markdown("#### Rainfall Prediction Engine · Periyar Basin, Kerala")
    st.caption(
        "Trained on 9 years (2015–2023) of real IMD gridded daily rainfall data, fused "
        "with a DEM-derived terrain susceptibility layer. Ministry of Earth Sciences / "
        "IMD problem statement pilot basin."
    )

    model, susceptibility, grid_meta = _load()

    if "periyar_rainfall_mm" not in st.session_state:
        st.session_state.periyar_rainfall_mm = 50.0

    col_ctrl, col_out = st.columns([1, 2], gap="large")

    with col_ctrl:
        st.markdown("**Quick scenarios**")
        # Stacked, not side-by-side columns: col_ctrl is already only ~1/3 of
        # the page, and splitting it into 3 more columns left no room for the
        # button text (hence "Norm...", "Heavy...", "Aug 2..." in testing).
        if st.button("☀️ Normal (5mm)", use_container_width=True):
            st.session_state.periyar_rainfall_mm = 5.0
        if st.button("🌧️ Heavy rain (90mm)", use_container_width=True):
            st.session_state.periyar_rainfall_mm = 90.0
        if st.button("🌊 Aug 2018 flood (260mm)", use_container_width=True):
            st.session_state.periyar_rainfall_mm = 260.0

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        rainfall_mm = st.slider(
            "Simulated rainfall today (mm)",
            min_value=0.0,
            max_value=300.0,  # raised from the original 200.0 so the 260mm preset is reachable
            step=5.0,
            key="periyar_rainfall_mm",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    result = predict_inundation_risk(rainfall_mm, model, susceptibility)
    imd_alert = get_imd_alert_level(rainfall_mm)

    with col_out:
        st.markdown(
            f"""
            <div style="background-color:{imd_alert['color']}; padding:18px; border-radius:10px; text-align:center;">
                <h2 style="color:white; margin:0;">{imd_alert['level']} Alert</h2>
                <p style="color:white; margin:0;">{imd_alert['label']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")
        m1, m2 = st.columns(2)
        m1.metric("ML risk score", f"{result['ml_risk_score']:.3f}")
        m2.metric("Combined rainfall risk", f"{result['rainfall_risk']:.3f}")

        st.markdown("")
        st.markdown("**Inundation risk map**")
        risk_map, peak = _build_risk_map(result["inundation_map"], grid_meta)
        st.caption(
            f"OpenStreetMap basemap, zoomed to the Periyar Basin model grid · "
            f"peak risk this scenario: {peak:.2f}"
        )
        st_folium(
            risk_map,
            height=480,
            use_container_width=True,
            returned_objects=[],
            key=f"periyar-risk-map-{rainfall_mm}",
        )