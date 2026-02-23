# Dashboard Cleanup Plan

## Goal
Remove redundant dashboard-related code while **keeping the current working system intact**: register, login, prediction, `/farmer` (upload), and `/expert` (admin view).

---

## What We Keep (Do Not Break)

| Component | Location | Purpose |
|-----------|----------|---------|
| Auth | `backend/auth/routes.py` | Register, login, logout, Google OAuth. Redirects use `farmer_dashboard` / `expert_dashboard` (app view names → `/farmer`, `/expert`). |
| Farmer flow | `backend/app.py` | `GET /farmer` → upload page (`upload.html`), `POST /upload` → prediction + DB. |
| Expert flow | `backend/app.py` | `GET /expert` → expert view (`admin_dashboard.html`) with farmers, prediction count, distribution. |
| Templates | `upload.html`, `admin_dashboard.html`, `login.html`, `register.html` | Used by the above; standalone (no dashboard layout). |
| Config, DB, ML | `config.py`, `ml_utils.py`, `models/` | Unchanged. |

---

## Redundant Dashboard Code (To Remove)

### 1. Dashboard blueprints (unused routes)
- **`backend/dashboards/farmer.py`** — Registers `/farmer/dashboard`, `/farmer/history`, `/farmer/profile`. Not used; you reverted to app’s `/farmer` only.
- **`backend/dashboards/expert.py`** — Registers `/expert/dashboard`, `/expert/review`, `/expert/manage-schemes`, `/expert/profile`. Not used; you use app’s `/expert` only.
- **Action:** Unregister these blueprints in `app.py` and delete the `backend/dashboards/` package (folder and files).

### 2. Dashboard layout template
- **`backend/templates/dashboard_layout.html`** — Sidebar layout that links to `farmer.farmer_dashboard`, `expert.expert_dashboard`, etc. No registered route uses it after blueprint removal.
- **Action:** Delete `dashboard_layout.html`.

### 3. Nav link fix (current system)
- **`backend/templates/layouts/base.html`** — Expert link points to `/admin`; working route is `/expert`.
- **Action:** Change Dashboard/Admin link for expert from `/admin` to `/expert` so the nav matches the working app.

---

## Additional Cleanup (Redundant Files & Folders Removed)

- **`backend/blueprints/`** — Entire folder removed (admin, farmer, main, auth — none were registered).
- **`backend/extensions.py`** — Removed (unused; app uses `auth.routes.bcrypt` and in-app LoginManager/OAuth).
- **`backend/models/db.py`** — Removed (empty file).
- **`backend/dashboards/`** — Folder removed (blueprint files already deleted earlier).
- **Unused templates** — Removed: `layouts/base.html`, `layouts/dashboard.html`, `farmer/*`, `admin/*`, `main/*`, `requests.html`.

---

## Verification After Cleanup

1. **Login (farmer)** → redirects to `/farmer` (upload page).
2. **Login (expert)** → redirects to `/expert` (admin dashboard).
3. **`/farmer`** → upload page; **`/upload`** (POST) → prediction works.
4. **`/expert`** → farmers list, prediction count, distribution.
5. No remaining references to `dashboards.farmer` or `dashboards.expert` in registered app code.

---

*Plan created for cleanup; next step is fresh dashboard implementation and design language.*
