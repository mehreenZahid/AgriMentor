from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory, flash
import os
import logging
import mysql.connector
from werkzeug.utils import secure_filename
from flask_login import LoginManager, login_required, current_user
from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth
from config import Config
from ml_utils import predict_image, detect_soil_type_from_image, get_crop_recommendations, validate_plant_image
from auth.routes import auth_bp
from datetime import datetime

# ---------------------------------------------------
# APP INITIALIZATION
# ---------------------------------------------------

app = Flask(__name__)
app.config.from_object(Config)

# ---------------------------------------------------
# EXTENSIONS
# ---------------------------------------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login_page"


from auth.routes import bcrypt
bcrypt.init_app(app)

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)


# ---------------------------------------------------
# REGISTER BLUEPRINTS
# ---------------------------------------------------

app.register_blueprint(auth_bp)


# ---------------------------------------------------
# PUBLIC LANDING PAGE
# ---------------------------------------------------

@app.route("/")
def index():
    # If the user is already logged in, keep the existing behaviour
    # of sending them straight to their dashboard.
    if current_user.is_authenticated:
        if current_user.role == "farmer":
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("expert_dashboard"))

    # Anonymous users see the marketing / landing page.
    featured_schemes = []
    try:
        cursor.execute(
            """
            SELECT
                id,
                title,
                -- Fallback: if eligibility_summary does not exist or is NULL,
                -- derive a short summary from eligibility/description.
                COALESCE(eligibility_summary, '') AS eligibility_summary,
                COALESCE(eligibility, '') AS eligibility,
                COALESCE(description, '') AS description
            FROM schemes
            ORDER BY deadline ASC
            LIMIT 3
            """
        )
        rows = cursor.fetchall()

        # Ensure each row has a non-empty eligibility_summary
        for row in rows:
            if not row.get("eligibility_summary"):
                base_text = row.get("eligibility") or row.get("description") or ""
                row["eligibility_summary"] = (base_text[:120] + "…") if base_text else ""

        featured_schemes = rows
    except mysql.connector.Error:
        # If the schemes table is missing or errors, fail silently
        featured_schemes = []

    return render_template("index.html", featured_schemes=featured_schemes)

# ---------------------------------------------------
# PATH SETUP (ML SAFE)
# ---------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = app.config["UPLOAD_FOLDER"]
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_CONTENT_LENGTH_MB = 10
MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH_MB * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------------------------------------------
# LOGGING
# ---------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _allowed_file(filename):
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


# ---------------------------------------------------
# UPLOADED IMAGE SERVING
# ---------------------------------------------------


@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    if current_user.role not in ("farmer", "expert"):
        abort(403)
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ---------------------------------------------------
# DATABASE CONNECTION (ML SAFE - NOT REMOVED)
# ---------------------------------------------------

db = mysql.connector.connect(
    host=app.config["DB_HOST"],
    user=app.config["DB_USER"],
    password=app.config["DB_PASSWORD"],
    database=app.config["DB_NAME"],
    port=app.config["DB_PORT"]
)

cursor = db.cursor(dictionary=True)

# ---------------------------------------------------
# FARMER DASHBOARD (UPLOAD)
# ---------------------------------------------------

@app.route("/farmer")
@login_required
def farmer_dashboard():
    if current_user.role != "farmer":
        abort(403)
    return render_template("upload.html")


@app.route("/upload", methods=["POST"])
@login_required
def upload():

    if current_user.role != "farmer":
        abort(403)

    if "image" not in request.files:
        flash("No file was uploaded. Please select an image.", "danger")
        return redirect(url_for("farmer_dashboard"))

    image = request.files["image"]

    if not image or not image.filename or image.filename.strip() == "":
        flash("Please select an image to upload.", "danger")
        return redirect(url_for("farmer_dashboard"))

    if not _allowed_file(image.filename):
        flash("Please upload a valid image file (JPG or PNG only).", "danger")
        return redirect(url_for("farmer_dashboard"))

    image.seek(0, 2)
    size = image.tell()
    image.seek(0)
    if size > MAX_CONTENT_LENGTH:
        flash(f"File size must be less than {MAX_CONTENT_LENGTH_MB} MB.", "danger")
        return redirect(url_for("farmer_dashboard"))

    try:
        filename = secure_filename(image.filename)
        if not filename:
            filename = "upload_" + str(int(datetime.now().timestamp())) + ".jpg"
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image.save(image_path)

        # Pre-validate if it's a plant/leaf image
        if not validate_plant_image(image_path):
            return render_template(
                "upload.html",
                low_confidence=True
            )

        predicted_class, confidence = predict_image(image_path)
        
        confidence_threshold = 70.0
        
        if confidence < confidence_threshold:
            return render_template(
                "upload.html",
                low_confidence=True
            )

        query = """
        INSERT INTO uploads (image_name, upload_time, predicted_class, confidence, status, farmer_id)
        VALUES (%s, NOW(), %s, %s, %s, %s)
        """
        cursor.execute(query, (
            filename,
            predicted_class,
            float(confidence),
            "completed",
            current_user.id
        ))
        db.commit()

        return render_template(
            "upload.html",
            prediction=predicted_class,
            confidence=confidence
        )
    except Exception as ex:
        logger.exception("Upload or prediction failed")
        flash("Something went wrong while processing your image. Please try again.", "danger")
        return redirect(url_for("farmer_dashboard"))

