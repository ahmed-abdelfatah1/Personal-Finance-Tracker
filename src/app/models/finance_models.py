"""
Finance Models
Defines all database models for the application.
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Integer, String, DateTime, Date, DECIMAL, Text, 
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from app.extensions import db


class User(db.Model):
    """
    User account model for authentication and user preferences.
    """
    __tablename__ = 'user'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    default_currency: Mapped[str] = mapped_column(String(10), default='EGP')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
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
    
    def __repr__(self):
        return f'<User {self.email}>'


class Account(db.Model):
    """
    Financial account model (bank accounts, wallets, etc.).
    Supports multi-currency (FR-15).
    """
    __tablename__ = 'account'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[Optional[str]] = mapped_column(String(50))
    initial_balance: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=Decimal('0.00'))
    current_balance: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=Decimal('0.00'))
    currency: Mapped[str] = mapped_column(String(10), default='EGP')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="accounts")
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="account", cascade="all, delete-orphan"
    )
    transaction_templates: Mapped[List["TransactionTemplate"]] = relationship(
        "TransactionTemplate", back_populates="account"
    )
    
    def __repr__(self):
        return f'<Account {self.name} - {self.currency}>'


class Category(db.Model):
    """
    Transaction category model for Income/Expense classification.
    Supports optional max single transaction amount (FR-16).
    """
    __tablename__ = 'category'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'Income' or 'Expense'
    color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color code
    max_single_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2))  # FR-16
    
    # Relationships
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
    
    def __repr__(self):
        return f'<Category {self.name} ({self.category_type})>'


class Transaction(db.Model):
    """
    Financial transaction model for tracking income and expenses.
    Indexed for search performance.
    """
    __tablename__ = 'transaction'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('category.id', ondelete='CASCADE'), nullable=False)
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'Income' or 'Expense'
    description: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)  
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    account: Mapped["Account"] = relationship("Account", back_populates="transactions")
    category: Mapped["Category"] = relationship("Category", back_populates="transactions")
    
    # Indexes for search and performance
    __table_args__ = (
        Index('idx_transaction_user_date', 'user_id', 'date'),
        Index('idx_transaction_search', 'user_id', 'description', 'notes'),
    )
    
    def __repr__(self):
        return f'<Transaction {self.transaction_type} {self.amount} on {self.date}>'


class Budget(db.Model):
    """
    Budget model for monthly spending limits per category.
    Tracks current spending and alert thresholds.
    """
    __tablename__ = 'budget'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('category.id', ondelete='CASCADE'), nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    limit_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    current_spent: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=Decimal('0.00'))
    alert_threshold: Mapped[int] = mapped_column(Integer, default=80)  # Percentage
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="budgets")
    category: Mapped["Category"] = relationship("Category", back_populates="budgets")
    
    # Unique constraint: one budget per user/category/month/year
    __table_args__ = (
        UniqueConstraint('user_id', 'category_id', 'month', 'year', name='uq_budget_user_category_month_year'),
    )
    
    def __repr__(self):
        return f'<Budget {self.category.name if self.category else "N/A"} {self.month}/{self.year}>'
    
    @property
    def spent_percentage(self) -> float:
        """Calculate the percentage of budget spent."""
        if self.limit_amount == 0:
            return 0.0
        return float((self.current_spent / self.limit_amount) * 100)
    
    @property
    def is_over_threshold(self) -> bool:
        """Check if spending has exceeded the alert threshold."""
        return self.spent_percentage >= self.alert_threshold
    
    @property
    def is_over_budget(self) -> bool:
        """Check if spending has exceeded the budget limit."""
        return self.current_spent > self.limit_amount


class TransactionTemplate(db.Model):
    """
    Template model for recurring transactions.
    Helps quick entry of regular income/expenses.
    """
    __tablename__ = 'transaction_template'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Monthly Rent"
    description: Mapped[Optional[str]] = mapped_column(String(255))
    default_amount: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2))
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'Income' or 'Expense'
    account_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('account.id', ondelete='SET NULL')
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey('category.id', ondelete='SET NULL')
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="transaction_templates")
    account: Mapped[Optional["Account"]] = relationship("Account", back_populates="transaction_templates")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="transaction_templates")
    
    def __repr__(self):
        return f'<TransactionTemplate {self.name}>'


class Currency(db.Model):
    """
    Currency model for multi-currency support.
    Stores exchange rates relative to a base currency.
    """
    __tablename__ = 'currency'
    
    code: Mapped[str] = mapped_column(String(10), primary_key=True)  # e.g., 'EGP', 'USD'
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., 'Egyptian Pound'
    symbol: Mapped[Optional[str]] = mapped_column(String(5))  # e.g., 'E£', '$'
    rate_to_base: Mapped[Decimal] = mapped_column(DECIMAL(12, 6), nullable=False)  
    
    def __repr__(self):
        return f'<Currency {self.code} - {self.name}>'

