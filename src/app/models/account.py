"""Financial account model (bank accounts, wallets, etc.)."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import Integer, String, DateTime, DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


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