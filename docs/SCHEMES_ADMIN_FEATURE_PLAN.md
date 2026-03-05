## Schemes Admin Feature — Implementation Plan

This document outlines a **simple, working** plan to let the **expert/admin** create and manage agricultural schemes from the dashboard, and to surface those schemes cleanly to farmers, **without breaking any existing flows**.

The plan follows existing patterns in `app.py`, uses the current MySQL access style, and keeps UI consistent with the existing `layout.html` shell and dashboards.

---

### 1. Current Behaviour & Constraints (Do Not Break)

- **Auth & roles**
  - `expert` users (admins) land on `expert_dashboard` (`/expert`).
  - `farmer` users see `/dashboard` and `/farmer` (upload/prediction flows) and must retain:
    - `/farmer` upload page (`upload.html`) and `/upload` POST prediction.
    - `/dashboard` view with:
      - Recent predictions (`uploads` table).
      - A **read-only** snippet of schemes (currently `SELECT ... FROM schemes LIMIT 5`).
- **Public/user schemes views (already present, must keep working)**
  - `GET /schemes` → `schemes.html` with a list of schemes.
  - `GET /schemes/<int:scheme_id>` → `scheme_detail.html` for details.
  - These are read-only and should **keep using** the `schemes` table, just with whatever data admin enters.
- **Database**
  - Table `schemes` already assumed and queried as:
    - `id, title, description, eligibility, benefits, deadline, status`.
  - No ORM; all access uses `mysql.connector` cursors (`cursor` in `app.py`).
- **UI shell**
  - `layout.html` defines **Expert workspace** sidebar and nav, currently with:
    - `Dashboard` (links to `expert_dashboard`).
    - `Support`.
  - Farmer layout and existing templates (`dashboard.html`, `upload.html`, `schemes.html`, `scheme_detail.html`, `admin_dashboard.html`) must remain visually consistent.

---

### 2. Goal & Scope of New Feature

- **Goal:** Allow an **expert/admin** to:
  - Create new schemes.
  - See a simple list of existing schemes.
  - Optionally edit basic scheme fields or archive/close schemes (minimal CRUD).
- **Visibility:**
  - All schemes created by expert appear:
    - On **farmer dashboard** (`dashboard.html` snippet).
    - On full **schemes listing** (`/schemes`) and **scheme details** (`/schemes/<id>`).
    - On expert’s own admin page for verification.
- **Non‑goals (for now, to keep it simple)**
  - No farmer application or “Apply now” workflow.
  - No multi-step approvals or complex statuses.
  - No file uploads or attachments to schemes.

---

### 3. Data Model & Validation Plan

- **Database: `schemes` table (existing)**
  - Expected columns (from code):
    - `id` (INT, PK, auto-increment)
    - `title` (VARCHAR, required)
    - `description` (TEXT, optional)
    - `eligibility` (TEXT, optional)
    - `benefits` (TEXT, optional)
    - `deadline` (DATE or DATETIME, nullable)
    - `status` (VARCHAR, e.g. `"open"`, `"closed"`, `"archived"`)
    - (Optional) `created_at` (DATETIME) if already present.
- **Form-level validation (server‑side, simple)**
  - Required: `title`.
  - Optional text areas: `description`, `eligibility`, `benefits`.
  - `deadline` string parsed safely:
    - If blank → store `NULL`.
    - If invalid format → ignore and treat as `NULL` (or re-render form with error message in a later iteration).
  - `status` constrained to a small fixed set: `"open"`, `"closed"`, `"archived"`.

---

### 4. Backend Routes — Expert/Admin Schemes Management

All routes implemented in `backend/app.py` using the existing global `db` and `cursor`. Every admin route must:
- Be protected by `@login_required`.
- Check `current_user.role == "expert"` and `abort(403)` otherwise.

#### 4.1. List Schemes for Admin

