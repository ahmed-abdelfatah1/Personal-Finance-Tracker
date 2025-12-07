"""Database migration script to add new tables."""

from src.app import create_app
from src.app.extensions import db

app = create_app()

with app.app_context():
    print("Creating new database tables...")
    db.create_all()
    print("Database tables created successfully!")
    print("\nNew tables added:")
    print("  - goal (Financial Goals)")
    print("  - recurring_transaction (Recurring Transactions)")
