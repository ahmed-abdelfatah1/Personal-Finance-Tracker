"""Financial transaction model for tracking income and expenses."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import Integer, String, DateTime, Date, DECIMAL, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


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