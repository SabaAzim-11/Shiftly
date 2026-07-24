"""ShiftSync AI – Employee Calendar page"""

import streamlit as st
import calendar
from datetime import date
from utils.data import (get_employees, get_leave_requests,
                         get_holidays, get_attendance_monthly)
from auth import current_user


def render():
    st.markdown("### 🗓 My Calendar")
    st.caption("Personal schedule — shifts, leaves, holidays, and attendance")
    st.markdown("---")

    emp_df = get_employees()
    emp_map = {f"{r.emp_id} – {r['name']}": r.id for _, r in emp_df.iterrows()}
    user = current_user()

    col_emp, col_yr, col_mo = st.columns([3, 1, 1])
    with col_emp:
        selected_emp = st.selectbox("Employee", list(emp_map.keys()),
                                     label_visibility="collapsed")
    with col_yr:
        year = st.selectbox("Year", [2026, 2025, 2024], index=0, label_visibility="collapsed")
    with col_mo:
        month = st.selectbox("Month", range(1, 13),
                              format_func=lambda m: date(year, m, 1).strftime("%B"),
                              index=date.today().month - 1,
                              label_visibility="collapsed")

    emp_db_id = emp_map[selected_emp]

    # ── Fetch data ─────────────────────────────────────────────────────────────
    leave_df    = get_leave_requests(emp_id=emp_db_id)
    approved_lv = leave_df[leave_df["status"] == "Approved"] if not leave_df.empty else leave_df
    holidays_df = get_holidays(year)
    att_df      = get_attendance_monthly(year, month)

    holiday_dates = set(holidays_df["holiday_date"].tolist()) if not holidays_df.empty else set()

    leave_dates = set()
    if not approved_lv.empty:
        for _, row in approved_lv.iterrows():
            try:
                d = date.fromisoformat(row["from_date"])
                end = date.fromisoformat(row["to_date"])
                while d <= end:
                    if d.year == year and d.month == month:
                        leave_dates.add(d.isoformat())
                    d = date(d.year, d.month, d.day + 1) if d.day < 28 else date(d.year + (d.month == 12), (d.month % 12) + 1, 1)
            except Exception:
                pass

    # ── Calendar grid ─────────────────────────────────────────────────────────
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"**{date(year, month, 1).strftime('%B %Y')}**")

        LEGEND = [
            ("#4f8ef7","Today"),("rgba(74,222,128,.2)","Present"),
            ("#2d2010","Leave"),("#2d1010","Holiday"),("#1e1540","Weekly Off"),
        ]
        legend_html = " ".join(
            f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:11px;color:#9aa3c0">'
            f'<span style="width:10px;height:10px;border-radius:2px;background:{c};display:inline-block"></span>{l}</span>'
            for c, l in LEGEND
        )
        st.markdown(legend_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Build HTML calendar
        cal = calendar.monthcalendar(year, month)
        today_str = date.today().isoformat()

        day_names = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        header = "".join(
            f'<div style="text-align:center;font-size:11px;color:#6b7494;padding:4px">{d}</div>'
            for d in day_names
        )

        cells = ""
        for week in cal:
            for day in week:
                if day == 0:
                    cells += '<div></div>'
                    continue
                d_str = date(year, month, day).isoformat()
                is_today   = d_str == today_str
                is_holiday = d_str in holiday_dates
                is_leave   = d_str in leave_dates
                is_sunday  = date(year, month, day).weekday() == 6

                if is_today:
                    bg, tc = "#4f8ef7", "#fff"
                elif is_holiday:
                    bg, tc = "#2d1010", "#f87171"
                elif is_leave:
                    bg, tc = "#2d2010", "#fbbf24"
                elif is_sunday:
                    bg, tc = "#1e1540", "#a78bfa"
                else:
                    bg, tc = "#1e2435", "#9aa3c0"

                cells += (
                    f'<div style="text-align:center;padding:6px 4px;border-radius:6px;'
                    f'background:{bg};color:{tc};font-size:13px;cursor:pointer">{day}</div>'
                )

        cal_html = (
            f'<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:4px">'
            f'{header}{cells}</div>'
        )
        st.markdown(cal_html, unsafe_allow_html=True)

    with col2:
        # ── Summary boxes ──────────────────────────────────────────────────────
        emp_row = emp_df[emp_df["id"] == emp_db_id]
        if not emp_row.empty:
            e = emp_row.iloc[0]
            st.markdown("**My Details**")
            for label, value, color in [
                ("Shift",      e["shift"],      "#4f8ef7"),
                ("Weekly Off", e["weekly_off"], "#a78bfa"),
                ("Dept",       e["department"], "#2dd4bf"),
            ]:
                st.markdown(
                    f'<div style="background:#1e2435;border-radius:8px;padding:8px 12px;'
                    f'margin-bottom:6px;display:flex;justify-content:space-between;align-items:center">'
                    f'<span style="font-size:12px;color:#6b7494">{label}</span>'
                    f'<span style="font-size:13px;font-weight:600;color:{color}">{value}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        st.markdown("<br>**Month Summary**")
        att_row = att_df[att_df.index == att_df.index[0]].squeeze() if not att_df.empty else None
        working_days = sum(1 for d in range(1, calendar.monthrange(year, month)[1] + 1)
                           if date(year, month, d).weekday() != 6)
        leave_cnt = len(leave_dates)

        for label, val, color in [
            ("Working Days",   working_days, "#4f8ef7"),
            ("Leaves Applied", leave_cnt,   "#fbbf24"),
            ("Holidays",       len([h for h in holiday_dates
                                    if h.startswith(f"{year}-{month:02d}")]), "#f87171"),
        ]:
            st.markdown(
                f'<div style="background:#1e2435;border-radius:8px;padding:8px 12px;'
                f'margin-bottom:6px;display:flex;justify-content:space-between">'
                f'<span style="font-size:12px;color:#6b7494">{label}</span>'
                f'<span style="font-weight:700;color:{color}">{val}</span>'
                f'</div>',
                unsafe_allow_html=True
            )