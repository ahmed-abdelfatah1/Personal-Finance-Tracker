import os

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")
    
    # Use environment variable for database path if set
    db_path = os.environ.get("DATABASE_PATH")
    if db_path:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
    else:
        # Check if root database exists first (for compatibility with existing databases)
        root_db = os.path.join(basedir, "finance.db")
        if os.path.exists(root_db):
            # Use existing root database if it exists
            SQLALCHEMY_DATABASE_URI = "sqlite:///" + root_db
        elif os.environ.get("FLASK_ENV") == "production":
            # In Docker/production, use /app/data directory for new databases
            data_dir = os.path.join(basedir, "data")
            os.makedirs(data_dir, exist_ok=True)
            SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(data_dir, "finance.db")
        else:
            # In local development, use project root
            SQLALCHEMY_DATABASE_URI = "sqlite:///" + root_db
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