# ---------------------------------------------------
# SOIL RECOMMENDATION (FARMER)
# ---------------------------------------------------

@app.route("/recommend")
@login_required
def recommend_entry():
    if current_user.role != "farmer":
        abort(403)
    return redirect(url_for("soil_recommendation"))


@app.route("/soil-recommendation", methods=["GET", "POST"])
@login_required
def soil_recommendation():
    if current_user.role != "farmer":
        abort(403)

    if request.method == "POST":
        soil_type = request.form.get("soil_type")
        season = request.form.get("season")
        water = request.form.get("water")

        detected_soil = None

        if "image" in request.files:
            image = request.files["image"]
            if image and image.filename != "" and _allowed_file(image.filename):
                try:
                    filename = secure_filename(image.filename)
                    if not filename:
                        filename = "soil_upload_" + str(int(datetime.now().timestamp())) + ".jpg"
                    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    image.save(image_path)
                    
                    detected_soil = detect_soil_type_from_image(image_path)
                except Exception as ex:
                    logger.exception("Soil image upload/detection failed")
                    flash("Failed to process soil image. Using manual selection.", "danger")

        if not detected_soil:
            if soil_type:
                detected_soil = soil_type
            else:
                detected_soil = "Loamy"

        crops, explanation = get_crop_recommendations(detected_soil, season, water)
        
        try:
            crops_str = ", ".join(crops) if isinstance(crops, list) else str(crops)
            cursor.execute('''
                INSERT INTO soil_recommendations 
                (user_id, soil_type, season, water, recommended_crops) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (current_user.id, detected_soil, season, water, crops_str))
            db.commit()
        except Exception as ex:
            logger.exception("Failed to insert soil recommendation into database")
        
        cursor.execute(
            """
            SELECT soil_type, season, water, recommended_crops, timestamp
            FROM soil_recommendations
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT 5
            """, (current_user.id,)
        )
        recent_soil_recommendations = cursor.fetchall()

        return render_template(
            "soil_recommendation.html",
            detected_soil=detected_soil,
            recommended_crops=crops,
            explanation=explanation,
            season=season,
            water=water,
            manual_soil_type=soil_type,
            scroll_to_results=True,
            recent_soil_recommendations=recent_soil_recommendations
        )

    cursor.execute(
        """
        SELECT soil_type, season, water, recommended_crops, timestamp
        FROM soil_recommendations
        WHERE user_id = %s
        ORDER BY timestamp DESC
        LIMIT 5
        """, (current_user.id,)
    )
    recent_soil_recommendations = cursor.fetchall()

    return render_template("soil_recommendation.html", recent_soil_recommendations=recent_soil_recommendations)


# ---------------------------------------------------
# EXPERT DASHBOARD
# ---------------------------------------------------

@app.route("/expert")
@app.route("/expert_dashboard")
@login_required
def expert_dashboard():

    if current_user.role != "expert":
        abort(403)

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # ------------------------
    # FARMERS LIST
    # ------------------------

    farmer_query = "SELECT * FROM users WHERE role='farmer'"
    farmer_params = []

    if start_date and end_date:
        farmer_query += " AND DATE(created_at) BETWEEN %s AND %s"
        farmer_params.extend([start_date, end_date])

    cursor.execute(farmer_query, farmer_params)
    farmers = cursor.fetchall()

    # ------------------------
    # PREDICTION COUNT
    # ------------------------

    prediction_query = "SELECT COUNT(*) as total FROM uploads WHERE 1=1"
    prediction_params = []

    if start_date and end_date:
        prediction_query += " AND DATE(upload_time) BETWEEN %s AND %s"
        prediction_params.extend([start_date, end_date])

    cursor.execute(prediction_query, prediction_params)
    prediction_count = cursor.fetchone()["total"]

    # ------------------------
    # TOTAL FARMERS COUNT
    # ------------------------

    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='farmer'")
    total_farmers_count = cursor.fetchone()["total"]

    # ------------------------
    # PREDICTION DISTRIBUTION
    # ------------------------

    distribution_query = """
    SELECT predicted_class, COUNT(*) as count
    FROM uploads
    GROUP BY predicted_class
    """

    cursor.execute(distribution_query)
    distribution_data = cursor.fetchall()


    return render_template(
    "admin_dashboard.html",
    farmers=farmers,
    prediction_count=prediction_count,
    total_farmers_count=total_farmers_count,
    distribution_data=distribution_data
)


# ---------------------------------------------------
# USER-FACING DASHBOARD & PAGES (FARMER)
# ---------------------------------------------------

@app.route("/farmer_dashboard")
@app.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "farmer":
        # Experts keep using the existing expert dashboard
        return redirect(url_for("expert_dashboard"))

    # Recent predictions (global for now, not per-user)
    cursor.execute(
        """
        SELECT image_name, upload_time, predicted_class, confidence
        FROM uploads
        WHERE farmer_id = %s
        ORDER BY upload_time DESC
        LIMIT 5
        """, (current_user.id,)
    )
    recent_predictions = cursor.fetchall()



    # Agricultural schemes (if table exists)
    schemes = []
    try:
        cursor.execute(
            """
            SELECT id, title, description, eligibility, benefits, deadline, status
            FROM schemes
            WHERE status != 'archived'
            ORDER BY deadline ASC
            LIMIT 5
            """
        )
        schemes = cursor.fetchall()
    except mysql.connector.Error:
        schemes = []

    return render_template(
        "dashboard.html",
        recent_predictions=recent_predictions,
        schemes=schemes,
    )


# ---------------------------------------------------
# PUBLIC SCHEMES LISTING
# ---------------------------------------------------

@app.route("/schemes")
def schemes():
    records = []
    try:
        cursor.execute(
            """
            SELECT id, title, description, eligibility, benefits, deadline, status
            FROM schemes
            WHERE status != 'archived'
            ORDER BY deadline ASC
            """
        )
        records = cursor.fetchall()
    except mysql.connector.Error:
        records = []

    return render_template("schemes.html", schemes=records)


@app.route("/schemes/<int:scheme_id>")
def scheme_detail(scheme_id):
    scheme = None
    try:
        cursor.execute(
            """
            SELECT id, title, description, eligibility, benefits, deadline, status
            FROM schemes
            WHERE id = %s
            """,
            (scheme_id,),
        )
        scheme = cursor.fetchone()
    except mysql.connector.Error:
        scheme = None

    if not scheme:
        abort(404)

    return render_template("scheme_detail.html", scheme=scheme)


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/admin/schemes", methods=["GET"])
@login_required
def admin_schemes():
    if current_user.role != "expert":
        abort(403)

    cursor.execute(
        """
        SELECT id, title, status, deadline
        FROM schemes
        ORDER BY deadline ASC
        """
    )
    schemes = cursor.fetchall()

    return render_template("admin_schemes.html", schemes=schemes)


def _parse_deadline(date_str):
    date_str = (date_str or "").strip()
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _valid_status(s):
    return s in ("open", "closed", "archived")


@app.route("/admin/schemes/new", methods=["GET", "POST"])
@login_required
def admin_new_scheme():
    if current_user.role != "expert":
        abort(403)

    error = None
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        eligibility = (request.form.get("eligibility") or "").strip()
        benefits = (request.form.get("benefits") or "").strip()
        deadline_input = (request.form.get("deadline") or "").strip()
        status = (request.form.get("status") or "").strip() or "open"

        deadline = _parse_deadline(deadline_input)

        if not title:
            error = "Title is required."
        elif deadline_input and deadline is None:
            error = "Please enter a valid deadline date (YYYY-MM-DD)."
        elif not _valid_status(status):
            error = "Status must be one of: Open, Closed, or Archived."
        else:
            try:
                cursor.execute(
                    """
                    INSERT INTO schemes (title, description, eligibility, benefits, deadline, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (title, description, eligibility, benefits, deadline, status),
                )
                db.commit()
                return redirect(url_for("admin_schemes"))
            except Exception as ex:
                logger.exception("Admin scheme creation failed")
                error = "Something went wrong. Please try again."

        scheme = {
            "title": title,
            "description": description,
            "eligibility": eligibility,
            "benefits": benefits,
            "deadline": deadline_input,
            "status": status,
        }
    else:
        scheme = {
            "title": "",
            "description": "",
            "eligibility": "",
            "benefits": "",
            "deadline": "",
            "status": "open",
        }

    return render_template(
        "admin_scheme_form.html",
        mode="create",
        scheme=scheme,
        error=error,
    )


@app.route("/admin/schemes/<int:scheme_id>/edit", methods=["GET", "POST"])
@login_required
def admin_edit_scheme(scheme_id):
    if current_user.role != "expert":
        abort(403)

    error = None

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        description = (request.form.get("description") or "").strip()
        eligibility = (request.form.get("eligibility") or "").strip()
        benefits = (request.form.get("benefits") or "").strip()
        deadline_input = (request.form.get("deadline") or "").strip()
        status = (request.form.get("status") or "").strip() or "open"

        deadline = _parse_deadline(deadline_input)

        if not title:
            error = "Title is required."
        elif deadline_input and deadline is None:
            error = "Please enter a valid deadline date (YYYY-MM-DD)."
        elif not _valid_status(status):
            error = "Status must be one of: Open, Closed, or Archived."
        else:
            try:
                cursor.execute(
                    """
                    UPDATE schemes
                    SET title=%s,
                        description=%s,
                        eligibility=%s,
                        benefits=%s,
                        deadline=%s,
                        status=%s
                    WHERE id=%s
                    """,
                    (title, description, eligibility, benefits, deadline, status, scheme_id),
                )
                db.commit()
                return redirect(url_for("admin_schemes"))
            except Exception as ex:
                logger.exception("Admin scheme update failed")
                error = "Something went wrong. Please try again."

        scheme = {
            "id": scheme_id,
            "title": title,
            "description": description,
            "eligibility": eligibility,
            "benefits": benefits,
            "deadline": deadline_input,
            "status": status,
        }
    else:
        cursor.execute(
            """
            SELECT id, title, description, eligibility, benefits, deadline, status
            FROM schemes
            WHERE id = %s
            """,
            (scheme_id,),
        )
        scheme = cursor.fetchone()
        if not scheme:
            abort(404)

        # Normalize deadline for the date input field
        deadline_value = ""
        if scheme.get("deadline"):
            try:
                deadline_value = scheme["deadline"].strftime("%Y-%m-%d")
            except AttributeError:
                # If it's already a string or unexpected type, fall back silently
                deadline_value = str(scheme["deadline"])
        scheme["deadline"] = deadline_value

    return render_template(
        "admin_scheme_form.html",
        mode="edit",
        scheme=scheme,
        error=error,
    )


@app.route("/admin/schemes/<int:scheme_id>/archive", methods=["POST"])
@login_required
def admin_archive_scheme(scheme_id):
    if current_user.role != "expert":
        abort(403)

    cursor.execute(
        "UPDATE schemes SET status = 'archived' WHERE id = %s",
        (scheme_id,),
    )
    db.commit()
    return redirect(url_for("admin_schemes"))


@app.route("/predict")
@login_required
def predict_entry():

    if current_user.role != "farmer":
        abort(403)

    # Reuse the existing upload dashboard at /farmer
    return redirect(url_for("farmer_dashboard"))


@app.route("/history")
@login_required
def history():

    if current_user.role != "farmer":
        abort(403)

    cursor.execute(
        """
        SELECT image_name, upload_time, predicted_class, confidence
        FROM uploads
        WHERE farmer_id = %s
        ORDER BY upload_time DESC
        LIMIT 50
        """, (current_user.id,)
    )
    predictions = cursor.fetchall()

    return render_template("history.html", predictions=predictions)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if current_user.role != "farmer":
        abort(403)

    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Please enter your name.", "danger")
        elif len(name) < 2:
            flash("Name must be at least 2 characters.", "danger")
        else:
            try:
                cursor.execute(
                    "UPDATE users SET name = %s WHERE id = %s",
                    (name, current_user.id),
                )
                db.commit()
                current_user.name = name
                flash("Profile updated successfully.", "success")
            except Exception as ex:
                logger.exception("Profile update failed")
                flash("Something went wrong. Please try again.", "danger")

    return render_template("profile.html", user=current_user)


@app.route("/community")
@login_required
def community():
    return render_template("community.html")


@app.route("/support")
@login_required
def support():
    return render_template("support.html")



# ---------------------------------------------------
# USER LOADER (IMPORTANT FOR FLASK-LOGIN)
# ---------------------------------------------------

from models import User  # Make sure User class exists

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

# ---------------------------------------------------

app.google = google

if __name__ == "__main__":
    app.run(debug=True)
