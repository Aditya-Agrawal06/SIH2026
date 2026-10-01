import copy

import folium
import streamlit as st
from streamlit_folium import st_folium

ANDHERI_LAT = 19.1136
ANDHERI_LON = 72.8697

# GeoJSON polygon around Andheri Subway (lon, lat)
FLOOD_POLYGON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "name": "Andheri Subway Inundation Zone",
                "hazard": "urban_flood",
                "agency": "BMC Disaster Management Cell",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [72.8676, 19.1154],
                        [72.8692, 19.1158],
                        [72.8714, 19.1151],
                        [72.8719, 19.1138],
                        [72.8716, 19.1123],
                        [72.8698, 19.1118],
                        [72.8679, 19.1124],
                        [72.8674, 19.1139],
                        [72.8676, 19.1154],
                    ]
                ],
            },
        }
    ],
}

TRANSFORMERS = [
    {
        "id": "TX-AND-01",
        "name": "Andheri East Grid – TX-01",
        "lat": 19.1149,
        "lon": 72.8682,
        "fails_on_radar": False,
    },
    {
        "id": "TX-AND-07",
        "name": "Subway Feeder – TX-07",
        "lat": 19.1134,
        "lon": 72.8711,
        "fails_on_radar": True,
    },
    {
        "id": "TX-AND-12",
        "name": "Western Line Tie – TX-12",
        "lat": 19.1122,
        "lon": 72.8691,
        "fails_on_radar": True,
    },
]


def flood_style(radar_on: bool):
    fill = "#ef4444" if radar_on else "#ef4444"
    return lambda _feature: {
        "fillColor": fill,
        "color": "#fca5a5" if radar_on else "#ef4444",
        "weight": 2 if radar_on else 0,
        "fillOpacity": 0.42 if radar_on else 0.0,
        "opacity": 0.95 if radar_on else 0.0,
        "dashArray": "4, 6" if radar_on else None,
    }


def scale_ring(ring, factor: float):
    """Scale a closed [lon, lat] ring outward/inward around its own centroid."""
    if factor == 1.0:
        return ring
    pts = ring[:-1] if ring[0] == ring[-1] else ring
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return [[cx + (lon - cx) * factor, cy + (lat - cy) * factor] for lon, lat in ring]


def get_flood_polygon(scale_factor: float = 1.0) -> dict:
    """Return the base flood polygon, optionally scaled (Digital Twin linkage from Tab 3)."""
    if scale_factor == 1.0:
        return FLOOD_POLYGON
    poly = copy.deepcopy(FLOOD_POLYGON)
    ring = poly["features"][0]["geometry"]["coordinates"][0]
    poly["features"][0]["geometry"]["coordinates"][0] = scale_ring(ring, scale_factor)
    return poly


def build_map(radar_on: bool, scale_factor: float = 1.0) -> folium.Map:
    m = folium.Map(
        location=[ANDHERI_LAT, ANDHERI_LON],
        zoom_start=15,
        tiles=None,
        control_scale=True,
    )
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Esri, HERE, Garmin, FAO, NOAA, USGS",
        name="Dark Gray",
        control=False,
    ).add_to(m)

    folium.Marker(
        [ANDHERI_LAT, ANDHERI_LON],
        tooltip="Andheri Subway — Priority Asset",
        popup=folium.Popup(
            "<b>Andheri Subway</b><br/>BMC critical underpass<br/>Lat 19.1136 · Lon 72.8697",
            max_width=260,
        ),
        icon=folium.Icon(color="cadetblue", icon="info-sign"),
    ).add_to(m)

    folium.GeoJson(
        get_flood_polygon(scale_factor),
        name="Flood inundation zone",
        style_function=flood_style(radar_on),
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "hazard"],
            aliases=["Zone", "Hazard"],
        ),
    ).add_to(m)

    for tx in TRANSFORMERS:
        offline = radar_on and tx["fails_on_radar"]
        color = "red" if offline else "green"
        popup_html = (
            "<b>OFFLINE: Flood Inundation</b><br/>"
            f"{tx['name']}<br/>Asset ID: {tx['id']}<br/>"
            "Status: Cascading failure — isolate feeder"
            if offline
            else f"<b>ONLINE</b><br/>{tx['name']}<br/>Asset ID: {tx['id']}<br/>Load: Nominal"
        )
        folium.Marker(
            [tx["lat"], tx["lon"]],
            tooltip=f"Electrical Transformer · {tx['id']}",
            popup=folium.Popup(popup_html, max_width=280),
            icon=folium.Icon(color=color, icon="flash"),
        ).add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)
    return m


