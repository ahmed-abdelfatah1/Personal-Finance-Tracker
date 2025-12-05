"""Application Factory - Creates and configures the Flask application."""

from flask import Flask

from .config import Config
from .extensions import db, bcrypt, login_manager


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    _init_extensions(app)
    _register_blueprints(app)

    return app


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        from .models import User
        return User.query.get(int(user_id))


def _register_blueprints(app: Flask) -> None:
    from .controllers import (
        auth_bp,
        dashboard_bp,
        transaction_bp,
        account_bp,
        budget_bp,
        category_bp,
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(category_bp)

