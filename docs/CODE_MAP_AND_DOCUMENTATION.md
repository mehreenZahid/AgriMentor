# AgriMentor — Code Map & Documentation Overview

## 1. High-Level Project Summary

**AgriMentor** is a Flask-based web application for AI-powered agriculture: crop disease/health prediction from images and management of government schemes (farmers apply, experts/admin manage). The app supports two roles—**farmer** and **expert**—with login (email/password and Google OAuth), role-based dashboards, image upload for prediction (TensorFlow/Keras model), and scheme browsing/application.

- **Backend:** Flask (Python), MySQL (raw `mysql.connector`), Flask-Login, Flask-Bcrypt, Authlib (Google OAuth).
- **ML:** TensorFlow/Keras model (`potato_transfer_model.h5`) for image classification (e.g. crop disease/health).
- **Entry point:** `backend/app.py` (no separate `main.py` or WSGI file found).

---

## 2. Code Map — File & Module Relationships

### 2.1 Directory Layout

```
AgriMentor/
├── backend/                    # Flask application root
│   ├── app.py                  # ★ ENTRY POINT — creates app, registers blueprints, core routes
│   ├── config.py               # Configuration (DB, OAuth, secret, upload folder)
│   ├── extensions.py           # Extension instances (Bcrypt, LoginManager, OAuth) — not used by app.py
│   ├── ml_utils.py             # ML prediction (loads .h5 model, predict_image())
│   ├── auth/
│   │   ├── __init__.py         # (empty)
│   │   └── routes.py           # Auth blueprint: login, register, logout, Google OAuth
│   ├── models/
│   │   ├── __init__.py         # Exports User (and db helpers)
│   │   └── db.py               # (empty) — DB logic lives in models/__init__.py
│   ├── dashboards/
│   │   ├── __init__.py         # (empty)
│   │   ├── farmer.py           # Farmer blueprint: /farmer/dashboard, /history, /profile
│   │   └── expert.py           # Expert blueprint: /expert/dashboard, /review, /manage-schemes, /profile
│   ├── blueprints/             # ★ NOT REGISTERED in app.py — alternate/legacy modules
│   │   ├── admin/routes.py     # Admin blueprint (overview, schemes, applications, farmers)
│   │   ├── farmer/routes.py    # Farmer blueprint (overview, upload, history, schemes, apply, profile)
│   │   ├── main/routes.py      # Main blueprint (home, about, schemes — public)
│   │   └── auth/routes.py      # Alternate auth (uses extensions.bcrypt)
│   ├── templates/              # Jinja2 templates (see list below)
│   └── static/
│       ├── css/style.css
│       └── images/             # e.g. farm-hero.jpg, logo-image.png
├── ml/                         # Standalone ML scripts (not imported by Flask app)
│   ├── data_loader.py          # Keras image dataset loading
│   └── transfer_learning.py    # Transfer learning training script
└── docs/                       # Documentation (this file)
```

### 2.2 Module Connection Overview

| From | Imports / Uses |
|------|----------------|
| `app.py` | `Config`, `auth.routes.auth_bp` + `bcrypt`, `ml_utils.predict_image`, `models.User`, `dashboards.farmer`, `dashboards.expert` |
| `auth/routes.py` | `User` from `models`, defines `auth_bp`, `bcrypt` (own instance) |
| `models/__init__.py` | `mysql.connector`, `Config`, `User` class with `get_db_connection()` |
| `ml_utils.py` | `tensorflow`, `os` — loads `potato_transfer_model.h5` from backend dir |
| `dashboards/farmer.py`, `dashboards/expert.py` | Flask `Blueprint`, `render_template`, `session`, `redirect`, `url_for` |
| `blueprints/*` | Each has its own `get_db()` using `Config`; **not** registered in `app.py` |

- **Flask app creation:** Done in `app.py` (single `Flask(__name__)`), not an app factory.
- **Blueprints registered in `app.py`:** Only `auth_bp`, `farmer` (dashboards), `expert` (dashboards).
- **Database:** Global `mysql.connector` connection and cursor in `app.py`; `User` and blueprint modules use separate `get_db_connection()` / `get_db()` per request.
- **Login:** `LoginManager` in `app.py`, `login_view = "auth.login_page"`; user loader uses `User.get_by_id(user_id)`.

