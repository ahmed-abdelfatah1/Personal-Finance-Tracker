"""Transaction category model for Income/Expense classification."""

from decimal import Decimal
from typing import Optional, List

from sqlalchemy import Integer, String, DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


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