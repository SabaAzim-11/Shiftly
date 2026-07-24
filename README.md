# ⚡ ShiftSync AI — Smart Workforce & Shift Management Platform

A production-ready AI-powered Workforce Management System built with Python, Streamlit, SQLite, Plotly, and the Anthropic Claude API.

---

## 📁 Project Structure

```
shiftsync/
│
├── app.py                        ← Main entry point (run this)
├── database.py                   ← DB init, schema creation, seed data
├── auth.py                       ← Login / logout / session management
├── schema.sql                    ← Standalone SQL schema file
├── requirements.txt              ← All Python dependencies
├── .gitignore
│
├── pages/
│   ├── dashboard.py              ← Executive dashboard
│   ├── employees.py              ← Employee management (CRUD + bulk import)
│   ├── shifts.py                 ← Shift management & rotation engine
│   ├── weeklyoff.py              ← Weekly off assignment
│   ├── attendance.py             ← Daily attendance, monthly summary
│   ├── leaves.py                 ← Leave requests, approvals, balances
│   ├── analytics.py              ← Charts and AI insights
│   ├── calendar.py               ← Personal calendar view
│   ├── ai_assistant.py           ← Claude AI chatbot (live DB context)
│   └── reports.py                ← PDF & Excel export
│
├── components/
│   └── ui.py                     ← Shared CSS, KPI cards, badges, helpers
│
├── utils/
│   ├── data.py                   ← All database queries (data access layer)
│   ├── charts.py                 ← Plotly dark-theme chart builders
│   └── reports.py                ← PDF (ReportLab) + Excel (OpenPyXL) generation
│
└── .streamlit/
    ├── config.toml               ← Dark theme + server settings
    └── secrets.toml              ← API keys (NOT committed to Git)
```

---

## 🚀 Step-by-Step Setup in VS Code

### STEP 1 — Install Prerequisites

Make sure you have these installed on your machine:

| Tool | Version | Download |
|------|---------|----------|
| Python | 3.10+ | https://python.org/downloads |
| VS Code | Latest | https://code.visualstudio.com |
| Git | Latest | https://git-scm.com |

Verify installs by opening a terminal and running:
```bash
python --version     # should show Python 3.10+
git --version        # should show git version 2.x
```

---

### STEP 2 — Clone Your GitHub Repository

```bash
# In your terminal (or VS Code terminal: Ctrl+` )
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Navigate into the project folder
cd YOUR_REPO_NAME
```

**Or if starting fresh (new repo):**
```bash
# Create a new folder and initialise git
mkdir shiftsync
cd shiftsync
git init
```

---

### STEP 3 — Open in VS Code

```bash
# While inside the project folder, run:
code .
```

This opens the entire project in VS Code.

---

### STEP 4 — Create a Virtual Environment

In the VS Code terminal (`Ctrl + `` ` ``):

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` appear at the start of your terminal prompt.

---

### STEP 5 — Install All Dependencies

```bash
pip install -r requirements.txt
```

This installs: Streamlit, Pandas, Plotly, Anthropic SDK, OpenPyXL, ReportLab, and all other dependencies.

To verify:
```bash
pip list
```

---

### STEP 6 — Add Your Anthropic API Key

**Option A — Using `.streamlit/secrets.toml` (recommended for local dev):**

1. Create the `.streamlit/` folder if it doesn't exist
2. Create a file called `secrets.toml` inside it
3. Add this content:

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-YOUR_ACTUAL_KEY_HERE"
```

Get your API key at: https://console.anthropic.com/settings/api-keys

**Option B — Using a `.env` file:**

Create a file called `.env` in the project root:
```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_ACTUAL_KEY_HERE
```

Then install python-dotenv (already in requirements.txt) and load it at the top of `app.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

**Option C — System environment variable (for production):**
```bash
# Windows
set ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY

# Mac/Linux
export ANTHROPIC_API_KEY=sk-ant-api03-YOUR_KEY
```

> ⚠️ **IMPORTANT:** Never commit `secrets.toml` or `.env` to GitHub. They are already in `.gitignore`.

---

### STEP 7 — (Optional) Create the SQLite Database Manually

The app creates the database automatically on first run. But if you want to create it manually using the SQL schema:

```bash
# Install sqlite3 command line (usually pre-installed)
sqlite3 shiftsync.db < schema.sql
```

Check it worked:
```bash
sqlite3 shiftsync.db
.tables       # should list all 10 tables
.quit
```

---

### STEP 8 — Run the App

```bash
streamlit run app.py
```

The app will open automatically at: **http://localhost:8501**

**Login credentials (seeded automatically):**
| Username | Password | Role |
|----------|----------|------|
| `admin`  | `admin123` | Admin |
| `hr`     | `hr123`    | HR |