def sidebar_roi(radar_on: bool) -> None:
    st.sidebar.markdown("### Command Context")
    st.sidebar.caption("Mumbai Suburban · Ward K-East · Andheri Subway corridor")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ROI Ticker")
    st.sidebar.caption("Reflects the Andheri Subway impact scenario (Tab 2) · mock 6-hour window")

    if radar_on:
        avoided_loss = "₹18.4 Cr"
        response_roi = "4.7×"
        ticker = (
            "LIVE RADAR  ·  2 feeders offline  ·  Early-warning ROI 4.7×  ·  "
            "Avoided commercial downtime ₹18.4 Cr  ·  EMS reroute saved 11 min  ·  "
            "NDRF staging cost avoided ₹62 L  ·  "
        )
        delta_loss = "+₹6.1 Cr protected"
        delta_roi = "+1.2× vs baseline"
    else:
        avoided_loss = "₹12.3 Cr"
        response_roi = "3.5×"
        ticker = (
            "WATCH MODE  ·  All transformers online  ·  Baseline ROI 3.5×  ·  "
            "Preparedness spend ₹3.5 Cr  ·  Insured exposure ₹42 Cr  ·  "
            "Subway traffic 86k PPH  ·  "
        )
        delta_loss = "steady"
        delta_roi = "watch"

    st.sidebar.metric("Avoided economic loss", avoided_loss, delta_loss)
    st.sidebar.metric("Emergency response ROI", response_roi, delta_roi)
    st.sidebar.metric("Population in buffer", "41,200", "K-East + metro catchment")

    st.sidebar.markdown(
        f"""
        <div class="ticker-wrap">
            <div class="ticker-track">{ticker * 2}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("")
    st.sidebar.info(
        "ROI updates when radar ingest is armed. Figures are demonstration values for SIH 2026."
    )


def render_live_map_tab(radar_on: bool, scale_factor: float = 1.0) -> None:
    st.markdown("")
    left, right = st.columns([2.35, 1], gap="large")

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("**Live Impact Map · Andheri Subway**")
        st.caption(
            "Dark basemap · flood GeoJSON overlay · electrical transformer assets (mock telemetry)"
        )
        if scale_factor > 1.0:
            st.caption(
                f"🔺 Digital Twin forecast (Tab 4) is scaling the flood zone {scale_factor:.1f}× "
                "— predicted rainfall exceeds 100 mm/hr."
            )
        fmap = build_map(radar_on, scale_factor)
        st_folium(
            fmap,
            height=560,
            use_container_width=True,
            returned_objects=[],
            key=f"impact-map-{'radar' if radar_on else 'watch'}-{scale_factor}",
        )
        st.markdown(
            """
            <div class="legend">
                <span class="dot" style="background:#22c55e"></span> Transformer online &nbsp;&nbsp;
                <span class="dot" style="background:#ef4444"></span> Transformer offline &nbsp;&nbsp;
                <span class="dot" style="background:#38bdf8"></span> Priority underpass &nbsp;&nbsp;
                <span class="dot" style="background:#ef4444;opacity:.45"></span> Inundation polygon (radar)
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        if radar_on:
            st.warning("Alert: 2 Transformers compromised. Rerouting emergency services.")
            st.markdown(
                """
                <div class="metric-card">
                    <div class="metric-label">Inundation status</div>
                    <div class="metric-value">HIGH WATER</div>
                    <div class="metric-hint">Radar-derived depth proxy · subway bowl</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("")
            failed = [tx for tx in TRANSFORMERS if tx["fails_on_radar"]]
            healthy = [tx for tx in TRANSFORMERS if not tx["fails_on_radar"]]
            st.markdown("**Grid cascade (simulated)**")
            for tx in failed:
                st.markdown(
                    f'<div class="asset-row"><span><span class="dot" style="background:#ef4444"></span>{tx["id"]}</span><b style="color:#fca5a5">OFFLINE</b></div>',
                    unsafe_allow_html=True,
                )
            for tx in healthy:
                st.markdown(
                    f'<div class="asset-row"><span><span class="dot" style="background:#22c55e"></span>{tx["id"]}</span><b style="color:#86efac">ONLINE</b></div>',
                    unsafe_allow_html=True,
                )
            st.markdown("")
            st.markdown(
                """
                <div class="panel">
                    <div class="metric-label">Dispatch action</div>
                    <p style="margin:8px 0 0 0;font-size:13px;color:#d7e3f4;">
                        Reroute BEST / EMS via SV Road and WEH. Isolate TX-07 and TX-12.
                        Keep TX-01 as islanded feed for subway pumps.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.success("Watch mode: inundation overlay hidden. All three transformers online.")
            st.markdown(
                """
                <div class="metric-card">
                    <div class="metric-label">Inundation status</div>
                    <div class="metric-value">CLEAR</div>
                    <div class="metric-hint">Polygon loaded · fill opacity 0</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("")
            st.markdown("**Electrical transformers**")
            for tx in TRANSFORMERS:
                st.markdown(
                    f'<div class="asset-row"><span><span class="dot" style="background:#22c55e"></span>{tx["id"]}</span><b style="color:#86efac">ONLINE</b></div>',
                    unsafe_allow_html=True,
                )
            st.caption("Arm radar ingest to simulate cascading flood impact on the grid.")