### 2.3 Execution Flow

1. **Start:** `python app.py` (or run `app` from backend directory) → `app.run(debug=True)`.
2. **Request:**  
   - `/` → `auth_bp.root()` → redirect to login or role dashboard.  
   - `/login`, `/register`, `/logout`, `/google-login`, `/google-callback` → `auth.routes`.  
   - `/farmer` → `app.farmer_dashboard()` (in `app.py`) → `upload.html`.  
   - `/upload` (POST) → `app.upload()` → save file, `predict_image()`, insert into `uploads`, render result.  
   - `/expert` → `app.expert_dashboard()` → queries farmers, uploads, distribution → `admin_dashboard.html`.  
   - `/farmer/dashboard`, `/farmer/history`, `/farmer/profile` → `dashboards.farmer`.  
   - `/expert/dashboard`, `/expert/review`, `/expert/manage-schemes`, `/expert/profile` → `dashboards.expert`.
3. **Auth:** After login, redirect uses `farmer.farmer_dashboard` or `expert.expert_dashboard` (dashboard blueprints). Logout → `auth.logout` → login page.

---

## 3. Architecture Overview

### 3.1 Structure

- **Style:** Monolithic Flask app with **route/blueprint-centric** organization; no formal MVC split (templates act as views; “models” are largely the `User` class + raw SQL in routes).
- **Data access:** No ORM. Direct **MySQL** via `mysql.connector` (connection/cursor in `app.py` or per-module `get_db()` / `get_db_connection()`).
- **Auth:** Session-based (Flask-Login), with Bcrypt for passwords and Authlib for Google OAuth.

### 3.2 Flask Configuration

- **Config:** `app.config.from_object(Config)` from `config.py`.
- **Extensions (in app.py):**  
  - `LoginManager` — `login_view = "auth.login_page"`.  
  - `Bcrypt` — imported from `auth.routes` and `bcrypt.init_app(app)`.  
  - `OAuth(app)` — Google provider with `client_id`, `client_secret`, OpenID scope.
- **Blueprint registration:** `auth_bp`, then `farmer` and `expert` from `dashboards`.
- **Middleware:** None explicitly registered (no before_request/after_request in the reviewed code).
- **Upload path:** `Config.UPLOAD_FOLDER`; directory created at startup if missing.

### 3.3 Main Dependencies (implied from imports)

| Package | Purpose |
|--------|---------|
| Flask | Web framework, routing, templates |
| flask-login | Session-based auth, `current_user`, `@login_required` |
| flask-bcrypt | Password hashing |
| authlib | Google OAuth (OAuth(app), authorize_redirect, authorize_access_token) |
| mysql-connector-python | MySQL driver |
| TensorFlow / Keras | Model loading and inference in `ml_utils` |
| Jinja2 | Templates (bundled with Flask) |

---

## 4. Component-Level Documentation

### 4.1 `backend/app.py`

- **Purpose:** Create Flask app, load config, register blueprints, define core farmer/expert and upload routes, set up DB connection and user loader.
- **Key elements:**  
  - `app = Flask(__name__)`, `Config`, `login_manager`, `oauth`, `google` provider.  
  - `app.register_blueprint(auth_bp)`, `app.register_blueprint(farmer)`, `app.register_blueprint(expert)`.  
  - Global `db`, `cursor` (MySQL).  
  - Routes: `GET /farmer` → farmer dashboard (upload page), `POST /upload` → image upload + prediction + DB insert, `GET /expert` → expert dashboard (farmers, prediction count, distribution).  
  - `load_user(user_id)` → `User.get_by_id(user_id)`.
- **Decorators:** `@login_required` on `/farmer`, `/upload`, `/expert`. Role checks with `abort(403)`.

### 4.2 `backend/config.py`

- **Purpose:** Central configuration.
- **Key:** `SECRET_KEY`, `DB_*` (host, user, password, database, port), `UPLOAD_FOLDER`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `SESSION_*`.