---

### STEP 9 — Recommended VS Code Extensions

Install these from the Extensions panel (`Ctrl+Shift+X`):

| Extension | Purpose |
|-----------|---------|
| **Python** (Microsoft) | Python language support |
| **Pylance** | Fast type checking and autocomplete |
| **SQLite Viewer** | Browse your `.db` file visually |
| **GitLens** | Enhanced Git integration |
| **Thunder Client** | Test APIs directly in VS Code |

---

### STEP 10 — Push to GitHub

```bash
# Stage all files
git add .

# Commit
git commit -m "Initial commit: ShiftSync AI workforce platform"

# Add your GitHub remote (replace with your URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push
git push -u origin main
```

---

## 🔧 Wiring Up the 3 Production Components

### 1. SQLite → Python/Streamlit Backend

The app already uses SQLite via `database.py`. Data flows like this:

```
User clicks button in Streamlit UI
        ↓
pages/employees.py calls utils/data.py function
        ↓
utils/data.py runs SQL query via sqlite3
        ↓
Returns pandas DataFrame
        ↓
Streamlit renders it as table/chart
```

No extra wiring needed — it works out of the box.

**To switch to PostgreSQL (production):**

1. Install: `pip install sqlalchemy psycopg2-binary`
2. In `database.py`, replace `sqlite3.connect(DB_PATH)` with:
```python
from sqlalchemy import create_engine
engine = create_engine(os.getenv("DATABASE_URL"))
conn = engine.connect()
```

---

### 2. Anthropic API Key — Secure Backend Proxy

The AI Assistant (`pages/ai_assistant.py`) calls the Anthropic API **server-side** via Python — not from the browser. This is the correct, secure approach.

**How it works:**
```
User types question in Streamlit
        ↓
ai_assistant.py collects live DB data into a context string
        ↓
_call_anthropic() reads key from st.secrets or env variable
        ↓
Python sends POST to api.anthropic.com/v1/messages
        ↓
Response returned and displayed in chat UI
```

**Key reading priority (in `_call_anthropic`):**
```python
api_key = (
    os.getenv("ANTHROPIC_API_KEY") or      # 1. Environment variable
    st.secrets.get("ANTHROPIC_API_KEY", "")  # 2. .streamlit/secrets.toml
)
```

The API key is **never exposed to the browser** — it stays on the server.

---

### 3. ReportLab (PDF) + OpenPyXL (Excel) Reports

Both libraries are already integrated in `utils/reports.py`.

**How PDF generation works:**
```
User clicks "Generate Report" in pages/reports.py
        ↓
Fetches data from DB as pandas DataFrame
        ↓
generate_pdf_report(df, title) in utils/reports.py
        ↓
ReportLab builds styled PDF in memory (BytesIO)
        ↓
st.download_button() delivers file to user's browser
```

**How Excel generation works:**
```
Same flow, but generate_excel_report() uses OpenPyXL
Creates dark-themed .xlsx with formatted headers and alternating row colors
```

No server storage needed — files are generated in memory and streamed directly to the browser.

---

## 🌐 Deploy to Streamlit Cloud (Free)

1. Push your code to GitHub (Step 10 above)
2. Go to https://share.streamlit.io
3. Click **"New app"**
4. Select your GitHub repo, branch `main`, file `app.py`
5. Click **"Advanced settings"** → paste your secrets:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-api03-YOUR_KEY"
   ```
6. Click **"Deploy"**

Your app will be live at: `https://YOUR_APP.streamlit.app`

---

## 🔑 Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes (for AI) | Your Anthropic API key |
| `SHIFTSYNC_DB` | No | Custom path for SQLite file (default: `shiftsync.db`) |
| `DATABASE_URL` | No | PostgreSQL URL for production |

---

## 🛠 Common Issues & Fixes

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: streamlit` | Run `pip install -r requirements.txt` |
| `ModuleNotFoundError: anthropic` | Run `pip install anthropic` |
| App opens but shows white screen | Make sure `(venv)` is active |
| AI says "API key not configured" | Add key to `.streamlit/secrets.toml` |
| Database errors on first run | Delete `shiftsync.db` and restart — it rebuilds automatically |
| Port 8501 already in use | Run `streamlit run app.py --server.port 8502` |
| Excel download fails | Run `pip install openpyxl` |
| PDF download fails | Run `pip install reportlab` |

---

## 📄 Demo Credentials

| Username | Password | Role | Access |
|----------|----------|------|--------|
| `admin` | `admin123` | Admin | Full access |
| `hr` | `hr123` | HR | HR + reports |

---

*Built with ❤ using Streamlit, SQLite, Plotly, and Claude AI*