"""ShiftSync AI – Attendance page"""

import streamlit as st
from datetime import date
import pandas as pd
from utils.data import (get_attendance_today, mark_attendance,
                         get_attendance_monthly, get_attendance_trend)
from utils.charts import attendance_trend_line, monthly_trend_area
from utils.data import get_monthly_attendance_trend


def render():
    st.markdown("### ✅ Attendance Management")
    st.caption("Daily tracking, monthly summary, and analytics")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📋 Daily Attendance", "📊 Monthly Summary", "📈 Trends"])

    # ── Daily ─────────────────────────────────────────────────────────────────
    with tab1:
        today = date.today()
        att_date = st.date_input("Date", value=today)
        df = get_attendance_today()

        c1, c2, c3, c4 = st.columns(4)
        for col, (label, status, color) in zip(
            [c1, c2, c3, c4],
            [("Present","Present","#4ade80"),("Absent","Absent","#f87171"),
             ("On Leave","Leave","#fbbf24"),("Weekly Off","Weekly Off","#a78bfa")]
        ):
            cnt = len(df[df["status"]==status])
            with col:
                st.markdown(
                    f'<div style="background:#161b27;border:1px solid #2a3350;border-radius:10px;'
                    f'padding:12px;border-top:2px solid {color}"><div style="font-size:10px;'
                    f'color:#6b7494;text-transform:uppercase">{label}</div>'
                    f'<div style="font-size:24px;font-weight:700;color:{color}">{cnt}</div></div>',
                    unsafe_allow_html=True
                )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Mark / Update Attendance**")

        dept_filter = st.selectbox(
            "Filter by Department",
            ["All"] + sorted(df["department"].unique().tolist()),
            label_visibility="collapsed"
        )
        view_df = df if dept_filter == "All" else df[df["department"] == dept_filter]

        STATUS_OPTIONS = ["Present", "Absent", "Leave", "Late", "Half Day", "Weekly Off", "Holiday"]

        with st.form("bulk_attendance"):
            edited = st.data_editor(
                view_df[["emp_id","name","department","shift","status","in_time","out_time"]].rename(
                    columns={"emp_id":"ID","name":"Name","department":"Dept",
                             "shift":"Shift","in_time":"In Time","out_time":"Out Time"}
                ),
                column_config={
                    "status": st.column_config.SelectboxColumn(
                        "Status", options=STATUS_OPTIONS, required=True
                    ),
                    "In Time": st.column_config.TextColumn("In Time"),
                    "Out Time": st.column_config.TextColumn("Out Time"),
                },
                use_container_width=True,
                hide_index=True,
                num_rows="fixed",
            )
            if st.form_submit_button("💾 Save Attendance", type="primary"):
                saved = 0
                for i, row in edited.iterrows():
                    try:
                        orig_row = view_df.iloc[i]
                        mark_attendance(
                            int(orig_row["emp_db_id"]),
                            att_date.isoformat(),
                            row["status"],
                            row.get("In Time",""),
                            row.get("Out Time",""),
                        )
                        saved += 1
                    except Exception:
                        pass
                st.success(f"✅ Attendance saved for {saved} employees.")
                st.rerun()

    # ── Monthly ───────────────────────────────────────────────────────────────
    with tab2:
        col_y, col_m = st.columns(2)
        with col_y:
            year  = st.selectbox("Year",  [2025, 2024, 2023], index=0)
        with col_m:
            month = st.selectbox("Month", list(range(1, 13)),
                                  format_func=lambda m: date(2025, m, 1).strftime("%B"),
                                  index=date.today().month - 1)
        mdf = get_attendance_monthly(year, month)
        if not mdf.empty:
            mdf["attendance_%"] = (mdf["present"] / mdf["total_marked"].replace(0, 1) * 100).round(1)
            st.dataframe(
                mdf.rename(columns={"name":"Name","department":"Dept","present":"Present",
                                    "absent":"Absent","on_leave":"Leave",
                                    "weekly_off":"WO","attendance_%":"Att %"}),
                use_container_width=True, hide_index=True
            )
            st.caption(f"Total employees: {len(mdf)} | Avg attendance: {mdf['attendance_%'].mean():.1f}%")
        else:
            st.info("No data for selected period.")

    # ── Trends ────────────────────────────────────────────────────────────────
    with tab3:
        trend_df = get_attendance_trend(30)
        if not trend_df.empty:
            st.plotly_chart(attendance_trend_line(trend_df), use_container_width=True,
                            config={"displayModeBar": False})
        monthly_df = get_monthly_attendance_trend(6)
        if not monthly_df.empty:
            from utils.charts import monthly_trend_area
            st.plotly_chart(monthly_trend_area(monthly_df), use_container_width=True,
                            config={"displayModeBar": False})