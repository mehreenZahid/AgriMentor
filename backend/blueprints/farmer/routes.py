from flask import Blueprint, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
import mysql.connector
from config import Config
from ml_utils import predict_image
import os

farmer_bp = Blueprint("farmer", __name__)

def get_db():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT
    )

# -----------------------------
# Overview
# -----------------------------
@farmer_bp.route("/")
@login_required
def overview():

    if current_user.role != "farmer":
        abort(403)

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM uploads WHERE farmer_id=%s", (current_user.id,))
    total_uploads = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM scheme_applications WHERE farmer_id=%s", (current_user.id,))
    total_applications = cursor.fetchone()["total"]

    cursor.close()
    db.close()

    return render_template(
        "farmer/overview.html",
        total_uploads=total_uploads,
        total_applications=total_applications
    )

# -----------------------------
# Upload
# -----------------------------
@farmer_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():

    if current_user.role != "farmer":
        abort(403)

    prediction = None
    confidence = None

    if request.method == "POST":

        image = request.files.get("image")

        if image and image.filename:

            image_path = os.path.join(Config.UPLOAD_FOLDER, image.filename)
            image.save(image_path)

            predicted_class, confidence = predict_image(image_path)

            db = get_db()
            cursor = db.cursor()

            cursor.execute("""
                INSERT INTO uploads 
                (image_name, upload_time, predicted_class, confidence, status, farmer_id)
                VALUES (%s, NOW(), %s, %s, %s, %s)
            """, (
                image.filename,
                predicted_class,
                float(confidence),
                "completed",
                current_user.id
            ))

            db.commit()
            cursor.close()
            db.close()

            prediction = predicted_class

    return render_template(
        "farmer/upload.html",
        prediction=prediction,
        confidence=confidence
    )

# -----------------------------
# Prediction History
# -----------------------------
@farmer_bp.route("/history")
@login_required
def history():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM uploads WHERE farmer_id=%s ORDER BY upload_time DESC", (current_user.id,))
    uploads = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("farmer/history.html", uploads=uploads)

# -----------------------------
# Browse Schemes
# -----------------------------
@farmer_bp.route("/schemes")
@login_required
def farmer_schemes():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM schemes WHERE status='active' ORDER BY deadline ASC")
    schemes = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("farmer/schemes.html", schemes=schemes)

# -----------------------------
# Apply to Scheme
# -----------------------------
@farmer_bp.route("/apply/<int:scheme_id>", methods=["POST"])
@login_required
def apply_scheme(scheme_id):

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO scheme_applications (farmer_id, scheme_id, status)
        VALUES (%s, %s, %s)
    """, (current_user.id, scheme_id, "applied"))

    db.commit()
    cursor.close()
    db.close()

    return redirect(url_for("farmer.farmer_schemes"))

# -----------------------------
# My Applications
# -----------------------------
@farmer_bp.route("/applications")
@login_required
def applications():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT s.title, s.deadline, a.status, a.applied_at
        FROM scheme_applications a
        JOIN schemes s ON a.scheme_id = s.id
        WHERE a.farmer_id=%s
        ORDER BY a.applied_at DESC
    """, (current_user.id,))

    applications = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("farmer/applications.html", applications=applications)

# -----------------------------
# Profile
# -----------------------------
@farmer_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        name = request.form.get("name")

        cursor.execute(
            "UPDATE users SET name=%s WHERE id=%s",
            (name, current_user.id)
        )
        db.commit()

    cursor.execute("SELECT name, email FROM users WHERE id=%s", (current_user.id,))
    user = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template("farmer/profile.html", user=user)