"""
ShiftSync AI – Shared UI components & custom CSS
"""

import streamlit as st
import pandas as pd


# ── Global CSS ────────────────────────────────────────────────────────────────
DARK_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── Page background ── */
.stApp { background: #0f1117; color: #e8eaf0; }
[data-testid="stSidebar"] { border-right: 1px solid #2a3350; }
[data-testid="stSidebar"] * { color: #9aa3c0 !important; }

/* ── Main content ── */
.block-container { padding: 1.5rem 2rem !important; max-width: 1400px; }

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #161b27; border: 1px solid #2a3350;
    border-radius: 12px; padding: 14px 18px;
}
[data-testid="stMetricLabel"] { font-size: 11px !important; color: #6b7494 !important;
    text-transform: uppercase; letter-spacing: .07em; }
[data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 700 !important; color: #4f8ef7 !important; }
[data-testid="stMetricDelta"] { font-size: 12px !important; }

/* ── Dataframes ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

[data-testid="stDataFrame"] th, .stDataFrame th {
    color: #4f8ef7 !important;
    background: #141827 !important;
}
[data-testid="stDataFrame"] td, .stDataFrame td {
    color: #e8eaf0 !important;
    # background: #161b27 !important;
}
# .dvn-scroller { background: #161b27 !important; }

/* ── Buttons ── */
.stButton>button {
    background: #1e2435 !important; color: #9aa3c0 !important;
    border: 1px solid #2a3350 !important; border-radius: 8px !important;
    font-weight: 500 !important; transition: all .15s !important;
}
.stButton>button:hover { background: #252d3f !important; color: #e8eaf0 !important; }
.stButton>button[kind="primary"] {
    background: #4f8ef7 !important; color: #fff !important;
    border-color: #4f8ef7 !important;
}
.stButton>button[kind="primary"]:hover { background: #3370e0 !important; }

/* ── Inputs ── */
.stTextInput>div>div>input, .stSelectbox>div>div,
.stTextArea>div>div>textarea, .stDateInput>div>div>input {
    background: #1e2435 !important; color: #e8eaf0 !important;
    border: 1px solid #2a3350 !important; border-radius: 8px !important;
}
.stSelectbox [data-baseweb="select"] { background: #1e2435 !important; }
.stSelectbox [data-baseweb="popover"] { background: #1e2435 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #1e2435; border-radius: 10px; padding: 3px; gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: #9aa3c0 !important;
    border-radius: 8px !important; font-size: 13px !important;
}
.stTabs [aria-selected="true"] {
     color: #e8eaf0 !important;
}
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── Expander ── */
.streamlit-expanderHeader {
     border: 1px solid #2a3350 !important;
    border-radius: 10px !important; color: #e8eaf0 !important;
}
.streamlit-expanderContent {
     border: 1px solid #2a3350 !important;
    border-top: none !important;
}

/* ── Alerts ── */
.stAlert { border-radius: 10px !important; }
[data-testid="stAlert"] { background: #1a2d5a !important; color: #4f8ef7 !important; }

/* ── Sidebar nav ── */
.sidebar-nav-item {
    display: flex; align-items: center; gap: 10px; padding: 9px 12px;
    border-radius: 8px; cursor: pointer; color: #9aa3c0;
    font-size: 14px; margin-bottom: 2px; transition: all .15s;
    text-decoration: none;
}
.sidebar-nav-item:hover { background: #1e2435; color: #e8eaf0; }
.sidebar-nav-item.active {
    background: #1a2d5a; color: #4f8ef7; font-weight: 600;
}

/* ── KPI badge ── */
.kpi-badge {
    display: inline-flex; align-items: center; padding: 3px 10px;
    border-radius: 20px; font-size: 11px; font-weight: 600;
}
.badge-blue   { background: #1a2d5a; color: #4f8ef7; }
.badge-green  { background: #0d2d1a; color: #4ade80; }
.badge-amber  { background: #2d2010; color: #fbbf24; }
.badge-red    { background: #2d1010; color: #f87171; }
.badge-purple { background: #1e1540; color: #a78bfa; }
.badge-teal   { background: #0d3330; color: #2dd4bf; }
.badge-gray   { background: #252d3f; color: #9aa3c0; }

/* ── Progress bar ── */
.ss-progress {
    height: 4px; background: #252d3f; border-radius: 2px; overflow: hidden;
}
.ss-progress-fill { height: 100%; border-radius: 2px; }

/* ── Card ── */
.ss-card {
    background: #161b27; border: 1px solid #2a3350;
    border-radius: 14px; padding: 20px;
}

/* ── Chat ── */
.chat-bubble-ai {
    background: #1e2435; border-radius: 4px 12px 12px 12px;
    padding: 10px 14px; font-size: 13px; line-height: 1.6;
    color: #e8eaf0; max-width: 75%; margin-bottom: 12px;
}
.chat-bubble-user {
    background: #4f8ef7; border-radius: 12px 4px 12px 12px;
    padding: 10px 14px; font-size: 13px; line-height: 1.6;
    color: #fff; max-width: 75%; margin-left: auto; margin-bottom: 12px;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2a3350; border-radius: 4px; }

/* ── Divider ── */
hr { border-color: #2a3350 !important; }

/* ── Form labels ── */
.stForm label, label { color: #9aa3c0 !important; font-size: 13px !important; }

/* ── Plotly charts dark bg ── */
.js-plotly-plot .plotly { background: transparent !important; }

/* ── Success/error messages ── */
.stSuccess { background: #0d2d1a !important; color: #4ade80 !important; border-radius: 8px !important; }
.stError   { background: #2d1010 !important; color: #f87171 !important; border-radius: 8px !important; }
.stWarning { background: #2d2010 !important; color: #fbbf24 !important; border-radius: 8px !important; }
.stInfo    { background: #1a2d5a !important; color: #4f8ef7 !important; border-radius: 8px !important; }

/* ── Number input ── */
[data-testid="stNumberInput"] input {
    background: #1e2435 !important; color: #e8eaf0 !important;
    border: 1px solid #2a3350 !important; border-radius: 8px !important;
}
</style>
"""


def inject_css():
    st.markdown(DARK_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", action_label: str = None):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"### {title}")
        if subtitle:
            st.caption(subtitle)
    if action_label:
        with col2:
            return st.button(action_label, type="primary", use_container_width=True)
    return False


def badge(text: str, color: str = "blue") -> str:
    return f'<span class="kpi-badge badge-{color}">{text}</span>'


def status_badge(status: str) -> str:
    color_map = {
        "Present":    "green",
        "Absent":     "red",
        "Leave":      "amber",
        "Weekly Off": "purple",
        "Holiday":    "blue",
        "Late":       "amber",
        "Half Day":   "teal",
        "WFH":        "teal",
        "Approved":   "green",
        "Rejected":   "red",
        "Pending":    "amber",
        "Active":     "green",
        "Inactive":   "red",
        "General":    "blue",
        "A":          "amber",
        "B":          "purple",
        "Morning":    "amber",
        "Evening":    "purple",
        "Night":      "gray",
    }
    color = color_map.get(status, "gray")
    return badge(status, color)


def progress_bar(value: int, max_val: int = 100, color: str = "#4f8ef7") -> str:
    pct = min(100, int(value / max_val * 100)) if max_val else 0
    return f"""
    <div class="ss-progress">
        <div class="ss-progress-fill" style="width:{pct}%;background:{color}"></div>
    </div>"""


def metric_card(label: str, value, delta: str = None, color: str = "#4f8ef7"):
    delta_html = f'<div style="font-size:11px;color:#6b7494;margin-top:4px">{delta}</div>' if delta else ""
    return f"""
    <div style="background:#161b27;border:1px solid #2a3350;border-radius:12px;
                padding:16px;border-top:2px solid {color}">
        <div style="font-size:11px;color:#6b7494;text-transform:uppercase;
                    letter-spacing:.07em;margin-bottom:8px">{label}</div>
        <div style="font-size:28px;font-weight:700;color:{color};line-height:1">{value}</div>
        {delta_html}
    </div>"""


def render_kpi_row(metrics: list):
    """metrics = [(label, value, delta, color), ...]"""
    cols = st.columns(len(metrics))
    for col, (label, value, delta, color) in zip(cols, metrics):
        with col:
            st.markdown(metric_card(label, value, delta, color), unsafe_allow_html=True)


def dataframe_config():
    return {
        "use_container_width": True,
        "hide_index": True,
    }


def confirm_dialog(key: str, message: str) -> bool:
    if st.session_state.get(f"confirm_{key}"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✓ Confirm", key=f"yes_{key}", type="primary"):
                st.session_state[f"confirm_{key}"] = False
                return True
        with col2:
            if st.button("✗ Cancel", key=f"no_{key}"):
                st.session_state[f"confirm_{key}"] = False
        return False
    return False


def sidebar_logo():
    st.markdown("""
    <div style="padding:20px 16px 12px">
        <div style="font-size:22px;font-weight:800;background:linear-gradient(135deg,#4f8ef7,#2dd4bf);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent">
            ⚡ ShiftSync AI
        </div>
        <div style="font-size:10px;color:#6b7494;letter-spacing:.1em;text-transform:uppercase;
                    margin-top:2px">Smart Workforce Platform</div>
    </div>
    """, unsafe_allow_html=True)