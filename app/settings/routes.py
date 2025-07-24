from flask import render_template
from app.settings import settings_bp

@settings_bp.route("/", methods=['GET'])
def index():
    return render_template("settings/index.html")