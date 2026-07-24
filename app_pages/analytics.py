"""ShiftSync AI – Workforce Analytics page"""

import streamlit as st
from utils.data import (get_dept_distribution, get_shift_distribution,
                         get_monthly_attendance_trend, get_leave_balance,
                         get_absenteeism_by_dept, get_weekly_off_distribution,
                         get_workforce_summary, get_leave_types, get_employees)
from utils.charts import (dept_bar_chart, shift_donut, monthly_trend_area,
                           absenteeism_bar, weekly_off_distribution,
                           attendance_status_donut)


def render():
    st.markdown("### 📊 Workforce Analytics")
    st.caption("Interactive charts, trends, and AI-powered insights")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Department Distribution**")
        st.plotly_chart(dept_bar_chart(get_dept_distribution()),
                        use_container_width=True, config={"displayModeBar": False})

    with col2:
        st.markdown("**Shift Distribution**")
        st.plotly_chart(shift_donut(get_shift_distribution()),
                        use_container_width=True, config={"displayModeBar": False})

    st.markdown("**6-Month Workforce Trend**")
    st.plotly_chart(monthly_trend_area(get_monthly_attendance_trend(6)),
                    use_container_width=True, config={"displayModeBar": False})

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**Absenteeism by Department**")
        abs_df = get_absenteeism_by_dept()
        if not abs_df.empty:
            st.plotly_chart(absenteeism_bar(abs_df),
                            use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Insufficient data.")

    with col4:
        st.markdown("**Weekly Off Distribution**")
        st.plotly_chart(weekly_off_distribution(get_weekly_off_distribution()),
                        use_container_width=True, config={"displayModeBar": False})

    # ── AI Insights ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**🤖 AI Workforce Insights**")
    s = get_workforce_summary()
    emp_df = get_employees()

    insights = []
    if s["absent"] > 2:
        insights.append(("⚠️", "amber", f"{s['absent']} employees are absent today — consider temporary reallocation."))
    if s["coverage"] < 80:
        insights.append(("🔴", "red", f"Workforce coverage at {s['coverage']}% — below 80% threshold."))
    if s["pending_leaves"] > 3:
        insights.append(("📋", "amber", f"{s['pending_leaves']} leave requests pending approval."))
    night_count = len(emp_df[emp_df["shift"] == "Night"])
    if night_count < 2:
        insights.append(("🌙", "red", "Night shift has fewer than 2 employees — rotation recommended."))
    if s["coverage"] >= 90:
        insights.append(("✅", "green", f"Excellent coverage at {s['coverage']}% today."))
    if not insights:
        insights.append(("✅", "green", "All workforce metrics look healthy today."))

    COLORS = {"amber":"#2d2010","red":"#2d1010","green":"#0d2d1a","blue":"#1a2d5a"}
    TCOLORS = {"amber":"#fbbf24","red":"#f87171","green":"#4ade80","blue":"#4f8ef7"}
    for icon, color, msg in insights:
        st.markdown(
            f'<div style="background:{COLORS[color]};border:1px solid {TCOLORS[color]}33;'
            f'border-radius:8px;padding:10px 14px;margin-bottom:8px;color:{TCOLORS[color]};font-size:13px">'
            f'{icon} {msg}</div>',
            unsafe_allow_html=True
        )

    st.caption("Powered by ShiftSync AI Engine • Updated in real-time")