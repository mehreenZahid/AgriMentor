from flask import Flask, render_template, request, redirect, url_for, abort
import os
import mysql.connector
from flask_login import LoginManager, login_required, current_user
from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth
from config import Config
from ml_utils import predict_image
from auth.routes import auth_bp

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
# PATH SETUP (ML SAFE)
# ---------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = app.config["UPLOAD_FOLDER"]

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

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
# FARMER DASHBOARD (ML)
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
        return "No file part"

    image = request.files["image"]

    if image.filename == "":
        return "No file selected"

    image_path = os.path.join(app.config["UPLOAD_FOLDER"], image.filename)
    image.save(image_path)

    predicted_class, confidence = predict_image(image_path)

    query = """
    INSERT INTO uploads (image_name, upload_time, predicted_class, confidence, status)
    VALUES (%s, NOW(), %s, %s, %s)
    """

    cursor.execute(query, (
        image.filename,
        predicted_class,
        float(confidence),
        "completed"
    ))

    db.commit()

    return render_template(
        "upload.html",
        prediction=predicted_class,
        confidence=confidence
    )

# ---------------------------------------------------
# EXPERT DASHBOARD
# ---------------------------------------------------

@app.route("/expert")
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
    distribution_data=distribution_data
)


# ---------------------------------------------------
# USER-FACING DASHBOARD & PAGES (FARMER)
# ---------------------------------------------------

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
        ORDER BY upload_time DESC
        LIMIT 5
        """
    )
    recent_predictions = cursor.fetchall()

    # Agricultural schemes (if table exists)
    schemes = []
    try:
        cursor.execute(
            """
            SELECT title, description, eligibility, benefits, deadline, status
            FROM schemes
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
        ORDER BY upload_time DESC
        LIMIT 50
        """
    )
    predictions = cursor.fetchall()

    return render_template("history.html", predictions=predictions)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    if current_user.role != "farmer":
        abort(403)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            cursor.execute(
                "UPDATE users SET name = %s WHERE id = %s",
                (name, current_user.id),
            )
            db.commit()
            current_user.name = name

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