### 4.3 `backend/extensions.py`

- **Purpose:** Holds `Bcrypt()`, `LoginManager()`, `OAuth()` instances.
- **Usage:** Not used by `app.py` (app uses `auth.routes.bcrypt` and in-app `LoginManager`/`OAuth`). Used by `blueprints/auth/routes.py` (`from extensions import bcrypt`).

### 4.4 `backend/auth/routes.py`

- **Purpose:** Authentication blueprint (root redirect, register, login, logout, Google OAuth).
- **Blueprint:** `auth_bp = Blueprint("auth", __name__)`.
- **Routes:**  
  - `GET /` → redirect by role or to login.  
  - `GET/POST /register` → register form / create user (farmer).  
  - `GET/POST /login` → login form / validate and redirect by role (`farmer.farmer_dashboard` / `expert.expert_dashboard`).  
  - `GET /logout` → logout, redirect to login.  
  - `GET /google-login` → redirect to Google.  
  - `GET /google-callback` → exchange token, create or load user, login, redirect by role.
- **Logic:** Uses `User.get_by_email`, `User.create`, `User.create_google_user`, `bcrypt.generate_password_hash` / `check_password_hash`, `login_user` / `logout_user`.

### 4.5 `backend/models/__init__.py`

- **Purpose:** User model and DB helper for auth.
- **Key:**  
  - `get_db_connection()` → new MySQL connection from `Config`.  
  - `User(UserMixin)`: `id`, `name`, `email`, `password_hash`, `role`, `oauth_provider`, `oauth_id`; `get_id()`; `get_by_id()`, `get_by_email()`, `create()`, `create_google_user()`, `admin_exists()`.
- **Usage:** Used by `app.py` (user_loader) and `auth/routes.py`.

### 4.6 `backend/ml_utils.py`

- **Purpose:** Load Keras model and run image prediction.
- **Key:** `MODEL_PATH` (e.g. `potato_transfer_model.h5`), `CLASS_NAMES` list, `predict_image(img_path)` → returns `(predicted_class, confidence_percent)`.
- **Dependency:** TensorFlow/Keras; model file expected in backend directory.

### 4.7 `backend/dashboards/farmer.py`

- **Purpose:** Farmer dashboard blueprint (thin wrappers; no DB in this file).
- **Blueprint:** `farmer = Blueprint("farmer", __name__, url_prefix="/farmer")`.
- **Routes:**  
  - `GET /farmer/dashboard` → `farmer/dashboard.html`.  
  - `GET /farmer/history` → `farmer/history.html`.  
  - `GET /farmer/profile` → `farmer/profile.html`.
- **Auth:** Session check `session.get("role") != "farmer"` → redirect to login (no `@login_required`; inconsistent with app.py role checks).

### 4.8 `backend/dashboards/expert.py`

- **Purpose:** Expert dashboard blueprint (thin wrappers).
- **Blueprint:** `expert = Blueprint("expert", __name__, url_prefix="/expert")`.
- **Routes:**  
  - `GET /expert/dashboard` → `expert/dashboard.html`.  
  - `GET /expert/review` → `expert/review_cases.html`.  
  - `GET /expert/manage-schemes` → `expert/manage_schemes.html`.  
  - `GET /expert/profile` → `expert/profile.html`.
- **Auth:** Same session-based role check as farmer.

### 4.9 `backend/blueprints/admin/routes.py` (not registered)

- **Purpose:** Admin/expert CRUD: overview, schemes, applications, farmers.
- **Routes:** `GET /` (overview), `GET/POST /schemes`, `GET /applications`, `GET /application/<id>/<action>`, `GET /farmers`. Uses `@login_required` and `admin_required()` (role expert).
- **Templates:** `admin/overview.html`, `admin/schemes.html`, `admin/applications.html`, `admin/farmers.html`.

### 4.10 `backend/blueprints/farmer/routes.py` (not registered)

- **Purpose:** Full farmer flow: overview, upload (with ML), history, schemes, apply, applications, profile. Uses `farmer_id` in `uploads` and `scheme_applications`.
- **Routes:** `GET /` (overview), `GET/POST /upload`, `GET /history`, `GET /schemes`, `POST /apply/<scheme_id>`, `GET /applications`, `GET/POST /profile`.

