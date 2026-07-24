"""ShiftSync AI – Leave Management page"""

import streamlit as st
from datetime import date, timedelta
from utils.data import (get_leave_requests, submit_leave_request,
                         update_leave_status, get_leave_balance,
                         get_leave_types, get_employees)
from auth import current_user, is_admin


def render():
    st.markdown("### 🏖 Leave Management")
    st.caption("Applications, approvals, balances, and team calendar")
    st.markdown("---")

    user = current_user()
    admin = is_admin()

    tabs = st.tabs(["📥 Requests", "💰 Leave Balance", "📅 Team Calendar", "➕ Apply Leave"])

    # ── All Requests ──────────────────────────────────────────────────────────
    with tabs[0]:
        status_filter = st.selectbox("Filter by Status",
                                      ["All","Pending","Approved","Rejected"],
                                      label_visibility="collapsed")
        df = get_leave_requests(status=None if status_filter=="All" else status_filter)

        c1, c2, c3, c4 = st.columns(4)
        for col, (lbl, stat, color) in zip(
            [c1, c2, c3, c4],
            [("Pending","Pending","#fbbf24"),("Approved","Approved","#4ade80"),
             ("Rejected","Rejected","#f87171"),("Total",None,"#4f8ef7")]
        ):
            cnt = len(get_leave_requests(status=stat)) if stat else len(get_leave_requests())
            with col:
                st.markdown(
                    f'<div style="border:1px solid #2a3350;border-radius:10px;'
                    f'padding:10px;border-top:2px solid {color}">'
                    f'<div style="font-size:10px;color:#6b7494">{lbl}</div>'
                    f'<div style="font-size:22px;font-weight:700;color:{color}">{cnt}</div></div>',
                    unsafe_allow_html=True
                )

        st.markdown("<br>", unsafe_allow_html=True)

        if df.empty:
            st.info("No leave requests found.")
        else:
            st.dataframe(
                df[["id","employee","department","leave_type","from_date","to_date","days","reason","status","applied_on"]],
                use_container_width=True, hide_index=True,
            )

            if admin:
                st.markdown("**Approve / Reject a Request**")
                pending_df = get_leave_requests(status="Pending")
                if not pending_df.empty:
                    options = {f"#{r.id} – {r.employee} ({r.leave_type}, {r.days}d)": r.id
                               for _, r in pending_df.iterrows()}
                    col_sel, col_app, col_rej = st.columns([3, 1, 1])
                    with col_sel:
                        chosen = st.selectbox("Select Request", list(options.keys()),
                                              label_visibility="collapsed")
                    with col_app:
                        if st.button("✅ Approve", type="primary", use_container_width=True):
                            update_leave_status(options[chosen], "Approved")
                            st.success("Leave approved.")
                            st.rerun()
                    with col_rej:
                        if st.button("❌ Reject", use_container_width=True):
                            update_leave_status(options[chosen], "Rejected")
                            st.warning("Leave rejected.")
                            st.rerun()
                else:
                    st.success("✅ No pending requests.")

    # ── Leave Balance ─────────────────────────────────────────────────────────
    with tabs[1]:
        emp_df = get_employees()
        emp_map = {f"{r.emp_id} – {r['name']}": r.id
                   for _, r in emp_df.iterrows()}
        selected = st.selectbox("Select Employee", list(emp_map.keys()))
        emp_db_id = emp_map[selected]

        balance_df = get_leave_balance(emp_db_id)
        if not balance_df.empty:
            COLORS = {"Casual Leave":"#4f8ef7","Sick Leave":"#f87171",
                      "Earned Leave":"#4ade80","Comp Off":"#a78bfa","Work From Home":"#2dd4bf"}
            cols = st.columns(len(balance_df))
            for col, (_, row) in zip(cols, balance_df.iterrows()):
                color = COLORS.get(row["name"], "#4f8ef7")
                pct   = int((row["remaining"] / row["allocated"]) * 100) if row["allocated"] else 0
                with col:
                    st.markdown(
                        f'<div style="border:1px solid #2a3350;border-radius:12px;'
                        f'padding:14px;text-align:center">'
                        f'<div style="font-size:11px;color:#6b7494">{row["name"]}</div>'
                        f'<div style="font-size:30px;font-weight:700;color:{color};margin:8px 0">'
                        f'{int(row["remaining"])}</div>'
                        f'<div style="font-size:11px;color:#6b7494">of {int(row["allocated"])} remaining</div>'
                        f'<div style="height:4px;background:#252d3f;border-radius:2px;margin-top:8px">'
                        f'<div style="width:{pct}%;height:100%;background:{color};border-radius:2px"></div>'
                        f'</div></div>',
                        unsafe_allow_html=True
                    )
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(
                balance_df.rename(columns={"name":"Leave Type","code":"Code",
                                           "allocated":"Allocated","used":"Used","remaining":"Remaining"}),
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No leave balance data found.")

    # ── Team Calendar ─────────────────────────────────────────────────────────
    with tabs[2]:
        st.markdown("**Approved Leaves This Month**")
        approved = get_leave_requests(status="Approved")
        today = date.today()
        month_leaves = approved[
            (approved["from_date"] >= today.replace(day=1).isoformat()) |
            (approved["to_date"] >= today.replace(day=1).isoformat())
        ] if not approved.empty else approved

        if not month_leaves.empty:
            st.dataframe(
                month_leaves[["employee","department","leave_type","from_date","to_date","days"]],
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No approved leaves this month.")

    # ── Apply Leave ───────────────────────────────────────────────────────────
    with tabs[3]:
        st.markdown("**Apply for Leave**")
        lt_df = get_leave_types()
        emp_df2 = get_employees()
        emp_map2 = {f"{r.emp_id} – {r['name']}": r.id for _, r in emp_df2.iterrows()}

        with st.form("apply_leave"):
            emp_sel = st.selectbox("Employee", list(emp_map2.keys()))
            lt_sel  = st.selectbox("Leave Type", lt_df["name"].tolist())
            col_f, col_t = st.columns(2)
            with col_f:
                from_d = st.date_input("From Date", value=date.today())
            with col_t:
                to_d = st.date_input("To Date", value=date.today() + timedelta(days=1))
            reason = st.text_area("Reason", placeholder="Brief reason for leave…")
            submitted = st.form_submit_button("📤 Submit Request", type="primary")

        if submitted:
            days = max(1, (to_d - from_d).days + 1)
            submit_leave_request(
                emp_map2[emp_sel], lt_sel,
                from_d.isoformat(), to_d.isoformat(), days, reason
            )
            st.success(f"✅ Leave request submitted for {days} day(s).")
            st.rerun()