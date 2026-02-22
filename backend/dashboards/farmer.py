from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user

farmer = Blueprint("farmer", __name__, url_prefix="/farmer")

@farmer.route("/dashboard")
@login_required
def farmer_dashboard():
    if current_user.role != "farmer":
        abort(403)
    return render_template("farmer/dashboard.html")


@farmer.route("/history")
@login_required
def history():
    if current_user.role != "farmer":
        abort(403)
    return render_template("farmer/history.html")


@farmer.route("/profile")
@login_required
def profile():
    if current_user.role != "farmer":
        abort(403)
    return render_template("farmer/profile.html")
