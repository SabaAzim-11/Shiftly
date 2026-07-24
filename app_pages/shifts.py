"""ShiftSync AI – Shift Management page"""

import streamlit as st
from utils.data import (get_employees, get_shifts, get_shift_names,
                         get_shift_distribution, rotate_shift, get_departments)
from utils.charts import shift_donut


def render():
    st.markdown("### 🔄 Shift Management")
    st.caption("Shift assignment, rotation engine, and coverage monitoring")
    st.markdown("---")

    shifts_df = get_shifts()
    emp_df    = get_employees()

    # ── KPI ───────────────────────────────────────────────────────────────────
    cols = st.columns(4)
    SHIFT_COLORS = {
        "General":"#4f8ef7",
        "A":"#fbbf24",
        "B":"#a78bfa",
        "Morning":"#fbbf24",
        "Evening":"#a78bfa",
        "Night":"#6b7494",
    }
    SHIFT_TIMES  = {
        "General":"09:00–18:00",
        "A":"06:00–14:00",
        "B":"14:00–22:00",
        "Morning":"06:00–14:00",
        "Evening":"14:00–22:00",
        "Night":"22:00–06:00",
    }
    for col, (_, row) in zip(cols, shifts_df.iterrows()):
        cnt   = len(emp_df[emp_df["shift"] == row["name"]])
        color = SHIFT_COLORS.get(row["name"], "#4f8ef7")
        with col:
            st.markdown(
                f'<div style="border:1px solid #2a3350;border-radius:12px;'
                f'padding:14px;border-top:2px solid {color}">'
                f'<div style="font-size:10px;color:#6b7494;text-transform:uppercase">{row["name"]} Shift</div>'
                f'<div style="font-size:28px;font-weight:700;color:{color}">{cnt}</div>'
                f'<div style="font-size:11px;color:#6b7494">{SHIFT_TIMES.get(row["name"],"")}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    # ── Donut ─────────────────────────────────────────────────────────────────
    with col1:
        st.markdown("**Shift Distribution**")
        dist = get_shift_distribution()
        if not dist.empty:
            st.plotly_chart(shift_donut(dist), use_container_width=True,
                            config={"displayModeBar": False})

    # ── Coverage monitor ──────────────────────────────────────────────────────
    with col2:
        st.markdown("**Coverage Monitor**")
        MIN_REQ = {"General": 5, "A": 3, "B": 3, "Morning": 3, "Evening": 2, "Night": 2}
        for _, row in shifts_df.iterrows():
            cnt    = len(emp_df[emp_df["shift"] == row["name"]])
            minr   = MIN_REQ.get(row["name"], 2)
            pct    = min(100, int(cnt / len(emp_df) * 100)) if len(emp_df) else 0
            ok     = cnt >= minr
            color  = "#4ade80" if ok else "#f87171"
            st.markdown(
                f'<div style="margin-bottom:12px">'
                f'<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">'
                f'<span style="color:#9aa3c0">{row["name"]} Shift</span>'
                f'<span style="color:{color}">{cnt}/{minr} min {"✓" if ok else "⚠"}</span>'
                f'</div>'
                f'<div style="height:4px;background:#252d3f;border-radius:2px">'
                f'<div style="width:{pct}%;height:100%;background:{color};border-radius:2px"></div>'
                f'</div></div>',
                unsafe_allow_html=True
            )

    # ── Rotation engine ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**⚙ Shift Rotation Engine**")
    st.info("ℹ Auto-rotation reassigns employees across shifts on a weekly/monthly cycle. "
            "Use the manual tool below for one-off changes.")

    with st.expander("Manual Shift Reassignment"):
        emp_map = {f"{r.emp_id} – {r['name']} (currently {r['shift']})": r.id
                   for _, r in emp_df.iterrows()}
        col_e, col_s, col_b = st.columns([3, 2, 1])
        with col_e:
            chosen_emp = st.selectbox("Employee", list(emp_map.keys()),
                                       label_visibility="collapsed")
        with col_s:
            new_shift = st.selectbox("New Shift", get_shift_names(),
                                      label_visibility="collapsed")
        with col_b:
            if st.button("Reassign", type="primary", use_container_width=True):
                rotate_shift(emp_map[chosen_emp], new_shift)
                st.success(f"Shift updated to {new_shift}.")
                st.rerun()

    # ── Monthly rotation table ────────────────────────────────────────────────
    # st.markdown("**Monthly Rotation Plan — Production**")
    # prod_df = emp_df[emp_df["department"] == "Production"]
    # st.markdown(f"**Production employees:** {len(prod_df)}")
    # ROTA = ["Morning", "Evening", "Night", "General"]
    # rows = []
    # for _, r in prod_df.iterrows():
    #     idx  = ROTA.index(r["shift"]) if r["shift"] in ROTA else 0
    #     rows.append({
    #         "Employee":  r["name"],
    #         "Week 1":    ROTA[(idx)   % 4],
    #         "Week 2":    ROTA[(idx+1) % 4],
    #         "Week 3":    ROTA[(idx+2) % 4],
    #         "Week 4":    ROTA[(idx+3) % 4],
    #     })
    # if rows:
    #     import pandas as pd
    #     st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    # else:
    #     st.info("No production employees found. Check your employee department assignments.")