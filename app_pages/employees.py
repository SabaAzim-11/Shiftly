"""ShiftSync AI – Employee Management page"""

import streamlit as st
import pandas as pd
from datetime import date
from utils.data import (get_employees, add_employee, update_employee,
                         deactivate_employee, get_departments, get_shift_names,
                         get_employee_by_id)
from components.ui import status_badge, badge


WEEKLY_DAYS = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
EMP_TYPES   = ["Full-time","Contract","Part-time","Intern"]


def render():
    st.markdown("### 👥 Employee Management")
    st.caption("Manage all employee records, shifts, and weekly offs")
    st.markdown("---")

    if "show_add" not in st.session_state:
        st.session_state["show_add"] = False
    if "show_edit" not in st.session_state:
        st.session_state["show_edit"] = False

    depts  = ["All"] + get_departments()
    shifts = ["All"] + get_shift_names()

    # ── Filters ───────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        search = st.text_input("🔍 Search", placeholder="Name, ID, email…", label_visibility="collapsed")
    with col2:
        dept_filter = st.selectbox("Department", depts, label_visibility="collapsed")
    with col3:
        shift_filter = st.selectbox("Shift", shifts, label_visibility="collapsed")
    with col4:
        if st.button("➕ Add Employee", type="primary", use_container_width=True):
            st.session_state["show_add"] = True

    # ── Load data ─────────────────────────────────────────────────────────────
    df = get_employees(
        dept=None if dept_filter == "All" else dept_filter,
        shift=None if shift_filter == "All" else shift_filter,
    )

    if search:
        mask = (
            df["name"].str.contains(search, case=False, na=False) |
            df["emp_id"].str.contains(search, case=False, na=False) |
            df["email"].str.contains(search, case=False, na=False) |
            df["designation"].str.contains(search, case=False, na=False)
        )
        df = df[mask]

    # ── Stats row ─────────────────────────────────────────────────────────────
    total_df = get_employees()
    c1, c2, c3, c4, c5 = st.columns(5)
    for col, (label, val, color) in zip(
        [c1, c2, c3, c4, c5],
        [
            ("Total",     len(total_df),                                        "#4f8ef7"),
            ("Full-time", len(total_df[total_df["employment_type"]=="Full-time"]), "#4ade80"),
            ("Contract",  len(total_df[total_df["employment_type"]=="Contract"]),  "#fbbf24"),
            ("Showing",   len(df),                                              "#2dd4bf"),
            ("Depts",     total_df["department"].nunique(),                     "#a78bfa"),
        ]
    ):
        with col:
            st.markdown(
                f'<div style="background:#161b27;border:1px solid #2a3350;border-radius:10px;'
                f'padding:10px 14px;border-top:2px solid {color}">'
                f'<div style="font-size:10px;color:#6b7494;text-transform:uppercase">{label}</div>'
                f'<div style="font-size:22px;font-weight:700;color:{color}">{val}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Table ─────────────────────────────────────────────────────────────────
    display_cols = ["emp_id","name","department","designation","shift","weekly_off","employment_type"]
    if df.empty:
        st.info("No employees match your filters.")
        st.dataframe(
            pd.DataFrame(columns=["ID","Name","Department","Designation","Shift","Weekly Off","Type"]),
            use_container_width=True,
            hide_index=True,
            height=320,
        )
    else:
        st.dataframe(
            df[display_cols].rename(columns={
                "emp_id": "ID", "name": "Name", "department": "Department",
                "designation": "Designation", "shift": "Shift",
                "weekly_off": "Weekly Off", "employment_type": "Type",
            }),
            use_container_width=True,
            hide_index=True,
            height=420,
        )

    # ── Edit / Deactivate ─────────────────────────────────────────────────────
    st.markdown("**Edit or Deactivate Employee**")
    if df.empty:
        st.warning("No employees available to edit or deactivate.")
        edit_clicked = False
        selected_label = None
    else:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            emp_options = {f"{r.emp_id} – {r.name}": r.id for _, r in df.iterrows()}
            selected_label = st.selectbox(
                "Select employee",
                list(emp_options.keys()),
                label_visibility="collapsed"
            )
        with col_b:
            edit_clicked = st.button("✏ Edit", use_container_width=True)

        if edit_clicked and selected_label:
            emp_db_id = emp_options[selected_label]
            st.session_state["edit_emp_id"] = emp_db_id
            st.session_state["show_edit"] = True

    # ── Add Employee Form ─────────────────────────────────────────────────────
    if st.session_state.get("show_add"):
        st.markdown("---")
        st.markdown("#### ➕ Add New Employee")
        with st.form("add_emp_form"):
            c1, c2 = st.columns(2)
            with c1:
                name         = st.text_input("Full Name *")
                email        = st.text_input("Email *")
                mobile       = st.text_input("Mobile")
                dept         = st.selectbox("Department *", get_departments())
                designation  = st.text_input("Designation *")
            with c2:
                manager      = st.text_input("Manager")
                location     = st.text_input("Location")
                joining_date = st.date_input("Joining Date *", value=date.today())
                emp_type     = st.selectbox("Employment Type", EMP_TYPES)
                shift        = st.selectbox("Shift *", get_shift_names())
                weekly_off   = st.selectbox("Weekly Off Day", WEEKLY_DAYS)
                off_type     = st.selectbox("Off Type", ["Fixed", "Rotating"])

            submitted = st.form_submit_button("✅ Add Employee", type="primary")
            cancel    = st.form_submit_button("Cancel")

        if cancel:
            st.session_state["show_add"] = False
            st.rerun()

        if submitted:
            if not name or not email or not designation:
                st.error("Name, email, and designation are required.")
            else:
                try:
                    add_employee({
                        "name": name, "email": email, "mobile": mobile,
                        "department": dept, "designation": designation,
                        "manager": manager, "location": location,
                        "joining_date": joining_date.isoformat(),
                        "employment_type": emp_type, "shift": shift,
                        "weekly_off": weekly_off, "weekly_off_type": off_type,
                    })
                    st.success(f"✅ Employee '{name}' added successfully!")
                    st.session_state["show_add"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Employee save failed: {e}")

    # ── Edit Employee Form ────────────────────────────────────────────────────
    if st.session_state.get("show_edit"):
        emp_db_id = st.session_state.get("edit_emp_id")
        emp = get_employee_by_id(emp_db_id)
        if emp:
            st.markdown("---")
            st.markdown(f"#### ✏ Edit Employee — {emp['name']}")
            with st.form("edit_emp_form"):
                c1, c2 = st.columns(2)
                depts_list  = get_departments()
                shifts_list = get_shift_names()
                with c1:
                    name        = st.text_input("Full Name", value=emp["name"])
                    email       = st.text_input("Email", value=emp["email"])
                    mobile      = st.text_input("Mobile", value=emp.get("mobile",""))
                    dept_idx    = depts_list.index(emp["department"]) if emp["department"] in depts_list else 0
                    dept        = st.selectbox("Department", depts_list, index=dept_idx)
                    designation = st.text_input("Designation", value=emp["designation"])
                with c2:
                    manager     = st.text_input("Manager", value=emp.get("manager",""))
                    location    = st.text_input("Location", value=emp.get("location",""))
                    emp_type    = st.selectbox("Employment Type", EMP_TYPES,
                                               index=EMP_TYPES.index(emp["employment_type"])
                                               if emp["employment_type"] in EMP_TYPES else 0)
                    shift_idx   = shifts_list.index(emp["shift_name"]) if emp["shift_name"] in shifts_list else 0
                    shift       = st.selectbox("Shift", shifts_list, index=shift_idx)
                    off_idx     = WEEKLY_DAYS.index(emp["weekly_off"]) if emp["weekly_off"] in WEEKLY_DAYS else 0
                    weekly_off  = st.selectbox("Weekly Off", WEEKLY_DAYS, index=off_idx)
                    off_type    = st.selectbox("Off Type", ["Fixed","Rotating"])

                col_s, col_d, col_c = st.columns(3)
                save    = col_s.form_submit_button("💾 Save Changes", type="primary")
                deact   = col_d.form_submit_button("🗑 Deactivate")
                cancel2 = col_c.form_submit_button("Cancel")

            if cancel2:
                st.session_state["show_edit"] = False
                st.rerun()
            if save:
                update_employee(emp_db_id, {
                    "name": name, "email": email, "mobile": mobile,
                    "department": dept, "designation": designation,
                    "manager": manager, "location": location,
                    "employment_type": emp_type, "shift": shift,
                    "weekly_off": weekly_off, "weekly_off_type": off_type,
                })
                st.success("✅ Employee updated successfully!")
                st.session_state["show_edit"] = False
                st.rerun()
            if deact:
                deactivate_employee(emp_db_id)
                st.warning(f"Employee deactivated.")
                st.session_state["show_edit"] = False
                st.rerun()

    # ── Bulk import hint ──────────────────────────────────────────────────────
    with st.expander("📥 Bulk Import via Excel"):
        st.info("Upload a .xlsx file with columns: name, email, mobile, department, "
                "designation, joining_date, shift, weekly_off, employment_type")
        uploaded = st.file_uploader("Upload Employee Excel", type=["xlsx"])
        if uploaded:
            try:
                import_df = pd.read_excel(uploaded)
                st.dataframe(import_df.head(10), use_container_width=True, hide_index=True)
                if st.button("✅ Import All Rows", type="primary"):
                    count = 0
                    for _, row in import_df.iterrows():
                        try:
                            add_employee({
                                "name": row.get("name",""),
                                "email": row.get("email",""),
                                "mobile": str(row.get("mobile","")),
                                "department": row.get("department","IT"),
                                "designation": row.get("designation",""),
                                "manager": row.get("manager",""),
                                "location": row.get("location",""),
                                "joining_date": str(row.get("joining_date", date.today())),
                                "employment_type": row.get("employment_type","Full-time"),
                                "shift": row.get("shift","General"),
                                "weekly_off": row.get("weekly_off","Sunday"),
                                "weekly_off_type": "Fixed",
                            })
                            count += 1
                        except Exception:
                            pass
                    st.success(f"✅ Imported {count} employees.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading file: {e}")