"""User account model for authentication and preferences."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from flask_login import UserMixin

from .extensions import db, bcrypt


class User(UserMixin, db.Model):
    """User account model for authentication and preferences."""
    __tablename__ = 'user'

    id: db.Mapped[int] = db.mapped_column(db.Integer, primary_key=True, autoincrement=True)
    email: db.Mapped[str] = db.mapped_column(db.String(120), nullable=False, unique=True)
    password_hash: db.Mapped[str] = db.mapped_column(db.String(128), nullable=False)
    display_name: db.Mapped[Optional[str]] = db.mapped_column(db.String(100))
    default_currency: db.Mapped[str] = db.mapped_column(db.String(10), default='EGP')
    created_at: db.Mapped[datetime] = db.mapped_column(db.DateTime, default=datetime.utcnow)

    accounts: db.Mapped[List["Account"]] = db.relationship(
        "Account", back_populates="user", cascade="all, delete-orphan"
    )
    categories: db.Mapped[List["Category"]] = db.relationship(
        "Category", back_populates="user", cascade="all, delete-orphan"
    )
    transactions: db.Mapped[List["Transaction"]] = db.relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    budgets: db.Mapped[List["Budget"]] = db.relationship(
        "Budget", back_populates="user", cascade="all, delete-orphan"
    )
    transaction_templates: db.Mapped[List["TransactionTemplate"]] = db.relationship(
        "TransactionTemplate", back_populates="user", cascade="all, delete-orphan"
    )
    goals: db.Mapped[List["Goal"]] = db.relationship(
        "Goal", back_populates="user", cascade="all, delete-orphan"
    )
    recurring_transactions: db.Mapped[List["RecurringTransaction"]] = db.relationship(
        "RecurringTransaction", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_total_balance(self) -> Decimal:
        return sum((acc.current_balance for acc in self.accounts), Decimal('0.00'))

    def __repr__(self) -> str:
        return f'<User {self.email}>'