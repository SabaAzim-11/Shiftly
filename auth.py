"""
ShiftSync AI – Authentication & session management
"""

import streamlit as st
from database import get_conn


def login_page():
    st.markdown("""
    <style>
    .login-wrap {
        max-width: 420px; margin: 60px auto; padding: 0 1rem;
    }
    .login-card {
        background: #161b27; border: 1px solid #2a3350;
        border-radius: 16px; padding: 36px 32px;
    }
    .login-logo {
        font-size: 28px; font-weight: 800; text-align: center;
        background: linear-gradient(135deg, #4f8ef7, #2dd4bf);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    .login-sub {
        text-align: center; color: #6b7494; font-size: 13px;
        margin-bottom: 28px;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-logo">⚡ ShiftSync AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Smart Workforce & Shift Management Platform</div>', unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin / hr")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

        if submitted:
            user = authenticate(username, password)
            if user:
                st.session_state["authenticated"] = True
                st.session_state["user"] = dict(user)
                st.session_state["page"] = "dashboard"
                st.rerun()
            else:
                st.error("Invalid username or password")

        st.caption("Demo: admin/admin123 · hr/hr123")


def authenticate(username: str, password: str):
    conn = get_conn()
    user = conn.execute("""
        SELECT u.*, e.name as emp_name, e.emp_id, e.department_id
        FROM users u
        LEFT JOIN employees e ON u.employee_id = e.id
        WHERE u.username=? AND u.password=? AND u.is_active=1
    """, (username, password)).fetchone()
    conn.close()
    return user


def logout():
    for key in ["authenticated", "user", "page"]:
        st.session_state.pop(key, None)
    st.rerun()


def require_auth():
    """Call at top of every page. Returns True if authenticated."""
    return st.session_state.get("authenticated", False)


def current_user():
    return st.session_state.get("user", {})


def is_admin():
    return current_user().get("role") in ("Admin", "HR")