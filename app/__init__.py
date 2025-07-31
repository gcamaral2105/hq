from flask import Flask
from .extensions import db, migrate

from .main import main_bp

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from app.main import main_bp
        from app.settings import settings_bp
        from app.product import product_bp

        app.register_blueprint(main_bp, url_prefix="/")
        app.register_blueprint(settings_bp, url_prefix="/settings")
        app.register_blueprint(product_bp, url_prefix="/product")

    return app