### 4.11 `backend/blueprints/main/routes.py` (not registered)

- **Purpose:** Public pages: home, about, schemes list.
- **Routes:** `GET /`, `GET /about`, `GET /schemes` (with optional search/status).

### 4.12 `backend/blueprints/auth/routes.py` (not registered)

- **Purpose:** Alternative auth module using `extensions.bcrypt`; redirects to `farmer.overview` / `admin.overview` (aligns with unregistered blueprints).

---

## 5. API / Route Documentation (Registered Only)

All routes below are actually registered in the running app (auth_bp + app.py + dashboards farmer/expert).

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Optional | Root: redirect to login or role dashboard (farmer/expert). |
| GET | `/register` | No | Registration form. |
| POST | `/register` | No | Create farmer account; redirect to login. |
| GET | `/login` | No | Login form. |
| POST | `/login` | No | Validate credentials; redirect to farmer or expert dashboard. |
| GET | `/logout` | Yes | Logout and redirect to login. |
| GET | `/google-login` | No | Redirect to Google OAuth. |
| GET | `/google-callback` | No | OAuth callback; create/load user, login, redirect by role. |
| GET | `/farmer` | Yes (farmer) | Farmer dashboard (upload page). |
| POST | `/upload` | Yes (farmer) | Upload image; run prediction; store in `uploads`; return result. |
| GET | `/expert` | Yes (expert) | Expert dashboard: farmers list, prediction count, distribution (optional date filter). |
| GET | `/farmer/dashboard` | Session check | Render farmer dashboard template. |
| GET | `/farmer/history` | Session check | Farmer history page. |
| GET | `/farmer/profile` | Session check | Farmer profile page. |
| GET | `/expert/dashboard` | Session check | Expert dashboard template. |
| GET | `/expert/review` | Session check | Expert review cases. |
| GET | `/expert/manage-schemes` | Session check | Expert manage schemes. |
| GET | `/expert/profile` | Session check | Expert profile. |

**Parameters (notable):**

- **POST /register:** `name`, `email`, `password` (form).
- **POST /login:** `email`, `password` (form).
- **POST /upload:** `image` (file).
- **GET /expert:** optional `start_date`, `end_date` (query).

**Responses:** HTML (Jinja2) or redirects; no JSON API documented.

---

## 6. Database & Models

### 6.1 ORM

- **None.** All access is raw SQL via `mysql.connector` (cursor with `dictionary=True` where used).

### 6.2 Tables (inferred from code)

| Table | Purpose |
|-------|---------|
| `users` | id, name, email, password_hash, role, oauth_provider, oauth_id, created_at |
| `uploads` | image_name, upload_time, predicted_class, confidence, status; in `app.py` no `farmer_id`; in `blueprints/farmer` has `farmer_id` |
| `schemes` | title, description, eligibility, benefits, deadline, status, created_at |
| `scheme_applications` | farmer_id, scheme_id, status, applied_at (and id) |

### 6.3 User Model (Flask-Login)

- Lives in `models/__init__.py`: `User(UserMixin)` with `get_id`, `get_by_id`, `get_by_email`, `create`, `create_google_user`, `admin_exists`. No SQLAlchemy or migrations.

### 6.4 Migrations / Init

- No migration framework or SQL init scripts found in the repo. Schema must be created manually or via external scripts.

---

## 7. Templates & Static Assets

### 7.1 Templates (backend/templates)

- **Layouts:** `layouts/base.html`, `layouts/dashboard.html`, `dashboard_layout.html`
- **Auth:** `login.html`, `register.html`
- **Core:** `upload.html`, `admin_dashboard.html`, `requests.html`
- **Main (used if main_bp registered):** `main/home.html`, `main/schemes.html` (about.html referenced but not in glob)
- **Farmer:** `farmer/overview.html`, `farmer/profile.html`, `farmer/applications.html`, `farmer/schemes.html`  
  Dashboard blueprints expect also: `farmer/dashboard.html`, `farmer/history.html` (overview/history may be same or missing).
