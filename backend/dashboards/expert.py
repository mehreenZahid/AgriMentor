from flask import Blueprint, render_template, session, redirect, url_for

expert = Blueprint("expert", __name__, url_prefix="/expert")

@expert.route("/dashboard")
def expert_dashboard():
    if session.get("role") != "expert":
        return redirect(url_for("auth.login_page"))

    return render_template("expert/dashboard.html")


@expert.route("/review")
def review_cases():
    if session.get("role") != "expert":
        return redirect(url_for("auth.login_page"))

    return render_template("expert/review_cases.html")


@expert.route("/manage-schemes")
def manage_schemes():
    if session.get("role") != "expert":
        return redirect(url_for("auth.login_page"))

    return render_template("expert/manage_schemes.html")


@expert.route("/profile")
def profile():
    if session.get("role") != "expert":
        return redirect(url_for("auth.login_page"))

    return render_template("expert/profile.html")
