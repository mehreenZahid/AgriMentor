from flask import Blueprint, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
import mysql.connector
from config import Config

admin_bp = Blueprint("admin", __name__)

def get_db():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT
    )

def admin_required():
    if current_user.role != "expert":
        abort(403)

# -----------------------------
# Overview
# -----------------------------
@admin_bp.route("/")
@login_required
def overview():

    admin_required()

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role='farmer'")
    total_farmers = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM schemes")
    total_schemes = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as total FROM scheme_applications")
    total_applications = cursor.fetchone()["total"]

    cursor.close()
    db.close()

    return render_template(
        "admin/overview.html",
        total_farmers=total_farmers,
        total_schemes=total_schemes,
        total_applications=total_applications
    )

# -----------------------------
# Manage Schemes
# -----------------------------
@admin_bp.route("/schemes", methods=["GET", "POST"])
@login_required
def manage_schemes():

    admin_required()

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        eligibility = request.form.get("eligibility")
        benefits = request.form.get("benefits")
        deadline = request.form.get("deadline")

        cursor.execute("""
            INSERT INTO schemes (title, description, eligibility, benefits, deadline)
            VALUES (%s, %s, %s, %s, %s)
        """, (title, description, eligibility, benefits, deadline))

        db.commit()

    cursor.execute("SELECT * FROM schemes ORDER BY created_at DESC")
    schemes = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("admin/schemes.html", schemes=schemes)

# -----------------------------
# Applications Review
# -----------------------------
@admin_bp.route("/applications")
@login_required
def applications():

    admin_required()

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT a.id, u.name as farmer_name, s.title, a.status, a.applied_at
        FROM scheme_applications a
        JOIN users u ON a.farmer_id = u.id
        JOIN schemes s ON a.scheme_id = s.id
        ORDER BY a.applied_at DESC
    """)

    applications = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("admin/applications.html", applications=applications)

@admin_bp.route("/application/<int:id>/<string:action>")
@login_required
def update_application(id, action):

    admin_required()

    db = get_db()
    cursor = db.cursor()

    if action in ["approved", "rejected"]:
        cursor.execute(
            "UPDATE scheme_applications SET status=%s WHERE id=%s",
            (action, id)
        )
        db.commit()

    cursor.close()
    db.close()

    return redirect(url_for("admin.applications"))

# -----------------------------
# Manage Farmers
# -----------------------------
@admin_bp.route("/farmers")
@login_required
def farmers():

    admin_required()

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT id, name, email, created_at FROM users WHERE role='farmer'")
    farmers = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("admin/farmers.html", farmers=farmers)