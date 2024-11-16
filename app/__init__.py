# app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)

    # Import and register blueprints
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app