- **Route:** `GET /admin/schemes`
- **Name:** `admin_schemes`
- **Purpose:** Show a simple table/list of all schemes with links to edit.
- **Behaviour:**
  - Query:
    - `SELECT id, title, status, deadline FROM schemes ORDER BY deadline ASC`
  - Render new template: `admin_schemes.html`.
  - Only visible to expert users.

#### 4.2. Create New Scheme (Form)

- **Route:** `GET /admin/schemes/new`
- **Name:** `admin_new_scheme`
- **Purpose:** Render an empty creation form.
- **Behaviour:**
  - Render `admin_scheme_form.html` with:
    - `mode="create"`.
    - Empty/default values for fields.

#### 4.3. Create New Scheme (Submit)

- **Route:** `POST /admin/schemes/new`
- **Name:** reuse `admin_new_scheme` (same function with method list `["GET", "POST"]`).
- **Behaviour:**
  - Read form fields:
    - `title` (required).
    - `description`, `eligibility`, `benefits` (optional).
    - `deadline` (optional, parse string).
    - `status` (default `"open"` if not provided).
  - Basic validation:
    - If `title` missing → re-render form with error message (can be a simple inline message using Jinja).
  - Insert into DB using existing cursor:
    - `INSERT INTO schemes (title, description, eligibility, benefits, deadline, status) VALUES (%s, %s, %s, %s, %s, %s)`
  - `db.commit()`.
  - Redirect to `admin_schemes` on success.

#### 4.4. Edit Existing Scheme

- **Route:** `GET /admin/schemes/<int:scheme_id>/edit`
- **Name:** `admin_edit_scheme`
- **Behaviour:**
  - Fetch scheme by id:
    - `SELECT id, title, description, eligibility, benefits, deadline, status FROM schemes WHERE id = %s`
  - If not found → `abort(404)`.
  - Pre-fill form in `admin_scheme_form.html` with current values, `mode="edit"`.

#### 4.5. Update Existing Scheme (Submit)

- **Route:** `POST /admin/schemes/<int:scheme_id>/edit`
- **Name:** reuse `admin_edit_scheme` (methods `["GET", "POST"]`) or separate function, whichever is simpler.
- **Behaviour:**
  - Same form parsing/validation logic as create.
  - `UPDATE schemes SET title=%s, description=%s, eligibility=%s, benefits=%s, deadline=%s, status=%s WHERE id=%s`
  - `db.commit()`.
  - Redirect back to `admin_schemes`.

#### 4.6. Optional: Soft “Archive/Close”

- **Route:** `POST /admin/schemes/<int:scheme_id>/archive` (optional).
- **Behaviour:**
  - Set `status = 'archived'` (or `'closed'`) for that scheme.
  - `db.commit()`.
  - Redirect back to `admin_schemes`.
- **Note:** Farmers / public listing can simply hide `archived` schemes if desired (see Section 5).

---

### 5. Farmer & Public Views — Minimal Changes

Keep the existing routes and templates, only slightly adjust queries to align with admin‑managed data.

#### 5.1. Farmer Dashboard (`/dashboard`)

- **Current code:** already queries:
  - `SELECT title, description, eligibility, benefits, deadline, status FROM schemes ORDER BY deadline ASC LIMIT 5`
- **Plan:**
  - Optionally filter out archived schemes:
    - Add `WHERE status != 'archived'` (or `WHERE status = 'open'`) **only if** this does not break existing data.
  - Keep the rest of the route and `dashboard.html` unchanged.

#### 5.2. Public Schemes List (`/schemes`)

- **Current code:** `SELECT id, title, description, eligibility, benefits, deadline, status FROM schemes ORDER BY deadline ASC`
- **Plan:**
  - Optionally filter out archived schemes as:
    - `WHERE status != 'archived'` or `WHERE status = 'open'`.
  - Keep `schemes.html` unchanged; it already displays the fields we will collect via admin.

#### 5.3. Scheme Detail (`/schemes/<id>`)