- **Admin:** `admin/overview.html`, `admin/schemes.html`, `admin/applications.html`, `admin/farmers.html`
- **Expert (dashboards):** `expert/dashboard.html`, `expert/review_cases.html`, `expert/manage_schemes.html`, `expert/profile.html` (may be missing)

### 7.2 Static

- `static/css/style.css`
- `static/images/` (e.g. `farm-hero.jpg`, `logo-image.png`)
- Templates reference `static/css/dashboard.css` (file not in glob result)

---

## 8. Setup & Run Instructions

### 8.1 Dependencies

- No `requirements.txt` in repo. From code, install at least:
  - `flask`
  - `flask-login`
  - `flask-bcrypt`
  - `authlib` (with Flask client)
  - `mysql-connector-python`
  - `tensorflow` (or `tensorflow-cpu`)
- Optional for ML training: see `ml/data_loader.py`, `ml/transfer_learning.py`.

### 8.2 Environment / Config

- Edit `backend/config.py`: set `DB_*` (host, user, password, database, port), `SECRET_KEY`, `GOOGLE_CLIENT_*`, and `UPLOAD_FOLDER` if needed.
- No `.env` loading in code; config is Python-only.

### 8.3 Database

- MySQL server on port per config (e.g. 3307).
- Create database (e.g. `agrimentor`) and tables: `users`, `uploads`, `schemes`, `scheme_applications` (schema inferred from INSERT/SELECT in code; no script provided).

### 8.4 Run

- From project root or `backend`:  
  `cd backend`  
  `python app.py`  
  App runs with `debug=True` (default Flask dev server).

### 8.5 ML Model

- Place `potato_transfer_model.h5` in `backend/` (or adjust `MODEL_PATH` in `ml_utils.py`).
- `CLASS_NAMES` in `ml_utils.py` must match model output.

### 8.6 Testing / Debugging

- No test suite or pytest config found. Use browser or manual HTTP; `ml_utils` has print-based debug around predictions.

---

## 9. Developer Notes & Potential Improvements

1. **Unregistered blueprints:** `blueprints/admin`, `blueprints/farmer`, `blueprints/main`, and `blueprints/auth` are never registered. Either wire them (and possibly remove duplicate logic from `app.py` and `dashboards`) or remove dead code.
2. **Route duplication:** Farmer/expert flows exist both in `app.py` + `dashboards` and in `blueprints/farmer` and `blueprints/admin`. Consolidate on one set of blueprints and one URL layout.
3. **Auth consistency:** `auth/routes.py` redirects to `farmer.farmer_dashboard` / `expert.expert_dashboard`, while `app.py` defines `farmer_dashboard` at `/farmer` (no prefix). Dashboards use session role checks instead of `@login_required` and `current_user`; standardizing on Flask-Login is safer.
4. **Database:** Single global `db`/`cursor` in `app.py` is not request-safe. Prefer per-request connections (e.g. `get_db()` in each route or a teardown that closes connections). Consider SQLAlchemy + migrations (e.g. Flask-Migrate) for schema and connection handling.
5. **Schema mismatch:** `app.py` uploads omit `farmer_id`; `blueprints/farmer` expects it. Unify schema and either add `farmer_id` to uploads in `app.py` or drop it from the alternate blueprint.
6. **Config:** Move secrets and DB credentials to environment variables and load in `Config`; avoid committing secrets.
7. **Templates:** Some dashboard templates (`farmer/dashboard.html`, `expert/dashboard.html`, etc.) may be missing; add or point to existing equivalents (e.g. `farmer/overview.html`).
8. **Public home:** Root `/` currently redirects to login. If a public landing is desired, register `main_bp` and adjust `/` to serve `main.home` or a dedicated landing.
9. **Requirements:** Add `requirements.txt` with pinned versions for reproducible installs.
10. **API:** If a JSON API is needed, add dedicated blueprint(s) and return JSON with proper status codes; keep HTML routes separate.

---

*Generated for AI navigation and context awareness. Update this doc when blueprints or routes change.*
