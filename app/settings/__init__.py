from flask import Blueprint

settings_bp = Blueprint("settings_bp", __name__,
                        template_folder='templates')

from app.settings import routes