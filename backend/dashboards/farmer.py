from flask import Blueprint, render_template, session, redirect, url_for


farmer = Blueprint("farmer", __name__, url_prefix="/farmer")

@farmer.route("/dashboard")
def farmer_dashboard():
    if session.get("role") != "farmer":
        return redirect(url_for("auth.login_page"))

    return render_template("farmer/dashboard.html")


@farmer.route("/history")
def history():
    if session.get("role") != "farmer":
        return redirect(url_for("auth.login_page"))

    return render_template("farmer/history.html")


@farmer.route("/profile")
def profile():
    if session.get("role") != "farmer":
        return redirect(url_for("auth.login_page"))

    return render_template("farmer/profile.html")
