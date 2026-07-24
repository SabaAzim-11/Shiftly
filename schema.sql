-- ============================================================
--  ShiftSync AI – SQLite Database Schema
--  File: schema.sql
--  Run:  sqlite3 shiftsync.db < schema.sql
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ── 1. Departments ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT    UNIQUE NOT NULL,
    head      TEXT,
    location  TEXT
);

-- ── 2. Shifts ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shifts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    UNIQUE NOT NULL,        -- General | Morning | Evening | Night
    start_time TEXT    NOT NULL,               -- e.g. "09:00"
    end_time   TEXT    NOT NULL,               -- e.g. "18:00"
    color_code TEXT    DEFAULT '#4f8ef7'
);

-- ── 3. Employees ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id          TEXT    UNIQUE NOT NULL,   -- e.g. EMP-001
    name            TEXT    NOT NULL,
    email           TEXT    UNIQUE NOT NULL,
    mobile          TEXT,
    department_id   INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    designation     TEXT,
    manager         TEXT,
    location        TEXT,
    joining_date    TEXT,                      -- ISO date: 2024-01-15
    employment_type TEXT    DEFAULT 'Full-time',
    shift_id        INTEGER REFERENCES shifts(id) ON DELETE SET NULL,
    weekly_off      TEXT    DEFAULT 'Sunday',  -- Day name
    weekly_off_type TEXT    DEFAULT 'Fixed',   -- Fixed | Rotating
    is_active       INTEGER DEFAULT 1,         -- 1 = active, 0 = deactivated
    created_at      TEXT    DEFAULT (date('now'))
);

-- ── 4. Users (Authentication) ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT    UNIQUE NOT NULL,
    password    TEXT    NOT NULL,              -- store hashed in production!
    role        TEXT    DEFAULT 'Employee',    -- Admin | HR | Manager | Employee
    employee_id INTEGER REFERENCES employees(id) ON DELETE SET NULL,
    is_active   INTEGER DEFAULT 1
);

-- ── 5. Attendance ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attendance (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    att_date    TEXT    NOT NULL,              -- ISO date: 2024-06-24
    status      TEXT    NOT NULL,             
    --  Present | Absent | Leave | Late | Half Day | Weekly Off | Holiday | WFH
    in_time     TEXT,                          -- e.g. "09:05"
    out_time    TEXT,                          -- e.g. "18:15"
    remarks     TEXT,
    UNIQUE (employee_id, att_date)             -- one record per employee per day
);

-- ── 6. Leave Types ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leave_types (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    UNIQUE NOT NULL,    -- Casual Leave | Sick Leave | etc.
    code          TEXT    UNIQUE NOT NULL,    -- CL | SL | EL | CO | WFH
    max_days      INTEGER DEFAULT 10,
    carry_forward INTEGER DEFAULT 0          -- 1 = unused days carry to next year
);

-- ── 7. Leave Balances ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leave_balances (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id   INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    leave_type_id INTEGER NOT NULL REFERENCES leave_types(id) ON DELETE CASCADE,
    year          INTEGER NOT NULL,
    allocated     INTEGER DEFAULT 0,
    used          INTEGER DEFAULT 0,
    UNIQUE (employee_id, leave_type_id, year)
);

-- ── 8. Leave Requests ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS leave_requests (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id   INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    leave_type_id INTEGER NOT NULL REFERENCES leave_types(id),
    from_date     TEXT    NOT NULL,            -- ISO date
    to_date       TEXT    NOT NULL,            -- ISO date
    days          INTEGER NOT NULL,
    reason        TEXT,
    status        TEXT    DEFAULT 'Pending',   -- Pending | Approved | Rejected
    approved_by   INTEGER REFERENCES employees(id),
    applied_on    TEXT    DEFAULT (date('now')),
    action_on     TEXT                         -- date of approval/rejection
);

-- ── 9. Holidays ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS holidays (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    holiday_date  TEXT    NOT NULL,            -- ISO date: 2025-01-26
    type          TEXT    DEFAULT 'National',  -- National | Optional | Restricted
    year          INTEGER
);

-- ── 10. Shift Rotation Log ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS shift_rotations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    shift_id    INTEGER NOT NULL REFERENCES shifts(id),
    from_date   TEXT,
    to_date     TEXT,
    created_at  TEXT    DEFAULT (date('now'))
);

-- ============================================================
--  INDEXES for query performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_att_date        ON attendance (att_date);
CREATE INDEX IF NOT EXISTS idx_att_emp         ON attendance (employee_id);
CREATE INDEX IF NOT EXISTS idx_att_emp_date    ON attendance (employee_id, att_date);
CREATE INDEX IF NOT EXISTS idx_emp_dept        ON employees  (department_id);
CREATE INDEX IF NOT EXISTS idx_emp_shift       ON employees  (shift_id);
CREATE INDEX IF NOT EXISTS idx_emp_active      ON employees  (is_active);
CREATE INDEX IF NOT EXISTS idx_lr_status       ON leave_requests (status);
CREATE INDEX IF NOT EXISTS idx_lr_emp          ON leave_requests (employee_id);
CREATE INDEX IF NOT EXISTS idx_lb_emp_year     ON leave_balances (employee_id, year);

-- ============================================================
--  SEED DATA – Reference / Lookup Tables
-- ============================================================

INSERT OR IGNORE INTO departments (name, head, location) VALUES
    ('Production', 'Sneha Gupta',  'Plant Floor'),
    ('IT',         'Nisha Varma',  'Head Office'),
    ('HR',         'Sneha Gupta',  'Head Office'),
    ('Finance',    'Kiran Bhatia', 'Head Office'),
    ('Security',   'Deepak Joshi', 'Gate 1'),
    ('Logistics',  'Suresh Babu',  'Warehouse');

INSERT OR IGNORE INTO shifts (name, start_time, end_time, color_code) VALUES
    ('General', '09:00', '18:00', '#4f8ef7'),
    ('Morning', '06:00', '14:00', '#fbbf24'),
    ('Evening', '14:00', '22:00', '#a78bfa'),
    ('Night',   '22:00', '06:00', '#6b7494');

INSERT OR IGNORE INTO leave_types (name, code, max_days, carry_forward) VALUES
    ('Casual Leave',   'CL',  12, 0),
    ('Sick Leave',     'SL',  10, 0),
    ('Earned Leave',   'EL',  20, 1),
    ('Comp Off',       'CO',   5, 0),
    ('Work From Home', 'WFH', 15, 0);

INSERT OR IGNORE INTO holidays (name, holiday_date, type, year) VALUES
    ('Republic Day',     '2025-01-26', 'National', 2025),
    ('Holi',             '2025-03-14', 'National', 2025),
    ('Eid ul-Fitr',      '2025-03-31', 'National', 2025),
    ('Ambedkar Jayanti', '2025-04-14', 'National', 2025),
    ('Good Friday',      '2025-04-18', 'National', 2025),
    ('Labour Day',       '2025-05-01', 'National', 2025),
    ('Eid al-Adha',      '2025-06-25', 'National', 2025),
    ('Independence Day', '2025-08-15', '  National', 2025),
    ('Janmashtami',      '2025-08-16', 'Optional', 2025),
    ('Gandhi Jayanti',   '2025-10-02', 'National', 2025),
    ('Diwali',           '2025-10-20', 'National', 2025),
    ('Christmas',        '2025-12-25', 'National', 2025);

-- ============================================================
--  END OF SCHEMA
-- ============================================================