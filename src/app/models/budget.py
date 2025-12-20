"""Budget model for monthly spending limits per category."""

from decimal import Decimal
from typing import Optional

from sqlalchemy import Integer, DECIMAL, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .extensions import db


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
            db.func.coalesce(db.func.sum(db.model.Transaction.amount), 0)
        ).filter(
            db.model.Transaction.category_id == self.category_id,
            db.model.Transaction.user_id == self.user_id,
            db.model.Transaction.transaction_type == 'Expense',
            db.extract('month', db.model.Transaction.date) == self.month,
            db.extract('year', db.model.Transaction.date) == self.year
        ).scalar()
        self.current_spent = Decimal(str(total))

    def __repr__(self) -> str:
        cat_name = self.category.name if self.category else "N/A"
        return f'<Budget {cat_name} {self.month}/{self.year}>'