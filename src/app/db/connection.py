"""
Database Connection Module - Centralized DB lifecycle utilities and connection management.
"""

from typing import Optional
from flask import Flask
from sqlalchemy import text

from ..extensions import db


# Singleton DB Access

def get_db():
    """Get the singleton database instance."""
    return db


def get_engine():
    """Get the current database engine."""
    return db.engine


def get_session():
    """Get the current database session."""
    return db.session


# Database Lifecycle Functions

def init_db(app: Optional[Flask] = None):
    """Initialize the database schema - creates all tables."""
    from ..models import finance_models  
    
    if app is not None:
        with app.app_context():
            db.create_all()
    else:
        db.create_all()


def drop_db(app: Optional[Flask] = None):
    """Drop all database tables."""
    if app is not None:
        with app.app_context():
            db.drop_all()
    else:
        db.drop_all()


def reset_db(app: Optional[Flask] = None):
    """Reset the database by dropping and recreating all tables."""
    drop_db(app)
    init_db(app)


# Database Health & Info

def check_connection() -> bool:
    """Check if the database connection is healthy."""
    try:
        db.session.execute(text('SELECT 1'))
        return True
    except Exception:
        return False


def get_table_names() -> list:
    """Get a list of all table names in the database."""
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    return inspector.get_table_names()


def table_exists(table_name: str) -> bool:
    """Check if a specific table exists in the database."""
    return table_name in get_table_names()


def get_db_info() -> dict:
    """Get information about the current database configuration."""
    engine = db.engine
    return {
        'dialect': engine.dialect.name,
        'driver': engine.driver,
        'database': engine.url.database,
        'tables': get_table_names(),
        'connection_healthy': check_connection()
    }
