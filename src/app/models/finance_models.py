"""Finance Models - Defines all database models for the application."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from flask_login import UserMixin
from sqlalchemy import (
    Integer, String, DateTime, Date, DECIMAL, Text,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import db, bcrypt


class User(UserMixin, db.Model):
    """User account model for authentication and preferences."""
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    default_currency: Mapped[str] = mapped_column(String(10), default='EGP')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    accounts: Mapped[List["Account"]] = relationship(
        "Account", back_populates="user", cascade="all, delete-orphan"
    )
    categories: Mapped[List["Category"]] = relationship(
        "Category", back_populates="user", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    budgets: Mapped[List["Budget"]] = relationship(
        "Budget", back_populates="user", cascade="all, delete-orphan"
    )
    transaction_templates: Mapped[List["TransactionTemplate"]] = relationship(
        "TransactionTemplate", back_populates="user", cascade="all, delete-orphan"
    )
    goals: Mapped[List["Goal"]] = relationship(
        "Goal", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_total_balance(self) -> Decimal:
        return sum((acc.current_balance for acc in self.accounts), Decimal('0.00'))

    def __repr__(self) -> str:
        return f'<User {self.email}>'


class Account(db.Model):
    """Financial account model (bank accounts, wallets, etc.)."""
    __tablename__ = 'account'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[Optional[str]] = mapped_column(String(50))
    initial_balance: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal('0.00')
    )
    current_balance: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal('0.00')
    )
    currency: Mapped[str] = mapped_column(String(10), default='EGP')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="account", cascade="all, delete-orphan"
    )
    transaction_templates: Mapped[List["TransactionTemplate"]] = relationship(
        "TransactionTemplate", back_populates="account"
    )

    def __repr__(self) -> str:
        return f'<Account {self.name} - {self.currency}>'


class Category(db.Model):
    """Transaction category model for Income/Expense classification."""
    __tablename__ = 'category'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_type: Mapped[str] = mapped_column(String(10), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7))
    max_single_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2))

    user: Mapped["User"] = relationship("User", back_populates="categories")
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="category", cascade="all, delete-orphan"
    )
    budgets: Mapped[List["Budget"]] = relationship(
        "Budget", back_populates="category", cascade="all, delete-orphan"
    )
    transaction_templates: Mapped[List["TransactionTemplate"]] = relationship(
        "TransactionTemplate", back_populates="category"
    )

    def __repr__(self) -> str:
        return f'<Category {self.name} ({self.category_type})>'


class Transaction(db.Model):
    """Financial transaction model for tracking income and expenses."""
    __tablename__ = 'transaction'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False
    )
    account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('account.id', ondelete='CASCADE'), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('category.id', ondelete='CASCADE'), nullable=False
    )
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="transactions")
    account: Mapped["Account"] = relationship("Account", back_populates="transactions")
    category: Mapped["Category"] = relationship(
        "Category", back_populates="transactions"
    )

    __table_args__ = (
        Index('idx_transaction_user_date', 'user_id', 'date'),
        Index('idx_transaction_search', 'user_id', 'description', 'notes'),
    )

    def __repr__(self) -> str:
        return f'<Transaction {self.transaction_type} {self.amount} on {self.date}>'


class Budget(db.Model):
    """Budget model for monthly spending limits per category."""
    __tablename__ = 'budget'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('category.id', ondelete='CASCADE'), nullable=False
    )
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    current_spent: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal('0.00')
    )
    alert_threshold: Mapped[int] = mapped_column(Integer, default=80)

    user: Mapped["User"] = relationship("User", back_populates="budgets")
    category: Mapped["Category"] = relationship("Category", back_populates="budgets")

    __table_args__ = (
        UniqueConstraint(
            'user_id', 'category_id', 'month', 'year',
            name='uq_budget_user_category_month_year'
        ),
    )

    @property
    def spent_percentage(self) -> float:
        if self.limit_amount == 0:
            return 0.0
        return float((self.current_spent / self.limit_amount) * 100)

    @property
    def is_over_threshold(self) -> bool:
        return self.spent_percentage >= self.alert_threshold

    @property
    def is_over_budget(self) -> bool:
        return self.current_spent > self.limit_amount

    def get_percentage_used(self) -> float:
        return self.spent_percentage

    def check_alert_threshold(self) -> bool:
        return self.is_over_threshold

    def update_current_spent(self) -> None:
        total = db.session.query(
            db.func.coalesce(db.func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.category_id == self.category_id,
            Transaction.user_id == self.user_id,
            Transaction.transaction_type == 'Expense',
            db.extract('month', Transaction.date) == self.month,
            db.extract('year', Transaction.date) == self.year
        ).scalar()
        self.current_spent = Decimal(str(total))

    def __repr__(self) -> str:
        cat_name = self.category.name if self.category else "N/A"
        return f'<Budget {cat_name} {self.month}/{self.year}>'


class TransactionTemplate(db.Model):
    """Template model for recurring transactions."""
    __tablename__ = 'transaction_template'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    default_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2))
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    account_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('account.id', ondelete='SET NULL')
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('category.id', ondelete='SET NULL')
    )

    user: Mapped["User"] = relationship("User", back_populates="transaction_templates")
    account: Mapped[Optional["Account"]] = relationship(
        "Account", back_populates="transaction_templates"
    )
    category: Mapped[Optional["Category"]] = relationship(
        "Category", back_populates="transaction_templates"
    )

    def __repr__(self) -> str:
        return f'<TransactionTemplate {self.name}>'


class Goal(db.Model):
    """Financial goal model for tracking savings goals."""
    __tablename__ = 'goal'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    current_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), default=Decimal('0.00')
    )
    target_date: Mapped[Optional[datetime]] = mapped_column(Date)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="goals")

    @property
    def progress_percentage(self) -> float:
        if self.target_amount == 0:
            return 0.0
        return float((self.current_amount / self.target_amount) * 100)

    @property
    def remaining_amount(self) -> Decimal:
        return self.target_amount - self.current_amount

    @property
    def is_completed(self) -> bool:
        return self.current_amount >= self.target_amount

    def __repr__(self) -> str:
        return f'<Goal {self.name} - {self.current_amount}/{self.target_amount}>'


class Currency(db.Model):
    """Currency model for multi-currency support."""
    __tablename__ = 'currency'

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[Optional[str]] = mapped_column(String(5))
    rate_to_base: Mapped[Decimal] = mapped_column(DECIMAL(12, 6), nullable=False)

    def __repr__(self) -> str:
        return f'<Currency {self.code} - {self.name}>'
