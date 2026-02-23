from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import User




auth_bp = Blueprint("auth", __name__)

# ---------------------------------------------------
# BCRYPT INSTANCE
# ---------------------------------------------------

bcrypt = Bcrypt()

# ---------------------------------------------------
# ROOT ROUTE
# ---------------------------------------------------

@auth_bp.route("/")
def root():
    if current_user.is_authenticated:
        if current_user.role == "farmer":
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("expert_dashboard"))
    return redirect(url_for("auth.login_page"))


# ---------------------------------------------------
# REGISTER PAGE
# ---------------------------------------------------

@auth_bp.route("/register")
def register_page():
    return render_template("register.html")


# ---------------------------------------------------
# REGISTER LOGIC
# ---------------------------------------------------

@auth_bp.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    role = "farmer"


    existing_user = User.get_by_email(email)
    if existing_user:
        flash("Email already registered.", "danger")
        return redirect(url_for("auth.register_page"))

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    User.create(name, email, hashed_password, role)

    flash("Registration successful. Please login.", "success")
    return redirect(url_for("auth.login_page"))


# ---------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------




# ---------------------------------------------------
# LOGIN (GET + POST)
# ---------------------------------------------------

@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.get_by_email(email)

        if user and user.password_hash and bcrypt.check_password_hash(user.password_hash, password):

            login_user(user)

            # ROLE-BASED REDIRECT (same as Google login: app routes at /farmer, /expert)
            if user.role == "farmer":
                return redirect(url_for("dashboard"))
            elif user.role == "expert":
                return redirect(url_for("expert_dashboard"))

        flash("Invalid email or password", "danger")

    return render_template("login.html")



# ---------------------------------------------------
# LOGOUT
# ---------------------------------------------------

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login_page"))

@auth_bp.route("/google-login")
def google_login():
    redirect_uri = url_for("auth.google_callback", _external=True)
    return current_app.google.authorize_redirect(redirect_uri)

@auth_bp.route("/google-callback")
def google_callback():

    try:
        token = current_app.google.authorize_access_token()
    except Exception:
        flash("Google login failed.", "danger")
        return redirect(url_for("auth.login_page"))

    user_info = token["userinfo"]

    email = user_info["email"]
    name = user_info["name"]
    google_id = user_info["sub"]

    user = User.get_by_email(email)

    if not user:
        # Create new farmer account by default
        User.create_google_user(
            name=name,
            email=email,
            oauth_provider="google",
            oauth_id=google_id,
            role="farmer"
        )
        user = User.get_by_email(email)

    login_user(user)

    if user.role == "farmer":
        return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("expert_dashboard"))
