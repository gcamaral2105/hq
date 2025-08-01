from flask import Blueprint

partners_bp = Blueprint("partners_bp", __name__,
                        template_folder='templates')

from app.partner import routes