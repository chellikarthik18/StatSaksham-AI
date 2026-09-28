# STATSAKHAM AI — Skill Intelligence & Learning Platform

An AI-enabled skill intelligence and learning platform for official statistics
workforce learning: FastAPI + SQLAlchemy + MySQL backend, with the original
Admin Dashboard and Employee Learning Portal frontends (HTML/CSS/Bootstrap/JS/
Chart.js) wired to real, MySQL-backed data.

```
StatSaksham-AI/
├── backend/                 FastAPI application, models, routers, seed script
├── frontend/
│   ├── STATSAKHAM-Frontend-f1/Admin DashBoard-STATSAKHAM-AI/   Admin dashboard (static)
│   └── employee_learning_frontend/                              Employee portal (static)
├── database/create_database.sql
├── backend/.env.example
└── README.md   (this file)
```

The two frontends are plain static sites (no build step) — open them with a
static file server (e.g. VS Code "Live Server", or Python's http.server) on
`http://localhost:5500` / `5501`. The backend runs separately on
`http://127.0.0.1:8000`.

---

## 1. Prerequisites

- Python 3.11+ and `pip`
- MySQL 8.x server running locally (or reachable)
- A way to serve static files, e.g. VS Code's "Live Server" extension, or
  Python's built-in `http.server`

---

## 2. Create the MySQL database (Windows PowerShell / CMD)

```powershell
mysql -u root -p < database\create_database.sql
```

(Or open the file's contents in MySQL Workbench and run it.) This creates an
empty `statsaksham` database. All tables are created automatically by the
backend/seed script — you do not need to write any `CREATE TABLE` statements
yourself.

---

## 3. Backend setup (Windows PowerShell)

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Now edit `.env` and set your real MySQL password:

```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=statsaksham
JWT_SECRET_KEY=some-long-random-string
```

Seed the database (safe to re-run any time):

```powershell
python seed.py
```

Start the API:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health

## 3a. Windows CMD equivalent

```bat
cd backend
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
python seed.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 4. Frontend setup

The frontend already points at `http://127.0.0.1:8000/api` (see
`assets/app.js` and `employee_learning_frontend/script.js`). Serve each
frontend as static files — for example with VS Code Live Server, or:

```powershell
# Admin dashboard, from the project root
cd "frontend\STATSAKHAM-Frontend-f1\Admin DashBoard-STATSAKHAM-AI"
python -m http.server 5500
# open http://localhost:5500/login.html

# Employee portal, in a second terminal
cd frontend\employee_learning_frontend
python -m http.server 5501
# open http://localhost:5501/index.html
```

The backend's CORS is pre-configured to allow `localhost:5500` and
`localhost:5501` (see `backend/.env.example` → `CORS_ORIGINS`). If you serve
the frontends on different ports, add them to `CORS_ORIGINS` in `.env` and
restart the backend.

---

## 5. Demo accounts (created by `seed.py`)

| Role     | Login                          | Password      |
|----------|---------------------------------|---------------|
| Admin    | admin@statsaksham.gov.in       | Admin@123     |
| Trainer  | trainer@statsaksham.gov.in     | Trainer@123   |
| Employee | employee@statsaksham.gov.in    | Employee@123  |

Admin and Trainer accounts log in through the Admin Dashboard
(`login.html`). The Employee account (and any employee who signs up) logs in
through the Employee Learning Portal (`index.html`).

`python seed.py` is idempotent — running it again will not create duplicates;
it only fills in anything missing.

---

## 6. What's implemented

**Auth & users** — JWT login/logout, bcrypt password hashing (via passlib),
role-based authorization (`admin`, `trainer`, `employee`), `/api/auth/me`,
employee self-signup.

**Admin** — dashboard KPIs/charts, employee CRUD + search/filter/pagination +
CSV export, departments, competency profiles, competency framework, skill-gap
analysis ("Run Analysis" recomputes real gaps from stored competency data),
emerging skills (+ a deterministic "predict" action), iGOT course catalogue
CRUD and a mock-catalogue sync, NSSTA/TPAC programme CRUD and mock sync,
learning-path creation/assignment + an AI-generation action driven by each
employee's actual skill gaps, learning-material upload (PDF/DOCX/PPTX/TXT)
with best-effort text extraction, an AI quiz generator with a **fully local,
deterministic MCQ generator** (no external API key required) plus an optional
hook to a real LLM if you configure one via environment variables, a question
bank (edit/delete), assessment/workforce/training analytics, reports,
notifications, and persisted settings.

**Employee portal** — profile, skill self-assessment, a 10-question
diagnostic assessment that updates the employee's competency profile and
skill-gap snapshot, AI course recommendations driven by real skill gaps,
learning-path progress tracking (enroll, complete modules, auto-complete),
an on-demand AI practice quiz, notifications, and a competency-growth view.

**Mock vs. live integrations** — the iGOT Karmayogi and NSSTA/TPAC
"sync" actions upsert a small bundled demo catalogue
(`backend/app/seed_data.py`). This project does **not** claim a live
government API integration, since no real credentials or API were supplied;
the sync endpoints say so explicitly in their response.

**AI without a paid API key** — the quiz generator and diagnostic engine work
entirely offline using a deterministic algorithm (a curated topic question
bank, plus fill-in-the-blank questions generated from uploaded material text).
If you want to plug in a real LLM, set `LLM_PROVIDER`, `LLM_API_KEY`, and
`LLM_MODEL` in `backend/.env` — the code will try the LLM first and silently
fall back to the deterministic generator on any error, so nothing breaks if
you don't configure one.

---

## 7. Notes, honesty about verification, and known limitations

- This backend was built and syntax-checked (`python -m py_compile`) and its
  JavaScript was checked with `node --check`, but it was **not** executed
  end-to-end against a live MySQL server in the environment that produced
  this code, because that sandbox had no network access and no MySQL server
  available to install. Please run through the steps above and open an issue
  in your own tracker if you hit an error — the most likely causes for a
  first-run hiccup are a MySQL connection string mismatch in `.env` or a
  package version conflict; both are easy to fix by checking `.env` and
  `pip show <package>`.
- `bcrypt` is pinned to `4.0.1` for compatibility with `passlib[bcrypt]==1.7.4`
  (newer `bcrypt` releases changed an internal attribute that passlib's
  version-detection code relies on).
- Deleting an employee, course, or programme also removes rows that reference
  it (skill-gap snapshots, enrolments, learning-path items, etc.) so the
  action never fails with a foreign-key error.
- The iGOT/NSSTA "sync" buttons are explicitly mock-catalogue upserts, not
  live government API calls.
- File uploads are stored under `backend/uploads/` (created automatically)
  and capped at 25MB; supported types are `.pdf .doc .docx .ppt .pptx .txt`.

---

## 8. API reference

Full interactive documentation (all request/response schemas) is generated
automatically by FastAPI and served at **http://127.0.0.1:8000/docs** once
the backend is running.
