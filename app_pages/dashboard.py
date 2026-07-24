"""ShiftSync AI – Executive Dashboard page"""

import streamlit as st
from datetime import date
from utils.data import (get_workforce_summary, get_dept_distribution,
                         get_shift_distribution, get_attendance_trend,
                         get_holidays, get_leave_requests)
from utils.charts import (dept_bar_chart, shift_donut, attendance_trend_line,
                           attendance_status_donut)
from components.ui import render_kpi_row, status_badge


def render():
    st.markdown("### ◼ Executive Dashboard")
    st.caption(f"Real-time workforce overview • {date.today().strftime('%B %Y')}")
    st.markdown("---")

    # ── KPI Row ───────────────────────────────────────────────────────────────
    s = get_workforce_summary()
    render_kpi_row([
        ("Total Employees",   s["total"],        "Registered workforce",      "#4f8ef7"),
        ("Present Today",     s["present"],      f"{s['coverage']}% coverage", "#4ade80"),
        ("On Leave",          s["on_leave"],      f"{s['pending_leaves']} pending approvals", "#fbbf24"),
        ("Absent",            s["absent"],        "Unplanned absence",         "#f87171"),
        ("Weekly Off",        s["weekly_off"],    "Scheduled offs today",      "#a78bfa"),
        ("Coverage %",        f"{s['coverage']}%","Workforce active today",   "#2dd4bf"),
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: charts ─────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Department Distribution**")
        dept_df = get_dept_distribution()
        if not dept_df.empty:
            st.plotly_chart(dept_bar_chart(dept_df), use_container_width=True,
                            config={"displayModeBar": False})

    with col2:
        st.markdown("**Shift Distribution**")
        shift_df = get_shift_distribution()
        if not shift_df.empty:
            st.plotly_chart(shift_donut(shift_df), use_container_width=True,
                            config={"displayModeBar": False})

    # ── Row 3: trend + status ─────────────────────────────────────────────────
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**Attendance Trend — Last 30 Days**")
        trend_df = get_attendance_trend(30)
        if not trend_df.empty:
            st.plotly_chart(attendance_trend_line(trend_df), use_container_width=True,
                            config={"displayModeBar": False})
        else:
            st.info("No attendance data yet.")

    with col4:
        st.markdown("**Today's Workforce Status**")
        st.plotly_chart(attendance_status_donut(s), use_container_width=True,
                        config={"displayModeBar": False})

    # ── Row 4: holidays + pending leaves ─────────────────────────────────────
    col5, col6 = st.columns(2)

    with col5:
        st.markdown("**Upcoming Holidays**")
        holidays = get_holidays()
        today_str = date.today().isoformat()
        upcoming = holidays[holidays["holiday_date"] >= today_str].head(6)
        if not upcoming.empty:
            for _, row in upcoming.iterrows():
                color = "#f87171" if row["type"] == "National" else "#fbbf24"
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:12px;'
                    f'padding:8px 12px;background:#1e2435;border-radius:8px;margin-bottom:6px">'
                    f'<div style="color:{color};font-weight:600;font-size:13px;width:80px">'
                    f'{row["holiday_date"]}</div>'
                    f'<div style="color:#e8eaf0;font-size:13px">{row["name"]}</div>'
                    f'<div style="margin-left:auto">'
                    f'<span style="background:#2a3350;color:{color};font-size:10px;'
                    f'padding:2px 8px;border-radius:20px">{row["type"]}</span></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("No upcoming holidays.")

    with col6:
        st.markdown("**Pending Leave Approvals**")
        pending = get_leave_requests(status="Pending")
        if not pending.empty:
            for _, row in pending.head(5).iterrows():
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;'
                    f'padding:8px 12px;background:#1e2435;border-radius:8px;margin-bottom:6px">'
                    f'<div style="flex:1">'
                    f'<div style="color:#e8eaf0;font-size:13px;font-weight:500">{row["employee"]}</div>'
                    f'<div style="color:#9aa3c0;font-size:11px">{row["leave_type"]} • {row["days"]} day(s)</div>'
                    f'</div>'
                    f'<span style="background:#2d2010;color:#fbbf24;font-size:10px;'
                    f'padding:2px 8px;border-radius:20px">Pending</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.success("No pending leave approvals.")