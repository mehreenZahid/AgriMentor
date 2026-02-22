from flask import Blueprint, render_template, request
import mysql.connector
from config import Config

main_bp = Blueprint("main", __name__)

def get_db():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT
    )

# -----------------------
# HOME
# -----------------------
@main_bp.route("/")
def home():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM schemes ORDER BY created_at DESC LIMIT 3")
    schemes = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("main/home.html", schemes=schemes)

# -----------------------
# ABOUT
# -----------------------
@main_bp.route("/about")
def about():
    return render_template("main/about.html")

# -----------------------
# SCHEMES
# -----------------------
@main_bp.route("/schemes")
def schemes():

    search = request.args.get("search")
    status = request.args.get("status", "active")

    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = "SELECT * FROM schemes WHERE status = %s"
    params = [status]

    if search:
        query += " AND title LIKE %s"
        params.append(f"%{search}%")

    query += " ORDER BY deadline ASC"

    cursor.execute(query, params)
    schemes = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("main/schemes.html", schemes=schemes)