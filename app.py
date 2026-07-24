"""
ShiftSync AI – Main entry point
Run: streamlit run app.py
"""

import streamlit as st

# ── Page config MUST be first Streamlit call ──────────────────────────────────
st.set_page_config(
    page_title="ShiftSync AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from database import init_db
from auth import login_page, logout, require_auth, current_user
from components.ui import inject_css, sidebar_logo

# ── Init DB once ──────────────────────────────────────────────────────────────
init_db()
inject_css()

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not require_auth():
    login_page()
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_logo()
    st.markdown("---")

    user = current_user()
    role = user.get("role", "Employee")

    NAV = [
        ("dashboard",  "◼ Dashboard",          "Overview"),
        ("employees",  "👥 Employees",          "Workforce"),
        ("shifts",     "🔄 Shift Management",   "Workforce"),
        ("weeklyoff",  "📅 Weekly Off",         "Workforce"),
        ("attendance", "✅ Attendance",          "HR"),
        ("leaves",     "🏖 Leave Management",   "HR"),
        ("analytics",  "📊 Analytics",          "Intelligence"),
        ("calendar",   "🗓 My Calendar",        "Intelligence"),
        ("ai",         "🤖 AI Assistant",       "Intelligence"),
        ("reports",    "📋 Reports",            "Intelligence"),
    ]

    if "page" not in st.session_state:
        st.session_state["page"] = "dashboard"

    current_section = None
    for page_key, label, section in NAV:
        if section != current_section:
            st.markdown(
                f'<div style="font-size:10px;color:#6b7494;letter-spacing:.1em;'
                f'text-transform:uppercase;padding:10px 8px 4px">{section}</div>',
                unsafe_allow_html=True
            )
            current_section = section
        active = st.session_state["page"] == page_key
        style = ("background:#1a2d5a;color:#4f8ef7;font-weight:600;"
                 if active else "color:#9aa3c0;")
        if st.button(
            label,
            key=f"nav_{page_key}",
            use_container_width=True,
        ):
            st.session_state["page"] = page_key
            st.rerun()

    st.markdown("---")
    st.markdown(
        f'<div style="padding:4px 8px">'
        f'<div style="font-size:12px;font-weight:500;color:#e8eaf0">'
        f'{user.get("emp_name","Admin")}</div>'
        f'<div style="font-size:11px;color:#6b7494">{role}</div>'
        f'</div>',
        unsafe_allow_html=True
    )
    if st.button("🚪 Logout", use_container_width=True):
        logout()

# ── Route to page ─────────────────────────────────────────────────────────────
page = st.session_state.get("page", "dashboard")

if page == "dashboard":
    from app_pages.dashboard import render
elif page == "employees":
    from app_pages.employees import render
elif page == "shifts":
    from app_pages.shifts import render
elif page == "weeklyoff":
    from app_pages.weeklyoff import render
elif page == "attendance":
    from app_pages.attendance import render
elif page == "leaves":
    from app_pages.leaves import render
elif page == "analytics":
    from app_pages.analytics import render
elif page == "calendar":
    from app_pages.calendar import render
elif page == "ai":
    from app_pages.ai_assistant import render
elif page == "reports":
    from app_pages.reports import render
else:
    from app_pages.dashboard import render

render()