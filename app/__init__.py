# app/__init__.py
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
import secrets

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Generate a secret key
    app.secret_key = secrets.token_hex(32)

    # Initialise SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Update with your database URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Initialize the login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    with app.app_context():
        # Import the User model
        from app.models import User
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # Import and register blueprints
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app