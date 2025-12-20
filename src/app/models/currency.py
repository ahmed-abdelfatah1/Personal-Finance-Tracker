"""Currency model for multi-currency support."""

from decimal import Decimal
from typing import Optional

from sqlalchemy import String, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column

from .extensions import db


class Currency(db.Model):
    """Currency model for multi-currency support."""
    __tablename__ = 'currency'

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[Optional[str]] = mapped_column(String(5))
    rate_to_base: Mapped[Decimal] = mapped_column(DECIMAL(12, 6), nullable=False)

    def __repr__(self) -> str:
        return f'<Currency {self.code} - {self.name}>'