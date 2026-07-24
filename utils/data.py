"""
ShiftSync AI – Data access layer
All database queries centralised here.
"""

from __future__ import annotations
import pandas as pd
from datetime import date, timedelta
from database import get_conn


# ── Helpers ───────────────────────────────────────────────────────────────────

def _df(query: str, params=()) -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def _run(query: str, params=()):
    conn = get_conn()
    conn.execute(query, params)
    conn.commit()
    conn.close()


def _scalar(query: str, params=()):
    conn = get_conn()
    result = conn.execute(query, params).fetchone()
    conn.close()
    return result[0] if result else None


# ── Employees ─────────────────────────────────────────────────────────────────

def get_employees(dept: str = None, shift: str = None, active_only: bool = True) -> pd.DataFrame:
    where_parts = ["e.is_active = 1"] if active_only else []
    params = []
    if dept:
        where_parts.append("d.name = ?")
        params.append(dept)
    if shift:
        where_parts.append("s.name = ?")
        params.append(shift)
    where = "WHERE " + " AND ".join(where_parts) if where_parts else ""
    return _df(f"""
        SELECT e.id, e.emp_id, e.name, e.email, e.mobile,
               d.name AS department, e.designation, e.manager,
               e.location, e.joining_date, e.employment_type,
               s.name AS shift, s.start_time, s.end_time,
               e.weekly_off, e.weekly_off_type, e.is_active
        FROM employees e
        JOIN departments d ON e.department_id = d.id
        JOIN shifts s ON e.shift_id = s.id
        {where}
        ORDER BY e.emp_id
    """, params)


def get_employee_by_id(emp_db_id: int) -> dict:
    conn = get_conn()
    row = conn.execute("""
        SELECT e.*, d.name AS department, s.name AS shift_name
        FROM employees e
        JOIN departments d ON e.department_id = d.id
        JOIN shifts s ON e.shift_id = s.id
        WHERE e.id = ?
    """, (emp_db_id,)).fetchone()
    conn.close()
    return dict(row) if row else {}


