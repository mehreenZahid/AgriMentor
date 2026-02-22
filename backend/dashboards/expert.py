from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

expert = Blueprint("expert", __name__, url_prefix="/expert")

@expert.route("/dashboard")
@login_required
def expert_dashboard():
    if current_user.role != "expert":
        abort(403)
    return render_template("expert/dashboard.html")


@expert.route("/review")
@login_required
def review_cases():
    if current_user.role != "expert":
        abort(403)
    return render_template("expert/review_cases.html")


@expert.route("/manage-schemes")
@login_required
def manage_schemes():
    if current_user.role != "expert":
        abort(403)
    return render_template("expert/manage_schemes.html")


@expert.route("/profile")
@login_required
def profile():
    if current_user.role != "expert":
        abort(403)
    return render_template("expert/profile.html")
