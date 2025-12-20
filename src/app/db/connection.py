"""
Database Connection Module - Centralized DB lifecycle utilities and connection management.
"""

from typing import Optional
from flask import Flask
from sqlalchemy import text

from .singleton_db import DatabaseSingleton


# Singleton DB Access

def get_db():
    """
    Get the singleton database instance.
    
    This function ensures that only one database connection exists
    by using the DatabaseSingleton pattern. All calls to this function
    return the same database instance, preventing unnecessary connection creation.
    
    The singleton pattern ensures:
    - Only one SQLite connection pool is created
    - All database operations use the same connection instance
    - Prevents creating thousands of unnecessary connections
    
    Returns:
        The singleton SQLAlchemy database instance
    """
    try:
        return DatabaseSingleton.get_db()
    except RuntimeError:
        # Fallback to direct db import if singleton not initialized
        # (should not happen in normal operation)
        from ..extensions import db  # Lazy import to avoid circular dependency
        return db


def get_engine():
    """Get the current database engine."""
    db_instance = get_db()
    return db_instance.engine


def get_session():
    """Get the current database session."""
    db_instance = get_db()
    return db_instance.session


# Database Lifecycle Functions

def init_db(app: Optional[Flask] = None):
    """Initialize the database schema - creates all tables."""
    from ..models import finance_models  # Import models to register them
    
    db_instance = get_db()
    if app is not None:
        with app.app_context():
            db_instance.create_all()
    else:
        db_instance.create_all()


def drop_db(app: Optional[Flask] = None):
    """Drop all database tables."""
    db_instance = get_db()
    if app is not None:
        with app.app_context():
            db_instance.drop_all()
    else:
        db_instance.drop_all()


def reset_db(app: Optional[Flask] = None):
    """Reset the database by dropping and recreating all tables."""
    drop_db(app)
    init_db(app)


# Database Health & Info

def check_connection() -> bool:
    """Check if the database connection is healthy."""
    try:
        db_instance = get_db()
        db_instance.session.execute(text('SELECT 1'))
        return True
    except Exception:
        return False


def get_table_names() -> list:
    """Get a list of all table names in the database."""
    from sqlalchemy import inspect
    db_instance = get_db()
    inspector = inspect(db_instance.engine)
    return inspector.get_table_names()


def table_exists(table_name: str) -> bool:
    """Check if a specific table exists in the database."""
    return table_name in get_table_names()


def get_db_info() -> dict:
    """Get information about the current database configuration."""
    db_instance = get_db()
    engine = db_instance.engine
    return {
        'dialect': engine.dialect.name,
        'driver': engine.driver,
        'database': engine.url.database,
        'tables': get_table_names(),
        'connection_healthy': check_connection()
    }
