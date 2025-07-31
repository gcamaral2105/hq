from flask import Blueprint

product_bp = Blueprint('product_bp', __name__,
                    template_folder='templates',
                    static_folder='static')

from app.product import routes