"""Template model for recurring transactions."""

from decimal import Decimal
from typing import Optional

from sqlalchemy import Integer, String, DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


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