- **Current code:** fetches one scheme by id and renders `scheme_detail.html`.
- **Plan:**
  - No change required; once admin routes insert/update data in `schemes`, details page will automatically display correct information.

---

### 6. Templates — Admin UI for Schemes

Follow existing `layout.html` shell styles (`shell-card`, `shell-table`, etc.) and `admin_dashboard.html` patterns.

#### 6.1. `admin_schemes.html`

- Extends `layout.html`.
- Displays:
  - Page header: “Manage schemes”.
  - Button/link: “New scheme” → `url_for('admin_new_scheme')`.
  - Table of schemes:
    - Columns: Title, Status, Deadline, Actions.
    - Action links:
      - “Edit” → `url_for('admin_edit_scheme', scheme_id=s.id)`.
      - (Optional) “Archive” as a small form with POST button.

#### 6.2. `admin_scheme_form.html`

- Extends `layout.html`.
- Single form used for both create and edit:
  - Title (`input[type=text]`, required).
  - Description (`textarea`).
  - Eligibility (`textarea`).
  - Benefits (`textarea`).
  - Deadline (`input[type=date]`).
  - Status (`select` with options `"open"`, `"closed"`, `"archived"`).
  - Submit button text conditional on mode:
    - “Create scheme” vs “Save changes”.
- Show a minimal error message block if the backend passes an `error` string.

#### 6.3. Hook into Expert Navigation

- Update `layout.html` expert sidebar (`Expert workspace`) to include a new link:
  - Text: “Schemes”.
  - Href: `url_for('admin_schemes')`.
  - `is-active` state when `request.endpoint == 'admin_schemes'` or when on an edit/create route (by checking endpoint).

---

### 7. Access Control & Safety Checks

- **Every** `/admin/schemes*` route:
  - Decorated with `@login_required`.
  - Starts with:
    - `if current_user.role != "expert": abort(403)`
- Avoid any database operations that affect other tables (`users`, `uploads`) in these routes.
- Use parametrized queries as in existing code to avoid SQL injection.

---

### 8. Step‑by‑Step Implementation Order

To minimize breakage, follow this order:

1. **Add backend routes (no template changes yet)**
   - Implement skeletons for:
     - `/admin/schemes` (returns plain text or minimal template stub).
     - `/admin/schemes/new` and `/admin/schemes/<id>/edit` (GET/POST logic using existing DB connection).
   - Add role checks and simple redirects.
2. **Create admin templates**
   - `admin_schemes.html` with basic table and “New scheme” button.
   - `admin_scheme_form.html` with fields and CSRF‑free simple HTML form (consistent with existing forms).
3. **Wire navigation**
   - Add “Schemes” link into expert sidebar in `layout.html`.
   - Verify that:
     - Farmer sidebar is unchanged.
     - Anonymous layout is unchanged.
4. **Refine queries for farmer & public views**
   - Optionally filter out archived schemes in:
     - `/dashboard` schemes snippet.
     - `/schemes` listing.
   - Confirm pages still load when `schemes` table is empty.
5. **Manual testing**
   - As expert:
     - Log in → `expert_dashboard`.
     - Navigate to “Schemes”.
     - Create a scheme with title, description, eligibility, benefits, deadline, and status.
     - Edit an existing scheme and confirm changes persist.
   - As farmer:
     - Confirm `/dashboard` shows the new scheme in the “Agricultural schemes” card.
     - Visit `/schemes` and `/schemes/<id>` to see full details.
   - As unauthenticated:
     - Ensure `/schemes` and `/schemes/<id>` still work (if currently public) or behave as before.

---

### 9. Future Enhancements (Out of Scope for Now)

These are intentionally deferred to keep the first version simple and stable:

- Farmer **“Apply to scheme”** workflow with `scheme_applications` table integration.
- File or document uploads per scheme.
- Rich text editing for descriptions/eligibility.
- Region/state tagging and filtering.
- API endpoints for schemes (JSON for mobile apps).