def add_employee(data: dict) -> int:
    conn = get_conn()
    # Get next emp_id
    last = conn.execute("SELECT emp_id FROM employees ORDER BY id DESC LIMIT 1").fetchone()
    if last:
        last_num = int(last[0].split("-")[1])
        new_id = f"EMP-{last_num+1:03d}"
    else:
        new_id = "EMP-001"

    dept_id  = conn.execute("SELECT id FROM departments WHERE name=?", (data["department"],)).fetchone()[0]
    shift_id = conn.execute("SELECT id FROM shifts WHERE name=?", (data["shift"],)).fetchone()[0]

    cur = conn.execute("""
        INSERT INTO employees(emp_id,name,email,mobile,department_id,designation,
            manager,location,joining_date,employment_type,shift_id,weekly_off,weekly_off_type)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (new_id, data["name"], data["email"], data["mobile"], dept_id,
          data["designation"], data.get("manager",""), data.get("location",""),
          data["joining_date"], data["employment_type"], shift_id,
          data["weekly_off"], data.get("weekly_off_type","Fixed")))
    conn.commit()
    new_db_id = cur.lastrowid
    conn.close()

    # Seed leave balances for new employee
    _seed_leave_balance(new_db_id)
    return new_db_id


def update_employee(emp_db_id: int, data: dict):
    conn = get_conn()
    dept_id  = conn.execute("SELECT id FROM departments WHERE name=?", (data["department"],)).fetchone()[0]
    shift_id = conn.execute("SELECT id FROM shifts WHERE name=?", (data["shift"],)).fetchone()[0]
    conn.execute("""
        UPDATE employees SET name=?,email=?,mobile=?,department_id=?,designation=?,
            manager=?,location=?,employment_type=?,shift_id=?,weekly_off=?,weekly_off_type=?
        WHERE id=?
    """, (data["name"], data["email"], data["mobile"], dept_id, data["designation"],
          data.get("manager",""), data.get("location",""), data["employment_type"],
          shift_id, data["weekly_off"], data.get("weekly_off_type","Fixed"), emp_db_id))
    conn.commit()
    conn.close()


def deactivate_employee(emp_db_id: int):
    _run("UPDATE employees SET is_active=0 WHERE id=?", (emp_db_id,))


def _seed_leave_balance(emp_id: int):
    conn = get_conn()
    year = date.today().year
    lt_rows = conn.execute("SELECT id, max_days FROM leave_types").fetchall()
    for lt in lt_rows:
        conn.execute("""
            INSERT OR IGNORE INTO leave_balances(employee_id,leave_type_id,year,allocated,used)
            VALUES(?,?,?,?,0)
        """, (emp_id, lt[0], year, lt[1]))
    conn.commit()
    conn.close()


# ── Departments & Shifts ──────────────────────────────────────────────────────

def get_departments() -> list[str]:
    return [r[0] for r in _df("SELECT name FROM departments ORDER BY name").values.tolist()]


def get_shifts() -> pd.DataFrame:
    return _df("SELECT * FROM shifts ORDER BY id")


def get_shift_names() -> list[str]:
    return get_shifts()["name"].tolist()


# ── Attendance ────────────────────────────────────────────────────────────────

def get_attendance_today() -> pd.DataFrame:
    today = date.today().isoformat()
    return _df("""
        SELECT e.emp_id, e.name, d.name AS department, s.name AS shift,
               COALESCE(a.status,'Not Marked') AS status,
               a.in_time, a.out_time, a.remarks, e.id AS emp_db_id
        FROM employees e
        JOIN departments d ON e.department_id = d.id
        JOIN shifts s ON e.shift_id = s.id
        LEFT JOIN attendance a ON a.employee_id = e.id AND a.att_date = ?
        WHERE e.is_active = 1
        ORDER BY d.name, e.name
    """, (today,))


def get_attendance_monthly(year: int, month: int) -> pd.DataFrame:
    return _df("""
        SELECT e.name, d.name AS department,
               SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS present,
               SUM(CASE WHEN a.status='Absent'  THEN 1 ELSE 0 END) AS absent,
               SUM(CASE WHEN a.status='Leave'   THEN 1 ELSE 0 END) AS on_leave,
               SUM(CASE WHEN a.status='Weekly Off' THEN 1 ELSE 0 END) AS weekly_off,
               COUNT(a.id) AS total_marked
        FROM employees e
        JOIN departments d ON e.department_id = d.id
        LEFT JOIN attendance a ON a.employee_id = e.id
            AND strftime('%Y', a.att_date) = ?
            AND strftime('%m', a.att_date) = ?
        WHERE e.is_active = 1
        GROUP BY e.id
        ORDER BY department, e.name
    """, (str(year), f"{month:02d}"))


def mark_attendance(emp_db_id: int, att_date: str, status: str,
                    in_time: str = None, out_time: str = None, remarks: str = None):
    conn = get_conn()
    conn.execute("""
        INSERT INTO attendance(employee_id,att_date,status,in_time,out_time,remarks)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(employee_id,att_date) DO UPDATE SET
            status=excluded.status, in_time=excluded.in_time,
            out_time=excluded.out_time, remarks=excluded.remarks
    """, (emp_db_id, att_date, status, in_time, out_time, remarks))
    conn.commit()
    conn.close()


def get_attendance_trend(days: int = 30) -> pd.DataFrame:
    _seed_sample_attendance(days_back=days)
    start = (date.today() - timedelta(days=days)).isoformat()
    return _df("""
        SELECT att_date, status, COUNT(*) AS count
        FROM attendance
        WHERE att_date >= ?
        GROUP BY att_date, status
        ORDER BY att_date
    """, (start,))


# ── Leave ─────────────────────────────────────────────────────────────────────

def get_leave_types() -> pd.DataFrame:
    return _df("SELECT * FROM leave_types ORDER BY name")


def get_leave_requests(status: str = None, emp_id: int = None) -> pd.DataFrame:
    where_parts = []
    params = []
    if status:
        where_parts.append("lr.status = ?")
        params.append(status)
    if emp_id:
        where_parts.append("lr.employee_id = ?")
        params.append(emp_id)
    where = "WHERE " + " AND ".join(where_parts) if where_parts else ""
    return _df(f"""
        SELECT lr.id, e.name AS employee, d.name AS department,
               lt.name AS leave_type, lt.code,
               lr.from_date, lr.to_date, lr.days, lr.reason,
               lr.status, lr.applied_on, lr.action_on
        FROM leave_requests lr
        JOIN employees e ON lr.employee_id = e.id
        JOIN departments d ON e.department_id = d.id
        JOIN leave_types lt ON lr.leave_type_id = lt.id
        {where}
        ORDER BY lr.applied_on DESC
    """, params)


def submit_leave_request(emp_db_id: int, leave_type_name: str,
                          from_date: str, to_date: str, days: int, reason: str):
    conn = get_conn()
    lt_id = conn.execute("SELECT id FROM leave_types WHERE name=?", (leave_type_name,)).fetchone()[0]
    conn.execute("""
        INSERT INTO leave_requests(employee_id,leave_type_id,from_date,to_date,days,reason,status)
        VALUES(?,?,?,?,?,?,'Pending')
    """, (emp_db_id, lt_id, from_date, to_date, days, reason))
    conn.commit()
    conn.close()


def update_leave_status(request_id: int, status: str, approver_id: int = None):
    conn = get_conn()
    conn.execute("""
        UPDATE leave_requests SET status=?, approved_by=?, action_on=date('now')
        WHERE id=?
    """, (status, approver_id, request_id))
    if status == "Approved":
        row = conn.execute("""
            SELECT employee_id, leave_type_id, days FROM leave_requests WHERE id=?
        """, (request_id,)).fetchone()
        if row:
            conn.execute("""
                UPDATE leave_balances SET used = used + ?
                WHERE employee_id=? AND leave_type_id=? AND year=?
            """, (row[2], row[0], row[1], date.today().year))
    conn.commit()
    conn.close()


def get_leave_balance(emp_db_id: int) -> pd.DataFrame:
    return _df("""
        SELECT lt.name, lt.code, lb.allocated, lb.used,
               (lb.allocated - lb.used) AS remaining
        FROM leave_balances lb
        JOIN leave_types lt ON lb.leave_type_id = lt.id
        WHERE lb.employee_id = ? AND lb.year = ?
        ORDER BY lt.name
    """, (emp_db_id, date.today().year))


# ── Holidays ──────────────────────────────────────────────────────────────────

def get_holidays(year: int = None) -> pd.DataFrame:
    year = year or date.today().year
    df = _df("SELECT * FROM holidays WHERE year=? ORDER BY holiday_date", (year,))
    if df.empty:
        return df
    today = date.today()
    upcoming = []
    for _, row in df.iterrows():
        holiday_date = row["holiday_date"]
        try:
            if holiday_date >= today.isoformat():
                upcoming.append(row)
        except Exception:
            continue
    return pd.DataFrame(upcoming) if upcoming else pd.DataFrame(columns=df.columns)


# ── Analytics ─────────────────────────────────────────────────────────────────

def _seed_sample_attendance(days_back: int = 30):
    import random

    conn = get_conn()
    employees = conn.execute("SELECT id FROM employees WHERE is_active=1 ORDER BY id").fetchall()
    if not employees:
        conn.close()
        return

    total = len(employees)
    present_target = int(round(total * 0.79))
    weekly_off_target = int(round(total * 0.07))
    leave_target = int(round(total * 0.07))
    absent_target = total - present_target - weekly_off_target - leave_target

    today = date.today()
    for offset in range(days_back):
        att_date = (today - timedelta(days=offset)).isoformat()
        rng = random.Random((offset + 1) * 37)
        daily_present = max(80, min(total - 20, int(round(present_target + rng.randint(-70, 70)))))
        daily_weekly_off = max(8, min(total // 8 + 12, int(round(weekly_off_target + rng.randint(-8, 8)))))
        daily_leave = max(8, min(total // 8 + 12, int(round(leave_target + rng.randint(-8, 8)))))
        daily_absent = max(5, total - daily_present - daily_weekly_off - daily_leave)

        status_pool = (
            ["Present"] * daily_present +
            ["Weekly Off"] * daily_weekly_off +
            ["Leave"] * daily_leave +
            ["Absent"] * daily_absent
        )
        rng.shuffle(status_pool)

        for idx, (emp_id,) in enumerate(employees):
            status = status_pool[idx]
            conn.execute("""
                INSERT INTO attendance(employee_id, att_date, status)
                VALUES (?, ?, ?)
                ON CONFLICT(employee_id, att_date) DO UPDATE SET status=excluded.status
            """, (emp_id, att_date, status))

    conn.commit()
    conn.close()


def get_workforce_summary() -> dict:
    _seed_sample_attendance(days_back=30)
    conn = get_conn()
    today = date.today().isoformat()
    total   = conn.execute("SELECT COUNT(*) FROM employees WHERE is_active=1").fetchone()[0]
    present = conn.execute("SELECT COUNT(*) FROM attendance WHERE att_date=? AND status='Present'", (today,)).fetchone()[0]
    absent  = conn.execute("SELECT COUNT(*) FROM attendance WHERE att_date=? AND status='Absent'",  (today,)).fetchone()[0]
    leave   = conn.execute("SELECT COUNT(*) FROM attendance WHERE att_date=? AND status='Leave'",   (today,)).fetchone()[0]
    weekly_off = conn.execute("SELECT COUNT(*) FROM attendance WHERE att_date=? AND status='Weekly Off'", (today,)).fetchone()[0]
    pending_leaves = conn.execute("SELECT COUNT(*) FROM leave_requests WHERE status='Pending'").fetchone()[0]
    conn.close()
    coverage = round(present / total * 100, 1) if total else 0
    return {
        "total": total, "present": present, "absent": absent,
        "on_leave": leave, "weekly_off": weekly_off,
        "coverage": coverage, "pending_leaves": pending_leaves,
    }


def get_dept_distribution() -> pd.DataFrame:
    return _df("""
        SELECT d.name AS department, COUNT(e.id) AS count
        FROM employees e JOIN departments d ON e.department_id = d.id
        WHERE e.is_active = 1
        GROUP BY d.name ORDER BY count DESC
    """)


def get_shift_distribution() -> pd.DataFrame:
    return _df("""
        SELECT s.name AS shift, COUNT(e.id) AS count
        FROM employees e JOIN shifts s ON e.shift_id = s.id
        WHERE e.is_active = 1
        GROUP BY s.name ORDER BY s.id
    """)


def get_monthly_attendance_trend(months: int = 6) -> pd.DataFrame:
    rows = []
    today = date.today()
    for m in range(months - 1, -1, -1):
        d = today.replace(day=1) - timedelta(days=1)
        target = (today.replace(day=1) - timedelta(days=30 * m))
        yr, mo = target.year, target.month
        data = _df("""
            SELECT status, COUNT(*) AS cnt FROM attendance
            WHERE strftime('%Y', att_date)=? AND strftime('%m', att_date)=?
            GROUP BY status
        """, (str(yr), f"{mo:02d}"))
        row = {"month": target.strftime("%b %Y")}
        for _, r in data.iterrows():
            row[r["status"]] = r["cnt"]
        rows.append(row)
    return pd.DataFrame(rows).fillna(0)


def get_weekly_off_distribution() -> pd.DataFrame:
    return _df("""
        SELECT weekly_off AS day, COUNT(*) AS count
        FROM employees WHERE is_active=1
        GROUP BY weekly_off
    """)


def get_absenteeism_by_dept() -> pd.DataFrame:
    return _df("""
        SELECT d.name AS department,
               SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END) AS absent_days,
               COUNT(a.id) AS total_days,
               ROUND(100.0*SUM(CASE WHEN a.status='Absent' THEN 1 ELSE 0 END)/MAX(COUNT(a.id),1),1) AS rate
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        JOIN departments d ON e.department_id = d.id
        GROUP BY d.name ORDER BY rate DESC
    """)


# ── Shift rotation ────────────────────────────────────────────────────────────

def rotate_shift(emp_db_id: int, new_shift_name: str):
    conn = get_conn()
    shift_id = conn.execute("SELECT id FROM shifts WHERE name=?", (new_shift_name,)).fetchone()[0]
    conn.execute("UPDATE employees SET shift_id=? WHERE id=?", (shift_id, emp_db_id))
    conn.execute("""
        INSERT INTO shift_rotations(employee_id,shift_id,from_date)
        VALUES(?,?,date('now'))
    """, (emp_db_id, shift_id))
    conn.commit()
    conn.close()


def _normalize_shift_group(shift_name: str) -> str:
    if not shift_name:
        return "General"
    name = str(shift_name).strip().lower()
    if name in {"general", "general shift", "g", "gen"}:
        return "General"
    if name in {"morning", "morning shift", "m", "a", "a shift"}:
        return "A"
    if name in {"evening", "evening shift", "e", "b", "b shift"}:
        return "B"
    if name in {"night", "night shift", "n"}:
        return "Night"
    return str(shift_name).strip().title()


def distribute_weekly_off_assignments(df: pd.DataFrame) -> list[dict]:
    """Spread weekly-off days within each department/shift group so they do not collide."""
    if df.empty:
        return []

    day_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    results = []
    work_df = df.copy()
    work_df["shift_group"] = work_df["shift"].apply(_normalize_shift_group)

    for _, group_df in work_df.groupby(["department", "shift_group"], sort=True):
        used_days = set()
        ordered_rows = group_df.sort_values(["name", "emp_id"], kind="mergesort")
        for _, row in ordered_rows.iterrows():
            preferred_day = row.get("weekly_off") or "Sunday"
            if preferred_day in day_order and preferred_day not in used_days:
                selected_day = preferred_day
            else:
                selected_day = next((day for day in day_order if day not in used_days), day_order[0])
            used_days.add(selected_day)
            results.append({"id": int(row["id"]), "weekly_off": selected_day})

    return results


def update_weekly_off(emp_db_id: int, new_off_day: str):
    _run("UPDATE employees SET weekly_off=? WHERE id=?", (new_off_day, emp_db_id))