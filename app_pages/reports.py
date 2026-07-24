"""ShiftSync AI – Reports & Exports page"""

import streamlit as st
from datetime import date
from utils.data import (get_employees, get_attendance_monthly,
                         get_leave_requests, get_workforce_summary,
                         get_dept_distribution, get_shift_distribution)
from utils.reports import (generate_excel_report, generate_pdf_report,
                            attendance_excel, employee_excel, leave_excel)


REPORT_CARDS = [
    ("📊", "Attendance Report",    "Daily/monthly attendance summary",    "blue"),
    ("🔄", "Shift Report",         "Shift allocation and coverage data",  "purple"),
    ("🏖", "Leave Report",         "Leave trends by employee and dept",   "amber"),
    ("📈", "Workforce Coverage",   "Real-time and historical coverage",   "green"),
    ("🏢", "Department Summary",   "Dept-wise headcount and status",      "teal"),
    ("💰", "Payroll-Ready Export", "Attendance formatted for payroll",    "red"),
]

COLORS = {
    "blue":   ("#1a2d5a", "#4f8ef7"),
    "purple": ("#1e1540", "#a78bfa"),
    "amber":  ("#2d2010", "#fbbf24"),
    "green":  ("#0d2d1a", "#4ade80"),
    "teal":   ("#0d3330", "#2dd4bf"),
    "red":    ("#2d1010", "#f87171"),
}


def render():
    st.markdown("### 📋 Reports & Exports")
    st.caption("Generate PDF and Excel reports with one click")
    st.markdown("---")

    st.info("ℹ All reports are generated from live database data. "
            "PDF requires `reportlab`, Excel requires `openpyxl`.")

    # ── Report cards grid ─────────────────────────────────────────────────────
    cols = st.columns(3)
    for i, (icon, name, desc, color) in enumerate(REPORT_CARDS):
        bg, tc = COLORS[color]
        with cols[i % 3]:
            st.markdown(
                f'<div style="border:1px solid #2a3350;border-radius:12px;'
                f'padding:18px;margin-bottom:12px;border-top:2px solid {tc}'>
                f'<div style="font-size:26px;margin-bottom:8px">{icon}</div>'
                f'<div style="font-size:14px;font-weight:600;color:#e8eaf0">{name}</div>'
                f'<div style="font-size:11px;color:#6b7494;margin-top:4px">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("---")

    # ── Quick Report Generator ─────────────────────────────────────────────────
    st.markdown("### ⚡ Quick Report Generator")

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        report_type = st.selectbox("Report Type",
                                    ["Attendance","Employee Directory","Leave","Workforce Summary"],
                                    label_visibility="collapsed")
    with col2:
        from_date = st.date_input("From", value=date.today().replace(day=1),
                                   label_visibility="collapsed")
    with col3:
        to_date = st.date_input("To", value=date.today(),
                                 label_visibility="collapsed")
    with col4:
        fmt = st.selectbox("Format", ["Excel (.xlsx)", "PDF (.pdf)"],
                            label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    gen_col, _ = st.columns([1, 3])
    with gen_col:
        generate = st.button("⚡ Generate Report", type="primary", use_container_width=True)

    if generate:
        with st.spinner(f"Generating {report_type} report…"):
            try:
                year  = from_date.year
                month = from_date.month

                if report_type == "Employee Directory":
                    df = get_employees()[["emp_id","name","department","designation",
                                         "shift","weekly_off","employment_type","email","mobile"]]
                    title = "ShiftSync – Employee Directory"

                elif report_type == "Attendance":
                    df = get_attendance_monthly(year, month)
                    title = f"ShiftSync – Attendance Report ({from_date.strftime('%B %Y')})"

                elif report_type == "Leave":
                    df = get_leave_requests()
                    if not df.empty:
                        df = df[["employee","department","leave_type","from_date",
                                 "to_date","days","status","applied_on"]]
                    title = "ShiftSync – Leave Report"

                else:  # Workforce Summary
                    import pandas as pd
                    s = get_workforce_summary()
                    dept = get_dept_distribution()
                    shift = get_shift_distribution()
                    df = pd.DataFrame([
                        {"Metric": "Total Employees",    "Value": s["total"]},
                        {"Metric": "Present Today",      "Value": s["present"]},
                        {"Metric": "Absent Today",       "Value": s["absent"]},
                        {"Metric": "On Leave",           "Value": s["on_leave"]},
                        {"Metric": "Coverage %",         "Value": f"{s['coverage']}%"},
                        {"Metric": "Pending Leaves",     "Value": s["pending_leaves"]},
                    ])
                    title = "ShiftSync – Workforce Summary"

                if df.empty:
                    st.warning("No data found for the selected period.")
                elif "Excel" in fmt:
                    data = generate_excel_report(df, report_type, title)
                    filename = f"shiftsync_{report_type.lower().replace(' ','_')}_{date.today()}.xlsx"
                    st.download_button(
                        f"📥 Download {filename}",
                        data=data,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary",
                        use_container_width=True,
                    )
                    st.success(f"✅ {report_type} report ready! Click above to download.")
                else:
                    data = generate_pdf_report(df, title)
                    filename = f"shiftsync_{report_type.lower().replace(' ','_')}_{date.today()}.pdf"
                    st.download_button(
                        f"📥 Download {filename}",
                        data=data,
                        file_name=filename,
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True,
                    )
                    st.success(f"✅ {report_type} PDF ready! Click above to download.")

            except ImportError as e:
                st.error(f"Missing library: {e}\n\nRun: `pip install openpyxl reportlab`")
            except Exception as e:
                st.error(f"Report generation failed: {e}")

    st.markdown("---")
    st.markdown("**Individual Quick Exports**")
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("📊 Employee List (Excel)", use_container_width=True):
            try:
                df = get_employees()[["emp_id","name","department","designation",
                                      "shift","weekly_off","employment_type"]]
                data = employee_excel(df)
                st.download_button("📥 Download", data=data,
                                   file_name=f"employees_{date.today()}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception as e:
                st.error(str(e))

    with c2:
        if st.button("🏖 Leave Report (Excel)", use_container_width=True):
            try:
                df = get_leave_requests()
                if not df.empty:
                    data = leave_excel(df)
                    st.download_button("📥 Download", data=data,
                                       file_name=f"leaves_{date.today()}.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                else:
                    st.info("No leave data.")
            except Exception as e:
                st.error(str(e))

    with c3:
        if st.button("✅ Attendance (Excel)", use_container_width=True):
            try:
                df = get_attendance_monthly(date.today().year, date.today().month)
                data = attendance_excel(df)
                st.download_button("📥 Download", data=data,
                                   file_name=f"attendance_{date.today().strftime('%Y_%m')}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except Exception as e:
                st.error(str(e))
