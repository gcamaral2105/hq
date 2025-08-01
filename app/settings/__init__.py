from flask import Blueprint

settings_bp = Blueprint("settings_bp", __name__,
                        template_folder='templates',
                        static_folder='static',
                        static_url_path='/settings/static')

from app.settings import routes