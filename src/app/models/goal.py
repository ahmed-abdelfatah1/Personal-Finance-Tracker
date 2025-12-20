"""Financial goal model for tracking savings goals."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Date, DECIMAL, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


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