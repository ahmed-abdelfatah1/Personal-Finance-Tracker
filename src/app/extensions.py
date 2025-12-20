"""
Flask Extensions
Initializes Flask extensions used throughout the application.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

from .db.singleton_db import DatabaseSingleton

# Initialize extensions
# Database connection is managed as a singleton to ensure only one SQLite connection
db = SQLAlchemy()
DatabaseSingleton.set_db(db)  # Register the db instance with the singleton

bcrypt = Bcrypt()
login_manager = LoginManager()

# Configure login manager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

