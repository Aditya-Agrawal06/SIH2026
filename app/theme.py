import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap');

            .stApp {
                background: radial-gradient(1200px 600px at 10% -10%, #13233a 0%, #0b1220 42%, #070b14 100%);
                color: #e8eef7;
                font-family: 'IBM Plex Sans', sans-serif;
            }
            header[data-testid="stHeader"] { background: transparent; }
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #101929 0%, #0a111c 100%);
                border-right: 1px solid #1e2d44;
            }
            [data-testid="stSidebar"] * { color: #d7e3f4; }
            .block-container { padding-top: 1.1rem; padding-bottom: 2rem; max-width: 1480px; }

            .cmd-banner {
                background: linear-gradient(90deg, #0f2744 0%, #16365a 48%, #1a2a18 100%);
                border: 1px solid #2b4d78;
                border-left: 6px solid #d4a017;
                border-radius: 10px;
                padding: 16px 20px;
                display: flex;
                justify-content: space-between;
                gap: 16px;
                align-items: center;
            }
            .cmd-kicker {
                font-family: 'IBM Plex Mono', monospace;
                letter-spacing: 0.16em;
                font-size: 11px;
                color: #d4a017;
                margin-bottom: 4px;
            }
            .cmd-title { font-size: 26px; font-weight: 700; margin: 0; color: #f4f8ff; }
            .cmd-sub { margin: 4px 0 0 0; color: #9fb3cc; font-size: 13px; }
            .status-chip {
                background: rgba(34, 197, 94, 0.12);
                border: 1px solid #22c55e;
                color: #86efac;
                padding: 8px 12px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 600;
                white-space: nowrap;
            }
            .status-chip.alert {
                background: rgba(239, 68, 68, 0.14);
                border-color: #ef4444;
                color: #fca5a5;
            }
            .metric-card {
                background: #111b2b;
                border: 1px solid #24354d;
                border-radius: 10px;
                padding: 12px 14px;
            }
            .metric-label {
                font-size: 11px;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: #8aa0bb;
            }
            .metric-value { font-size: 22px; font-weight: 700; color: #f8fbff; margin-top: 4px; }
            .metric-hint { font-size: 12px; color: #7dd3fc; margin-top: 2px; }
            .ticker-wrap {
                overflow: hidden;
                border: 1px solid #2a4060;
                background: #0c1624;
                border-radius: 8px;
                margin-top: 8px;
            }
            .ticker-track {
                display: inline-block;
                white-space: nowrap;
                animation: ticker 18s linear infinite;
                padding: 10px 0;
                color: #fbbf24;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 12px;
            }
            @keyframes ticker {
                0% { transform: translateX(12%); }
                100% { transform: translateX(-70%); }
            }
            .panel {
                background: #101a29;
                border: 1px solid #24354d;
                border-radius: 12px;
                padding: 14px 16px;
            }
            .asset-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid #1d2b40;
                padding: 8px 0;
                font-size: 13px;
            }
            .dot {
                width: 9px; height: 9px; border-radius: 50%; display: inline-block; margin-right: 8px;
            }
            .legend { color: #9fb3cc; font-size: 12px; line-height: 1.6; }
            div[data-testid="stTabs"] button { color: #c5d4e8; }
            div[data-testid="stTabs"] button[aria-selected="true"] { color: #f8fbff; }
            div[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: #7dd3fc !important; }
            .stToggle label p { font-weight: 600; }
            [data-testid="stMetricValue"] { color: #f8fbff; }
        </style>
        """,
        unsafe_allow_html=True,
    )