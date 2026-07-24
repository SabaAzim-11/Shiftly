"""
ShiftSync AI – Database layer
SQLite for development, PostgreSQL-ready via SQLAlchemy
"""

import sqlite3
import os
from datetime import date, timedelta
import random

DB_PATH = os.getenv("SHIFTSYNC_DB", "shiftsync.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    """Create all tables and seed sample data if empty."""
    conn = get_conn()
    c = conn.cursor()

    # ── Departments ──────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT UNIQUE NOT NULL,
            head     TEXT,
            location TEXT
        )
    """)

    # ── Shifts ───────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT UNIQUE NOT NULL,
            start_time TEXT NOT NULL,
            end_time   TEXT NOT NULL,
            color_code TEXT DEFAULT '#4f8ef7'
        )
    """)

    # ── Employees ─────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id          TEXT UNIQUE NOT NULL,
            name            TEXT NOT NULL,
            email           TEXT UNIQUE NOT NULL,
            mobile          TEXT,
            department_id   INTEGER REFERENCES departments(id),
            designation     TEXT,
            manager         TEXT,
            location        TEXT,
            joining_date    TEXT,
            employment_type TEXT DEFAULT 'Full-time',
            shift_id        INTEGER REFERENCES shifts(id),
            weekly_off      TEXT DEFAULT 'Sunday',
            weekly_off_type TEXT DEFAULT 'Fixed',
            is_active       INTEGER DEFAULT 1,
            created_at      TEXT DEFAULT (date('now'))
        )
    """)

    # ── Users (auth) ──────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            role        TEXT DEFAULT 'Employee',
            employee_id INTEGER REFERENCES employees(id),
            is_active   INTEGER DEFAULT 1
        )
    """)

    # ── Attendance ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER REFERENCES employees(id),
            att_date    TEXT NOT NULL,
            status      TEXT NOT NULL,
            in_time     TEXT,
            out_time    TEXT,
            remarks     TEXT,
            UNIQUE(employee_id, att_date)
        )
    """)

    # ── Leave types ───────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS leave_types (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT UNIQUE NOT NULL,
            code         TEXT UNIQUE NOT NULL,
            max_days     INTEGER DEFAULT 10,
            carry_forward INTEGER DEFAULT 0
        )
    """)

    # ── Leave balances ────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS leave_balances (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER REFERENCES employees(id),
            leave_type_id INTEGER REFERENCES leave_types(id),
            year        INTEGER,
            allocated   INTEGER DEFAULT 0,
            used        INTEGER DEFAULT 0,
            UNIQUE(employee_id, leave_type_id, year)
        )
    """)

    # ── Leave requests ────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id     INTEGER REFERENCES employees(id),
            leave_type_id   INTEGER REFERENCES leave_types(id),
            from_date       TEXT NOT NULL,
            to_date         TEXT NOT NULL,
            days            INTEGER NOT NULL,
            reason          TEXT,
            status          TEXT DEFAULT 'Pending',
            approved_by     INTEGER REFERENCES employees(id),
            applied_on      TEXT DEFAULT (date('now')),
            action_on       TEXT
        )
    """)

    # ── Holidays ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS holidays (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            holiday_date TEXT NOT NULL,
            type        TEXT DEFAULT 'National',
            year        INTEGER
        )
    """)

    # ── Shift rotation log ────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS shift_rotations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER REFERENCES employees(id),
            shift_id    INTEGER REFERENCES shifts(id),
            from_date   TEXT,
            to_date     TEXT,
            created_at  TEXT DEFAULT (date('now'))
        )
    """)

    conn.commit()
    _seed_data(conn)
    conn.close()


def _seed_data(conn):
    c = conn.cursor()

    # Skip if already seeded
    if c.execute("SELECT COUNT(*) FROM employees").fetchone()[0] > 0:
        return

    # Departments
    depts = [
        ("Production", "Sneha Gupta", "Plant Floor"),
        ("IT", "Nisha Varma", "Head Office"),
        ("HR", "Sneha Gupta", "Head Office"),
        ("Finance", "Kiran Bhatia", "Head Office"),
        ("Security", "Deepak Joshi", "Gate 1"),
        ("Logistics", "Suresh Babu", "Warehouse"),
    ]
    c.executemany("INSERT INTO departments(name,head,location) VALUES(?,?,?)", depts)

    # Shifts
    shifts_data = [
        ("General", "09:00", "18:00", "#4f8ef7"),
        ("A",       "06:00", "14:00", "#fbbf24"),
        ("B",       "14:00", "22:00", "#a78bfa"),
        ("Night",   "22:00", "06:00", "#6b7494"),
    ]
    c.executemany(
        "INSERT INTO shifts(name,start_time,end_time,color_code) VALUES(?,?,?,?)",
        shifts_data
    )

    # Leave types
    leave_types = [
        ("Casual Leave",    "CL",  12, 0),
        ("Sick Leave",      "SL",  10, 0),
        ("Earned Leave",    "EL",  20, 1),
        ("Comp Off",        "CO",   5, 0),
        ("Work From Home",  "WFH", 15, 0),
    ]
    c.executemany(
        "INSERT INTO leave_types(name,code,max_days,carry_forward) VALUES(?,?,?,?)",
        leave_types
    )

    # Holidays 2025
    holidays = [
        ("Republic Day",       "2025-01-26", "National", 2025),
        ("Holi",               "2025-03-14", "National", 2025),
        ("Good Friday",        "2025-04-18", "National", 2025),
        ("Eid ul-Fitr",        "2025-03-31", "National", 2025),
        ("Ambedkar Jayanti",   "2025-04-14", "National", 2025),
        ("Labour Day",         "2025-05-01", "National", 2025),
        ("Eid al-Adha",        "2025-06-25", "National", 2025),
        ("Independence Day",   "2025-08-15", "National", 2025),
        ("Janmashtami",        "2025-08-16", "Optional", 2025),
        ("Gandhi Jayanti",     "2025-10-02", "National", 2025),
        ("Diwali",             "2025-10-20", "National", 2025),
        ("Christmas",          "2025-12-25", "National", 2025),
    ]
    c.executemany(
        "INSERT INTO holidays(name,holiday_date,type,year) VALUES(?,?,?,?)",
        holidays
    )

    # Employees
    departments = [
        ("Production", "Sneha Gupta", "Plant"),
        ("IT",         "Nisha Varma",  "HO"),
        ("HR",         "Sunita Patel", "HO"),
        ("Finance",    "Kiran Bhatia", "HO"),
        ("Security",   "Deepak Joshi", "Gate1"),
        ("Logistics",  "Suresh Babu", "WH"),
    ]

    names = [
        "Aarav Singh", "Ananya Sharma", "Rahul Mehta", "Priya Patel", "Amit Verma",
        "Sneha Joshi", "Deepak Kumar", "Neha Reddy", "Karan Gupta", "Isha Khan",
        "Rohit Nair", "Sara Kapoor", "Vikram Iyer", "Maya Menon", "Aditya Rao",
        "Anjali Desai", "Rohan Bhatia", "Kavita Lal", "Siddharth Nanda", "Meera Shah",
        "Arjun Dixit", "Nidhi Sen", "Kunal Paul", "Divya Shah", "Rajiv Nanda",
        "Aishwarya Bose", "Manish Sinha", "Priyanka Ghosh", "Sameer Malik", "Mira Thomas",
        "Yash Khanna", "Ishita Chawla", "Ankur Joshi", "Rhea Verma", "Vivek Kumar",
        "Simran Kaur", "Tanya Roy", "Neeraj Singh", "Harsha Yadav", "Pooja Jain",
        "Suresh Rao", "Neha Chatterjee", "Kabir Reddy", "Ritika Nair", "Aadil Khan",
        "Lina Das", "Tarun Gupta", "Esha Sharma", "Varun Pillai", "Aanya Sharma",
        "Nikhil Bansal", "Ritu Sharma", "Aravind Joshi", "Priya Nair", "Sana Kapoor",
        "Lokesh Singh", "Aditi Mehra", "Naveen Kaur", "Radha Iyer", "Mohit Sharma",
        "Priyanka Joshi", "Sahil Malhotra", "Monika Chawla", "Pavan Singh", "Gita Rao",
    ]

    general_roles = {
        "Production": ["Production Engineer", "Quality Analyst", "Maintenance Coordinator", "Assembly Specialist", "Process Lead"],
        "IT": ["Software Engineer", "Systems Analyst", "IT Support", "Network Administrator", "Database Administrator"],
        "HR": ["HR Generalist", "Recruitment Specialist", "Payroll Coordinator", "Learning & Development Specialist"],
        "Finance": ["Finance Analyst", "Accounts Executive", "Payroll Specialist", "Treasury Associate"],
        "Security": ["Security Supervisor", "Access Control Officer", "Facility Safety Officer"],
        "Logistics": ["Logistics Coordinator", "Warehouse Supervisor", "Inventory Specialist", "Dispatch Planner"],
    }

    shift_roles = {
        "Production": ["Line Operator", "Process Technician", "Maintenance Technician", "Shift Supervisor"],
        "Security": ["Security Guard", "Patrol Officer", "Control Room Operator", "Gate Supervisor"],
        "Logistics": ["Forklift Operator", "Warehouse Associate", "Material Handler", "Dispatch Coordinator"],
        "IT": ["Data Center Technician", "Shift Support Engineer"],
    }

    employees = []
    off_days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    rotating_shifts = ["A", "B", "Night"]
    shift_dept_cycle = ["Production"] * 5 + ["Logistics"] * 2 + ["Security"] * 2 + ["IT"]

    for idx in range(1, 301):
        emp_id = f"EMP-{idx:03d}"
        name = names[(idx - 1) % len(names)]
        email = f"{name.lower().replace(' ', '.')}.{idx}@shiftsync.in"
        mobile = f"9{idx:09d}"
        dept, manager, loc = departments[(idx - 1) % len(departments)]
        role = general_roles[dept][(idx - 1) % len(general_roles[dept])]
        joining = f"20{18 + ((idx - 1) % 7)}-{(idx - 1) % 12 + 1:02d}-{(idx - 1) % 28 + 1:02d}"
        employees.append((emp_id, name, email, mobile, dept, role, manager, loc,
                          joining, "Full-time", "General", "Sunday", "Fixed"))

    for idx in range(301, 501):
        emp_id = f"EMP-{idx:03d}"
        name = names[(idx - 1) % len(names)]
        email = f"{name.lower().replace(' ', '.')}.{idx}@shiftsync.in"
        mobile = f"9{idx:09d}"
        dept = shift_dept_cycle[(idx - 301) % len(shift_dept_cycle)]
        manager = next(mgr for d, mgr, _ in departments if d == dept)
        loc = next(loc for d, _, loc in departments if d == dept)
        role = shift_roles[dept][(idx - 301) % len(shift_roles[dept])]
        joining = f"20{18 + ((idx - 1) % 7)}-{(idx - 1) % 12 + 1:02d}-{(idx - 1) % 28 + 1:02d}"
        shift_name = rotating_shifts[(idx - 301) % len(rotating_shifts)]
        weekly_off = off_days[1 + ((idx - 301) % 6)]
        employees.append((emp_id, name, email, mobile, dept, role, manager, loc,
                          joining, "Full-time", shift_name, weekly_off, "Rotating"))

    for emp in employees:
        emp_id, name, email, mobile, dept, desig, manager, loc, join, etype, shift_name, off, off_type = emp
        dept_id = c.execute("SELECT id FROM departments WHERE name=?", (dept,)).fetchone()[0]
        shift_id = c.execute("SELECT id FROM shifts WHERE name=?", (shift_name,)).fetchone()[0]
        c.execute("""
            INSERT INTO employees(emp_id,name,email,mobile,department_id,designation,
                manager,location,joining_date,employment_type,shift_id,weekly_off,weekly_off_type)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (emp_id, name, email, mobile, dept_id, desig, manager, loc, join,
                etype, shift_id, off, off_type))

    # Admin user
    c.execute("""
        INSERT INTO users(username,password,role,employee_id)
        VALUES('admin','admin123','Admin',10)
    """)
    c.execute("""
        INSERT INTO users(username,password,role,employee_id)
        VALUES('hr','hr123','HR',10)
    """)

    # Seed attendance for current month
    today = date.today()
    statuses = ["Present","Present","Present","Present","Absent","Leave","Present"]
    emp_rows = c.execute("SELECT id, weekly_off FROM employees").fetchall()
    for emp_id, weekly_off in emp_rows:
        for delta in range(24):
            d = today - timedelta(days=23 - delta)
            if d.strftime('%A') == weekly_off:
                status = "Weekly Off"
            else:
                status = random.choices(
                    ["Present","Absent","Leave"],
                    weights=[80, 10, 10]
                )[0]
            in_time = f"0{random.randint(6,9)}:{random.randint(0,59):02d}" if status == "Present" else None
            try:
                c.execute("""
                    INSERT OR IGNORE INTO attendance(employee_id,att_date,status,in_time)
                    VALUES(?,?,?,?)
                """, (emp_id, d.isoformat(), status, in_time))
            except Exception:
                pass

    # Seed leave balances
    year = today.year
    lt_ids = [r[0] for r in c.execute("SELECT id FROM leave_types").fetchall()]
    lt_days = {r[0]: r[1] for r in c.execute("SELECT id,max_days FROM leave_types").fetchall()}
    emp_ids = [r[0] for r in c.execute("SELECT id FROM employees").fetchall()]
    for emp_id in emp_ids:
        for lt_id in lt_ids:
            allocated = lt_days[lt_id]
            used = random.randint(0, min(3, allocated))
            c.execute("""
                INSERT OR IGNORE INTO leave_balances(employee_id,leave_type_id,year,allocated,used)
                VALUES(?,?,?,?,?)
            """, (emp_id, lt_id, year, allocated, used))

    # Seed leave requests
    leave_reqs = [
        (3,  1, "2025-06-18","2025-06-20", 3, "Sick",          "Approved"),
        (12, 2, "2025-06-21","2025-06-22", 2, "Personal work", "Approved"),
        (9,  3, "2025-06-24","2025-06-25", 2, "Travel",        "Pending"),
        (2,  5, "2025-06-25","2025-06-25", 1, "WFH",           "Pending"),
        (4,  4, "2025-06-27","2025-06-27", 1, "Comp off",      "Pending"),
    ]
    for r in leave_reqs:
        c.execute("""
            INSERT INTO leave_requests(employee_id,leave_type_id,from_date,to_date,days,reason,status)
            VALUES(?,?,?,?,?,?,?)
        """, r)

    conn.commit()