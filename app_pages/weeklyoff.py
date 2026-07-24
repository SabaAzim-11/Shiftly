"""ShiftSync AI – Weekly Off Management page"""

import streamlit as st
from utils.data import get_employees, update_weekly_off, get_weekly_off_distribution, distribute_weekly_off_assignments
from utils.charts import weekly_off_distribution

DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

def render():
    st.markdown("### 📅 Weekly Off Management")
    st.caption("Individual weekly off assignment and distribution")
    st.markdown("---")

    dist_df = get_weekly_off_distribution()
    emp_df  = get_employees()

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("**Off-Day Distribution**")
        if not dist_df.empty:
            st.plotly_chart(weekly_off_distribution(dist_df), use_container_width=True,
                            config={"displayModeBar": False})

    with col2:
        st.markdown("**Day-wise Count**")
        cols = st.columns(7)
        for col, day in zip(cols, DAYS):
            cnt = len(emp_df[emp_df["weekly_off"] == day])
            with col:
                st.markdown(
                    f'<div style="border:1px solid #2a3350;border-radius:10px;'
                    f'padding:10px;text-align:center">'
                    f'<div style="font-size:10px;color:#ffffff">{day[:3]}</div>'
                    f'<div style="font-size:22px;font-weight:700;color:{"#ffffff" if cnt else "#ffffff"}">{cnt}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    st.markdown("---")
    st.markdown("**Employee Off-Day Map**")
    dept_filter = st.selectbox("Filter by Department",
                                 ["All"] + sorted(emp_df["department"].unique().tolist()),
                                 label_visibility="collapsed")
    view_df = emp_df if dept_filter == "All" else emp_df[emp_df["department"] == dept_filter]

    import pandas as pd
    view_df = view_df.reset_index(drop=True)
    edited = st.data_editor(
        view_df[["emp_id","name","department","shift","weekly_off","weekly_off_type"]].rename(
            columns={"emp_id":"ID","name":"Name","department":"Dept",
                     "weekly_off":"Weekly Off","weekly_off_type":"Off Type"}
        ),
        column_config={
            "Weekly Off": st.column_config.SelectboxColumn("Weekly Off", options=DAYS, required=True),
            "Off Type":   st.column_config.SelectboxColumn("Off Type", options=["Fixed","Rotating"]),
        },
        use_container_width=True, hide_index=True, num_rows="fixed",
    )
    if st.button("💾 Save Changes", type="primary"):
        edited_df = view_df.copy()
        edited_df["weekly_off"] = edited["Weekly Off"].tolist()
        assignments = distribute_weekly_off_assignments(edited_df)
        saved = 0
        for change in assignments:
            update_weekly_off(int(change["id"]), change["weekly_off"])
            saved += 1
        st.success(f"✅ Updated {saved} employee(s).")
        st.rerun()