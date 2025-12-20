"""Recurring transaction model for automatic transaction generation."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Date, DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


class RecurringTransaction(db.Model):
    """Recurring transaction model for automatic transaction generation."""
    __tablename__ = 'recurring_transaction'

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
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    start_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(Date)
    last_generated: Mapped[Optional[datetime]] = mapped_column(Date)
    next_due: Mapped[datetime] = mapped_column(Date, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = db.mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="recurring_transactions")
    account: Mapped["Account"] = relationship("Account")
    category: Mapped["Category"] = relationship("Category")

    def __repr__(self) -> str:
        return f'<RecurringTransaction {self.name} - {self.frequency}>'